"""
Plotly figure builders for the Smart Traffic analytics and dashboard views.
All colours use proper #rrggbb or rgba() -- no hex+alpha strings.
_layout() merges per-chart overrides so there are NEVER duplicate keyword args.
"""

import plotly.graph_objects as go
import pandas as pd

from utils.constants import LANES, LANE_COLORS, HOURS, PEAK_HOURS


DARK_BG  = "#060912"
CARD_BG  = "#0d1117"
GRID_COL = "#1e2a40"
TEXT_COL = "#aaaaaa"


def _hex_rgba(hex_color: str, alpha: float) -> str:
    """Convert '#rrggbb' to 'rgba(r,g,b,alpha)' — the only format Plotly accepts for transparency."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _layout(**overrides) -> dict:
    """
    Return a layout dict that starts from the dark base theme and deep-merges
    any per-chart overrides.  Using this instead of **_LAYOUT_BASE + extra kwargs
    avoids 'multiple values for keyword argument' errors.
    """
    base = dict(
        paper_bgcolor=CARD_BG,
        plot_bgcolor=DARK_BG,
        font=dict(family="system-ui, sans-serif", color=TEXT_COL, size=11),
        margin=dict(l=50, r=20, t=30, b=40),
        xaxis=dict(gridcolor=GRID_COL, zerolinecolor=GRID_COL),
        yaxis=dict(gridcolor=GRID_COL, zerolinecolor=GRID_COL),
    )
    # Deep-merge: if both base and override have the same dict key, merge them
    for k, v in overrides.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            base[k] = {**base[k], **v}
        else:
            base[k] = v
    return base


# ─────────────────────────────────────────────────────────────────────────────
def sparkline_fig(values: list, color: str, height: int = 60) -> go.Figure:
    """Mini sparkline for dashboard KPI cards."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=values, mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=_hex_rgba(color, 0.15),
    ))
    fig.update_layout(**_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False, showgrid=False),
        yaxis=dict(visible=False, showgrid=False),
        showlegend=False,
    ))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
def density_bar_fig(lane_states: dict) -> go.Figure:
    """Horizontal bar chart comparing current density across all lanes."""
    fig = go.Figure()
    for lane in LANES:
        density = lane_states[lane]["density"]
        color = "#ff4444" if density > 70 else "#ffaa00" if density > 40 else "#44ff88"
        fig.add_trace(go.Bar(
            y=[lane], x=[density],
            orientation="h",
            marker=dict(color=color, line=dict(width=0)),
            name=lane,
            text=[f"{density}%"],
            textposition="inside",
            insidetextanchor="middle",
        ))
    fig.update_layout(**_layout(
        height=180,
        showlegend=False,
        barmode="group",
        xaxis=dict(range=[0, 100], gridcolor=GRID_COL, title="Density %"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        bargap=0.25,
    ))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
def trend_line_fig(day_data: dict, selected_lane: str, metric: str) -> go.Figure:
    """24-hour trend line chart for analytics tab."""
    lanes = LANES if selected_lane == "All" else [selected_lane]
    fig = go.Figure()

    titles = {"density": "Density %", "vehicles": "Vehicle Count", "green_time": "Green Time (s)"}
    ytitle = titles.get(metric, metric)

    for lane in lanes:
        data = day_data[lane]
        x = [d["hour"] for d in data]
        y = [d[metric] for d in data]
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode="lines+markers",
            name=lane,
            line=dict(color=LANE_COLORS[lane], width=2.5),
            marker=dict(size=4, color=LANE_COLORS[lane]),
        ))

    for h in [8, 17]:
        fig.add_vrect(
            x0=h, x1=h + 2,
            fillcolor="rgba(255,170,0,0.08)",
            layer="below", line_width=0,
            annotation_text="Peak" if h == 8 else "",
            annotation_position="top left",
            annotation_font=dict(color="#ffaa00", size=9),
        )

    fig.update_layout(**_layout(
        height=280,
        xaxis=dict(
            gridcolor=GRID_COL, title="Hour of Day",
            tickvals=list(range(0, 24, 3)),
            ticktext=[f"{h:02d}:00" for h in range(0, 24, 3)],
        ),
        yaxis=dict(gridcolor=GRID_COL, title=ytitle),
        legend=dict(
            bgcolor="#0d1117", bordercolor=GRID_COL,
            borderwidth=1, font=dict(color=TEXT_COL, size=10),
        ),
        hovermode="x unified",
    ))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
