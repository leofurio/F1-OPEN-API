import pandas as pd
from dash import Input, Output, State, callback
from api.openf1 import fetch_meetings, fetch_sessions


@callback(
    output=[
        Output("meetings-store", "data"),
        Output("meeting-dropdown", "options"),
        Output("meeting-dropdown", "value"),
        Output("meetings-status", "children"),
    ],
    inputs=[Input("load-meetings-btn", "n_clicks")],
    state=[State("year-input", "value")],
)
def load_meetings(n_clicks, year):
    try:
        df = fetch_meetings(year=int(year)) if year else fetch_meetings()
    except Exception as e:
        return None, [], None, f"❌ Errore: {e}"

    if df.empty:
        return None, [], None, "⚠ Nessun circuito trovato."

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


@callback(
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
        return None, [], None, f"❌ Errore: {e}"

    if df_sessions.empty:
        return None, [], None, "⚠ Nessuna sessione trovata."

    options = [
        {
            "label": f"{row.get('session_name') or row.get('session_type') or 'Session'} "
                     f"(key={int(row['session_key'])})",
            "value": int(row["session_key"]),
        }
        for _, row in df_sessions.iterrows()
        if pd.notna(row["session_key"])
    ]

    value = options[-1]["value"] if options else None
    status = f"✅ Sessioni caricate: {len(options)}"

    return df_sessions.to_dict("records"), options, value, status
