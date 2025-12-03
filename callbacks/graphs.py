import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, callback_context, no_update

from api.openf1 import fetch_car_data_for_lap, fetch_location_for_lap
from utils.telemetry import (
    compute_delta_time,
    lap_duration_seconds_from_row,
    fmt_duration,
)
from config import COLOR1, COLOR2
from utils.i18n import t, LANG_DEFAULT


def driver_label(num: int, df_drivers: pd.DataFrame) -> str:
    """Format a readable label for a driver."""
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


@callback(
    output=[
        Output("track-graph", "figure"),
        Output("delta-graph", "figure"),
        Output("speed-graph", "figure"),
        Output("speed-heatmap", "figure"),
        Output("throttle-graph", "figure"),
        Output("brake-graph", "figure"),
        Output("gear-graph", "figure"),
    ],
    inputs=[
        Input("session-dropdown", "value"),
        Input("driver1-dropdown", "value"),
        Input("lap1-dropdown", "value"),
        Input("driver2-dropdown", "value"),
        Input("lap2-dropdown", "value"),
        Input("selected-time-store", "data"),
        Input("lang-store", "data"),
    ],
    state=[
        State("laps-store", "data"),
        State("drivers-store", "data"),
    ],
    prevent_initial_call=False,
)
def update_graphs(session_key, driver1, lap1_number, driver2, lap2_number, selected_time,
                  lang, laps_data, drivers_data):
    """Aggiorna tutti i 6 grafici."""
    lang = lang or LANG_DEFAULT

    empty_fig = go.Figure()
    empty_fig.update_layout(
        title=t(lang, "graphs_select"),
        xaxis_title=t(lang, "telemetry_x"),
        yaxis_title="",
        template="plotly_white",
    )

    track_fig = go.Figure()
    track_fig.update_layout(
        title=t(lang, "track_unavailable"),
        xaxis_title="X (m)",
        yaxis_title="Y (m)",
        template="plotly_white",
    )

    delta_fig = go.Figure()
    delta_fig.update_layout(
        title=t(lang, "delta_unavailable"),
        xaxis_title=t(lang, "progress_x"),
        yaxis_title=t(lang, "delta_y_time"),
        template="plotly_white",
    )

    if not laps_data or not session_key or not driver1 or not driver2 or not lap1_number or not lap2_number:
        return track_fig, delta_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

    df_laps = pd.DataFrame(laps_data)
    df_drivers = pd.DataFrame(drivers_data) if drivers_data else pd.DataFrame()

    lap1_rows = df_laps[
        (df_laps["driver_number"] == driver1) & (df_laps["lap_number"] == lap1_number)
    ]
    lap2_rows = df_laps[
        (df_laps["driver_number"] == driver2) & (df_laps["lap_number"] == lap2_number)
    ]

    if lap1_rows.empty or lap2_rows.empty:
        empty_fig.update_layout(title=t(lang, "lap_unavailable"))
        return track_fig, delta_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

    lap1_row = lap1_rows.iloc[0]
    lap2_row = lap2_rows.iloc[0]

    try:
        df1 = fetch_car_data_for_lap(int(session_key), int(driver1), lap1_row)
        df2 = fetch_car_data_for_lap(int(session_key), int(driver2), lap2_row)
        loc1 = fetch_location_for_lap(int(session_key), int(driver1), lap1_row)
        loc2 = fetch_location_for_lap(int(session_key), int(driver2), lap2_row)
    except Exception as e:
        empty_fig.update_layout(title=t(lang, "error_generic", error=e))
        return track_fig, delta_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

    if df1.empty and df2.empty:
        empty_fig.update_layout(title=t(lang, "lap_unavailable"))
        return track_fig, delta_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

    name1_short = driver_label(int(driver1), df_drivers)
    name2_short = driver_label(int(driver2), df_drivers)

    dur1_s = lap_duration_seconds_from_row(lap1_row, df1)
    dur2_s = lap_duration_seconds_from_row(lap2_row, df2)
    dur1_str = fmt_duration(dur1_s)
    dur2_str = fmt_duration(dur2_s)

    # Nomi per la legenda con a capo prima del tempo giro
    name1 = f"{name1_short}<br>Lap {lap1_number} (durata: {dur1_str})"
    name2 = f"{name2_short}<br>Lap {lap2_number} (durata: {dur2_str})"

    title_suffix = f" · {name1_short} Lap {lap1_number} vs {name2_short} Lap {lap2_number}"
    selected_time_str = f" · t: {fmt_duration(selected_time)}" if selected_time is not None else ""

    # -------- TRACK --------
    track_fig = go.Figure()
    if not loc1.empty and loc1["x"].notna().any():
        track_fig.add_trace(go.Scatter(x=loc1["x"], y=loc1["y"], mode="lines", name=name1, line=dict(color=COLOR1)))
    if not loc2.empty and loc2["x"].notna().any():
        track_fig.add_trace(go.Scatter(x=loc2["x"], y=loc2["y"], mode="lines", name=name2, line=dict(color=COLOR2)))
    track_fig.update_layout(
        title=f"{t(lang, 'track_title')} · {name1_short} vs {name2_short}",
        xaxis_title="X (m)",
        yaxis_title="Y (m)",
        template="plotly_white",
        yaxis_scaleanchor="x",
    )

    # -------- DELTA --------
    progress, delta_t = compute_delta_time(df1, df2, n_points=200)
    delta_fig = go.Figure()
    if progress is not None:
        delta_fig.add_trace(go.Scatter(x=progress * 100.0, y=delta_t, mode="lines",
                                       name=f"{name2_short} vs {name1_short}", line=dict(color="#2ca02c")))
        delta_fig.update_layout(
            title=f"{t(lang, 'delta_graph_title')} · {name2_short} vs {name1_short}",
            xaxis_title=t(lang, "progress_x"),
            yaxis_title=f"Delta (s, >0 = {name2_short} più lento)",
            template="plotly_white",
            shapes=[dict(type="line", xref="paper", x0=0, x1=1, y0=0, y1=0, line=dict(dash="dash", width=1))],
        )

    # -------- SPEED --------
    speed_fig = go.Figure()
    if not df1.empty:
        speed_fig.add_trace(go.Scatter(x=df1["t_rel_s"], y=df1["speed"], mode="lines",
                                       name=name1, line=dict(color=COLOR1)))
    if not df2.empty:
        speed_fig.add_trace(go.Scatter(x=df2["t_rel_s"], y=df2["speed"], mode="lines",
                                       name=name2, line=dict(color=COLOR2)))
    speed_fig.update_layout(
        title=t(lang, "speed_title", suffix=title_suffix) + selected_time_str,
        xaxis_title=t(lang, "telemetry_x"),
        yaxis_title=t(lang, "speed_y"),
        template="plotly_white",
    )

    # -------- SPEED HEATMAP --------
    speed_heatmap = go.Figure()
    progress_grid = np.linspace(0.0, 1.0, 120)

    def interp_speed(df, duration):
        if df.empty:
            return np.full_like(progress_grid, np.nan, dtype=float)
        duration = duration or float(df["t_rel_s"].max())
        rel = df["t_rel_s"].to_numpy()
        speed_vals = df["speed"].to_numpy()
        return np.interp(progress_grid * duration, rel, speed_vals)

    z = [
        interp_speed(df1, dur1_s),
        interp_speed(df2, dur2_s),
    ]
    speed_heatmap.add_trace(
        go.Heatmap(
            z=z,
            x=progress_grid * 100.0,
            y=[name1_short, name2_short],
            colorscale="Turbo",
            colorbar=dict(title="km/h"),
            zmin=np.nanmin(z) if not np.isnan(z).all() else None,
            zmax=np.nanmax(z) if not np.isnan(z).all() else None,
        )
    )
    heatmap_shapes = []
    if selected_time is not None:
        heatmap_shapes.append(
            dict(
                type="line",
                xref="x",
                x0=selected_time / dur1_s * 100 if dur1_s else selected_time,
                x1=selected_time / dur1_s * 100 if dur1_s else selected_time,
                yref="paper",
                y0=0,
                y1=1,
                line=dict(color="black", dash="dot", width=1.5),
            )
        )
    speed_heatmap.update_layout(
        title=t(lang, "heat_speed_title", suffix=title_suffix) + selected_time_str,
        xaxis_title=t(lang, "progress_x"),
        yaxis_title="Pilota",
        template="plotly_white",
        shapes=heatmap_shapes,
    )

    # -------- THROTTLE --------
    throttle_fig = go.Figure()
    if not df1.empty:
        throttle_fig.add_trace(go.Scatter(x=df1["t_rel_s"], y=df1["throttle"], mode="lines",
                                          name=name1, line=dict(color=COLOR1)))
    if not df2.empty:
        throttle_fig.add_trace(go.Scatter(x=df2["t_rel_s"], y=df2["throttle"], mode="lines",
                                          name=name2, line=dict(color=COLOR2)))
    throttle_fig.update_layout(
        title=t(lang, "throttle_title", suffix=title_suffix) + selected_time_str,
        xaxis_title=t(lang, "telemetry_x"),
        yaxis_title="Throttle (%)",
        template="plotly_white",
    )

    # -------- BRAKE --------
    brake_fig = go.Figure()
    if not df1.empty:
        brake_fig.add_trace(go.Scatter(x=df1["t_rel_s"], y=df1["brake"], mode="lines",
                                       name=name1, line=dict(color=COLOR1)))
    if not df2.empty:
        brake_fig.add_trace(go.Scatter(x=df2["t_rel_s"], y=df2["brake"], mode="lines",
                                       name=name2, line=dict(color=COLOR2)))
    brake_fig.update_layout(
        title=t(lang, "brake_title", suffix=title_suffix) + selected_time_str,
        xaxis_title=t(lang, "telemetry_x"),
        yaxis_title="Brake",
        template="plotly_white",
    )

    # -------- GEAR --------
    gear_fig = go.Figure()
    if not df1.empty:
        gear_fig.add_trace(go.Scatter(x=df1["t_rel_s"], y=df1["n_gear"], mode="lines",
                                      name=name1, line=dict(color=COLOR1)))
    if not df2.empty:
        gear_fig.add_trace(go.Scatter(x=df2["t_rel_s"], y=df2["n_gear"], mode="lines",
                                      name=name2, line=dict(color=COLOR2)))
    gear_fig.update_layout(
        title=t(lang, "gear_title", suffix=title_suffix) + selected_time_str,
        xaxis_title=t(lang, "telemetry_x"),
        yaxis_title="Marcia",
        template="plotly_white",
    )

    # Linee verticali a fine giro per i due piloti
    end_lines = []
    if dur1_s is not None:
        end_lines.append(
            dict(
                type="line",
                xref="x",
                x0=dur1_s,
                x1=dur1_s,
                yref="paper",
                y0=0,
                y1=1,
                line=dict(color=COLOR1, dash="dash", width=1.2),
            )
        )
    if dur2_s is not None:
        end_lines.append(
            dict(
                type="line",
                xref="x",
                x0=dur2_s,
                x1=dur2_s,
                yref="paper",
                y0=0,
                y1=1,
                line=dict(color=COLOR2, dash="dash", width=1.2),
            )
        )

    for fig in [speed_fig, throttle_fig, brake_fig, gear_fig]:
        base_shapes = list(fig.layout.shapes) if fig.layout.shapes else []
        base_shapes.extend(end_lines)

        base_annotations = list(fig.layout.annotations) if fig.layout.annotations else []
        if dur1_s is not None:
            base_annotations.append(
                dict(
                    x=dur1_s,
                    xref="x",
                    y=1.02,
                    yref="paper",
                    text=t(lang, "finish_label"),
                    showarrow=False,
                    font=dict(color=COLOR1, size=10),
                )
            )
        if dur2_s is not None:
            base_annotations.append(
                dict(
                    x=dur2_s,
                    xref="x",
                    y=1.02,
                    yref="paper",
                    text=t(lang, "finish_label"),
                    showarrow=False,
                    font=dict(color=COLOR2, size=10),
                )
            )

        fig.update_layout(shapes=base_shapes, annotations=base_annotations)

    # Aggiungi linea verticale e marcatori se selected_time
    if selected_time is not None:
        vertical_line = dict(
            type="line",
            xref="x",
            x0=selected_time,
            x1=selected_time,
            yref="paper",
            y0=0,
            y1=1,
            line=dict(color="black", dash="dot", width=1.5),
        )

        for fig in [speed_fig, throttle_fig, brake_fig, gear_fig]:
            shapes = list(fig.layout.shapes) if fig.layout.shapes else []
            shapes.append(vertical_line)
            fig.update_layout(shapes=shapes)

        def add_marker(loc_df, color, label):
            if loc_df.empty or "t_rel_s" not in loc_df:
                return
            loc_df_valid = loc_df.dropna(subset=["t_rel_s", "x", "y"])
            if loc_df_valid.empty:
                return
            idx = (loc_df_valid["t_rel_s"] - selected_time).abs().idxmin()
            row = loc_df_valid.loc[idx]
            track_fig.add_trace(
                go.Scatter(
                    x=[row["x"]],
                    y=[row["y"]],
                    mode="markers",
                    name=f"{label} @ {fmt_duration(selected_time)}",
                    marker=dict(color=color, size=10, symbol="x"),
                    showlegend=True,
                )
            )

        add_marker(loc1, COLOR1, name1_short)
        add_marker(loc2, COLOR2, name2_short)

    return track_fig, delta_fig, speed_fig, speed_heatmap, throttle_fig, brake_fig, gear_fig


@callback(
    Output("selected-time-store", "data"),
    inputs=[
        Input("speed-graph", "clickData"),
        Input("session-dropdown", "value"),
    ],
)
def update_selected_time(click_data, session_key):
    """Cattura il tempo selezionato con click sul grafico speed."""
    ctx = callback_context

    if not ctx.triggered:
        return no_update

    prop_id = ctx.triggered[0]["prop_id"]

    if "session-dropdown" in prop_id:
        return None

    source = click_data

    if not source or "points" not in source or not source["points"]:
        return no_update

    x_val = source["points"][0].get("x")
    if x_val is None:
        return no_update

    try:
        return float(x_val)
    except (TypeError, ValueError):
        return no_update
