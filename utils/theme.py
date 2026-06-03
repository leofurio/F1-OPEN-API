"""Registra il template Plotly F1-dark e lo imposta come default globale."""

import plotly.graph_objects as go
import plotly.io as pio

_layout = go.Layout(
    paper_bgcolor="#1a1a1a",
    plot_bgcolor="#111111",
    font=dict(color="#cccccc", family="Inter, -apple-system, sans-serif", size=12),
    title=dict(font=dict(color="#f0f0f0", size=14), x=0.02),
    xaxis=dict(
        gridcolor="#252525",
        linecolor="#333333",
        zerolinecolor="#333333",
        tickfont=dict(color="#888888"),
    ),
    yaxis=dict(
        gridcolor="#252525",
        linecolor="#333333",
        zerolinecolor="#333333",
        tickfont=dict(color="#888888"),
    ),
    legend=dict(
        bgcolor="#222222",
        bordercolor="#333333",
        borderwidth=1,
        font=dict(color="#cccccc"),
    ),
    colorway=["#e10600", "#0090d0", "#00d2be", "#ff8000", "#dc143c", "#90ee90", "#ffd700", "#da70d6"],
    hoverlabel=dict(bgcolor="#1c1c1c", bordercolor="#333", font=dict(color="#f0f0f0")),
    margin=dict(l=50, r=20, t=50, b=50),
)

pio.templates["f1dark"] = go.layout.Template(layout=_layout)
pio.templates.default = "f1dark"
