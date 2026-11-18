PAGE_HTML = r"""
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sleep IQ — AI Sleep Companion</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #080b16;
    --bg2: #0f1225;
    --bg3: #161a30;
    --bg4: #1e2340;
    --border: rgba(99,115,199,.18);
    --text: #e8ecf8;
    --text2: #8b93b8;
    --accent: #7b8fff;
    --accent2: #5e6fe8;
    --accent-glow: rgba(123,143,255,.15);
    --green: #34d399;
    --yellow: #fbbf24;
    --red: #f87171;
    --orange: #fb923c;
    --radius: 16px;
    --radius-sm: 10px;
    --shadow: 0 8px 32px rgba(0,0,0,.5);
    --glass: rgba(22,26,48,.65);
    --glass-border: rgba(99,115,199,.12);
    --gradient-accent: linear-gradient(135deg, #7b8fff 0%, #a78bfa 50%, #c084fc 100%);
    --gradient-card: linear-gradient(145deg, rgba(22,26,48,.8), rgba(14,17,37,.9));
    --font: 'Inter', system-ui, -apple-system, sans-serif;
  }
  :root[data-theme="light"] {
    --bg: #f0f2f8;
    --bg2: #ffffff;
    --bg3: #f6f7fb;
    --bg4: #ebedf5;
    --border: rgba(100,116,190,.15);
    --text: #1a1d35;
    --text2: #5a6088;
    --accent: #5e6fe8;
    --accent2: #4858c8;
    --accent-glow: rgba(94,111,232,.1);
    --shadow: 0 4px 24px rgba(0,0,0,.06);
    --glass: rgba(255,255,255,.7);
    --glass-border: rgba(100,116,190,.1);
    --gradient-accent: linear-gradient(135deg, #5e6fe8 0%, #8b7cf6 50%, #a78bfa 100%);
    --gradient-card: linear-gradient(145deg, rgba(255,255,255,.9), rgba(246,247,251,.95));
  }
  @media (prefers-color-scheme: light) {
    :root:not([data-theme="dark"]):not([data-theme="light"]) { --bg: #f0f2f8; --bg2: #ffffff; --bg3: #f6f7fb; --bg4: #ebedf5; --border: rgba(100,116,190,.15); --text: #1a1d35; --text2: #5a6088; --accent: #5e6fe8; --accent2: #4858c8; --accent-glow: rgba(94,111,232,.1); --shadow: 0 4px 24px rgba(0,0,0,.06); --glass: rgba(255,255,255,.7); --glass-border: rgba(100,116,190,.1); --gradient-accent: linear-gradient(135deg, #5e6fe8 0%, #8b7cf6 50%, #a78bfa 100%); --gradient-card: linear-gradient(145deg, rgba(255,255,255,.9), rgba(246,247,251,.95)); }
  }
  html, body { height: 100%; background: var(--bg); color: var(--text); font-family: var(--font); font-weight: 400; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
  body { display: flex; overflow: hidden; }

  /* ─── Left Panel (Upload / Dashboard) ─── */
  .left-panel {
    flex: 1; min-width: 0;
    display: flex; flex-direction: column;
    border-right: 1px solid var(--glass-border);
  }
  .left-header {
    display: flex; align-items: center; gap: 14px;
    padding: 20px 28px;
    border-bottom: 1px solid var(--border);
    background: var(--bg2);
    flex-shrink: 0;
    position: relative;
  }
  .left-header::after {
    content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 1px;
    background: var(--gradient-accent); opacity: .4;
  }
  .left-header .logo {
    width: 44px; height: 44px;
    background: var(--gradient-accent);
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; font-weight: 700; color: #fff;
    box-shadow: 0 4px 16px rgba(123,143,255,.3);
    transition: transform .2s, box-shadow .2s;
  }
  .left-header .logo:hover { transform: scale(1.05); box-shadow: 0 6px 24px rgba(123,143,255,.4); }
  .left-header h1 { font-size: 21px; font-weight: 700; letter-spacing: -.02em; background: var(--gradient-accent); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  .left-header .sub { font-size: 12px; color: var(--text2); margin-top: 2px; font-weight: 400; letter-spacing: .02em; }
  .left-header .header-actions {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .left-header .badge {
    background: var(--accent-glow); color: var(--accent);
    padding: 5px 14px; border-radius: 20px; font-size: 11px; font-weight: 500;
    border: 1px solid var(--glass-border);
  }

  /* ─── Upload Screen ─── */
  .upload-screen {
    flex: 1; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 40px 24px; gap: 20px;
  }
  .upload-screen.hidden { display: none; }
  .upload-icon {
    width: 96px; height: 96px; border-radius: 50%;
    background: var(--glass); border: 2px dashed var(--border);
    display: flex; align-items: center; justify-content: center;
    font-size: 42px; color: var(--text2); transition: all .3s ease;
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  }
  .upload-screen.drag .upload-icon {
    border-color: var(--accent); background: var(--accent-glow); color: var(--accent);
    transform: scale(1.08); box-shadow: 0 0 40px rgba(123,143,255,.2);
  }
  .upload-screen h2 { font-size: 22px; font-weight: 600; letter-spacing: -.01em; }
  .upload-screen p { color: var(--text2); font-size: 14px; text-align: center; max-width: 420px; line-height: 1.6; }
  .upload-btn {
    background: var(--gradient-accent); color: #fff; border: none;
    padding: 14px 36px; border-radius: var(--radius); font-size: 15px;
    cursor: pointer; transition: all .3s ease; font-weight: 600;
    box-shadow: 0 4px 20px rgba(123,143,255,.3);
    letter-spacing: .01em;
  }
  .upload-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(123,143,255,.4); }
  .upload-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
  .demo-btn {
    background: transparent; color: var(--accent); border: 1px solid var(--border);
    padding: 12px 28px; border-radius: var(--radius); font-size: 14px;
    cursor: pointer; transition: all .3s ease; font-weight: 500;
    backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
  }
  .demo-btn:hover { border-color: var(--accent); background: var(--accent-glow); transform: translateY(-1px); }
  .upload-formats { font-size: 12px; color: var(--text2); margin-top: 8px; font-weight: 400; }
  .upload-progress { display: none; width: 100%; max-width: 400px; }
  .upload-progress.active { display: block; }
  .upload-progress .bar {
    height: 4px; background: var(--bg3); border-radius: 4px; overflow: hidden;
  }
  .upload-progress .bar-fill {
    height: 100%; width: 0; background: var(--gradient-accent); border-radius: 4px;
    transition: width .3s ease;
  }
  .upload-error { color: var(--red); font-size: 13px; display: none; margin-top: 8px; font-weight: 500; }

  /* ─── Dashboard (hidden until data loaded) ─── */
  .dashboard { flex: 1; display: none; flex-direction: column; overflow: hidden; }
  .dashboard.active { display: flex; }
  .dash-scroll { flex: 1; overflow-y: auto; padding: 24px 28px; }
  .dash-scroll::-webkit-scrollbar { width: 6px; }
  .dash-scroll::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

  .metrics-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 14px; margin-bottom: 24px;
  }
  .metric-card {
    background: var(--gradient-card); border: 1px solid var(--glass-border);
    border-radius: var(--radius); padding: 20px;
    backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
    transition: all .3s ease; position: relative; overflow: hidden;
  }
  .metric-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: var(--gradient-accent); opacity: 0; transition: opacity .3s ease;
  }
  .metric-card:hover { transform: translateY(-2px); box-shadow: var(--shadow); }
  .metric-card:hover::before { opacity: 1; }
  .metric-card .label { font-size: 11px; text-transform: uppercase; letter-spacing: .06em; color: var(--text2); margin-bottom: 8px; font-weight: 500; }
  .metric-card .value { font-size: 28px; font-weight: 700; letter-spacing: -.02em; }
  .metric-card .value .unit { font-size: 13px; font-weight: 400; color: var(--text2); margin-left: 3px; }
  .metric-card .sub { font-size: 12px; margin-top: 6px; font-weight: 500; }
  .metric-card .sub.good { color: var(--green); }
  .metric-card .sub.warn { color: var(--yellow); }
  .metric-card .sub.bad { color: var(--red); }

  .chart-wrapper {
    background: var(--gradient-card); border: 1px solid var(--glass-border);
    border-radius: var(--radius); padding: 24px; margin-bottom: 20px;
    backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
    transition: box-shadow .3s ease;
  }
  .chart-wrapper:hover { box-shadow: 0 4px 24px rgba(0,0,0,.15); }
  .chart-wrapper .chart-header {
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;
  }
  .chart-wrapper .chart-header h3 { font-size: 15px; font-weight: 600; letter-spacing: -.01em; }
  .chart-range {
    display: flex; gap: 4px;
  }
  .chart-range button {
    background: transparent; color: var(--text2); border: 1px solid transparent;
    padding: 5px 12px; border-radius: 8px; font-size: 12px; cursor: pointer; transition: all .2s ease; font-weight: 500;
  }
  .chart-range button:hover { color: var(--text); border-color: var(--border); }
  .chart-range button.active { background: var(--accent-glow); color: var(--accent); border-color: rgba(123,143,255,.3); }
  .chart-container { position: relative; height: 220px; }

  .flags-box {
    background: var(--gradient-card); border: 1px solid var(--glass-border);
    border-radius: var(--radius); padding: 20px;
    backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  }
  .flags-box h3 { font-size: 15px; font-weight: 600; margin-bottom: 12px; letter-spacing: -.01em; }
  .flag-item {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 10px 0; border-bottom: 1px solid var(--border); font-size: 13px; line-height: 1.5;
  }
  .flag-item:last-child { border-bottom: none; }
  .flag-item .icon { flex-shrink: 0; }
  .source-tag {
    display: inline-block; background: var(--accent-glow); color: var(--accent);
    padding: 4px 12px; border-radius: 14px; font-size: 11px; margin-bottom: 14px;
    font-weight: 500; border: 1px solid var(--glass-border);
  }

  /* ─── Right Panel (Chat) ─── */
  .right-panel {
    width: 440px; min-width: 380px; max-width: 520px;
    display: flex; flex-direction: column;
    background: var(--bg2);
    border-left: 1px solid var(--glass-border);
  }
  .chat-header {
    display: flex; align-items: center; gap: 12px;
    padding: 20px 24px;
    border-bottom: 1px solid var(--border);
    background: var(--bg2); flex-shrink: 0;
    position: relative;
  }
  .chat-header::after {
    content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 1px;
    background: var(--gradient-accent); opacity: .25;
  }
  .chat-header h2 { font-size: 16px; font-weight: 600; letter-spacing: -.01em; }
  .chat-header .status {
    margin-left: auto; font-size: 11px; color: var(--text2);
    display: flex; align-items: center; gap: 6px; font-weight: 500;
  }
  .chat-header .status .dot {
    width: 8px; height: 8px; border-radius: 50%; background: var(--text2);
    transition: background .3s ease;
  }
  .chat-header .status .dot.online { background: var(--green); box-shadow: 0 0 8px rgba(52,211,153,.5); }

  .chat-messages {
    flex: 1; overflow-y: auto; padding: 20px 24px; display: flex; flex-direction: column; gap: 18px;
    scroll-behavior: smooth;
  }
  .chat-messages::-webkit-scrollbar { width: 6px; }
  .chat-messages::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
  .chat-messages:empty::after {
    content: 'Upload your sleep data, then ask me anything about your sleep health.';
    display: block; color: var(--text2); font-size: 13px; text-align: center;
    padding: 40px 20px; line-height: 1.6;
  }

  .msg { max-width: 95%; animation: fadeUp .25s ease; }
  @keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
  .msg.user { align-self: flex-end; }
  .msg.user .bubble {
    background: var(--gradient-accent); color: #fff;
    border-radius: 18px 18px 4px 18px; padding: 12px 18px;
    font-size: 14px; line-height: 1.55; font-weight: 400;
    box-shadow: 0 2px 12px rgba(123,143,255,.2);
  }
  .msg.assistant .bubble {
    background: var(--glass); border: 1px solid var(--glass-border);
    border-radius: 18px 18px 18px 4px; padding: 14px 18px;
    font-size: 14px; line-height: 1.65; color: var(--text);
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  }
  .msg.assistant .bubble p { margin-bottom: 8px; }
  .msg.assistant .bubble p:last-child { margin-bottom: 0; }
  .msg.assistant .bubble strong { color: var(--accent); }
  .msg .time { font-size: 10px; color: var(--text2); margin-top: 4px; padding: 0 4px; }
  .msg .reasoning-toggle {
    font-size: 11px; color: var(--accent); cursor: pointer;
    margin-top: 6px; display: inline-block; user-select: none;
  }
  .msg .reasoning-toggle:hover { text-decoration: underline; }
  .msg .reasoning-steps {
    margin-top: 8px; padding: 10px 14px; background: var(--accent-glow);
    border: 1px solid var(--glass-border); border-radius: var(--radius-sm);
    font-size: 12px; display: none; line-height: 1.6;
  }
  .msg .reasoning-steps.open { display: block; }
  .msg .reasoning-steps .step { color: var(--text2); padding: 2px 0; }

  .typing-indicator {
    align-self: flex-start; display: none;
    padding: 14px 18px; background: var(--glass); border: 1px solid var(--glass-border);
    border-radius: 18px 18px 18px 4px;
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  }
  .typing-indicator.active { display: flex; gap: 4px; }
  .typing-indicator span {
    width: 7px; height: 7px; border-radius: 50%; background: var(--text2);
    animation: typing 1.2s infinite;
  }
  .typing-indicator span:nth-child(2) { animation-delay: .2s; }
  .typing-indicator span:nth-child(3) { animation-delay: .4s; }
  @keyframes typing { 0%,60%,100% { opacity: .3; } 30% { opacity: 1; } }

  .chat-input-area {
    padding: 16px 24px; border-top: 1px solid var(--border);
    background: var(--bg2); flex-shrink: 0;
  }
  .chat-input-row {
    display: flex; gap: 10px;
  }
  .chat-input-row input {
    flex: 1; background: var(--glass); border: 1px solid var(--glass-border);
    border-radius: var(--radius); padding: 12px 16px;
    color: var(--text); font-size: 14px; outline: none; transition: all .3s ease;
    backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
    font-family: var(--font);
  }
  .chat-input-row input::placeholder { color: var(--text2); }
  .chat-input-row input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
  .chat-input-row input:disabled { opacity: .5; }
  .chat-send-btn {
    background: var(--gradient-accent); color: #fff; border: none;
    width: 44px; height: 44px; border-radius: var(--radius);
    cursor: pointer; transition: all .3s ease; font-size: 18px;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 2px 12px rgba(123,143,255,.25);
  }
  .chat-send-btn:hover { transform: scale(1.05); box-shadow: 0 4px 20px rgba(123,143,255,.35); }
  .chat-send-btn:disabled { opacity: .4; cursor: not-allowed; transform: none; box-shadow: none; }
  .chat-send-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
  .chat-hint { font-size: 11px; color: var(--text2); margin-top: 8px; text-align: center; font-weight: 400; }

  /* ─── Theme Toggle ─── */
  .theme-toggle {
    background: var(--glass); border: 1px solid var(--glass-border);
    color: var(--text2); padding: 0 14px; height: 34px;
    border-radius: 10px; cursor: pointer; font-size: 13px;
    display: flex; align-items: center; justify-content: center; gap: 6px;
    transition: all .3s ease; white-space: nowrap; font-weight: 500;
    backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
  }
  .theme-toggle:hover { border-color: var(--accent); color: var(--text); background: var(--accent-glow); }

  /* ─── Scrollbar ─── */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

  /* ─── Disclaimer Banner ─── */
  .disclaimer-bar {
    background: linear-gradient(90deg, rgba(248,113,113,.1), rgba(248,113,113,.03));
    border-bottom: 1px solid rgba(248,113,113,.15);
    padding: 10px 28px;
    display: flex; align-items: center; gap: 10px;
    font-size: 12px; color: var(--red); flex-shrink: 0; font-weight: 400;
    backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
  }
  .disclaimer-bar .icon { font-size: 14px; flex-shrink: 0; }

  /* ─── Print Button ─── */
  .print-btn {
    background: var(--glass); color: var(--text2); border: 1px solid var(--glass-border);
    padding: 5px 14px; border-radius: 8px; font-size: 12px; cursor: pointer; transition: all .2s ease;
    display: flex; align-items: center; gap: 5px; font-weight: 500;
  }
  .print-btn:hover { color: var(--text); border-color: var(--accent); background: var(--accent-glow); }

  /* ─── Source Tabs & Add Source ─── */
  .source-tabs { display: flex; gap: 4px; margin-bottom: 12px; }
  .source-tabs .tab {
    background: transparent; color: var(--text2); border: 1px solid var(--border);
    padding: 6px 16px; border-radius: 10px; font-size: 12px; cursor: pointer; transition: all .2s ease; font-weight: 500;
  }
  .source-tabs .tab:hover { color: var(--text); border-color: var(--accent); }
  .source-tabs .tab.active { background: var(--gradient-accent); color: #fff; border-color: transparent; box-shadow: 0 2px 10px rgba(123,143,255,.25); }
  .add-source-btn {
    background: transparent; color: var(--accent); border: 1px dashed var(--border);
    padding: 7px 18px; border-radius: var(--radius); font-size: 12px; cursor: pointer;
    transition: all .2s ease; margin-bottom: 14px; display: inline-block; font-weight: 500;
  }
  .add-source-btn:hover { border-color: var(--accent); background: var(--accent-glow); }
  .source-tabs .tab .tab-close {
    margin-left: 6px; cursor: pointer; opacity: .5; font-size: 14px; line-height: 1;
  }
  .source-tabs .tab .tab-close:hover { opacity: 1; }
  .clear-data-btn {
    background: transparent; color: var(--red); border: 1px solid rgba(248,113,113,.25);
    padding: 5px 14px; border-radius: 8px; font-size: 11px; cursor: pointer;
    transition: all .2s ease; font-weight: 500; margin-left: 8px;
  }
  .clear-data-btn:hover { border-color: var(--red); background: rgba(248,113,113,.1); }
  .demo-badge {
    display: inline-block; background: rgba(251,191,36,.15); color: var(--yellow);
    padding: 1px 7px; border-radius: 8px; font-size: 9px; font-weight: 700; margin-left: 6px;
    vertical-align: middle; line-height: 1.4; letter-spacing: .03em;
  }

  /* ─── Suggested Questions ─── */
  .suggestions {
    padding: 10px 24px 6px;
    display: flex; flex-wrap: wrap; gap: 8px;
    flex-shrink: 0;
  }
  .suggestions .suggestion-chip {
    background: var(--glass); color: var(--text2);
    border: 1px solid var(--glass-border); border-radius: 20px;
    padding: 6px 14px; font-size: 12px;
    cursor: pointer; transition: all .25s ease; white-space: nowrap; font-weight: 500;
    backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
  }
  .suggestions .suggestion-chip:hover {
    border-color: var(--accent); color: var(--accent); background: var(--accent-glow);
    transform: translateY(-1px);
  }

  /* ─── Print Styles ─── */
  @media print {
    body { overflow: visible !important; background: #fff; color: #000; display: block; }
    .right-panel, .disclaimer-bar, .print-btn, .chart-range, .chat-input-area,
    .chat-header, .left-header, .upload-screen, .typing-indicator { display: none !important; }
    .left-panel { border: none !important; width: 100% !important; }
    .dashboard { display: block !important; }
    .dash-scroll { overflow: visible !important; padding: 0 !important; }
    .metric-card, .chart-wrapper, .flags-box {
      background: #f5f5f5 !important; border-color: #ddd !important;
      break-inside: avoid; box-shadow: none !important;
    }
    .metric-card .label { color: #666 !important; }
    .metric-card .value { color: #000 !important; }
    .chart-wrapper .chart-header h3 { color: #000 !important; }
    .flags-box h3 { color: #000 !important; }
    .flag-item { color: #333 !important; border-color: #ddd !important; }
    .source-tag { color: #666 !important; background: #eee !important; }
    #trendChart { max-height: 250px; }
    @page { margin: 1.5cm; }
  }

  /* ─── Responsive ─── */
  @media (max-width: 900px) {
    body { flex-direction: column; }
    .left-panel { border-right: none; border-bottom: 1px solid var(--border); }
    .right-panel { width: 100%; max-width: 100%; min-width: 0; }
    .metrics-grid { grid-template-columns: repeat(2, 1fr); }
  }
</style>
</head>
<body>

<!-- ═══════ LEFT PANEL ═══════ -->
<div class="left-panel">

  <div class="left-header">
    <div class="logo"><img src="/static/logo.jpeg" alt="Sleep IQ" style="width:44px;height:44px;border-radius:14px;object-fit:cover;"></div>
    <div>
      <h1>Sleep IQ</h1>
      <div class="sub">AI Sleep Companion</div>
    </div>
    <div class="header-actions">
      <button class="theme-toggle" id="themeToggle" type="button" aria-label="Toggle theme"></button>
      <div class="badge" id="sourceBadge">No data</div>
    </div>
  </div>

  <!-- ── Disclaimer ── -->
  <div class="disclaimer-bar">
    <span class="icon">&#9888;</span>
    <span><strong>Not medical advice.</strong> Sleep IQ provides AI-generated analysis for informational purposes only. Always consult a healthcare provider about your sleep health.</span>
  </div>

  <!-- ── Upload Screen ── -->
  <div class="upload-screen" id="uploadScreen">
    <div class="upload-icon" id="uploadIcon">&#128164;</div>
    <h2>Upload your sleep data</h2>
    <p>Drag &amp; drop your file here, or click to browse.<br>
    Supports CPAP (EDF/JSON), Apple Health (XML), Fitbit (JSON), and CSV.</p>
    <button class="upload-btn" id="uploadBtn" type="button">Choose File</button>
    <input type="file" id="fileInput" accept=".edf,.json,.xml,.csv,.zip" style="display:none">
    <button class="demo-btn" id="demoBtn" type="button">&#9654; Load CPAP Demo</button>
    <button class="demo-btn" id="wearableDemoBtn" type="button">&#9654; Load Smartwatch Demo</button>
    <div class="upload-progress" id="uploadProgress">
      <div class="bar"><div class="bar-fill" id="progressFill"></div></div>
    </div>
    <div class="upload-error" id="uploadError"></div>
    <div class="upload-formats">Accepted: EDF, JSON, XML, CSV, ZIP &middot; Max 500 MB</div>
  </div>

  <!-- ── Dashboard ── -->
  <div class="dashboard" id="dashboard">
    <div class="dash-scroll">
      <div class="source-tag" id="dashSource"></div>
      <div class="source-tabs" id="sourceTabs" style="display:none"></div>
      <div style="display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap;">
        <button class="add-source-btn" id="addSourceBtn" type="button">+ Add another data source</button>
        <button class="clear-data-btn" id="clearDataBtn" type="button" style="display:none">&#128465; Clear all</button>
      </div>
      <div class="metrics-grid" id="metricsGrid"></div>
      <div class="chart-wrapper">
        <div class="chart-header">
          <h3>Trends</h3>
          <button class="print-btn" onclick="window.print()" type="button" aria-label="Download doctor report">&#128424; Download Report</button>
          <div class="chart-range" id="chartRange">
            <button data-days="30" class="active">30d</button>
            <button data-days="90">90d</button>
            <button data-days="365">1y</button>
            <button data-days="all">All</button>
            <button id="customRangeBtn">Custom</button>
          </div>
        </div>
        <div id="customRangeInputs" style="display:none; gap: 8px; margin-bottom: 16px; justify-content: flex-end; align-items: center;">
          <input type="date" id="startDate" style="background:var(--bg2); color:var(--text); border:1px solid var(--border); border-radius:4px; padding:4px 8px; font-size:12px;">
          <span style="color:var(--text2); font-size:12px;">to</span>
          <input type="date" id="endDate" style="background:var(--bg2); color:var(--text); border:1px solid var(--border); border-radius:4px; padding:4px 8px; font-size:12px;">
          <button id="applyCustomBtn" style="background:var(--accent); color:#fff; border:none; border-radius:4px; padding:4px 12px; font-size:12px; cursor:pointer;">Apply</button>
        </div>
        <div class="chart-container">
          <canvas id="trendChart" aria-label="Sleep data trend chart" role="img"></canvas>
        </div>
      </div>
      <div class="flags-box" id="flagsBox">
        <h3>&#9888; Flags &amp; Observations</h3>
        <div id="flagsList"></div>
      </div>
    </div>
  </div>
</div>

<!-- ═══════ RIGHT PANEL ═══════ -->
<div class="right-panel">
  <div class="chat-header">
    <h2>&#128172; Sleep Chat</h2>
    <div class="status">
      <span class="dot" id="statusDot"></span>
      <span id="statusText">Waiting for data</span>
    </div>
  </div>

  <div class="chat-messages" id="chatMessages" role="log" aria-live="polite"></div>

  <div class="typing-indicator" id="typingIndicator">
    <span></span><span></span><span></span>
  </div>

  <div class="suggestions" id="suggestions" style="display:none">
    <div class="suggestion-chip" data-question="How was my sleep this month compared to last month?">Compare months</div>
    <div class="suggestion-chip" data-question="What are my 3 biggest sleep problems right now?">3 biggest problems</div>
    <div class="suggestion-chip" data-question="Give me a summary for my doctor appointment.">Doctor report</div>
    <div class="suggestion-chip" data-question="Are there any concerning trends I should know about?">Concerning trends</div>
  </div>

  <div class="chat-input-area">
    <div class="chat-input-row">
      <input type="text" id="chatInput" placeholder="Ask about your sleep data..." autocomplete="off" disabled>
      <button class="chat-send-btn" id="chatSendBtn" disabled aria-label="Send message">&#10148;</button>
    </div>
    <div class="chat-hint">Analysis is session-based &middot; No data is stored</div>
  </div>
</div>

<script>
(function() {
  'use strict';

  // ─── State ───
  let hasData = false;
  let dataSource = '';
  let trendSeries = {};
  let chartInstance = null;
  let chartDays = 30;
  let isDemoLoading = false;
  let isMultiSource = false;
  let sourceKeys = [];
  let activeSource = '';

  // ─── DOM refs ───
  const uploadScreen = document.getElementById('uploadScreen');
  const dashboard = document.getElementById('dashboard');
  const uploadBtn = document.getElementById('uploadBtn');
  const fileInput = document.getElementById('fileInput');
  const demoBtn = document.getElementById('demoBtn');
  const wearableDemoBtn = document.getElementById('wearableDemoBtn');
  const uploadProgress = document.getElementById('uploadProgress');
  const progressFill = document.getElementById('progressFill');
  const uploadError = document.getElementById('uploadError');
  const sourceBadge = document.getElementById('sourceBadge');
  const dashSource = document.getElementById('dashSource');
  const metricsGrid = document.getElementById('metricsGrid');
  const flagsList = document.getElementById('flagsList');
  const chatMessages = document.getElementById('chatMessages');
  const chatInput = document.getElementById('chatInput');
  const chatSendBtn = document.getElementById('chatSendBtn');
  const typingIndicator = document.getElementById('typingIndicator');
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');
  const trendChart = document.getElementById('trendChart');
  const suggestions = document.getElementById('suggestions');
  const themeToggle = document.getElementById('themeToggle');
  const sourceTabs = document.getElementById('sourceTabs');
  const addSourceBtn = document.getElementById('addSourceBtn');

  // ─── Theme ───
  function getSavedTheme() {
    try { return localStorage.getItem('sleepiq-theme'); } catch(e) { return null; }
  }
  function saveTheme(theme) {
    try { localStorage.setItem('sleepiq-theme', theme); } catch(e) {}
  }
  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    saveTheme(theme);
    themeToggle.innerHTML = theme === 'light' ? '🌙 Dark' : '☀️ Light';
    if (chartInstance) renderChart(); // re-render chart to pick up new CSS vars
  }
  var initialTheme = getSavedTheme();
  if (!initialTheme) {
    initialTheme = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }
  setTheme(initialTheme);
  themeToggle.addEventListener('click', function() {
    var current = document.documentElement.getAttribute('data-theme') || 'dark';
    setTheme(current === 'light' ? 'dark' : 'light');
  });

  // ─── Upload Screen Drag & Drop ───
  uploadScreen.addEventListener('dragover', function(e) {
    e.preventDefault();
    uploadScreen.classList.add('drag');
  });
  uploadScreen.addEventListener('dragleave', function(e) {
    e.preventDefault();
    uploadScreen.classList.remove('drag');
  });
  uploadScreen.addEventListener('drop', function(e) {
    e.preventDefault();
    uploadScreen.classList.remove('drag');
    const files = e.dataTransfer.files;
    if (files.length) uploadFile(files[0]);
  });

  uploadBtn.addEventListener('click', function() { fileInput.click(); });
  fileInput.addEventListener('change', function() {
    if (this.files.length) uploadFile(this.files[0]);
  });
  demoBtn.addEventListener('click', loadDemo);
  wearableDemoBtn.addEventListener('click', loadWearableDemo);
  document.querySelectorAll('.chart-range button').forEach(function(btn) {
    if (btn.id === 'customRangeBtn') return;
    btn.addEventListener('click', function() {
      document.querySelectorAll('.chart-range button').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      chartDays = btn.dataset.days;
      document.getElementById('customRangeInputs').style.display = 'none';
      fetchWithFilters(chartDays, '', '');
    });
  });

  document.getElementById('customRangeBtn').addEventListener('click', function() {
    document.querySelectorAll('.chart-range button').forEach(function(b) { b.classList.remove('active'); });
    this.classList.add('active');
    document.getElementById('customRangeInputs').style.display = 'flex';
  });

  document.getElementById('applyCustomBtn').addEventListener('click', function() {
    var start = document.getElementById('startDate').value;
    var end = document.getElementById('endDate').value;
    if (!start && !end) return;
    chartDays = 'all'; // Backend will handle the date filtering
    fetchWithFilters('', start, end);
  });

  function fetchWithFilters(days, start, end) {
    if (!dataSource || dataSource === 'unknown') return;
    var url = '/api/source-data?source=' + dataSource;
    if (days && days !== 'all') url += '&days=' + days;
    if (start) url += '&start=' + start;
    if (end) url += '&end=' + end;
    
    fetch(url)
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.error) return;
        trendSeries = data.trend_series || {};
        renderMetrics(data.key_metrics || {}, dataSource);
        renderFlags(data.flags || []);
        renderChart();
      })
      .catch(function() {});
  }

  // ─── Chat ───
  chatInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
  chatSendBtn.addEventListener('click', sendMessage);
  suggestions.addEventListener('click', function(e) {
    var chip = e.target.closest('.suggestion-chip');
    if (chip) {
      chatInput.value = chip.dataset.question;
      sendMessage();
    }
  });
  addSourceBtn.addEventListener('click', function() {
    uploadScreen.classList.remove('hidden');
    dashboard.classList.remove('active');
  });
  document.getElementById('clearDataBtn').addEventListener('click', function() {
    if (!confirm('Clear all data and start fresh?')) return;
    fetch('/api/clear-data', { method: 'POST' })
      .then(function(r) { return r.json(); })
      .then(function() {
        hasData = false;
        dataSource = '';
        trendSeries = {};
        if (chartInstance) { chartInstance.destroy(); chartInstance = null; }
        dashboard.classList.remove('active');
        uploadScreen.classList.remove('hidden');
        uploadProgress.classList.remove('active');
        chatMessages.innerHTML = '';
        chatInput.disabled = true;
        chatSendBtn.disabled = true;
        suggestions.style.display = 'none';
        sourceTabs.style.display = 'none';
        sourceTabs.innerHTML = '';
        document.getElementById('clearDataBtn').style.display = 'none';
        addSourceBtn.style.display = 'none';
        sourceBadge.textContent = 'No data';
        dashSource.innerHTML = '';
        metricsGrid.innerHTML = '';
        flagsList.innerHTML = '<div class="flag-item" style="color:var(--text2)">No flags detected.</div>';
        setStatus(false, '');
        addSourceBtn.textContent = '+ Add another data source';
      })
      .catch(function() { alert('Failed to clear data.'); });
  });

  function removeSource(source) {
    if (!confirm('Remove ' + source.replace('_demo', '').replace(/_/g, ' ') + ' data?')) return;
    fetch('/api/remove-source', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source: source })
    })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (!data.success) { alert('Failed to remove source.'); return; }
        if (!data.has_data) {
          document.getElementById('clearDataBtn').click();
          return;
        }
        // Rebuild tabs from remaining sources
        var remaining = Object.keys(data.remaining_sources);
        if (remaining.length === 1) {
          sourceTabs.style.display = 'none';
          sourceTabs.innerHTML = '';
          activeSource = remaining[0];
          dataSource = remaining[0];
          switchSource(activeSource);
        } else {
          renderSourceTabs(remaining, remaining[0], data.remaining_sources);
          switchSource(remaining[0]);
        }
      })
      .catch(function() { alert('Failed to remove source.'); });
  }

  // ─── Upload file ───
  function uploadFile(file) {
    var formData = new FormData();
    formData.append('file', file);
    uploadError.style.display = 'none';
    uploadProgress.classList.add('active');
    progressFill.style.width = '30%';

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/upload');
    xhr.onload = function() {
      uploadProgress.classList.remove('active');
      if (xhr.status === 200) {
        var data = JSON.parse(xhr.responseText);
        onDataLoaded(data);
      } else {
        try {
          var err = JSON.parse(xhr.responseText);
          showUploadError(err.error || 'Upload failed');
        } catch(_) {
          showUploadError('Upload failed (status ' + xhr.status + ')');
        }
      }
    };
    xhr.onerror = function() { showUploadError('Network error during upload.'); };
    xhr.upload.onprogress = function(e) {
      if (e.lengthComputable) progressFill.style.width = Math.round((e.loaded / e.total) * 100) + '%';
    };
    xhr.send(formData);
  }

  // ─── Load Demo Data ───
  function loadDemo() {
    if (isDemoLoading) return;
    isDemoLoading = true;
    demoBtn.disabled = true;
    demoBtn.textContent = 'Loading...';

    fetch('/api/load-demo', { method: 'POST' })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.error) { showUploadError(data.error); return; }
        onDataLoaded(data);
      })
      .catch(function() { showUploadError('Failed to load demo data.'); })
      .finally(function() {
        isDemoLoading = false;
        demoBtn.disabled = false;
        demoBtn.textContent = '\u25B6 Load CPAP Demo';
      });
  }

  // ─── Load Wearable Demo ───
  function loadWearableDemo() {
    if (isDemoLoading) return;
    isDemoLoading = true;
    wearableDemoBtn.disabled = true;
    wearableDemoBtn.textContent = 'Loading...';

    fetch('/api/load-wearable-demo', { method: 'POST' })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.error) { showUploadError(data.error); return; }
        onDataLoaded(data);
      })
      .catch(function() { showUploadError('Failed to load wearable demo data.'); })
      .finally(function() {
        isDemoLoading = false;
        wearableDemoBtn.disabled = false;
        wearableDemoBtn.textContent = '\u25B6 Load Smartwatch Demo';
      });
  }

  function showUploadError(msg) {
    uploadError.textContent = msg;
    uploadError.style.display = 'block';
    uploadProgress.classList.remove('active');
  }

  // ─── Data Loaded ───
  function onDataLoaded(data) {
    hasData = true;
    isMultiSource = data.multi_source === true;
    dataSource = data.source || 'unknown';
    activeSource = dataSource;
    trendSeries = data.trend_series || {};

    uploadScreen.classList.add('hidden');
    dashboard.classList.add('active');
    document.getElementById('clearDataBtn').style.display = 'inline-block';

    if (isMultiSource && data.sources) {
      sourceKeys = Object.keys(data.sources);
      renderSourceTabs(sourceKeys, activeSource, data.sources);
      addSourceBtn.textContent = '+ Add another data source';
      addSourceBtn.style.display = 'inline-block';
    } else {
      sourceTabs.style.display = 'none';
      sourceTabs.innerHTML = '';
      addSourceBtn.textContent = '+ Add another data source';
      addSourceBtn.style.display = 'inline-block';
    }

    renderSourceTag(data.source, data.is_demo);
    renderMetrics(data.key_metrics, data.source);
    renderFlags(data.flags || []);
    renderChart();

    chatInput.disabled = false;
    chatSendBtn.disabled = false;
    chatInput.focus();
    setStatus(true, isMultiSource ? 'multi' : data.source);
    suggestions.style.display = 'flex';

    var msg = isMultiSource
      ? ('Multiple data sources loaded. I can see CPAP therapy data and smartwatch data. '
         + 'Try asking: "How does my sleep quality compare with my AHI trends?"')
      : ('Sleep data loaded. I can see ' + (data.record_count || 0) + ' records. What would you like to know about your sleep?' + (data.is_demo ? ' (Demo data)' : ''));
    addSystemMessage(msg);
  }

  function renderSourceTabs(keys, active, sourcesInfo) {
    sourceTabs.style.display = 'flex';
    var labels = { cpap: 'CPAP', apple_health: 'Apple Health', fitbit: 'Fitbit', csv: 'Sleep CSV', cpap_demo: 'CPAP Demo', fitbit_demo: 'Smartwatch Demo' };
    var html = '';
    var isSingle = keys.length <= 1;
    keys.forEach(function(k) {
      var info = sourcesInfo ? sourcesInfo[k] : {};
      var displayName = labels[k] || k;
      if (info.is_demo && !labels[k]) displayName += ' (Demo)';
      html += '<button class="tab' + (k === active ? ' active' : '') + '" data-source="' + k + '">' + displayName;
      if (!isSingle) html += '<span class="tab-close" data-remove="' + k + '">&#10005;</span>';
      html += '</button>';
    });
    sourceTabs.innerHTML = html;
    sourceTabs.querySelectorAll('.tab').forEach(function(tab) {
      tab.addEventListener('click', function(e) {
        if (e.target.classList.contains('tab-close')) return;
        sourceTabs.querySelectorAll('.tab').forEach(function(t) { t.classList.remove('active'); });
        tab.classList.add('active');
        switchSource(tab.dataset.source);
      });
    });
    sourceTabs.querySelectorAll('.tab-close').forEach(function(el) {
      el.addEventListener('click', function(e) {
        e.stopPropagation();
        removeSource(el.dataset.remove);
      });
    });
  }

  function switchSource(source) {
    activeSource = source;
    dataSource = source;
    fetch('/api/source-data?source=' + source)
      .then(function(r) { return r.json(); })
      .then(function(data) {
        trendSeries = data.trend_series || {};
        renderSourceTag(source, source.indexOf('_demo') > -1);
        renderMetrics(data.key_metrics || {}, source);
        renderFlags(data.flags || []);
        renderChart();
      })
      .catch(function() {});
  }

  function setStatus(online, source) {
    statusDot.className = 'dot' + (online ? ' online' : '');
    statusText.textContent = online ? 'Ready' : 'Waiting for data';
    if (source) {
      var labels = { cpap: 'CPAP', apple_health: 'Apple Health', fitbit: 'Fitbit', csv: 'CSV', multi: 'Multi', cpap_demo: 'CPAP Demo', fitbit_demo: 'Smartwatch Demo' };
      sourceBadge.textContent = labels[source] || source.replace('_demo', '').replace(/_/g, ' ').replace(/\b\w/g, function(c) { return c.toUpperCase(); });
    }
  }

  function renderSourceTag(source, isDemo) {
    var labels = { cpap: 'CPAP Therapy', apple_health: 'Apple Health', fitbit: 'Fitbit Data', csv: 'Sleep CSV', cpap_demo: 'CPAP Therapy', fitbit_demo: 'Smartwatch' };
    var text = labels[source] || 'Sleep Data';
    if (isDemo || source.indexOf('_demo') > -1) text += ' <span class="demo-badge">DEMO</span>';
    dashSource.innerHTML = text;
  }

  function renderMetrics(km, source) {
    if (!km) { metricsGrid.innerHTML = ''; return; }
    var cards = '';
    var base = source.replace('_demo', '');
    if (base === 'cpap') {
      cards += card('AHI', km.ahi, 'events/hr', severitySub(km.severity));
      cards += card('Compliance', km.compliance, '%', sub(km.trend, 'trend'));
      cards += card('Avg Usage', km.usage_hrs, 'hrs');
      cards += card('Leak Rate (P95)', km.leak_p95, 'L/min');
    } else {
      cards += card('Sleep Score', km.sleep_score, '/100');
      cards += card('HRV', km.hrv_ms, 'ms');
      cards += card('SpO\u2082', km.spo2_avg, '%');
      cards += card('Deep Sleep', km.deep_min, 'min');
      cards += card('Total Sleep', km.total_hrs, 'hrs');
    }
    metricsGrid.innerHTML = cards;
  }

  function card(label, value, unit, subHtml) {
    if (value == null) return '';
    var v = typeof value === 'number' ? value.toFixed(1) : value;
    return '<div class="metric-card"><div class="label">' + label + '</div><div class="value">' + v + '<span class="unit">' + unit + '</span></div>' + (subHtml || '') + '</div>';
  }

  function severitySub(s) {
    if (!s) return '';
    var cls = 'good';
    if (s === 'mild') cls = 'warn';
    else if (s === 'moderate' || s === 'severe') cls = 'bad';
    return '<div class="sub ' + cls + '">' + s.charAt(0).toUpperCase() + s.slice(1) + '</div>';
  }

  function sub(v, prefix) {
    if (!v) return '';
    return '<div class="sub warn">' + prefix + ': ' + v + '</div>';
  }

  function renderFlags(flags) {
    if (!flags || !flags.length) {
      flagsList.innerHTML = '<div class="flag-item" style="color:var(--text2)">No flags detected.</div>';
      return;
    }
    var html = '';
    flags.forEach(function(f) {
      var text = typeof f === 'string' ? f : (f.message || JSON.stringify(f));
      var icon = '&#8505;';
      if (text.indexOf('CRITICAL') === 0 || text.indexOf('CRITICAL:') === 0) icon = '&#128721;';
      else if (text.indexOf('WARNING') === 0 || text.indexOf('WARNING:') === 0) icon = '&#9888;';
      else if (text.indexOf('GOOD') === 0 || text.indexOf('GOOD:') === 0) icon = '&#9989;';
      else if (text.indexOf('ATTENTION') === 0 || text.indexOf('ATTENTION:') === 0) icon = '&#9888;';
      html += '<div class="flag-item"><span class="icon">' + icon + '</span><span>' + escapeHtml(text) + '</span></div>';
    });
    flagsList.innerHTML = html;
  }

  // ─── Chart ───
  function renderChart() {
    if (!trendSeries || !Object.keys(trendSeries).length) return;
    var labels = getChartLabels();
    var datasets = getChartDatasets(labels);
    if (!datasets.length) return;

    var ctx = trendChart.getContext('2d');
    if (chartInstance) { chartInstance.destroy(); chartInstance = null; }

    var style = getComputedStyle(document.documentElement);
    var text2 = style.getPropertyValue('--text2').trim() || '#949bb8';
    var text = style.getPropertyValue('--text').trim() || '#e2e6f0';
    var bg3 = style.getPropertyValue('--bg3').trim() || '#1a1f2e';
    var border = style.getPropertyValue('--border').trim() || '#2a3148';
    var gridColor = document.documentElement.getAttribute('data-theme') === 'light' ? 'rgba(0,0,0,0.05)' : 'rgba(42,49,72,.4)';

    chartInstance = new Chart(ctx, {
      type: 'line',
      data: { labels: labels, datasets: datasets },
      options: {
        responsive: true, maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        plugins: {
          legend: { labels: { color: text2, font: { size: 11 }, boxWidth: 12, padding: 12 } },
          tooltip: { backgroundColor: bg3, titleColor: text, bodyColor: text2, borderColor: border, borderWidth: 1, padding: 10, cornerRadius: 8 }
        },
        scales: {
          x: { ticks: { color: text2, font: { size: 10 }, maxTicksLimit: 10 }, grid: { color: gridColor } },
          y: { ticks: { color: text2, font: { size: 10 } }, grid: { color: gridColor }, beginAtZero: true }
        }
      }
    });
  }

  // trend_series shape: {dates:[...], ahi:[...], usage_hrs:[...], leak_95:[...], press_95:[...], ...}
  function getChartLabels() {
    var dates = trendSeries['dates'] || [];
    if (!dates.length) return [];
    var n = chartDays === 'all' ? dates.length : Math.min(parseInt(chartDays) || 30, dates.length);
    return dates.slice(-n).map(function(d) {
      // Show as MM/DD
      var parts = (d || '').split('-');
      return parts.length === 3 ? parts[1] + '/' + parts[2] : d;
    });
  }

  function getChartDatasets(labels) {
    var colors = {'ahi':'#6c8cff','usage_hrs':'#34d399','scores':'#34d399','leak_95':'#fbbf24','press_95':'#fb923c','hrv':'#a78bfa','spo2':'#34d399','total_hrs':'#6c8cff','deep':'#f87171'};
    var labelMap = {'ahi':'AHI','usage_hrs':'Usage Hrs','scores':'Sleep Score','leak_95':'Leak 95','press_95':'Press 95','hrv':'HRV','spo2':'SpO2','total_hrs':'Total Hrs','deep':'Deep Sleep'};
    var skip = {'dates': true};
    var n = chartDays === 'all' ? 9999 : (parseInt(chartDays) || 30);
    var ds = [];
    Object.keys(trendSeries).forEach(function(key) {
      if (skip[key]) return;
      var arr = trendSeries[key] || [];
      if (!arr.length) return;
      var sliced = arr.slice(-n).map(function(v) { return (v == null || isNaN(v)) ? null : +v; });
      var color = colors[key] || '#6c8cff';
      ds.push({
        label: labelMap[key] || key,
        data: sliced,
        borderColor: color,
        backgroundColor: color + '18',
        fill: false,
        tension: .3,
        pointRadius: 1,
        pointHoverRadius: 5,
        borderWidth: 2,
        spanGaps: true
      });
    });
    return ds;
  }

  // ─── Chat ───
  // ─── Reasoning toggle (delegated) ───
  chatMessages.addEventListener('click', function(e) {
    var toggle = e.target.closest('.reasoning-toggle');
    if (toggle) {
      var steps = toggle.nextElementSibling;
      if (steps && steps.classList.contains('reasoning-steps')) {
        steps.classList.toggle('open');
        toggle.textContent = steps.classList.contains('open') ? '\u25BC Hide reasoning' : '\u25B6 Show reasoning';
      }
    }
  });

  function sendMessage() {
    var text = chatInput.value.trim();
    if (!text || !hasData) return;
    chatInput.value = '';
    chatInput.disabled = true;
    chatSendBtn.disabled = true;

    addUserMessage(text);
    showTyping();

    var history = [];
    document.querySelectorAll('#chatMessages .msg.assistant, #chatMessages .msg.user').forEach(function(el) {
      var role = el.classList.contains('user') ? 'user' : 'assistant';
      var bubble = el.querySelector('.bubble');
      if (bubble) history.push({ role: role, content: bubble.textContent.trim() });
    });

    fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, history: history })
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      hideTyping();
      if (data.answer) addAssistantMessage(data.answer, data.reasoning_steps || [], data.tool_calls || []);
    })
    .catch(function() {
      hideTyping();
      addAssistantMessage('Sorry, something went wrong. Please try again.');
    })
    .finally(function() {
      chatInput.disabled = false;
      chatSendBtn.disabled = false;
      chatInput.focus();
    });
  }

  function addUserMessage(text) {
    var div = document.createElement('div');
    div.className = 'msg user';
    div.innerHTML = '<div class="bubble">' + escapeHtml(text) + '</div><div class="time">Just now</div>';
    chatMessages.appendChild(div);
    scrollChat();
  }

  function addAssistantMessage(text, reasoningSteps, toolCalls) {
    var div = document.createElement('div');
    div.className = 'msg assistant';

    var bubbleHtml = '<div class="bubble">' + formatAnswer(text) + '</div>';
    var stepsHtml = '';
    if (reasoningSteps && reasoningSteps.length) {
      stepsHtml += '<span class="reasoning-toggle">\u25B6 Show reasoning</span>';
      stepsHtml += '<div class="reasoning-steps">';
      reasoningSteps.forEach(function(s) { stepsHtml += '<div class="step">' + escapeHtml(s) + '</div>'; });
      stepsHtml += '</div>';
    }
    div.innerHTML = bubbleHtml + stepsHtml + '<div class="time">Just now</div>';
    chatMessages.appendChild(div);
    scrollChat();
  }

  function addSystemMessage(text) {
    var div = document.createElement('div');
    div.className = 'msg assistant';
    div.innerHTML = '<div class="bubble">' + escapeHtml(text) + '</div>';
    chatMessages.appendChild(div);
    scrollChat();
  }

  function showTyping() { typingIndicator.classList.add('active'); scrollChat(); }
  function hideTyping() { typingIndicator.classList.remove('active'); }

  function scrollChat() { chatMessages.scrollTop = chatMessages.scrollHeight; }

  function formatAnswer(text) {
    if (!text) return '';
    text = escapeHtml(text);
    text = text.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/### (.+)/g, '<strong>$1</strong>');
    text = '<p>' + text + '</p>';
    return text;
  }

  function escapeHtml(s) {
    var d = document.createElement('div');
    d.appendChild(document.createTextNode(s));
    return d.innerHTML;
  }

  // ─── Auto-load CPAP demo on first visit ───
  fetch('/api/status')
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.has_data) {
        fetch('/api/session-data')
          .then(function(r) { return r.json(); })
          .then(function(sdata) {
            onDataLoaded(sdata);
          })
          .catch(function() {});
      } else {
        // First visit — auto-load CPAP demo so judges see data instantly
        loadDemo();
      }
    })
    .catch(function() {});

})();
</script>
</body>
</html>
"""
