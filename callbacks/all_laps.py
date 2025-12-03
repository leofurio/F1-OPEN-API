import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, html

from utils.telemetry import lap_duration_seconds_from_row, fmt_duration


def _prepare_driver_laps(df_laps: pd.DataFrame, driver_number: int) -> pd.DataFrame:
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


def _empty_fig(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        template="plotly_white",
    )
    return fig


@callback(
    output=[
        Output("all-laps-times-graph", "figure"),
        Output("all-laps-delta-graph", "figure"),
        Output("all-laps-summary", "children"),
    ],
    inputs=[
        Input("session-dropdown", "value"),
        Input("driver1-dropdown", "value"),
        Input("driver2-dropdown", "value"),
    ],
    state=[State("laps-store", "data")],
)
def render_all_laps(session_key, driver1, driver2, laps_data):
    """Mostra confronto di tutti i giri tra due piloti della stessa sessione."""
    try:
        if not session_key or not driver1 or not driver2 or not laps_data:
            msg = "Seleziona sessione e due piloti per confrontare tutti i giri."
            return _empty_fig(msg), _empty_fig(msg), msg

        df_laps = pd.DataFrame(laps_data)
        d1 = _prepare_driver_laps(df_laps, int(driver1))
        d2 = _prepare_driver_laps(df_laps, int(driver2))

        if d1.empty and d2.empty:
            msg = "Nessun giro disponibile per i piloti selezionati."
            return _empty_fig(msg), _empty_fig(msg), msg

        # Grafico tempi giro
        times_fig = go.Figure()
        if not d1.empty:
            times_fig.add_trace(
                go.Scatter(
                    x=d1["lap_number"],
                    y=d1["lap_time_s"],
                    mode="lines+markers",
                    name=f"Driver {driver1}",
                    customdata=d1["lap_time_s"].apply(fmt_duration),
                    hovertemplate="Lap %{x}<br>Tempo %{customdata}<extra>%{name}</extra>",
                )
            )
        if not d2.empty:
            times_fig.add_trace(
                go.Scatter(
                    x=d2["lap_number"],
                    y=d2["lap_time_s"],
                    mode="lines+markers",
                    name=f"Driver {driver2}",
                    customdata=d2["lap_time_s"].apply(fmt_duration),
                    hovertemplate="Lap %{x}<br>Tempo %{customdata}<extra>%{name}</extra>",
                )
            )
        times_fig.update_layout(
            title=f"Tempi giro - Driver {driver1} vs Driver {driver2}",
            xaxis_title="Lap",
            yaxis_title="Tempo giro (s)",
            template="plotly_white",
        )

        # Grafico delta (d2 - d1)
        delta_fig = go.Figure()
        if not d1.empty and not d2.empty:
            merged = d1[["lap_number", "lap_time_s"]].merge(
                d2[["lap_number", "lap_time_s"]],
                on="lap_number",
                suffixes=("_d1", "_d2"),
            )
            if merged.empty:
                delta_fig = _empty_fig("Nessun lap in comune per calcolare il delta.")
            else:
                merged["delta_s"] = merged["lap_time_s_d2"] - merged["lap_time_s_d1"]
                colors = ["#2ca02c" if val < 0 else "#d62728" for val in merged["delta_s"]]
                delta_fig.add_trace(
                    go.Bar(
                        x=merged["lap_number"],
                        y=merged["delta_s"],
                        marker_color=colors,
                        name=f"Delta (Driver {driver2} - Driver {driver1})",
                        hovertemplate="Lap %{x}<br>Delta %{y:.3f} s<extra></extra>",
                    )
                )
                delta_fig.update_layout(
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
                    ]
                )
        else:
            delta_fig = _empty_fig("Seleziona due piloti con giri disponibili per il delta.")

        delta_fig.update_layout(
            title=f"Delta tempo per giro (Driver {driver2} - Driver {driver1})",
            xaxis_title="Lap",
            yaxis_title="Delta (s, negativo = Driver 2 piu veloce)",
            template="plotly_white",
        )

        # Sintesi testuale
        def stats_block(df: pd.DataFrame, label: str):
            if df.empty:
                return f"{label}: nessun giro valido."
            best = df.loc[df["lap_time_s"].idxmin()]
            return (
                f"{label}: giri validi {len(df)}, "
                f"miglior lap {int(best['lap_number'])} ({fmt_duration(best['lap_time_s'])}), "
                f"media {fmt_duration(df['lap_time_s'].mean())}"
            )

        summary_text = [
            html.Div(stats_block(d1, f"Driver {driver1}")),
            html.Div(stats_block(d2, f"Driver {driver2}")),
        ]

        return times_fig, delta_fig, summary_text

    except Exception as e:
        msg = f"Errore: {e}"
        return _empty_fig(msg), _empty_fig(msg), msg
