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


def create_outliers_table(df):
    if df.empty:
        return html.Div(
            html.P('Nenhum outlier identificado', className='text-muted text-center py-4'),
            className='border rounded'
        )
    
    motivo_colors = {
        'A': 'danger',
        'B': 'warning',
        'C': 'info',
        'D': 'secondary'
    }
    
    header = html.Thead(
        html.Tr([
            html.Th('Motivo', style={'fontSize': '0.85rem', 'width': '80px'}),
            html.Th('Nome do Paciente', style={'fontSize': '0.85rem'}),
            html.Th('Cartão SUS', style={'fontSize': '0.85rem'}),
            html.Th('Data Inconsistente', style={'fontSize': '0.85rem'}),
            html.Th('Valor Crítico', style={'fontSize': '0.85rem'}),
            html.Th('Descrição', style={'fontSize': '0.85rem'})
        ])
    )
    
    rows = []
    for _, row in df.iterrows():
        motivo = row.get('motivo_do_outlier', '')
        badge_color = motivo_colors.get(motivo, 'secondary')
        
        nome = str(row.get('nome_paciente', ''))[:35]
        if len(str(row.get('nome_paciente', ''))) > 35:
            nome += '...'
        
        cartao = str(row.get('cartao_sus', ''))
        
        cells = [
            html.Td(dbc.Badge(motivo, color=badge_color, className='fw-bold')),
            html.Td(nome, style={'fontSize': '0.85rem'}),
            html.Td(cartao, style={'fontSize': '0.85rem', 'fontFamily': 'monospace'}),
            html.Td(str(row.get('data_inconsistente', '-')), style={'fontSize': '0.85rem'}),
            html.Td(
                html.Span(str(row.get('valor_critico', '-')), 
                         style={'color': COLORS['danger'], 'fontWeight': '500', 'fontSize': '0.85rem'})
            ),
            html.Td(str(row.get('descricao_motivo', '-')), style={'fontSize': '0.85rem'})
        ]
        rows.append(html.Tr(cells))
    
    body = html.Tbody(rows)
    
    return dbc.Card([
        dbc.CardHeader(
            html.H5('Lista de Outliers para Auditoria', className='mb-0', style={'fontWeight': '500'}),
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


def create_outliers_summary_cards(summary_df):
    if summary_df.empty:
        return html.Div('Nenhum outlier encontrado', className='text-muted')
    
    cards = []
    motivo_icons = {
        'A': 'fas fa-calendar-times',
        'B': 'fas fa-exchange-alt',
        'C': 'fas fa-exclamation-triangle',
        'D': 'fas fa-clock'
    }
    motivo_colors = {
        'A': COLORS['danger'],
        'B': COLORS['warning'],
        'C': COLORS['info'],
        'D': COLORS['secondary']
    }
    
    total_outliers = summary_df['total_registros'].sum()
    
    for _, row in summary_df.iterrows():
        motivo = row.get('motivo_outlier', '')
        descricao = row.get('descricao', '')
        total = row.get('total_registros', 0)
        icon = motivo_icons.get(motivo, 'fas fa-question')
        color = motivo_colors.get(motivo, COLORS['secondary'])
        
        card = dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className=f'{icon} fa-2x', style={'color': color}),
                        html.Span(f' Tipo {motivo}', className='ms-2 fw-bold', style={'fontSize': '1.1rem'})
                    ], className='d-flex align-items-center mb-2'),
                    html.H3(f'{total:,}'.replace(',', '.'), style={'color': color, 'fontWeight': '600'}),
                    html.Small(descricao, className='text-muted')
                ])
            ], className='shadow-sm h-100', style={'borderRadius': '10px', 'border': 'none'})
        ], md=3, sm=6, className='mb-3')
        
        cards.append(card)
    
    total_card = dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className='fas fa-bug fa-2x', style={'color': COLORS['danger']}),
                    html.Span(' Total', className='ms-2 fw-bold', style={'fontSize': '1.1rem'})
                ], className='d-flex align-items-center mb-2'),
                html.H3(f'{total_outliers:,}'.replace(',', '.'), style={'color': COLORS['danger'], 'fontWeight': '600'}),
                html.Small('Total de registros com problemas', className='text-muted')
            ])
        ], className='shadow-sm h-100', style={'borderRadius': '10px', 'border': 'none', 'backgroundColor': '#fff5f5'})
    ], md=3, sm=6, className='mb-3')
    
    return dbc.Row([total_card] + cards)
