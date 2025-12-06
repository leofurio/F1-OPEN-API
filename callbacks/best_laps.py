import pandas as pd
from dash import Input, Output, callback, html

from utils.telemetry import lap_duration_seconds_from_row, fmt_duration, parse_time_str
from utils.i18n import t, LANG_DEFAULT


def _driver_label(num: int, df_drivers: pd.DataFrame) -> str:
    """Restituisce una label leggibile per il pilota."""
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


def _build_table(rows: list[str | html.Tr], lang: str):
    """Costruisce la tabella HTML con intestazioni tradotte."""
    header_cell_style = {"borderBottom": "2px solid #ccc", "padding": "8px 10px", "textAlign": "left"}
    header = html.Thead(
        html.Tr(
            [
                html.Th(t(lang, "best_laps_driver"), style=header_cell_style),
                html.Th(t(lang, "best_laps_lap"), style=header_cell_style),
                html.Th(t(lang, "best_laps_time"), style=header_cell_style),
                html.Th(t(lang, "best_laps_s1"), style=header_cell_style),
                html.Th(t(lang, "best_laps_s2"), style=header_cell_style),
                html.Th(t(lang, "best_laps_s3"), style=header_cell_style),
                html.Th(t(lang, "best_laps_gap"), style=header_cell_style),
            ]
        )
    )
    body = html.Tbody(rows)
    return html.Table(
        [header, body],
        style={
            "borderCollapse": "collapse",
            "width": "100%",
        },
    )

SECTOR_KEYS = [
    "duration_sector_1",
    "duration_sector_2",
    "duration_sector_3",
]


@callback(
    Output("best-laps-table", "children"),
    inputs=[
        Input("session-dropdown", "value"),
        Input("lang-store", "data"),
        Input("laps-store", "data"),
        Input("drivers-store", "data"),
    ],
)
def render_best_laps(session_key, lang, laps_data, drivers_data):
    """Mostra una tabella con il miglior giro per ogni pilota della sessione."""
    lang = lang or LANG_DEFAULT

    if not session_key:
        return t(lang, "best_laps_prompt")
    if not laps_data:
        return t(lang, "best_laps_none")

    df_laps = pd.DataFrame(laps_data)
    df_drivers = pd.DataFrame(drivers_data) if drivers_data else pd.DataFrame()

    if df_laps.empty:
        return t(lang, "best_laps_none")

    df_laps = df_laps.copy()
    df_laps["lap_time_s"] = df_laps.apply(
        lambda r: lap_duration_seconds_from_row(r, pd.DataFrame()),
        axis=1,
    )
    df_laps = df_laps.dropna(subset=["lap_time_s", "lap_number", "driver_number"])
    if df_laps.empty:
        return t(lang, "best_laps_none")

    best_rows = []
    for driver_number, group in df_laps.groupby("driver_number"):
        group_sorted = group.sort_values("lap_time_s")
        best_row = group_sorted.iloc[0]

        def _sector_value(row, key):
            val = row.get(key)
            parsed = parse_time_str(val) if val is not None else None
            return float(parsed) if parsed is not None else None

        s1 = _sector_value(best_row, SECTOR_KEYS[0])
        s2 = _sector_value(best_row, SECTOR_KEYS[1])
        s3 = _sector_value(best_row, SECTOR_KEYS[2])

        best_rows.append(
            {
                "driver_number": int(driver_number),
                "lap_number": int(best_row["lap_number"]),
                "lap_time_s": float(best_row["lap_time_s"]),
                "s1": s1,
                "s2": s2,
                "s3": s3,
            }
        )

    if not best_rows:
        return t(lang, "best_laps_none")

    best_df = pd.DataFrame(best_rows).sort_values("lap_time_s")
    session_best = best_df["lap_time_s"].min()
    best_s1 = best_df["s1"].min() if "s1" in best_df and best_df["s1"].notna().any() else None
    best_s2 = best_df["s2"].min() if "s2" in best_df and best_df["s2"].notna().any() else None
    best_s3 = best_df["s3"].min() if "s3" in best_df and best_df["s3"].notna().any() else None

    def _format_sector(val, best_val):
        if val is None or pd.isna(val):
            return "N/A"
        text = fmt_duration(val)
        if best_val is not None and abs(val - best_val) < 1e-6:
            return html.B(text)
        return text

    table_rows = []
    for _, row in best_df.iterrows():
        gap = row["lap_time_s"] - session_best
        gap_str = "+" + fmt_duration(gap) if gap > 1e-6 else t(lang, "best_laps_fastest")
        cell_style = {"padding": "8px 10px"}
        table_rows.append(
            html.Tr(
                [
                    html.Td(_driver_label(int(row["driver_number"]), df_drivers), style=cell_style),
                    html.Td(int(row["lap_number"]), style=cell_style),
                    html.Td(fmt_duration(row["lap_time_s"]), style=cell_style),
                    html.Td(_format_sector(row.get("s1"), best_s1), style=cell_style),
                    html.Td(_format_sector(row.get("s2"), best_s2), style=cell_style),
                    html.Td(_format_sector(row.get("s3"), best_s3), style=cell_style),
                    html.Td(gap_str, style=cell_style),
                ],
                style={"borderTop": "1px solid #ddd"},
            )
        )

    return _build_table(table_rows, lang)
