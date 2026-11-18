"""
Sleep IQ — Foundry Agent Orchestrator

Multi-agent reasoning pipeline using Azure AI Foundry (azure-ai-projects SDK).
Falls back gracefully to direct OpenAI API if Foundry project is not configured.

Architecture:
  User Query
    → Orchestrator Agent (Foundry)
        → [Tool] load_and_analyse_data
        → [Tool] get_recent_nights
        → [Tool] get_trend_analysis
        → [Tool] generate_doctor_report
    → Synthesized answer with cited reasoning steps
"""

import json, os, traceback, time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Import data tools ────────────────────────────────────────────────────────
from cpap_tool import load_cpap_data, compute_cpap_stats
from apple_health_tool import parse_apple_health, compute_apple_health_stats
from fitbit_csv_tool import parse_fitbit, parse_generic_csv, compute_wearable_stats


# ─── Session state (in-memory, per Flask request) ────────────────────────────
# Keyed by session_id → {'data_sources': {...}, 'multi_source': bool, '_created': ...}
_sessions: dict = {}
_SESSION_TTL = 3600  # sessions expire after 1 hour

def _evict_stale_sessions():
    """Remove sessions older than _SESSION_TTL seconds."""
    now = time.time()
    stale = [sid for sid, sess in list(_sessions.items())
             if now - sess.get('_created', 0) > _SESSION_TTL]
    for sid in stale:
        _sessions.pop(sid, None)

def _get_primary_source(sid: str) -> str:
    sess = _sessions.get(sid)
    if not sess:
        return 'unknown'
    sources = list(sess.get('data_sources', {}).keys())
    return sources[0] if sources else 'unknown'

def _is_multi_source(sid: str) -> bool:
    return len(_sessions.get(sid, {}).get('data_sources', {})) > 1

def _get_source_names(sid: str) -> list:
    return list(_sessions.get(sid, {}).get('data_sources', {}).keys())

def _get_source_stats(sid: str, source: str) -> dict:
    return _sessions.get(sid, {}).get('data_sources', {}).get(source, {}).get('stats', {})

def _get_primary_stats(sid: str) -> dict:
    primary = _get_primary_source(sid)
    return _get_source_stats(sid, primary)


# ─── Tool functions (called by the agent) ─────────────────────────────────────

def tool_get_data_summary(session_id: str, days: int = None) -> str:
    """
    Returns a comprehensive statistical summary of the user's sleep data.
    Call this first when answering any question about sleep health.

    Args:
        session_id: The current user session
        days: Number of recent days to analyse (None = all available data)

    Returns: JSON string with full statistics
    """
    if session_id not in _sessions:
        return json.dumps({'error': 'No data loaded. Please upload your sleep data first.'})

    if _is_multi_source(session_id):
        combined = {'data_type': 'multi', 'sources': {}}
        for src_name in _get_source_names(session_id):
            st = _get_source_stats(session_id, src_name)
            combined['sources'][src_name] = {
                'summary': st.get('summary', {}),
                'key_metrics': _extract_key_metrics(st, src_name),
                'flags': st.get('flags', []),
            }
        return json.dumps(combined, indent=2)

    stats = _get_primary_stats(session_id)
    return json.dumps(stats, indent=2)


def tool_get_recent_nights(session_id: str, n: int = 7) -> str:
    """
    Returns nightly detail for the last N sessions.
    Use this when the user asks about specific nights or recent trends.

    Args:
        session_id: The current user session
        n: Number of recent nights to return (default 7)

    Returns: JSON string with per-night metrics
    """
    if session_id not in _sessions:
        return json.dumps({'error': 'No data loaded.'})

    if _is_multi_source(session_id):
        result = {'sources': {}}
        for src_name in _get_source_names(session_id):
            st = _get_source_stats(session_id, src_name)
            recent = st.get('recent_nights', [])[-n:]
            result['sources'][src_name] = recent
        return json.dumps(result, indent=2)

    stats = _get_primary_stats(session_id)
    recent = stats.get('recent_nights', [])[-n:]
    return json.dumps({'recent_nights': recent, 'count': len(recent)}, indent=2)


