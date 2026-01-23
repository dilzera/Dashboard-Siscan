import dash
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from flask import request, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import timedelta, datetime
from src.data_layer import get_years, get_health_units, get_regions, get_sex_options, get_birads_options, create_access_request, get_pending_access_requests, approve_access_request, reject_access_request
from src.components.layout import (
    create_main_layout, create_login_layout, create_access_request_layout,
    create_change_password_layout, create_forgot_password_layout, create_reset_password_layout
)
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
        
        secretaria_password = os.environ.get('SECRETARIA_PASSWORD')
        secretaria = db_session.query(User).filter_by(username='SecretariaDeSaude').first()
        if not secretaria:
            if secretaria_password:
                secretaria = User(
                    username='SecretariaDeSaude',
                    name='Secretaria de Saude',
                    role='admin'
                )
                secretaria.set_password(secretaria_password)
                db_session.add(secretaria)
                db_session.commit()
                print("Usuario SecretariaDeSaude criado com sucesso!")
        elif secretaria_password:
            secretaria.set_password(secretaria_password)
            db_session.commit()
            print("Senha do SecretariaDeSaude atualizada via SECRETARIA_PASSWORD.")
        
        roche_password = os.environ.get('ROCHE_PASSWORD')
        roche = db_session.query(User).filter_by(username='Roche').first()
        if not roche:
            if roche_password:
                roche = User(
                    username='Roche',
                    name='Roche Visualizador',
                    role='viewer'
                )
                roche.set_password(roche_password)
                db_session.add(roche)
                db_session.commit()
                print("Usuario Roche criado com sucesso!")
        elif roche_password:
            roche.set_password(roche_password)
            db_session.commit()
            print("Senha do Roche atualizada via ROCHE_PASSWORD.")
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
    dcc.Store(id='data-masked-store', data=True, storage_type='session'),
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
    
    if pathname == '/solicitar-acesso':
        return create_access_request_layout(COLORS)
    
    if pathname == '/recuperar-senha':
        return create_forgot_password_layout(COLORS)
    
    if pathname and pathname.startswith('/redefinir-senha/'):
        from src.data_layer import validate_reset_token
        token = pathname.replace('/redefinir-senha/', '')
        validation = validate_reset_token(token)
        return create_reset_password_layout(COLORS, token=token, valid=validation.get('valid', False), username=validation.get('username'))
    
    if not current_user.is_authenticated:
        return create_login_layout(COLORS)
    
    if getattr(current_user, 'must_change_password', False):
        return create_change_password_layout(COLORS, user_id=current_user.id, username=current_user.username)
    
    years = get_years()
    health_units = get_health_units()
    regions = get_regions()
    sex_options = get_sex_options()
    birads_options = get_birads_options()
    
    user_access_level = getattr(current_user, 'access_level', 'secretaria') or 'secretaria'
    user_district = getattr(current_user, 'district', None)
    user_health_unit = getattr(current_user, 'health_unit', None)
    
    if user_access_level == 'distrito' and user_district:
        from src.data_layer import get_units_by_district
        health_units = get_units_by_district(user_district)
        regions = [user_district]
    elif user_access_level == 'unidade' and user_health_unit:
        health_units = [user_health_unit]
        from src.data_layer import get_district_for_unit
        district = get_district_for_unit(user_health_unit)
        regions = [district] if district else []
    
    initial_content = build_dashboard_content(
        health_unit=user_health_unit if user_access_level == 'unidade' else None,
        region=user_district if user_access_level == 'distrito' else None
    )
    
    return create_main_layout(
        years, 
        health_units, 
        regions, 
        initial_content,
        sex_options=sex_options,
        birads_options=birads_options,
        user_name=current_user.name if current_user.is_authenticated else None,
        user_access_level=user_access_level,
        user_district=user_district,
        user_health_unit=user_health_unit
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

@app.callback(
    Output('unmask-modal', 'is_open'),
    [Input('toggle-mask-btn', 'n_clicks'),
     Input('unmask-cancel-btn', 'n_clicks'),
     Input('unmask-confirm-btn', 'n_clicks')],
    [State('unmask-modal', 'is_open'),
     State('data-masked-store', 'data')],
    prevent_initial_call=True
)
def toggle_unmask_modal(toggle_clicks, cancel_clicks, confirm_clicks, is_open, is_masked):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'toggle-mask-btn':
        if is_masked:
            return True
        else:
            return False
    elif trigger_id in ['unmask-cancel-btn', 'unmask-confirm-btn']:
        return False
    
    return dash.no_update

@app.callback(
    [Output('data-masked-store', 'data'),
     Output('unmask-error-msg', 'children'),
     Output('toggle-mask-btn', 'color'),
     Output('toggle-mask-btn', 'title'),
     Output('toggle-mask-btn', 'children')],
    [Input('unmask-confirm-btn', 'n_clicks'),
     Input('toggle-mask-btn', 'n_clicks')],
    [State('unmask-password-input', 'value'),
     State('data-masked-store', 'data')],
    prevent_initial_call=True
)
def handle_unmask(confirm_clicks, toggle_clicks, password, is_masked):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'toggle-mask-btn' and not is_masked:
        return True, '', 'warning', 'Dados mascarados - Clique para desmascarar', [html.I(className='fas fa-eye-slash')]
    
    if trigger_id == 'unmask-confirm-btn':
        if not password:
            return dash.no_update, 'Por favor, insira a senha.', dash.no_update, dash.no_update, dash.no_update
        
        db_session = get_session()
        try:
            authorized_users = db_session.query(User).filter(
                User.is_active == True,
                (User.role == 'admin') | (User.access_level.in_(['secretaria', 'distrito']))
            ).all()
            password_valid = False
            for user in authorized_users:
                if user.check_password(password):
                    password_valid = True
                    break
            
            if password_valid:
                return False, '', 'success', 'Dados visíveis - Clique para mascarar', [html.I(className='fas fa-eye')]
            else:
                return dash.no_update, 'Senha incorreta ou usuário sem permissão.', dash.no_update, dash.no_update, dash.no_update
        finally:
            db_session.close()
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('request-access-btn', 'n_clicks'),
    prevent_initial_call=True
)
def go_to_access_request(n_clicks):
    if n_clicks:
        return '/solicitar-acesso'
    return dash.no_update


