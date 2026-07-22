"""
Monday.com Business Intelligence Agent
Main Streamlit Application — Dark Glassmorphism Edition
"""

import os
import re
import streamlit as st
from monday_client import discover_board_ids, get_work_orders, get_deals
from data_cleaner import build_work_orders_df, build_deals_df, format_currency, data_quality_report
from agent import BIAgent

# ─── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="BizIntel — Monday.com AI Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS ──────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ─── Global ─── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #0d1117;
    background-image:
        radial-gradient(ellipse 80% 50% at 20% -20%, rgba(99,102,241,0.18) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(139,92,246,0.12) 0%, transparent 55%);
    min-height: 100vh;
}

/* ─── Hide Streamlit Branding ─── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ─── Sidebar ─── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080812 0%, #0d0d20 60%, #0a0a1a 100%) !important;
    border-right: 1px solid rgba(99,102,241,0.25) !important;
    box-shadow: 4px 0 30px rgba(99,102,241,0.08);
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 0;
    padding-left: 0.75rem;
    padding-right: 0.75rem;
}

/* ─── Sidebar Toggle (Arrow) ─── */
[data-testid="collapsedControl"] {
    background: rgba(99,102,241,0.2) !important;
    border-radius: 50% !important;
    border: 1px solid rgba(99,102,241,0.5) !important;
    margin: 10px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 0 15px rgba(99,102,241,0.4) !important;
}

[data-testid="collapsedControl"]:hover {
    background: rgba(99,102,241,0.4) !important;
    box-shadow: 0 0 25px rgba(99,102,241,0.7) !important;
    transform: scale(1.15) !important;
}

[data-testid="collapsedControl"] svg {
    color: #ffffff !important;
    fill: #ffffff !important;
    width: 28px !important;
    height: 28px !important;
}

/* ─── Sidebar Brand ─── */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    padding: 1.5rem 1rem 0.75rem;
    background: linear-gradient(135deg, rgba(99,102,241,0.12) 0%, rgba(139,92,246,0.06) 100%);
    border-bottom: 1px solid rgba(99,102,241,0.15);
    margin-bottom: 0;
}

.sidebar-logo-icon {
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    box-shadow: 0 4px 20px rgba(99,102,241,0.5), inset 0 1px 0 rgba(255,255,255,0.15);
    flex-shrink: 0;
}

.sidebar-logo-text .title {
    color: #ffffff;
    font-weight: 800;
    font-size: 1.15rem;
    line-height: 1;
    letter-spacing: -0.4px;
}

.sidebar-logo-text .subtitle {
    background: linear-gradient(90deg, #6366f1, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-top: 0.25rem;
}

/* ─── Sidebar Status Badge ─── */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0.75rem;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}

.status-pill.connected {
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.3);
    color: #22c55e;
}

.status-pill.disconnected {
    background: rgba(248,113,113,0.12);
    border: 1px solid rgba(248,113,113,0.3);
    color: #f87171;
}

.status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
    animation: blink 2s ease-in-out infinite;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* ─── Sidebar Stats Cards ─── */
.stat-mini {
    background: rgba(22,27,39,0.8);
    border: 1px solid rgba(99,102,241,0.15);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.stat-mini-label {
    color: #64748b;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.stat-mini-value {
    color: #a5b4fc;
    font-size: 0.9rem;
    font-weight: 700;
}

/* ─── Config label ─── */
.config-label {
    color: #64748b;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.6rem;
    padding: 0 0.25rem;
}

/* ─── Header ─── */
.bi-header {
    padding: 3rem 2.5rem 2.5rem 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    background: linear-gradient(135deg, rgba(10,10,26,0.95) 0%, rgba(20,16,40,0.9) 100%);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 24px;
    overflow: hidden;
    backdrop-filter: blur(20px);
    box-shadow:
        0 0 0 1px rgba(99,102,241,0.1),
        0 40px 80px rgba(0,0,0,0.5),
        inset 0 1px 0 rgba(255,255,255,0.06);
}

/* Glow orbs inside header */
.bi-header::before {
    content: '';
    position: absolute;
    top: -60px; left: -60px;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(99,102,241,0.25) 0%, transparent 65%);
    pointer-events: none;
}