def tool_get_trend_analysis(session_id: str) -> str:
    """
    Returns trend data suitable for identifying patterns and anomalies.
    Use this when the user asks about trends, improvements, or worsening.

    Args:
        session_id: The current user session

    Returns: JSON with trend series and computed trend direction
    """
    if session_id not in _sessions:
        return json.dumps({'error': 'No data loaded.'})

    if _is_multi_source(session_id):
        result = {'multi_source': True, 'sources': {}}
        for src_name in _get_source_names(session_id):
            st = _get_source_stats(session_id, src_name)
            trend_data = st.get('trend_series', {})
            flags = st.get('flags', [])
            result['sources'][src_name] = {
                'trend_series': trend_data,
                'flags': flags,
            }
        return json.dumps(result, indent=2)

    stats = _get_primary_stats(session_id)
    trend_data = stats.get('trend_series', {})
    flags = stats.get('flags', [])
    source = _get_primary_source(session_id)
    return json.dumps({
        'source': source,
        'trend_series': trend_data,
        'flags': flags,
        'ahi_trend': stats.get('ahi', {}).get('trend') if source == 'cpap' else None,
        'hrv_trend': stats.get('hrv', {}).get('trend') if source != 'cpap' else None,
    }, indent=2)


def tool_generate_doctor_report(session_id: str) -> str:
    """
    Generates a structured doctor-ready report.
    Call this when the user asks to 'generate a report', 'doctor summary', or 'print report'.

    Args:
        session_id: The current user session

    Returns: JSON with formatted report sections
    """
    if session_id not in _sessions:
        return json.dumps({'error': 'No data loaded.'})
    sess = _sessions[session_id]
    stats = sess.get('stats', {})
    source = sess.get('source', 'unknown')

    summary_section = stats.get('summary', {})
    flags = stats.get('flags', [])

    if source == 'cpap':
        ahi_info = stats.get('ahi', {})
        comp_info = stats.get('compliance', {})
        therapy_info = stats.get('therapy', {})
        report = {
            'title': 'Sleep IQ — CPAP Therapy Summary',
            'for_physician': True,
            'patient_data': summary_section,
            'key_metrics': {
                'Average AHI': f"{ahi_info.get('average',0)} events/hr ({ahi_info.get('severity','').upper()})",
                'AHI Trend': ahi_info.get('trend', '').capitalize(),
                'Compliance (≥4h)': f"{comp_info.get('pct_ge_4h',0)}% ({comp_info.get('status','')})",
                'Avg Usage': f"{comp_info.get('avg_usage_hours',0)} hours/night",
                'Leak Rate (P95)': f"{therapy_info.get('leak_rate_p95',0)} L/min",
                'Pressure (P95)': f"{therapy_info.get('pressure_p95',0)} cmH2O",
                'Dominant Event Type': stats.get('events',{}).get('dominant_type','').capitalize(),
            },
            'flags': flags,
            'settings_summary': therapy_info.get('settings', {}),
            'talking_points': _cpap_talking_points(stats),
            'disclaimer': 'This report was generated by Sleep IQ AI and is intended to supplement, not replace, professional medical evaluation.',
        }
    else:
        hrv_info   = stats.get('hrv', {})
        spo2_info  = stats.get('spo2', {})
        sleep_info = stats.get('sleep_quality', {})
        report = {
            'title': 'Sleep IQ — Sleep Quality Summary',
            'for_physician': False,
            'patient_data': summary_section,
            'key_metrics': {
                'Avg Sleep Score':   sleep_info.get('score_avg'),
                'Avg Sleep Duration':f"{sleep_info.get('total_hrs_avg',0)} hours",
                'Avg Deep Sleep':    f"{sleep_info.get('deep_min_avg',0)} minutes",
                'Avg HRV':          f"{hrv_info.get('average_ms',0)} ms",
                'Avg SpO2':         f"{spo2_info.get('average_pct',0)}%",
                'SpO2 Concern Nights': spo2_info.get('concern_nights', 0),
            },
            'flags': flags,
            'talking_points': _wearable_talking_points(stats),
            'disclaimer': 'This report was generated by Sleep IQ AI. SpO2 and HRV patterns that may suggest sleep apnea should be evaluated by a healthcare provider.',
        }

    return json.dumps(report, indent=2)


