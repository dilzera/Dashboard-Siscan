import dash_bootstrap_components as dbc
from dash import html, dcc
from src.config import COLORS
from src.data_layer import get_regions, get_health_units


def create_access_request_layout(colors, regions=None, health_units=None):
    if regions is None:
        regions = get_regions()
    if health_units is None:
        health_units = get_health_units()
    
    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.I(className='fas fa-user-plus', style={'fontSize': '2.5rem', 'color': colors['primary']}),
                    html.H2('Solicitar Acesso', style={'color': colors['primary'], 'marginTop': '15px'}),
                    html.P('Preencha os dados para solicitar acesso ao sistema', 
                           style={'color': colors['text_muted'], 'fontSize': '0.9rem'})
                ], className='text-center mb-4'),
                
                html.Div(id='access-request-message'),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label('Nome Completo *', className='fw-bold'),
                        dbc.Input(id='req-name', type='text', placeholder='Seu nome completo', className='mb-3')
                    ], md=6),
                    dbc.Col([
                        dbc.Label('CPF *', className='fw-bold'),
                        dbc.Input(id='req-cpf', type='text', placeholder='000.000.000-00', className='mb-3', maxLength=14)
                    ], md=6),
                ]),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label('E-mail *', className='fw-bold'),
                        dbc.Input(id='req-email', type='email', placeholder='seu.email@curitiba.pr.gov.br', className='mb-3')
                    ], md=6),
                    dbc.Col([
                        dbc.Label('Telefone', className='fw-bold'),
                        dbc.Input(id='req-phone', type='text', placeholder='(41) 00000-0000', className='mb-3')
                    ], md=6),
                ]),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label('Matrícula Funcional *', className='fw-bold'),
                        dbc.Input(id='req-matricula', type='text', placeholder='Número da matrícula', className='mb-3')
                    ], md=6),
                    dbc.Col([
                        dbc.Label('Nome de Usuário Desejado *', className='fw-bold'),
                        dbc.Input(id='req-username', type='text', placeholder='usuario.desejado', className='mb-3')
                    ], md=6),
                ]),
                
                html.Hr(style={'margin': '20px 0'}),
                
                html.H5('Tipo de Acesso', className='fw-bold mb-3'),
                
                dbc.RadioItems(
                    id='req-access-level',
                    options=[
                        {'label': html.Span([html.I(className='fas fa-building me-2'), 'Secretaria de Saúde - Acesso completo a todos os dados'], style={'fontSize': '0.9rem'}), 'value': 'secretaria'},
                        {'label': html.Span([html.I(className='fas fa-map-marker-alt me-2'), 'Gestor de Distrito - Acesso aos dados do distrito'], style={'fontSize': '0.9rem'}), 'value': 'distrito'},
                        {'label': html.Span([html.I(className='fas fa-hospital me-2'), 'Unidade de Saúde/Prestador - Acesso aos dados da unidade'], style={'fontSize': '0.9rem'}), 'value': 'unidade'},
                    ],
                    value='unidade',
                    className='mb-3'
                ),
                
                html.Div([
                    dbc.Label('Distrito Sanitário *', className='fw-bold'),
                    dcc.Dropdown(
                        id='req-district',
                        options=[{'label': r, 'value': r} for r in regions],
                        placeholder='Selecione o distrito',
                        className='mb-3'
                    )
                ], id='req-district-div', style={'display': 'none'}),
                
                html.Div([
                    dbc.Label('Unidade de Saúde/Prestador *', className='fw-bold'),
                    dcc.Dropdown(
                        id='req-health-unit',
                        options=[{'label': u, 'value': u} for u in health_units],
                        placeholder='Selecione a unidade de saúde',
                        className='mb-3'
                    )
                ], id='req-health-unit-div', style={'display': 'none'}),
                
                dbc.Label('Justificativa (opcional)', className='fw-bold'),
                dbc.Textarea(id='req-justification', placeholder='Descreva o motivo da solicitação de acesso...', className='mb-4', rows=3),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [html.I(className='fas fa-arrow-left me-2'), 'Voltar'],
                            id='back-to-login-btn',
                            color='secondary',
                            outline=True,
                            className='w-100'
                        )
                    ], md=6),
                    dbc.Col([
                        dbc.Button(
                            [html.I(className='fas fa-paper-plane me-2'), 'Enviar Solicitação'],
                            id='submit-access-request-btn',
                            color='primary',
                            className='w-100'
                        )
                    ], md=6),
                ])
            ], className='p-4', style={
                'backgroundColor': 'white',
                'borderRadius': '10px',
                'boxShadow': '0 4px 20px rgba(0,0,0,0.1)',
                'maxWidth': '700px',
                'width': '100%'
            })
        ], style={
            'display': 'flex',
            'justifyContent': 'center',
            'alignItems': 'center',
            'minHeight': '100vh',
            'backgroundColor': colors['background'],
            'padding': '20px'
        })
    ])


def create_login_layout(colors, session_expired=False):
    expired_message = []
    if session_expired:
        expired_message = [
            dbc.Alert([
                html.I(className='fas fa-clock me-2'),
                'Sua sessão expirou por segurança. Por favor, faça login novamente.'
            ], color='warning', className='mb-3', style={'fontSize': '0.9rem'})
        ]
    
    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.I(className='fas fa-ribbon', style={'fontSize': '3rem', 'color': '#ff69b4'}),
                    html.H1([
                        html.Span('Central Inteligente', style={'color': colors['primary'], 'fontSize': '1.6rem'}),
                    ], style={'marginTop': '15px', 'marginBottom': '0px'}),
                    html.H2([
                        html.Span('de Câncer de Mama', style={'color': colors['text'], 'fontSize': '1.2rem', 'fontWeight': '400'}),
                    ], style={'marginBottom': '5px'}),
                    html.P('Secretaria Municipal de Saúde - Curitiba', 
                           style={'color': colors['text_muted'], 'fontSize': '0.95rem'})
                ], className='login-logo'),
                
                html.Hr(style={'margin': '20px 0'}),
                
                *expired_message,
                
                html.Div([
                    dbc.Label('Usuário', className='fw-bold'),
                    dbc.Input(
                        id='login-username',
                        type='text',
                        placeholder='Digite seu usuário',
                        className='mb-3',
                        style={'borderRadius': '5px'}
                    ),
                    
                    dbc.Label('Senha', className='fw-bold'),
                    dbc.Input(
                        id='login-password',
                        type='password',
                        placeholder='Digite sua senha',
                        className='mb-3',
                        style={'borderRadius': '5px'}
                    ),
                    
                    html.Div(id='login-error', style={'display': 'none'}),
                    
                    dbc.Button(
                        [html.I(className='fas fa-sign-in-alt me-2'), 'Entrar'],
                        id='login-button',
                        color='primary',
                        className='w-100 mt-3',
                        style={
                            'backgroundColor': colors['primary'],
                            'borderColor': colors['primary'],
                            'padding': '12px',
                            'fontSize': '1.1rem',
                            'fontWeight': '600',
                            'borderRadius': '5px'
                        }
                    )
                ]),
                
                html.Div([
                    html.I(className='fas fa-shield-alt me-2', style={'color': colors['secondary']}),
                    html.Span('Sessão expira automaticamente após 1 hora', 
                             style={'color': colors['text_muted'], 'fontSize': '0.85rem'})
                ], className='text-center mt-4'),
                
                html.Div([
                    dcc.Link(
                        'Esqueci minha senha',
                        id='forgot-password-link',
                        href='/recuperar-senha',
                        style={'color': colors['primary'], 'fontSize': '0.85rem', 'textDecoration': 'none', 'cursor': 'pointer'}
                    )
                ], className='text-center mt-2'),
                
                html.Hr(style={'margin': '20px 0'}),
                
                html.Div([
                    html.P('Ainda não tem acesso?', style={'color': colors['text_muted'], 'fontSize': '0.9rem', 'marginBottom': '10px'}),
                    dbc.Button(
                        [html.I(className='fas fa-user-plus me-2'), 'Solicitar Acesso'],
                        id='request-access-btn',
                        color='secondary',
                        outline=True,
                        className='w-100',
                        style={'borderRadius': '5px'}
                    )
                ], className='text-center')
            ], className='login-card')
        ], className='login-container')
    ])


