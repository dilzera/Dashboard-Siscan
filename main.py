import dash
from dash import Dash
import dash_bootstrap_components as dbc
from src.data_layer import get_years, get_health_units, get_regions, populate_sample_data
from src.components.layout import create_main_layout
from src.callbacks import register_callbacks

populate_sample_data()

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        {'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}
    ]
)

app.title = 'SISCAN Dashboard'

years = get_years()
health_units = get_health_units()
regions = get_regions()

app.layout = create_main_layout(years, health_units, regions)

register_callbacks(app)

server = app.server

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