def _cpap_talking_points(stats: dict) -> list:
    """Generate plain-English talking points for a doctor appointment."""
    pts = []
    ahi = stats.get('ahi', {})
    comp = stats.get('compliance', {})
    therapy = stats.get('therapy', {})

    if ahi.get('severity') in ('moderate', 'severe'):
        pts.append(f"My average AHI is {ahi.get('average')} events/hr ({ahi.get('severity')} range). I'd like to discuss therapy adjustment.")
    if ahi.get('trend') == 'worsening':
        pts.append(f"My AHI has been trending worse — from {ahi.get('early_avg')} to {ahi.get('recent_avg')} events/hr recently.")
    if therapy.get('leak_concern'):
        pts.append(f"I'm experiencing high leak rates on {therapy.get('high_leak_nights')} nights. Could we review mask fit or type?")
    if comp.get('status') == 'non-compliant':
        pts.append(f"My compliance is {comp.get('pct_ge_4h')}%. I'd like strategies to improve consistent use.")
    if stats.get('events', {}).get('central_avg', 0) > 5:
        pts.append("My central apnea index is elevated. Should we investigate treatment-emergent central sleep apnea?")
    return pts


def _wearable_talking_points(stats: dict) -> list:
    """Generate talking points for a wearable user visiting a doctor."""
    pts = []
    spo2 = stats.get('spo2', {})
    hrv  = stats.get('hrv', {})
    sq   = stats.get('sleep_quality', {})

    if spo2.get('concern_nights', 0) > 0:
        pts.append(f"My smartwatch recorded {spo2.get('concern_nights')} nights where my SpO2 dropped below 90%. Could this indicate sleep apnea?")
    if spo2.get('average_pct') and spo2['average_pct'] < 93:
        pts.append(f"My average overnight SpO2 is {spo2['average_pct']}%, which seems low. Should I have a sleep study?")
    if hrv.get('average_ms') and hrv['average_ms'] < 25:
        pts.append(f"My HRV has been consistently low ({hrv['average_ms']} ms). Could this be related to poor sleep quality?")
    if sq.get('deep_min_avg') and sq['deep_min_avg'] < 45:
        pts.append(f"I'm only getting about {sq['deep_min_avg']} minutes of deep sleep per night. Is this a concern?")
    return pts


# ─── Data loading & session management ────────────────────────────────────────

