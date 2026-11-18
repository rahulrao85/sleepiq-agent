"""
Sleep IQ — Flask Application
Routes, file upload handling, and API endpoints.
"""

import os, uuid, json, tempfile, zipfile, time, functools
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string, session
from dotenv import load_dotenv
from orchestrator import load_session_data, run_agent, has_session

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
if not app.secret_key:
    app.secret_key = os.urandom(64)
    import warnings
    warnings.warn('FLASK_SECRET_KEY not set — using ephemeral key (sessions invalidated on restart)')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB
app.config['MAX_FORM_MEMORY_SIZE'] = 256 * 1024  # 256 KB form data limit
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.permanent_session_lifetime = 3600  # session cookie expires in 1 hour

UPLOAD_DIR = Path(tempfile.gettempdir()) / 'sleepiq_uploads'
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'.edf', '.json', '.xml', '.csv', '.zip'}

# ─── In-memory rate limiter (simple per-IP, per-endpoint) ─────────────────────

_RATE_LIMITS = {}  # (endpoint, ip) -> [timestamps]

def rate_limit(max_requests: int = 20, window: int = 60):
    """Decorator: max_requests per IP per `window` seconds."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = (request.endpoint, request.remote_addr or 'local')
            now = time.time()
            hits = _RATE_LIMITS.get(key, [])
            hits = [t for t in hits if now - t < window]
            if len(hits) >= max_requests:
                return jsonify({'error': 'Too many requests. Please wait before trying again.'}), 429
            hits.append(now)
            _RATE_LIMITS[key] = hits
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_session_id():
    session.permanent = True
    if 'sid' not in session:
        session['sid'] = str(uuid.uuid4())
    return session['sid']

def allowed(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    from ui_template import PAGE_HTML
    return render_template_string(PAGE_HTML)

@app.route('/api/upload', methods=['POST'])
@rate_limit(max_requests=10, window=60)
def upload():
    sid = get_session_id()
    f = request.files.get('file')
    if not f or not f.filename:
        return jsonify({'error': 'No file provided.'}), 400
    if not allowed(f.filename):
        return jsonify({'error': f'Unsupported file type. Accepted: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    source_hint = request.form.get('source', 'auto')
    save_path = UPLOAD_DIR / f'{uuid.uuid4()}_{Path(f.filename).name}'
    f.save(str(save_path))

    try:
        result = load_session_data(str(sid), str(save_path), source_hint)
    finally:
        try: save_path.unlink()
        except: pass

    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result)

@app.route('/api/chat', methods=['POST'])
@rate_limit(max_requests=30, window=60)
def chat():
    sid = get_session_id()
    body = request.get_json(force=True) or {}
    message  = (body.get('message') or '').strip()
    history  = body.get('history', [])

    if not message:
        return jsonify({'error': 'Empty message.'}), 400
    if len(message) > 4000:
        return jsonify({'error': 'Message too long (max 4000 characters).'}), 400
    if not has_session(str(sid)):
        return jsonify({'answer': 'Please upload your sleep data first — click the upload button to get started.', 'tool_calls': [], 'reasoning_steps': []})

    result = run_agent(str(sid), message, history)
    return jsonify(result)

@app.route('/api/csv-template')
def csv_template():
    from fitbit_csv_tool import get_csv_template
    from flask import Response
    return Response(get_csv_template(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=sleepiq_template.csv'})

@app.route('/api/status')
def status():
    sid = get_session_id()
    from orchestrator import get_session_source
    src = get_session_source(str(sid))
    return jsonify({'has_data': has_session(str(sid)), 'session_id': str(sid), 'source': src})

@app.route('/api/session-data')
def session_data():
    sid = get_session_id()
    if not has_session(str(sid)):
        return jsonify({'error': 'No active session.'}), 404
    from orchestrator import _sessions, _is_multi_source, _get_primary_source, get_session_sources_info, _get_source_stats, _extract_key_metrics
    sess = _sessions[str(sid)]
    is_multi = _is_multi_source(str(sid))
    primary = _get_primary_source(str(sid))
    
    sources_info = {}
    if is_multi:
        for sname, sdata in sess['data_sources'].items():
            st = sdata['stats']
            sources_info[sname] = {
                'file_name': sdata['file_name'],
                'record_count': len(sdata['raw_data'].get('records', [])),
                'key_metrics': _extract_key_metrics(st, sname),
                'is_demo': sdata.get('is_demo', False),
            }
            
    primary_sdata = sess['data_sources'][primary]
    primary_stats = primary_sdata['stats']
    
    return jsonify({
        'success': True,
        'source': primary,
        'is_demo': primary_sdata.get('is_demo', False),
        'multi_source': is_multi,
        'sources': sources_info,
        'summary': primary_stats.get('summary', {}),
        'flags': primary_stats.get('flags', []),
        'record_count': len(primary_sdata['raw_data'].get('records', [])),
        'key_metrics': _extract_key_metrics(primary_stats, primary),
        'trend_series': primary_stats.get('trend_series', {}),
    })


@app.route('/api/source-data')
def source_data():
    sid = get_session_id()
    source = request.args.get('source', '')
    days_str = request.args.get('days', '')
    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')

    if not source or not has_session(str(sid)):
        return jsonify({'error': 'No data.'}), 400
    from orchestrator import _get_source_stats, _extract_key_metrics, _sessions, _compute_stats
    
    sess = _sessions.get(str(sid))
    if not sess or source not in sess.get('data_sources', {}):
        return jsonify({'error': 'Source not found.'}), 404
        
    sdata = sess['data_sources'][source]
    
    if days_str or start_date or end_date:
        days = int(days_str) if days_str and days_str.isdigit() else None
        stats = _compute_stats(sdata['raw_data'], days=days, start_date=start_date, end_date=end_date)
        if 'error' in stats:
            stats = sdata['stats'] # fallback
    else:
        stats = sdata['stats']

    return jsonify({
        'source': source,
        'key_metrics': _extract_key_metrics(stats, source),
        'trend_series': stats.get('trend_series', {}),
        'flags': stats.get('flags', []),
        'summary': stats.get('summary', {}),
    })

# ─── Demo data loader (synthetic cpap_data.json: no real person or device) ────────────

@app.route('/api/load-demo', methods=['POST'])
@rate_limit(max_requests=5, window=60)
def load_demo():
    sid = get_session_id()
    candidates = [
        Path(__file__).parent / 'cpap_data.json',
        Path(__file__).parent.parent / 'Sleep Data' / 'cpap_data.json',
    ]
    demo_path = next((p for p in candidates if p.exists()), None)
    if not demo_path:
        # If no real CPAP data, load wearable demo as fallback
        wearable = Path(__file__).parent / 'wearable_demo_data.json'
        if wearable.exists():
            result = load_session_data(str(sid), str(wearable), 'fitbit')
            if 'error' not in result:
                return jsonify(result)
        return jsonify({'error': 'Demo data file not found. Place cpap_data.json next to app.py.'}), 404

    result = load_session_data(str(sid), str(demo_path), 'cpap_demo')
    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result)

@app.route('/api/load-wearable-demo', methods=['POST'])
@rate_limit(max_requests=5, window=60)
def load_wearable_demo():
    sid = get_session_id()
    demo_path = Path(__file__).parent / 'wearable_demo_data.json'
    if not demo_path.exists():
        return jsonify({'error': 'Wearable demo data file not found.'}), 404

    result = load_session_data(str(sid), str(demo_path), 'fitbit_demo')
    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result)

@app.route('/api/remove-source', methods=['POST'])
@rate_limit(max_requests=20, window=60)
def remove_source():
    sid = get_session_id()
    body = request.get_json(force=True) or {}
    source = body.get('source', '')
    from orchestrator import remove_data_source, get_session_sources_info, _get_primary_source
    if not source or not remove_data_source(str(sid), source):
        return jsonify({'error': 'Source not found.'}), 404
    remaining = get_session_sources_info(str(sid))
    return jsonify({'success': True, 'remaining_sources': remaining, 'has_data': bool(remaining)})

@app.route('/api/clear-data', methods=['POST'])
@rate_limit(max_requests=10, window=60)
def clear_data():
    sid = get_session_id()
    from orchestrator import clear_session_data
    clear_session_data(str(sid))
    return jsonify({'success': True, 'has_data': False})

if __name__ == '__main__':
    import webbrowser
    from threading import Timer
    port = int(os.getenv('FLASK_PORT', 5000))
    print(f'\n  [Sleep IQ] Starting on http://localhost:{port}\n')
    Timer(1.5, lambda: webbrowser.open(f'http://localhost:{port}')).start()
    app.run(host='0.0.0.0', port=port, debug=False)
