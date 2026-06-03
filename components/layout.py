from dash import dcc, html
from datetime import datetime
from utils.graph_order import DEFAULT_GRAPH_ORDER, GRAPH_TITLES


def _label(text_id: str, text: str, **extra) -> html.Label:
    return html.Label(text, className="form-label", id=text_id, **extra)


def create_layout():
    current_year = datetime.utcnow().year
    year_options = [{"label": str(y), "value": y} for y in range(current_year, 2017, -1)]

    return html.Div(
        style={"minHeight": "100vh", "backgroundColor": "#0d0d0d"},
        children=[

            # ── Header ───────────────────────────────────────────
            html.Header(
                className="app-header",
                children=[
                    html.Div(
                        className="app-header-brand",
                        children=[
                            html.Div(
                                className="brand-icon",
                                children=[
                                    html.Div(className="brand-stripe"),
                                    html.Div(className="brand-stripe"),
                                    html.Div(className="brand-stripe"),
                                ],
                            ),
                            html.Div(
                                className="brand-text",
                                children=[
                                    html.H1(
                                        id="page-title",
                                        className="app-title",
                                        children=[html.Span("OpenF1"), " · Driver Comparison"],
                                    ),
                                    html.P(
                                        id="intro-text",
                                        className="app-subtitle",
                                        children="Telemetria & Analisi · Formula 1 Open Data",
                                    ),
                                ],
                            ),
                        ],
                    ),
                    dcc.Dropdown(
                        id="language-dropdown",
                        options=[
                            {"label": "🇮🇹  Italiano", "value": "it"},
                            {"label": "🇬🇧  English",  "value": "en"},
                        ],
                        value="it",
                        clearable=False,
                        style={"width": "160px"},
                    ),
                ],
            ),

            # ── Stores (hidden) ──────────────────────────────────
            dcc.Store(id="meetings-store"),
            dcc.Store(id="sessions-store"),
            dcc.Store(id="laps-store"),
            dcc.Store(id="drivers-store"),
            dcc.Store(id="selected-time-store"),
            dcc.Store(id="graph-order-store", data=DEFAULT_GRAPH_ORDER),
            dcc.Store(id="lang-store", data="it"),

            # ── Body ─────────────────────────────────────────────
            html.Div(
                className="app-body",
                children=[

                    # ── Selection panel ──────────────────────────
                    html.Div(
                        className="panel",
                        children=[
                            html.Div(className="panel-title", children="Selezione Sessione"),

                            # Row 1: Anno · Circuito · Sessione
                            html.Div(
                                style={"display": "flex", "gap": "16px", "marginBottom": "14px"},
                                children=[
                                    html.Div(
                                        style={"flex": "0 0 140px"},
                                        children=[
                                            _label("year-label", "Anno"),
                                            dcc.Dropdown(
                                                id="year-input",
                                                options=year_options,
                                                value=current_year,
                                                clearable=False,
                                            ),
                                            html.Div(id="meetings-status", className="status-msg"),
                                        ],
                                    ),
                                    html.Div(
                                        style={"flex": "1"},
                                        children=[
                                            _label("meeting-label", "Circuito (Gran Premio)"),
                                            dcc.Dropdown(id="meeting-dropdown", options=[], value=None),
                                        ],
                                    ),
                                    html.Div(
                                        style={"flex": "0 0 220px"},
                                        children=[
                                            _label("session-label", "Sessione"),
                                            dcc.Dropdown(id="session-dropdown", options=[], value=None),
                                            html.Div(id="sessions-status", className="status-msg"),
                                        ],
                                    ),
                                ],
                            ),

                            html.Hr(),

                            # Row 2: Pilota 1 · Pilota 2 · Status
                            html.Div(
                                style={"display": "flex", "gap": "14px", "alignItems": "flex-start"},
                                children=[
                                    # Pilota 1
                                    html.Div(
                                        className="driver-panel driver-panel-1",
                                        children=[
                                            html.Div(
                                                className="driver-panel-header",
                                                children=[
                                                    html.Span("P1", className="driver-badge driver-badge-1"),
                                                    _label("driver1-label", "Pilota 1", style={"margin": "0"}),
                                                ],
                                            ),
                                            dcc.Dropdown(id="driver1-dropdown", options=[], value=None),
                                            html.Div(
                                                style={"marginTop": "10px"},
                                                children=[
                                                    _label("lap1-label", "Giro"),
                                                    dcc.Dropdown(id="lap1-dropdown", options=[], value=None),
                                                ],
                                            ),
                                        ],
                                    ),
                                    # Pilota 2
                                    html.Div(
                                        className="driver-panel driver-panel-2",
                                        children=[
                                            html.Div(
                                                className="driver-panel-header",
                                                children=[
                                                    html.Span("P2", className="driver-badge driver-badge-2"),
                                                    _label("driver2-label", "Pilota 2", style={"margin": "0"}),
                                                ],
                                            ),
                                            dcc.Dropdown(id="driver2-dropdown", options=[], value=None),
                                            html.Div(
                                                style={"marginTop": "10px"},
                                                children=[
                                                    _label("lap2-label", "Giro"),
                                                    dcc.Dropdown(id="lap2-dropdown", options=[], value=None),
                                                ],
                                            ),
                                        ],
                                    ),
                                    # Status sidebar
                                    html.Div(
                                        style={
                                            "flex": "0 0 280px",
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "gap": "8px",
                                            "justifyContent": "center",
                                            "paddingTop": "6px",
                                        },
                                        children=[
                                            html.Div(id="laps-status", className="status-msg"),
                                            html.Div(id="lap-compare-status"),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),

                    # ── Tabs ─────────────────────────────────────
                    dcc.Tabs(
                        id="page-tabs",
                        value="telemetry",
                        children=[

                            # ── Tab: Telemetria giro ─────────────
                            dcc.Tab(
                                id="tab-telemetry",
                                label="Telemetria giro",
                                value="telemetry",
                                children=[
                                    html.Div(
                                        style={"paddingTop": "16px"},
                                        children=[
                                            # toolbar
                                            html.Div(
                                                className="panel",
                                                style={"display": "flex", "gap": "20px", "alignItems": "flex-start"},
                                                children=[
                                                    html.Div(
                                                        children=[
                                                            html.Div(
                                                                className="panel-title",
                                                                style={"marginBottom": "10px"},
                                                                children="Ordine grafici",
                                                            ),
                                                            dcc.RadioItems(
                                                                id="graph-order-radio",
                                                                options=[
                                                                    {"label": GRAPH_TITLES[g], "value": g}
                                                                    for g in DEFAULT_GRAPH_ORDER
                                                                ],
                                                                value=DEFAULT_GRAPH_ORDER[0],
                                                                labelStyle={"display": "block", "margin": "4px 0", "fontSize": "0.8rem"},
                                                                inputStyle={"marginRight": "8px"},
                                                                id="graph-order-label",
                                                            ),
                                                        ],
                                                        style={"minWidth": "220px"},
                                                    ),
                                                    html.Div(
                                                        style={"display": "flex", "flexDirection": "column", "gap": "6px", "paddingTop": "34px"},
                                                        children=[
                                                            html.Button(id="move-up-btn",   children="↑ Su",    n_clicks=0),
                                                            html.Button(id="move-down-btn", children="↓ Giù",   n_clicks=0),
                                                            html.Button(id="reset-graph-order-btn", children="⟳ Reset", n_clicks=0),
                                                        ],
                                                    ),
                                                    html.Div(
                                                        style={"display": "flex", "flexDirection": "column", "gap": "10px", "paddingTop": "34px"},
                                                        children=[
                                                            html.Button(id="print-btn", children="⎙  Stampa PDF", n_clicks=0),
                                                            html.Div(id="graph-order-msg", className="status-msg"),
                                                        ],
                                                    ),
                                                ],
                                            ),
                                            html.Div(id="print-trigger", style={"display": "none"}),
                                            # grafici
                                            dcc.Loading(
                                                type="circle",
                                                color="#e10600",
                                                children=html.Div(
                                                    id="graphs-container",
                                                    style={"display": "flex", "flexDirection": "column", "gap": "10px"},
                                                    children=[
                                                        html.Div(
                                                            className="graph-wrap",
                                                            children=[
                                                                html.Div(GRAPH_TITLES.get(gid, gid), className="graph-label"),
                                                                dcc.Graph(id=gid, config={"displayModeBar": True, "displaylogo": False}),
                                                            ],
                                                        )
                                                        for gid in DEFAULT_GRAPH_ORDER
                                                    ],
                                                ),
                                            ),
                                        ],
                                    ),
                                ],
                            ),

                            # ── Tab: Confronto giri ──────────────
                            dcc.Tab(
                                id="tab-all-laps",
                                label="Confronto giri",
                                value="all-laps",
                                children=[
                                    html.Div(
                                        style={"paddingTop": "16px", "display": "flex", "flexDirection": "column", "gap": "10px"},
                                        children=[
                                            dcc.Loading(type="circle", color="#e10600",
                                                        children=html.Div(id="all-laps-summary",
                                                                          className="panel", style={"minHeight": "40px"})),
                                            html.Div(className="graph-wrap",
                                                     children=dcc.Loading(type="circle", color="#e10600",
                                                                          children=dcc.Graph(id="all-laps-times-graph",
                                                                                             config={"displaylogo": False}))),
                                            html.Div(className="graph-wrap",
                                                     children=dcc.Loading(type="circle", color="#e10600",
                                                                          children=dcc.Graph(id="all-laps-delta-graph",
                                                                                             config={"displaylogo": False}))),
                                            html.Div(className="graph-wrap",
                                                     children=dcc.Loading(type="circle", color="#e10600",
                                                                          children=dcc.Graph(id="all-laps-heatmap",
                                                                                             style={"width": "100%"},
                                                                                             config={"responsive": True, "displaylogo": False}))),
                                        ],
                                    ),
                                ],
                            ),

                            # ── Tab: Strategia gomme ─────────────
                            dcc.Tab(
                                id="tab-strategy",
                                label="Strategia gomme",
                                value="strategy",
                                children=[
                                    html.Div(
                                        style={"paddingTop": "16px", "display": "flex", "flexDirection": "column", "gap": "10px"},
                                        children=[
                                            dcc.Loading(type="circle", color="#e10600",
                                                        children=html.Div(id="strategy-summary",
                                                                          className="panel", style={"minHeight": "40px"})),
                                            html.Div(className="graph-wrap",
                                                     children=dcc.Loading(type="circle", color="#e10600",
                                                                          children=dcc.Graph(id="stints-graph", config={"displaylogo": False}))),
                                            html.Div(className="graph-wrap",
                                                     children=dcc.Loading(type="circle", color="#e10600",
                                                                          children=dcc.Graph(id="pitstop-graph", config={"displaylogo": False}))),
                                            html.Div(className="graph-wrap",
                                                     children=dcc.Loading(type="circle", color="#e10600",
                                                                          children=dcc.Graph(id="degradation-graph", config={"displaylogo": False}))),
                                        ],
                                    ),
                                ],
                            ),

                            # ── Tab: Classifica giri ─────────────
                            dcc.Tab(
                                id="tab-ranking",
                                label="Classifica giri",
                                value="ranking",
                                children=[
                                    html.Div(
                                        style={"paddingTop": "16px"},
                                        children=[
                                            html.Div(className="graph-wrap",
                                                     children=dcc.Loading(type="circle", color="#e10600",
                                                                          children=dcc.Graph(id="ranking-graph", config={"displaylogo": False}))),
                                        ],
                                    ),
                                ],
                            ),

                            # ── Tab: Miglior giro per pilota ─────
                            dcc.Tab(
                                id="tab-best-laps",
                                label="Miglior giro",
                                value="best-laps",
                                children=[
                                    html.Div(
                                        style={"paddingTop": "16px"},
                                        children=[
                                            dcc.Loading(type="circle", color="#e10600",
                                                        children=html.Div(id="best-laps-table",
                                                                          className="panel")),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
