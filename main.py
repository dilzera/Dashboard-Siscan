import dash
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from flask import request, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import timedelta, datetime
from src.data_layer import get_years, get_health_units, get_regions, get_sex_options, get_birads_options
from src.components.layout import create_main_layout, create_login_layout
from src.callbacks import build_dashboard_content
from src.config import COLORS, SESSION_SECRET
from src.models import User, TermoLinkage, get_session, get_engine, Base

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

app.title = 'Central Inteligente de Câncer de Mama - Curitiba'

server = app.server
server.secret_key = SESSION_SECRET
server.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'

@server.route('/health')
def health_check():
    return 'OK', 200

@server.before_request
def check_session_timeout():
    if current_user.is_authenticated:
        login_time = session.get('login_time')
        if login_time:
            login_datetime = datetime.fromisoformat(login_time)
            if datetime.utcnow() - login_datetime > timedelta(hours=1):
                logout_user()
                session.clear()
                return redirect('/login?expired=1')
    
    excluded_paths = ['/login', '/logout', '/_dash-', '/_reload-hash', '/assets/', '/favicon', '/health']
    if not any(request.path.startswith(p) for p in excluded_paths):
        if not current_user.is_authenticated:
            if request.path not in ['/', ''] and not request.path.endswith(('.ico', '.png', '.jpg', '.css', '.js', '.map')):
                session['next_url'] = request.path
            elif 'next_url' not in session:
                session['next_url'] = '/'
            return redirect('/login')

@login_manager.user_loader
def load_user(user_id):
    db_session = get_session()
    try:
        user = db_session.query(User).get(int(user_id))
        return user
    finally:
        db_session.close()

def init_users_table():
    import os
    import secrets
    engine = get_engine()
    Base.metadata.create_all(engine, tables=[User.__table__])
    
    db_session = get_session()
    try:
        admin_password = os.environ.get('ADMIN_PASSWORD')
        admin = db_session.query(User).filter_by(username='admin').first()
        
        if not admin:
            if not admin_password:
                admin_password = secrets.token_urlsafe(12)
                print(f"AVISO: ADMIN_PASSWORD nao definida. Senha temporaria gerada: {admin_password}")
                print("Defina ADMIN_PASSWORD no ambiente para uma senha persistente.")
            admin = User(
                username='admin',
                name='Administrador',
                role='admin'
            )
            admin.set_password(admin_password)
            db_session.add(admin)
            db_session.commit()
            print("Usuario admin criado com sucesso!")
        elif admin_password:
            admin.set_password(admin_password)
            db_session.commit()
            print("Senha do admin atualizada via ADMIN_PASSWORD.")
        
        neusa_password = os.environ.get('NEUSA_PASSWORD')
        neusa = db_session.query(User).filter_by(username='Neusa.andrade').first()
        
        if not neusa:
            if neusa_password:
                neusa = User(
                    username='Neusa.andrade',
                    name='Neusa Andrade',
                    role='admin'
                )
                neusa.set_password(neusa_password)
                db_session.add(neusa)
                db_session.commit()
                print("Usuario Neusa.andrade criado com sucesso!")
        elif neusa_password:
            neusa.set_password(neusa_password)
            db_session.commit()
            print("Senha do Neusa.andrade atualizada via NEUSA_PASSWORD.")
    finally:
        db_session.close()

def init_termo_linkage_table():
    engine = get_engine()
    Base.metadata.create_all(engine, tables=[TermoLinkage.__table__])
    db_session = get_session()
    try:
        count = db_session.query(TermoLinkage).count()
        print(f"Tabela termo_linkage: {count} registros.")
    finally:
        db_session.close()

init_users_table()
init_termo_linkage_table()

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
                background: {COLORS['header_bg']};
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
            .navbar.bg-light,
            .navbar.bg-primary-custom {{
                background-color: {COLORS['primary']} !important;
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
    [Input('url', 'pathname'),
     Input('url', 'search')]
)
def display_page(pathname, search):
    if pathname == '/logout':
        return create_login_layout(COLORS)
    
    if pathname == '/login':
        session_expired = search and 'expired=1' in search
        return create_login_layout(COLORS, session_expired=session_expired)
    
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
            login_user(user, remember=False)
            session.permanent = True
            session['login_time'] = datetime.utcnow().isoformat()
            next_url = session.pop('next_url', '/')
            return next_url, '', {'display': 'none'}
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