def load_session_data(session_id: str, file_path: str, source_hint: str = 'auto') -> dict:
    """
    Load and analyse data for a session. Called from Flask on file upload.

    Args:
        session_id: Unique session identifier
        file_path: Path to uploaded file
        source_hint: 'cpap', 'apple_health', 'fitbit', 'csv', or 'auto'

    Returns: Summary dict for frontend display
    """
    p = Path(file_path)
    ext = p.suffix.lower()

    try:
        # Detect source (strip _demo suffix for parsing)
        parse_hint = source_hint.replace('_demo', '') if source_hint != 'auto' else 'auto'
        if parse_hint == 'auto':
            if ext in ('.edf',): parse_hint = 'cpap'
            elif ext == '.xml':  parse_hint = 'apple_health'
            elif ext == '.csv':  parse_hint = 'csv'
            elif ext == '.json': parse_hint = _sniff_json(file_path)
            elif ext == '.zip':  parse_hint = _sniff_zip(file_path)
            source_hint = parse_hint

        # Parse
        if parse_hint == 'cpap':
            raw = load_cpap_data(file_path)
            stats = compute_cpap_stats(raw)
        elif parse_hint == 'apple_health':
            raw = parse_apple_health(file_path)
            stats = compute_apple_health_stats(raw)
        elif parse_hint == 'fitbit':
            raw = parse_fitbit(file_path)
            stats = compute_wearable_stats(raw)
        elif parse_hint == 'csv':
            raw = parse_generic_csv(file_path)
            stats = compute_wearable_stats(raw)
        else:
            return {'error': f'Could not detect file type for {p.name}. Please specify source.'}

        if 'error' in stats:
            return stats

        _evict_stale_sessions()

        # Multi-source merge: if session already has data
        existing = _sessions.get(session_id)
        multi_source = False
        is_demo = source_hint.endswith('_demo')
        if existing and existing.get('data_sources'):
            existing_sources = list(existing['data_sources'].keys())

            if source_hint in existing_sources:
                # Same source type — merge records instead of replacing
                existing_records = existing['data_sources'][source_hint]['raw_data'].get('records', [])
                new_records = raw.get('records', [])
                existing_dates = {r.get('date', '') for r in existing_records}
                merged = list(existing_records)
                for r in new_records:
                    if r.get('date', '') not in existing_dates:
                        merged.append(r)
                        existing_dates.add(r.get('date', ''))
                merged.sort(key=lambda x: x.get('date', ''))
                raw['records'] = merged
                # Recompute stats on merged data
                stats = _compute_stats(raw)
                existing['data_sources'][source_hint] = {
                    'raw_data': raw, 'stats': stats, 'file_name': existing['data_sources'][source_hint]['file_name'] + ', ' + p.name, 'is_demo': is_demo or existing['data_sources'][source_hint].get('is_demo', False),
                }
                existing['_created'] = time.time()
                multi_source = len(existing['data_sources']) > 1
            else:
                # Different source type — add as new source
                existing['data_sources'][source_hint] = {
                    'raw_data': raw, 'stats': stats, 'file_name': p.name, 'is_demo': is_demo,
                }
                existing['_created'] = time.time()
                multi_source = True

            # Return source info for all sources
            sources_info = {}
            for sname, sdata in existing['data_sources'].items():
                st = sdata['stats']
                sources_info[sname] = {
                    'file_name': sdata['file_name'],
                    'record_count': len(sdata['raw_data'].get('records', [])),
                    'key_metrics': _extract_key_metrics(st, sname),
                    'is_demo': sdata.get('is_demo', False),
                }
            # Use the merged stats for the current source
            current_stats = existing['data_sources'][source_hint]['stats']
            return {
                'success': True,
                'source': source_hint,
                'multi_source': multi_source,
                'sources': sources_info,
                'summary': current_stats.get('summary', {}),
                'flags': current_stats.get('flags', []),
                'record_count': len(raw.get('records', [])),
                'key_metrics': _extract_key_metrics(current_stats, source_hint),
                'trend_series': current_stats.get('trend_series', {}),
            }

        # No existing session — create new
        is_demo = source_hint.endswith('_demo')
        display_source = source_hint.replace('_demo', '')
        _sessions[session_id] = {
            'data_sources': {
                source_hint: {
                    'raw_data': raw,
                    'stats':    stats,
                    'file_name': p.name,
                    'is_demo': is_demo,
                }
            },
            'multi_source': False,
            '_created':  time.time(),
        }

        return {
            'success': True,
            'source':  source_hint,
            'is_demo': is_demo,
            'summary': stats.get('summary', {}),
            'flags':   stats.get('flags', []),
            'record_count': len(raw.get('records', [])),
            'key_metrics': _extract_key_metrics(stats, source_hint),
            'trend_series': stats.get('trend_series', {}),
        }

    except Exception as e:
        return {'error': f'Failed to parse file: {e}', 'traceback': traceback.format_exc()}


def _compute_stats(raw_data: dict, days: int = None, start_date: str = None, end_date: str = None) -> dict:
    """Re-compute stats for a filtered time window."""
    source = raw_data.get('source', 'cpap').replace('_demo', '')
    if source == 'cpap':
        return compute_cpap_stats(raw_data, days=days, start_date=start_date, end_date=end_date)
    elif source == 'apple_health':
        return compute_apple_health_stats(raw_data, days=days, start_date=start_date, end_date=end_date)
    else:
        return compute_wearable_stats(raw_data, days=days, start_date=start_date, end_date=end_date)


def _sniff_zip(zip_path: str) -> str:
    """Peek inside a ZIP to determine source type."""
    import zipfile
    try:
        with zipfile.ZipFile(zip_path) as z:
            names = [n.lower() for n in z.namelist()]
        if any('str.edf' in n or 'identification.tgt' in n for n in names):
            return 'cpap'
        if any('export.xml' in n for n in names):
            return 'apple_health'
        if any('sleep-' in n and n.endswith('.json') for n in names):
            return 'fitbit'
    except Exception:
        pass
    return 'unknown'


