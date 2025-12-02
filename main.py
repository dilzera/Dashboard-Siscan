import dash
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from flask import request, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import timedelta, datetime
from src.data_layer import get_years, get_health_units, get_regions, get_sex_options, get_birads_options
from src.components.layout import create_main_layout, create_login_layout
from src.callbacks import build_dashboard_content
from src.config import COLORS, SESSION_SECRET
from src.models import User, get_session, get_engine, Base

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

app.title = 'Dashboard SISCAN - Monitoramento de Mamografia'

server = app.server
server.secret_key = SESSION_SECRET
server.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'

@login_manager.user_loader
def load_user(user_id):
    db_session = get_session()
    try:
        user = db_session.query(User).get(int(user_id))
        return user
    finally:
        db_session.close()

def init_users_table():
    engine = get_engine()
    Base.metadata.create_all(engine, tables=[User.__table__])
    
    db_session = get_session()
    try:
        admin = db_session.query(User).filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                name='Administrador',
                role='admin'
            )
            admin.set_password('siscan2024')
            db_session.add(admin)
            db_session.commit()
            print("Usuario admin criado com sucesso!")
    finally:
        db_session.close()

init_users_table()

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
            .btn-primary {{
                background-color: {COLORS['primary']};
                border-color: {COLORS['primary']};
            }}
            .btn-primary:hover {{
                background-color: {COLORS['sidebar_bg']};
                border-color: {COLORS['sidebar_bg']};
            }}
            .btn-info {{
                background-color: {COLORS['primary']};
                border-color: {COLORS['primary']};
            }}
            .btn-info:hover {{
                background-color: {COLORS['secondary']};
                border-color: {COLORS['secondary']};
            }}
            .login-container {{
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['sidebar_bg']} 100%);
            }}
            .login-card {{
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                padding: 40px;
                width: 100%;
                max-width: 400px;
            }}
            .login-logo {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .login-logo h1 {{
                color: {COLORS['primary']};
                font-weight: 700;
                margin: 0;
            }}
            .login-logo span {{
                color: {COLORS['accent']};
            }}
            .form-control:focus {{
                border-color: {COLORS['primary']};
                box-shadow: 0 0 0 0.2rem rgba(0, 91, 150, 0.25);
            }}
            .user-info {{
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .user-badge {{
                background-color: rgba(255,255,255,0.2);
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 14px;
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

@server.after_request
def add_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    html.Div(id='page-content')
])

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/logout':
        return create_login_layout(COLORS)
    
    if not current_user.is_authenticated:
        return create_login_layout(COLORS)
    
    years = get_years()
    health_units = get_health_units()
    regions = get_regions()
    sex_options = get_sex_options()
    birads_options = get_birads_options()
    initial_content = build_dashboard_content()
    
    return create_main_layout(
        years, 
        health_units, 
        regions, 
        initial_content,
        sex_options=sex_options,
        birads_options=birads_options,
        user_name=current_user.name if current_user.is_authenticated else None
    )

@app.callback(
    [Output('url', 'pathname'),
     Output('login-error', 'children'),
     Output('login-error', 'style')],
    Input('login-button', 'n_clicks'),
    [State('login-username', 'value'),
     State('login-password', 'value')],
    prevent_initial_call=True
)
def handle_login(n_clicks, username, password):
    if not n_clicks:
        return dash.no_update, '', {'display': 'none'}
    
    if not username or not password:
        return dash.no_update, 'Por favor, preencha todos os campos.', {'display': 'block', 'color': COLORS['danger'], 'marginTop': '10px'}
    
    db_session = get_session()
    try:
        user = db_session.query(User).filter_by(username=username, is_active=True).first()
        
        if user and user.check_password(password):
            user.last_login = datetime.utcnow()
            db_session.commit()
            login_user(user)
            return '/', '', {'display': 'none'}
        else:
            return dash.no_update, 'Usuário ou senha incorretos.', {'display': 'block', 'color': COLORS['danger'], 'marginTop': '10px', 'fontWeight': '500'}
    finally:
        db_session.close()

@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('logout-button', 'n_clicks'),
    prevent_initial_call=True
)
def handle_logout(n_clicks):
    if n_clicks:
        logout_user()
        return '/logout'
    return dash.no_update

from src.callbacks import register_callbacks
register_callbacks(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
