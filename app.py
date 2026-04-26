"""
Smart Traffic Management System
================================
Deep Learning powered dynamic traffic signal control with real-time
vehicle density analysis, emergency vehicle priority, and analytics.

Run: streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Smart Traffic Management System",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #060912; }
    .stApp { background-color: #060912; }
    section[data-testid="stSidebar"] {
        background-color: #0a0d12;
        border-right: 1px solid #1e2a40;
    }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    html, body, [class*="css"] {
        color: #e0e0e0;
        font-family: 'Inter', system-ui, sans-serif;
    }
    /* Metrics */
    [data-testid="metric-container"] {
        background: #0d1117;
        border: 1px solid #1e2a40;
        border-radius: 12px;
        padding: 14px !important;
    }
    [data-testid="metric-container"] label {
        color: #666 !important; font-size: 11px !important; letter-spacing: 2px;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #00d4ff !important; font-size: 28px !important; font-weight: 900 !important;
    }
    /* Buttons */
    .stButton > button {
        background: rgba(0, 212, 255, 0.1) !important;
        border: 1px solid rgba(0, 212, 255, 0.3) !important;
        color: #00d4ff !important;
        border-radius: 8px !important;
        font-family: 'Inter', system-ui, sans-serif !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: #00d4ff !important;
        color: #060912 !important;
        border-color: #00d4ff !important;
    }
    /* Selectbox */
    .stSelectbox > div > div {
        background: #0d1117 !important;
        border-color: #1e2a40 !important;
        color: #e0e0e0 !important;
    }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #080b10;
        border-bottom: 1px solid #1e2a40;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #556 !important;
        border: 1px solid transparent !important;
        border-radius: 8px !important;
        padding: 6px 16px !important;
        font-family: 'Inter', system-ui, sans-serif !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    .stTabs [aria-selected="true"] {
        background: #0d1525 !important;
        color: #00d4ff !important;
        border-color: #1e3a5f !important;
        font-weight: 700 !important;
    }
    /* Dataframe */
    .stDataFrame { background: #0d1117 !important; }
    /* Expander */
    .streamlit-expanderHeader {
        background: #0d1117 !important;
        color: #aaa !important;
        border: 1px solid #1e2a40 !important;
        border-radius: 8px !important;
    }
    .streamlit-expanderContent {
        background: #080b10 !important;
        border: 1px solid #1e2a40 !important;
    }
    hr { border-color: #1e2a40 !important; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0a0d12; }
    ::-webkit-scrollbar-thumb { background: #1e2a40; border-radius: 3px; }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }
    .alert-box {
        background: #1a0000; border: 1px solid #ff444444;
        border-radius: 8px; padding: 8px 14px; margin: 4px 0;
        font-size: 12px; color: #ff8888;
    }
</style>
""", unsafe_allow_html=True)

# ── Init & tick ───────────────────────────────────────────────────────────────
from utils.state import init_session_state, tick_simulation
from utils.constants import LANES, LANE_COLORS

init_session_state()