def create_change_password_layout(colors, user_id=None, username=None):
    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.I(className='fas fa-key', style={'fontSize': '2.5rem', 'color': colors['primary']}),
                    html.H2('Alterar Senha', style={'color': colors['primary'], 'marginTop': '15px'}),
                    html.P('Sua senha é temporária. Por favor, defina uma nova senha para continuar.', 
                           style={'color': colors['text_muted'], 'fontSize': '0.9rem'})
                ], className='text-center mb-4'),
                
                html.Div(id='change-password-message'),
                
                dcc.Store(id='change-password-user-id', data=user_id),
                
                dbc.Label('Nova Senha *', className='fw-bold'),
                dbc.Input(id='new-password', type='password', placeholder='Digite a nova senha', className='mb-3'),
                
                dbc.Label('Confirmar Nova Senha *', className='fw-bold'),
                dbc.Input(id='confirm-new-password', type='password', placeholder='Confirme a nova senha', className='mb-3'),
                
                html.Small([
                    html.I(className='fas fa-info-circle me-1'),
                    'A senha deve ter pelo menos 8 caracteres'
                ], style={'color': colors['text_muted'], 'fontSize': '0.8rem'}),
                
                dbc.Button(
                    [html.I(className='fas fa-save me-2'), 'Salvar Nova Senha'],
                    id='save-new-password-btn',
                    color='primary',
                    className='w-100 mt-4',
                    style={
                        'backgroundColor': colors['primary'],
                        'borderColor': colors['primary'],
                        'padding': '12px',
                        'fontSize': '1rem',
                        'fontWeight': '600',
                        'borderRadius': '5px'
                    }
                )
            ], className='login-card')
        ], className='login-container')
    ])


def create_forgot_password_layout(colors):
    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.I(className='fas fa-unlock-alt', style={'fontSize': '2.5rem', 'color': colors['primary']}),
                    html.H2('Recuperar Senha', style={'color': colors['primary'], 'marginTop': '15px'}),
                    html.P('Informe seu e-mail cadastrado para receber as instruções de recuperação.', 
                           style={'color': colors['text_muted'], 'fontSize': '0.9rem'})
                ], className='text-center mb-4'),
                
                html.Div(id='forgot-password-message'),
                
                dbc.Label('E-mail Cadastrado *', className='fw-bold'),
                dbc.Input(id='forgot-email', type='email', placeholder='seu.email@curitiba.pr.gov.br', className='mb-3'),
                
                dbc.Button(
                    [html.I(className='fas fa-paper-plane me-2'), 'Enviar'],
                    id='send-reset-email-btn',
                    color='primary',
                    className='w-100 mt-3',
                    style={
                        'backgroundColor': colors['primary'],
                        'borderColor': colors['primary'],
                        'padding': '12px',
                        'fontSize': '1rem',
                        'fontWeight': '600',
                        'borderRadius': '5px'
                    }
                ),
                
                html.Hr(style={'margin': '20px 0'}),
                
                dbc.Button(
                    [html.I(className='fas fa-arrow-left me-2'), 'Voltar ao Login'],
                    id='back-to-login-from-forgot-btn',
                    color='secondary',
                    outline=True,
                    className='w-100',
                    href='/login',
                    style={'borderRadius': '5px'}
                )
            ], className='login-card')
        ], className='login-container')
    ])


def create_reset_password_layout(colors, token=None, valid=False, username=None):
    if not valid:
        return html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.I(className='fas fa-exclamation-triangle', style={'fontSize': '2.5rem', 'color': '#dc3545'}),
                        html.H2('Link Inválido', style={'color': '#dc3545', 'marginTop': '15px'}),
                        html.P('Este link de recuperação de senha é inválido ou expirou.', 
                               style={'color': colors['text_muted'], 'fontSize': '0.9rem'})
                    ], className='text-center mb-4'),
                    
                    dbc.Button(
                        [html.I(className='fas fa-arrow-left me-2'), 'Voltar ao Login'],
                        color='secondary',
                        outline=True,
                        className='w-100',
                        href='/login',
                        style={'borderRadius': '5px'}
                    )
                ], className='login-card')
            ], className='login-container')
        ])
    
    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.I(className='fas fa-key', style={'fontSize': '2.5rem', 'color': colors['primary']}),
                    html.H2('Nova Senha', style={'color': colors['primary'], 'marginTop': '15px'}),
                    html.P(f'Defina uma nova senha para {username}', 
                           style={'color': colors['text_muted'], 'fontSize': '0.9rem'})
                ], className='text-center mb-4'),
                
                html.Div(id='reset-password-message'),
                
                dcc.Store(id='reset-token-store', data=token),
                
                dbc.Label('Nova Senha *', className='fw-bold'),
                dbc.Input(id='reset-new-password', type='password', placeholder='Digite a nova senha', className='mb-3'),
                
                dbc.Label('Confirmar Nova Senha *', className='fw-bold'),
                dbc.Input(id='reset-confirm-password', type='password', placeholder='Confirme a nova senha', className='mb-3'),
                
                dbc.Button(
                    [html.I(className='fas fa-save me-2'), 'Salvar Nova Senha'],
                    id='save-reset-password-btn',
                    color='primary',
                    className='w-100 mt-3',
                    style={
                        'backgroundColor': colors['primary'],
                        'borderColor': colors['primary'],
                        'padding': '12px',
                        'fontSize': '1rem',
                        'fontWeight': '600',
                        'borderRadius': '5px'
                    }
                )
            ], className='login-card')
        ], className='login-container')
    ])


