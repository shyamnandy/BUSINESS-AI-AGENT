"""
Monday.com Business Intelligence Agent
Main Streamlit Application
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ─── Global ─── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0a0a1a 0%, #0d1117 50%, #0a1628 100%);
    min-height: 100vh;
}

/* ─── Hide Streamlit Branding ─── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ─── Sidebar ─── */
section[data-testid="stSidebar"] {
    background: rgba(13, 17, 23, 0.95) !important;
    border-right: 1px solid rgba(255,255,255,0.06);
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 2rem;
}

/* ─── Header ─── */
.bi-header {
    background: linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(168,85,247,0.1) 100%);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(20px);
}

.bi-header h1 {
    color: #e2e8f0;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0;
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.bi-header p {
    color: #94a3b8;
    font-size: 0.9rem;
    margin: 0.3rem 0 0;
}

/* ─── Metric Cards ─── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.metric-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    transition: all 0.2s ease;
}

.metric-card:hover {
    border-color: rgba(99,102,241,0.4);
    background: rgba(99,102,241,0.08);
    transform: translateY(-2px);
}

.metric-label {
    color: #64748b;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
}

.metric-value {
    color: #e2e8f0;
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1;
}

.metric-sub {
    color: #94a3b8;
    font-size: 0.75rem;
    margin-top: 0.3rem;
}

.metric-up { color: #34d399; }
.metric-down { color: #f87171; }

/* ─── Chat Container ─── */
.chat-container {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 1.5rem;
    min-height: 400px;
    max-height: 600px;
    overflow-y: auto;
    margin-bottom: 1rem;
}

/* ─── Chat Bubbles ─── */
.msg-user {
    display: flex;
    justify-content: flex-end;
    margin: 0.8rem 0;
    animation: slideInRight 0.3s ease;
}

.msg-user-bubble {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 0.75rem 1.2rem;
    max-width: 75%;
    font-size: 0.9rem;
    line-height: 1.5;
    box-shadow: 0 4px 20px rgba(99,102,241,0.3);
}

.msg-agent {
    display: flex;
    justify-content: flex-start;
    margin: 0.8rem 0;
    animation: slideInLeft 0.3s ease;
}

.msg-agent-bubble {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    color: #e2e8f0;
    border-radius: 18px 18px 18px 4px;
    padding: 0.75rem 1.2rem;
    max-width: 80%;
    font-size: 0.9rem;
    line-height: 1.6;
}

.msg-agent-bubble strong { color: #a78bfa; }

.agent-avatar {
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 0.6rem;
    flex-shrink: 0;
    font-size: 0.9rem;
}

@keyframes slideInRight {
    from { opacity: 0; transform: translateX(20px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}

/* ─── Quick Query Pills ─── */
.quick-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

/* ─── Status Badges ─── */
.badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.badge-green { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.3); }
.badge-yellow { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }
.badge-red { background: rgba(248,113,113,0.15); color: #f87171; border: 1px solid rgba(248,113,113,0.3); }
.badge-blue { background: rgba(96,165,250,0.15); color: #60a5fa; border: 1px solid rgba(96,165,250,0.3); }

/* ─── Sidebar Config ─── */
.config-label {
    color: #64748b;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.4rem;
}

/* ─── Input ─── */
.stTextInput input, .stTextArea textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: rgba(99,102,241,0.6) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}

/* ─── Buttons ─── */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 25px rgba(99,102,241,0.4) !important;
}

/* ─── Divider ─── */
hr { border-color: rgba(255,255,255,0.06) !important; }

/* ─── Expander ─── */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 8px !important;
    color: #94a3b8 !important;
}

/* ─── Loading ─── */
.loading-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #6366f1;
    animation: pulse 1.2s ease-in-out infinite;
    margin: 0 2px;
}
.loading-dot:nth-child(2) { animation-delay: 0.2s; }
.loading-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes pulse {
    0%, 100% { opacity: 0.3; transform: scale(0.8); }
    50% { opacity: 1; transform: scale(1.1); }
}

/* ─── Tables ─── */
.dataframe {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 8px !important;
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
        
        # ─── Validate all required secrets are present ───────────────────────
        missing_secrets = []
        if not token:
            missing_secrets.append("MONDAY_API_TOKEN")
        if not groq_key:
            missing_secrets.append("GROQ_API_KEY")
        if not wo_id:
            missing_secrets.append("WO_BOARD_ID")
        if not deals_id:
            missing_secrets.append("DEALS_BOARD_ID")
        
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
                f"Connected to Monday.com! Loaded **{len(wo_df)} work orders** "
                f"and **{len(deals_df)} deals**.\n\n"
                "I'm your BI analyst. Ask me anything — pipeline health, sector performance, "
                "revenue breakdown, at-risk deals — or click **Generate Leadership Brief** "
                "for an instant board-ready update."
            )
        }]
    except Exception as e:
        st.session_state.connection_error = str(e)

if not st.session_state.data_loaded:
    _try_autoconnect()

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 1.5rem;">
        <div style="font-size: 2.5rem;">📊</div>
        <div style="color: #a78bfa; font-weight: 700; font-size: 1.1rem; margin-top: 0.3rem;">BizIntel Agent</div>
        <div style="color: #475569; font-size: 0.75rem;">Monday.com × Groq AI</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Data Stats
    if st.session_state.data_loaded:
        wo_df = st.session_state.wo_df
        deals_df = st.session_state.deals_df

        st.markdown('<div class="config-label">📈 Data Overview</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="color: #94a3b8; font-size: 0.8rem; line-height: 1.8;">
            📋 Work Orders: <strong style="color:#a78bfa">{len(wo_df)}</strong><br>
            💼 Deals: <strong style="color:#60a5fa">{len(deals_df)}</strong><br>
            🕐 Live from Monday.com<br>
            🔄 Cache: 5 min TTL
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Leadership Brief Button
        if st.button("📋 Generate Leadership Brief", use_container_width=True):
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
            st.session_state.agent = None
            st.session_state.wo_df = None
            st.session_state.deals_df = None
            st.rerun()

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

# ─── Main Area ────────────────────────────────────────────────────────────────

st.markdown("""
<div class="bi-header">
    <h1>📊 BizIntel — Monday.com AI Agent</h1>
    <p>Founder-level business intelligence powered by Groq AI · Real-time Monday.com data</p>
