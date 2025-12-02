import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
from src.config import COLORS, BIRADS_COLORS


def create_high_risk_table(df):
    if df.empty:
        return html.Div(
            html.P('Sem dados de alto risco disponíveis', className='text-muted text-center py-4'),
            className='border rounded'
        )
    
    columns = ['patient_id', 'patient_name', 'health_unit', 'birads_category', 'wait_days', 'conformity_status', 'request_date']
    column_labels = {
        'patient_id': 'ID Paciente',
        'patient_name': 'Nome',
        'health_unit': 'Unidade de Saúde',
        'birads_category': 'BI-RADS',
        'wait_days': 'Dias de Espera',
        'conformity_status': 'Status',
        'request_date': 'Data Solicitação'
    }
    
    available_columns = [col for col in columns if col in df.columns]
    
    header = html.Thead(
        html.Tr([html.Th(column_labels.get(col, col), style={'fontSize': '0.85rem'}) for col in available_columns])
    )
    
    rows = []
    for _, row in df.iterrows():
        cells = []
        for col in available_columns:
            value = row.get(col)
            
            if pd.isna(value):
                cell = html.Td('-')
            elif col == 'birads_category':
                badge_color = BIRADS_COLORS.get(str(value), COLORS['secondary'])
                cell = html.Td(
                    dbc.Badge(f'BI-RADS {value}', style={'backgroundColor': badge_color})
                )
            elif col == 'conformity_status':
                badge_color = 'success' if value == 'Dentro do Prazo' else 'danger'
                cell = html.Td(dbc.Badge(str(value), color=badge_color))
            elif col == 'wait_days':
                try:
                    wait_val = int(float(value))
                    text_color = COLORS['danger'] if wait_val > 30 else COLORS['text']
                    cell = html.Td(
                        html.Span(f'{wait_val} dias', style={'color': text_color, 'fontWeight': '500'})
                    )
                except:
                    cell = html.Td('-')
            elif col == 'request_date':
                cell = html.Td(str(value)[:10] if value else '-')
            elif col == 'patient_name':
                name = str(value)[:30] + '...' if len(str(value)) > 30 else str(value)
                cell = html.Td(name)
            elif col == 'patient_id':
                cell = html.Td(str(value)[:8] + '...')
            else:
                cell = html.Td(str(value))
            
            cells.append(cell)
        rows.append(html.Tr(cells))
    
    body = html.Tbody(rows)
    
    return dbc.Card([
        dbc.CardHeader(
            html.H5('Casos de Alto Risco (BI-RADS 4/5)', className='mb-0', style={'fontWeight': '500'}),
            style={'backgroundColor': COLORS['card_bg'], 'border': 'none'}
        ),
        dbc.CardBody([
            dbc.Table(
                [header, body],
                bordered=True,
                hover=True,
                responsive=True,
                striped=True,
                size='sm',
                className='mb-0'
            )
        ])
    ],
        className='shadow-sm',
        style={
            'borderRadius': '10px',
            'border': 'none',
            'backgroundColor': COLORS['card_bg']
        }
    )
