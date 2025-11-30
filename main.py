from dash import Dash
from components.layout import create_layout

# Import callbacks per registrarli
import callbacks.meetings
import callbacks.drivers
import callbacks.graphs
import callbacks.cache
import callbacks.graph_order
import callbacks.print_callback

# Abilita suppress_callback_exceptions per permettere callback su componenti creati dinamicamente
app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "OpenF1 – Driver Comparison"
app.layout = create_layout()

if __name__ == "__main__":
    app.run(debug=True)