def create_header(user_name=None):
    user_section = []
    if user_name:
        user_section = [
            html.Div([
                dbc.Button(
                    [html.I(className='fas fa-eye-slash', id='mask-icon')],
                    id='toggle-mask-btn',
                    size='sm',
                    outline=True,
                    color='warning',
                    className='me-3',
                    style={'borderRadius': '20px'},
                    title='Dados mascarados - Clique para desmascarar'
                ),
                html.I(className='fas fa-user-circle me-2', style={'fontSize': '1.2rem'}),
                html.Span(user_name, className='user-badge'),
                dbc.Button(
                    [html.I(className='fas fa-sign-out-alt me-1'), 'Sair'],
                    id='logout-button',
                    size='sm',
                    outline=True,
                    color='light',
                    className='ms-3',
                    style={'borderRadius': '20px'}
                )
            ], className='user-info', style={'color': 'white', 'display': 'flex', 'alignItems': 'center'})
        ]
    
    mask_modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([
            html.I(className='fas fa-lock me-2'),
            'Desmascarar Dados'
        ])),
        dbc.ModalBody([
            html.P('Para visualizar os dados sensíveis dos pacientes, insira a senha de administrador:', className='mb-3'),
            dbc.Input(
                id='unmask-password-input',
                type='password',
                placeholder='Senha de administrador...',
                className='mb-2'
            ),
            html.Div(id='unmask-error-msg', className='text-danger small')
        ]),
        dbc.ModalFooter([
            dbc.Button('Cancelar', id='unmask-cancel-btn', color='secondary', outline=True),
            dbc.Button([html.I(className='fas fa-unlock me-2'), 'Desmascarar'], id='unmask-confirm-btn', color='primary')
        ])
    ], id='unmask-modal', is_open=False, centered=True)
    
    return html.Div([
        dbc.Navbar(
            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.A([
                            html.I(className='fas fa-ribbon me-2', style={'color': '#ff69b4', 'fontSize': '1.3rem'}),
                            html.Span(
                                "Central Inteligente",
                                style={'color': 'white', 'fontWeight': '700', 'fontSize': '1.4rem'}
                            ),
                            html.Span(
                                "de Câncer de Mama",
                                style={'color': 'white', 'fontWeight': '400', 'fontSize': '1.3rem', 'marginLeft': '6px'}
                            ),
                            html.Span(
                                " - CURITIBA",
                                style={'color': '#ff69b4', 'fontWeight': '700', 'fontSize': '1.3rem', 'marginLeft': '5px'}
                            ),
                        ], id='header-title-link', style={'display': 'flex', 'alignItems': 'center', 'cursor': 'pointer', 'textDecoration': 'none'})
                    ], width='auto'),
                    dbc.Col(user_section, width='auto', className='ms-auto')
                ], align='center', justify='between', className='w-100')
            ], fluid=True),
            style={
                'backgroundColor': COLORS['primary'],
                'boxShadow': '0 2px 4px rgba(0,0,0,0.15)'
            },
            dark=True,
            className='mb-4 bg-primary-custom'
        ),
        mask_modal
    ])


def create_filters(years, health_units, regions, selected_year=None, selected_health_unit=None, 
                   selected_region=None, selected_age_range=None, selected_birads=None, selected_priority=None):
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label('Ano', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='year-filter',
                        options=[{'label': str(y), 'value': y} for y in years],
                        value=selected_year,
                        placeholder='Todos os anos',
                        clearable=True,
                        style={'fontSize': '0.9rem'}
                    )
                ], lg=2, md=4, sm=6, className='mb-3 mb-lg-0 pe-lg-3'),
                
                dbc.Col([
                    html.Label('Unidade de Saúde', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='health-unit-filter',
                        options=[{'label': u, 'value': u} for u in health_units],
                        value=selected_health_unit,
                        placeholder='Todas as unidades',
                        clearable=True,
                        searchable=True,
                        optionHeight=45,
                        style={'fontSize': '0.9rem'}
                    )
                ], lg=2, md=4, sm=6, className='mb-3 mb-lg-0 pe-lg-3'),
                
                dbc.Col([
                    html.Label('Distrito Sanitário', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='region-filter',
                        options=[{'label': r, 'value': r} for r in regions],
                        value=selected_region,
                        placeholder='Todos os distritos',
                        clearable=True,
                        style={'fontSize': '0.9rem'}
                    )
                ], lg=2, md=4, sm=6, className='mb-3 mb-lg-0 pe-lg-3'),
                
                dbc.Col([
                    html.Label('Faixa Etária', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='age-range-filter',
                        options=[
                            {'label': 'Menos de 40 anos', 'value': '0-39'},
                            {'label': '40-49 anos', 'value': '40-49'},
                            {'label': '50-69 anos (rastreamento)', 'value': '50-69'},
                            {'label': '70 anos ou mais', 'value': '70+'}
                        ],
                        value=selected_age_range,
                        placeholder='Todas as idades',
                        clearable=True,
                        style={'fontSize': '0.9rem'}
                    )
                ], lg=2, md=4, sm=6, className='mb-3 mb-lg-0 pe-lg-3'),
                
                dbc.Col([
                    html.Label('BI-RADS', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='birads-filter',
                        options=[
                            {'label': html.Span(['● ', 'BI-RADS 0'], style={'color': '#fd7e14'}), 'value': '0'},
                            {'label': html.Span(['● ', 'BI-RADS 1'], style={'color': '#17a2b8'}), 'value': '1'},
                            {'label': html.Span(['● ', 'BI-RADS 2'], style={'color': '#17a2b8'}), 'value': '2'},
                            {'label': html.Span(['● ', 'BI-RADS 3'], style={'color': '#ffc107'}), 'value': '3'},
                            {'label': html.Span(['● ', 'BI-RADS 4'], style={'color': '#dc3545'}), 'value': '4'},
                            {'label': html.Span(['● ', 'BI-RADS 5'], style={'color': '#dc3545'}), 'value': '5'},
                            {'label': html.Span(['● ', 'BI-RADS 6'], style={'color': '#28a745'}), 'value': '6'}
                        ],
                        value=selected_birads,
                        placeholder='Todos',
                        clearable=True,
                        style={'fontSize': '0.9rem'}
                    ),
                    html.Div([
                        html.Small([
                            html.Span('● ', style={'color': '#dc3545'}), 'Suspeito ',
                            html.Span('● ', style={'color': '#fd7e14'}), 'Inconclusivo ',
                            html.Span('● ', style={'color': '#ffc107'}), 'Acompanhar ',
                            html.Span('● ', style={'color': '#28a745'}), 'Tratamento ',
                            html.Span('● ', style={'color': '#17a2b8'}), 'Benigno'
                        ], style={'fontSize': '0.7rem', 'color': '#666'})
                    ], className='mt-1')
                ], lg=2, md=4, sm=6, className='mb-3 mb-lg-0 pe-lg-3'),
                
                dbc.Col([
                    html.Label('Prioridade', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='priority-filter',
                        options=[
                            {'label': html.Span(['● ', 'CRÍTICA (BI-RADS 4/5)'], style={'color': '#dc3545', 'fontWeight': 'bold'}), 'value': 'CRITICA'},
                            {'label': html.Span(['● ', 'ALTA (BI-RADS 0)'], style={'color': '#fd7e14', 'fontWeight': 'bold'}), 'value': 'ALTA'},
                            {'label': html.Span(['● ', 'MÉDIA (BI-RADS 3)'], style={'color': '#ffc107', 'fontWeight': 'bold'}), 'value': 'MEDIA'},
                            {'label': html.Span(['● ', 'MONITORAMENTO (BI-RADS 6)'], style={'color': '#28a745', 'fontWeight': 'bold'}), 'value': 'MONITORAMENTO'},
                            {'label': html.Span(['● ', 'ROTINA (BI-RADS 1/2)'], style={'color': '#17a2b8', 'fontWeight': 'bold'}), 'value': 'ROTINA'}
                        ],
                        value=selected_priority,
                        placeholder='Todas',
                        clearable=True,
                        style={'fontSize': '0.9rem'}
                    )
                ], lg=2, md=4, sm=6, className='mb-3 mb-lg-0')
            ], className='g-3'),
            
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        [html.I(className='fas fa-sync-alt me-2'), 'Atualizar Dados'],
                        id='refresh-btn',
                        size='sm',
                        className='mt-3',
                        n_clicks=0,
                        style={
                            'backgroundColor': COLORS['primary'],
                            'borderColor': COLORS['primary'],
                            'color': 'white'
                        }
                    ),
                    html.Small(
                        id='last-update',
                        className='text-muted ms-3',
                        style={'fontSize': '0.8rem'}
                    )
                ])
            ])
        ])
    ],
        className='shadow-sm mb-4',
        style={
            'borderRadius': '10px',
            'border': 'none',
            'backgroundColor': COLORS['card_bg']
        }
    )


