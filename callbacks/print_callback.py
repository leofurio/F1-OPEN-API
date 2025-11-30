from dash import Input, Output, clientside_callback


# Client-side print to avoid server roundtrip delays; triggers window.print().
clientside_callback(
    """
    function(n) {
        if (!n) { return window.dash_clientside.no_update; }
        setTimeout(() => window.print(), 50);
        return "";
    }
    """,
    Output("print-trigger", "children"),
    Input("print-btn", "n_clicks"),
)
