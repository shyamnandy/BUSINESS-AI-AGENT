# Decision Log — BizIntel Monday.com BI Agent
**Author:** [Your Name] | **Date:** July 2026 | **Scope:** 2-hour build

---

## 1. Key Assumptions

**Data Shape**
- Monday.com boards have loosely structured columns (no strict schema enforced)
- Work Orders = project/delivery tracking; Deals = sales pipeline
- Data is real-world messy: mixed date formats, null values, inconsistent naming, currency strings

**User (Founder) Behavior**
- Queries are natural language, not SQL — "how's energy sector doing?" not "SELECT * FROM deals WHERE sector='Energy'"
- Founders want insight, not raw rows — they care about totals, trends, risks
- They don't want to be blocked by data quality issues — graceful degradation is mandatory

**Board Configuration**
- Column names vary (e.g., "Deal Value" vs "Value" vs "Amount") — built multi-alias resolution
- Boards might not have all expected columns — fallback to None/Unknown, never crash
- Auto-detect board IDs by name matching to reduce setup friction

---

## 2. Trade-offs and Why

### Streamlit over React/Next.js
**Chosen:** Streamlit  
**Why:** In a 2-hour window, a full React frontend + FastAPI backend setup would consume 40+ minutes on scaffolding alone. Streamlit gives a production-ready UI in minutes. The trade-off is less UI flexibility, but the custom CSS makes it look premium.

### Gemini 1.5 Flash over GPT-4o
**Chosen:** Gemini 1.5 Flash  
**Why:** Free tier available immediately, no billing setup needed, fast inference (~1-2s), and excellent instruction following. GPT-4o is marginally better at complex reasoning but requires paid API access and adds 5-10 min of setup.

### Direct REST/GraphQL over MCP
**Chosen:** Monday.com GraphQL API directly  
**Why:** MCP requires running a separate server process, port management, and more config. Direct API calls are stateless, simpler to debug, and deploy cleanly on Streamlit Cloud. The 2-hour constraint made this the only realistic choice.

### Deterministic Analysis + LLM Narration over Pure LLM
**Chosen:** Pandas analysis → context → Gemini narration  
**Why:** Letting an LLM query raw data directly risks hallucinated numbers. The architecture runs real aggregations (pandas), then feeds structured results to Gemini for natural language generation. This gives accurate numbers with human-readable explanations.

### 5-Minute Cache
**Chosen:** `@st.cache_data(ttl=300)`  
**Why:** Monday.com API has rate limits. Caching prevents hammering the API on every message while keeping data reasonably fresh. A full production system would use a database sync (e.g., PostgreSQL + cron).

---

## 3. What I'd Do Differently With More Time

1. **Persistent database layer** — Sync Monday.com to PostgreSQL hourly via a worker; query the DB instead of the API directly. This enables historical trend analysis and faster queries.

2. **Real function calling** — Implement proper Gemini function-calling (tool_config) instead of regex-based query routing. This would handle complex multi-part questions more reliably.

3. **Chart generation** — Add Plotly charts for pipeline funnel, sector breakdown, trend over time. The current text-only output is functional but visual dashboards communicate faster in leadership settings.

4. **Webhook integration** — Monday.com supports webhooks; real-time updates instead of polling.

5. **Auth layer** — Add Google OAuth or magic link auth so the prototype is safe to share publicly.

6. **Better date range queries** — "This quarter" vs "last quarter" vs "YTD" needs proper date arithmetic that accounts for partial quarters.

---

## 4. How I Interpreted "Leadership Updates"

**Interpretation:** A leadership update is a structured, opinionated document — not just a data dump. It answers: *What's happening? What's the risk? What should we do?*

**Implementation:** The "Generate Leadership Brief" button triggers a separate Gemini prompt engineered to produce:
1. **Executive Summary** (2-3 sentences — the TL;DR)
2. **Pipeline Health** (deal counts, total value, win rate, open vs closed)
3. **Execution Status** (work order completion, top customers, sector breakdown)
4. **Opportunities & Risks** (surfaced from data patterns — e.g., high-value deals stuck in pipeline)
5. **Recommended Actions** (2-3 bullets — decision prompts for the leadership team)

This format mirrors a standard board update or investor memo, making it immediately usable without editing.

---

## 5. Data Quality Approach

- **Null values:** Treated as `None`/`Unknown` — never crash, never assume
- **Date formats:** 11 formats tried sequentially + pandas fallback
- **Currency:** Handles `$1.2M`, `1,234.56`, `1200000` — extracts numeric value
- **Sector names:** Fuzzy keyword mapping (e.g., "oil" → "Energy", "saas" → "Technology")
- **Status normalization:** Maps 15+ variants to 7 canonical statuses
- **Transparency:** Data quality report (% missing per field) is always passed to the AI so it can caveat its answers honestly