def create_kpi_row(initial_content=None):
    if initial_content:
        return dbc.Row([
            dbc.Col(html.Div(initial_content['kpi_mean'], id='kpi-mean-wait'), lg=3, md=6, className='mb-3'),
            dbc.Col(html.Div(initial_content['kpi_median'], id='kpi-median-wait'), lg=3, md=6, className='mb-3'),
            dbc.Col(html.Div(initial_content['kpi_conformity'], id='kpi-conformity'), lg=3, md=6, className='mb-3'),
            dbc.Col(html.Div(initial_content['kpi_risk'], id='kpi-high-risk'), lg=3, md=6, className='mb-3'),
        ], className='mb-4')
    return dbc.Row([
        dbc.Col(html.Div(id='kpi-mean-wait'), lg=3, md=6, className='mb-3'),
        dbc.Col(html.Div(id='kpi-median-wait'), lg=3, md=6, className='mb-3'),
        dbc.Col(html.Div(id='kpi-conformity'), lg=3, md=6, className='mb-3'),
        dbc.Col(html.Div(id='kpi-high-risk'), lg=3, md=6, className='mb-3'),
    ], className='mb-4')


def create_performance_tab(initial_content=None):
    if initial_content:
        return html.Div([
            dbc.Row([
                dbc.Col(html.Div(initial_content['chart_volume'], id='chart-monthly-volume'), lg=8, className='mb-4'),
                dbc.Col(html.Div(initial_content['gauge_chart'], id='chart-conformity-gauge'), lg=4, className='mb-4')
            ]),
            dbc.Row([
                dbc.Col(html.Div(initial_content['chart_conformity'], id='chart-conformity-by-unit'), lg=12, className='mb-4')
            ])
        ])
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div(id='chart-monthly-volume')
            ], lg=8, className='mb-4'),
            dbc.Col([
                html.Div(id='chart-conformity-gauge')
            ], lg=4, className='mb-4')
        ]),
        dbc.Row([
            dbc.Col([
                html.Div(id='chart-conformity-by-unit')
            ], lg=12, className='mb-4')
        ])
    ])


def create_audit_tab(initial_content=None):
    if initial_content:
        return html.Div([
            dbc.Row([
                dbc.Col(html.Div(initial_content['chart_birads'], id='chart-birads-dist'), lg=6, className='mb-4'),
                dbc.Col(html.Div(initial_content['chart_birads_pie'], id='chart-birads-pie'), lg=6, className='mb-4')
            ]),
            dbc.Row([
                dbc.Col(html.Div(initial_content.get('table_risk', ''), id='table-high-risk'), lg=12, className='mb-4')
            ]),
            dbc.Row([
                dbc.Col(html.Div(initial_content.get('table_other_birads', ''), id='table-other-birads'), lg=12, className='mb-4')
            ])
        ])
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div(id='chart-birads-dist')
            ], lg=6, className='mb-4'),
            dbc.Col([
                html.Div(id='chart-birads-pie')
            ], lg=6, className='mb-4')
        ]),
        dbc.Row([
            dbc.Col([
                html.Div(id='table-high-risk')
            ], lg=12, className='mb-4')
        ]),
        dbc.Row([
            dbc.Col([
                html.Div(id='table-other-birads')
            ], lg=12, className='mb-4')
        ])
    ])


def create_outliers_tab(initial_content=None):
    sort_options = [
        {'label': 'Descrição', 'value': 'descricao_motivo'},
        {'label': 'Motivo', 'value': 'motivo_do_outlier'},
        {'label': 'Nome do Paciente', 'value': 'nome_paciente'},
        {'label': 'Cartão SUS', 'value': 'cartao_sus'},
        {'label': 'Distrito', 'value': 'distrito_saude'},
        {'label': 'Unidade de Saúde', 'value': 'unidade_saude'},
        {'label': 'Data Inconsistente', 'value': 'data_inconsistente'},
        {'label': 'Valor Crítico', 'value': 'valor_critico'}
    ]
    
    sort_controls = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label('Classificar por:', className='fw-bold mb-1', style={'fontSize': '0.9rem'}),
                    dcc.Dropdown(
                        id='outliers-sort-field',
                        options=sort_options,
                        value='descricao_motivo',
                        clearable=False,
                        style={'fontSize': '0.9rem'}
                    )
                ], md=4, sm=6, className='mb-2 mb-md-0'),
                dbc.Col([
                    html.Label('Ordem:', className='fw-bold mb-1', style={'fontSize': '0.9rem'}),
                    dcc.Dropdown(
                        id='outliers-sort-order',
                        options=[
                            {'label': 'Crescente (A-Z)', 'value': 'asc'},
                            {'label': 'Decrescente (Z-A)', 'value': 'desc'}
                        ],
                        value='asc',
                        clearable=False,
                        style={'fontSize': '0.9rem'}
                    )
                ], md=3, sm=6, className='mb-2 mb-md-0'),
                dbc.Col([
                    html.Label('\u00a0', className='fw-bold mb-1', style={'fontSize': '0.9rem'}),
                    dbc.Button(
                        [html.I(className='fas fa-sort me-2'), 'Aplicar Ordenação'],
                        id='outliers-sort-btn',
                        color='primary',
                        className='w-100',
                        size='sm'
                    )
                ], md=3, sm=12)
            ])
        ])
    ], className='mb-3 shadow-sm')
    
    if initial_content and 'outliers_summary' in initial_content:
        return html.Div([
            html.Div([
                html.H5('Resumo de Inconsistências', className='mb-3'),
                html.P('Registros que violam regras de integridade lógica ou limites estatísticos.', 
                       className='text-muted mb-4')
            ]),
            html.Div(initial_content.get('outliers_summary', ''), id='outliers-summary'),
            html.Hr(className='my-4'),
            sort_controls,
            dbc.Row([
                dbc.Col(html.Div(initial_content.get('outliers_table', ''), id='outliers-table'), lg=12, className='mb-4')
            ])
        ])
    return html.Div([
        html.Div([
            html.H5('Resumo de Inconsistências', className='mb-3'),
            html.P('Registros que violam regras de integridade lógica ou limites estatísticos.', 
                   className='text-muted mb-4')
        ]),
        html.Div(id='outliers-summary'),
        html.Hr(className='my-4'),
        sort_controls,
        dbc.Row([
            dbc.Col(html.Div(id='outliers-table'), lg=12, className='mb-4')
        ])
    ])


