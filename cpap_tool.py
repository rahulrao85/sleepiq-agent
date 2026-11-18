"""
Sleep IQ — CPAP Data Tool
Parses ResMed STR.edf files or pre-parsed cpap_data.json.
Exposes structured analytics for the Foundry agent to reason over.
"""

import struct, json, os, zipfile, re, tempfile
from datetime import datetime, timedelta
from pathlib import Path

NUM_SIGNALS = 80
EPOCH = datetime(1970, 1, 1)
EDF_HEADER_SIZE = 20736


# ─── EDF Parser ───────────────────────────────────────────────────────────────

def parse_edf(filepath: str) -> dict:
    """Parse a ResMed STR.edf file and return structured CPAP data."""
    with open(filepath, 'rb') as f:
        data = f.read()

    labels = []
    for i in range(NUM_SIGNALS):
        label = data[256 + i * 16: 256 + i * 16 + 16].decode('ascii', errors='replace').strip()
        labels.append(label)

    off = 256 + NUM_SIGNALS * 16 + NUM_SIGNALS * 80 + NUM_SIGNALS * 8
    pmin_o = off; off += NUM_SIGNALS * 8
    pmax_o = off; off += NUM_SIGNALS * 8
    dmin_o = off; off += NUM_SIGNALS * 8
    dmax_o = off; off += NUM_SIGNALS * 8
    off += NUM_SIGNALS * 80
    samp_o = off

    def gf(i, o):
        return float(data[o + i * 8: o + i * 8 + 8].decode('ascii', errors='replace').strip())
    def gi(i, o):
        return int(data[o + i * 8: o + i * 8 + 8].decode('ascii', errors='replace').strip())

    pmins = [gf(i, pmin_o) for i in range(NUM_SIGNALS)]
    pmaxs = [gf(i, pmax_o) for i in range(NUM_SIGNALS)]
    dmins = [gi(i, dmin_o) for i in range(NUM_SIGNALS)]
    dmaxs = [gi(i, dmax_o) for i in range(NUM_SIGNALS)]
    scnts = [gi(i, samp_o) for i in range(NUM_SIGNALS)]

    rbytes = sum(scnts) * 2
    if rbytes == 0:
        raise ValueError('Not a valid ResMed STR.edf file.')

    nrecs = (len(data) - EDF_HEADER_SIZE) // rbytes
    records = []
    for r in range(nrecs):
        rec = {}
        ro = EDF_HEADER_SIZE + r * rbytes
        si = 0
        for i, label in enumerate(labels):
            ns = scnts[i]
            if ns == 0:
                continue
            raw = [struct.unpack_from('<h', data, ro + (si + s) * 2)[0] for s in range(ns)]
            if dmaxs[i] != dmins[i]:
                vals = [(v - dmins[i]) / (dmaxs[i] - dmins[i]) * (pmaxs[i] - pmins[i]) + pmins[i] for v in raw]
            else:
                vals = [float(v) for v in raw]
            rec[label] = vals if len(vals) > 1 else vals[0]
            si += ns
        records.append(rec)

    info = {'model': 'ResMed Device', 'serial': ''}
    parent = os.path.dirname(filepath)
    ipath = os.path.join(parent, 'Identification.tgt')
    if os.path.exists(ipath):
        with open(ipath) as f:
            for line in f:
                s = line.strip()
                if s.startswith('#PNA '): info['model'] = s[5:]
                elif s.startswith('#SRN '): info['serial'] = s[5:]

    out = {'source': 'cpap', 'device': info, 'records': []}
    for rec in records:
        entry = {}
        for label in labels:
            v = rec.get(label)
            if v is not None:
                entry[label] = v
        dv = rec.get('Date')
        if isinstance(dv, (int, float)):
            try:
                entry['DateFormatted'] = (EPOCH + timedelta(days=int(dv))).strftime('%Y-%m-%d')
            except:
                entry['DateFormatted'] = str(dv)
        out['records'].append(entry)
    return out


_DATE_PATTERN = re.compile(r'^(\d{2})-(\w{3})-(\d{4})$')
_MONTHS = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06',
           'Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}

def _normalise_dates(records: list) -> list:
    """Convert DD-Mon-YYYY DateFormatted to YYYY-MM-DD in-place."""
    for r in records:
        raw = r.get('DateFormatted', '')
        m = _DATE_PATTERN.match(raw)
        if m:
            month = _MONTHS.get(m.group(2))
            if month:
                r['DateFormatted'] = f'{m.group(3)}-{month}-{m.group(1)}'
    return records

