import pandas as pd
from dash import Input, Output, State, callback

from api.openf1 import fetch_laps, fetch_drivers
from utils.telemetry import fmt_duration, lap_duration_seconds_from_row
from utils.i18n import t, LANG_DEFAULT


@callback(
    output=[
        Output("laps-store", "data"),
        Output("driver1-dropdown", "options"),
        Output("driver1-dropdown", "value"),
        Output("driver2-dropdown", "options"),
        Output("driver2-dropdown", "value"),
        Output("laps-status", "children"),
        Output("drivers-store", "data"),
    ],
    inputs=[Input("session-dropdown", "value"), Input("lang-store", "data")],
)
def load_laps_and_drivers(session_key, lang):
    lang = lang or LANG_DEFAULT
    if not session_key:
        return None, [], None, [], None, t(lang, "status_select_session"), None

    try:
        df_laps = fetch_laps(int(session_key))
    except Exception as e:
        return None, [], None, [], None, t(lang, "error_generic", error=e), None

    if df_laps.empty:
        return None, [], None, [], None, t(lang, "status_no_laps"), None

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
                    return f"#{int(num)} - {full_name} ({team})"
                if full_name:
                    return f"#{int(num)} - {full_name}"
        return f"Driver #{int(num)}"

    driver_options = [
        {"label": driver_label(int(d)), "value": int(d)} for d in driver_numbers
    ]

    d1 = driver_numbers[0] if len(driver_numbers) > 0 else None
    d2 = driver_numbers[1] if len(driver_numbers) > 1 else None

    status = t(
        lang,
        "status_laps_summary",
        laps=len(df_laps),
        drivers=len(driver_numbers),
        max_lap=int(df_laps["lap_number"].max()),
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


@callback(
    output=[Output("lap1-dropdown", "options"), Output("lap1-dropdown", "value")],
    inputs=[Input("driver1-dropdown", "value")],
    state=[State("laps-store", "data")],
)
def update_lap1_dropdown(driver1, laps_data):
    if not laps_data:
        return [], None

    df_laps = pd.DataFrame(laps_data)
    lap_options, lap_value = _build_lap_options(df_laps, driver1)
    return lap_options, lap_value


@callback(
    output=[Output("lap2-dropdown", "options"), Output("lap2-dropdown", "value")],
    inputs=[Input("driver2-dropdown", "value")],
    state=[State("laps-store", "data")],
)
def update_lap2_dropdown(driver2, laps_data):
    if not laps_data:
        return [], None

    df_laps = pd.DataFrame(laps_data)
    lap_options, lap_value = _build_lap_options(df_laps, driver2)
    return lap_options, lap_value


def _build_lap_options(df_laps: pd.DataFrame, driver):
    """Crea le opzioni dei giri per il driver indicato, evidenziando il migliore."""
    if not driver:
        return [], None
    rows = df_laps[df_laps["driver_number"] == int(driver)].dropna(subset=["lap_number"]).copy()
    if rows.empty:
        return [], None

    rows["dur_s"] = rows.apply(
        lambda r: lap_duration_seconds_from_row(r, pd.DataFrame()),
        axis=1,
    )
    best_lap_num = None
    valid = rows.dropna(subset=["dur_s"])
    if not valid.empty:
        best_lap_num = int(valid.loc[valid["dur_s"].idxmin()]["lap_number"])

    opts = []
    for _, r in rows.sort_values("lap_number").iterrows():
        lap_num = int(r["lap_number"])
        dur_s = r.get("dur_s")
        dur_label = fmt_duration(dur_s)
        suffix = " (migliore)" if best_lap_num is not None and lap_num == best_lap_num else ""
        label = f"Lap {lap_num} — {dur_label}{suffix}"
        opts.append({"label": label, "value": lap_num})
    # Preseleziona il secondo giro disponibile se esiste, altrimenti il primo
    if len(opts) >= 2:
        val = opts[1]["value"]
    else:
        val = opts[0]["value"] if opts else None
    return opts, val


@callback(
    Output("lap-compare-status", "children"),
    inputs=[
        Input("driver1-dropdown", "value"),
        Input("lap1-dropdown", "value"),
        Input("driver2-dropdown", "value"),
        Input("lap2-dropdown", "value"),
        Input("lang-store", "data"),
    ],
    state=[
        State("laps-store", "data"),
        State("drivers-store", "data"),
    ],
)
def show_fastest_lap(driver1, lap1, driver2, lap2, lang, laps_data, drivers_data):
    """Mostra quale giro selezionato e piu veloce tra i due piloti."""
    lang = lang or LANG_DEFAULT
    if not laps_data:
        return ""

    if not driver1 or not driver2 or not lap1 or not lap2:
        return t(lang, "laps_select_two")

    df_laps = pd.DataFrame(laps_data)
    df_drivers = pd.DataFrame(drivers_data) if drivers_data else pd.DataFrame()

    def driver_name(num: int) -> str:
        if df_drivers.empty:
            return f"Driver #{int(num)}"
        row = df_drivers[df_drivers["driver_number"] == num]
        if row.empty:
            return f"Driver #{int(num)}"
        row = row.iloc[0]
        full_name = row.get("full_name") or row.get("name_acronym") or ""
        team = row.get("team_name") or ""
        if full_name and team:
            return f"#{int(num)} - {full_name} ({team})"
        if full_name:
            return f"#{int(num)} - {full_name}"
        return f"Driver #{int(num)}"

    def pick_row(driver_num, lap_num):
        rows = df_laps[
            (df_laps["driver_number"] == int(driver_num))
            & (df_laps["lap_number"] == int(lap_num))
        ]
        return rows.iloc[0] if not rows.empty else None

    lap1_row = pick_row(driver1, lap1)
    lap2_row = pick_row(driver2, lap2)
    if lap1_row is None or lap2_row is None:
        return t(lang, "lap_unavailable")

    dur1_s = lap_duration_seconds_from_row(lap1_row, pd.DataFrame())
    dur2_s = lap_duration_seconds_from_row(lap2_row, pd.DataFrame())
    if pd.isna(dur1_s) or pd.isna(dur2_s):
        return t(lang, "lap_unavailable")

    label1 = f"{driver_name(int(driver1))} - Lap {lap1}"
    label2 = f"{driver_name(int(driver2))} - Lap {lap2}"

    delta = abs(dur1_s - dur2_s)
    delta_str = fmt_duration(delta)

    if abs(dur1_s - dur2_s) < 1e-3:
        return t(lang, "lap_fast_equal", lap1=label1, lap2=label2, time=fmt_duration(dur1_s))

    if dur1_s < dur2_s:
        return f"{t(lang, 'lap_fast_winner', winner=label1, time=fmt_duration(dur1_s))}, {t(lang, 'lap_fast_advantage', delta=delta_str, other=label2)}"

    return f"{t(lang, 'lap_fast_winner', winner=label2, time=fmt_duration(dur2_s))}, {t(lang, 'lap_fast_advantage', delta=delta_str, other=label1)}"
