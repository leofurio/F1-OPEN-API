from dash import dcc, html


def create_layout():
    """Crea il layout della dashboard."""
    return html.Div(
        style={"fontFamily": "Arial, sans-serif", "margin": "20px"},
        children=[
            html.H1("OpenF1 – Driver Comparison Dashboard"),
            html.P("Flusso: Circuito → Session → Drivers → Lap → Telemetria + Location + Delta time."),

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

            # Store per cache
            dcc.Store(id="meetings-store"),
            dcc.Store(id="sessions-store"),
            dcc.Store(id="laps-store"),
            dcc.Store(id="drivers-store"),
            dcc.Store(id="selected-time-store"),

            html.Hr(),

            # Grafici
            html.Div(
                style={"display": "flex", "flexDirection": "column", "gap": "20px"},
                children=[
                    dcc.Graph(id="track-graph"),
                    dcc.Graph(id="delta-graph"),
                    dcc.Graph(id="speed-graph"),
                    dcc.Graph(id="throttle-graph"),
                    dcc.Graph(id="brake-graph"),
                    dcc.Graph(id="gear-graph"),
                ],
            ),
        ],
    )