</div>
""", unsafe_allow_html=True)

# ─── Metrics Row ──────────────────────────────────────────────────────────────

if st.session_state.data_loaded:
    wo_df = st.session_state.wo_df
    deals_df = st.session_state.deals_df

    total_pipeline = deals_df["value"].sum() if not deals_df.empty else 0
    total_wo_value = wo_df["value"].sum() if not wo_df.empty else 0
    open_deals = len(deals_df[deals_df["status"].isin(["Open", "In Progress", "New", "Pending"])]) if not deals_df.empty else 0
    won_deals = len(deals_df[deals_df["status"] == "Won"]) if not deals_df.empty else 0
    win_rate = (won_deals / len(deals_df) * 100) if not deals_df.empty and len(deals_df) > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Total Pipeline", format_currency(total_pipeline) if total_pipeline > 0 else "N/A")
    with col2:
        st.metric("📋 Work Orders Value", format_currency(total_wo_value) if total_wo_value > 0 else "N/A")
    with col3:
        st.metric("🎯 Open Deals", f"{open_deals}")
    with col4:
        st.metric("✅ Win Rate", f"{win_rate:.1f}%" if win_rate > 0 else "N/A")

    st.divider()

# ─── Not Connected Banner ─────────────────────────────────────────────────────

if not st.session_state.data_loaded:
    if st.session_state.connection_error:
        st.markdown("""
        <div style="
            background: rgba(248,113,113,0.08);
            border: 1px solid rgba(248,113,113,0.3);
            border-radius: 12px;
            padding: 2rem;
            margin: 2rem 0;
        ">
            <div style="font-size: 1.5rem; margin-bottom: 1rem;">❌ Connection Failed</div>
            <div style="color: #f87171; font-size: 0.95rem; margin-bottom: 1rem; font-family: 'Courier New', monospace;">
                <strong>Error:</strong> """ + st.session_state.connection_error.replace("<", "&lt;").replace(">", "&gt;") + """
            </div>
            <div style="color: #cbd5e1; font-size: 0.85rem; line-height: 1.6;">
                <strong>What to check:</strong><br>
                ✓ Verify all API keys are set in .streamlit/secrets.toml (local) or deployment platform secrets<br>
                ✓ Required secrets: <code>MONDAY_API_TOKEN</code>, <code>GROQ_API_KEY</code>, <code>WO_BOARD_ID</code>, <code>DEALS_BOARD_ID</code><br>
                ✓ Check that Monday.com and Groq API keys are valid and not expired<br>
                ✓ Ensure board IDs are correct and accessible with your API token
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="
            background: rgba(99,102,241,0.08);
            border: 1px solid rgba(99,102,241,0.2);
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            margin: 2rem 0;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⏳</div>
            <div style="color: #a78bfa; font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">
                Connecting to Monday.com...
            </div>
            <div style="color: #64748b; font-size: 0.9rem;">
                Loading your boards automatically from configuration.
            </div>
        </div>
        """, unsafe_allow_html=True)

# ─── Chat Interface ───────────────────────────────────────────────────────────

if st.session_state.data_loaded:

    # Quick query suggestions
    st.markdown("**💡 Quick queries:**")
    quick_cols = st.columns(4)
    quick_queries = [
        "Pipeline overview",
        "Energy sector performance",
        "Win rate this quarter",
        "Top 5 open deals",
    ]
    quick_clicked = None
    for i, (col, query) in enumerate(zip(quick_cols, quick_queries)):
        with col:
            if st.button(query, key=f"quick_{i}", use_container_width=True):
                quick_clicked = query

    more_cols = st.columns(4)
    more_queries = [
        "Work orders by status",
        "Revenue by sector",
        "At-risk deals",
        "Leadership brief",
    ]
    for i, (col, query) in enumerate(zip(more_cols, more_queries)):
        with col:
            if st.button(query, key=f"more_{i}", use_container_width=True):
                quick_clicked = query

    st.divider()

    # Chat messages
    chat_html = '<div class="chat-container" id="chat-box">'
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            chat_html += f'''
            <div class="msg-user">
                <div class="msg-user-bubble">{msg["content"]}</div>
            </div>'''
        else:
            import html as html_lib
            content = msg["content"].replace("\n", "<br>")
            # Make **text** bold
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            # Make *text* italic
            content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
            chat_html += f'''
            <div class="msg-agent">
                <div class="agent-avatar">🤖</div>
                <div class="msg-agent-bubble">{content}</div>
            </div>'''

    if not st.session_state.messages:
        chat_html += '''
        <div style="text-align:center; padding: 3rem; color: #475569;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">💬</div>
            <div>Ask me anything about your business data...</div>
        </div>'''

    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)

    # Auto-scroll script
    st.markdown("""
    <script>
        const chatBox = document.getElementById('chat-box');
        if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
    </script>
    """, unsafe_allow_html=True)

    # Input
    with st.form(key="chat_form", clear_on_submit=True):
        cols = st.columns([6, 1])
        with cols[0]:
            user_input = st.text_input(
                "Ask your business question...",
                placeholder="How's our pipeline looking for energy sector this quarter?",
                label_visibility="collapsed",
                key="chat_input"
            )
        with cols[1]:
            submitted = st.form_submit_button("Send →", use_container_width=True)

    # Process input
    query_to_process = None
    if submitted and user_input:
        query_to_process = user_input
    elif quick_clicked:
        query_to_process = quick_clicked

    if query_to_process:
        st.session_state.messages.append({"role": "user", "content": query_to_process})

        with st.spinner("Analyzing your data..."):
            try:
                response = st.session_state.agent.chat(
                    query_to_process,
                    st.session_state.messages[:-1]
                )
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"⚠️ Error: {str(e)}"
                })
        st.rerun()

    # Data Preview Expanders
    with st.expander("🔍 Preview Work Orders Data"):
        if st.session_state.wo_df is not None and not st.session_state.wo_df.empty:
            display_cols = [c for c in st.session_state.wo_df.columns if c != "_raw"]
            st.dataframe(
                st.session_state.wo_df[display_cols].head(20),
                use_container_width=True
            )
        else:
            st.info("No work orders data loaded")

    with st.expander("🔍 Preview Deals Data"):
        if st.session_state.deals_df is not None and not st.session_state.deals_df.empty:
            display_cols = [c for c in st.session_state.deals_df.columns if c != "_raw"]
            st.dataframe(
                st.session_state.deals_df[display_cols].head(20),
                use_container_width=True
            )
        else:
            st.info("No deals data loaded")
