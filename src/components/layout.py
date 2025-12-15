import dash_bootstrap_components as dbc
from dash import html, dcc
from src.config import COLORS


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
                    html.I(className='fas fa-heartbeat', style={'fontSize': '3rem', 'color': colors['primary']}),
                    html.H1([
                        html.Span('Dashboard ', style={'color': colors['primary']}),
                        html.Span('SISCAN', style={'color': colors['accent']})
                    ], style={'marginTop': '15px', 'marginBottom': '5px'}),
                    html.P('Sistema de Monitoramento de Mamografia', 
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
                ], className='text-center mt-4')
            ], className='login-card')
        ], className='login-container')
    ])


def create_header(user_name=None):
    user_section = []
    if user_name:
        user_section = [
            html.Div([
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
            ], className='user-info', style={'color': 'white'})
        ]
    
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.I(className='fas fa-heartbeat me-2', style={'color': 'white', 'fontSize': '1.3rem'}),
                        html.Span(
                            "Dashboard",
                            style={'color': 'white', 'fontWeight': '700', 'fontSize': '1.5rem'}
                        ),
                        html.Span(
                            " SISCAN",
                            style={'color': COLORS['accent'], 'fontWeight': '700', 'fontSize': '1.5rem'}
                        ),
                        html.Span(
                            " - Monitoramento de Mamografia",
                            style={'color': 'rgba(255,255,255,0.8)', 'fontWeight': '400', 'fontSize': '1rem', 'marginLeft': '10px'}
                        ),
                    ], style={'display': 'flex', 'alignItems': 'center'})
                ], width='auto'),
                dbc.Col(user_section, width='auto', className='ms-auto')
            ], align='center', justify='between', className='w-100')
        ], fluid=True),
        style={
            'backgroundColor': COLORS['header_bg'],
            'boxShadow': '0 2px 4px rgba(0,0,0,0.15)'
        },
        dark=True,
        className='mb-4'
    )


def create_filters(years, health_units, regions, selected_year=None, selected_health_unit=None, 
                   selected_region=None, selected_conformity=None):
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
                ], md=3, sm=6, className='mb-2 mb-md-0'),
                
                dbc.Col([
                    html.Label('Unidade de Saúde', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='health-unit-filter',
                        options=[{'label': u, 'value': u} for u in health_units],
                        value=selected_health_unit,
                        placeholder='Todas as unidades',
                        clearable=True,
                        searchable=True,
                        style={'fontSize': '0.9rem'}
                    )
                ], md=3, sm=6, className='mb-2 mb-md-0'),
                
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
                ], md=3, sm=6, className='mb-2 mb-md-0'),
                
                dbc.Col([
                    html.Label('Status', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='conformity-filter',
                        options=[
                            {'label': 'Dentro do Prazo', 'value': 'Dentro do Prazo'},
                            {'label': 'Fora do Prazo', 'value': 'Fora do Prazo'}
                        ],
                        value=selected_conformity,
                        placeholder='Todos',
                        clearable=True,
                        style={'fontSize': '0.9rem'}
                    )
                ], md=3, sm=6)
            ]),
            
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
                dbc.Col(html.Div(initial_content['table_risk'], id='table-high-risk'), lg=12, className='mb-4')
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
        ])
    ])


def create_outliers_tab(initial_content=None):
    if initial_content and 'outliers_summary' in initial_content:
        return html.Div([
            html.Div([
                html.H5('Resumo de Inconsistências', className='mb-3'),
                html.P('Registros que violam regras de integridade lógica ou limites estatísticos.', 
                       className='text-muted mb-4')
            ]),
            html.Div(initial_content.get('outliers_summary', ''), id='outliers-summary'),
            html.Hr(className='my-4'),
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
        dbc.Row([
            dbc.Col(html.Div(id='outliers-table'), lg=12, className='mb-4')
        ])
    ])


def create_patient_navigation_tab(initial_content=None):
    if initial_content and 'navigation_stats' in initial_content:
        return html.Div([
            html.Div([
                html.H5('Navegação da Paciente', className='mb-3'),
                html.P('Pacientes com múltiplos atendimentos e histórico de exames.', 
                       className='text-muted mb-4')
            ]),
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
                html.I(className='fas fa-link me-2'),
                'Cruzamento de Dados SISCAN x eSaude (Termo Linkage)'
            ], className='mb-3', style={'color': COLORS['primary'], 'fontWeight': '600'}),
            html.P('Visualize e compare dados de pacientes entre sistemas SISCAN e eSaude', 
                   className='text-muted mb-4')
        ]),
        
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
                ], lg=2, md=4, sm=6, className='mb-3')
            ])
        ], className='mb-4 p-3 bg-white rounded shadow-sm'),
        
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


def create_tabs(initial_content=None, sex_options=None, birads_options=None, health_units=None):
    return dbc.Tabs([
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
            label='Unidade de Saúde',
            tab_id='tab-health-unit',
            className='p-3'
        ),
        dbc.Tab(
            create_linkage_tab(initial_content),
            label='Termo Linkage',
            tab_id='tab-linkage',
            className='p-3'
        )
    ], id='main-tabs', active_tab='tab-performance')


def create_footer():
    return html.Footer(
        dbc.Container([
            html.Hr(),
            html.P(
                'SISCAN Dashboard - Sistema de Informação do Câncer',
                className='text-muted text-center mb-0',
                style={'fontSize': '0.85rem'}
            )
        ], fluid=True),
        className='mt-4 pb-3'
    )


def create_main_layout(years, health_units, regions, initial_content=None,
                       selected_year=None, selected_health_unit=None,
                       selected_region=None, selected_conformity=None,
                       sex_options=None, birads_options=None, user_name=None):
    last_update_text = ''
    if initial_content:
        last_update_text = initial_content.get('last_update', '')
    
    return html.Div([
        create_header(user_name=user_name),
        
        dbc.Container([
            create_filters(years, health_units, regions, 
                          selected_year, selected_health_unit, 
                          selected_region, selected_conformity),
            html.Div(last_update_text, id='last-update-display', className='text-muted mb-3', 
                    style={'fontSize': '0.85rem'}),
            create_kpi_row(initial_content),
            create_tabs(initial_content, sex_options, birads_options, health_units),
            create_footer()
        ], fluid=True, className='px-4')
    ], style={'backgroundColor': COLORS['background'], 'minHeight': '100vh'})