@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('back-to-login-btn', 'n_clicks'),
    prevent_initial_call=True
)
def go_back_to_login(n_clicks):
    if n_clicks:
        return '/login'
    return dash.no_update


@app.callback(
    [Output('req-district-div', 'style'),
     Output('req-health-unit-div', 'style')],
    Input('req-access-level', 'value')
)
def toggle_access_level_fields(access_level):
    if access_level == 'secretaria':
        return {'display': 'none'}, {'display': 'none'}
    elif access_level == 'distrito':
        return {'display': 'block'}, {'display': 'none'}
    else:
        return {'display': 'none'}, {'display': 'block'}


@app.callback(
    Output('access-request-message', 'children'),
    Input('submit-access-request-btn', 'n_clicks'),
    [State('req-name', 'value'),
     State('req-email', 'value'),
     State('req-phone', 'value'),
     State('req-cpf', 'value'),
     State('req-matricula', 'value'),
     State('req-username', 'value'),
     State('req-access-level', 'value'),
     State('req-district', 'value'),
     State('req-health-unit', 'value'),
     State('req-justification', 'value')],
    prevent_initial_call=True
)
def submit_access_request(n_clicks, name, email, phone, cpf, matricula, username, access_level, district, health_unit, justification):
    if not n_clicks:
        return dash.no_update
    
    if not name or not email or not cpf or not matricula or not username:
        return dbc.Alert('Por favor, preencha todos os campos obrigatórios.', color='danger')
    
    if access_level == 'distrito' and not district:
        return dbc.Alert('Por favor, selecione o distrito sanitário.', color='danger')
    
    if access_level == 'unidade' and not health_unit:
        return dbc.Alert('Por favor, selecione a unidade de saúde.', color='danger')
    
    result = create_access_request(
        name=name,
        email=email,
        phone=phone,
        cpf=cpf,
        matricula=matricula,
        username=username,
        access_level=access_level,
        district=district if access_level in ('distrito', 'unidade') else None,
        health_unit=health_unit if access_level == 'unidade' else None,
        justification=justification
    )
    
    if result['success']:
        return dbc.Alert([
            html.I(className='fas fa-check-circle me-2'),
            result['message']
        ], color='success')
    else:
        return dbc.Alert([
            html.I(className='fas fa-exclamation-circle me-2'),
            result['message']
        ], color='danger')


