import dash_bootstrap_components as dbc
from dash import html
from src.config import COLORS


def create_kpi_card(title, value, subtitle=None, icon=None, color='primary', button_id=None, button_text=None):
    color_map = {
        'primary': COLORS['primary'],
        'success': COLORS['success'],
        'warning': COLORS['warning'],
        'danger': COLORS['danger'],
        'info': COLORS['info']
    }
    
    card_color = color_map.get(color, COLORS['primary'])
    
    header_icon = None
    if color == 'danger':
        header_icon = html.I(className='fas fa-exclamation-triangle', 
                            style={'color': COLORS['accent'], 'fontSize': '1.2rem', 'marginRight': '8px'})
    
    card_content = [
        html.Div([
            html.Div([
                header_icon if header_icon else None,
                html.H6(title, className='text-muted mb-2 d-inline', style={'fontSize': '0.85rem'}),
            ], style={'display': 'flex', 'alignItems': 'center'}),
            html.H3(value, className='mb-1', style={'color': card_color, 'fontWeight': '600'}),
        ])
    ]
    
    if subtitle:
        card_content.append(
            html.Small(subtitle, className='text-muted')
        )
    
    if button_id and button_text:
        card_content.append(
            html.Div([
                dbc.Button(
                    [html.I(className='fas fa-file-export me-2'), button_text],
                    id=button_id,
                    color='warning',
                    size='sm',
                    className='mt-2',
                    style={'fontSize': '0.75rem', 'width': '100%'}
                )
            ])
        )
    
    return dbc.Card(
        dbc.CardBody(card_content),
        className='shadow-sm h-100',
        style={
            'borderRadius': '10px',
            'border': 'none',
            'backgroundColor': COLORS['card_bg']
        }
    )


def create_chart_card(title, chart_component, subtitle=None):
    header_content = [
        html.H5(title, className='mb-0', style={'color': COLORS['text'], 'fontWeight': '500'})
    ]
    
    if subtitle:
        header_content.append(
            html.Small(subtitle, className='text-muted d-block mt-1')
        )
    
    return dbc.Card([
        dbc.CardHeader(
            html.Div(header_content),
            style={
                'backgroundColor': COLORS['card_bg'],
                'border': 'none',
                'paddingBottom': '0'
            }
        ),
        dbc.CardBody(chart_component)
    ],
        className='shadow-sm h-100',
        style={
            'borderRadius': '10px',
            'border': 'none',
            'backgroundColor': COLORS['card_bg']
        }
    )


def create_filter_card(filter_components):
    return dbc.Card(
        dbc.CardBody([
            html.H6('Filtros', className='mb-3', style={'color': COLORS['text'], 'fontWeight': '600'}),
            *filter_components
        ]),
        className='shadow-sm mb-4',
        style={
            'borderRadius': '10px',
            'border': 'none',
            'backgroundColor': COLORS['card_bg']
        }
    )
