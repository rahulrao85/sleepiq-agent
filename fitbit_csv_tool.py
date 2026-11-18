"""
Sleep IQ — Fitbit & Generic CSV Tool

Fitbit: Parses JSON export from fitbit.com dashboard
Generic: Universal CSV template for Garmin, Samsung, manual entry

Fitbit export: fitbit.com → Settings → Data Export → Request Data
Unzip → sleep/ folder contains per-month JSON files.
"""

import json, csv, io
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# ─── Fitbit Parser ────────────────────────────────────────────────────────────

def parse_fitbit(path: str) -> dict:
    """
    Parse Fitbit sleep export.

    Accepts:
    - A single sleep-YYYY-MM-DD.json file
    - A folder containing multiple monthly sleep JSON files
    - A ZIP of the export

    Returns: Sleep IQ standard dict
    """
    p = Path(path)

    if p.suffix.lower() == '.zip':
        import zipfile, tempfile
        tmp = tempfile.mkdtemp()
        with zipfile.ZipFile(p) as z:
            z.extractall(tmp)
        p = Path(tmp)

    # Collect all sleep JSON files
    if p.is_dir():
        json_files = list(p.rglob('sleep-*.json')) + list(p.rglob('sleep_*.json'))
        if not json_files:
            # Try any JSON in a sleep/ subfolder
            json_files = list((p / 'sleep').glob('*.json')) if (p / 'sleep').exists() else []
        if not json_files:
            raise FileNotFoundError('No Fitbit sleep JSON files found. Expected files like sleep-2025-01.json')
    else:
        json_files = [p]

    all_records = []
    for jf in json_files:
        with open(jf) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                continue
        # Each file is a list of sleep log objects
        if isinstance(data, list):
            all_records.extend(data)
        elif isinstance(data, dict) and 'sleep' in data:
            all_records.extend(data['sleep'])

    if not all_records:
        return {'source': 'fitbit', 'error': 'No sleep records found in Fitbit export.', 'records': []}

    return _build_fitbit_records(all_records)


def _build_fitbit_records(raw_records: list) -> dict:
    """Convert raw Fitbit sleep log entries to Sleep IQ standard format."""
    daily = defaultdict(lambda: {
        'main_sleep': None, 'naps': [],
    })

    for rec in raw_records:
        date_of_sleep = rec.get('dateOfSleep', '')
        if not date_of_sleep:
            continue
        if rec.get('isMainSleep', False):
            daily[date_of_sleep]['main_sleep'] = rec
        else:
            daily[date_of_sleep]['naps'].append(rec)

    records = []
    for day_key in sorted(daily.keys()):
        main = daily[day_key]['main_sleep']
        if not main:
            continue

        levels = main.get('levels', {})
        summary = levels.get('summary', {})

        # Stage minutes
        deep_min  = summary.get('deep',  {}).get('minutes', 0) or summary.get('deepSleep', {}).get('minutes', 0)
        light_min = summary.get('light', {}).get('minutes', 0) or summary.get('lightSleep', {}).get('minutes', 0)
        rem_min   = summary.get('rem',   {}).get('minutes', 0) or summary.get('remSleep',   {}).get('minutes', 0)
        wake_min  = summary.get('wake',  {}).get('minutes', 0) or summary.get('awake',      {}).get('minutes', 0)

        # Efficiency and total
        efficiency  = main.get('efficiency', None)
        total_min   = main.get('minutesAsleep', 0) or main.get('duration', 0) // 60000
        in_bed_min  = main.get('timeInBed', 0)
        spo2_avg    = main.get('spo2', {}).get('avg', None) if isinstance(main.get('spo2'), dict) else main.get('spo2', None)
        hrv_daily   = main.get('hrv', {}).get('dailyRmssd', None) if isinstance(main.get('hrv'), dict) else None
        score_data  = main.get('score', None)  # newer Fitbit devices
        if isinstance(score_data, dict):
            sleep_score = score_data.get('overall', None)
        else:
            sleep_score = score_data

        records.append({
            'DateFormatted':    day_key,
            'sleep_total_min':  round(total_min),
            'sleep_deep_min':   round(deep_min),
            'sleep_light_min':  round(light_min),
            'sleep_rem_min':    round(rem_min),
            'sleep_awake_min':  round(wake_min),
            'sleep_efficiency': efficiency,
            'spo2_avg_pct':     round(spo2_avg, 1) if spo2_avg else None,
            'hrv_avg_ms':       round(hrv_daily, 1) if hrv_daily else None,
            'sleep_score':      sleep_score,
            'spo2_concern':     bool(spo2_avg and spo2_avg < 90),
        })

    return {
        'source': 'fitbit',
        'device': 'Fitbit',
        'records': records,
    }