def create_patient_navigation_tab(initial_content=None):
    evolution_filter = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label('Filtrar por Evolução', className='fw-bold mb-1', style={'fontSize': '0.9rem'}),
                    dcc.Dropdown(
                        id='navigation-evolution-filter',
                        options=[
                            {'label': html.Span([html.I(className='fas fa-arrow-down me-2', style={'color': '#28a745'}), 'Evolução Positiva (BI-RADS diminuiu)'], style={'fontSize': '0.9rem'}), 'value': 'positive'},
                            {'label': html.Span([html.I(className='fas fa-arrow-up me-2', style={'color': '#dc3545'}), 'Evolução Negativa (BI-RADS aumentou)'], style={'fontSize': '0.9rem'}), 'value': 'negative'},
                        ],
                        placeholder='Todos os pacientes',
                        clearable=True,
                        optionHeight=45,
                        style={'fontSize': '0.9rem'}
                    )
                ], md=4, sm=6, className='mb-2'),
                dbc.Col([
                    html.Label('\u00a0', className='d-block mb-1', style={'fontSize': '0.9rem'}),
                    dbc.Button(
                        [html.I(className='fas fa-filter me-2'), 'Aplicar Filtro'],
                        id='navigation-apply-filter-btn',
                        color='primary',
                        style={'backgroundColor': COLORS['primary'], 'borderColor': COLORS['primary']}
                    )
                ], md=2, sm=6, className='mb-2')
            ])
        ], className='p-3')
    ], className='border-0 shadow-sm mb-4')
    
    if initial_content and 'navigation_stats' in initial_content:
        return html.Div([
            html.Div([
                html.H5('Navegação da Paciente', className='mb-3'),
                html.P('Pacientes com múltiplos atendimentos e histórico de exames.', 
                       className='text-muted mb-4')
            ]),
            evolution_filter,
            html.Div(initial_content.get('navigation_stats', ''), id='navigation-stats'),
            html.Hr(className='my-4'),
            dbc.Row([
                dbc.Col(html.Div(initial_content.get('navigation_table', ''), id='navigation-table'), lg=12, className='mb-4')
            ])
        ])
    return html.Div([
        html.Div([
            html.H5('Navegação da Paciente', className='mb-3'),
            html.P('Pacientes com múltiplos atendimentos e histórico de exames.', 
                   className='text-muted mb-4')
        ]),
        evolution_filter,
        html.Div(id='navigation-stats'),
        html.Hr(className='my-4'),
        dbc.Row([
            dbc.Col(html.Div(id='navigation-table'), lg=12, className='mb-4')
        ])
    ])


def create_health_unit_tab(health_units=None, initial_content=None):
    """Create the health unit analysis tab"""
    units = health_units or []
    
    unit_selector = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label('Selecione a Unidade de Saúde', className='fw-bold mb-1', style={'fontSize': '0.9rem'}),
                    dcc.Dropdown(
                        id='unit-analysis-selector',
                        options=[{'label': u, 'value': u} for u in units],
                        placeholder='Selecione uma unidade...',
                        clearable=True,
                        searchable=True,
                        style={'fontSize': '0.9rem'}
                    )
                ], md=8, sm=12, className='mb-2 mb-md-0'),
                
                dbc.Col([
                    html.Label('\u00a0', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dbc.Button(
                        [html.I(className='fas fa-chart-bar me-2'), 'Analisar Unidade'],
                        id='unit-analysis-btn',
                        color='primary',
                        size='sm',
                        className='w-100',
                        n_clicks=0
                    )
                ], md=4, sm=12)
            ])
        ])
    ], className='shadow-sm mb-4', style={'borderRadius': '10px', 'border': 'none'})
    
    return html.Div([
        html.Div([
            html.H5('Análise por Unidade de Saúde', className='mb-3'),
            html.P('Visão detalhada do desempenho de cada unidade de saúde.', 
                   className='text-muted mb-4')
        ]),
        unit_selector,
        
        html.Div(id='unit-kpis', className='mb-4'),
        dcc.Download(id='download-busca-ativa-csv'),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6([
                            html.I(className='fas fa-sort-amount-up me-2'),
                            'Priorização de Atendimento'
                        ], className='mb-0')
                    ], style={'backgroundColor': COLORS['card_bg'], 'border': 'none'}),
                    dbc.CardBody([
                        html.Div(id='unit-priority-summary', className='mb-3'),
                        html.Hr(className='my-3'),
                        html.Div([
                            html.H6([
                                html.I(className='fas fa-list-ol me-2'),
                                'Fila de Priorização'
                            ], className='mb-2'),
                            html.Small('Pacientes ordenados por nível de prioridade e ação recomendada.', className='text-muted mb-3 d-block'),
                            html.Div(id='unit-priority-table')
                        ])
                    ])
                ], className='shadow-sm mb-4', style={'borderRadius': '10px', 'border': 'none'})
            ], lg=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6('Pacientes por Faixa Etária e BI-RADS', className='mb-0')
                    ], style={'backgroundColor': COLORS['card_bg'], 'border': 'none'}),
                    dbc.CardBody([
                        html.Div(id='unit-demographics-chart')
                    ])
                ], className='shadow-sm h-100', style={'borderRadius': '10px', 'border': 'none'})
            ], lg=6, className='mb-4'),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6('Agilidade no Atendimento', className='mb-0')
                    ], style={'backgroundColor': COLORS['card_bg'], 'border': 'none'}),
                    dbc.CardBody([
                        html.Div(id='unit-agility-chart')
                    ])
                ], className='shadow-sm h-100', style={'borderRadius': '10px', 'border': 'none'})
            ], lg=6, className='mb-4')
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6('Tempo Médio de Espera por Mês', className='mb-0')
                    ], style={'backgroundColor': COLORS['card_bg'], 'border': 'none'}),
                    dbc.CardBody([
                        html.Div(id='unit-wait-time-chart')
                    ])
                ], className='shadow-sm', style={'borderRadius': '10px', 'border': 'none'})
            ], lg=12, className='mb-4')
        ]),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        html.H6('Pacientes Sem Retorno', className='mb-1'),
                        html.Small([
                            'Pacientes com BI-RADS 0, 3, 4 ou 5 que não retornaram na data prevista. ',
                            dbc.Badge(id='unit-follow-up-count', color='danger', className='ms-2')
                        ], className='text-muted')
                    ], className='mb-3'),
                    html.Div(id='unit-follow-up-table')
                ])
            ], lg=12, className='mb-4')
        ])
    ])


