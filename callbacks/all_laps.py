import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, html

from utils.telemetry import lap_duration_seconds_from_row, fmt_duration
from utils.i18n import t, LANG_DEFAULT


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


def _driver_label(num: int, df_drivers: pd.DataFrame) -> str:
    """Restituisce un'etichetta leggibile per il pilota."""
    if df_drivers.empty:
        return f"Driver {num}"
    row = df_drivers[df_drivers["driver_number"] == num]
    if row.empty:
        return f"Driver {num}"
    row = row.iloc[0]
    full_name = row.get("full_name") or ""
    acronym = row.get("name_acronym") or ""
    team = row.get("team_name") or ""
    name = full_name or acronym or f"Driver {num}"
    if team:
        return f"{name} ({team})"
    return name


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
        Output("all-laps-heatmap", "figure"),
        Output("all-laps-summary", "children"),
    ],
    inputs=[
        Input("session-dropdown", "value"),
        Input("driver1-dropdown", "value"),
        Input("driver2-dropdown", "value"),
        Input("lap1-dropdown", "value"),
        Input("lap2-dropdown", "value"),
        Input("lang-store", "data"),
    ],
    state=[
        State("laps-store", "data"),
        State("drivers-store", "data"),
    ],
)
def render_all_laps(session_key, driver1, driver2, lap1, lap2, lang, laps_data, drivers_data):
    """Mostra confronto di tutti i giri tra due piloti e una heatmap per il singolo giro selezionato."""
    lang = lang or LANG_DEFAULT
    try:
        if not session_key or not driver1 or not driver2 or not laps_data:
            msg = t(lang, "all_laps_prompt")
            return _empty_fig(msg), _empty_fig(msg), _empty_fig(msg), msg

        df_laps = pd.DataFrame(laps_data)
        df_drivers = pd.DataFrame(drivers_data) if drivers_data else pd.DataFrame()
        label1 = _driver_label(int(driver1), df_drivers)
        label2 = _driver_label(int(driver2), df_drivers)
        d1 = _prepare_driver_laps(df_laps, int(driver1))
        d2 = _prepare_driver_laps(df_laps, int(driver2))

        if d1.empty and d2.empty:
            msg = t(lang, "all_laps_none")
            return _empty_fig(msg), _empty_fig(msg), _empty_fig(msg), msg

        # Grafico tempi giro
        times_fig = go.Figure()
        if not d1.empty:
            times_fig.add_trace(
                go.Scatter(
                    x=d1["lap_number"],
                    y=d1["lap_time_s"],
                    mode="lines+markers",
                    name=label1,
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
                    name=label2,
                    customdata=d2["lap_time_s"].apply(fmt_duration),
                    hovertemplate="Lap %{x}<br>Tempo %{customdata}<extra>%{name}</extra>",
                )
            )
        times_fig.update_layout(
            title=t(lang, "times_title", d1=label1, d2=label2),
            xaxis_title="Lap",
            yaxis_title=t(lang, "times_y"),
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
                delta_fig = _empty_fig(t(lang, "delta_no_common"))
            else:
                merged["delta_s"] = merged["lap_time_s_d2"] - merged["lap_time_s_d1"]
                colors = ["#2ca02c" if val < 0 else "#d62728" for val in merged["delta_s"]]
                delta_fig.add_trace(
                    go.Bar(
                        x=merged["lap_number"],
                        y=merged["delta_s"],
                        marker_color=colors,
                        name=f"Delta ({label2} - {label1})",
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
            delta_fig = _empty_fig(t(lang, "delta_need_drivers"))

        delta_fig.update_layout(
            title=t(lang, "delta_title", d2=label2, d1=label1),
            xaxis_title="Lap",
            yaxis_title=t(lang, "delta_y"),
            template="plotly_white",
        )

        # Heatmap lap times: mostra tutti i giri (asse Y) per entrambi i piloti
        heatmap_fig = go.Figure()
        all_laps_numbers = sorted(set(d1["lap_number"]).union(set(d2["lap_number"])))
        if not all_laps_numbers:
            heatmap_fig = _empty_fig(t(lang, "heatmap_none"))
        else:
            time_x = [label1, label2]
            delta_x = ["Delta (d2 - d1)"]
            cumulative_x = ["Delta cumulativo"]
            time_z = []
            time_text = []
            delta_z = []
            delta_text = []
            cumulative_z = []
            cumulative_text = []
            cumulative_sum = 0.0
            for lap in all_laps_numbers:
                d1_val_series = d1[d1["lap_number"] == lap]["lap_time_s"]
                d2_val_series = d2[d2["lap_number"] == lap]["lap_time_s"]
                v1 = d1_val_series.iloc[0] if not d1_val_series.empty else None
                v2 = d2_val_series.iloc[0] if not d2_val_series.empty else None
                delta = (v2 - v1) if (v1 is not None and v2 is not None) else None

                row_vals = [v1 if pd.notna(v1) else None, v2 if pd.notna(v2) else None]
                valid_times = [v for v in row_vals if v is not None]
                best = min(valid_times) if valid_times else None

                row_time_text = []
                for v in row_vals:
                    if v is None:
                        row_time_text.append("")
                        continue
                    label = fmt_duration(v)
                    if best is not None and abs(v - best) < 1e-6:
                        label = f"<b>{label}</b>"
                    row_time_text.append(label)

                time_z.append(row_vals)
                time_text.append(row_time_text)

                delta_z.append([delta if pd.notna(delta) else None])
                if delta is None:
                    delta_text.append([""])
                else:
                    sign = "+" if delta >= 0 else "-"
                    delta_text.append([f"{sign}{fmt_duration(abs(delta))}"])

                if delta is None:
                    cumulative_z.append([None])
                    cumulative_text.append([""])
                else:
                    cumulative_sum += delta
                    cumulative_z.append([cumulative_sum])
                    sign_cum = "+" if cumulative_sum >= 0 else "-"
                    cumulative_text.append([f"{sign_cum}{fmt_duration(abs(cumulative_sum))}"])

            has_values = any(val is not None for row in time_z for val in row)
            if has_values:
                heatmap_fig.add_trace(
                    go.Heatmap(
                        z=time_z,
                        x=time_x,
                        y=all_laps_numbers,
                        text=time_text,
                        texttemplate="%{text}",
                        colorscale="RdYlGn_r",
                        colorbar_title="Tempo (s)",
                        hovertemplate="Lap %{y}<br>Driver %{x}<br>Tempo %{text}<extra></extra>",
                        zmin=min(val for row in time_z for val in row if val is not None),
                        zmax=max(val for row in time_z for val in row if val is not None),
                    )
                )
                heatmap_fig.add_trace(
                    go.Heatmap(
                        z=delta_z,
                        x=delta_x,
                        y=all_laps_numbers,
                        text=delta_text,
                        texttemplate="%{text}",
                        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                        showscale=False,
                        hovertemplate="Lap %{y}<br>Delta %{text}<extra></extra>",
                    )
                )
                heatmap_fig.add_trace(
                    go.Heatmap(
                        z=cumulative_z,
                        x=cumulative_x,
                        y=all_laps_numbers,
                        text=cumulative_text,
                        texttemplate="%{text}",
                        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                        showscale=False,
                        hovertemplate="Lap %{y}<br>Delta cumulativo %{text}<extra></extra>",
                    )
                )
                heatmap_fig.update_traces(textfont={"size": 14})
                heatmap_fig.update_layout(
                    title=t(lang, "heatmap_title"),
                    xaxis_title=t(lang, "heatmap_x"),
                    yaxis_title=t(lang, "heatmap_y"),
                    template="plotly_white",
                    height=1040,
                    autosize=True,
                    xaxis=dict(side="top"),
                    yaxis=dict(autorange="reversed"),
                    margin=dict(l=40, r=20, t=80, b=40),
                )
            else:
                heatmap_fig = _empty_fig(t(lang, "heatmap_nodata"))

        # Sintesi testuale
        def stats_block(df: pd.DataFrame, label: str):
            if df.empty:
                return t(lang, "summary_none", driver=label)
            best = df.loc[df["lap_time_s"].idxmin()]
            return t(
                lang,
                "summary_stats",
                driver=label,
                count=len(df),
                best_lap=int(best["lap_number"]),
                best_time=fmt_duration(best["lap_time_s"]),
                avg=fmt_duration(df["lap_time_s"].mean()),
            )

        summary_text = [
            html.Div(stats_block(d1, label1)),
            html.Div(stats_block(d2, label2)),
        ]

        return times_fig, delta_fig, heatmap_fig, summary_text

    except Exception as e:
        msg = t(lang, "error_generic", error=e)
        return _empty_fig(msg), _empty_fig(msg), _empty_fig(msg), msg
