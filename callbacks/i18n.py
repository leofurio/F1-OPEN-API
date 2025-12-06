from dash import Input, Output, callback

from utils.i18n import t, LANG_DEFAULT


@callback(
    output=[
        Output("lang-store", "data"),
        Output("page-title", "children"),
        Output("intro-text", "children"),
        Output("year-label", "children"),
        Output("year-input", "placeholder"),
        Output("load-meetings-btn", "children"),
        Output("meeting-label", "children"),
        Output("session-label", "children"),
        Output("driver1-label", "children"),
        Output("lap1-label", "children"),
        Output("driver2-label", "children"),
        Output("lap2-label", "children"),
        Output("tab-telemetry", "label"),
        Output("tab-all-laps", "label"),
        Output("tab-best-laps", "label"),
        Output("graph-order-label", "children"),
        Output("move-up-btn", "children"),
        Output("move-down-btn", "children"),
        Output("reset-graph-order-btn", "children"),
        Output("print-btn", "children"),
    ],
    inputs=[Input("language-dropdown", "value")],
)
def translate_ui(lang):
    """Aggiorna le etichette statiche in base alla lingua selezionata."""
    lang = lang or LANG_DEFAULT
    return [
        lang,
        t(lang, "page_title"),
        t(lang, "intro"),
        t(lang, "year_label"),
        t(lang, "year_placeholder"),
        t(lang, "load_meetings"),
        t(lang, "meeting_label"),
        t(lang, "session_label"),
        t(lang, "driver1_label"),
        t(lang, "lap1_label"),
        t(lang, "driver2_label"),
        t(lang, "lap2_label"),
        t(lang, "tab_telemetry"),
        t(lang, "tab_all_laps"),
        t(lang, "tab_best_laps"),
        t(lang, "graph_order"),
        t(lang, "move_up"),
        t(lang, "move_down"),
        t(lang, "reset_order"),
        t(lang, "print_pdf"),
    ]