def create_patient_data_tab(sex_options=None, birads_options=None, initial_content=None):
    sex_opts = sex_options or []
    birads_opts = birads_options or []
    
    filters_row = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label('Buscar por Nome', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dbc.Input(
                        id='patient-data-name-filter',
                        type='text',
                        placeholder='Digite o nome do paciente...',
                        debounce=True,
                        style={'fontSize': '0.9rem'}
                    )
                ], md=4, sm=12, className='mb-2 mb-md-0'),
                
                dbc.Col([
                    html.Label('Sexo', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='patient-data-sex-filter',
                        options=[{'label': s, 'value': s} for s in sex_opts],
                        placeholder='Todos',
                        clearable=True,
                        style={'fontSize': '0.9rem'}
                    )
                ], md=2, sm=6, className='mb-2 mb-md-0'),
                
                dbc.Col([
                    html.Label('BI-RADS', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='patient-data-birads-filter',
                        options=[{'label': f'Categoria {b}', 'value': b} for b in birads_opts],
                        placeholder='Todos',
                        clearable=True,
                        style={'fontSize': '0.9rem'}
                    )
                ], md=2, sm=6, className='mb-2 mb-md-0'),
                
                dbc.Col([
                    html.Label('Registros por página', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='patient-data-page-size',
                        options=[
                            {'label': '25', 'value': 25},
                            {'label': '50', 'value': 50},
                            {'label': '100', 'value': 100}
                        ],
                        value=50,
                        clearable=False,
                        style={'fontSize': '0.9rem'}
                    )
                ], md=2, sm=6, className='mb-2 mb-md-0'),
                
                dbc.Col([
                    html.Label('\u00a0', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dbc.Button(
                        [html.I(className='fas fa-search me-2'), 'Buscar'],
                        id='patient-data-search-btn',
                        color='primary',
                        size='sm',
                        className='w-100',
                        n_clicks=0
                    )
                ], md=2, sm=6)
            ])
        ])
    ], className='shadow-sm mb-4', style={'borderRadius': '10px', 'border': 'none'})
    
    pagination_row = dbc.Row([
        dbc.Col([
            html.Div([
                dbc.Button(
                    html.I(className='fas fa-chevron-left'),
                    id='patient-data-prev-btn',
                    color='secondary',
                    size='sm',
                    className='me-2',
                    disabled=True
                ),
                html.Span(id='patient-data-page-info', className='mx-3', style={'fontSize': '0.9rem'}),
                dbc.Button(
                    html.I(className='fas fa-chevron-right'),
                    id='patient-data-next-btn',
                    color='secondary',
                    size='sm',
                    className='ms-2'
                )
            ], className='d-flex align-items-center justify-content-center my-3')
        ])
    ])
    
    return html.Div([
        html.Div([
            html.H5('Dados do Paciente', className='mb-3'),
            html.P('Listagem completa dos registros de exames com dados clínicos detalhados.', 
                   className='text-muted mb-4')
        ]),
        filters_row,
        html.Div(id='patient-data-count', className='text-muted mb-2', style={'fontSize': '0.85rem'}),
        dcc.Store(id='patient-data-current-page', data=1),
        html.Div(id='patient-data-table', className='mb-3'),
        pagination_row
    ])


def create_indicator_card(title, description, value, percentage=None, icon_class='fas fa-chart-bar', color='primary'):
    """Create a card for an indicator with value and description"""
    percentage_badge = None
    if percentage is not None:
        percentage_badge = html.Span(
            f'{percentage:.1f}%',
            className='badge bg-secondary ms-2',
            style={'fontSize': '0.8rem'}
        )
    
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f'{icon_class} me-2', style={'color': COLORS['primary']}),
                html.H6(title, className='mb-0 d-inline', style={'fontSize': '0.95rem', 'fontWeight': '600'})
            ], className='mb-2'),
            html.Div([
                html.Span(
                    f'{value:,}' if isinstance(value, int) else str(value),
                    style={'fontSize': '1.5rem', 'fontWeight': '700', 'color': COLORS['primary']}
                ),
                percentage_badge
            ]),
            html.P(
                description,
                className='text-muted mb-0 mt-2',
                style={'fontSize': '0.8rem', 'lineHeight': '1.3'}
            )
        ])
    ], className='h-100 shadow-sm', style={'borderLeft': f'4px solid {COLORS["primary"]}'})


