from dash import dcc, html
from datetime import datetime
from utils.graph_order import DEFAULT_GRAPH_ORDER, GRAPH_TITLES


def create_layout():
    """Crea il layout della dashboard."""
    current_year = datetime.utcnow().year
    return html.Div(
        style={"fontFamily": "Arial, sans-serif", "margin": "20px"},
        children=[
            html.H1("OpenF1 – Driver Comparison Dashboard"),
            html.P("Flusso: Anno → Circuito → Session → Drivers → Lap → Telemetria + Location + Delta time."),

            html.Hr(),

            # RIGA 1: anno + circuito
            html.Div(
                style={"display": "flex", "gap": "20px", "marginBottom": "20px"},
                children=[
                    html.Div(
                        style={"flex": "1"},
                        children=[
                            html.Label("Anno"),
                            dcc.Input(
                                id="year-input",
                                type="number",
                                placeholder="Es. 2024",
                                value=current_year,   # prevalorizzato con anno corrente
                                style={"width": "100%"},
                            ),
                            html.Button( 
                                "Carica Circuiti",
                                id="load-meetings-btn",
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
                            html.Label("Circuito (Gran Premio)"),
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
                            html.Label("Sessione"),
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
                            html.Label("Pilota 1"),
                            dcc.Dropdown(id="driver1-dropdown", options=[], value=None),
                            html.Label("Giro Pilota 1"),
                            dcc.Dropdown(id="lap1-dropdown", options=[], value=None),
                            html.Br(),
                            html.Label("Pilota 2"),
                            dcc.Dropdown(id="driver2-dropdown", options=[], value=None),
                            html.Label("Giro Pilota 2"),
                            dcc.Dropdown(id="lap2-dropdown", options=[], value=None),
                            html.Div(
                                id="laps-status",
                                style={"marginTop": "10px", "color": "#555"},
                            ),
                        ],
                    ),
                ],
            ),

            # Pulsante reset ordine grafici
            html.Div(
                style={"display": "flex", "gap": "12px", "alignItems": "center", "marginBottom": "15px"},
                children=[
                    html.Div(
                        children=[
                            html.Label("Ordine grafici:"),
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
                            html.Button("↑ Move Up", id="move-up-btn", n_clicks=0),
                            html.Button("↓ Move Down", id="move-down-btn", n_clicks=0),
                            html.Button("🔄 Reset ordine", id="reset-graph-order-btn", n_clicks=0),
                        ],
                    ),
                    html.Div(id="graph-order-msg", style={"color": "#555", "marginLeft": "12px"}),
                ],
            ),

            # Store per ordine grafici
            dcc.Store(id="graph-order-store", data=DEFAULT_GRAPH_ORDER),

            # Store per cache
            dcc.Store(id="meetings-store"),
            dcc.Store(id="sessions-store"),
            dcc.Store(id="laps-store"),
            dcc.Store(id="drivers-store"),
            dcc.Store(id="selected-time-store"),

            html.Hr(),

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
    )
