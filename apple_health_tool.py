"""
Sleep IQ — Apple Health Tool
Parses Apple Health XML exports (export.xml from iPhone/Apple Watch).

How to export:
  iPhone → Health app → Profile picture → Export All Health Data → share .zip
  Unzip → export.xml is the file we parse.

Extracts: HRV, SpO2, resting heart rate, sleep duration, sleep stages.
"""

import xml.etree.ElementTree as ET
import json
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict


RECORD_TYPES = {
    'HKQuantityTypeIdentifierHeartRateVariabilitySDNN':    'hrv_ms',
    'HKQuantityTypeIdentifierOxygenSaturation':            'spo2_pct',
    'HKQuantityTypeIdentifierRestingHeartRate':            'resting_hr',
    'HKCategoryTypeIdentifierSleepAnalysis':               'sleep_stage',
    'HKQuantityTypeIdentifierAppleSleepingWristTemperature': 'wrist_temp_c',
}

SLEEP_STAGE_VALUES = {
    'HKCategoryValueSleepAnalysisAsleepCore':   'light',
    'HKCategoryValueSleepAnalysisAsleepDeep':   'deep',
    'HKCategoryValueSleepAnalysisAsleepREM':    'rem',
    'HKCategoryValueSleepAnalysisAwake':        'awake',
    'HKCategoryValueSleepAnalysisInBed':        'in_bed',
    'HKCategoryValueSleepAnalysisAsleep':       'asleep',  # older format
}


def parse_apple_health(path: str) -> dict:
    """
    Parse Apple Health export.xml or export.zip.

    Args:
        path: Path to export.xml or the unzipped folder containing it

    Returns:
        Structured sleep data dict compatible with Sleep IQ agent
    """
    p = Path(path)

    # If zip, extract first
    if p.suffix.lower() == '.zip':
        import zipfile, tempfile
        tmp = tempfile.mkdtemp()
        with zipfile.ZipFile(p) as z:
            z.extractall(tmp)
        # Find export.xml
        xml_candidates = list(Path(tmp).rglob('export.xml'))
        if not xml_candidates:
            raise FileNotFoundError('export.xml not found inside the Apple Health ZIP.')
        xml_path = str(xml_candidates[0])
    elif p.is_dir():
        xml_candidates = list(p.rglob('export.xml'))
        if not xml_candidates:
            raise FileNotFoundError('export.xml not found in the provided folder.')
        xml_path = str(xml_candidates[0])
    else:
        xml_path = str(p)

    return _parse_xml(xml_path)


def _parse_xml(xml_path: str) -> dict:
    """Core XML parser — streams records to avoid memory issues with large exports."""
    daily = defaultdict(lambda: {
        'hrv_readings': [], 'spo2_readings': [], 'resting_hr': [],
        'sleep_minutes': {'light': 0, 'deep': 0, 'rem': 0, 'awake': 0, 'asleep': 0},
        'wrist_temp': [],
    })

    # Use iterparse to handle potentially huge XML files (can be 1GB+)
    context = ET.iterparse(xml_path, events=('start',))
    for event, elem in context:
        if elem.tag != 'Record':
            elem.clear()
            continue

        rtype = elem.get('type', '')
        field = RECORD_TYPES.get(rtype)
        if not field:
            elem.clear()
            continue

        try:
            start_str = elem.get('startDate', '')
            dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            # Key by the date the sleep session *ended* (next morning)
            day_key = dt.date().isoformat()

            if field == 'hrv_ms':
                val = float(elem.get('value', 0))
                if val > 0:
                    daily[day_key]['hrv_readings'].append(val)

            elif field == 'spo2_pct':
                val = float(elem.get('value', 0))
                if 70 <= val <= 100:
                    # Convert decimal (0.97) to percentage if needed
                    daily[day_key]['spo2_readings'].append(val if val > 1 else val * 100)

            elif field == 'resting_hr':
                val = float(elem.get('value', 0))
                if val > 0:
                    daily[day_key]['resting_hr'].append(val)

            elif field == 'sleep_stage':
                stage_val = elem.get('value', '')
                stage = SLEEP_STAGE_VALUES.get(stage_val)
                if stage:
                    end_str = elem.get('endDate', start_str)
                    end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                    minutes = (end_dt - dt).total_seconds() / 60
                    if 0 < minutes < 600:  # sanity check
                        daily[day_key]['sleep_minutes'][stage] += minutes

            elif field == 'wrist_temp_c':
                val = float(elem.get('value', 0))
                daily[day_key]['wrist_temp'].append(val)

        except (ValueError, TypeError):
            pass

        elem.clear()

    return _build_output(daily)