def create_time_indicator_card(title, description, media, mediana, icon_class='fas fa-clock'):
    """Create a card for time-based indicators showing average and median"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f'{icon_class} me-2', style={'color': COLORS['primary']}),
                html.H6(title, className='mb-0 d-inline', style={'fontSize': '0.95rem', 'fontWeight': '600'})
            ], className='mb-2'),
            dbc.Row([
                dbc.Col([
                    html.Div('Média', className='text-muted', style={'fontSize': '0.75rem'}),
                    html.Span(
                        f'{media:.1f} dias',
                        style={'fontSize': '1.2rem', 'fontWeight': '700', 'color': COLORS['primary']}
                    )
                ], width=6),
                dbc.Col([
                    html.Div('Mediana', className='text-muted', style={'fontSize': '0.75rem'}),
                    html.Span(
                        f'{mediana:.1f} dias',
                        style={'fontSize': '1.2rem', 'fontWeight': '700', 'color': COLORS['secondary']}
                    )
                ], width=6)
            ]),
            html.P(
                description,
                className='text-muted mb-0 mt-2',
                style={'fontSize': '0.8rem', 'lineHeight': '1.3'}
            )
        ])
    ], className='h-100 shadow-sm', style={'borderLeft': f'4px solid {COLORS["primary"]}'})


def create_indicators_tab(initial_content=None):
    """Create the Indicators tab with all 10 indicators organized in blocks"""
    
    return html.Div([
        html.Div([
            html.H5('Indicadores de Rastreamento e Encaminhamento', className='mb-3'),
            html.P('Indicadores clínicos para monitoramento da cobertura populacional e encaminhamentos.', 
                   className='text-muted mb-4')
        ]),
        
        html.Div([
            html.H6([
                html.I(className='fas fa-users me-2'),
                'Cobertura da População Alvo'
            ], className='mb-3', style={'color': COLORS['primary'], 'fontWeight': '600'}),
            dbc.Row([
                dbc.Col([
                    html.Div(id='indicator-1-card')
                ], lg=6, md=12, className='mb-3'),
                dbc.Col([
                    html.Div(id='indicator-2-charts')
                ], lg=6, md=12, className='mb-3')
            ], className='mb-4')
        ], className='mb-4 p-3 bg-white rounded shadow-sm'),
        
        html.Div([
            html.H6([
                html.I(className='fas fa-clock me-2'),
                'Agilidade no Acesso e Entrega de Resultados'
            ], className='mb-3', style={'color': COLORS['primary'], 'fontWeight': '600'}),
            dbc.Row([
                dbc.Col([
                    html.Div(id='indicator-3-card')
                ], lg=6, md=12, className='mb-3'),
                dbc.Col([
                    html.Div(id='indicator-4-card')
                ], lg=6, md=12, className='mb-3')
            ], className='mb-4')
        ], className='mb-4 p-3 bg-white rounded shadow-sm'),
        
        html.Div([
            html.H6([
                html.I(className='fas fa-directions me-2'),
                'Encaminhamentos por Categoria BI-RADS'
            ], className='mb-3', style={'color': COLORS['primary'], 'fontWeight': '600'}),
            dbc.Row([
                dbc.Col([
                    html.Div(id='indicator-5-card')
                ], lg=4, md=6, className='mb-3'),
                dbc.Col([
                    html.Div(id='indicator-6-card')
                ], lg=4, md=6, className='mb-3'),
                dbc.Col([
                    html.Div(id='indicator-7-card')
                ], lg=4, md=12, className='mb-3')
            ], className='mb-4')
        ], className='mb-4 p-3 bg-white rounded shadow-sm'),
        
        html.Div([
            html.H6([
                html.I(className='fas fa-exclamation-triangle me-2'),
                'Casos Especiais e Fora da Faixa Etária'
            ], className='mb-3', style={'color': COLORS['primary'], 'fontWeight': '600'}),
            dbc.Row([
                dbc.Col([
                    html.Div(id='indicator-8-card')
                ], lg=4, md=6, className='mb-3'),
                dbc.Col([
                    html.Div(id='indicator-9-card')
                ], lg=4, md=6, className='mb-3'),
                dbc.Col([
                    html.Div(id='indicator-10-card')
                ], lg=4, md=12, className='mb-3')
            ], className='mb-4')
        ], className='mb-4 p-3 bg-white rounded shadow-sm')
    ])


def create_linkage_tab(initial_content=None):
    return html.Div([
        html.Div([
            html.H5([
                html.I(className='fas fa-exchange-alt me-2'),
                'Dados de Interoperabilidade SISCAN x eSaude'
            ], className='mb-3', style={'color': COLORS['primary'], 'fontWeight': '600'}),
            html.P('Visualize e compare dados de pacientes entre sistemas SISCAN e eSaude', 
                   className='text-muted mb-4')
        ]),
        
        html.Div([
            html.H6([
                html.I(className='fas fa-search me-2'),
                'Pesquisa de Pacientes'
            ], className='mb-3', style={'color': COLORS['primary'], 'fontWeight': '600'}),
            dbc.Row([
                dbc.Col([
                    dbc.Label('Buscar por Nome', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dbc.Input(
                        id='linkage-search-nome',
                        type='text',
                        placeholder='Digite o nome...',
                        style={'fontSize': '0.9rem'}
                    )
                ], md=4, className='mb-2'),
                dbc.Col([
                    dbc.Label('Buscar por CPF', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dbc.Input(
                        id='linkage-search-cpf',
                        type='text',
                        placeholder='Digite o CPF...',
                        style={'fontSize': '0.9rem'}
                    )
                ], md=3, className='mb-2'),
                dbc.Col([
                    dbc.Label('Buscar por Cartao SUS', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dbc.Input(
                        id='linkage-search-cartao',
                        type='text',
                        placeholder='Digite o Cartao SUS...',
                        style={'fontSize': '0.9rem'}
                    )
                ], md=3, className='mb-2'),
                dbc.Col([
                    dbc.Label('\u00a0', className='d-block mb-1', style={'fontSize': '0.85rem'}),
                    dbc.Button(
                        [html.I(className='fas fa-search me-2'), 'Pesquisar'],
                        id='linkage-search-button',
                        color='primary',
                        className='w-100',
                        style={'backgroundColor': COLORS['primary'], 'borderColor': COLORS['primary']}
                    )
                ], md=2, className='mb-2')
            ])
        ], className='mb-4 p-3 bg-white rounded shadow-sm'),
        
        html.Div([
            html.H6([
                html.I(className='fas fa-database me-2'),
                'Comparação entre Bases de Dados'
            ], className='mb-3', style={'color': COLORS['primary'], 'fontWeight': '600'}),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6('Registros exam_records', className='text-muted mb-1', style={'fontSize': '0.85rem'}),
                            html.H4(id='comparison-exam-records', children='...', style={'color': COLORS['primary'], 'fontWeight': '700'})
                        ], className='text-center p-3')
                    ], className='border-0 shadow-sm')
                ], lg=2, md=4, sm=6, className='mb-3'),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6('Registros termo_linkage', className='text-muted mb-1', style={'fontSize': '0.85rem'}),
                            html.H4(id='comparison-termo-linkage', children='...', style={'color': COLORS['secondary'], 'fontWeight': '700'})
                        ], className='text-center p-3')
                    ], className='border-0 shadow-sm')
                ], lg=2, md=4, sm=6, className='mb-3'),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6('CNS únicos exam_records', className='text-muted mb-1', style={'fontSize': '0.85rem'}),
                            html.H4(id='comparison-unique-exam', children='...', style={'color': COLORS['primary'], 'fontWeight': '700'})
                        ], className='text-center p-3')
                    ], className='border-0 shadow-sm')
                ], lg=2, md=4, sm=6, className='mb-3'),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6('CNS únicos termo_linkage', className='text-muted mb-1', style={'fontSize': '0.85rem'}),
                            html.H4(id='comparison-unique-termo', children='...', style={'color': COLORS['secondary'], 'fontWeight': '700'})
                        ], className='text-center p-3')
                    ], className='border-0 shadow-sm')
                ], lg=2, md=4, sm=6, className='mb-3'),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6('CNS em ambas tabelas', className='text-muted mb-1', style={'fontSize': '0.85rem'}),
                            html.H4(id='comparison-common-cns', children='...', style={'color': COLORS['success'], 'fontWeight': '700'})
                        ], className='text-center p-3')
                    ], className='border-0 shadow-sm', style={'borderLeft': f'3px solid {COLORS["success"]}'})
                ], lg=2, md=4, sm=6, className='mb-3'),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6('CNS só em exam_records', className='text-muted mb-1', style={'fontSize': '0.85rem'}),
                            html.H4(id='comparison-only-exam', children='...', style={'color': COLORS['warning'], 'fontWeight': '700'})
                        ], className='text-center p-3')
                    ], className='border-0 shadow-sm')
                ], lg=2, md=4, sm=6, className='mb-3'),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6('CNS só em termo_linkage', className='text-muted mb-1', style={'fontSize': '0.85rem'}),
                            html.H4(id='comparison-only-termo', children='...', style={'color': COLORS['accent'], 'fontWeight': '700'})
                        ], className='text-center p-3')
                    ], className='border-0 shadow-sm')
                ], lg=2, md=4, sm=6, className='mb-3')
            ])
        ], className='mb-4 p-3 bg-white rounded shadow-sm'),
        
        html.Div([
            html.H6([
                html.I(className='fas fa-chart-pie me-2'),
                'Resumo de Qualidade dos Dados'
            ], className='mb-3', style={'color': COLORS['primary'], 'fontWeight': '600'}),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6('Total de Registros', className='text-muted mb-1', style={'fontSize': '0.85rem'}),
                            html.H4(id='linkage-total', children='...', style={'color': COLORS['primary'], 'fontWeight': '700'})
                        ], className='text-center p-3')
                    ], className='border-0 shadow-sm')
                ], lg=2, md=4, sm=6, className='mb-3'),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6('Com CPF', className='text-muted mb-1', style={'fontSize': '0.85rem'}),
                            html.H4(id='linkage-cpf', children='...', style={'color': COLORS['secondary'], 'fontWeight': '700'})
                        ], className='text-center p-3')
                    ], className='border-0 shadow-sm')
                ], lg=2, md=4, sm=6, className='mb-3'),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6('Com Telefone', className='text-muted mb-1', style={'fontSize': '0.85rem'}),
                            html.H4(id='linkage-telefone', children='...', style={'color': COLORS['secondary'], 'fontWeight': '700'})
                        ], className='text-center p-3')
                    ], className='border-0 shadow-sm')
                ], lg=2, md=4, sm=6, className='mb-3'),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6('Com Nome eSaude', className='text-muted mb-1', style={'fontSize': '0.85rem'}),
                            html.H4(id='linkage-nome-esaude', children='...', style={'color': COLORS['secondary'], 'fontWeight': '700'})
                        ], className='text-center p-3')
                    ], className='border-0 shadow-sm')
                ], lg=2, md=4, sm=6, className='mb-3'),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6('Com APAC Cancer', className='text-muted mb-1', style={'fontSize': '0.85rem'}),
                            html.H4(id='linkage-apac', children='...', style={'color': COLORS['accent'], 'fontWeight': '700'})
                        ], className='text-center p-3')
                    ], className='border-0 shadow-sm')
                ], lg=2, md=4, sm=6, className='mb-3'),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6('Nomes Conferem', className='text-muted mb-1', style={'fontSize': '0.85rem'}),
                            html.H4(id='linkage-nomes-conferem', children='...', style={'color': COLORS['success'], 'fontWeight': '700'})
                        ], className='text-center p-3')
                    ], className='border-0 shadow-sm')
                ], lg=2, md=4, sm=6, className='mb-3'),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6('CNS Duplicados', className='text-muted mb-1', style={'fontSize': '0.85rem'}),
                            html.H4(id='linkage-duplicados', children='...', style={'color': COLORS['warning'], 'fontWeight': '700'})
                        ], className='text-center p-3')
                    ], className='border-0 shadow-sm', style={'borderLeft': f'3px solid {COLORS["warning"]}'})
                ], lg=2, md=4, sm=6, className='mb-3')
            ])
        ], className='mb-4 p-3 bg-white rounded shadow-sm'),
        
        html.Div([
            html.Div([
                html.H6([
                    html.I(className='fas fa-table me-2'),
                    'Dados de Cruzamento'
                ], className='mb-0 d-inline', style={'color': COLORS['primary'], 'fontWeight': '600'}),
                html.Span(id='linkage-count-display', className='ms-3 text-muted', style={'fontSize': '0.85rem'})
            ], className='mb-3'),
            html.Div(id='linkage-table-container', children=[
                html.P('Clique em Pesquisar para ver os dados', className='text-muted text-center p-4')
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Pagination(
                        id='linkage-pagination',
                        max_value=1,
                        active_page=1,
                        first_last=True,
                        previous_next=True,
                        fully_expanded=False,
                        className='mt-3'
                    )
                ], className='d-flex justify-content-center')
            ])
        ], className='mb-4 p-3 bg-white rounded shadow-sm')
    ])


def create_access_management_tab():
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className='fas fa-user-shield me-2'),
                    'Gerenciamento de Acessos'
                ], className='mb-3'),
                html.P('Gerencie as solicitações de acesso ao sistema.', className='text-muted mb-4')
            ])
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    [html.I(className='fas fa-sync-alt me-2'), 'Atualizar Lista'],
                    id='refresh-access-requests-btn',
                    color='primary',
                    size='sm',
                    className='mb-3'
                )
            ])
        ]),
        
        html.Div(id='access-requests-table', children=[
            dbc.Alert('Clique em "Atualizar Lista" para carregar as solicitações pendentes.', color='info')
        ]),
        
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle('Aprovar Solicitação')),
            dbc.ModalBody([
                html.P('Defina uma senha temporária para o novo usuário:'),
                dbc.Input(id='approve-temp-password', type='password', placeholder='Senha temporária'),
                html.Small('O usuário deverá alterar a senha no primeiro acesso.', className='text-muted')
            ]),
            dbc.ModalFooter([
                dbc.Button('Cancelar', id='approve-cancel-btn', color='secondary'),
                dbc.Button('Aprovar', id='approve-confirm-btn', color='success')
            ])
        ], id='approve-modal', is_open=False),
        
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle('Rejeitar Solicitação')),
            dbc.ModalBody([
                html.P('Informe o motivo da rejeição:'),
                dbc.Textarea(id='reject-reason', placeholder='Motivo da rejeição...', rows=3)
            ]),
            dbc.ModalFooter([
                dbc.Button('Cancelar', id='reject-cancel-btn', color='secondary'),
                dbc.Button('Rejeitar', id='reject-confirm-btn', color='danger')
            ])
        ], id='reject-modal', is_open=False),
        
        dcc.Store(id='selected-request-id', data=None)
    ])


def create_tabs(initial_content=None, sex_options=None, birads_options=None, health_units=None, show_access_management=False):
    tabs = [
        dbc.Tab(
            create_performance_tab(initial_content),
            label='Visão Geral de Performance',
            tab_id='tab-performance',
            className='p-3'
        ),
        dbc.Tab(
            create_audit_tab(initial_content),
            label='Auditoria de Risco',
            tab_id='tab-audit',
            className='p-3'
        ),
        dbc.Tab(
            create_outliers_tab(initial_content),
            label='Auditoria de Outliers',
            tab_id='tab-outliers',
            className='p-3'
        ),
        dbc.Tab(
            create_indicators_tab(initial_content),
            label='Indicadores',
            tab_id='tab-indicators',
            className='p-3'
        ),
        dbc.Tab(
            create_patient_navigation_tab(initial_content),
            label='Navegação da Paciente',
            tab_id='tab-navigation',
            className='p-3'
        ),
        dbc.Tab(
            create_patient_data_tab(sex_options, birads_options, initial_content),
            label='Dados do Paciente',
            tab_id='tab-patient-data',
            className='p-3'
        ),
        dbc.Tab(
            create_health_unit_tab(health_units, initial_content),
            label='Unidade de Saúde e Prestador',
            tab_id='tab-health-unit',
            className='p-3'
        ),
        dbc.Tab(
            create_linkage_tab(initial_content),
            label='Dados Interoperabilidade',
            tab_id='tab-linkage',
            className='p-3'
        )
    ]
    
    if show_access_management:
        tabs.append(
            dbc.Tab(
                create_access_management_tab(),
                label='Gerenciar Acessos',
                tab_id='tab-access-management',
                className='p-3'
            )
        )
    
    return dbc.Tabs(tabs, id='main-tabs', active_tab='tab-performance')


def create_footer():
    return html.Footer(
        dbc.Container([
            html.Hr(),
            html.P(
                'Central Inteligente de Câncer de Mama - Secretaria Municipal de Saúde de Curitiba',
                className='text-muted text-center mb-0',
                style={'fontSize': '0.85rem'}
            )
        ], fluid=True),
        className='mt-4 pb-3'
    )


def create_main_layout(years, health_units, regions, initial_content=None,
                       selected_year=None, selected_health_unit=None,
                       selected_region=None, selected_conformity=None,
                       sex_options=None, birads_options=None, user_name=None,
                       user_access_level=None, user_district=None, user_health_unit=None):
    last_update_text = ''
    if initial_content:
        last_update_text = initial_content.get('last_update', '')
    
    show_access_management = user_access_level in ('secretaria', 'distrito')
    
    return html.Div([
        create_header(user_name=user_name),
        
        dbc.Container([
            create_filters(years, health_units, regions, 
                          selected_year, selected_health_unit, 
                          selected_region, selected_conformity),
            html.Div(last_update_text, id='last-update-display', className='text-muted mb-3', 
                    style={'fontSize': '0.85rem'}),
            create_kpi_row(initial_content),
            create_tabs(initial_content, sex_options, birads_options, health_units, show_access_management=show_access_management),
            create_footer()
        ], fluid=True, className='px-4'),
        
        dcc.Store(id='user-access-level-store', data=user_access_level),
        dcc.Store(id='user-district-store', data=user_district),
        dcc.Store(id='user-health-unit-store', data=user_health_unit)
    ], style={'backgroundColor': COLORS['background'], 'minHeight': '100vh'})
