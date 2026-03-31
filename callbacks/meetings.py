import pandas as pd
from dash import Input, Output, State, callback

from api.openf1 import fetch_meetings, fetch_sessions
from utils.i18n import t, LANG_DEFAULT

_DATE_COLUMNS = (
    "date_end",
    "session_end_date",
    "date_start",
    "session_start_date",
    "meeting_end_date",
    "meeting_start_date",
)


def _sort_latest_first(df: pd.DataFrame) -> pd.DataFrame:
    """Ordina dal più recente al meno recente usando le date disponibili."""
    if df.empty:
        return df

    sortable = df.copy()
    sort_cols = []
    for col in _DATE_COLUMNS:
        if col in sortable.columns:
            parsed_col = f"__sort_{col}"
            sortable[parsed_col] = pd.to_datetime(sortable[col], errors="coerce", utc=True)
            if sortable[parsed_col].notna().any():
                sort_cols.append(parsed_col)

    if sort_cols:
        return sortable.sort_values(sort_cols, ascending=[False] * len(sort_cols), na_position="last")

    for fallback_col in ("meeting_key", "session_key"):
        if fallback_col in sortable.columns:
            return sortable.sort_values(fallback_col, ascending=False, na_position="last")

    return sortable.iloc[::-1]


def _latest_option_value(options: list[dict]) -> int | None:
    return options[0]["value"] if options else None


@callback(
    output=[
        Output("meetings-store", "data"),
        Output("meeting-dropdown", "options"),
        Output("meeting-dropdown", "value"),
        Output("meetings-status", "children"),
    ],
    inputs=[Input("year-input", "value"), Input("lang-store", "data")],
)
def load_meetings(year, lang):
    lang = lang or LANG_DEFAULT
    try:
        df = fetch_meetings(year=int(year)) if year else fetch_meetings()
    except Exception as e:
        return None, [], None, t(lang, "meetings_error", error=e)

    if df.empty:
        return None, [], None, t(lang, "meetings_none")

    ordered_meetings = _sort_latest_first(df)

    def make_label(row):
        y = row.get("year")
        name = row.get("meeting_name") or "Unknown"
        country = row.get("country_name") or ""
        return f"{y} - {name} ({country})" if country else f"{y} - {name}"

    options = [
        {"label": make_label(row), "value": int(row["meeting_key"])}
        for _, row in ordered_meetings.iterrows()
        if pd.notna(row["meeting_key"])
    ]
    value = _latest_option_value(options)
    status = t(lang, "meetings_loaded", count=len(options))

    return ordered_meetings.to_dict("records"), options, value, status


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

    ordered_sessions = _sort_latest_first(df_sessions)
    options = [
        {
            "label": f"{row.get('session_name') or row.get('session_type') or 'Session'} "
                     f"(key={int(row['session_key'])})",
            "value": int(row["session_key"]),
        }
        for _, row in ordered_sessions.iterrows()
        if pd.notna(row["session_key"])
    ]

    value = _latest_option_value(options)
    status = t(lang, "sessions_loaded", count=len(options))

    return ordered_sessions.to_dict("records"), options, value, status