.bi-header::after {
    content: '';
    position: absolute;
    bottom: -80px; right: -40px;
    width: 320px; height: 220px;
    background: radial-gradient(circle, rgba(139,92,246,0.18) 0%, transparent 65%);
    pointer-events: none;
}

/* top accent line */
.bi-header-line {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #6366f1, #8b5cf6, #a78bfa, transparent);
}

.bi-header h1 {
    color: #ffffff;
    font-size: 3.4rem;
    font-weight: 900;
    margin: 0 0 0.9rem 0;
    letter-spacing: -2px;
    line-height: 1.0;
    position: relative;
    z-index: 1;
    text-shadow: 0 2px 40px rgba(99,102,241,0.25);
}

.bi-header h1 .highlight {
    background: linear-gradient(120deg, #818cf8 0%, #a78bfa 40%, #c4b5fd 70%, #e0d7ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 0 20px rgba(139,92,246,0.5));
}

.bi-header p {
    color: rgba(255,255,255,0.6);
    font-size: 1.05rem;
    font-weight: 400;
    line-height: 1.65;
    max-width: 620px;
    position: relative;
    z-index: 1;
}

.bi-header p .accent {
    color: #c4b5fd;
    font-weight: 700;
}

/* Header divider rule */
.bi-header-rule {
    height: 1px;
    background: linear-gradient(90deg, rgba(255,255,255,0.08), rgba(99,102,241,0.3), rgba(255,255,255,0.04));
    margin: 1.5rem 0 0;
    position: relative;
    z-index: 1;
}


/* ─── HERO CHAT SECTION ─── */
.chat-hero-wrapper {
    background: rgba(15,20,35,0.85);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 24px;
    overflow: hidden;
    box-shadow: 0 0 0 1px rgba(99,102,241,0.06), 0 40px 80px rgba(0,0,0,0.4);
    backdrop-filter: blur(20px);
    position: relative;
    margin-bottom: 2rem;
}

.chat-hero-wrapper::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #a78bfa, #8b5cf6, #6366f1);
    background-size: 200% 100%;
    animation: gradientShift 4s linear infinite;
}

@keyframes gradientShift {
    0% { background-position: 0% 0%; }
    100% { background-position: 200% 0%; }
}

.chat-title-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.1rem 1.5rem;
    border-bottom: 1px solid rgba(99,102,241,0.12);
    background: rgba(10,10,26,0.5);
}

.chat-title-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.chat-ai-avatar {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    box-shadow: 0 4px 12px rgba(99,102,241,0.4);
    flex-shrink: 0;
}

.chat-title-text .name {
    color: #e2e8f0;
    font-weight: 700;
    font-size: 0.9rem;
}

.chat-title-text .status {
    color: #22c55e;
    font-size: 0.65rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.3rem;
}

.chat-title-text .status::before {
    content: '';
    display: inline-block;
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #22c55e;
    animation: blink 2s infinite;
}

/* ─── Quick Query Chips ─── */
.chips-bar {
    padding: 0.8rem 1.5rem;
    border-bottom: 1px solid rgba(99,102,241,0.08);
    background: rgba(13,17,23,0.4);
}

.chips-label {
    color: #475569;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
}

/* ─── Chat Messages ─── */
.chat-container {
    padding: 1.5rem;
    min-height: 380px;
    max-height: 520px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: rgba(99,102,241,0.3) transparent;
}

.chat-container::-webkit-scrollbar { width: 4px; }
.chat-container::-webkit-scrollbar-track { background: transparent; }
.chat-container::-webkit-scrollbar-thumb {
    background: rgba(99,102,241,0.3);
    border-radius: 2px;
}

.msg-user {
    display: flex;
    justify-content: flex-end;
    margin: 0.75rem 0;
    animation: slideInRight 0.3s cubic-bezier(0.4,0,0.2,1);
}