def _build_output(daily: dict) -> dict:
    """Convert daily aggregates into Sleep IQ standard format."""
    records = []
    for day_key in sorted(daily.keys()):
        d = daily[day_key]
        hrv_list    = d['hrv_readings']
        spo2_list   = d['spo2_readings']
        hr_list     = d['resting_hr']
        sleep_mins  = d['sleep_minutes']
        temp_list   = d['wrist_temp']

        # Skip days with no meaningful data
        total_sleep = sum(sleep_mins.values())
        if total_sleep < 30 and not hrv_list and not spo2_list:
            continue

        def safe_avg(arr): return round(sum(arr)/len(arr), 2) if arr else None
        def safe_min(arr): return round(min(arr), 2) if arr else None

        spo2_avg = safe_avg(spo2_list)
        spo2_min = safe_min(spo2_list)
        hrv_avg  = safe_avg(hrv_list)
        rhr      = safe_avg(hr_list)

        # Derive a simple sleep score (0-100)
        score = _sleep_score(hrv_avg, spo2_avg, spo2_min, rhr,
                             sleep_mins.get('deep',0), sleep_mins.get('rem',0), total_sleep)

        records.append({
            'DateFormatted': day_key,
            'hrv_avg_ms':    hrv_avg,
            'spo2_avg_pct':  spo2_avg,
            'spo2_min_pct':  spo2_min,
            'resting_hr_bpm':rhr,
            'wrist_temp_c':  safe_avg(temp_list),
            'sleep_light_min': round(sleep_mins.get('light',0)),
            'sleep_deep_min':  round(sleep_mins.get('deep',0)),
            'sleep_rem_min':   round(sleep_mins.get('rem',0)),
            'sleep_awake_min': round(sleep_mins.get('awake',0)),
            'sleep_total_min': round(total_sleep),
            'sleep_score':     score,
            # Flags for agent
            'spo2_concern':  bool(spo2_min and spo2_min < 90),
            'hrv_low':       bool(hrv_avg and hrv_avg < 20),
        })

    if not records:
        return {'source': 'apple_health', 'error': 'No sleep or HRV data found in this export.', 'records': []}

    return {
        'source': 'apple_health',
        'device': 'Apple Watch / iPhone Health',
        'records': records,
    }


def _sleep_score(hrv, spo2_avg, spo2_min, rhr, deep_min, rem_min, total_min) -> int:
    """
    Simple heuristic sleep score (0-100).
    Not a medical metric — used for intuitive display only.
    """
    score = 50  # base

    # Duration contribution (0-20 pts)
    if total_min >= 480:   score += 20
    elif total_min >= 420: score += 15
    elif total_min >= 360: score += 10
    elif total_min >= 300: score += 5

    # Deep sleep (0-15 pts) — target ≥90 min
    if deep_min >= 90:    score += 15
    elif deep_min >= 60:  score += 10
    elif deep_min >= 30:  score += 5

    # REM (0-10 pts) — target ≥90 min
    if rem_min >= 90:    score += 10
    elif rem_min >= 60:  score += 7
    elif rem_min >= 30:  score += 3

    # SpO2 (0-10 pts)
    if spo2_avg:
        if spo2_avg >= 96:   score += 10
        elif spo2_avg >= 93: score += 5
        elif spo2_avg < 90:  score -= 15  # penalty
    if spo2_min and spo2_min < 88:
        score -= 20  # significant penalty

    # HRV (0-5 pts — higher is generally better but highly individual)
    if hrv:
        if hrv >= 50:   score += 5
        elif hrv >= 30: score += 3

    return max(0, min(100, score))


