from dash import Input, Output, State, callback, html, dcc, callback_context
from utils.graph_order import DEFAULT_GRAPH_ORDER, GRAPH_TITLES


def _normalize_order(order):
    if order and isinstance(order, list):
        return [g for g in order if isinstance(g, str)]
    return list(DEFAULT_GRAPH_ORDER)


@callback(
    Output("graph-order-store", "data"),
    Output("graph-order-msg", "children"),
    inputs=[
        Input("move-up-btn", "n_clicks"),
        Input("move-down-btn", "n_clicks"),
        Input("reset-graph-order-btn", "n_clicks"),
    ],
    state=[State("graph-order-store", "data"), State("graph-order-radio", "value")],
    prevent_initial_call=True,
)
def change_graph_order(n_up, n_down, n_reset, order, selected):
    """Muove l'elemento selezionato su/giu o resetta l'ordine."""
    ctx = callback_context
    if not ctx.triggered:
        return order or DEFAULT_GRAPH_ORDER, ""

    trigger = ctx.triggered[0]["prop_id"]
    current = _normalize_order(order)

    if "reset-graph-order-btn" in trigger:
        return DEFAULT_GRAPH_ORDER, "Ordine resettato."

    if not selected or selected not in current:
        return current, "Seleziona prima un grafico."

    idx = current.index(selected)

    if "move-up-btn" in trigger:
        if idx == 0:
            return current, "Gia in cima."
        current[idx - 1], current[idx] = current[idx], current[idx - 1]
        return current, f"Spostato: {GRAPH_TITLES[selected]}"

    if "move-down-btn" in trigger:
        if idx == len(current) - 1:
            return current, "Gia in fondo."
        current[idx + 1], current[idx] = current[idx], current[idx + 1]
        return current, f"Spostato: {GRAPH_TITLES[selected]}"

    return current, ""


@callback(
    Output("graph-order-radio", "options"),
    Output("graph-order-radio", "value"),
    inputs=[Input("graph-order-store", "data")],
)
def sync_radio_with_order(order):
    """Aggiorna le options del radio in base all'ordine corrente."""
    order = _normalize_order(order)
    opts = [{"label": GRAPH_TITLES.get(g, g), "value": g} for g in order]
    value = order[0] if order else None
    return opts, value


@callback(
    Output("graphs-container", "children"),
    inputs=[Input("graph-order-store", "data")],
)
def render_graphs_container(order):
    """Rende i grafici nell'ordine scelto dall'utente."""
    order = _normalize_order(order)
    children = []
    for graph_id in order:
        title = GRAPH_TITLES.get(graph_id, graph_id)
        children.append(
            html.Div(
                [
                    html.H3(title, style={"marginBottom": "6px"}),
                    dcc.Graph(id=graph_id),
                ],
                style={"display": "flex", "flexDirection": "column", "gap": "6px"},
            )
        )
    return children