# ─── Generic / Garmin CSV Parser ──────────────────────────────────────────────

GENERIC_COLUMNS = {
    # Required
    'date': ['date', 'day', 'Date', 'Day', 'Sleep Score 4 Weeks', 'Sleep Score 7 Days', 'Sleep Score 1 Year', 'Sleep Score 6 Months', 'Sleep Score 30 Days'],
    # Optional — we try multiple possible column names
    'sleep_total_min':  ['sleep_total_min', 'total_sleep_minutes', 'sleep_minutes', 'SleepDuration', 'Avg Duration', 'Duration'],
    'sleep_deep_min':   ['sleep_deep_min', 'deep_sleep_min', 'DeepSleepMinutes', 'deep'],
    'sleep_rem_min':    ['sleep_rem_min', 'rem_sleep_min', 'REMSleepMinutes', 'rem'],
    'sleep_light_min':  ['sleep_light_min', 'light_sleep_min', 'LightSleepMinutes', 'light'],
    'sleep_score':      ['sleep_score', 'SleepScore', 'sleep_quality_score', 'score', 'Avg Score', 'Score'],
    'hrv_avg_ms':       ['hrv_avg_ms', 'hrv_ms', 'HRV', 'hrv', 'AvgHRV', 'Avg HRV', 'HRV Status'],
    'spo2_avg_pct':     ['spo2_avg_pct', 'spo2', 'SpO2', 'oxygen_saturation', 'AvgSpO2', 'Avg SpO2', 'Pulse Ox'],
    'spo2_min_pct':     ['spo2_min_pct', 'min_spo2', 'MinSpO2', 'lowest_spo2'],
    'resting_hr_bpm':   ['resting_hr_bpm', 'resting_hr', 'RestingHR', 'resting_heart_rate', 'Avg Resting HR', 'Resting Heart Rate'],
}