def load_cpap_data(path: str) -> dict:
    """Load CPAP data from .json, .edf, or .zip."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = p.suffix.lower()
    if ext == '.zip':
        with zipfile.ZipFile(path) as z:
            edf_files = [n for n in z.namelist() if n.lower().endswith('.edf')]
            json_files = [n for n in z.namelist() if n.lower().endswith('.json')]
            if edf_files:
                tmp = tempfile.NamedTemporaryFile(suffix='.edf', delete=False)
                tmp.write(z.read(edf_files[0]))
                tmp.close()
                try:
                    d = parse_edf(tmp.name)
                    d['records'] = _normalise_dates(d.get('records', []))
                    return d
                finally:
                    os.unlink(tmp.name)
            elif json_files:
                tmp = tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w')
                tmp.write(z.read(json_files[0]).decode('utf-8'))
                tmp.close()
                try:
                    return load_cpap_data(tmp.name)
                finally:
                    os.unlink(tmp.name)
        raise ValueError("No .edf or .json found inside the ZIP archive.")

    if ext == '.json':
        with open(p) as f:
            d = json.load(f)
            d['source'] = 'cpap'
            d['records'] = _normalise_dates(d.get('records', []))
            return d
    elif ext == '.edf':
        d = parse_edf(str(p))
        d['records'] = _normalise_dates(d.get('records', []))
        return d
    raise ValueError(f"Unsupported file type: {ext}")


# ─── Analytics Engine ─────────────────────────────────────────────────────────

def compute_cpap_stats(data: dict, days: int = None, start_date: str = None, end_date: str = None) -> dict:
    """
    Compute comprehensive CPAP statistics for AI reasoning.

    Args:
        data: Raw CPAP data dict
        days: Limit to last N days (None = all)
        start_date: Limit to dates >= start_date (YYYY-MM-DD)
        end_date: Limit to dates <= end_date (YYYY-MM-DD)

    Returns:
        Structured analytics dict with severity, trends, flags
    """
    records = sorted(data.get('records', []), key=lambda r: r.get('DateFormatted', r.get('Date', '')))
    
    if start_date:
        records = [r for r in records if r.get('DateFormatted', '') >= start_date]
    if end_date:
        records = [r for r in records if r.get('DateFormatted', '') <= end_date]
        
    if days:
        records = records[-days:]

    valid = [r for r in records if (r.get('OnDuration') or 0) > 0]
    if not valid:
        return {'error': 'No therapy sessions found in the selected date range.'}

    def med(arr):
        if not arr: return 0.0
        s = sorted(arr)
        m = len(s) // 2
        return (s[m-1] + s[m]) / 2 if len(s) % 2 == 0 else float(s[m])

    def avg(arr):
        return sum(arr) / len(arr) if arr else 0.0

    def pct_ile(arr, p):
        if not arr: return 0.0
        s = sorted(arr)
        return s[min(int(len(s) * p / 100), len(s) - 1)]

    # Extract signal arrays
    ahi   = [r['AHI']         for r in valid if r.get('AHI')         is not None]
    ai    = [r['AI']          for r in valid if r.get('AI')          is not None]
    hi    = [r['HI']          for r in valid if r.get('HI')          is not None]
    oai   = [r['OAI']         for r in valid if r.get('OAI')         is not None]
    cai   = [r['CAI']         for r in valid if r.get('CAI')         is not None]
    csr   = [r['CSR']         for r in valid if r.get('CSR')         is not None]
    leak  = [r['Leak.95'] * 60 for r in valid if r.get('Leak.95')     is not None]
    press = [r['MaskPress.95']for r in valid if r.get('MaskPress.95')is not None]
    dur   = [r['OnDuration']  for r in valid if r.get('OnDuration')  is not None]

    total_mins   = sum(dur)
    days_ge4h    = len([d for d in dur if d >= 240])
    compliance   = days_ge4h / len(records) * 100 if records else 0

    # Trend: compare first third vs last third
    n = len(ahi)
    third = max(1, n // 3)
    ahi_early = avg(ahi[:third])
    ahi_late  = avg(ahi[-third:])
    if ahi_late < ahi_early * 0.85:
        ahi_trend = 'improving'
    elif ahi_late > ahi_early * 1.15:
        ahi_trend = 'worsening'
    else:
        ahi_trend = 'stable'

    avg_ahi = avg(ahi)
    avg_leak = avg(leak)
    bad_nights = [r for r in valid if (r.get('AHI') or 0) >= 10]
    high_leak_nights = [r for r in valid if (r.get('Leak.95') or 0) > 24]

    ref = valid[-1] if valid else {}

    return {
        'data_type': 'cpap',
        'summary': {
            'total_days': len(records),
            'therapy_days': len(valid),
            'date_range': f"{records[0].get('DateFormatted','?')} to {records[-1].get('DateFormatted','?')}",
            'device': f"{data.get('device',{}).get('model','ResMed Device')} (S/N: {data.get('device',{}).get('serial','')})",
        },
        'ahi': {
            'average': round(avg_ahi, 2),
            'median':  round(med(ahi), 2),
            'worst':   round(max(ahi), 2) if ahi else 0,
            'best':    round(min(ahi), 2) if ahi else 0,
            'p95':     round(pct_ile(ahi, 95), 2),
            'trend':   ahi_trend,
            'early_avg':  round(ahi_early, 2),
            'recent_avg': round(ahi_late, 2),
            'severity': (
                'normal'   if avg_ahi < 5  else
                'mild'     if avg_ahi < 15 else
                'moderate' if avg_ahi < 30 else
                'severe'
            ),
            'bad_nights_count': len(bad_nights),
            'bad_nights_pct':   round(len(bad_nights) / len(valid) * 100, 1) if valid else 0,
        },
        'events': {
            'apnea_avg':       round(avg(ai), 2),
            'hypopnea_avg':    round(avg(hi), 2),
            'obstructive_avg': round(avg(oai), 2),
            'central_avg':     round(avg(cai), 2),
            'cheyne_stokes':   round(avg(csr), 2),
            'dominant_type': (
                'obstructive' if avg(oai) > avg(cai) else
                'central'     if avg(cai) > avg(oai) else
                'mixed'
            ),
        },
        'compliance': {
            'pct_ge_4h':          round(compliance, 1),
            'days_ge_4h':         days_ge4h,
            'avg_usage_hours':    round(total_mins / len(valid) / 60, 2) if valid else 0,
            'median_usage_hours': round(med(dur) / 60, 2),
            'total_hours':        round(total_mins / 60, 1),
            'status': (
                'compliant'     if compliance >= 70 else
                'borderline'    if compliance >= 50 else
                'non-compliant'
            ),
        },
        'therapy': {
            'pressure_p95':       round(med(press), 1),
            'leak_rate_p95':      round(med(leak), 1),
            'high_leak_nights':   len(high_leak_nights),
            'leak_concern':       len(high_leak_nights) > len(valid) * 0.2,
            'avg_leak':           round(avg_leak, 2),
            'settings': {
                'mode':         {1:'AutoSet',2:'CPAP',3:'AutoSet for Her'}.get(ref.get('Mode'),'AutoSet'),
                'min_pressure': round(ref.get('S.AS.MinPress', 4), 1),
                'max_pressure': round(ref.get('S.AS.MaxPress', 20), 1),
                'epr_level':    round(ref.get('S.EPR.Level', 0), 1),
                'mask_type':    {1:'Nasal',2:'Full Face',3:'Nasal Pillows'}.get(ref.get('S.Mask'),'Unknown'),
            },
        },
        'flags': _generate_flags(avg_ahi, avg_leak, compliance, ahi_trend, avg(cai), avg(oai)),
        'trend_series': {
            'dates':      [r.get('DateFormatted','') for r in records],
            'ahi':        [round(r.get('AHI',0) or 0, 2)           for r in records],
            'usage_hrs':  [round((r.get('OnDuration',0) or 0)/60,2) for r in records],
            'leak_95':    [round((r.get('Leak.95',0) or 0)*60, 2)   for r in records],
            'press_95':   [round(r.get('MaskPress.95',0) or 0, 2)   for r in records],
        },
        'recent_nights': _recent_nights(valid, 7),
    }


def _generate_flags(avg_ahi, avg_leak, compliance, trend, avg_cai, avg_oai) -> list:
    """Generate actionable flag strings for the AI agent to reason over."""
    flags = []
    if avg_ahi >= 30:
        flags.append('CRITICAL: Average AHI is severe (≥30). Urgent clinical review recommended.')
    elif avg_ahi >= 15:
        flags.append('WARNING: Average AHI is moderate (15–30). Therapy may need adjustment.')
    elif avg_ahi >= 5:
        flags.append('INFO: AHI is mildly elevated (5–15). Monitor and discuss with provider.')
    else:
        flags.append('GOOD: AHI is within normal range (<5 events/hour).')

    if trend == 'worsening':
        flags.append('WARNING: AHI trend is worsening over the analysis period.')
    elif trend == 'improving':
        flags.append('GOOD: AHI is trending in the right direction — therapy is working.')

    if avg_leak > 24:
        flags.append('WARNING: Average large leak rate is high (>24 L/min). Check mask fit and seal.')

    if compliance < 50:
        flags.append('WARNING: Compliance is below 50%. Insurance and therapeutic goals may be at risk.')
    elif compliance < 70:
        flags.append('INFO: Compliance is borderline. Try to use CPAP every night.')

    if avg_cai > 5:
        flags.append('ATTENTION: Central apnea index is elevated. Discuss with your sleep physician.')

    return flags


def _recent_nights(valid_records: list, n: int) -> list:
    """Return the last N nights as a clean list for agent reasoning."""
    recent = valid_records[-n:]
    return [{
        'date':       r.get('DateFormatted', ''),
        'ahi':        round(r.get('AHI',0) or 0, 2),
        'usage_hrs':  round((r.get('OnDuration',0) or 0)/60, 2),
        'leak_95':    round((r.get('Leak.95',0) or 0)*60, 2),
        'press_95':   round(r.get('MaskPress.95',0) or 0, 2),
        'obstructive':round(r.get('OAI',0) or 0, 2),
        'central':    round(r.get('CAI',0) or 0, 2),
    } for r in recent]