if st.session_state.is_live:
    tick_simulation()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:10px 0 20px 0;'>
        <div style='font-size:36px;'>🚦</div>
        <div style='color:#00d4ff;font-weight:900;font-size:13px;letter-spacing:2px;'>SMART TRAFFIC</div>
        <div style='color:#223;font-size:9px;letter-spacing:3px;'>MANAGEMENT SYSTEM</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("<div style='color:#555;font-size:11px;letter-spacing:2px;margin-bottom:8px;'>⚙️ SIMULATION CONTROL</div>",
                unsafe_allow_html=True)
    
    st.session_state.control_mode = st.radio("Mode", ["Dynamic (AI)", "Manual"], horizontal=True, label_visibility="collapsed")
    if st.session_state.control_mode == "Manual":
        st.markdown("<div style='color:#555;font-size:10px;letter-spacing:1px;margin:8px 0 4px 0;'>🚦 MANUAL OVERRIDE</div>", unsafe_allow_html=True)
        idx = LANES.index(st.session_state.current_green) if st.session_state.current_green in LANES else 0
        selected_lane = st.radio("Select Lane", LANES, horizontal=True, label_visibility="collapsed", key="manual_lane_radio", index=idx)
        if selected_lane != st.session_state.current_green:
            st.session_state.current_green = selected_lane
            st.session_state.phase = "green"
            st.session_state.time_left = "∞"
            st.session_state.cycle_count += 1
            st.rerun()
        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        btn_label = "▶ Resume" if not st.session_state.is_live else "⏸ Pause"
        if st.button(btn_label, use_container_width=True):
            st.session_state.is_live = not st.session_state.is_live
            st.rerun()
    with c2:
        if st.button("🔄 Reset", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    st.markdown("---")
    st.markdown("<div style='color:#555;font-size:11px;letter-spacing:2px;margin-bottom:8px;'>📡 SYSTEM STATUS</div>",
                unsafe_allow_html=True)

    sc = "#00ff88" if st.session_state.is_live else "#ff4444"
    st_text = "ONLINE" if st.session_state.is_live else "PAUSED"
    tl_str = f"{st.session_state.time_left}s" if isinstance(st.session_state.time_left, int) else str(st.session_state.time_left)
    st.markdown(f"""
    <div style='display:flex;flex-direction:column;gap:7px;'>
        <div style='display:flex;justify-content:space-between;'>
            <span style='color:#555;font-size:11px;'>Status</span>
            <span style='color:{sc};font-size:11px;font-weight:700;'>● {st_text}</span>
        </div>
        <div style='display:flex;justify-content:space-between;'>
            <span style='color:#555;font-size:11px;'>Signal Cycles</span>
            <span style='color:#00d4ff;font-size:11px;font-weight:700;'>{st.session_state.cycle_count}</span>
        </div>
        <div style='display:flex;justify-content:space-between;'>
            <span style='color:#555;font-size:11px;'>Vehicles Logged</span>
            <span style='color:#a8ff3e;font-size:11px;font-weight:700;'>{st.session_state.total_vehicles:,}</span>
        </div>
        <div style='display:flex;justify-content:space-between;'>
            <span style='color:#555;font-size:11px;'>Active Green</span>
            <span style='color:#00ff88;font-size:11px;font-weight:700;'>{st.session_state.current_green}</span>
        </div>
        <div style='display:flex;justify-content:space-between;'>
            <span style='color:#555;font-size:11px;'>Time Left</span>
            <span style='color:#ffcc00;font-size:11px;font-weight:700;'>{tl_str}</span>
        </div>
        <div style='display:flex;justify-content:space-between;'>
            <span style='color:#555;font-size:11px;'>Phase</span>
            <span style='color:#aaa;font-size:11px;font-weight:700;'>{st.session_state.phase.upper()}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div style='color:#555;font-size:11px;letter-spacing:2px;margin-bottom:8px;'>📊 LIVE DENSITIES</div>",
                unsafe_allow_html=True)

    for lane in LANES:
        d     = st.session_state.lane_states[lane]["density"]
        color = LANE_COLORS[lane]
        bc    = "#ff4444" if d > 70 else "#ffaa00" if d > 40 else "#44ff88"
        em    = st.session_state.lane_states[lane]["has_emergency"]
        st.markdown(f"""
        <div style='margin-bottom:9px;'>
            <div style='display:flex;justify-content:space-between;margin-bottom:3px;'>
                <span style='color:{color};font-size:11px;font-weight:700;'>{lane} {"🚨" if em else ""}</span>
                <span style='color:#aaa;font-size:11px;'>{d}%</span>
            </div>
            <div style='background:#111;border-radius:99px;height:6px;overflow:hidden;'>
                <div style='height:100%;width:{d}%;background:{bc};border-radius:99px;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div style='color:#222;font-size:9px;text-align:center;letter-spacing:1px;'>YOLOv8 · Deep Learning · Streamlit · v2.0</div>",
                unsafe_allow_html=True)

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(90deg,#060912,#0d1525,#060912);
     border-bottom:1px solid #1e2a40;padding:16px 0 12px 0;margin-bottom:20px;'>
    <div style='display:flex;align-items:center;gap:14px;'>
        <div style='font-size:28px;'>🚦</div>
        <div>
            <div style='font-size:17px;font-weight:900;color:#00d4ff;letter-spacing:3px;'>
                SMART TRAFFIC MANAGEMENT SYSTEM
            </div>
            <div style='font-size:9px;color:#334;letter-spacing:4px;'>
                DEEP LEARNING · DYNAMIC SIGNALS · REAL-TIME ANALYTICS · YOLOV8
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Emergency alert banner ────────────────────────────────────────────────────
alerts = st.session_state.alerts
if alerts:
    a = alerts[-1]
    st.markdown(f"""
    <div style='background:#1a0000;border:1px solid #ff444466;border-radius:8px;
         padding:8px 16px;margin-bottom:16px;display:flex;align-items:center;gap:12px;'>
        <span style='color:#ff4444;font-size:13px;font-weight:800;'>🚨 ALERT</span>
        <span style='color:#ff8888;font-size:12px;'>{a["msg"]}</span>
        <span style='color:#555;font-size:11px;margin-left:auto;'>{a["time"]}</span>
    </div>
    """, unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_dash, tab_feeds, tab_signals, tab_analytics = st.tabs([
    "🖥️  Dashboard",
    "📷  Video Feeds",
    "🚦  Signal Control",
    "📊  Analytics",
])

from pages.dashboard     import render_dashboard
from pages.video_feeds   import render_video_feeds
from pages.signal_control import render_signal_control
from pages.analytics     import render_analytics

with tab_dash:
    render_dashboard()

with tab_feeds:
    render_video_feeds()

with tab_signals:
    render_signal_control()

with tab_analytics:
    render_analytics()

# ── Auto-refresh ──────────────────────────────────────────────────────────────
if st.session_state.is_live:
    import time
    time.sleep(2)
    st.rerun()