def parse_generic_csv(path: str, device_name: str = 'Wearable Device') -> dict:
    """
    Parse a generic sleep CSV export (Garmin, Samsung, manual entry).

    Column names are flexible — see GENERIC_COLUMNS for accepted headers.
    A template CSV can be downloaded from the Sleep IQ app.

    Args:
        path: Path to .csv file
        device_name: Name of the device for display

    Returns: Sleep IQ standard dict
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f'CSV file not found: {path}')

    with open(p, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return {'source': 'generic_csv', 'error': 'CSV file is empty.', 'records': []}

    headers = list(rows[0].keys())

    # Build column map: our field → actual CSV column name
    col_map = {}
    for field, candidates in GENERIC_COLUMNS.items():
        for candidate in candidates:
            if candidate in headers:
                col_map[field] = candidate
                break

    if 'date' not in col_map:
        return {'source': 'generic_csv', 'error': f'CSV must have a date column. Found columns: {headers}', 'records': []}

    def safe_float(row, field):
        col = col_map.get(field)
        if not col: return None
        val = row.get(col, '').strip()
        if not val or val == '--': return None
        if 'h' in val and 'min' in val:
            try:
                parts = val.replace('min', '').split('h')
                return float(parts[0].strip()) * 60 + float(parts[1].strip())
            except Exception: pass
        try: return float(val)
        except ValueError: return None

    records = []
    for row in rows:
        date_val = row.get(col_map['date'], '').strip()
        if not date_val:
            continue

        # Normalise date to YYYY-MM-DD
        day_key = date_val
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d'):
            try:
                day_key = datetime.strptime(date_val, fmt).strftime('%Y-%m-%d')
                break
            except ValueError:
                pass

        if day_key == date_val and '-' in date_val:
            import re
            parts = date_val.split('-')
            end_str = parts[1].strip()
            if end_str.isdigit():
                m = re.search(r'([a-zA-Z]{3,})', parts[0])
                if m: end_str = f"{m.group(1)} {end_str}"
            try:
                day_key = datetime.strptime(f"{end_str} {datetime.now().year}", '%b %d %Y').strftime('%Y-%m-%d')
            except ValueError:
                pass

        total_min = safe_float(row, 'sleep_total_min')
        spo2_avg  = safe_float(row, 'spo2_avg_pct')
        spo2_min  = safe_float(row, 'spo2_min_pct')
        hrv       = safe_float(row, 'hrv_avg_ms')

        records.append({
            'DateFormatted':   day_key,
            'sleep_total_min': total_min,
            'sleep_deep_min':  safe_float(row, 'sleep_deep_min'),
            'sleep_rem_min':   safe_float(row, 'sleep_rem_min'),
            'sleep_light_min': safe_float(row, 'sleep_light_min'),
            'sleep_score':     safe_float(row, 'sleep_score'),
            'hrv_avg_ms':      hrv,
            'spo2_avg_pct':    spo2_avg,
            'spo2_min_pct':    spo2_min,
            'resting_hr_bpm':  safe_float(row, 'resting_hr_bpm'),
            'spo2_concern':    bool(spo2_min and spo2_min < 90),
            'hrv_low':         bool(hrv and hrv < 20),
        })

    return {
        'source': 'generic_csv',
        'device': device_name,
        'records': sorted(records, key=lambda r: r.get('DateFormatted', '')),
    }


def get_csv_template() -> str:
    """Return a CSV template string for users to fill in manually."""
    headers = [
        'date', 'sleep_total_min', 'sleep_deep_min', 'sleep_rem_min',
        'sleep_light_min', 'sleep_score', 'hrv_avg_ms',
        'spo2_avg_pct', 'spo2_min_pct', 'resting_hr_bpm'
    ]
    example = [
        '2026-06-01', '450', '90', '100', '260', '78',
        '45.2', '97.1', '94.0', '62'
    ]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    w.writerow(example)
    return buf.getvalue()


# ─── Unified Stats (shared between Fitbit + Generic) ─────────────────────────

def compute_wearable_stats(data: dict, days: int = None, start_date: str = None, end_date: str = None) -> dict:
    """Compute stats from any non-CPAP wearable source (Fitbit, Garmin, etc.)"""
    records = sorted(data.get('records', []), key=lambda r: r.get('DateFormatted', ''))
    
    if start_date:
        records = [r for r in records if r.get('DateFormatted', '') >= start_date]
    if end_date:
        records = [r for r in records if r.get('DateFormatted', '') <= end_date]
        
    if days:
        records = records[-days:]
    if not records:
        return {'error': 'No records found in this date range.'}

    def avg(arr): return round(sum(arr)/len(arr), 2) if arr else None
    def med(arr):
        if not arr: return None
        s = sorted(arr); m = len(s)//2
        return round((s[m-1]+s[m])/2 if len(s)%2==0 else s[m], 2)

    hrv    = [r['hrv_avg_ms']    for r in records if r.get('hrv_avg_ms')]
    spo2   = [r['spo2_avg_pct']  for r in records if r.get('spo2_avg_pct')]
    spo2mn = [r['spo2_min_pct']  for r in records if r.get('spo2_min_pct')]
    scores = [r['sleep_score']   for r in records if r.get('sleep_score') is not None]
    deep   = [r['sleep_deep_min']for r in records if r.get('sleep_deep_min')]
    total  = [r['sleep_total_min']for r in records if r.get('sleep_total_min')]
    rhr    = [r['resting_hr_bpm']for r in records if r.get('resting_hr_bpm')]

    spo2_nights = [r for r in records if r.get('spo2_concern')]

    flags = []
    avg_spo2 = avg(spo2)
    if avg_spo2 and avg_spo2 < 93:
        flags.append('WARNING: Average SpO2 is below 93%. Please consult a healthcare provider.')
    if spo2_nights:
        flags.append(f'ATTENTION: SpO2 dropped below 90% on {len(spo2_nights)} nights. Consider a sleep study.')
    if avg(total) and avg(total) < 360:
        flags.append('WARNING: Average sleep duration under 6 hours.')

    return {
        'data_type': data.get('source', 'wearable'),
        'summary': {
            'total_days': len(records),
            'date_range': f"{records[0].get('DateFormatted','?')} to {records[-1].get('DateFormatted','?')}",
            'device': data.get('device', 'Wearable'),
        },
        'hrv':         {'average_ms': avg(hrv), 'median_ms': med(hrv)},
        'spo2':        {'average_pct': avg_spo2, 'min_recorded': min(spo2mn) if spo2mn else None,
                        'concern_nights': len(spo2_nights)},
        'heart_rate':  {'resting_avg': avg(rhr)},
        'sleep_quality': {
            'score_avg':     avg(scores),
            'deep_min_avg':  avg(deep),
            'total_hrs_avg': round(avg(total)/60,2) if avg(total) else None,
        },
        'flags': flags,
        'trend_series': {
            'dates':  [r.get('DateFormatted','') for r in records],
            'hrv':    [r.get('hrv_avg_ms') for r in records],
            'spo2':   [r.get('spo2_avg_pct') for r in records],
            'scores': [r.get('sleep_score') for r in records],
            'total_hrs': [round((r.get('sleep_total_min') or 0)/60,2) for r in records],
        },
        'recent_nights': records[-7:],
    }
