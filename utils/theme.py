"""Registra il template Plotly F1-dark e lo imposta come default globale."""

import plotly.graph_objects as go
import plotly.io as pio

_layout = go.Layout(
    paper_bgcolor="#151517",
    plot_bgcolor="#0f0f11",
    font=dict(color="#c8c8cf", family="Inter, -apple-system, sans-serif", size=12),
    title=dict(font=dict(color="#f4f4f6", size=15, family="Rajdhani, Inter, sans-serif"), x=0.02),
    xaxis=dict(
        gridcolor="#222228",
        linecolor="#2a2a30",
        zerolinecolor="#2a2a30",
        tickfont=dict(color="#8a8a93"),
    ),
    yaxis=dict(
        gridcolor="#222228",
        linecolor="#2a2a30",
        zerolinecolor="#2a2a30",
        tickfont=dict(color="#8a8a93"),
    ),
    legend=dict(
        bgcolor="rgba(28,28,32,0.85)",
        bordercolor="#2a2a30",
        borderwidth=1,
        font=dict(color="#c8c8cf"),
    ),
    colorway=["#e10600", "#00b4e6", "#00d2be", "#ff8000", "#ff4d6d", "#a0f0a0", "#ffd700", "#da70d6"],
    hoverlabel=dict(bgcolor="#1c1c20", bordercolor="#2a2a30", font=dict(color="#f4f4f6", family="Inter, sans-serif")),
    margin=dict(l=55, r=24, t=54, b=52),
)

pio.templates["f1dark"] = go.layout.Template(layout=_layout)
pio.templates.default = "f1dark"
