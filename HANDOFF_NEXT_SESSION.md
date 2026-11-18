# Next Session — Pick Up Here

## ✅ Completed This Session (June 11)

### Logo & Images
- [x] Generated all 4 images (Logo, Hero, Architecture, Social) via LLM prompts
- [x] Logo swapped into `ui_template.py` (replaced "Z" placeholder → `<img src="/static/logo.jpeg">`)
- [x] All 4 images stored in `static/` folder and pushed to GitHub
- `IMAGE_PROMPTS.md` has the original prompts; `AGENTS_LEAGUE_CONTEXT.md` can be used as context input for better prompt generation

### Bug Fixes
- [x] **Flags/Observations not updating** when switching data sources — fixed `switchSource()` and `fetchWithFilters()` to call `renderFlags()`
- [x] **Same-source upload merge** — uploading two watch files (e.g., Jan + Feb) now merges records, dedupes by date, and recomputes stats
- [x] **Source tag layout** — fixed horizontal stretching (removed `display:flex` conflict), DEMO badge is now compact

### Multi-Source UX
- [x] **"+ Add another data source"** always visible, even in multi-source mode
- [x] **Source tabs** with active highlighting + **× remove button** per source
- [x] **"Clear all"** button resets everything to upload screen
- [x] **DEMO badge** (yellow pill) shown on demo data sources
- [x] Backend: `/api/remove-source` and `/api/clear-data` endpoints
- [x] Backend: `is_demo` tracking per data source
- [x] Backend: `_demo` suffix on source keys (e.g., `cpap_demo`, `fitbit_demo`)

### Bug Fixes
- [x] **CPAP demo button not working** — `source_hint='cpap_demo'` didn't match parser conditions. Fixed by adding `parse_hint` that strips `_demo` suffix for parsing while preserving original for session storage.
- [x] **CPAP cards missing on user upload** — `source_hint` stayed `'auto'` after auto-detection because `parse_hint` wasn't copied back. Frontend rendered wearable cards (null) instead. Added `source_hint = parse_hint` after detection.
- [x] **CPAP JSON upload failed** — all `.json` files assumed Fitbit format. Added `_sniff_json()` that checks for CPAP fields (`device`, `patient`, `records`).
- [x] **Deploy unreliable** — ZipDeploy via Python timed out; ZipDeploy via `Invoke-RestMethod` with 300s timeout works. Oryx builds take ~2 min.

### New
- [x] **`_sniff_json()` function** in `orchestrator.py` — distinguishes CPAP JSON (dict with device/patient/records) from Fitbit JSON (list or sleep-key dict)

### 🔴 Important: This session's commits are NOT pushed to GitHub. All changes are local + deployed to Azure only.

## 📋 Pending Before June 14 Deadline

- [ ] **Push all changes to GitHub** (`orchestrator.py`, `fitbit_csv_tool.py`, `ui_template.py`, `SLEEPIQ_FEATURES.md`, `HANDOFF_NEXT_SESSION.md`)
- [ ] **Record Demo Video** — Script in `DEMO_VIDEO_SCRIPT.md` (2 min walkthrough)
- [ ] **Submit on Agents League portal** (video + GitHub URL)
- [ ] **Share on Discord** on June 13 for community vote (+3 pts)
- [ ] **Audio/speech feature** not implemented yet — would need TTS and/or STT integration
- [ ] **Answer PromptWars Mumbai email** — drafted, ready to send

## URLs
- Repo: https://github.com/rahulrao85/sleepiq-agent
- Score: ~93/100 (demo video pushes to 95+)
- Deploy credentials: `$sleep-iq-app` / password in publish profile (expires 2027-06)
