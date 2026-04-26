"""
Dashboard Tab — KPIs, traffic lights (Plotly SVG), density, vehicle stats, alerts.
All Plotly colours use #rrggbb or rgba() only — never hex+alpha strings.
"""

import plotly.graph_objects as go
import streamlit as st

from utils.constants import LANES, LANE_COLORS
from utils.traffic_logic import calc_green_time
from utils.charts import sparkline_fig, density_bar_fig, vehicle_type_pie

CARD_BG  = "#0d1117"
DARK_BG  = "#060912"
GRID_COL = "#1e2a40"


# ── Colour helper ─────────────────────────────────────────────────────────────
def _rgba(hex_color: str, alpha: float) -> str:
    """'#rrggbb' → 'rgba(r,g,b,alpha)'.  The ONLY way to do transparency in Plotly."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ── Traffic-light Plotly figure ───────────────────────────────────────────────
def _traffic_light_fig(lane: str, phase: str, time_left,
                        density: int, has_emergency: bool) -> go.Figure:
    """Draw one traffic-light card as a Plotly SVG figure — zero raw-HTML injection."""

    lane_color = LANE_COLORS[lane]
    is_red     = phase == "red"
    is_yellow  = phase == "yellow"
    is_green   = phase == "green"
    border_col = "#ff3e3e" if has_emergency else lane_color
    bar_color  = "#ff4444" if density > 70 else "#ffaa00" if density > 40 else "#44ff88"
    if time_left == "∞":
        tl_text = "∞"
    elif isinstance(time_left, int):
        tl_text = f"{time_left}s"
    else:
        tl_text = "-"

    # Bulb colours — lit vs unlit
    RED_ON    = "#ff3333";  RED_OFF    = "#2a1010"
    YELLOW_ON = "#ffcc00";  YELLOW_OFF = "#2a2000"
    GREEN_ON  = "#00ff88";  GREEN_OFF  = "#00250f"

    red_col    = RED_ON    if is_red    else RED_OFF
    yellow_col = YELLOW_ON if is_yellow else YELLOW_OFF
    green_col  = GREEN_ON  if is_green  else GREEN_OFF

    fig = go.Figure()

    # Housing
    fig.add_shape(type="rect",
                  x0=0.28, x1=0.72, y0=0.16, y1=0.90,
                  fillcolor="#111111",
                  line=dict(color="#333333", width=2))

    # Bulbs: (centre-y, colour, is_lit)
    bulbs = [
        (0.78, red_col,    is_red),
        (0.57, yellow_col, is_yellow),
        (0.36, green_col,  is_green),
    ]
    for cy, col, lit in bulbs:
        if lit:
            # Outer glow ring — rgba(), never col+"44"
            fig.add_shape(type="circle",
                          x0=0.40, x1=0.60, y0=cy - 0.10, y1=cy + 0.10,
                          fillcolor=_rgba(col, 0.25),
                          line=dict(color=col, width=2))
        # Bulb core
        fig.add_shape(type="circle",
                      x0=0.42, x1=0.58, y0=cy - 0.08, y1=cy + 0.08,
                      fillcolor=col,
                      line=dict(color="#000000", width=1))

    # Outer card border
    fig.add_shape(type="rect",
                  x0=0.0, x1=1.0, y0=0.0, y1=1.0,
                  fillcolor="rgba(0,0,0,0)",
                  line=dict(color=border_col, width=2))

    # Density bar track
    fig.add_shape(type="rect",
                  x0=0.05, x1=0.95, y0=0.03, y1=0.10,
                  fillcolor="#111111",
                  line=dict(color="#222222", width=1))
    # Density bar fill
    bar_end = 0.05 + (density / 100) * 0.90
    fig.add_shape(type="rect",
                  x0=0.05, x1=bar_end, y0=0.03, y1=0.10,
                  fillcolor=bar_color,
                  line=dict(width=0))

    # Annotations
    annotations = [
        dict(x=0.5, y=0.96,
             text=f"<b>{lane.upper()}</b>",
             font=dict(color=lane_color, size=13, family="sans-serif"),
             showarrow=False, xanchor="center", yanchor="middle"),
        dict(x=0.5, y=0.21,
             text=f"<b>{tl_text}</b>",
             font=dict(color="#ffffff", size=20, family="sans-serif"),
             showarrow=False, xanchor="center", yanchor="middle"),
        dict(x=0.5, y=0.005,
             text=f"Density: {density}%",
             font=dict(color="#888888", size=9, family="sans-serif"),
             showarrow=False, xanchor="center", yanchor="bottom"),
    ]
    if has_emergency:
        annotations.append(dict(
            x=0.5, y=1.08, text="🚨 EMERGENCY",
            font=dict(color="#ff4444", size=10, family="sans-serif"),
            showarrow=False, xanchor="center", yanchor="bottom",
            bgcolor="#330000", bordercolor="#ff4444", borderwidth=1, borderpad=3,
        ))

    fig.update_layout(
        annotations=annotations,
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        margin=dict(l=4, r=4, t=22, b=4),
        height=230,
        xaxis=dict(visible=False, range=[0, 1], fixedrange=True),
        yaxis=dict(visible=False, range=[0, 1.15], fixedrange=True),
        showlegend=False,
    )
    return fig


# ── Main render function ──────────────────────────────────────────────────────
def render_dashboard() -> None:
    ls  = st.session_state.lane_states
    cur = st.session_state.current_green
    ph  = st.session_state.phase
    tl  = st.session_state.time_left
    dh  = st.session_state.density_history

    # ── KPI cards ────────────────────────────────────────────────────────
    kpi_cols = st.columns(4)
    for i, lane in enumerate(LANES):
        s     = ls[lane]
        color = LANE_COLORS[lane]
        emerg = "<span style='color:#ff4444;font-size:10px;'> 🚨 Emergency</span>" if s["has_emergency"] else ""
        with kpi_cols[i]:
            st.markdown(
                f"<div style='background:{CARD_BG};border:1px solid {color}44;"
                f"border-radius:14px;padding:16px 18px;'>"
                f"<div style='color:#555;font-size:10px;letter-spacing:2px;'>{lane.upper()} LANE</div>"
                f"<div style='color:{color};font-size:30px;font-weight:900;margin:4px 0;'>{s['density']}%</div>"
                f"<div style='color:#aaa;font-size:11px;'>{s['vehicles']} vehicles{emerg}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if dh[lane]:
                st.plotly_chart(sparkline_fig(dh[lane], color),
                                use_container_width=True,
                                config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Traffic lights + density column ──────────────────────────────────
    col_lights, col_density = st.columns([3, 1])

    with col_lights:
        live_txt = "LIVE" if st.session_state.is_live else "PAUSED"
        st.markdown(
            f"<div style='color:#aaa;font-size:11px;letter-spacing:2px;"
            f"margin-bottom:6px;'>🚦 SIGNAL STATUS &nbsp;·&nbsp; {live_txt}</div>",
            unsafe_allow_html=True,
        )

        # Four lights side by side
        light_cols = st.columns(4)
        for i, lane in enumerate(LANES):
            lane_phase = ph if lane == cur else "red"
            lane_tl    = tl if lane == cur else "-"
            with light_cols[i]:
                st.plotly_chart(
                    _traffic_light_fig(lane, lane_phase, lane_tl,
                                       ls[lane]["density"],
                                       ls[lane]["has_emergency"]),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

        # Phase info row
        next_lane   = LANES[(LANES.index(cur) + 1) % len(LANES)]
        phase_color = "#00ff88" if ph == "green" else "#ffcc00" if ph == "yellow" else "#ff4444"
        info_cols   = st.columns(4)
        labels_vals = [
            ("Active Green", cur,        "#00ff88"),
            ("Phase",        ph.upper(), phase_color),
            ("Remaining",    f"{tl}s" if isinstance(tl, int) else str(tl), "#00d4ff"),
            ("Next Green",   next_lane,  "#aaaaaa"),
        ]
        for col_w, (label, value, vc) in zip(info_cols, labels_vals):
            with col_w:
                st.markdown(
                    f"<div style='background:{DARK_BG};border:1px solid #1e3a5f;"
                    f"border-radius:8px;padding:8px 10px;text-align:center;'>"
                    f"<div style='color:#555;font-size:10px;'>{label}</div>"
                    f"<div style='color:{vc};font-weight:800;font-size:16px;'>{value}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    with col_density:
        st.markdown(
            f"<div style='color:#aaa;font-size:11px;letter-spacing:2px;"
            f"margin-bottom:4px;'>📊 DENSITY COMPARISON</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(density_bar_fig(ls), use_container_width=True,
                        config={"displayModeBar": False})

        st.markdown(
            "<div style='color:#555;font-size:10px;letter-spacing:1px;"
            "margin:4px 0 6px 0;'>AI ALLOCATION</div>",
            unsafe_allow_html=True,
        )
        for lane in LANES:
            d   = ls[lane]["density"]
            em  = ls[lane]["has_emergency"]
            gt  = calc_green_time(d, em)
            col = LANE_COLORS[lane]
            lbl = "🚨 60s (Emergency)" if em else f"{gt}s green"
            lc  = "#ff4444" if em else "#aaa"
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"font-size:11px;margin-bottom:4px;'>"
                f"<span style='color:{col};'>{lane}</span>"
                f"<span style='color:{lc};'>{lbl}</span></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Vehicle breakdown ─────────────────────────────────────────────────
    st.markdown(
        "<div style='color:#aaa;font-size:11px;letter-spacing:2px;"
        "margin-bottom:6px;'>🚗 VEHICLE TYPE BREAKDOWN</div>",
        unsafe_allow_html=True,
    )
    veh_cols = st.columns(4)
    for i, lane in enumerate(LANES):
        s     = ls[lane]
        color = LANE_COLORS[lane]
        with veh_cols[i]:
            st.markdown(
                f"<div style='background:{CARD_BG};border:1px solid {color}33;"
                f"border-radius:12px;padding:8px 14px; text-align:center;'>"
                f"<div style='color:{color};font-weight:800;font-size:13px;'>{lane} Lane</div></div>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(vehicle_type_pie(ls, lane),
                            use_container_width=True,
                            config={"displayModeBar": False})

    # ── Alerts ────────────────────────────────────────────────────────────
    st.markdown(
        f"<div style='background:{CARD_BG};border:1px solid {GRID_COL};"
        f"border-radius:16px;padding:18px;margin-top:8px;'>"
        f"<div style='color:#aaa;font-size:11px;letter-spacing:2px;"
        f"margin-bottom:10px;'>🚨 RECENT ALERTS</div>",
        unsafe_allow_html=True,
    )
    alerts = st.session_state.alerts
    if not alerts:
        st.markdown(
            "<div style='color:#333;font-size:13px;text-align:center;"
            "padding:16px 0;'>No alerts — all systems normal ✅</div>",
            unsafe_allow_html=True,
        )
    else:
        for a in reversed(alerts[-8:]):
            st.markdown(
                f"<div style='background:#1a0000;border:1px solid #ff444433;"
                f"border-radius:8px;padding:8px 14px;margin:4px 0;"
                f"display:flex;justify-content:space-between;'>"
                f"<span style='color:#ff8888;font-size:12px;'>{a['msg']}</span>"
                f"<span style='color:#555;font-size:11px;white-space:nowrap;"
                f"margin-left:12px;'>{a['time']}</span></div>",
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)