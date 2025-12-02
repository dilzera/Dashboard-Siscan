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
                    html.Label('UF', className='fw-bold mb-1', style={'fontSize': '0.85rem'}),
                    dcc.Dropdown(
                        id='region-filter',
                        options=[{'label': r, 'value': r} for r in regions],
                        value=selected_region,
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
                        color='primary',
                        size='sm',
                        className='mt-3',
                        n_clicks=0
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


def create_tabs(initial_content=None):
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
                       selected_region=None, selected_conformity=None):
    last_update_text = ''
    if initial_content:
        last_update_text = initial_content.get('last_update', '')
    
    return html.Div([
        create_header(),
        
        dbc.Container([
            create_filters(years, health_units, regions, 
                          selected_year, selected_health_unit, 
                          selected_region, selected_conformity),
            html.Div(last_update_text, id='last-update-display', className='text-muted mb-3', 
                    style={'fontSize': '0.85rem'}),
            create_kpi_row(initial_content),
            create_tabs(initial_content),
            create_footer()
        ], fluid=True, className='px-4')
    ], style={'backgroundColor': COLORS['background'], 'minHeight': '100vh'})
