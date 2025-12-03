from dash import dcc, html
from datetime import datetime
from utils.graph_order import DEFAULT_GRAPH_ORDER, GRAPH_TITLES


def create_layout():
    """Crea il layout della dashboard."""
    current_year = datetime.utcnow().year
    return html.Div(
        style={"fontFamily": "Arial, sans-serif", "margin": "20px"},
        children=[
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "gap": "12px"},
                children=[
                    html.H1(id="page-title", children="OpenF1 - Driver Comparison Dashboard"),
                    dcc.Dropdown(
                        id="language-dropdown",
                        options=[
                            {"label": "Italiano", "value": "it"},
                            {"label": "English", "value": "en"},
                        ],
                        value="it",
                        clearable=False,
                        style={"width": "180px"},
                    ),
                ],
            ),
            html.P(
                id="intro-text",
                children="Flusso: Anno > Circuito > Sessione > Drivers > Lap > Telemetria + Location + Delta time.",
            ),

            html.Hr(),

            # RIGA 1: anno + circuito
            html.Div(
                style={"display": "flex", "gap": "20px", "marginBottom": "20px"},
                children=[
                    html.Div(
                        style={"flex": "1"},
                        children=[
                            html.Label(id="year-label", children="Anno"),
                            dcc.Input(
                                id="year-input",
                                type="number",
                                placeholder="Es. 2024",
                                value=current_year,   # prevalorizzato con anno corrente
                                style={"width": "100%"},
                            ),
                            html.Button(
                                id="load-meetings-btn",
                                children="Carica Circuiti",
                                n_clicks=0,
                                style={"marginTop": "8px"},
                            ),
                            html.Div(
                                id="meetings-status",
                                style={"marginTop": "10px", "color": "#555"},
                            ),
                        ],
                    ),
                    html.Div(
                        style={"flex": "2"},
                        children=[
                            html.Label(id="meeting-label", children="Circuito (Gran Premio)"),
                            dcc.Dropdown(id="meeting-dropdown", options=[], value=None),
                        ],
                    ),
                ],
            ),

            # RIGA 2: sessione + piloti + giri
            html.Div(
                style={"display": "flex", "gap": "20px", "marginBottom": "20px"},
                children=[
                    html.Div(
                        style={"flex": "1"},
                        children=[
                            html.Label(id="session-label", children="Sessione"),
                            dcc.Dropdown(id="session-dropdown", options=[], value=None),
                            html.Div(
                                id="sessions-status",
                                style={"marginTop": "10px", "color": "#555"},
                            ),
                        ],
                    ),
                    html.Div(
                        style={"flex": "2"},
                        children=[
                            html.Label(id="driver1-label", children="Pilota 1"),
                            dcc.Dropdown(id="driver1-dropdown", options=[], value=None),
                            html.Label(id="lap1-label", children="Giro Pilota 1"),
                            dcc.Dropdown(id="lap1-dropdown", options=[], value=None),
                            html.Br(),
                            html.Label(id="driver2-label", children="Pilota 2"),
                            dcc.Dropdown(id="driver2-dropdown", options=[], value=None),
                            html.Label(id="lap2-label", children="Giro Pilota 2"),
                            dcc.Dropdown(id="lap2-dropdown", options=[], value=None),
                            html.Div(
                                id="laps-status",
                                style={"marginTop": "10px", "color": "#555"},
                            ),
                            html.Div(
                                id="lap-compare-status",
                                style={"marginTop": "6px", "color": "#222", "fontWeight": "bold"},
                            ),
                        ],
                    ),
                ],
            ),

            # Store per cache e stato condiviso
            dcc.Store(id="meetings-store"),
            dcc.Store(id="sessions-store"),
            dcc.Store(id="laps-store"),
            dcc.Store(id="drivers-store"),
            dcc.Store(id="selected-time-store"),
            dcc.Store(id="graph-order-store", data=DEFAULT_GRAPH_ORDER),
            dcc.Store(id="lang-store", data="it"),

            html.Hr(),

            dcc.Tabs(
                id="page-tabs",
                value="telemetry",
                children=[
                    dcc.Tab(
                        id="tab-telemetry",
                        label="Telemetria giro",
                        value="telemetry",
                        children=[
                            html.Div(
                                style={"display": "flex", "gap": "12px", "alignItems": "center", "marginBottom": "15px"},
                                children=[
                                    html.Div(
                                        children=[
                                            html.Label(id="graph-order-label", children="Ordine grafici:"),
                                            dcc.RadioItems(
                                                id="graph-order-radio",
                                                options=[{"label": GRAPH_TITLES[g], "value": g} for g in DEFAULT_GRAPH_ORDER],
                                                value=DEFAULT_GRAPH_ORDER[0],
                                                labelStyle={"display": "block", "margin": "4px 0"},
                                                inputStyle={"marginRight": "8px"},
                                            ),
                                        ],
                                        style={"minWidth": "220px"},
                                    ),
                                    html.Div(
                                        style={"display": "flex", "flexDirection": "column", "gap": "8px"},
                                        children=[
                                            html.Button(id="move-up-btn", children="Move Up", n_clicks=0),
                                            html.Button(id="move-down-btn", children="Move Down", n_clicks=0),
                                            html.Button(id="reset-graph-order-btn", children="Reset ordine", n_clicks=0),
                                        ],
                                    ),
                                    html.Div(id="graph-order-msg", style={"color": "#555", "marginLeft": "12px"}),
                                ],
                            ),

                            html.Div(
                                style={"marginBottom": "12px"},
                                children=[
                                    html.Button(id="print-btn", children="Stampa PDF", n_clicks=0),
                                ],
                            ),
                            html.Div(id="print-trigger", style={"display": "none"}),

                            # Contenitore grafici con spinner durante l'update
                            dcc.Loading(
                                id="graphs-loading",
                                type="circle",
                                color="#555",
                                children=html.Div(
                                    id="graphs-container",
                                    style={"display": "flex", "flexDirection": "column", "gap": "20px"},
                                    # Seed iniziale per evitare errori di validazione prima del callback
                                    children=[
                                        html.Div(
                                            [
                                                html.H3(GRAPH_TITLES.get(graph_id, graph_id), style={"marginBottom": "6px"}),
                                                dcc.Loading(
                                                    type="circle",
                                                    color="#555",
                                                    children=dcc.Graph(id=graph_id),
                                                ),
                                            ],
                                            style={"display": "flex", "flexDirection": "column", "gap": "6px"},
                                        )
                                        for graph_id in DEFAULT_GRAPH_ORDER
                                    ],
                                ),
                            ),
                        ],
                    ),
                    dcc.Tab(
                        id="tab-all-laps",
                        label="Confronto tutti i giri",
                        value="all-laps",
                        children=[
                            html.Div(
                                style={"display": "flex", "flexDirection": "column", "gap": "14px", "marginTop": "14px"},
                                children=[
                                    dcc.Loading(
                                        type="circle",
                                        color="#555",
                                        children=html.Div(id="all-laps-summary"),
                                    ),
                                    dcc.Loading(
                                        type="circle",
                                        color="#555",
                                        children=dcc.Graph(id="all-laps-times-graph"),
                                    ),
                                    dcc.Loading(
                                        type="circle",
                                        color="#555",
                                        children=dcc.Graph(id="all-laps-delta-graph"),
                                    ),
                                    dcc.Loading(
                                        type="circle",
                                        color="#555",
                                        children=dcc.Graph(
                                            id="all-laps-heatmap",
                                            style={"width": "100%"},
                                            config={"responsive": True},
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
