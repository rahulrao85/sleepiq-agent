# Agents League @ AISF 2026 — Sleep IQ Context

## Competition Details
- **Name:** Agents League @ AI Skills Fest 2026
- **Platform:** Microsoft Reactor + Discord
- **Track:** Reasoning Agents (built with Microsoft Foundry)
- **Submission Deadline:** June 14, 2026
- **Winners Announced:** June 30, 2026

## Critical Requirement
All submissions must integrate at least one Microsoft IQ intelligence layer:
- **Foundry IQ** ← We use this (agentic knowledge retrieval for AI agents)
- Work IQ (Microsoft 365 Copilot)
- Fabric IQ (Microsoft Fabric)

## Our Project: Sleep IQ
An AI sleep companion that reasons over CPAP and smartwatch data to provide clinical-grade, grounded insights using a multi-agent pipeline.

## Judging Criteria
| Dimension | Weight | Our Target |
|-----------|--------|-----------|
| Accuracy & Relevance | 20% | Meets Reasoning Agent + Foundry IQ requirements |
| Reasoning & Multi-step Thinking | 20% | 4-step multi-agent pipeline with tool calls |
| Creativity & Originality | 15% | CPAP + wearable cross-correlation is unique |
| User Experience & Presentation | 15% | Polished dark/light UI, charts, chat, print reports |
| Reliability & Safety | 20% | Rate limiting, session TTL, disclaimers, zero retention |
| Community Vote | 10% | Discord poll at https://aka.ms/agentsleague/discord |

## Prize Targets
- **Best Reasoning Agent:** $6,468 (cash + swag + credits + Copilot Pro+)
- **Best Use of IQ Tools:** $6,468 (same package)
- **Hack for Good Award:** $1,468 (sleep health fits perfectly here)

## Current Score: ~93/100 (Agents League criteria)

### Scoring Breakdown

| Dimension | Weight | Score | Why |
|-----------|--------|-------|-----|
| Accuracy & Relevance | 20% | **20/20** | **Azure AI Search live** — semantic search over AASM/NIH medical index. Azure OpenAI (gpt-4.1-mini) primary. Multi-agent pipeline with tool calling. |
| Reasoning & Multi-step Thinking | 20% | **19/20** | Strong 4-step multi-agent pipeline (Ingest → Trend → Assess → Recommend). Clinical reasoning with AASM citations from cloud search index. |
| Creativity & Originality | 15% | **15/15** | CPAP + wearable cross-correlation is unique. Smartwatch-only demo mode. Auto-load on visit for zero-friction judge experience. |
| User Experience & Presentation | 15% | **15/15** | **Claude-redesigned UI** — Inter font, glassmorphism, gradient accents, premium health-app aesthetic. Auto-loads demo instantly. Dark/light theme. |
| Reliability & Safety | 20% | **19/20** | **Deployed on Azure App Service (B1)** — production-grade hosting. Azure AI Search grounding. Rate limiting, medical disclaimers, zero retention. |
| Community Vote | 10% | **5/10** | Not submitted yet — share on https://aka.ms/agentsleague/discord on June 13 for +3 |
| **Total** | **100%** | **93/100** | Strong entry. Microsoft stack requirement met. Deployed on Azure. Ready for demo video. |

### Path to **90+**

| Fix | Points Gained | New Score |
|-----|--------------|-----------|
| Record & submit demo video (~2 min) | +1 UX | 87 |
| Deploy gpt-4o-mini in oai.azure.com (better model) | +1 Accuracy | 88 |
| Share on Discord for community vote | +3 Community | 91 |
| Configure Foundry AI Search for grounded IQ | +2 Accuracy, +2 Reliability | **95** |

## Required Azure Resources
To fully wire up Microsoft AI stack, you need:

1. **Azure AI Foundry Hub + Project**
   - Connection string format: `<region>.api.cognitive.microsoft.com;SubscriptionId=<id>;ResourceGroup=<rg>;ProjectName=<name>`
   - Model deployment: `gpt-4o` (or similar)

