import requests
import pandas as pd
from urllib.parse import urlencode

from dash import Dash, dcc, html, Input, Output, State
import plotly.graph_objects as go
import numpy as np  # <-- per delta time

BASE_URL = "https://api.openf1.org/v1"

# Colori fissi per i due piloti (coerenti su tutti i grafici)
COLOR1 = "#1f77b4"   # blu
COLOR2 = "#d62728"   # rosso


# =========================
# Helper API OpenF1
# =========================

def fetch_meetings(year: int | None = None) -> pd.DataFrame:
    """
    Recupera i meeting (Gran Premi / eventi) filtrabili per anno.
    """
    params = {}
    if year:
        params["year"] = year
    url = f"{BASE_URL}/meetings"
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    for col in ["meeting_key", "year", "country_name", "meeting_name"]:
        if col not in df.columns:
            df[col] = None
    return df


def fetch_sessions(meeting_key: int) -> pd.DataFrame:
    """
    Recupera le sessioni (FP, Quali, Gara, Sprint) per un meeting.
    """
    params = {"meeting_key": meeting_key}
    url = f"{BASE_URL}/sessions"
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    for col in ["session_key", "session_name", "session_type"]:
        if col not in df.columns:
            df[col] = None
    return df


def fetch_laps(session_key: int) -> pd.DataFrame:
    """
    Recupera i giri per una sessione.
    """
    params = {"session_key": session_key}
    url = f"{BASE_URL}/laps"
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    for col in ["driver_number", "lap_number", "date_start", "date_end"]:
        if col not in df.columns:
            df[col] = None
    return df


def fetch_drivers(session_key: int) -> pd.DataFrame:
    """
    Recupera i piloti per una sessione (per avere nomi, team, ecc.).
    """
    params = {"session_key": session_key}
    url = f"{BASE_URL}/drivers"
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    # campi utili
    for col in ["driver_number", "full_name", "name_acronym", "team_name"]:
        if col not in df.columns:
            df[col] = None
    return df