.msg-user-bubble {
    background: linear-gradient(135deg, #6366f1, #7c3aed);
    color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 0.8rem 1.2rem;
    max-width: 72%;
    font-size: 0.88rem;
    line-height: 1.55;
    box-shadow: 0 4px 15px rgba(99,102,241,0.35);
}

.msg-agent {
    display: flex;
    justify-content: flex-start;
    align-items: flex-start;
    gap: 0.6rem;
    margin: 0.75rem 0;
    animation: slideInLeft 0.3s cubic-bezier(0.4,0,0.2,1);
}

.agent-avatar {
    width: 30px;
    height: 30px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    flex-shrink: 0;
    margin-top: 2px;
    box-shadow: 0 2px 8px rgba(99,102,241,0.3);
}

.msg-agent-bubble {
    background: rgba(30,37,53,0.9);
    border: 1px solid rgba(99,102,241,0.15);
    color: #e2e8f0;
    border-radius: 4px 18px 18px 18px;
    padding: 0.8rem 1.2rem;
    max-width: 78%;
    font-size: 0.88rem;
    line-height: 1.65;
}

.msg-agent-bubble strong { color: #a5b4fc; }
.msg-agent-bubble em { color: #94a3b8; }
.msg-agent-bubble code {
    background: rgba(99,102,241,0.15);
    color: #c4b5fd;
    padding: 0.1rem 0.3rem;
    border-radius: 4px;
    font-size: 0.82rem;
}

.chat-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 300px;
    gap: 1rem;
    color: #475569;
}

.chat-empty-icon {
    font-size: 3rem;
    opacity: 0.5;
    animation: floatIcon 3s ease-in-out infinite;
}

@keyframes floatIcon {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}

.chat-empty-text {
    font-size: 0.9rem;
    font-weight: 500;
    text-align: center;
    line-height: 1.5;
    max-width: 300px;
}

/* ─── Chat Input Area ─── */
.chat-input-area {
    padding: 1rem 1.5rem;
    border-top: 1px solid rgba(99,102,241,0.12);
    background: rgba(10,10,26,0.6);
}

@keyframes slideInRight {
    from { opacity: 0; transform: translateX(15px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-15px); }
    to { opacity: 1; transform: translateX(0); }
}

/* ─── Input Overrides ─── */
.stTextInput input, .stTextArea textarea {
    background: rgba(22,27,39,0.9) !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.75rem 1rem !important;
    transition: all 0.2s ease !important;
}

.stTextInput input::placeholder, .stTextArea textarea::placeholder {
    color: #475569 !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12), 0 0 20px rgba(99,102,241,0.08) !important;
}

/* ─── Buttons ─── */
.stButton > button,
[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #6366f1, #7c3aed) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.25s ease !important;
    font-size: 0.88rem !important;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3) !important;
    letter-spacing: 0.01em !important;
}

.stButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    background: linear-gradient(135deg, #4f46e5, #6d28d9) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(99,102,241,0.45) !important;
}

.stButton > button:active,
[data-testid="stFormSubmitButton"] > button:active {
    transform: translateY(0) !important;
}

/* ─── Divider ─── */
hr { border-color: rgba(99,102,241,0.1) !important; }

/* ─── Expander ─── */
.streamlit-expanderHeader {
    background: rgba(22,27,39,0.6) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(99,102,241,0.12) !important;
    font-weight: 600 !important;
}

.streamlit-expanderHeader * { color: #e2e8f0 !important; opacity: 1 !important; }
[role="group"] { color: #e2e8f0 !important; }
[role="group"] * { color: #e2e8f0 !important; opacity: 1 !important; }
[role="group"] p { color: #e2e8f0 !important; opacity: 1 !important; }


/* ─── Tables ─── */
.dataframe {
    background: rgba(22,27,39,0.8) !important;
    border: 1px solid rgba(99,102,241,0.12) !important;
    border-radius: 12px !important;
}


/* ─── Metric widget overrides ─── */
[data-testid="stMetricValue"] {
    color: #e2e8f0 !important;
    font-weight: 800 !important;
    font-size: 1.6rem !important;
}

[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
    font-weight: 600 !important;
}

[data-testid="metric-container"] {
    background: rgba(22,27,39,0.7) !important;
    border: 1px solid rgba(99,102,241,0.12) !important;
    border-radius: 16px !important;
    padding: 1.25rem 1.5rem !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.3s ease !important;
}

[data-testid="metric-container"]:hover {
    border-color: rgba(99,102,241,0.35) !important;
    transform: translateY(-4px) !important;
    box-shadow: 0 20px 40px rgba(99,102,241,0.15) !important;
}

/* ─── Sidebar button overrides (secondary style) ─── */
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(99,102,241,0.1) !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    color: #a5b4fc !important;
    box-shadow: none !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(99,102,241,0.2) !important;
    border-color: rgba(99,102,241,0.5) !important;
    color: #e2e8f0 !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.2) !important;
}

/* ─── Spinner ─── */
.stSpinner > div {
    border-color: #6366f1 transparent transparent transparent !important;
}

</style>
""", unsafe_allow_html=True)

# ─── Session State ─────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = None
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "wo_df" not in st.session_state:
    st.session_state.wo_df = None
if "deals_df" not in st.session_state:
    st.session_state.deals_df = None
if "connection_error" not in st.session_state:
    st.session_state.connection_error = None

# ─── Auto-Connect (reads secrets on first load) ───────────────────────────────

def _try_autoconnect():
    try:
        token     = st.secrets.get("MONDAY_API_TOKEN", "")
        groq_key  = st.secrets.get("GROQ_API_KEY", "")
        wo_id     = st.secrets.get("WO_BOARD_ID", "")
        deals_id  = st.secrets.get("DEALS_BOARD_ID", "")

        missing_secrets = []
        if not token:    missing_secrets.append("MONDAY_API_TOKEN")
        if not groq_key: missing_secrets.append("GROQ_API_KEY")
        if not wo_id:    missing_secrets.append("WO_BOARD_ID")
        if not deals_id: missing_secrets.append("DEALS_BOARD_ID")

        if missing_secrets:
            st.session_state.connection_error = f"Missing secrets: {', '.join(missing_secrets)}"
            return

        os.environ["MONDAY_API_TOKEN"] = token
        os.environ["GROQ_API_KEY"]     = groq_key

        agent = BIAgent(wo_id, deals_id)
        wo_df, deals_df = agent.load_data()
        st.session_state.agent       = agent
        st.session_state.wo_df       = wo_df
        st.session_state.deals_df    = deals_df
        st.session_state.data_loaded = True
        st.session_state.messages    = [{
            "role": "assistant",
            "content": (
                f"👋 Hey! I'm connected to Monday.com — loaded **{len(wo_df)} work orders** "
                f"and **{len(deals_df)} deals** into memory.\n\n"
                "I can answer anything about your pipeline: deal health, sector performance, "
                "revenue breakdown, at-risk accounts, or generate a **Leadership Brief** for your board. "
                "What would you like to explore first?"
            )
        }]
    except Exception as e:
        st.session_state.connection_error = str(e)

if not st.session_state.data_loaded:
    _try_autoconnect()

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    # Logo
    connected = st.session_state.data_loaded
    status_class = "connected" if connected else "disconnected"
    status_text  = "● Live" if connected else "○ Offline"

    st.markdown(f"""
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">📊</div>
        <div class="sidebar-logo-text">
            <div class="title">BizIntel</div>
            <div class="subtitle">AI Agent</div>
        </div>
    </div>
    <div style="padding: 0 1rem 1rem;">
        <span class="status-pill {status_class}">
            <span class="status-dot"></span>
            {status_text}
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    if st.session_state.data_loaded:
        wo_df    = st.session_state.wo_df
        deals_df = st.session_state.deals_df

        st.markdown('<div class="config-label">📈 Data Overview</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="stat-mini">
            <span class="stat-mini-label">📋 Work Orders</span>
            <span class="stat-mini-value">{len(wo_df)}</span>
        </div>
        <div class="stat-mini">
            <span class="stat-mini-label">💼 Deals</span>
            <span class="stat-mini-value">{len(deals_df)}</span>
        </div>
        <div class="stat-mini">
            <span class="stat-mini-label">🔄 Cache TTL</span>
            <span class="stat-mini-value">5 min</span>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        st.markdown('<div class="config-label">⚡ Actions</div>', unsafe_allow_html=True)

        if st.button("📋 Leadership Brief", use_container_width=True):
            with st.spinner("Generating brief..."):
                brief = st.session_state.agent.generate_leadership_brief()
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"📋 **Leadership Update Brief**\n\n{brief}"
                })
                st.rerun()

        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.session_state.data_loaded = False
            st.session_state.agent       = None
            st.session_state.wo_df       = None
            st.session_state.deals_df    = None
            st.rerun()

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

# ─── Main Area ────────────────────────────────────────────────────────────────

st.markdown("""
<div class="bi-header">
    <div class="bi-header-line"></div>
    <h1>Business Intelligence<br><span class="highlight">AI Agent</span></h1>
    <p>Real-time insights from your Monday.com data. <span class="accent">Ask anything</span> — pipeline health, deal performance, revenue breakdowns — and get instant answers.</p>
    <div class="bi-header-rule"></div>
</div>
""", unsafe_allow_html=True)

# ─── Metrics Row ──────────────────────────────────────────────────────────────

if st.session_state.data_loaded:
    wo_df    = st.session_state.wo_df
    deals_df = st.session_state.deals_df

    total_pipeline = deals_df["value"].sum() if not deals_df.empty else 0
    total_wo_value = wo_df["value"].sum()    if not wo_df.empty    else 0
    open_deals  = len(deals_df[deals_df["status"].isin(["Open","In Progress","New","Pending"])]) if not deals_df.empty else 0
    won_deals   = len(deals_df[deals_df["status"] == "Won"]) if not deals_df.empty else 0
    win_rate    = (won_deals / len(deals_df) * 100) if not deals_df.empty and len(deals_df) > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Total Pipeline",    format_currency(total_pipeline) if total_pipeline > 0 else "N/A")
    with col2:
        st.metric("📋 Work Orders Value", format_currency(total_wo_value) if total_wo_value > 0 else "N/A")
    with col3:
        st.metric("🎯 Open Deals",        f"{open_deals}")
    with col4:
        st.metric("✅ Win Rate",           f"{win_rate:.1f}%" if win_rate > 0 else "N/A")

    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

# ─── Not Connected Banner ─────────────────────────────────────────────────────

if not st.session_state.data_loaded:
    if st.session_state.connection_error:
        st.markdown("""
        <div style="
            background: rgba(248,113,113,0.06);
            border: 1px solid rgba(248,113,113,0.25);
            border-radius: 16px;
            padding: 2rem;
            margin: 2rem 0;
        ">
            <div style="font-size: 1.4rem; margin-bottom: 0.75rem; color:#f87171; font-weight:700;">❌ Connection Failed</div>
            <div style="color: #f87171; font-size: 0.9rem; margin-bottom: 1rem; font-family: 'Courier New', monospace; background: rgba(248,113,113,0.06); padding: 0.75rem; border-radius: 8px;">
                """ + st.session_state.connection_error.replace("<", "&lt;").replace(">", "&gt;") + """
            </div>
            <div style="color: #94a3b8; font-size: 0.85rem; line-height: 1.8;">
                <strong style="color:#e2e8f0">What to check:</strong><br>
                ✓ All API keys set in <code style="background:rgba(99,102,241,0.15);color:#c4b5fd;padding:0.1rem 0.3rem;border-radius:3px;">.streamlit/secrets.toml</code><br>
                ✓ Required: <code style="background:rgba(99,102,241,0.15);color:#c4b5fd;padding:0.1rem 0.3rem;border-radius:3px;">MONDAY_API_TOKEN</code>, <code style="background:rgba(99,102,241,0.15);color:#c4b5fd;padding:0.1rem 0.3rem;border-radius:3px;">GROQ_API_KEY</code>, <code style="background:rgba(99,102,241,0.15);color:#c4b5fd;padding:0.1rem 0.3rem;border-radius:3px;">WO_BOARD_ID</code>, <code style="background:rgba(99,102,241,0.15);color:#c4b5fd;padding:0.1rem 0.3rem;border-radius:3px;">DEALS_BOARD_ID</code><br>
                ✓ API keys valid and not expired<br>
                ✓ Board IDs accessible with your token
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="
            background: rgba(99,102,241,0.06);
            border: 1px solid rgba(99,102,241,0.2);
            border-radius: 16px;
            padding: 3rem;
            text-align: center;
            margin: 2rem 0;
        ">
            <div style="font-size: 3.5rem; margin-bottom: 1rem; animation: floatIcon 3s ease-in-out infinite;">⏳</div>
            <div style="color: #a78bfa; font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem;">Connecting to Monday.com...</div>
            <div style="color: #475569; font-size: 0.85rem;">Loading your boards automatically from configuration.</div>
        </div>
        """, unsafe_allow_html=True)

# ─── HERO CHAT INTERFACE ───────────────────────────────────────────────────────

if st.session_state.data_loaded:

    # Quick query chips above the hero panel
    quick_queries = [
        "Pipeline overview",
        "Energy sector performance",
        "Win rate this quarter",
        "Top 5 open deals",
        "Work orders by status",
        "Revenue by sector",
        "At-risk deals",
        "Leadership brief",
    ]

    quick_clicked = None

    # ── Open the hero chat card ──
    st.markdown("""
    <div class="chat-hero-wrapper">
        <div class="chat-title-bar">
            <div class="chat-title-left">
                <div class="chat-ai-avatar">🤖</div>
                <div class="chat-title-text">
                    <div class="name">BizIntel AI Assistant</div>
                    <div class="status">Online · Ready to analyse</div>
                </div>
            </div>
        </div>
        <div class="chips-bar">
            <div class="chips-label">⚡ Quick queries</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick-query buttons rendered by Streamlit (inside the visual card via CSS overlap trick)
    chip_cols = st.columns(4)
    for i, query in enumerate(quick_queries[:4]):
        with chip_cols[i % 4]:
            if st.button(query, key=f"chip_{i}", use_container_width=True):
                quick_clicked = query

    chip_cols2 = st.columns(4)
    for i, query in enumerate(quick_queries[4:]):
        with chip_cols2[i % 4]:
            if st.button(query, key=f"chip2_{i}", use_container_width=True):
                quick_clicked = query

    st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)

    # ── Build and render chat messages ──
    chat_html = '<div class="chat-container" id="chat-box">'

    if not st.session_state.messages:
        chat_html += """
        <div class="chat-empty">
            <div class="chat-empty-icon">💬</div>
            <div class="chat-empty-text">
                Ask me anything about your business data.<br>
                <span style="color:#6366f1; font-weight:600;">I'm ready to analyse your pipeline.</span>
            </div>
        </div>"""
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                chat_html += f'''
                <div class="msg-user">
                    <div class="msg-user-bubble">{msg["content"]}</div>
                </div>'''
            else:
                content = msg["content"].replace("\n", "<br>")
                content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
                content = re.sub(r'\*(.*?)\*',     r'<em>\1</em>',         content)
                content = re.sub(r'`(.*?)`',       r'<code>\1</code>',     content)
                chat_html += f'''
                <div class="msg-agent">
                    <div class="agent-avatar">🤖</div>
                    <div class="msg-agent-bubble">{content}</div>
                </div>'''

    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)

    # Auto-scroll
    st.markdown("""
    <script>
        const chatBox = document.getElementById('chat-box');
        if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
    </script>
    """, unsafe_allow_html=True)

    # ── Chat Input ──
    st.markdown('<div class="chat-input-area" style="margin-top:-0.5rem;">', unsafe_allow_html=True)
    with st.form(key="chat_form", clear_on_submit=True):
        cols = st.columns([7, 1])
        with cols[0]:
            user_input = st.text_input(
                "Message",
                placeholder="Ask anything — 'How's our pipeline?', 'Top deals this month?', 'At-risk accounts?'",
                label_visibility="collapsed",
                key="chat_input"
            )
        with cols[1]:
            submitted = st.form_submit_button("Send ➤", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Process query ──
    query_to_process = None
    if submitted and user_input:
        query_to_process = user_input
    elif quick_clicked:
        query_to_process = quick_clicked

    if query_to_process:
        st.session_state.messages.append({"role": "user", "content": query_to_process})
        with st.spinner("Analysing your data..."):
            try:
                response = st.session_state.agent.chat(
                    query_to_process,
                    st.session_state.messages[:-1]
                )
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"⚠️ **Error:** {str(e)}"
                })
        st.rerun()

    # ── Data Preview Expanders ──
    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

    with st.expander(f"🔍 Preview Work Orders Data — all {len(st.session_state.wo_df)} records"):
        if st.session_state.wo_df is not None and not st.session_state.wo_df.empty:
            display_cols = [c for c in st.session_state.wo_df.columns if c != "_raw"]
            st.dataframe(st.session_state.wo_df[display_cols], use_container_width=True)
        else:
            st.info("No work orders data loaded")

    with st.expander(f"🔍 Preview Deals Data — all {len(st.session_state.deals_df)} records"):
        if st.session_state.deals_df is not None and not st.session_state.deals_df.empty:
            display_cols = [c for c in st.session_state.deals_df.columns if c != "_raw"]
            st.dataframe(st.session_state.deals_df[display_cols], use_container_width=True)
        else:
            st.info("No deals data loaded")
