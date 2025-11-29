from dash import Dash
from components.layout import create_layout

# Import callbacks per registrarli
import callbacks.meetings
import callbacks.drivers
import callbacks.graphs

app = Dash(__name__)
app.title = "OpenF1 – Driver Comparison"
app.layout = create_layout()

if __name__ == "__main__":
    app.run(debug=True)