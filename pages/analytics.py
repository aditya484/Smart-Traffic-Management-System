import pandas as pd
import streamlit as st
from utils.constants import LANES, LANE_COLORS, HOURS, PEAK_HOURS
from utils.charts import trend_line_fig, hourly_bar_fig, heatmap_fig


def _build_dataframe(day_data, lanes):
    rows = []
    for h in HOURS:
        row = {"Hour": f"{h:02d}:00", "Peak": "🔥" if h in PEAK_HOURS else ""}
        for lane in lanes:
            d = day_data[lane][h]
            row[f"{lane} Density%"]  = d["density"]
            row[f"{lane} Vehicles"]  = d["vehicles"]
            row[f"{lane} Green(s)"]  = d["green_time"]
            row[f"{lane} Emergency"] = "🚨" if d["emergency"] else "–"
        rows.append(row)
    return pd.DataFrame(rows)


def render_analytics():
    dd = st.session_state.day_data
    ls = st.session_state.lane_states

    st.markdown("""
    <div style="background:#0d1117;border:1px solid #1e2a40;border-radius:14px;
         padding:14px 20px;margin-bottom:16px;">
        <div style="color:#555;font-size:11px;letter-spacing:2px;margin-bottom:8px;">🎛️ FILTERS</div>
    """, unsafe_allow_html=True)

    c1, c2, _ = st.columns([2, 2, 3])
    with c1:
        selected_lane = st.selectbox("Lane", ["All"] + LANES, key="an_lane")
    with c2:
        metric = st.selectbox("Metric", ["density","vehicles","green_time"],
            format_func=lambda x: {"density":"Density %","vehicles":"Vehicle Count",
                                   "green_time":"Green Time (s)"}[x], key="an_metric")
    st.markdown("</div>", unsafe_allow_html=True)

    display_lanes = LANES if selected_lane == "All" else [selected_lane]
    busiest = max(LANES, key=lambda l: ls[l]["density"])
    avg_d   = round(sum(ls[l]["density"] for l in LANES) / 4)

    kpi_cols = st.columns(4)
    for i, (label, value, color) in enumerate([
        ("Peak Hours",         "08:00-10:00 & 17:00-19:00", "#ff6b35"),
        ("Busiest Lane",       busiest,                       "#00d4ff"),
        ("Avg Density (live)", f"{avg_d}%",                  "#a8ff3e"),
        ("Vehicles Tracked",   f"{st.session_state.total_vehicles:,}", "#ff3eee"),
    ]):
        with kpi_cols[i]:
            st.markdown(f"<div style='background:#0d1117;border:1px solid #1e2a40;border-radius:12px;padding:14px 18px;text-align:center;margin-bottom:12px;'><div style='color:#555;font-size:10px;letter-spacing:1px;'>{label}</div><div style='color:{color};font-size:15px;font-weight:800;margin-top:4px;'>{value}</div></div>",
                unsafe_allow_html=True)

    st.markdown(f"<div style='background:#0d1117;border:1px solid #1e2a40;border-radius:16px;padding:20px;margin-bottom:16px;'><div style='color:#aaa;font-size:11px;letter-spacing:2px;margin-bottom:8px;'>📈 24-HOUR TREND · {selected_lane} LANES</div>",
        unsafe_allow_html=True)
    st.plotly_chart(trend_line_fig(dd, selected_lane, metric),
        use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='color:#aaa;font-size:11px;letter-spacing:2px;margin-bottom:10px;'>📊 HOURLY DENSITY BARS (8AM-7PM)</div>",
        unsafe_allow_html=True)
    bar_cols = st.columns(len(display_lanes))
    for i, lane in enumerate(display_lanes):
        with bar_cols[i]:
            st.plotly_chart(hourly_bar_fig(dd, lane),
                use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='background:#0d1117;border:1px solid #1e2a40;border-radius:16px;padding:20px;margin-bottom:16px;'><div style='color:#aaa;font-size:11px;letter-spacing:2px;margin-bottom:8px;'>🔥 TRAFFIC DENSITY HEATMAP</div>",
        unsafe_allow_html=True)
    st.plotly_chart(heatmap_fig(dd, selected_lane),
        use_container_width=True, config={"displayModeBar": False})
    st.markdown("<div style='display:flex;gap:16px;margin-top:4px;align-items:center;'><span style='color:#555;font-size:10px;'>Scale:</span><span style='color:#44ff88;font-size:10px;'>■ Low &lt;40%</span><span style='color:#ffaa00;font-size:10px;'>■ Medium 40-70%</span><span style='color:#ff4444;font-size:10px;'>■ High &gt;70%</span></div></div>",
        unsafe_allow_html=True)

    st.markdown(f"<div style='background:#0d1117;border:1px solid #1e2a40;border-radius:16px;padding:20px;margin-bottom:16px;'><div style='color:#aaa;font-size:11px;letter-spacing:2px;margin-bottom:12px;'>📋 DETAILED HOURLY REPORT — {selected_lane} LANES</div>",
        unsafe_allow_html=True)
    df = _build_dataframe(dd, display_lanes)
    st.dataframe(df, use_container_width=True, height=420)
    st.download_button("⬇️ Download CSV Report", df.to_csv(index=False),
        "traffic_analytics_report.csv", "text/csv")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='background:#0d1117;border:1px solid #1e2a40;border-radius:16px;padding:20px;'><div style='color:#aaa;font-size:11px;letter-spacing:2px;margin-bottom:12px;'>🔥 PEAK HOUR SUMMARY</div>",
        unsafe_allow_html=True)
    ph_cols = st.columns(len(display_lanes))
    for i, lane in enumerate(display_lanes):
        color     = LANE_COLORS[lane]
        peak_data = [(h, dd[lane][h]) for h in PEAK_HOURS]
        avg_pd    = round(sum(d["density"]  for _, d in peak_data) / len(peak_data))
        avg_pv    = round(sum(d["vehicles"] for _, d in peak_data) / len(peak_data))
        max_d     = max(peak_data, key=lambda x: x[1]["density"])
        with ph_cols[i]:
            st.markdown(f"<div style='background:#060912;border:1px solid {color}33;border-radius:10px;padding:12px 14px;'><div style='color:{color};font-size:12px;font-weight:700;margin-bottom:8px;'>{lane}</div><div style='display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px;'><span style='color:#555;'>Avg Peak Density</span><span style='color:{color};font-weight:700;'>{avg_pd}%</span></div><div style='display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px;'><span style='color:#555;'>Avg Peak Vehicles</span><span style='color:#aaa;font-weight:700;'>{avg_pv}</span></div><div style='display:flex;justify-content:space-between;font-size:11px;'><span style='color:#555;'>Busiest Hour</span><span style='color:#ffbb00;font-weight:700;'>{max_d[0]:02d}:00 🔥</span></div></div>",
                unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
