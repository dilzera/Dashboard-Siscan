import dash
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
from flask import request, make_response
from src.data_layer import get_years, get_health_units, get_regions, get_sex_options, get_birads_options
from src.components.layout import create_main_layout
from src.callbacks import build_dashboard_content
from src.config import COLORS

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

app.title = 'Saúde Já - Painel de Monitoramento'

app.index_string = f'''
<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        <style>
            .nav-tabs .nav-link {{
                color: {COLORS['primary']};
                border: none;
                border-bottom: 2px solid transparent;
                font-weight: 500;
            }}
            .nav-tabs .nav-link:hover {{
                color: {COLORS['secondary']};
                border-bottom: 2px solid {COLORS['secondary']};
            }}
            .nav-tabs .nav-link.active {{
                color: {COLORS['primary']};
                background-color: transparent;
                border: none;
                border-bottom: 3px solid {COLORS['primary']};
                font-weight: 600;
            }}
            .nav-tabs {{
                border-bottom: 1px solid #dee2e6;
            }}
            .table thead th {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                font-weight: 500;
            }}
            .table tbody tr:nth-of-type(odd) {{
                background-color: {COLORS['table_row_alt']};
            }}
            .table tbody tr:hover {{
                background-color: #e9ecef;
            }}
            .btn-info {{
                background-color: {COLORS['primary']};
                border-color: {COLORS['primary']};
            }}
            .btn-info:hover {{
                background-color: {COLORS['secondary']};
                border-color: {COLORS['secondary']};
            }}
        </style>
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>
'''

@app.server.after_request
def add_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

years = get_years()
health_units = get_health_units()
regions = get_regions()
sex_options = get_sex_options()
birads_options = get_birads_options()


initial_content = build_dashboard_content()

app.layout = create_main_layout(
    years, 
    health_units, 
    regions, 
    initial_content,
    sex_options=sex_options,
    birads_options=birads_options
)

from src.callbacks import register_callbacks
register_callbacks(app)

server = app.server

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
