"""Funzioni di utilità condivise tra i callback."""

import pandas as pd
import plotly.graph_objects as go

from utils.telemetry import lap_duration_seconds_from_row


def driver_label(num: int, df_drivers: pd.DataFrame) -> str:
    """Restituisce un'etichetta leggibile per il pilota."""
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


def empty_fig(title: str) -> go.Figure:
    """Restituisce un grafico Plotly vuoto con titolo e tema standard."""
    fig = go.Figure()
    fig.update_layout(title=title, template="f1dark")
    return fig


def prepare_driver_laps(df_laps: pd.DataFrame, driver_number: int) -> pd.DataFrame:
    """Filtra e arricchisce i giri per un pilota con il tempo giro in secondi."""
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
