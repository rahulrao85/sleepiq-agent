"""Smoke tests for Sleep IQ data tools."""

import os, sys, json, tempfile, zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cpap_tool import load_cpap_data, parse_edf, _normalise_dates


def _demo_records():
    """Return a minimal demo dataset."""
    return {
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


def test_normalise_dates():
    recs = _demo_records()['records']
    _normalise_dates(recs)
    assert recs[0]['DateFormatted'] == '2025-04-17', f"Got {recs[0]['DateFormatted']}"
    assert recs[1]['DateFormatted'] == '2025-04-18', f"Got {recs[1]['DateFormatted']}"
    print('PASS: date normalisation')


def test_load_cpap_json():
    d = _demo_records()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(d, f)
        tmp = f.name
    try:
        result = load_cpap_data(tmp)
        assert result['source'] == 'cpap'
        assert len(result['records']) == 2
        assert result['records'][0]['DateFormatted'] == '2025-04-17'
        print('PASS: load CPAP JSON')
    finally:
        os.unlink(tmp)


def test_load_cpap_zip():
    d = _demo_records()
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as zf:
        with zipfile.ZipFile(zf, 'w') as z:
            z.writestr('cpap_data.json', json.dumps(d))
        zpath = zf.name
    try:
        result = load_cpap_data(zpath)
        assert result['source'] == 'cpap'
        assert len(result['records']) == 2
        print('PASS: load CPAP ZIP')
    finally:
        os.unlink(zpath)


def test_upload_response_shape():
    """Verify the response shape matches what the UI expects."""
    from orchestrator import load_session_data, _sessions, has_session
    import uuid
    d = _demo_records()
    sid = str(uuid.uuid4())
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(d, f)
        tmp = f.name
    try:
        result = load_session_data(sid, tmp, 'cpap')
        assert result['success'] is True
        assert result['source'] == 'cpap'
        assert 'summary' in result
        assert 'key_metrics' in result
        assert 'flags' in result
        assert 'trend_series' in result
        assert result['trend_series'].get('dates')
        assert result['trend_series'].get('ahi')
        assert has_session(sid)
        print('PASS: upload response shape')
    finally:
        os.unlink(tmp)
        _sessions.pop(sid, None)


def test_foundry_iq():
    from foundry_iq import search_knowledge
    results = search_knowledge('what is a normal ahi level')
    assert len(results) >= 1
    assert 'AASM' in results[0]['source']
    assert '5' in results[0]['content']
    print('PASS: Foundry IQ knowledge search')


if __name__ == '__main__':
    test_normalise_dates()
    test_load_cpap_json()
    test_load_cpap_zip()
    test_upload_response_shape()
    test_foundry_iq()
    print('\nAll tests passed.')
