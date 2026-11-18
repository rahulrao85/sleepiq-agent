"""End-to-end test: load data + call agent via Azure OpenAI."""
import os, sys, json, uuid, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from orchestrator import load_session_data, run_agent, _sessions, has_session

# Create demo CPAP data
demo = {
    'source': 'cpap',
    'device': {'model': 'Test Device', 'serial': '0000'},
    'records': [
        {'Date': 20195, 'DateFormatted': '17-Apr-2025', 'AHI': 5.2, 'OnDuration': 300,
         'AI': 2.1, 'HI': 3.1, 'OAI': 1.5, 'CAI': 0.6, 'CSR': 0.0,
         'Leak.95': 12.0, 'MaskPress.95': 11.0, 'Mode': 1,
         'S.AS.MinPress': 4, 'S.AS.MaxPress': 15, 'S.EPR.Level': 2, 'S.Mask': 1},
        {'Date': 20196, 'DateFormatted': '18-Apr-2025', 'AHI': 3.8, 'OnDuration': 360,
         'AI': 1.5, 'HI': 2.3, 'OAI': 1.0, 'CAI': 0.5, 'CSR': 0.0,
         'Leak.95': 15.0, 'MaskPress.95': 10.0, 'Mode': 1,
         'S.AS.MinPress': 4, 'S.AS.MaxPress': 15, 'S.EPR.Level': 2, 'S.Mask': 1},
    ]
}

sid = str(uuid.uuid4())
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(demo, f)
    tmp = f.name

try:
    # Load data
    result = load_session_data(sid, tmp, 'cpap')
    assert result['success'] == True
    assert has_session(sid)
    print('PASS: Data loaded')

    # Determine which provider will be used
    conn_str = os.getenv('AZURE_AI_PROJECT_CONNECTION_STRING', '')
    az_key = os.getenv('AZURE_OPENAI_API_KEY', '')
    or_key = os.getenv('OPENROUTER_API_KEY', '')

    if conn_str and ';' in conn_str:
        print('Route: Azure AI Foundry (PRIMARY)')
    elif az_key:
        print(f'Route: Azure OpenAI (Microsoft stack) with model {os.getenv("AZURE_AI_MODEL_DEPLOYMENT", "?")}')
    elif or_key:
        print('Route: OpenRouter (fallback)')
    else:
        print('Route: None configured')

    # Call the agent
    response = run_agent(sid, 'What is my AHI trend? Give me a short summary.')
    assert 'answer' in response
    print(f'\nAnswer:\n{response["answer"][:500]}')
    print(f'\nPASS: Agent responded successfully via Azure!')

finally:
    os.unlink(tmp)
    _sessions.pop(sid, None)
