from dash import Dash
from components.layout import create_layout

# Import callbacks per registrarli
import callbacks.meetings  # noqa: E402,F401
import callbacks.drivers  # noqa: E402,F401
import callbacks.graphs  # noqa: E402,F401
import callbacks.cache  # noqa: E402,F401
import callbacks.graph_order  # noqa: E402,F401
import callbacks.print_callback  # noqa: E402,F401
import callbacks.all_laps  # noqa: E402,F401
import callbacks.best_laps  # noqa: E402,F401
import callbacks.strategy  # noqa: E402,F401
import callbacks.ranking  # noqa: E402,F401
import callbacks.i18n  # noqa: E402,F401

# Abilita suppress_callback_exceptions per permettere callback su componenti creati dinamicamente
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "OpenF1 - Driver Comparison"
app.layout = create_layout()

if __name__ == "__main__":
    app.run(debug=True)
