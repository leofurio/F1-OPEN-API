import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, html

from api.openf1 import fetch_race_control, fetch_weather
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


def _fmt_value(value, suffix: str = "", digits: int = 1) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "N/A"
    try:
        return f"{float(value):.{digits}f}{suffix}"
    except Exception:
        return str(value)


def _yes_no(value, lang: str) -> str:
    truthy = bool(value)
    if lang == "it":
        return "si" if truthy else "no"
    return "yes" if truthy else "no"


def _build_race_control_table(df: pd.DataFrame, lang: str):
    if df.empty:
        return html.Div(t(lang, "rcw_race_control_none"))

    latest = df.sort_values("date", ascending=False).head(12).copy()
    if "date" in latest.columns:
        latest["date_fmt"] = pd.to_datetime(latest["date"], errors="coerce", utc=True).dt.strftime("%H:%M:%S")
        latest["date_fmt"] = latest["date_fmt"].fillna("")
    else:
        latest["date_fmt"] = ""

    header_style = {"borderBottom": "2px solid #ccc", "padding": "8px 10px", "textAlign": "left"}
    cell_style = {"padding": "8px 10px", "borderTop": "1px solid #eee", "verticalAlign": "top"}

    rows = []
    for _, row in latest.iterrows():
        driver_number = row.get("driver_number")
        driver_label = f"#{int(driver_number)}" if pd.notna(driver_number) else "-"
        lap_value = row.get("lap_number")
        lap_label = str(int(lap_value)) if pd.notna(lap_value) else "-"
        rows.append(
            html.Tr(
                [
                    html.Td(row.get("date_fmt") or "-", style=cell_style),
                    html.Td(row.get("category") or "-", style=cell_style),
                    html.Td(row.get("flag") or "-", style=cell_style),
                    html.Td(lap_label, style=cell_style),
                    html.Td(driver_label, style=cell_style),
                    html.Td(row.get("message") or "-", style=cell_style),
                ]
            )
        )

    return html.Div(
        [
            html.H4(t(lang, "rcw_table_title"), style={"marginBottom": "8px"}),
            html.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th(t(lang, "rcw_table_time"), style=header_style),
                                html.Th(t(lang, "rcw_table_category"), style=header_style),
                                html.Th(t(lang, "rcw_table_flag"), style=header_style),
                                html.Th(t(lang, "rcw_table_lap"), style=header_style),
                                html.Th(t(lang, "rcw_table_driver"), style=header_style),
                                html.Th(t(lang, "rcw_table_message"), style=header_style),
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
        Output("race-control-weather-summary", "children"),
        Output("weather-temperatures-graph", "figure"),
        Output("weather-conditions-graph", "figure"),
        Output("race-control-table", "children"),
    ],
    inputs=[
        Input("session-dropdown", "value"),
        Input("lang-store", "data"),
    ],
)
def render_race_control_weather(session_key, lang):
    lang = lang or LANG_DEFAULT
    prompt = t(lang, "rcw_prompt")
    if not session_key:
        empty = _empty_fig(prompt, xaxis_title=t(lang, "rcw_time"))
        return prompt, empty, empty, prompt

    try:
        weather = fetch_weather(int(session_key))
        race_control = fetch_race_control(int(session_key))
    except Exception as e:
        msg = sanitize_error_message(e)
        empty = _empty_fig(msg, xaxis_title=t(lang, "rcw_time"))
        return msg, empty, empty, msg

    weather_fig = _empty_fig(
        t(lang, "rcw_weather_none"),
        xaxis_title=t(lang, "rcw_time"),
        yaxis_title=t(lang, "rcw_temp_y"),
    )
    conditions_fig = _empty_fig(
        t(lang, "rcw_weather_none"),
        xaxis_title=t(lang, "rcw_time"),
        yaxis_title=t(lang, "rcw_humidity_y"),
    )

    summary_parts = []

    if not weather.empty and "date" in weather.columns:
        weather = weather.copy()
        weather["date"] = pd.to_datetime(weather["date"], errors="coerce", utc=True)
        weather = weather.dropna(subset=["date"]).sort_values("date")

        if not weather.empty:
            if "track_temperature" in weather.columns:
                weather_fig.add_trace(
                    go.Scatter(
                        x=weather["date"],
                        y=weather["track_temperature"],
                        mode="lines",
                        name="Track",
                        line=dict(color="#d62728", width=2),
                    )
                )
            if "air_temperature" in weather.columns:
                weather_fig.add_trace(
                    go.Scatter(
                        x=weather["date"],
                        y=weather["air_temperature"],
                        mode="lines",
                        name="Air",
                        line=dict(color="#1f77b4", width=2),
                    )
                )
            weather_fig.update_layout(
                title=t(lang, "rcw_temp_title"),
                xaxis_title=t(lang, "rcw_time"),
                yaxis_title=t(lang, "rcw_temp_y"),
                template="plotly_white",
            )

            if "humidity" in weather.columns:
                conditions_fig.add_trace(
                    go.Scatter(
                        x=weather["date"],
                        y=weather["humidity"],
                        mode="lines",
                        name="Humidity",
                        line=dict(color="#2ca02c", width=2),
                        yaxis="y1",
                    )
                )
            if "wind_speed" in weather.columns:
                conditions_fig.add_trace(
                    go.Scatter(
                        x=weather["date"],
                        y=weather["wind_speed"],
                        mode="lines",
                        name="Wind",
                        line=dict(color="#ff7f0e", width=2),
                        yaxis="y2",
                    )
                )
            if "rainfall" in weather.columns and weather["rainfall"].notna().any():
                rainfall_points = weather[weather["rainfall"].astype(bool)]
                if not rainfall_points.empty:
                    conditions_fig.add_trace(
                        go.Scatter(
                            x=rainfall_points["date"],
                            y=[100] * len(rainfall_points),
                            mode="markers",
                            name="Rainfall",
                            marker=dict(color="#0057e7", size=9, symbol="diamond"),
                            yaxis="y1",
                        )
                    )
            conditions_fig.update_layout(
                title=t(lang, "rcw_conditions_title"),
                xaxis_title=t(lang, "rcw_time"),
                yaxis=dict(title=t(lang, "rcw_humidity_y"), range=[0, 100]),
                yaxis2=dict(title=t(lang, "rcw_wind_y"), overlaying="y", side="right"),
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            )

            latest_weather = weather.iloc[-1]
            summary_parts.append(
                html.Div(
                    t(
                        lang,
                        "rcw_summary_weather",
                        track=_fmt_value(latest_weather.get("track_temperature"), "°C"),
                        air=_fmt_value(latest_weather.get("air_temperature"), "°C"),
                        humidity=_fmt_value(latest_weather.get("humidity"), "%"),
                        wind=_fmt_value(latest_weather.get("wind_speed"), " m/s"),
                        rain=_yes_no(latest_weather.get("rainfall"), lang),
                    )
                )
            )
    else:
        summary_parts.append(html.Div(t(lang, "rcw_weather_none")))

    if not race_control.empty:
        race_control = race_control.copy()
        if "date" in race_control.columns:
            race_control["date"] = pd.to_datetime(race_control["date"], errors="coerce", utc=True)
            race_control = race_control.dropna(subset=["date"]).sort_values("date")

        latest_event = race_control.iloc[-1] if not race_control.empty else None
        if latest_event is not None:
            event_label = (
                latest_event.get("message")
                or latest_event.get("flag")
                or latest_event.get("category")
                or t(lang, "rcw_event_unknown")
            )
        else:
            event_label = t(lang, "rcw_event_unknown")
        summary_parts.append(
            html.Div(
                t(
                    lang,
                    "rcw_summary_events",
                    count=len(race_control),
                    event=event_label,
                )
            )
        )
    else:
        summary_parts.append(html.Div(t(lang, "rcw_race_control_none")))

    race_control_table = _build_race_control_table(race_control, lang)
    return summary_parts, weather_fig, conditions_fig, race_control_table
