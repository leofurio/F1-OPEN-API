DEFAULT_GRAPH_ORDER = [
    "track-graph",
    "delta-graph",
    "speed-graph",
    "throttle-graph",
    "brake-graph",
    "gear-graph",
]

GRAPH_TITLES = {
    "track-graph": "🗺️ Tracciato",
    "delta-graph": "⏱️ Delta Tempo",
    "speed-graph": "🏎️💨 Velocità",
    "throttle-graph": "⚡ Throttle",
    "brake-graph": "🛑 Brake",
    "gear-graph": "⚙️ Marcia",
}


def get_graph_order_from_store(order_data):
    """Estrae l'ordine dal store, fallback a default."""
    if order_data and isinstance(order_data, list):
        return order_data
    return DEFAULT_GRAPH_ORDER