def compute_apple_health_stats(data: dict, days: int = None, start_date: str = None, end_date: str = None) -> dict:
    """Compute aggregate statistics from Apple Health data for agent reasoning."""
    records = data.get('records', [])
    if not records:
        return {'error': 'No Apple Health records found.'}

    records = sorted(records, key=lambda r: r.get('DateFormatted', ''))
    
    if start_date:
        records = [r for r in records if r.get('DateFormatted', '') >= start_date]
    if end_date:
        records = [r for r in records if r.get('DateFormatted', '') <= end_date]

    if days:
        records = records[-days:]

    def avg(arr): return round(sum(arr)/len(arr), 2) if arr else None
    def med(arr):
        if not arr: return None
        s = sorted(arr)
        m = len(s)//2
        return round((s[m-1]+s[m])/2 if len(s)%2==0 else s[m], 2)

    hrv    = [r['hrv_avg_ms']    for r in records if r.get('hrv_avg_ms')]
    spo2   = [r['spo2_avg_pct']  for r in records if r.get('spo2_avg_pct')]
    spo2mn = [r['spo2_min_pct']  for r in records if r.get('spo2_min_pct')]
    rhr    = [r['resting_hr_bpm']for r in records if r.get('resting_hr_bpm')]
    scores = [r['sleep_score']   for r in records if r.get('sleep_score') is not None]
    deep   = [r['sleep_deep_min']for r in records if r.get('sleep_deep_min')]
    rem    = [r['sleep_rem_min'] for r in records if r.get('sleep_rem_min')]
    total  = [r['sleep_total_min']for r in records if r.get('sleep_total_min')]

    spo2_concern_nights = [r for r in records if r.get('spo2_concern')]
    hrv_low_nights      = [r for r in records if r.get('hrv_low')]

    avg_spo2 = avg(spo2)
    avg_hrv  = avg(hrv)

    # HRV trend
    n = len(hrv)
    if n >= 6:
        hrv_early = avg(hrv[:n//3])
        hrv_late  = avg(hrv[-n//3:])
        hrv_trend = 'improving' if hrv_late > hrv_early * 1.1 else 'declining' if hrv_late < hrv_early * 0.9 else 'stable'
    else:
        hrv_trend = 'insufficient_data'

    flags = []
    if avg_spo2 and avg_spo2 < 93:
        flags.append('WARNING: Average SpO2 is below 93%. This may warrant a medical evaluation.')
    if spo2_concern_nights:
        flags.append(f'ATTENTION: SpO2 dropped below 90% on {len(spo2_concern_nights)} nights. Consider a sleep study.')
    if avg_hrv and avg_hrv < 20:
        flags.append('INFO: HRV is consistently low, suggesting high stress or poor recovery.')
    if hrv_trend == 'declining':
        flags.append('WARNING: HRV trend is declining — sleep quality may be deteriorating.')
    if avg(total) and avg(total) < 360:
        flags.append('WARNING: Average sleep duration is under 6 hours. Chronic sleep deprivation risk.')

    return {
        'data_type': 'apple_health',
        'summary': {
            'total_days': len(records),
            'date_range': f"{records[0].get('DateFormatted','?')} to {records[-1].get('DateFormatted','?')}",
            'device': data.get('device', 'Apple Watch'),
        },
        'hrv': {
            'average_ms': avg_hrv,
            'median_ms':  med(hrv),
            'trend':      hrv_trend,
            'low_nights': len(hrv_low_nights),
        },
        'spo2': {
            'average_pct': avg_spo2,
            'min_recorded': min(spo2mn) if spo2mn else None,
            'concern_nights': len(spo2_concern_nights),
            'concern_pct':    round(len(spo2_concern_nights)/len(records)*100,1) if records else 0,
        },
        'heart_rate': {
            'resting_avg': avg(rhr),
            'resting_median': med(rhr),
        },
        'sleep_quality': {
            'score_avg':      avg(scores),
            'deep_min_avg':   avg(deep),
            'rem_min_avg':    avg(rem),
            'total_hrs_avg':  round(avg(total)/60, 2) if avg(total) else None,
        },
        'flags': flags,
        'trend_series': {
            'dates':  [r.get('DateFormatted','') for r in records],
            'hrv':    [r.get('hrv_avg_ms') for r in records],
            'spo2':   [r.get('spo2_avg_pct') for r in records],
            'scores': [r.get('sleep_score') for r in records],
            'deep':   [r.get('sleep_deep_min') for r in records],
            'total_hrs': [round((r.get('sleep_total_min') or 0)/60, 2) for r in records],
        },
        'recent_nights': records[-7:],
    }
