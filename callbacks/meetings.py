import pandas as pd
from dash import Input, Output, State, callback

from api.openf1 import fetch_laps, fetch_meetings, fetch_sessions
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


def _select_latest_session_with_data(df_sessions: pd.DataFrame, fallback_to_latest: bool = True) -> int | None:
    """Seleziona la sessione più recente che abbia almeno un lap disponibile."""
    if df_sessions.empty or "session_key" not in df_sessions.columns:
        return None

    ordered_sessions = _sort_latest_first(df_sessions)
    fallback_value = None

    for _, row in ordered_sessions.iterrows():
        if pd.isna(row.get("session_key")):
            continue
        session_key = int(row["session_key"])
        if fallback_value is None:
            fallback_value = session_key
        try:
            df_laps = fetch_laps(session_key)
        except Exception:
            continue
        if not df_laps.empty:
            return session_key

    return fallback_value if fallback_to_latest else None


def _select_latest_meeting_with_data(df_meetings: pd.DataFrame) -> int | None:
    """Seleziona il meeting più recente che abbia almeno una sessione con lap disponibili."""
    if df_meetings.empty or "meeting_key" not in df_meetings.columns:
        return None

    ordered_meetings = _sort_latest_first(df_meetings)
    fallback_value = None

    for _, row in ordered_meetings.iterrows():
        if pd.isna(row.get("meeting_key")):
            continue
        meeting_key = int(row["meeting_key"])
        if fallback_value is None:
            fallback_value = meeting_key
        try:
            df_sessions = fetch_sessions(meeting_key)
        except Exception:
            continue
        if _select_latest_session_with_data(df_sessions, fallback_to_latest=False) is not None:
            return meeting_key

    return fallback_value


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
    value = _select_latest_meeting_with_data(ordered_meetings)
    if value is None:
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

    value = _select_latest_session_with_data(ordered_sessions)
    if value is None:
        value = _latest_option_value(options)
    status = t(lang, "sessions_loaded", count=len(options))

    return ordered_sessions.to_dict("records"), options, value, status