def _sniff_json(json_path: str) -> str:
    """Peek inside a JSON file to check if it's CPAP data vs Fitbit."""
    import json as _json
    try:
        with open(json_path, encoding='utf-8') as f:
            top = _json.load(f)
        # CPAP data has 'device' and 'patient' and 'records' at top level
        if isinstance(top, dict):
            keys = set(top.keys())
            cpap_signals = {'device', 'patient', 'records'}
            if cpap_signals.issubset(keys):
                return 'cpap'
        # Fitbit data is a list or has 'sleep' key
        return 'fitbit'
    except Exception:
        pass
    return 'fitbit'


def _extract_key_metrics(stats: dict, source: str) -> dict:
    """Pull the most important numbers for the dashboard cards."""
    base = source.replace('_demo', '')
    if base == 'cpap':
        return {
            'ahi':        stats.get('ahi', {}).get('average'),
            'severity':   stats.get('ahi', {}).get('severity'),
            'compliance': stats.get('compliance', {}).get('pct_ge_4h'),
            'usage_hrs':  stats.get('compliance', {}).get('avg_usage_hours'),
            'leak_p95':   stats.get('therapy', {}).get('leak_rate_p95'),
            'trend':      stats.get('ahi', {}).get('trend'),
        }
    else:
        return {
            'sleep_score': stats.get('sleep_quality', {}).get('score_avg'),
            'hrv_ms':      stats.get('hrv', {}).get('average_ms'),
            'spo2_avg':    stats.get('spo2', {}).get('average_pct'),
            'deep_min':    stats.get('sleep_quality', {}).get('deep_min_avg'),
            'total_hrs':   stats.get('sleep_quality', {}).get('total_hrs_avg'),
        }


def has_session(session_id: str) -> bool:
    _evict_stale_sessions()
    return session_id in _sessions


def get_session_source(session_id: str) -> str:
    if _is_multi_source(session_id):
        return 'multi'
    return _get_primary_source(session_id)


def get_session_sources_info(session_id: str) -> dict:
    """Return info about all data sources in the session."""
    sess = _sessions.get(session_id)
    if not sess:
        return {}
    ds = sess.get('data_sources', {})
    return {sname: {'file_name': sdata.get('file_name', ''), 'is_demo': sdata.get('is_demo', False)}
            for sname, sdata in ds.items()}


def remove_data_source(session_id: str, source: str) -> bool:
    """Remove a specific data source from the session."""
    sess = _sessions.get(session_id)
    if not sess or source not in sess.get('data_sources', {}):
        return False
    del sess['data_sources'][source]
    sess['_created'] = time.time()
    return True


def clear_session_data(session_id: str) -> bool:
    """Clear all data for a session."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


# ─── Azure AI Foundry Agent ───────────────────────────────────────────────────

def _build_system_prompt(source: str, user_message: str = '') -> str:
    if source == 'multi':
        data_context = (
            "The user has uploaded multiple data sources: CPAP therapy data AND smartwatch data. "
            "You have access to clinical CPAP metrics (AHI, compliance, leak rate, event indices, pressure) "
            "AND consumer wearable metrics (sleep stages, HRV, SpO2, sleep score, resting heart rate). "
            "Use the get_data_summary, get_trend_analysis, and generate_doctor_report tools "
            "to correlate across both sources. Look for patterns like: "
            "low HRV nights matching high AHI nights, or SpO2 drops correlating with apnea events. "
            "You can provide uniquely valuable cross-source insights."
        )
    else:
        source_base = source.replace('_demo', '')
        data_context = (
            "The user has CPAP therapy data from a ResMed device. "
            "You have access to AHI, compliance, leak rate, event indices (obstructive, central, hypopnea), "
            "pressure data, and multi-month trends."
            if source_base == 'cpap' else
            "The user has smartwatch sleep data. "
            "You have access to sleep stages (deep/REM/light), HRV, SpO2, sleep score, and resting heart rate."
        )

    # Ground with medical knowledge via Foundry IQ
    from foundry_iq import build_knowledge_context
    knowledge_context = build_knowledge_context(user_message or 'sleep health guidelines ahi compliance leak rate')

    return f"""You are Sleep IQ, an AI sleep health companion. You reason carefully over sleep data to provide