def hourly_bar_fig(day_data: dict, lane: str) -> go.Figure:
    """Bar chart of hourly density for a single lane (8 AM – 7 PM window)."""
    hours = list(range(8, 20))
    data = day_data[lane]
    densities = [data[h]["density"] for h in hours]
    colors = ["#ff4444" if d > 70 else "#ffaa00" if d > 40 else "#44ff88" for d in densities]
    peak_mark = ["🔥" if h in PEAK_HOURS else "" for h in hours]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"{h}:00 {peak_mark[i]}" for i, h in enumerate(hours)],
        y=densities,
        marker=dict(color=colors),
        text=[f"{d}%" for d in densities],
        textposition="outside",
        textfont=dict(size=9, color=TEXT_COL),
    ))
    fig.update_layout(**_layout(
        height=220,
        showlegend=False,
        title=dict(
            text=f"{lane} Lane - Hourly Density",
            font=dict(color=LANE_COLORS[lane], size=12),
        ),
        xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=9)),
        yaxis=dict(gridcolor=GRID_COL, range=[0, 110]),
        bargap=0.15,
    ))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
def heatmap_fig(day_data: dict, selected_lane: str) -> go.Figure:
    """2-D traffic density heatmap: lanes x hours."""
    lanes = LANES if selected_lane == "All" else [selected_lane]
    z, text = [], []
    for lane in lanes:
        row = [day_data[lane][h]["density"] for h in HOURS]
        z.append(row)
        text.append([f"{v}%" for v in row])

    fig = go.Figure(go.Heatmap(
        z=z,
        x=[f"{h:02d}:00" for h in HOURS],
        y=lanes,
        text=text,
        texttemplate="%{text}",
        textfont=dict(size=9),
        colorscale=[
            [0.0,  "#44ff88"],
            [0.4,  "#aaff44"],
            [0.6,  "#ffaa00"],
            [0.85, "#ff6644"],
            [1.0,  "#ff2222"],
        ],
        zmin=0, zmax=100,
        colorbar=dict(
            title=dict(text="Density %", font=dict(color=TEXT_COL)),
            tickfont=dict(color=TEXT_COL),
            bgcolor=CARD_BG,
            bordercolor=GRID_COL,
        ),
        hoverongaps=False,
    ))
    fig.update_layout(**_layout(
        height=max(160, 80 * len(lanes)),
        xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=9)),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
    ))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
def vehicle_type_pie(lane_states: dict, lane: str) -> go.Figure:
    """Donut chart showing vehicle-type breakdown for one lane."""
    types = lane_states[lane]["types"]
    labels = [t.capitalize() for t, v in types.items() if v > 0]
    values = [v for v in types.values() if v > 0]
    colors_map = {
        "Car": "#4488ff", "Truck": "#ff8844", "Bus": "#88ff44",
        "Motorcycle": "#ff44ff", "Emergency": "#ff4444",
    }
    colors = [colors_map.get(lb, "#aaaaaa") for lb in labels]

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color=DARK_BG, width=2)),
        textfont=dict(size=10, color="#ffffff"),
    ))
    fig.update_layout(**_layout(
        height=180,
        showlegend=True,
        legend=dict(font=dict(size=9, color=TEXT_COL), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=10, r=10, t=10, b=10),
    ))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
def green_time_gauge(current: int | str, maximum: int = 60, color: str = "#00ff88") -> go.Figure:
    """Semi-circular gauge for remaining green time."""
    # Force Streamlit reload with a slight refactor
    is_inf = (current == "∞")
    val = maximum if is_inf else int(current) if isinstance(current, (int, float, str)) and str(current).isdigit() else maximum
    suf = "" if is_inf else "s"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        number=dict(suffix=suf, valueformat="", font=dict(color=color, size=28, family="system-ui, sans-serif")),
        gauge=dict(
            axis=dict(
                range=[0, maximum],
                tickcolor=TEXT_COL,
                tickfont=dict(color=TEXT_COL, size=8),
            ),
            bar=dict(color=color),
            bgcolor=DARK_BG,
            bordercolor=GRID_COL,
            steps=[
                dict(range=[0,              maximum * 0.33], color="#1a2030"),
                dict(range=[maximum * 0.33, maximum * 0.66], color="#162030"),
                dict(range=[maximum * 0.66, maximum],        color="#102030"),
            ],
        ),
    ))
    
    # If it is infinity, plot a text annotation to override the number
    if current == "∞":
        fig.add_annotation(x=0.5, y=0.35, text="∞", showarrow=False,
                           font=dict(color=color, size=48, family="system-ui, sans-serif"))
        fig.update_traces(number=dict(font=dict(color="rgba(0,0,0,0)"))) # hide real number
        
    fig.update_layout(**_layout(
        height=160,
        margin=dict(l=20, r=20, t=20, b=10),
    ))
    return fig