import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, html

from api.openf1 import fetch_stints, fetch_pitstops
from utils.i18n import t, LANG_DEFAULT
from utils.telemetry import lap_duration_seconds_from_row, fmt_duration
from config import COLOR1, COLOR2


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


def _compound_color(compound: str | None) -> str:
    if not compound:
        return "#888888"
    c = compound.upper()
    mapping = {
        "SOFT": "#ff4c4c",
        "MEDIUM": "#f7e35c",
        "HARD": "#f0f0f0",
        "INTERMEDIATE": "#0abf04",
        "INTER": "#0abf04",
        "WET": "#0057e7",
    }
    return mapping.get(c, "#888888")


def _prepare_driver_laps(df_laps: pd.DataFrame, driver_number: int) -> pd.DataFrame:
    """Filtra i giri per driver e calcola il tempo giro in secondi."""
    if df_laps.empty:
        return pd.DataFrame()
    laps = df_laps[df_laps["driver_number"] == driver_number].copy()
    if laps.empty:
        return pd.DataFrame()
    laps["lap_time_s"] = laps.apply(
        lambda r: lap_duration_seconds_from_row(r, pd.DataFrame()),
        axis=1,
    )
    laps = laps.dropna(subset=["lap_time_s", "lap_number"])
    laps["lap_number"] = laps["lap_number"].astype(int)
    laps = laps.sort_values("lap_number")
    return laps


def _attach_compound(laps: pd.DataFrame, stints: pd.DataFrame, driver_number: int) -> pd.DataFrame:
    """Associa il compound ad ogni lap usando i dati stint."""
    if laps.empty or stints.empty:
        laps["compound"] = None
        return laps
    driver_stints = stints[stints["driver_number"] == driver_number]
    if driver_stints.empty:
        laps["compound"] = None
        return laps

    def find_compound(lap_num: int):
        for _, row in driver_stints.iterrows():
            start = row.get("lap_start") or row.get("stint_start") or row.get("lap_start")
            end = row.get("lap_end") or row.get("stint_end") or start
            try:
                start_int = int(start) if pd.notna(start) else None
                end_int = int(end) if pd.notna(end) else start_int
            except Exception:
                continue
            if start_int is None:
                continue
            if end_int is None:
                end_int = start_int
            if start_int <= lap_num <= end_int:
                return row.get("compound")
        return None

    laps["compound"] = laps["lap_number"].apply(find_compound)
    return laps


