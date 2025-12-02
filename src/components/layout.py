import dash_bootstrap_components as dbc
from dash import html, dcc
from src.config import COLORS


def create_header():
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H4(
                        "SISCAN Dashboard",
                        className='mb-0',
                        style={'color': 'white', 'fontWeight': '600'}
                    ),
                    html.Small(
                        "Sistema de Acompanhamento de Mamografias",
                        className='text-light opacity-75'
                    )
                ])
            ], align='center')
        ], fluid=True),
        color='dark',
        dark=True,
        className='mb-4',
        style={'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}
    )


def create_filters(years, health_units, regions):
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label('Ano', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='year-filter',
                        options=[{'label': str(y), 'value': y} for y in years],
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
                        placeholder='Todas as unidades',
                        clearable=True,
                        searchable=True,
                        style={'fontSize': '0.9rem'}
                    )
                ], md=3, sm=6, className='mb-2 mb-md-0'),
                
                dbc.Col([
                    html.Label('UF', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='region-filter',
                        options=[{'label': r, 'value': r} for r in regions],
                        placeholder='Todos os estados',
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
                        color='primary',
                        size='sm',
                        className='mt-3'
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


def create_kpi_row():
    return dbc.Row([
        dbc.Col(html.Div(id='kpi-mean-wait'), lg=3, md=6, className='mb-3'),
        dbc.Col(html.Div(id='kpi-median-wait'), lg=3, md=6, className='mb-3'),
        dbc.Col(html.Div(id='kpi-conformity'), lg=3, md=6, className='mb-3'),
        dbc.Col(html.Div(id='kpi-high-risk'), lg=3, md=6, className='mb-3'),
    ], className='mb-4')


def create_tabs():
    return dbc.Tabs([
        dbc.Tab(
            create_performance_tab(),
            label='Visão Geral de Performance',
            tab_id='tab-performance',
            className='p-3'
        ),
        dbc.Tab(
            create_audit_tab(),
            label='Auditoria de Risco',
            tab_id='tab-audit',
            className='p-3'
        )
    ], id='main-tabs', active_tab='tab-performance')


def create_performance_tab():
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


def create_audit_tab():
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


def create_main_layout(years, health_units, regions):
    return html.Div([
        dcc.Store(id='data-store'),
        dcc.Interval(id='interval-component', interval=300000, n_intervals=0),
        
        create_header(),
        
        dbc.Container([
            create_filters(years, health_units, regions),
            create_kpi_row(),
            create_tabs(),
            create_footer()
        ], fluid=True, className='px-4')
    ], style={'backgroundColor': COLORS['background'], 'minHeight': '100vh'})
