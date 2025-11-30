from dash import Input, Output, callback, callback_context
from utils.cache import clear_cache, cache_size_mb


@callback(
    Output("cache-status", "children"),
    inputs=[Input("clear-cache-btn", "n_clicks")],
    prevent_initial_call=False,
)
def manage_cache(n_clicks):
    """Unico callback che gestisce stato cache e pulizia."""
    ctx = callback_context
    # Se non è stato triggerato (render iniziale), mostra dimensione cache
    if not ctx.triggered:
        size_mb = cache_size_mb()
        return f"💾 Cache: {size_mb:.2f} MB"

    prop = ctx.triggered[0]["prop_id"]
    if "clear-cache-btn" in prop and n_clicks and n_clicks > 0:
        clear_cache()
        return "✅ Cache svuotato!"

    size_mb = cache_size_mb()
    return f"💾 Cache: {size_mb:.2f} MB"