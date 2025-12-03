import pandas as pd
from dash import Input, Output, State, callback

from api.openf1 import fetch_meetings, fetch_sessions
from utils.i18n import t, LANG_DEFAULT


@callback(
    output=[
        Output("meetings-store", "data"),
        Output("meeting-dropdown", "options"),
        Output("meeting-dropdown", "value"),
        Output("meetings-status", "children"),
    ],
    inputs=[Input("load-meetings-btn", "n_clicks"), Input("lang-store", "data")],
    state=[State("year-input", "value")],
)
def load_meetings(n_clicks, lang, year):
    lang = lang or LANG_DEFAULT
    try:
        df = fetch_meetings(year=int(year)) if year else fetch_meetings()
    except Exception as e:
        return None, [], None, t(lang, "meetings_error", error=e)

    if df.empty:
        return None, [], None, t(lang, "meetings_none")

    def make_label(row):
        y = row.get("year")
        name = row.get("meeting_name") or "Unknown"
        country = row.get("country_name") or ""
        return f"{y} - {name} ({country})" if country else f"{y} - {name}"

    options = [
        {"label": make_label(row), "value": int(row["meeting_key"])}
        for _, row in df.iterrows()
        if pd.notna(row["meeting_key"])
    ]
    value = options[-1]["value"] if options else None
    status = t(lang, "meetings_loaded", count=len(options))

    return df.to_dict("records"), options, value, status


@callback(
    output=[
        Output("sessions-store", "data"),
        Output("session-dropdown", "options"),
        Output("session-dropdown", "value"),
        Output("sessions-status", "children"),
    ],
    inputs=[Input("meeting-dropdown", "value"), Input("lang-store", "data")],
    state=[State("meetings-store", "data")],
)
def load_sessions(meeting_key, lang, meetings_data):
    lang = lang or LANG_DEFAULT
    if not meeting_key:
        return None, [], None, t(lang, "sessions_select_meeting")

    try:
        df_sessions = fetch_sessions(int(meeting_key))
    except Exception as e:
        return None, [], None, t(lang, "sessions_error", error=e)

    if df_sessions.empty:
        return None, [], None, t(lang, "sessions_none")

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
    status = t(lang, "sessions_loaded", count=len(options))

    return df_sessions.to_dict("records"), options, value, status
