import dash
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
from flask import request, make_response
from src.data_layer import get_years, get_health_units, get_regions
from src.components.layout import create_main_layout
from src.callbacks import build_dashboard_content

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

@app.server.after_request
def add_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

years = get_years()
health_units = get_health_units()
regions = get_regions()


initial_content = build_dashboard_content()

app.layout = create_main_layout(
    years, 
    health_units, 
    regions, 
    initial_content
)

from src.callbacks import register_callbacks
register_callbacks(app)

server = app.server

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