def fetch_car_data_for_lap(session_key: int,
                           driver_number: int,
                           lap_row: pd.Series) -> pd.DataFrame:
    """
    Recupera i dati di telemetria /car_data per un singolo giro,
    usando date_start/date_end del giro.
    Se date_end è None, calcola un intervallo ragionevole (~2 minuti).
    """
    date_start = lap_row.get("date_start")
    date_end = lap_row.get("date_end")

    if not date_start:
        return pd.DataFrame()

    # Se date_end è None, stima ~2 minuti dopo date_start
    if not date_end:
        from datetime import timedelta
        start_dt = pd.to_datetime(date_start)
        date_end = (start_dt + timedelta(minutes=2)).isoformat()
        print(f"⚠ date_end era None, usando stima: {date_end}")

    params = {
        "session_key": session_key,
        "driver_number": driver_number,
    }

    url = f"{BASE_URL}/car_data"

    # Usa gli operatori corretti per OpenF1: date>...&date<...
    query_string = urlencode(params)
    query_string += f"&date>{date_start}&date<{date_end}"

    full_url = f"{url}?{query_string}"
    print(f"🔗 Query URL (car_data): {full_url}")

    resp = requests.get(full_url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if not data:
        print(f"⚠ Nessun car_data trovato per driver {driver_number} tra {date_start} e {date_end}")
        return pd.DataFrame()

    df = pd.DataFrame(data)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        t0 = df["date"].min()
        df["t_rel_s"] = (df["date"] - t0).dt.total_seconds()
    else:
        df["t_rel_s"] = range(len(df))

    for col in ["speed", "throttle", "brake", "n_gear"]:
        if col not in df.columns:
            df[col] = None

    return df


def fetch_location_for_lap(session_key: int,
                           driver_number: int,
                           lap_row: pd.Series) -> pd.DataFrame:
    """
    Recupera i dati di posizione /location per un singolo giro,
    usando date_start/date_end del giro.
    Restituisce x, y e tempo relativo.
    """
    date_start = lap_row.get("date_start")
    date_end = lap_row.get("date_end")

    if not date_start:
        return pd.DataFrame()

    if not date_end:
        from datetime import timedelta
        start_dt = pd.to_datetime(date_start)
        date_end = (start_dt + timedelta(minutes=2)).isoformat()
        print(f"⚠ (location) date_end era None, usando stima: {date_end}")

    params = {
        "session_key": session_key,
        "driver_number": driver_number,
    }

    url = f"{BASE_URL}/location"

    query_string = urlencode(params)
    query_string += f"&date>{date_start}&date<{date_end}"

    full_url = f"{url}?{query_string}"
    print(f"🔗 Query URL (location): {full_url}")

    resp = requests.get(full_url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        print(f"⚠ Nessun location trovato per driver {driver_number} tra {date_start} e {date_end}")
        return pd.DataFrame()

    df = pd.DataFrame(data)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        t0 = df["date"].min()
        df["t_rel_s"] = (df["date"] - t0).dt.total_seconds()
    else:
        df["t_rel_s"] = range(len(df))

    for col in ["x", "y", "z"]:
        if col not in df.columns:
            df[col] = None

    return df


def compute_delta_time(df1: pd.DataFrame,
                       df2: pd.DataFrame,
                       n_points: int = 200):
    """
    Calcola il delta time tra due giri usando i dati car_data:
    - crea un asse 'progress' 0–1 per ciascun driver basato sull'indice
    - interpola t_rel_s su una griglia comune
    - restituisce (progress_grid, delta_t = t2 - t1)
    """
    if df1.empty or df2.empty:
        return None, None

    df1 = df1.sort_values("t_rel_s").copy()
    df2 = df2.sort_values("t_rel_s").copy()

    df1["progress"] = np.linspace(0.0, 1.0, len(df1))
    df2["progress"] = np.linspace(0.0, 1.0, len(df2))

    grid = np.linspace(0.0, 1.0, n_points)

    t1_interp = np.interp(grid, df1["progress"], df1["t_rel_s"])
    t2_interp = np.interp(grid, df2["progress"], df2["t_rel_s"])

    delta = t2_interp - t1_interp  # >0: driver2 più lento, <0: più veloce
    return grid, delta


# =========================
# App Dash
# =========================

app = Dash(__name__)
app.title = "OpenF1 – Driver Comparison (Meeting→Session)"

app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "margin": "20px"},
    children=[
        html.H1("OpenF1 – Driver Comparison Dashboard"),
        html.P("Flusso corretto: Circuito → Session → Drivers → Lap → Telemetria + Location + Delta time."),

        html.Hr(),

        # RIGA 1: anno + meeting
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

        # RIGA 2: sessione + piloti + lap
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

        html.Hr(),

        # Grafici
        html.Div(
            style={"display": "flex", "flexDirection": "column", "gap": "20px"},
            children=[
                dcc.Graph(id="track-graph"),    # pista
                dcc.Graph(id="delta-graph"),    # delta time
                dcc.Graph(id="speed-graph"),
                dcc.Graph(id="throttle-graph"),
                dcc.Graph(id="brake-graph"),
                dcc.Graph(id="gear-graph"),
            ],
        ),
    ],
)


# =========================
# Callbacks
# =========================

# 1) Carica circuiti per anno
@app.callback(
    output=[
        Output("meetings-store", "data"),
        Output("meeting-dropdown", "options"),
        Output("meeting-dropdown", "value"),
        Output("meetings-status", "children"),
    ],
    inputs=[Input("load-meetings-btn", "n_clicks")],
    state=[State("year-input", "value")],
    prevent_initial_call=True,
)
def load_meetings(n_clicks, year):
    try:
        df = fetch_meetings(year=int(year)) if year else fetch_meetings()
    except Exception as e:
        return None, [], None, f"❌ Errore nel caricamento dei circuiti: {e}"

    if df.empty:
        return None, [], None, "⚠ Nessun circuito trovato per questo anno."

    def make_label(row):
        y = row.get("year")
        name = row.get("meeting_name") or "Unknown"
        country = row.get("country_name") or ""
        return f"{y} – {name} ({country})" if country else f"{y} – {name}"

    options = [
        {"label": make_label(row), "value": int(row["meeting_key"])}
        for _, row in df.iterrows()
        if pd.notna(row["meeting_key"])
    ]
    value = options[0]["value"] if options else None
    status = f"✅ Circuiti caricati: {len(options)}"

    return df.to_dict("records"), options, value, status


