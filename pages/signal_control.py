import streamlit as st
from utils.constants import LANES, LANE_COLORS
from utils.traffic_logic import calc_green_time, priority_score
from utils.charts import green_time_gauge


def _intersection_svg(lane_states, current_green, phase):
    phase_color = "#00ff88" if phase == "green" else "#ffcc00" if phase == "yellow" else "#ff4444"
    phase_icon  = "🟢" if phase == "green" else "🟡" if phase == "yellow" else "🔴"

    def lane_label(lane, x, y):
        active = lane == current_green and phase == "green"
        col    = LANE_COLORS[lane]
        d      = lane_states[lane]["density"]
        em     = lane_states[lane]["has_emergency"]
        glow   = f"filter:drop-shadow(0 0 8px {col});" if active else ""
        bg     = f"{col}33" if active else "#0d1117"
        border = col if active else "#2a3a50"
        tc     = col if active else "#556"
        return (f"<div style='position:absolute;left:{x}px;top:{y}px;"
                f"transform:translate(-50%,-50%);background:{bg};border:2px solid {border};"
                f"border-radius:8px;padding:5px 10px;text-align:center;min-width:60px;{glow}'>"
                f"<div style='color:{tc};font-size:10px;font-weight:800;'>{lane} {'🚨' if em else ''}</div>"
                f"<div style='color:#aaa;font-size:9px;'>{d}%</div></div>")

    return f"""<div style="position:relative;width:300px;height:300px;background:#060912;border-radius:12px;border:1px solid #1e2a40;margin:0 auto;">
<div style="position:absolute;left:40%;top:0;width:20%;height:100%;background:#1a1a1a;border-radius:3px;"></div>
<div style="position:absolute;top:40%;left:0;height:20%;width:100%;background:#1a1a1a;border-radius:3px;"></div>
<div style="position:absolute;left:40%;top:40%;width:20%;height:20%;background:#222;"></div>
<div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:44px;height:44px;border-radius:50%;background:{phase_color}22;border:3px solid {phase_color};display:flex;align-items:center;justify-content:center;font-size:16px;">{phase_icon}</div>
{lane_label("North", 150, 25)}
{lane_label("South", 150, 278)}
{lane_label("West",  25,  152)}
{lane_label("East",  278, 152)}
</div>"""


