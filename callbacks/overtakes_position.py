import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, html

from api.openf1 import fetch_overtakes, fetch_position
from config import COLOR1, COLOR2
from utils.i18n import LANG_DEFAULT, t
from utils.security import sanitize_error_message


def _empty_fig(title: str, xaxis_title: str = "", yaxis_title: str = "") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        template="plotly_white",
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
    )
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


def _build_overtakes_table(df: pd.DataFrame, df_drivers: pd.DataFrame, lang: str):
    if df.empty:
        return html.Div(t(lang, "op_overtakes_none"))

    latest = df.sort_values("date", ascending=False).head(15).copy()
    latest["date_fmt"] = pd.to_datetime(latest["date"], errors="coerce", utc=True).dt.strftime("%H:%M:%S")
    latest["date_fmt"] = latest["date_fmt"].fillna("")

    header_style = {"borderBottom": "2px solid #ccc", "padding": "8px 10px", "textAlign": "left"}
    cell_style = {"padding": "8px 10px", "borderTop": "1px solid #eee", "verticalAlign": "top"}

    rows = []
    for _, row in latest.iterrows():
        overtaker = row.get("overtaking_driver_number")
        overtaken = row.get("overtaken_driver_number")
        position = row.get("position")
        rows.append(
            html.Tr(
                [
                    html.Td(row.get("date_fmt") or "-", style=cell_style),
                    html.Td(_driver_label(int(overtaker), df_drivers) if pd.notna(overtaker) else "-", style=cell_style),
                    html.Td(_driver_label(int(overtaken), df_drivers) if pd.notna(overtaken) else "-", style=cell_style),
                    html.Td(str(int(position)) if pd.notna(position) else "-", style=cell_style),
                ]
            )
        )

    return html.Div(
        [
            html.H4(t(lang, "op_table_title"), style={"marginBottom": "8px"}),
            html.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th(t(lang, "op_table_time"), style=header_style),
                                html.Th(t(lang, "op_table_overtaker"), style=header_style),
                                html.Th(t(lang, "op_table_overtaken"), style=header_style),
                                html.Th(t(lang, "op_table_position"), style=header_style),
                            ]
                        )
                    ),
                    html.Tbody(rows),
                ],
                style={"borderCollapse": "collapse", "width": "100%"},
            ),
        ]
    )


@callback(
    output=[
        Output("overtakes-position-summary", "children"),
        Output("position-timeline-graph", "figure"),
        Output("overtakes-table", "children"),
    ],
    inputs=[
        Input("session-dropdown", "value"),
        Input("driver1-dropdown", "value"),
        Input("driver2-dropdown", "value"),
        Input("lang-store", "data"),
    ],
    state=[State("drivers-store", "data")],
)
def render_overtakes_position(session_key, driver1, driver2, lang, drivers_data):
    lang = lang or LANG_DEFAULT
    prompt = t(lang, "op_prompt")
    if not session_key:
        empty = _empty_fig(prompt, xaxis_title=t(lang, "op_time"), yaxis_title=t(lang, "op_position_y"))
        return prompt, empty, prompt

    df_drivers = pd.DataFrame(drivers_data) if drivers_data else pd.DataFrame()

    try:
        positions = fetch_position(int(session_key))
        overtakes = fetch_overtakes(int(session_key))
    except Exception as e:
        msg = sanitize_error_message(e)
        empty = _empty_fig(msg, xaxis_title=t(lang, "op_time"), yaxis_title=t(lang, "op_position_y"))
        return msg, empty, msg

    position_fig = _empty_fig(
        t(lang, "op_position_none"),
        xaxis_title=t(lang, "op_time"),
        yaxis_title=t(lang, "op_position_y"),
    )

    summary_parts = []

    if not positions.empty and "date" in positions.columns:
        positions = positions.copy()
        positions["date"] = pd.to_datetime(positions["date"], errors="coerce", utc=True)
        positions = positions.dropna(subset=["date", "driver_number", "position"]).sort_values("date")

        selected = [drv for drv in [driver1, driver2] if drv]
        if not selected:
            available = positions["driver_number"].dropna().astype(int).unique().tolist()
            selected = available[:2]

        for drv, color in zip(selected[:2], [COLOR1, COLOR2]):
            drv_rows = positions[positions["driver_number"] == int(drv)].copy()
            if drv_rows.empty:
                continue
            label = _driver_label(int(drv), df_drivers)
            position_fig.add_trace(
                go.Scatter(
                    x=drv_rows["date"],
                    y=drv_rows["position"],
                    mode="lines+markers",
                    name=label,
                    line=dict(color=color, width=2),
                    marker=dict(size=6),
                )
            )

        if position_fig.data:
            position_fig.update_layout(
                title=t(lang, "op_position_title"),
                xaxis_title=t(lang, "op_time"),
                yaxis_title=t(lang, "op_position_y"),
                yaxis=dict(autorange="reversed"),
                template="plotly_white",
            )
            summary_parts.append(html.Div(t(lang, "op_summary_positions", count=len(positions))))
        else:
            summary_parts.append(html.Div(t(lang, "op_position_none")))
    else:
        summary_parts.append(html.Div(t(lang, "op_position_none")))

    if not overtakes.empty and "date" in overtakes.columns:
        overtakes = overtakes.copy()
        overtakes["date"] = pd.to_datetime(overtakes["date"], errors="coerce", utc=True)
        overtakes = overtakes.dropna(subset=["date"]).sort_values("date")
        summary_parts.append(html.Div(t(lang, "op_summary_overtakes", count=len(overtakes))))
    else:
        overtakes = pd.DataFrame()
        summary_parts.append(html.Div(t(lang, "op_overtakes_none")))

    overtakes_table = _build_overtakes_table(overtakes, df_drivers, lang)
    return summary_parts, position_fig, overtakes_table