# 2) Quando cambio circuito → carica sessions
@app.callback(
    output=[
        Output("sessions-store", "data"),
        Output("session-dropdown", "options"),
        Output("session-dropdown", "value"),
        Output("sessions-status", "children"),
    ],
    inputs=[Input("meeting-dropdown", "value")],
    state=[State("meetings-store", "data")],
)
def load_sessions(meeting_key, meetings_data):
    if not meeting_key:
        return None, [], None, "Seleziona un circuito."

    try:
        df_sessions = fetch_sessions(int(meeting_key))
    except Exception as e:
        return None, [], None, f"❌ Errore nel caricamento delle sessioni per il circuito: {e}"

    if df_sessions.empty:
        return None, [], None, "⚠ Nessuna sessione trovata per questo circuito."

    options = [
        {
            "label": f"{row.get('session_name') or row.get('session_type') or 'Session'} "
                     f"(key={int(row['session_key'])})",
            "value": int(row["session_key"]),
        }
        for _, row in df_sessions.iterrows()
        if pd.notna(row["session_key"])
    ]

    value = options[-1]["value"] if options else None  # di solito la gara è l'ultima
    status = f"✅ Sessioni caricate: {len(options)}"

    return df_sessions.to_dict("records"), options, value, status


# 3) Quando cambio session → carico laps + drivers e popolo dropdown
@app.callback(
    output=[
        Output("laps-store", "data"),
        Output("driver1-dropdown", "options"),
        Output("driver1-dropdown", "value"),
        Output("driver2-dropdown", "options"),
        Output("driver2-dropdown", "value"),
        Output("laps-status", "children"),
        Output("drivers-store", "data"),
    ],
    inputs=[Input("session-dropdown", "value")],
)
def load_laps_and_drivers(session_key):
    if not session_key:
        return None, [], None, [], None, "Seleziona una sessione.", None

    try:
        df_laps = fetch_laps(int(session_key))
    except Exception as e:
        return None, [], None, [], None, f"❌ Errore nel caricamento dei laps: {e}", None

    if df_laps.empty:
        return None, [], None, [], None, "⚠ Nessun giro trovato per questa sessione.", None

    try:
        df_drivers = fetch_drivers(int(session_key))
    except Exception:
        df_drivers = pd.DataFrame()

    driver_numbers = sorted(df_laps["driver_number"].dropna().unique())

    def driver_label(num: int) -> str:
        if not df_drivers.empty:
            row = df_drivers[df_drivers["driver_number"] == num]
            if not row.empty:
                row = row.iloc[0]
                full_name = row.get("full_name") or row.get("name_acronym") or ""
                team = row.get("team_name") or ""
                if full_name and team:
                    return f"#{int(num)} – {full_name} ({team})"
                elif full_name:
                    return f"#{int(num)} – {full_name}"
        return f"Driver #{int(num)}"

    driver_options = [
        {"label": driver_label(int(d)), "value": int(d)} for d in driver_numbers
    ]

    d1 = driver_numbers[0] if len(driver_numbers) > 0 else None
    d2 = driver_numbers[1] if len(driver_numbers) > 1 else None

    status = (
        f"✅ Laps caricati: {len(df_laps)} "
        f"(drivers: {len(driver_numbers)}, "
        f"max lap: {int(df_laps['lap_number'].max())})"
    )

    return (
        df_laps.to_dict("records"),
        driver_options,
        d1,
        driver_options,
        d2,
        status,
        df_drivers.to_dict("records") if not df_drivers.empty else None,
    )