def render_signal_control():
    ls  = st.session_state.lane_states
    cur = st.session_state.current_green
    ph  = st.session_state.phase
    tl  = st.session_state.time_left

    st.markdown("""
    <div style="background:#0d1117;border:1px solid #1e2a40;border-radius:16px;padding:24px;margin-bottom:16px;">
        <div style="color:#aaa;font-size:11px;letter-spacing:2px;margin-bottom:16px;">🗺️ INTERSECTION OVERVIEW</div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(_intersection_svg(ls, cur, ph), unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='text-align:center;margin-bottom:8px;'><div style='color:#555;font-size:10px;letter-spacing:2px;'>REMAINING GREEN TIME</div><div style='color:#00ff88;font-size:11px;font-weight:700;margin-top:2px;'>{cur} Lane</div></div>",
            unsafe_allow_html=True)
        gc = "#ff4444" if ls[cur]["has_emergency"] else "#00ff88" if ph == "green" else "#ffcc00"
        st.plotly_chart(green_time_gauge(tl, 60, gc),
            use_container_width=True, config={"displayModeBar": False})
        pc = "#00ff88" if ph == "green" else "#ffcc00" if ph == "yellow" else "#ff4444"
        st.markdown(f"<div style='display:flex;justify-content:space-around;margin-top:4px;'><div style='text-align:center;'><div style='color:#555;font-size:10px;'>Phase</div><div style='color:{pc};font-weight:800;font-size:16px;'>{ph.upper()}</div></div><div style='text-align:center;'><div style='color:#555;font-size:10px;'>Cycle</div><div style='color:#00d4ff;font-weight:800;font-size:16px;'>#{st.session_state.cycle_count}</div></div></div>",
            unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='color:#aaa;font-size:11px;letter-spacing:2px;margin-bottom:10px;'>⏱️ SIGNAL TIMING PER LANE</div>",
        unsafe_allow_html=True)

    cols = st.columns(4)
    for i, lane in enumerate(LANES):
        s      = ls[lane]
        color  = LANE_COLORS[lane]
        gt     = calc_green_time(s["density"], s["has_emergency"])
        is_act = lane == cur
        prio   = priority_score(s["density"], s["has_emergency"])
        border = f"2px solid {color}" if is_act else f"1px solid {color}33"
        glow   = f"0 0 16px {color}44" if is_act else "none"
        bar_c  = "#ff4444" if s["has_emergency"] else color

        with cols[i]:
            active_badge = f"<span style='background:{color}33;color:{color};font-size:9px;padding:2px 8px;border-radius:99px;'>ACTIVE</span>" if is_act else ""
            
            html_content = f"""<div style="background:#0d1117;border:{border};border-radius:14px;padding:18px;box-shadow:{glow};margin-bottom:8px;">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
<span style="color:{color};font-weight:800;font-size:14px;">{lane}</span>
{active_badge}
</div>
"""
            
            for label, val, vc in [("Density",f"{s['density']}%",color),
                                   ("Vehicles",s["vehicles"],"#aaa"),
                                   ("Green Time",f"{gt}s","#00ff88"),
                                   ("Red Phase",f"{round(gt*0.6)}s","#ff4444"),
                                   ("Yellow Phase","5s","#ffcc00")]:
                html_content += f"<div style='display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px;'><span style='color:#555;'>{label}</span><span style='color:{vc};font-weight:700;'>{val}</span></div>\n"
            
            if s["has_emergency"]:
                html_content += "<div style='color:#ff4444;font-size:10px;font-weight:700;margin-top:6px;'>🚨 PRIORITY OVERRIDE ACTIVE</div>\n"
                
            html_content += f"""<div style='margin-top:10px;'>
<div style='color:#555;font-size:9px;margin-bottom:3px;'>PRIORITY SCORE</div>
<div style='background:#111;border-radius:6px;height:7px;overflow:hidden;'>
<div style='height:100%;border-radius:6px;width:{prio}%;background:{bar_c};'></div>
</div>
</div>
</div>"""
            
            st.markdown(html_content, unsafe_allow_html=True)

    st.markdown("<div style='margin:12px 0;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='margin:12px 0;'></div>", unsafe_allow_html=True)
    with st.expander("🧠 View Dynamic Timing Algorithm Rules"):
        st.markdown("""
        <div style="background:#0d1117;border:1px solid #1e2a40;border-radius:12px;padding:24px;">
        """, unsafe_allow_html=True)

    al, fo = st.columns(2)
    with al:
        st.markdown("<div style='color:#00d4ff;font-size:13px;font-weight:700;margin-bottom:10px;'>Priority Rules</div>", unsafe_allow_html=True)
        for n, rule, color in [
            ("1","Emergency vehicle → Immediate 60s green","#ff4444"),
            ("2","High density (>70%) → 45–60s green","#ff8844"),
            ("3","Medium density (40–70%) → 25–45s green","#ffcc00"),
            ("4","Low density (<40%) → 10–25s green","#44ff88"),
            ("5","Minimum green: 10s guaranteed per lane","#00d4ff")]:
            st.markdown(f"<div style='display:flex;gap:10px;margin-bottom:7px;align-items:flex-start;'><div style='width:20px;height:20px;border-radius:50%;background:{color}33;border:1px solid {color};color:{color};font-size:10px;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0;'>{n}</div><div style='color:#aaa;font-size:11px;'>{rule}</div></div>",
                unsafe_allow_html=True)
    with fo:
        st.markdown("<div style='color:#a8ff3e;font-size:13px;font-weight:700;margin-bottom:10px;'>Formula (Python)</div>", unsafe_allow_html=True)
        st.code("""def calc_green_time(density, has_emergency):
    if has_emergency:
        return 60       # Emergency override
    return round(
        10 + (density / 100) * 50
    )
    # Range: 10s – 60s""", language="python")
        d  = ls[cur]["density"]
        em = ls[cur]["has_emergency"]
        gt = calc_green_time(d, em)
        st.markdown(f"<div style='color:#555;font-size:11px;margin-top:8px;'>Current: <span style='color:#00ff88;font-weight:700;'>{cur}</span> lane at <span style='color:#00d4ff;'>{d}%</span> density → <span style='color:#a8ff3e;'>{gt}s</span> green</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)