clear, grounded, compassionate insights. You are NOT a replacement for medical advice.

{data_context}

{knowledge_context}

RULES:
1. Always use the available tools before answering quantitative questions.
2. Cite your reasoning steps clearly — show how you arrived at your conclusion.
3. When SpO2 or AHI suggest serious concerns, recommend professional consultation.
4. Never diagnose. Use language like "this may suggest", "according to AASM guidelines", "worth discussing with your doctor".
5. Be warm and human. This is someone's health data — treat it with care.
6. For trend questions, use get_trend_analysis tool first.
7. For specific nights, use get_recent_nights tool.
8. For doctor report requests, use generate_doctor_report tool.
9. When citing medical knowledge, include the source name from the grounded knowledge context.
"""


TOOLS_SCHEMA = [
    {
        'type': 'function',
        'function': {
            'name': 'get_data_summary',
            'description': 'Get comprehensive statistics from the loaded sleep data. Call this first for any health question.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'days': {
                        'type': 'integer',
                        'description': 'Limit analysis to last N days. Omit for all data.'
                    }
                },
                'required': []
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_recent_nights',
            'description': 'Get per-night detail for the most recent sessions.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'n': {'type': 'integer', 'description': 'Number of recent nights (default 7)'}
                },
                'required': []
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_trend_analysis',
            'description': 'Get trend data and direction for AHI, HRV, SpO2, and flags.',
            'parameters': {'type': 'object', 'properties': {}, 'required': []}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'generate_doctor_report',
            'description': 'Generate a structured report suitable for a doctor appointment.',
            'parameters': {'type': 'object', 'properties': {}, 'required': []}
        }
    },
]


def run_agent(session_id: str, user_message: str, chat_history: list = None) -> dict:
    """
    Run the Sleep IQ reasoning agent.

    Priority order:
      1. Azure AI Foundry (PRIMARY — Microsoft AI stack required for Agents League)
      2. Azure OpenAI (if AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT set)
      3. OpenRouter (non-Microsoft fallback for local dev)
      4. Direct OpenAI (final fallback)

    Args:
        session_id:    Current session
        user_message:  User's question
        chat_history:  Previous messages [{'role': ..., 'content': ...}]

    Returns:
        {'answer': str, 'tool_calls': list, 'reasoning_steps': list}
    """
    if not has_session(session_id):
        return {
            'answer': "Please upload your sleep data first — I don't see any data loaded for this session.",
            'tool_calls': [],
            'reasoning_steps': [],
        }

    source = get_session_source(session_id)
    system_prompt = _build_system_prompt(source, user_message)
    history = chat_history or []

    # 1. Azure AI Foundry (PRIMARY — Microsoft AI stack for Agents League competition)
    conn_str = os.getenv('AZURE_AI_PROJECT_CONNECTION_STRING', '')
    if conn_str and ';' in conn_str:
        return _run_foundry_agent(session_id, user_message, history, system_prompt)

    # 2. Azure OpenAI (Microsoft stack — preferred over non-Microsoft providers)
    az_key = os.getenv('AZURE_OPENAI_API_KEY', '')
    az_ep = os.getenv('AZURE_OPENAI_ENDPOINT', '')
    if az_key and az_ep:
        return _run_openai_agent(session_id, user_message, history, system_prompt)

    # 3. OpenRouter (non-Microsoft fallback for local dev without Azure)
    or_key = os.getenv('GEMINI_API_KEY', '')
    if or_key:
        return _run_openrouter_agent(session_id, user_message, history, system_prompt)

    # 4. Direct OpenAI (final fallback)
    return _run_openai_agent(session_id, user_message, history, system_prompt)



def _dispatch_tool(session_id: str, tool_name: str, args: dict) -> str:
    """Route tool calls to the correct Python function."""
    if tool_name == 'get_data_summary':
        return tool_get_data_summary(session_id, args.get('days'))
    elif tool_name == 'get_recent_nights':
        return tool_get_recent_nights(session_id, args.get('n', 7))
    elif tool_name == 'get_trend_analysis':
        return tool_get_trend_analysis(session_id)
    elif tool_name == 'generate_doctor_report':
        return tool_generate_doctor_report(session_id)
    return json.dumps({'error': f'Unknown tool: {tool_name}'})



def _run_openrouter_agent(session_id, user_message, history, system_prompt) -> dict:
    """OpenRouter agent — uses OpenAI-compatible API. Primary path when OPENROUTER_API_KEY is set."""
    from openai import OpenAI

    api_key  = os.getenv('GEMINI_API_KEY')
    model    = os.getenv('AI_MODEL', 'gemini-3.5-flash')
    base_url = os.getenv('AI_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai')

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        default_headers={
            'HTTP-Referer': 'https://github.com/sleepiq',
            'X-Title': 'Sleep IQ',
        }
    )

    messages = [{'role': 'system', 'content': system_prompt}]
    messages += history[-10:]
    messages.append({'role': 'user', 'content': user_message})

    tool_calls_log = []
    reasoning_steps = []
    max_rounds = 5

    for _ in range(max_rounds):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice='auto',
            )
        except Exception as e:
            # Some free models don't support tool_choice — retry without tools
            print(f'[OpenRouter] Tool call failed ({e}), retrying without tools.')
            try:
                # Inject data summary directly into the prompt as context
                ctx = tool_get_data_summary(session_id)
                messages_no_tools = [{'role': 'system', 'content': system_prompt + '\n\nDATA CONTEXT:\n' + ctx}]
                messages_no_tools += history[-6:]
                messages_no_tools.append({'role': 'user', 'content': user_message})
                resp2 = client.chat.completions.create(model=model, messages=messages_no_tools)
                return {
                    'answer': resp2.choices[0].message.content,
                    'tool_calls': [],
                    'reasoning_steps': ['[Context injected directly — model does not support tool calls]'],
                }
            except Exception as e2:
                return {'answer': f'AI service error: {e2}', 'tool_calls': [], 'reasoning_steps': []}

        msg = response.choices[0].message

        if not getattr(msg, 'tool_calls', None):
            return {
                'answer': msg.content or 'No response generated.',
                'tool_calls': tool_calls_log,
                'reasoning_steps': reasoning_steps,
            }

        messages.append({'role': 'assistant', 'content': msg.content or '', 'tool_calls': [
            {'id': tc.id, 'type': 'function', 'function': {'name': tc.function.name, 'arguments': tc.function.arguments}}
            for tc in msg.tool_calls
        ]})

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments or '{}')
            result  = _dispatch_tool(session_id, fn_name, fn_args)

            tool_calls_log.append({'tool': fn_name, 'args': fn_args})
            reasoning_steps.append(f'Called {fn_name}')

            messages.append({
                'role': 'tool',
                'tool_call_id': tc.id,
                'content': result,
            })

    return {
        'answer': 'I reached the maximum reasoning steps. Please try rephrasing your question.',
        'tool_calls': tool_calls_log,
        'reasoning_steps': reasoning_steps,
    }


def _run_openai_agent(session_id, user_message, history, system_prompt) -> dict:

    """AI agent loop supporting OpenRouter, Azure OpenAI, or direct OpenAI."""
    from openai import AzureOpenAI, OpenAI

    api_key     = os.getenv('OPENAI_API_KEY', '')
    az_key      = os.getenv('AZURE_OPENAI_API_KEY', '')
    az_ep       = os.getenv('AZURE_OPENAI_ENDPOINT', '')
    or_key      = os.getenv('GEMINI_API_KEY', '')
    or_model    = os.getenv('AI_MODEL', 'gemini-3.5-flash')
    or_base     = os.getenv('AI_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai')
    model       = os.getenv('AZURE_AI_MODEL_DEPLOYMENT', 'gpt-4o')

    if az_key and az_ep:
        client = AzureOpenAI(api_key=az_key, azure_endpoint=az_ep, api_version='2024-12-01-preview')
    elif or_key:
        client = OpenAI(api_key=or_key, base_url=or_base)
        model = or_model
    elif api_key:
        client = OpenAI(api_key=api_key)
        model = 'gpt-4o'
    else:
        return {'answer': 'No AI API key configured. Set OPENROUTER_API_KEY, OPENAI_API_KEY, or AZURE_OPENAI_API_KEY in .env', 'tool_calls': [], 'reasoning_steps': []}

    messages = [{'role': 'system', 'content': system_prompt}]
    messages += history[-10:]  # keep last 10 turns for context
    messages.append({'role': 'user', 'content': user_message})

    tool_calls_log = []
    reasoning_steps = []
    max_rounds = 5

    # Some free-tier models don't support tools — try tools first, fall back gracefully
    for _ in range(max_rounds):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice='auto',
            )
        except Exception as tool_err:
            # Model may not support tools — retry without tools
            reasoning_steps.append(f'Tool calling unavailable ({tool_err}); using direct response.')
            response = client.chat.completions.create(
                model=model,
                messages=messages,
            )
            msg = response.choices[0].message
            return {
                'answer': msg.content or 'I had trouble processing that. Could you rephrase?',
                'tool_calls': tool_calls_log,
                'reasoning_steps': reasoning_steps,
            }

        msg = response.choices[0].message

        if not getattr(msg, 'tool_calls', None):
            return {
                'answer': msg.content,
                'tool_calls': tool_calls_log,
                'reasoning_steps': reasoning_steps,
            }

        messages.append(msg)
        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments or '{}')
            result  = _dispatch_tool(session_id, fn_name, fn_args)

            tool_calls_log.append({'tool': fn_name, 'args': fn_args})
            reasoning_steps.append(f"Called **{fn_name}**({fn_args})")

            messages.append({
                'role': 'tool',
                'tool_call_id': tc.id,
                'content': result,
            })

    return {
        'answer': 'I reached the maximum reasoning steps. Please try rephrasing your question.',
        'tool_calls': tool_calls_log,
        'reasoning_steps': reasoning_steps,
    }


def _run_foundry_agent(session_id, user_message, history, system_prompt) -> dict:
    """Azure AI Foundry agent (primary path when project is configured)."""
    foundry_tried = False
    agent_id = None
    thread_id = None
    try:
        from azure.ai.projects import AIProjectClient
        from azure.ai.projects.models import FunctionTool, ToolSet
        from azure.identity import DefaultAzureCredential

        conn_str = os.getenv('AZURE_AI_PROJECT_CONNECTION_STRING')
        model    = os.getenv('AZURE_AI_MODEL_DEPLOYMENT', 'gpt-4o')

        client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=conn_str,
        )

        def get_data_summary(days: int = None) -> str:
            return tool_get_data_summary(session_id, days)
        def get_recent_nights(n: int = 7) -> str:
            return tool_get_recent_nights(session_id, n)
        def get_trend_analysis() -> str:
            return tool_get_trend_analysis(session_id)
        def generate_doctor_report() -> str:
            return tool_generate_doctor_report(session_id)

        toolset = ToolSet()
        toolset.add(FunctionTool({get_data_summary, get_recent_nights, get_trend_analysis, generate_doctor_report}))

        agent = client.agents.create_agent(
            model=model,
            name='sleep-iq-agent',
            instructions=system_prompt,
            toolset=toolset,
        )
        foundry_tried = True
        agent_id = agent.id

        thread = client.agents.create_thread()
        thread_id = thread.id

        for h in history[-6:]:
            client.agents.create_message(thread_id=thread.id, role=h['role'], content=h['content'])

        client.agents.create_message(thread_id=thread.id, role='user', content=user_message)
        run = client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)

        messages = client.agents.list_messages(thread_id=thread.id)
        answer = next((m.content[0].text.value for m in messages.data
                       if m.role == 'assistant' and m.content), 'No response generated.')

        return {'answer': answer, 'tool_calls': [], 'reasoning_steps': ['Used Azure AI Foundry agent']}

    except Exception as e:
        print(f'[Sleep IQ] Foundry agent failed ({e}), falling back to OpenAI.')
        return _run_openai_agent(session_id, user_message, history, system_prompt)

    finally:
        if foundry_tried and client:
            try:
                if thread_id:
                    client.agents.delete_thread(thread_id)
            except Exception:
                pass
            try:
                if agent_id:
                    client.agents.delete_agent(agent_id)
            except Exception:
                pass