@app.callback(
    [Output('change-password-message', 'children'),
     Output('url', 'pathname', allow_duplicate=True)],
    Input('save-new-password-btn', 'n_clicks'),
    [State('new-password', 'value'),
     State('confirm-new-password', 'value'),
     State('change-password-user-id', 'data')],
    prevent_initial_call=True
)
def save_new_password(n_clicks, new_password, confirm_password, user_id):
    if not n_clicks:
        return dash.no_update, dash.no_update
    
    if not new_password or not confirm_password:
        return dbc.Alert('Por favor, preencha todos os campos.', color='danger'), dash.no_update
    
    if len(new_password) < 8:
        return dbc.Alert('A senha deve ter pelo menos 8 caracteres.', color='danger'), dash.no_update
    
    if new_password != confirm_password:
        return dbc.Alert('As senhas não conferem.', color='danger'), dash.no_update
    
    from src.data_layer import change_password_first_access
    result = change_password_first_access(user_id, new_password)
    
    if result['success']:
        return dbc.Alert([html.I(className='fas fa-check-circle me-2'), 'Senha alterada! Redirecionando...'], color='success'), '/'
    else:
        return dbc.Alert(result['message'], color='danger'), dash.no_update


@app.callback(
    Output('forgot-password-message', 'children'),
    Input('send-reset-email-btn', 'n_clicks'),
    State('forgot-email', 'value'),
    prevent_initial_call=True
)
def send_password_reset(n_clicks, email):
    if not n_clicks:
        return dash.no_update
    
    if not email:
        return dbc.Alert('Por favor, informe seu e-mail.', color='danger')
    
    from src.data_layer import create_password_reset_token
    import os
    
    result = create_password_reset_token(email)
    
    if result['success']:
        reset_url = f"https://{os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')}/redefinir-senha/{result['token']}"
        
        return dbc.Alert([
            html.I(className='fas fa-check-circle me-2'),
            html.Div([
                html.P('Link de recuperação gerado com sucesso!', className='mb-2'),
                html.P([
                    html.Strong('Link: '),
                    html.A(reset_url, href=reset_url, target='_blank', style={'wordBreak': 'break-all'})
                ], style={'fontSize': '0.85rem'}),
                html.Small('Copie este link e envie para o usuário. O link expira em 2 horas.', className='text-muted')
            ])
        ], color='success')
    else:
        return dbc.Alert([
            html.I(className='fas fa-exclamation-circle me-2'),
            result['message']
        ], color='danger')


@app.callback(
    [Output('reset-password-message', 'children'),
     Output('url', 'pathname', allow_duplicate=True)],
    Input('save-reset-password-btn', 'n_clicks'),
    [State('reset-new-password', 'value'),
     State('reset-confirm-password', 'value'),
     State('reset-token-store', 'data')],
    prevent_initial_call=True
)
def save_reset_password(n_clicks, new_password, confirm_password, token):
    if not n_clicks:
        return dash.no_update, dash.no_update
    
    if not new_password or not confirm_password:
        return dbc.Alert('Por favor, preencha todos os campos.', color='danger'), dash.no_update
    
    if len(new_password) < 8:
        return dbc.Alert('A senha deve ter pelo menos 8 caracteres.', color='danger'), dash.no_update
    
    if new_password != confirm_password:
        return dbc.Alert('As senhas não conferem.', color='danger'), dash.no_update
    
    from src.data_layer import reset_password_with_token
    result = reset_password_with_token(token, new_password)
    
    if result['success']:
        return dbc.Alert([html.I(className='fas fa-check-circle me-2'), 'Senha alterada! Redirecionando...'], color='success'), '/login'
    else:
        return dbc.Alert(result['message'], color='danger'), dash.no_update


from src.callbacks import register_callbacks
register_callbacks(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
