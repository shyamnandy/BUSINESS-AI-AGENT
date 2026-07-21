# BizIntel — Monday.com AI Business Intelligence Agent

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│             Streamlit Chat UI               │
│         (app.py — single file UI)           │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│              BIAgent (agent.py)             │
│  • Query routing & filter extraction        │
│  • Groq Llama 3.3-70b — natural language AI │
│  • Leadership brief generation              │
└──────────┬──────────────────┬───────────────┘
           │                  │
┌──────────▼──────┐  ┌────────▼────────────────┐
│ monday_client.py│  │   data_cleaner.py        │
│ • GraphQL API   │  │ • Date normalization     │
│ • Pagination    │  │ • Currency parsing       │
│ • 5-min cache   │  │ • Null handling          │
│ • Error handling│  │ • Sector normalization   │
└─────────────────┘  └─────────────────────────┘
```

## File Structure

```
BUSINESS AGENT/
├── app.py                  # Main Streamlit application
├── agent.py                # Groq AI agent + analysis logic
├── monday_client.py        # Monday.com GraphQL API client
├── data_cleaner.py         # Data normalization utilities
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── .streamlit/
    ├── config.toml         # Dark theme config
    └── secrets.toml        # API keys (local dev only, NOT committed)
```

## Setup Instructions

### Prerequisites
- Python 3.10+
- Monday.com account with API access
- Groq API key (free at console.groq.com)

### Local Setup

1. **Clone / download the project**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up secrets**
   Edit `.streamlit/secrets.toml`:
   ```toml
   MONDAY_API_TOKEN = "your_monday_api_token"
   GROQ_API_KEY = "your_groq_api_key"
   ```

4. **Run locally**
   ```bash
   streamlit run app.py
   ```

### Monday.com Board Configuration

**Getting your API Token:**
1. Go to monday.com → Click your avatar (bottom left)
2. Select `Developers` → `My Access Tokens`
3. Copy the personal token

**Getting Board IDs:**
- Option A: Use the **Auto-Detect** button in the sidebar
- Option B: Open your board → the URL shows `monday.com/boards/XXXXXXXX`

**Board Structure Expected:**
| Work Orders Board | Deals Board |
|---|---|
| Item Name (project/order name) | Item Name (deal name) |
| Customer Name | Company / Account |
| Status | Status / Stage |
| Sector / Industry | Sector / Industry |
| Value / Revenue | Value / Deal Value |
| Start Date | Close Date |
| End Date | Probability |
| Assigned To / Owner | Owner / Sales Rep |
| Priority | Priority |

> **Note:** Column names are flexible — the data cleaner tries multiple common naming conventions automatically.

### Deploying to Streamlit Cloud

1. Push this folder to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set secrets in Streamlit Cloud dashboard:
   - `MONDAY_API_TOKEN`
   - `GROQ_API_KEY`
5. Deploy — your app will be live at `yourapp.streamlit.app`

## Features

### Core
- **Natural language queries** — ask founder-level business questions
- **Cross-board analysis** — combines Work Orders + Deals insights
- **Real-time data** — live Monday.com queries with 5-minute cache
- **Data resilience** — handles nulls, messy dates, inconsistent naming

### Quick Queries (built-in)
- Pipeline overview
- Energy sector performance
- Win rate analysis
- Top open deals
- Work orders by status
- Revenue by sector
- At-risk deals identification

### Leadership Brief
- One-click executive summary generation
- Board meeting / investor update ready
- Covers: pipeline health, execution status, risks, recommendations

## Tech Stack Decisions

| Choice | Reason |
|---|---|
| **Streamlit** | Zero build step, fastest deploy, built-in secrets mgmt |
| **Groq Llama 3.3-70b** | Fast inference, free tier, excellent reasoning |
| **Monday.com REST/GraphQL** | No MCP server setup needed, direct and reliable |
| **Pandas** | Best-in-class for data analysis in Python |
| **No vector DB** | Overkill for structured tabular data; direct analysis is faster |
