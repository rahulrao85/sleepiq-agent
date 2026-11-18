# Sleep IQ 🧠

> **An AI sleep companion that reasons over your CPAP and smartwatch data to provide clinical-grade, grounded insights.**

Built for the **Microsoft Agents League @ AI Skills Fest 2026** — Reasoning Agents track.

[![Sleep IQ Demo Video](https://img.youtube.com/vi/45pAnEqiic4/0.jpg)](https://www.youtube.com/watch?v=45pAnEqiic4)

## 🌟 The Vision

Sleep data is hard to understand. CPAP machines produce complex medical metrics (AHI, leak rates, event indices), and smartwatches produce massive amounts of lifestyle data (HRV, SpO2, sleep stages). 

**Sleep IQ** bridges the gap. It's a multi-agent reasoning system that ingests your health data, analyzes multi-month trends, and provides personalized, grounded insights—complete with visible reasoning chains and source citations.

Whether you're managing sleep apnea with a CPAP machine or just trying to understand your Apple Watch data, Sleep IQ acts as your personal sleep clinician.

## 🏆 Competition Categories Targeted

1. **🧠 Best Reasoning Agent:** Utilizes a 4-step multi-agent pipeline (Ingestion → Trend Analysis → Risk Assessment → Recommendation).
2. **💡 Best Use of IQ Tools:** Integrates **Foundry IQ** to ensure medical advice is grounded in AASM clinical guidelines (embedded KB + Azure AI Search).
3. **🎗️ Hack for Good:** Helps uncover undiagnosed sleep apnea by correlating SpO2 drops and HRV patterns in general smartwatch data.
4. **👥 Accessibility Award:** Built with high-contrast theme, screen-reader-friendly markup, and keyboard navigation.

## ⚙️ How It Works

Sleep IQ leverages a sophisticated architecture powered by **Microsoft Azure AI Foundry** (primary) with an OpenRouter fallback for local testing:

1. **Data Ingestion:** Parses ResMed `STR.edf`, Apple Health XML, Fitbit JSON, or generic CSV.
2. **Statistical Engine:** Computes severity scores, 95th percentiles, and detects multi-month trends.
3. **Reasoning Agent:** An orchestrator agent that dynamically calls tools (`get_data_summary`, `get_trend_analysis`, `get_recent_nights`) to build a complete picture of your health before answering any question.
4. **Grounded Output:** Every answer cites its reasoning steps and relies on medical knowledge constraints.

👉 **[View the full Architecture Diagram](architecture.md)**

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- **Azure subscription** with AI Foundry hub + AI Search (see setup guide below)
- OR OpenRouter API key (for local dev without Azure)

### Azure Resource Setup
1. **Azure AI Foundry Hub + Project**
   - Go to [ai.azure.com](https://ai.azure.com) → Create hub → Create project
   - Deploy a model (e.g. `gpt-4o`)
   - Copy the **Project Connection String** from project settings

2. **Azure AI Search**
   - Go to [portal.azure.com](https://portal.azure.com) → Create Azure AI Search
   - Choose Basic tier or higher
   - Copy the endpoint URL and admin key

3. **Seed the knowledge index**
   ```bash
   python scripts/seed_search_index.py
   ```

### Installation
```bash
git clone https://github.com/yourusername/sleepiq-agent.git
cd sleepiq-agent
pip install -r requirements.txt
```

### Configuration
Copy the environment template and add your Azure credentials:
```bash
cp .env.example .env
```
Edit `.env` to include your **Azure AI Foundry connection string** (primary path):
- `AZURE_AI_PROJECT_CONNECTION_STRING` from your AI Foundry project
- `FOUNDRY_IQ_ENDPOINT`, `FOUNDRY_IQ_API_KEY` from Azure AI Search
- Or set `OPENROUTER_API_KEY` for local development without Azure

### Running the App

#### Option 1: Direct Python
```bash
python app.py
```

#### Option 2: Docker
```bash
docker compose up --build
```

The app will launch at `http://localhost:5000`.

### Testing the AI
1. Click **"Load Demo Data"** — loads 365 days of synthetic CPAP data instantly
2. Try clicking one of the **suggested questions** that appear below the chat
3. Ask custom questions like *"What's causing my AHI spikes?"* or *"Is my therapy working?"*
4. Click **"Print"** above the chart for a doctor-ready summary

## 🧪 Testing with Demo Data
Don't have CPAP data handy? Click the **"Load Demo Data"** button on the upload screen to load a complete, anonymized 365-day ResMed CPAP dataset and see the agent in action.

## 🔒 Privacy & Safety
- **Zero Data Retention:** All data processing occurs entirely in memory during your active session. No health data is ever saved to a database or disk.
- **Not Medical Advice:** The agent is heavily constrained to avoid making definitive medical diagnoses, instead framing insights as patterns to discuss with a clinician.

---
*Built by Rahul Rao for the Microsoft Agents League Hackathon.*

> **Data note:** `cpap_data.json` and `wearable_demo_data.json` are synthetic demo data. They describe no real person or device.
