# Sleep IQ — Feature Tracking

## Data Sources

| Source | Type | Status | Notes |
|--------|------|--------|-------|
| CPAP Demo | `cpap_demo` (fix: strips `_demo` suffix for parsing) | ✅ Working | 365 records, AHI 1.2, Compliance 99.5%, Usage 7.41h, Leak 0.0 |
| Smartwatch Demo | `fitbit_demo` | ✅ Working | 91 records, Sleep Score 58.71, HRV 21.88ms, SpO2 91.37% |
| Garmin CSV Upload | `csv` (generic) | ✅ Working | 28 records, multi-source merge supported |
| CPAP .edf Upload | `cpap` | ✅ Working | Auto-detected via file extension |
| CPAP JSON Upload | `cpap` (via `_sniff_json`) | ✅ Working | Sniffs JSON content for CPAP fields (`device`, `patient`, `records`) |
| Apple Health XML | `apple_health` | ✅ Working | Auto-detected via `.xml` extension |
| Fitbit JSON Upload | `fitbit` | ✅ Working | Auto-detected via `.json` extension; list-type JSON |
| ZIP upload | auto-sniff | ✅ Working | Sniffs internal file structure for EDF / XML / Fitbit |

## Dashboard UI

| Component | Status | Notes |
|-----------|--------|-------|
| Upload screen (drag & drop + file picker) | ✅ Working | |
| CPAP 4 metric cards (AHI, Compliance, Usage, Leak) | ✅ Working | Parsed from `key_metrics` response |
| Wearable 5 metric cards (Score, HRV, SpO2, Deep, Total) | ✅ Working | |
| Trend chart (AHI, usage_hrs, leak_95, press_95) | ✅ Working | Chart.js 4.4.7, 30-day default range |
| Chart date range buttons (7d, 14d, 30d, 90d, All, Custom) | ✅ Working | |
| Flags / insights panel | ✅ Working | |
| Multi-source tabs | ✅ Working | Switch between CPAP and CSV in same session |
| Source tag with DEMO badge | ✅ Working | |
| Theme toggle (dark/light) | ✅ Working | Persisted in localStorage |
| Clear data button | ✅ Working | |
| Remove individual source | ✅ Working | |

## LLM Chat

| Feature | Status | Notes |
|---------|--------|-------|
| Azure AI Foundry agent integration | ✅ Working | Uses Foundry API key |
| Medical knowledge base (45 entries) | ✅ Working | In `foundry_iq.py` |
| Multi-source cross-analysis | ✅ Working | Builds merged context for LLM |
| Chat history in session | ✅ Working | |
| Chat suggestions | ✅ Working | |

## Audio / Speech

| Feature | Status | Notes |
|---------|--------|-------|
| Text-to-speech | ❌ Not implemented | No audio output feature |
| Speech-to-text (voice input) | ❌ Not implemented | No speech recognition |
| Audio playback of analysis | ❌ Not implemented | Not in scope |

## API Endpoints

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/` | GET | ✅ | Serves SPA from `PAGE_HTML` |
| `/api/status` | GET | ✅ | Session health + source info |
| `/api/upload` | POST | ✅ | File upload with source hint |
| `/api/load-demo` | POST | ✅ | Loads CPAP demo (cpap_data.json) |
| `/api/load-wearable-demo` | POST | ✅ | Loads smartwatch demo |
| `/api/source-data` | GET | ✅ | Filtered data for chart range |
| `/api/remove-source` | POST | ✅ | Remove one data source |
| `/api/clear-data` | POST | ✅ | Clear all session data |
| `/api/chat` | POST | ✅ | LLM agent chat |
| `/api/csv-template` | GET | ✅ | Download CSV template |

## Deployment

| Item | Status | Notes |
|------|--------|-------|
| App Service Plan | B1 (Basic) | 1 core, 1.75 GB RAM |
| Free Tier auto-upgrade | Opted out | `tierUpgradePolicy: NoAutoUpgrade` |
| Deploy method | Kudu ZipDeploy API | Publish profile credentials |
| Compression | Images ~98% smaller | logo 8KB, hero 83KB, social 27KB, arch 32KB |

## Bug Fixes (June 11)

| Bug | Cause | Fix | File |
|-----|-------|-----|------|
| CPAP cards missing when uploading own data (`source: "auto"` returned to frontend) | `source_hint` not updated after auto-detection when `parse_hint` was introduced | Added `source_hint = parse_hint` after detection block | `orchestrator.py:286` |
| CPAP JSON upload failed ("No records found") | `.json` always detected as `fitbit`; CPAP data parsed by wrong parser | Added `_sniff_json()` — checks for CPAP-specific keys | `orchestrator.py:426-442` |
| CPAP demo button never worked | `source_hint='cpap_demo'` didn't match `source_hint == 'cpap'` in parser | Added `parse_hint = source_hint.replace('_demo', '')` for parsing only | `orchestrator.py:280` |
| CSV `date` column `Sleep Score 4 Weeks` accidentally removed | Over-aggressive cleanup of date candidates | Reverted to original date column list | `fitbit_csv_tool.py:136` |

## Upcoming / Desired

- [ ] Audio / speech output for LLM analysis
- [ ] Voice input for chat