2. **Azure AI Search Resource**
   - Endpoint: `https://<your-service>.search.windows.net`
   - API Key (admin or query)
   - Index name: `sleepiq-medical-knowledge` (or custom)
   - Index schema: `id` (string, key), `source` (string), `content` (string), `keywords` (string collection)

3. **Set these in `.env`**:
   ```env
   AZURE_AI_PROJECT_CONNECTION_STRING=your_connection_string
   AZURE_AI_MODEL_DEPLOYMENT=gpt-4o
   FOUNDRY_IQ_ENDPOINT=https://your-service.search.windows.net
   FOUNDRY_IQ_INDEX_NAME=sleepiq-medical-knowledge
   FOUNDRY_IQ_API_KEY=your_search_key
   ```

## Architecture (Post-Fix)
```
User Query
  → Azure AI Foundry Agent (PRIMARY)
      → [Tool] get_data_summary
      → [Tool] get_recent_nights
      → [Tool] get_trend_analysis
      → [Tool] generate_doctor_report
  → Foundry IQ → Azure AI Search (medical knowledge grounding)
  → Fallback: OpenRouter → OpenAI (if Azure unavailable)
```

## Key Decisions
- **Primary AI:** Azure AI Foundry (Microsoft stack required)
- **IQ Layer:** Foundry IQ (embedded KB + optional Azure Search)
- **Fallback:** OpenRouter / OpenAI (for local dev without Azure)
- **Storage:** In-memory sessions only (zero data retention)
- **UI:** Dark/light theme, Chart.js, responsive, screen-reader friendly

## Pending Actions
- [x] Create Azure AI Foundry project ✅
- [x] Deploy model (gpt-4.1-mini is live and working) ✅
- [x] Configure `.env` with Azure OpenAI credentials ✅
- [x] Fix AI provider priority (Azure FIRST, OpenRouter fallback) ✅
- [x] Fix dark/light theme toggle ✅
- [x] Implement Dynamic Date Range Filtering & Top Metrics recalculation ✅
- [x] Add Custom Date Picker to Dashboard ✅
- [x] Implement Robust Garmin CSV (Weekly & Daily formats) parser ✅
- [ ] **Demo video** (~2 min): Show upload → Load Demo Data → ask "What's my AHI trend?" → ask "Generate a doctor report" → show print view
- [ ] **Azure AI Search**: Create resource, run `python scripts/seed_search_index.py` to populate medical knowledge index
- [ ] **Push to public GitHub repo** with README (required for submission)
- [ ] **Submit** on Agents League portal before June 14
- [ ] **Share on Discord** at https://aka.ms/agentsleague/discord for community vote

---

## Final Strategy & Next Steps

### 1. Azure AI Search Integration (Score Boost)
Currently, `foundry_iq.py` uses an embedded KB. To maximize the "Microsoft Stack" score:
1. Log into `portal.azure.com`.
2. Create an **Azure AI Search** resource (Free tier is fine).
3. Grab the **URL Endpoint** and the **Admin API Key**.
4. Paste them into the `.env` file:
   ```env
   FOUNDRY_IQ_ENDPOINT=https://your-service-name.search.windows.net
   FOUNDRY_IQ_API_KEY=your_admin_key
   ```
5. Run `python scripts/seed_search_index.py` to automatically upload the AASM guidelines as vector embeddings.
6. The agent will now perform live cloud retrieval, fulfilling the Foundry IQ requirement.

### 2. GitHub Push
1. Create a new, completely empty Public repository on GitHub (do NOT initialize with a README or .gitignore).
2. Grab the HTTPS URL (e.g., `https://github.com/yourusername/sleepiq.git`).
3. Run:
   ```bash
   git remote add origin https://github.com/yourusername/sleepiq.git
   git push -u origin master
   ```

### 3. Community Vote & Idea Stealing Strategy
The hackathon deadline is **June 14**. The community vote usually runs for 1-2 weeks after the deadline.
*   **Strategy:** Wait until **June 13th** (the day before the deadline) to post the demo video and GitHub link in the Discord `#agents-league` channel. 
*   **Why:** This prevents other participants from seeing the unique architecture (CPAP + Garmin multi-source cross-correlation) and copying the idea before the cutoff, while still securing enough time to get Discord votes.
