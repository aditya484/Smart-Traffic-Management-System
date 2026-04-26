import streamlit as st
from utils.constants import LANES, LANE_COLORS, LANE_BG, DL_MODEL_INFO


def _camera_view_html(lane, state, is_live):
    color     = LANE_COLORS[lane]
    bg        = LANE_BG[lane]
    density   = state["density"]
    vehicles  = state["vehicles"]
    has_emerg = state["has_emergency"]
    feed_label = "🔴 LIVE" if is_live else "📹 VIDEO"
    bar_color  = "#ff4444" if density > 70 else "#ffaa00" if density > 40 else "#44ff88"

    vehicle_dots = ""
    vc_colors = ["#4488ff", "#ff8844", "#88ff44", "#ff44ff"]
    for i in range(min(12, round(vehicles / 10))):
        vc  = "#ff4444" if (i == 0 and has_emerg) else vc_colors[i % 4]
        l   = 10 + (i % 4) * 22
        t   = 10 + (i // 4) * 25
        em  = "🚑" if (i == 0 and has_emerg) else ""
        vehicle_dots += (f"<div style='position:absolute;left:{l}%;top:{t}%;width:18px;height:26px;"
                         f"background:{vc};border-radius:3px;opacity:0.85;display:flex;"
                         f"align-items:center;justify-content:center;font-size:10px;'>{em}</div>")

    emerg_badge = (
        "<div style='position:absolute;top:6px;right:6px;background:#ff0000cc;"
        "padding:2px 8px;border-radius:6px;color:#fff;font-size:9px;font-weight:800;'>"
        "🚨 EMERGENCY</div>" if has_emerg else ""
    )

    return f"""<div style="background:#0a0d12;border:1px solid {color}33;border-radius:12px;overflow:hidden;">
<div style="height:145px;background:linear-gradient(135deg,{bg},#0a0d12);position:relative;overflow:hidden;">
<div style="position:absolute;width:100%;height:100%;background:repeating-linear-gradient(0deg,#1a1a1a 0px,#1a1a1a 40px,#222 40px,#222 80px);opacity:0.35;"></div>
<div style="position:absolute;width:2px;height:100%;background:#fff3;left:50%;"></div>
{vehicle_dots}
<div style="position:absolute;top:6px;left:6px;background:#000a;padding:2px 8px;border-radius:6px;color:{color};font-size:10px;font-weight:700;">{feed_label} · {lane}</div>
<div style="position:absolute;bottom:6px;right:6px;background:#000a;padding:2px 8px;border-radius:6px;color:#fff;font-size:9px;">{vehicles} vehicles detected</div>
{emerg_badge}
</div>
<div style="padding:8px 12px;border-top:1px solid {color}22;">
<div style="display:flex;justify-content:space-between;margin-bottom:4px;">
<span style="color:{color};font-size:12px;font-weight:700;">{lane}</span>
<span style="color:#555;font-size:10px;">Density: {density}%</span>
</div>
<div style="background:#111;border-radius:4px;height:5px;overflow:hidden;">
<div style="height:100%;border-radius:4px;width:{density}%;background:{bar_color};"></div>
</div>
</div>
</div>"""


def render_video_feeds():
    ls      = st.session_state.lane_states
    is_live = st.session_state.get("feed_mode", "Live Camera") == "Live Camera"

    st.markdown("""
    <div style="text-align:center;margin-bottom:20px;">
        <h3 style="color:#fff;margin-bottom:4px;font-weight:600;">Live Intersection Monitoring</h3>
        <p style="color:#aaa;font-size:13px;margin-top:0;">Real-time AI vehicle detection and phase monitoring across all lanes.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("⚙️ Manage Video Sources (Upload Custom Videos)", expanded=False):
        upload_cols = st.columns(4)
        for i, lane in enumerate(LANES):
            with upload_cols[i]:
                st.markdown(f"<div style='color:{LANE_COLORS[lane]};font-size:12px;font-weight:600;'>{lane} Lane Feed</div>", unsafe_allow_html=True)
                uploaded = st.file_uploader("", type=["mp4","avi","mov"], key=f"upload_{lane}", label_visibility="collapsed")
                if uploaded:
                    st.success("Uploaded")

    st.markdown("<div style='margin:8px 0;'></div>", unsafe_allow_html=True)

    cur = st.session_state.current_green
    ph  = st.session_state.phase

    row1 = st.columns(2)
    row2 = st.columns(2)
    
    for i, lane in enumerate(LANES):
        col = row1[i] if i < 2 else row2[i - 2]
        with col:
            uploaded = st.session_state.get(f"upload_{lane}")
            lane_phase = ph if lane == cur else "red"
            sig_col    = "#00ff88" if lane_phase == "green" else "#ffcc00" if lane_phase == "yellow" else "#ff4444"
            sig_icon   = "🟢" if lane_phase == "green" else "🟡" if lane_phase == "yellow" else "🔴"
            color      = LANE_COLORS[lane]
            
            st.markdown(f"<div style='background:#0a0d12; border: 1px solid {color}33; border-radius:12px; padding: 12px; margin-bottom: 16px;'>"
                        f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom: 10px;'>"
                        f"<span style='color:{color}; font-weight:700; font-size:14px;'>{lane} Feed</span>"
                        f"<span style='color:{sig_col}; font-weight:800; font-size:11px; background:{sig_col}11; border: 1px solid {sig_col}44; padding: 4px 10px; border-radius: 6px;'>{sig_icon} SIGNAL: {lane_phase.upper()}</span>"
                        f"</div>", unsafe_allow_html=True)
            
            if uploaded:
                st.video(uploaded)
                density = ls[lane]["density"]
                vehicles = ls[lane]["vehicles"]
                bar_color = "#ff4444" if density > 70 else "#ffaa00" if density > 40 else "#44ff88"
                st.markdown(f"""
                <div style="padding-top:10px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                        <span style="color:#aaa;font-size:10px;">YOLOv8 Detection Active</span>
                        <span style="color:#555;font-size:10px;">Density: {density}% | Vehicles: {vehicles}</span>
                    </div>
                    <div style="background:#111;border-radius:4px;height:5px;overflow:hidden;">
                        <div style="height:100%;border-radius:4px;width:{density}%;background:{bar_color};"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(_camera_view_html(lane, ls[lane], True),
                    unsafe_allow_html=True)
                
            st.markdown("</div>", unsafe_allow_html=True)