# 3bis) Aggiorna lap options quando cambio driver1 o driver2
@app.callback(
    output=[
        Output("lap1-dropdown", "options"),
        Output("lap1-dropdown", "value"),
        Output("lap2-dropdown", "options"),
        Output("lap2-dropdown", "value"),
    ],
    inputs=[
        Input("driver1-dropdown", "value"),
        Input("driver2-dropdown", "value"),
    ],
    state=[State("laps-store", "data")],
)
def update_lap_dropdowns(driver1, driver2, laps_data):
    if not laps_data:
        return [], None, [], None

    df_laps = pd.DataFrame(laps_data)

    # Giri disponibili per driver1
    laps1 = sorted(
        df_laps[df_laps["driver_number"] == driver1]["lap_number"].dropna().unique()
    ) if driver1 else []
    lap1_options = [{"label": f"Lap {int(l)}", "value": int(l)} for l in laps1]
    lap1_val = int(laps1[-1]) if laps1 else None

    # Giri disponibili per driver2
    laps2 = sorted(
        df_laps[df_laps["driver_number"] == driver2]["lap_number"].dropna().unique()
    ) if driver2 else []
    lap2_options = [{"label": f"Lap {int(l)}", "value": int(l)} for l in laps2]
    lap2_val = int(laps2[-1]) if laps2 else None

    return lap1_options, lap1_val, lap2_options, lap2_val