@callback(
    output=[
        Output("stints-graph", "figure"),
        Output("pitstop-graph", "figure"),
        Output("degradation-graph", "figure"),
        Output("strategy-summary", "children"),
    ],
    inputs=[
        Input("session-dropdown", "value"),
        Input("driver1-dropdown", "value"),
        Input("driver2-dropdown", "value"),
        Input("lang-store", "data"),
    ],
    state=[
        State("laps-store", "data"),
        State("drivers-store", "data"),
    ],
)
def render_strategy(session_key, driver1, driver2, lang, laps_data, drivers_data):
    """Mostra strategia gomme, pit stop e degrado tempi giro."""
    lang = lang or LANG_DEFAULT
    prompt = t(lang, "strategy_prompt")
    if not session_key or not driver1 or not driver2:
        return _empty_fig(prompt), _empty_fig(prompt), _empty_fig(prompt), prompt

    df_laps = pd.DataFrame(laps_data) if laps_data else pd.DataFrame()
    df_drivers = pd.DataFrame(drivers_data) if drivers_data else pd.DataFrame()
    label1 = _driver_label(int(driver1), df_drivers)
    label2 = _driver_label(int(driver2), df_drivers)

    try:
        stints = fetch_stints(int(session_key))
    except Exception:
        stints = pd.DataFrame()
    try:
        pitstops = fetch_pitstops(int(session_key))
    except Exception:
        pitstops = pd.DataFrame()

    # --- Stints timeline ---
    stints_fig = go.Figure()
    stints_filtered = stints[stints["driver_number"].isin([driver1, driver2])] if not stints.empty else pd.DataFrame()
    if stints_filtered.empty:
        stints_fig.update_layout(
            title=t(lang, "stints_none"),
            xaxis_title="Lap",
            template="plotly_white",
        )
    else:
        for drv, color in [(driver1, COLOR1), (driver2, COLOR2)]:
            drv_stints = stints_filtered[stints_filtered["driver_number"] == drv]
            drv_label = label1 if drv == driver1 else label2
            for idx, row in drv_stints.sort_values("stint_number", na_position="last").iterrows():
                start = row.get("lap_start") or row.get("stint_start") or row.get("lap_start")
                end = row.get("lap_end") or row.get("stint_end") or start
                try:
                    start_int = int(start) if pd.notna(start) else None
                    end_int = int(end) if pd.notna(end) else start_int
                except Exception:
                    continue
                if start_int is None:
                    continue
                if end_int is None:
                    end_int = start_int
                width = max(end_int - start_int + 1, 1)
                compound = row.get("compound")
                compound_label = compound if compound else t(lang, "compound_unknown")
                color_fill = _compound_color(compound)
                stint_num = row.get("stint_number") if pd.notna(row.get("stint_number")) else idx + 1
                stints_fig.add_trace(
                    go.Bar(
                        y=[drv_label],
                        x=[width],
                        base=start_int - 1,
                        orientation="h",
                        name=drv_label,
                        marker_color=color_fill,
                        marker_line=dict(color=color, width=1),
                        customdata=[[compound_label, start_int, end_int, stint_num]],
                        hovertemplate=(
                            "Driver %{y}<br>"
                            "Stint %{customdata[3]}<br>"
                            "Lap %{customdata[1]}-%{customdata[2]}<br>"
                            "Compound %{customdata[0]}<extra></extra>"
                        ),
                        showlegend=False,
                    )
                )
        stints_fig.update_layout(
            title=t(lang, "stints_title"),
            xaxis_title="Lap",
            barmode="overlay",
            template="plotly_white",
        )

    # --- Pit stops ---
    pit_fig = go.Figure()
    pit_filtered = pitstops[pitstops["driver_number"].isin([driver1, driver2])] if not pitstops.empty else pd.DataFrame()
    if pit_filtered.empty:
        pit_fig.update_layout(title=t(lang, "pit_none"), template="plotly_white")
    else:
        for drv, color in [(driver1, COLOR1), (driver2, COLOR2)]:
            drv_pits = pit_filtered[pit_filtered["driver_number"] == drv]
            if drv_pits.empty:
                continue
            durations = []
            for _, row in drv_pits.iterrows():
                dur = row.get("pit_duration")
                if dur is None or (isinstance(dur, float) and pd.isna(dur)):
                    dur_ms = row.get("pit_duration_ms")
                    dur = float(dur_ms) / 1000.0 if dur_ms is not None and not pd.isna(dur_ms) else None
                durations.append(dur)
            pit_fig.add_trace(
                go.Scatter(
                    x=drv_pits["lap_number"],
                    y=durations,
                    mode="markers+lines",
                    name=_driver_label(int(drv), df_drivers),
                    marker=dict(color=color, size=10),
                    line=dict(color=color, dash="dot"),
                    hovertemplate="Lap %{x}<br>Durata %{y:.3f} s<extra>%{name}</extra>",
                )
            )
        pit_fig.update_layout(
            title=t(lang, "pit_title"),
            xaxis_title="Lap",
            yaxis_title=t(lang, "pit_y"),
            template="plotly_white",
            shapes=[
                dict(
                    type="line",
                    xref="paper",
                    x0=0,
                    x1=1,
                    y0=0,
                    y1=0,
                    line=dict(color="#555", dash="dash"),
                )
            ],
        )

    # --- Degradation / lap times ---
    deg_fig = go.Figure()
    d1 = _prepare_driver_laps(df_laps, int(driver1))
    d2 = _prepare_driver_laps(df_laps, int(driver2))
    d1 = _attach_compound(d1, stints, int(driver1))
    d2 = _attach_compound(d2, stints, int(driver2))

    if d1.empty and d2.empty:
        deg_fig.update_layout(title=t(lang, "deg_none"), template="plotly_white")
    else:
        for df, drv, color in [(d1, driver1, COLOR1), (d2, driver2, COLOR2)]:
            if df.empty:
                continue
            compounds = df["compound"].fillna("").tolist()
            colors = [_compound_color(c) for c in compounds]
            labels = [c if c else t(lang, "compound_unknown") for c in compounds]
            custom = list(zip(df["lap_time_s"].apply(fmt_duration), labels))
            deg_fig.add_trace(
                go.Scatter(
                    x=df["lap_number"],
                    y=df["lap_time_s"],
                    mode="lines+markers",
                    name=_driver_label(int(drv), df_drivers),
                    line=dict(color=color),
                    marker=dict(color=colors, size=9, line=dict(color="#222", width=0.5)),
                    customdata=custom,
                    hovertemplate="Lap %{x}<br>%{customdata[0]}<br>Compound %{customdata[1]}<extra>%{name}</extra>",
                )
            )
        deg_fig.update_layout(
            title=t(lang, "deg_title"),
            xaxis_title="Lap",
            yaxis_title=t(lang, "times_y"),
            template="plotly_white",
        )

    # --- Summary ---
    def summary_block(drv, label):
        drv_stints = stints_filtered[stints_filtered["driver_number"] == drv] if not stints_filtered.empty else pd.DataFrame()
        count = len(drv_stints)
        last_comp = None
        if not drv_stints.empty:
            last = drv_stints.iloc[-1]
            last_comp = last.get("compound")
        compound_label = last_comp if last_comp else t(lang, "compound_unknown")
        return html.Div(t(lang, "strategy_driver_summary", driver=label, count=count, compound=compound_label))

    summary = [summary_block(driver1, label1), summary_block(driver2, label2)]

    return stints_fig, pit_fig, deg_fig, summary
