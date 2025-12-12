import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback

from utils.i18n import t, LANG_DEFAULT
from utils.telemetry import lap_duration_seconds_from_row


def _empty_fig(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(title=title, template="plotly_white")
    return fig


def _driver_label(num: int, df_drivers: pd.DataFrame) -> str:
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


def _get_position(row: pd.Series):
    for key in ["position", "position_display", "track_position", "position_order"]:
        if key in row and pd.notna(row[key]):
            return row[key]
    return None


@callback(
    Output("ranking-graph", "figure"),
    inputs=[
        Input("session-dropdown", "value"),
        Input("lang-store", "data"),
        Input("laps-store", "data"),
        Input("drivers-store", "data"),
    ],
)
def render_ranking(session_key, lang, laps_data, drivers_data):
    lang = lang or LANG_DEFAULT
    prompt = t(lang, "ranking_prompt")
    if not session_key or not laps_data:
        return _empty_fig(prompt)

    df_laps = pd.DataFrame(laps_data)
    df_drivers = pd.DataFrame(drivers_data) if drivers_data else pd.DataFrame()

    if df_laps.empty or "lap_number" not in df_laps or "driver_number" not in df_laps:
        return _empty_fig(prompt)

    df_laps["position_val"] = df_laps.apply(_get_position, axis=1)

    df_laps["lap_number"] = df_laps["lap_number"].astype(int)
    df_laps = df_laps.sort_values(["lap_number"])

    has_positions = df_laps["position_val"].notna().any()

    if not has_positions:
        # fallback: stima posizione usando i tempi giro cumulati
        df_laps["lap_time_s"] = df_laps.apply(
            lambda r: lap_duration_seconds_from_row(r, pd.DataFrame()),
            axis=1,
        )
        df_laps = df_laps.dropna(subset=["lap_time_s"])
        if df_laps.empty:
            return _empty_fig(t(lang, "ranking_no_position"))

        df_laps = df_laps.sort_values(["driver_number", "lap_number"])
        df_laps["cum_time"] = df_laps.groupby("driver_number")["lap_time_s"].cumsum()

        positions = []
        for lap_num, group in df_laps.groupby("lap_number"):
            group = group.sort_values("cum_time")
            group["computed_pos"] = range(1, len(group) + 1)
            positions.append(group)
        df_laps = pd.concat(positions, ignore_index=True)
        df_laps["position_val"] = df_laps["computed_pos"]

    df_laps = df_laps.dropna(subset=["position_val"])
    if df_laps.empty:
        return _empty_fig(t(lang, "ranking_no_position"))

    drivers = sorted(df_laps["driver_number"].dropna().unique())

    # Palette Plotly qualitative (12 colori) riciclata
    palette = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b",
        "#e377c2", "#7f7f7f", "#bcbd22", "#17becf", "#393b79", "#637939",
    ]

    fig = go.Figure()
    for idx, drv in enumerate(drivers):
        drv_rows = df_laps[df_laps["driver_number"] == drv].sort_values("lap_number")
        if drv_rows.empty:
            continue
        label = _driver_label(int(drv), df_drivers)
        custom = list(zip([int(drv)] * len(drv_rows), [label] * len(drv_rows)))
        fig.add_trace(
            go.Scatter(
                x=drv_rows["lap_number"],
                y=drv_rows["position_val"],
                mode="lines+markers",
                name=label,
                line=dict(color=palette[idx % len(palette)], width=2),
                marker=dict(size=6),
                customdata=custom,
                hovertemplate="#%{customdata[0]} %{customdata[1]}<br>Lap %{x}<br>Pos %{y}<extra></extra>",
            )
        )

    max_pos = int(df_laps["position_val"].max()) if not df_laps["position_val"].empty else None
    fig.update_layout(
        title=t(lang, "ranking_title"),
        xaxis_title="Lap",
        yaxis_title="Pos",
        template="plotly_white",
        yaxis=dict(autorange="reversed", range=[max_pos + 0.5 if max_pos else None, 0.5]),
        legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=60, r=20, t=80, b=60),
    )
    return fig