# 4) Update grafici (track + delta + telemetria)
@app.callback(
    output=[
        Output("track-graph", "figure"),
        Output("delta-graph", "figure"),
        Output("speed-graph", "figure"),
        Output("throttle-graph", "figure"),
        Output("brake-graph", "figure"),
        Output("gear-graph", "figure"),
    ],
    inputs=[
        Input("session-dropdown", "value"),
        Input("driver1-dropdown", "value"),
        Input("lap1-dropdown", "value"),
        Input("driver2-dropdown", "value"),
        Input("lap2-dropdown", "value"),
    ],
    state=[
        State("laps-store", "data"),
        State("drivers-store", "data"),
    ],
    prevent_initial_call=False,
)
def update_graphs(session_key, driver1, lap1_number, driver2, lap2_number, laps_data, drivers_data):
    empty_fig = go.Figure()
    empty_fig.update_layout(
        title="Seleziona sessione, piloti e giri.",
        xaxis_title="Tempo relativo (s)",
        yaxis_title="",
        template="plotly_white",
    )

    # figure vuote di default anche per track/delta
    track_fig = go.Figure()
    track_fig.update_layout(
        title="Tracciato non disponibile",
        xaxis_title="X (m)",
        yaxis_title="Y (m)",
        template="plotly_white",
    )

    delta_fig = go.Figure()
    delta_fig.update_layout(
        title="Delta time non disponibile",
        xaxis_title="Progresso giro (%)",
        yaxis_title="Delta tempo (s)",
        template="plotly_white",
    )

    if not laps_data or not session_key or not driver1 or not driver2 or not lap1_number or not lap2_number:
        return track_fig, delta_fig, empty_fig, empty_fig, empty_fig, empty_fig

    df_laps = pd.DataFrame(laps_data)
    df_drivers = pd.DataFrame(drivers_data) if drivers_data else pd.DataFrame()

    def driver_label(num: int) -> str:
        if not df_drivers.empty:
            row = df_drivers[df_drivers["driver_number"] == num]
            if not row.empty:
                row = row.iloc[0]
                full_name = row.get("full_name") or row.get("name_acronym") or ""
                team = row.get("team_name") or ""
                if full_name and team:
                    return f"#{int(num)} – {full_name} ({team})"
                elif full_name:
                    return f"#{int(num)} – {full_name}"
        return f"Driver #{int(num)}"

    lap1_rows = df_laps[
        (df_laps["driver_number"] == driver1) & (df_laps["lap_number"] == lap1_number)
    ]
    lap2_rows = df_laps[
        (df_laps["driver_number"] == driver2) & (df_laps["lap_number"] == lap2_number)
    ]

    if lap1_rows.empty or lap2_rows.empty:
        empty_fig.update_layout(
            title="Dati non disponibili per questo giro/pilota."
        )
        return track_fig, delta_fig, empty_fig, empty_fig, empty_fig, empty_fig

    lap1_row = lap1_rows.iloc[0]
    lap2_row = lap2_rows.iloc[0]

    try:
        print(f"Lap1 (Driver {driver1}): date_start={lap1_row.get('date_start')}")
        print(f"Lap2 (Driver {driver2}): date_start={lap2_row.get('date_start')}")

        df1 = fetch_car_data_for_lap(int(session_key), int(driver1), lap1_row)
        df2 = fetch_car_data_for_lap(int(session_key), int(driver2), lap2_row)

        print(f"Dati car_data - Driver1 Lap{lap1_number}: {len(df1)} records, "
              f"Driver2 Lap{lap2_number}: {len(df2)} records")

        loc1 = fetch_location_for_lap(int(session_key), int(driver1), lap1_row)
        loc2 = fetch_location_for_lap(int(session_key), int(driver2), lap2_row)

    except Exception as e:
        empty_fig.update_layout(
            title=f"Errore nel recupero dei dati: {e}"
        )
        return track_fig, delta_fig, empty_fig, empty_fig, empty_fig, empty_fig

    if df1.empty and df2.empty:
        empty_fig.update_layout(
            title="Nessun dato car_data disponibile per questi giri."
        )
        return track_fig, delta_fig, empty_fig, empty_fig, empty_fig, empty_fig

    # Label “brevi” per i titoli, label complete (con lap) per le legend
    name1_short = driver_label(int(driver1))
    name2_short = driver_label(int(driver2))

    name1 = f"{name1_short} – Lap {lap1_number}"
    name2 = f"{name2_short} – Lap {lap2_number}"

    title_suffix = f" – {name1_short} Lap {lap1_number} vs {name2_short} Lap {lap2_number}"

    # Nota se uno dei due non ha dati car_data
    note = ""
    if df1.empty and not df2.empty:
        note = f" – Nessun dato car_data per {name1_short}"
    elif df2.empty and not df1.empty:
        note = f" – Nessun dato car_data per {name2_short}"

    # -------- TRACK FIG (pista x-y) --------
    track_fig = go.Figure()
    if not loc1.empty and loc1["x"].notna().any() and loc1["y"].notna().any():
        track_fig.add_trace(
            go.Scatter(
                x=loc1["x"],
                y=loc1["y"],
                mode="lines",
                name=name1,
                line=dict(color=COLOR1),
            )
        )
    if not loc2.empty and loc2["x"].notna().any() and loc2["y"].notna().any():
        track_fig.add_trace(
            go.Scatter(
                x=loc2["x"],
                y=loc2["y"],
                mode="lines",
                name=name2,
                line=dict(color=COLOR2),
            )
        )
    track_fig.update_layout(
        title=f"Tracciato del giro – {name1_short} vs {name2_short}",
        xaxis_title="X (m)",
        yaxis_title="Y (m)",
        template="plotly_white",
        yaxis_scaleanchor="x",  # per non deformare la pista
    )

    # -------- DELTA TIME FIG --------
    progress, delta_t = compute_delta_time(df1, df2, n_points=200)
    delta_fig = go.Figure()
    if progress is not None:
        delta_fig.add_trace(
            go.Scatter(
                x=progress * 100.0,
                y=delta_t,
                mode="lines",
                name=f"{name2_short} – {name1_short}",
                line=dict(color="#2ca02c"),
            )
        )
        delta_fig.update_layout(
            title=f"Delta time {name2_short} – {name1_short} lungo il giro",
            xaxis_title="Progresso giro (%)",
            yaxis_title=f"Delta tempo (s, >0 = {name2_short} più lento)",
            template="plotly_white",
            shapes=[
                dict(
                    type="line",
                    xref="paper",
                    x0=0,
                    x1=1,
                    y0=0,
                    y1=0,
                    line=dict(dash="dash", width=1),
                )
            ],
        )
    else:
        delta_fig.update_layout(
            title="Delta time non disponibile (dati insufficienti)",
            template="plotly_white",
        )

    # -------- SPEED FIG --------
    speed_fig = go.Figure()
    if not df1.empty:
        speed_fig.add_trace(
            go.Scatter(
                x=df1["t_rel_s"],
                y=df1["speed"],
                mode="lines",
                name=name1,
                line=dict(color=COLOR1),
            )
        )
    if not df2.empty:
        speed_fig.add_trace(
            go.Scatter(
                x=df2["t_rel_s"],
                y=df2["speed"],
                mode="lines",
                name=name2,
                line=dict(color=COLOR2),
            )
        )
    speed_fig.update_layout(
        title=f"Velocità vs tempo relativo{title_suffix}{note}",
        xaxis_title="Tempo relativo (s)",
        yaxis_title="Velocità (km/h)",
        template="plotly_white",
    )

    # -------- THROTTLE FIG --------
    throttle_fig = go.Figure()
    if not df1.empty:
        throttle_fig.add_trace(
            go.Scatter(
                x=df1["t_rel_s"],
                y=df1["throttle"],
                mode="lines",
                name=name1,
                line=dict(color=COLOR1),
            )
        )
    if not df2.empty:
        throttle_fig.add_trace(
            go.Scatter(
                x=df2["t_rel_s"],
                y=df2["throttle"],
                mode="lines",
                name=name2,
                line=dict(color=COLOR2),
            )
        )
    throttle_fig.update_layout(
        title=f"Throttle vs tempo relativo{title_suffix}{note}",
        xaxis_title="Tempo relativo (s)",
        yaxis_title="Throttle (%)",
        template="plotly_white",
    )

    # -------- BRAKE FIG --------
    brake_fig = go.Figure()
    if not df1.empty:
        brake_fig.add_trace(
            go.Scatter(
                x=df1["t_rel_s"],
                y=df1["brake"],
                mode="lines",
                name=name1,
                line=dict(color=COLOR1),
            )
        )
    if not df2.empty:
        brake_fig.add_trace(
            go.Scatter(
                x=df2["t_rel_s"],
                y=df2["brake"],
                mode="lines",
                name=name2,
                line=dict(color=COLOR2),
            )
        )
    brake_fig.update_layout(
        title=f"Brake vs tempo relativo{title_suffix}{note}",
        xaxis_title="Tempo relativo (s)",
        yaxis_title="Brake (valore grezzo / pressione)",
        template="plotly_white",
    )

    # -------- GEAR FIG (MARCE) --------
    gear_fig = go.Figure()
    if not df1.empty:
        gear_fig.add_trace(
            go.Scatter(
                x=df1["t_rel_s"],
                y=df1["n_gear"],
                mode="lines",
                name=name1,
                line=dict(color=COLOR1),
            )
        )
    if not df2.empty:
        gear_fig.add_trace(
            go.Scatter(
                x=df2["t_rel_s"],
                y=df2["n_gear"],
                mode="lines",
                name=name2,
                line=dict(color=COLOR2),
            )
        )
    gear_fig.update_layout(
        title=f"Marcia (gear) vs tempo relativo{title_suffix}{note}",
        xaxis_title="Tempo relativo (s)",
        yaxis_title="Marcia inserita",
        template="plotly_white",
    )

    # ritorna nell'ordine dichiarato dagli Output: track, delta, speed, throttle, brake, gear
    return track_fig, speed_fig, delta_fig,  throttle_fig, brake_fig, gear_fig


if __name__ == "__main__":
    app.run(debug=True)
