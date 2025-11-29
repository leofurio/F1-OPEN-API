import pandas as pd
from dash import Input, Output, State, callback
from api.openf1 import fetch_laps, fetch_drivers


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
    inputs=[Input("session-dropdown", "value")],
)
def load_laps_and_drivers(session_key):
    if not session_key:
        return None, [], None, [], None, "Seleziona una sessione.", None

    try:
        df_laps = fetch_laps(int(session_key))
    except Exception as e:
        return None, [], None, [], None, f"❌ Errore: {e}", None

    if df_laps.empty:
        return None, [], None, [], None, "⚠ Nessun giro trovato.", None

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
        f"✅ Laps: {len(df_laps)} | Drivers: {len(driver_numbers)} | "
        f"Max lap: {int(df_laps['lap_number'].max())}"
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

    laps1 = sorted(
        df_laps[df_laps["driver_number"] == driver1]["lap_number"].dropna().unique()
    ) if driver1 else []
    lap1_options = [{"label": f"Lap {int(l)}", "value": int(l)} for l in laps1]
    lap1_val = int(laps1[-1]) if laps1 else None

    laps2 = sorted(
        df_laps[df_laps["driver_number"] == driver2]["lap_number"].dropna().unique()
    ) if driver2 else []
    lap2_options = [{"label": f"Lap {int(l)}", "value": int(l)} for l in laps2]
    lap2_val = int(laps2[-1]) if laps2 else None

    return lap1_options, lap1_val, lap2_options, lap2_val