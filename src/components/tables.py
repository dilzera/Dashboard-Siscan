import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
from src.config import COLORS, BIRADS_COLORS


def mask_name(name, is_masked=True):
    """Mascara nome do paciente mantendo apenas iniciais"""
    if not name or not is_masked:
        return name if name else '-'
    name_str = str(name)
    if len(name_str) < 3:
        return '***'
    parts = name_str.split()
    if len(parts) > 1:
        return f"{parts[0][0]}****** {parts[-1][0]}******"
    return f"{name_str[0]}******"


def mask_cns(cns, is_masked=True):
    """Mascara Cartão SUS mostrando apenas últimos 4 dígitos"""
    if not cns or not is_masked:
        return str(cns) if cns else '-'
    cns_str = str(cns)
    if len(cns_str) <= 4:
        return '****'
    return f"{'*' * (len(cns_str) - 4)}{cns_str[-4:]}"


def mask_cpf(cpf, is_masked=True):
    """Mascara CPF mostrando apenas últimos 2 dígitos"""
    if not cpf or not is_masked:
        return cpf if cpf else '-'
    cpf_str = str(cpf)
    if len(cpf_str) <= 2:
        return '***'
    return f"***.***.**{cpf_str[-2:]}"


def mask_phone(phone, is_masked=True):
    """Mascara telefone mostrando apenas últimos 4 dígitos"""
    if not phone or not is_masked:
        return phone if phone else '-'
    phone_str = str(phone)
    if len(phone_str) <= 4:
        return '****'
    return f"{'*' * (len(phone_str) - 4)}{phone_str[-4:]}"


def create_high_risk_table(df, is_masked=True):
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
                name = mask_name(value, is_masked)
                cell = html.Td(name)
            elif col == 'patient_id':
                cell = html.Td(mask_cns(value, is_masked))
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


def create_outliers_table(df, is_masked=True):
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
            html.Th('Motivo', style={'fontSize': '0.85rem', 'width': '60px'}),
            html.Th('Nome do Paciente', style={'fontSize': '0.85rem'}),
            html.Th('Cartão SUS', style={'fontSize': '0.85rem'}),
            html.Th('Distrito', style={'fontSize': '0.85rem'}),
            html.Th('Unidade de Saúde', style={'fontSize': '0.85rem'}),
            html.Th('Data Inconsistente', style={'fontSize': '0.85rem'}),
            html.Th('Valor Crítico', style={'fontSize': '0.85rem'}),
            html.Th('Descrição', style={'fontSize': '0.85rem'})
        ])
    )
    
    rows = []
    for _, row in df.iterrows():
        motivo = row.get('motivo_do_outlier', '')
        badge_color = motivo_colors.get(motivo, 'secondary')
        
        nome = mask_name(row.get('nome_paciente', ''), is_masked)
        
        cartao = mask_cns(row.get('cartao_sus', ''), is_masked)
        
        distrito = str(row.get('distrito_saude', '-'))[:20]
        if len(str(row.get('distrito_saude', ''))) > 20:
            distrito += '...'
        
        unidade = str(row.get('unidade_saude', '-'))[:25]
        if len(str(row.get('unidade_saude', ''))) > 25:
            unidade += '...'
        
        cells = [
            html.Td(dbc.Badge(motivo, color=badge_color, className='fw-bold')),
            html.Td(nome, style={'fontSize': '0.85rem'}),
            html.Td(cartao, style={'fontSize': '0.85rem', 'fontFamily': 'monospace'}),
            html.Td(distrito, style={'fontSize': '0.85rem'}),
            html.Td(unidade, style={'fontSize': '0.85rem'}),
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


def create_patient_navigation_stats_cards(stats):
    if not stats:
        return html.Div('Nenhum dado disponível', className='text-muted')
    
    cards = []
    
    cards.append(dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className='fas fa-users fa-2x', style={'color': COLORS['primary']}),
                    html.Span(' Pacientes', className='ms-2 fw-bold', style={'fontSize': '1.1rem'})
                ], className='d-flex align-items-center mb-2'),
                html.H3(f'{stats["pacientes_multiplos_exames"]:,}'.replace(',', '.'), 
                       style={'color': COLORS['primary'], 'fontWeight': '600'}),
                html.Small('Com múltiplos atendimentos', className='text-muted')
            ])
        ], className='shadow-sm h-100', style={'borderRadius': '10px', 'border': 'none'})
    ], md=3, sm=6, className='mb-3'))
    
    cards.append(dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className='fas fa-file-medical fa-2x', style={'color': COLORS['info']}),
                    html.Span(' Exames', className='ms-2 fw-bold', style={'fontSize': '1.1rem'})
                ], className='d-flex align-items-center mb-2'),
                html.H3(f'{stats["total_exames_multiplos"]:,}'.replace(',', '.'), 
                       style={'color': COLORS['info'], 'fontWeight': '600'}),
                html.Small('Total de exames dessas pacientes', className='text-muted')
            ])
        ], className='shadow-sm h-100', style={'borderRadius': '10px', 'border': 'none'})
    ], md=3, sm=6, className='mb-3'))
    
    cards.append(dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className='fas fa-chart-line fa-2x', style={'color': COLORS['success']}),
                    html.Span(' Média', className='ms-2 fw-bold', style={'fontSize': '1.1rem'})
                ], className='d-flex align-items-center mb-2'),
                html.H3(f'{stats["media_exames_por_paciente"]:.1f}', 
                       style={'color': COLORS['success'], 'fontWeight': '600'}),
                html.Small('Exames por paciente', className='text-muted')
            ])
        ], className='shadow-sm h-100', style={'borderRadius': '10px', 'border': 'none'})
    ], md=3, sm=6, className='mb-3'))
    
    cards.append(dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className='fas fa-trophy fa-2x', style={'color': COLORS['warning']}),
                    html.Span(' Máximo', className='ms-2 fw-bold', style={'fontSize': '1.1rem'})
                ], className='d-flex align-items-center mb-2'),
                html.H3(f'{stats["max_exames_paciente"]}', 
                       style={'color': COLORS['warning'], 'fontWeight': '600'}),
                html.Small('Maior número de atendimentos', className='text-muted')
            ])
        ], className='shadow-sm h-100', style={'borderRadius': '10px', 'border': 'none'})
    ], md=3, sm=6, className='mb-3'))
    
    return dbc.Row(cards)


def create_patient_navigation_table(df, is_masked=True):
    if df.empty:
        return html.Div(
            html.P('Nenhuma paciente com múltiplos atendimentos encontrada', className='text-muted text-center py-4'),
            className='border rounded'
        )
    
    grouped = df.groupby('patient_unique_id')
    
    accordion_items = []
    
    patient_count = 0
    for patient_id, group in grouped:
        if patient_count >= 50:
            break
        patient_count += 1
        
        first_row = group.iloc[0]
        nome = mask_name(first_row.get('nome_paciente', ''), is_masked)
        cartao_sus = mask_cns(first_row.get('cartao_sus', ''), is_masked)
        total_exames = first_row.get('total_exames', len(group))
        
        exams_rows = []
        first_birads = group.iloc[0].get('first_birads', 0)
        last_birads = group.iloc[0].get('last_birads', 0)
        evolucao_positiva = first_birads > last_birads if first_birads and last_birads else False
        
        for _, exam in group.iterrows():
            birads = exam.get('birads_max', '-')
            birads_d = exam.get('birads_direita', '-')
            birads_e = exam.get('birads_esquerda', '-')
            
            birads_color = BIRADS_COLORS.get(str(birads), COLORS['secondary'])
            
            data_sol = str(exam.get('data_solicitacao', ''))[:10]
            data_real = str(exam.get('data_realizacao', ''))[:10] if exam.get('data_realizacao') else '-'
            unidade = str(exam.get('unidade_saude', '-'))[:25]
            prestador = str(exam.get('prestador_executante', '-'))[:25] if exam.get('prestador_executante') else '-'
            wait = exam.get('wait_days', '-')
            ordem = exam.get('exam_order', '-')
            
            exams_rows.append(html.Tr([
                html.Td(f'{ordem}º', style={'fontWeight': '500', 'textAlign': 'center'}),
                html.Td(data_sol, style={'fontSize': '0.85rem'}),
                html.Td(data_real, style={'fontSize': '0.85rem'}),
                html.Td(
                    dbc.Badge(f'BI-RADS {birads}', style={'backgroundColor': birads_color}),
                    style={'textAlign': 'center'}
                ),
                html.Td(f'D:{birads_d} E:{birads_e}', style={'fontSize': '0.8rem', 'color': '#666'}),
                html.Td(unidade, style={'fontSize': '0.85rem'}),
                html.Td(prestador, style={'fontSize': '0.85rem'}),
                html.Td(f'{wait} dias' if wait and wait != '-' else '-', style={'fontSize': '0.85rem'})
            ]))
        
        evolucao_badge = None
        if evolucao_positiva:
            evolucao_badge = dbc.Badge(f'↓ BI-RADS {first_birads}→{last_birads}', color='success', className='ms-2')
        
        exam_table = dbc.Table(
            [
                html.Thead(html.Tr([
                    html.Th('#', style={'width': '50px', 'textAlign': 'center'}),
                    html.Th('Solicitação', style={'width': '90px'}),
                    html.Th('Realização', style={'width': '90px'}),
                    html.Th('BI-RADS', style={'width': '90px', 'textAlign': 'center'}),
                    html.Th('Detalhe', style={'width': '90px'}),
                    html.Th('Unidade de Saúde'),
                    html.Th('Prestador Executante'),
                    html.Th('Espera', style={'width': '70px'})
                ])),
                html.Tbody(exams_rows)
            ],
            bordered=True,
            hover=True,
            responsive=True,
            striped=True,
            size='sm',
            className='mb-0'
        )
        
        title_elements = [
            html.Span(nome, style={'fontWeight': '500'}),
            html.Span(f' | CNS: {cartao_sus}', style={'color': '#666', 'fontSize': '0.9rem'}),
            dbc.Badge(f'{total_exames} exames', color='primary', className='ms-2')
        ]
        if evolucao_badge:
            title_elements.append(evolucao_badge)
        
        accordion_items.append(
            dbc.AccordionItem(
                exam_table,
                title=html.Div(title_elements),
                item_id=str(patient_id)
            )
        )
    
    return dbc.Card([
        dbc.CardHeader(
            html.H5('Histórico de Atendimentos por Paciente', className='mb-0', style={'fontWeight': '500'}),
            style={'backgroundColor': COLORS['card_bg'], 'border': 'none'}
        ),
        dbc.CardBody([
            html.P(f'Mostrando {min(50, len(grouped))} pacientes com mais atendimentos', 
                   className='text-muted mb-3', style={'fontSize': '0.85rem'}),
            dbc.Accordion(accordion_items, start_collapsed=True, flush=True)
        ])
    ],
        className='shadow-sm',
        style={
            'borderRadius': '10px',
            'border': 'none',
            'backgroundColor': COLORS['card_bg']
        }
    )


def create_patient_navigation_summary_chart(summary_df):
    if summary_df.empty:
        return html.Div('Nenhum dado disponível', className='text-muted text-center py-4')
    
    from src.components.charts import create_bar_chart
    return create_bar_chart(
        summary_df, 
        'numero_atendimentos', 
        'total_pacientes',
        'Distribuição por Número de Atendimentos',
        'Número de Atendimentos',
        'Quantidade de Pacientes'
    )


def create_patient_data_table(df, is_masked=True):
    if df.empty:
        return html.Div(
            html.P('Nenhum registro encontrado. Clique em "Buscar" para carregar os dados.', 
                   className='text-muted text-center py-4'),
            className='border rounded'
        )
    
    column_config = [
        ('nome', 'Nome', 200),
        ('idade', 'Idade', 60),
        ('sexo', 'Sexo', 60),
        ('data_nascimento', 'Data Nasc.', 100),
        ('nome_mae', 'Nome da Mãe', 180),
        ('unidade_saude', 'Unidade de Saúde', 180),
        ('data_solicitacao', 'Solicitação', 100),
        ('data_realizacao', 'Realização', 100),
        ('data_liberacao', 'Liberação', 100),
        ('prestador_servico', 'Prestador', 150),
        ('numero_exame', 'Nº Exame', 100),
        ('tipo_mamografia', 'Tipo Mamo', 120),
        ('tipo_mama', 'Tipo Mama', 150),
        ('linfonodos_axilares', 'Linfonodos', 150),
        ('achados_benignos', 'Achados Benignos', 200),
        ('birads_direita_class', 'BI-RADS Dir.', 100),
        ('birads_esquerda_class', 'BI-RADS Esq.', 100),
        ('recomendacoes', 'Recomendações', 200),
    ]
    
    available_cols = [(col, label, width) for col, label, width in column_config if col in df.columns]
    
    header = html.Thead(
        html.Tr([
            html.Th(label, style={
                'fontSize': '0.75rem', 
                'minWidth': f'{width}px',
                'whiteSpace': 'nowrap',
                'position': 'sticky',
                'top': '0',
                'backgroundColor': '#f8f9fa',
                'zIndex': '1'
            }) 
            for col, label, width in available_cols
        ])
    )
    
    rows = []
    for _, row in df.iterrows():
        cells = []
        for col, label, width in available_cols:
            value = row.get(col)
            
            if pd.isna(value) or value is None or str(value).lower() == 'none':
                cell_content = '-'
            elif col in ['data_solicitacao', 'data_realizacao', 'data_liberacao']:
                cell_content = str(value)[:10] if value else '-'
            elif col == 'data_nascimento':
                if is_masked:
                    cell_content = '**/**/****'
                else:
                    cell_content = str(value)[:10] if value else '-'
            elif col == 'nome':
                cell_content = mask_name(value, is_masked)
            elif col == 'nome_mae':
                cell_content = mask_name(value, is_masked)
            elif col in ['birads_direita_class', 'birads_esquerda_class']:
                cell_content = dbc.Badge(str(value), color='info', className='px-2')
            elif col == 'idade':
                try:
                    cell_content = f'{int(float(value))} anos'
                except:
                    cell_content = str(value)
            elif col in ['recomendacoes', 'achados_benignos', 'linfonodos_axilares', 'tipo_mama', 'tipo_mamografia']:
                text = str(value)[:50]
                if len(str(value)) > 50:
                    text += '...'
                cell_content = html.Span(text, title=str(value))
            elif col == 'prestador_servico':
                text = str(value)[:25]
                if len(str(value)) > 25:
                    text += '...'
                cell_content = text
            elif col == 'unidade_saude':
                text = str(value)[:30]
                if len(str(value)) > 30:
                    text += '...'
                cell_content = text
            else:
                cell_content = str(value)
            
            cells.append(html.Td(cell_content, style={'fontSize': '0.8rem', 'verticalAlign': 'middle'}))
        rows.append(html.Tr(cells))
    
    body = html.Tbody(rows)
    
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                dbc.Table(
                    [header, body],
                    bordered=True,
                    hover=True,
                    responsive=True,
                    striped=True,
                    size='sm',
                    className='mb-0',
                    style={'fontSize': '0.8rem'}
                )
            ], style={'maxHeight': '500px', 'overflowY': 'auto', 'overflowX': 'auto'})
        ], className='p-2')
    ],
        className='shadow-sm',
        style={
            'borderRadius': '10px',
            'border': 'none',
            'backgroundColor': COLORS['card_bg']
        }
    )


def create_follow_up_overdue_table(df, is_masked=True):
    """Create table showing patients with overdue follow-up appointments"""
    if df.empty:
        return html.Div(
            html.P('Nenhuma paciente com retorno pendente encontrada', 
                   className='text-muted text-center py-4'),
            className='border rounded'
        )
    
    header = html.Thead(
        html.Tr([
            html.Th('Nome', style={'fontSize': '0.8rem', 'minWidth': '150px'}),
            html.Th('Idade', style={'fontSize': '0.8rem', 'width': '60px'}),
            html.Th('BI-RADS', style={'fontSize': '0.8rem', 'width': '80px'}),
            html.Th('Data Exame', style={'fontSize': '0.8rem', 'width': '100px'}),
            html.Th('Data Prevista', style={'fontSize': '0.8rem', 'width': '100px'}),
            html.Th('Dias Atraso', style={'fontSize': '0.8rem', 'width': '90px'}),
            html.Th('Motivo Retorno', style={'fontSize': '0.8rem', 'minWidth': '180px'}),
            html.Th('Cartão SUS', style={'fontSize': '0.8rem', 'width': '130px'})
        ])
    )
    
    rows = []
    for _, row in df.iterrows():
        nome = mask_name(row.get('nome', ''), is_masked)
        
        idade = row.get('idade', '-')
        if idade and idade != '-':
            try:
                idade = f'{int(float(idade))} anos'
            except:
                idade = '-'
        
        birads = row.get('birads_max', '-')
        birads_color = BIRADS_COLORS.get(str(birads), COLORS['secondary'])
        
        data_exame = str(row.get('data_exame', ''))[:10] if row.get('data_exame') else '-'
        data_prevista = str(row.get('data_prevista_retorno', ''))[:10] if row.get('data_prevista_retorno') else '-'
        
        dias_atraso = row.get('dias_atraso', 0)
        try:
            dias_atraso = int(dias_atraso)
        except:
            dias_atraso = 0
        
        if dias_atraso > 180:
            atraso_color = COLORS['danger']
            atraso_badge = 'danger'
        elif dias_atraso > 90:
            atraso_color = '#fa8c16'
            atraso_badge = 'warning'
        else:
            atraso_color = COLORS['warning']
            atraso_badge = 'warning'
        
        motivo = str(row.get('motivo_retorno', '-'))
        cartao = mask_cns(row.get('cartao_sus', ''), is_masked)
        
        cells = [
            html.Td(nome, style={'fontSize': '0.8rem', 'fontWeight': '500'}),
            html.Td(idade, style={'fontSize': '0.8rem'}),
            html.Td(
                dbc.Badge(f'{birads}', style={'backgroundColor': birads_color}),
                style={'textAlign': 'center'}
            ),
            html.Td(data_exame, style={'fontSize': '0.8rem'}),
            html.Td(data_prevista, style={'fontSize': '0.8rem'}),
            html.Td(
                dbc.Badge(f'{dias_atraso} dias', color=atraso_badge, className='fw-bold'),
                style={'textAlign': 'center'}
            ),
            html.Td(motivo, style={'fontSize': '0.75rem', 'color': '#666'}),
            html.Td(cartao, style={'fontSize': '0.75rem', 'fontFamily': 'monospace'})
        ]
        rows.append(html.Tr(cells))
    
    body = html.Tbody(rows)
    
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.H5('Pacientes com Retorno Pendente', className='mb-0', style={'fontWeight': '500'}),
                html.Small('Ordenado por dias de atraso (maior primeiro)', className='text-muted')
            ])
        ], style={'backgroundColor': COLORS['card_bg'], 'border': 'none'}),
        dbc.CardBody([
            html.Div([
                dbc.Table(
                    [header, body],
                    bordered=True,
                    hover=True,
                    responsive=True,
                    striped=True,
                    size='sm',
                    className='mb-0'
                )
            ], style={'maxHeight': '400px', 'overflowY': 'auto', 'overflowX': 'auto'})
        ], className='p-2')
    ],
        className='shadow-sm',
        style={
            'borderRadius': '10px',
            'border': 'none',
            'backgroundColor': COLORS['card_bg']
        }
    )


def create_unit_kpi_cards(kpis):
    """Create KPI cards for health unit overview"""
    if not kpis:
        return html.Div('Selecione uma unidade de saúde', className='text-muted')
    
    cards = [
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className='fas fa-file-medical fa-2x', style={'color': COLORS['primary']}),
                        html.Span(' Total Exames', className='ms-2 fw-bold', style={'fontSize': '1rem'})
                    ], className='d-flex align-items-center mb-2'),
                    html.H3(f'{kpis["total_exames"]:,}'.replace(',', '.'), 
                           style={'color': COLORS['primary'], 'fontWeight': '600'}),
                    html.Small(f'{kpis["total_pacientes"]:,} pacientes'.replace(',', '.'), className='text-muted')
                ])
            ], className='shadow-sm h-100', style={'borderRadius': '10px', 'border': 'none'})
        ], md=2, sm=4, className='mb-3'),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className='fas fa-clock fa-2x', style={'color': COLORS['info']}),
                        html.Span(' Média Espera', className='ms-2 fw-bold', style={'fontSize': '1rem'})
                    ], className='d-flex align-items-center mb-2'),
                    html.H3(f'{kpis["media_espera"]} dias', 
                           style={'color': COLORS['info'], 'fontWeight': '600'}),
                    html.Small(f'Mediana: {kpis["mediana_espera"]} dias', className='text-muted')
                ])
            ], className='shadow-sm h-100', style={'borderRadius': '10px', 'border': 'none'})
        ], md=2, sm=4, className='mb-3'),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className='fas fa-check-circle fa-2x', 
                              style={'color': COLORS['success'] if kpis["taxa_conformidade"] >= 70 else COLORS['warning']}),
                        html.Span(' Conformidade', className='ms-2 fw-bold', style={'fontSize': '1rem'})
                    ], className='d-flex align-items-center mb-2'),
                    html.H3(f'{kpis["taxa_conformidade"]}%', 
                           style={'color': COLORS['success'] if kpis["taxa_conformidade"] >= 70 else COLORS['warning'], 
                                  'fontWeight': '600'}),
                    html.Small('Exames em até 30 dias', className='text-muted')
                ])
            ], className='shadow-sm h-100', style={'borderRadius': '10px', 'border': 'none'})
        ], md=2, sm=4, className='mb-3'),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className='fas fa-exclamation-triangle fa-2x', style={'color': COLORS['danger']}),
                        html.Span(' Alto Risco', className='ms-2 fw-bold', style={'fontSize': '1rem'})
                    ], className='d-flex align-items-center mb-2'),
                    html.H3(f'{kpis["casos_alto_risco"]}', 
                           style={'color': COLORS['danger'], 'fontWeight': '600'}),
                    html.Small('BI-RADS 4 e 5', className='text-muted'),
                    dbc.Button(
                        [html.I(className='fas fa-file-export me-1'), 'Encaminhar para busca ativa'],
                        id='download-busca-ativa-btn',
                        color='warning',
                        size='sm',
                        className='mt-2 w-100',
                        style={'fontSize': '0.7rem'},
                        disabled=kpis["casos_alto_risco"] == 0
                    )
                ])
            ], className='shadow-sm h-100', style={'borderRadius': '10px', 'border': 'none'})
        ], md=2, sm=4, className='mb-3'),
    ]
    
    return dbc.Row(cards)


def create_priority_summary_cards(summary):
    """Create priority summary cards showing distribution by priority level"""
    priority_config = [
        {'key': 'CRÍTICA', 'label': 'Crítica', 'color': '#dc3545', 'icon': 'fa-exclamation-circle', 'desc': 'BI-RADS 4/5 - Fast-Track'},
        {'key': 'ALTA', 'label': 'Alta', 'color': '#fd7e14', 'icon': 'fa-search', 'desc': 'BI-RADS 0 - Investigação'},
        {'key': 'MÉDIA', 'label': 'Média', 'color': '#ffc107', 'icon': 'fa-clock', 'desc': 'BI-RADS 3 - Monitoramento'},
        {'key': 'MONITORAMENTO', 'label': 'Monitoramento', 'color': '#6f42c1', 'icon': 'fa-heartbeat', 'desc': 'BI-RADS 6 - Oncológico'},
        {'key': 'ROTINA', 'label': 'Rotina', 'color': '#28a745', 'icon': 'fa-check-circle', 'desc': 'BI-RADS 1/2 - Rastreamento'}
    ]
    
    cards = []
    for config in priority_config:
        count = summary.get(config['key'], 0)
        cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className=f'fas {config["icon"]} fa-lg', 
                                  style={'color': config['color']}),
                            html.Span(f' {config["label"]}', className='ms-2 fw-bold', 
                                     style={'fontSize': '0.85rem'})
                        ], className='d-flex align-items-center mb-2'),
                        html.H4(f'{count:,}'.replace(',', '.'), 
                               style={'color': config['color'], 'fontWeight': '600', 'marginBottom': '0.25rem'}),
                        html.Small(config['desc'], className='text-muted', style={'fontSize': '0.7rem'})
                    ], className='py-2 px-3')
                ], className='shadow-sm h-100', style={'borderRadius': '8px', 'border': 'none'})
            ], className='mb-2', style={'flex': '1', 'minWidth': '140px'})
        )
    
    return html.Div([
        html.Div([
            html.I(className='fas fa-layer-group me-2', style={'color': COLORS['primary']}),
            html.Span('Distribuição por Prioridade', className='fw-bold')
        ], className='mb-3'),
        html.Div(cards, className='d-flex flex-wrap gap-2')
    ])


def create_priority_table(df, is_masked=True):
    """Create a table showing prioritized patients"""
    if df.empty:
        return html.Div(
            html.P('Selecione uma unidade para visualizar a fila de priorização.', 
                   className='text-muted text-center py-4'),
            className='border rounded'
        )
    
    header = html.Thead(
        html.Tr([
            html.Th('Prioridade', style={'fontSize': '0.8rem', 'width': '100px'}),
            html.Th('Paciente', style={'fontSize': '0.8rem'}),
            html.Th('BI-RADS', style={'fontSize': '0.8rem', 'width': '80px'}),
            html.Th('Idade', style={'fontSize': '0.8rem', 'width': '60px'}),
            html.Th('Ação Recomendada', style={'fontSize': '0.8rem'}),
            html.Th('SLA', style={'fontSize': '0.8rem', 'width': '80px'})
        ], style={'backgroundColor': COLORS['primary'], 'color': 'white'})
    )
    
    rows = []
    for idx, row in df.head(50).iterrows():
        prioridade = row.get('prioridade', 'N/A')
        cor = row.get('cor', '#6c757d')
        
        nome_masked = mask_name(row.get('nome', 'N/A'), is_masked)
        cns_masked = mask_cns(row.get('cartao_sus', ''), is_masked)
        
        rows.append(
            html.Tr([
                html.Td(
                    dbc.Badge(prioridade, style={'backgroundColor': cor, 'fontSize': '0.7rem'}),
                    style={'verticalAlign': 'middle'}
                ),
                html.Td([
                    html.Div(nome_masked, style={'fontSize': '0.8rem', 'fontWeight': '500'}),
                    html.Small(f"CNS: {cns_masked}", className='text-muted')
                ]),
                html.Td(
                    dbc.Badge(f"BI-RADS {row.get('birads_max', 'N/A')}", 
                             color='secondary', className='fw-normal'),
                    style={'verticalAlign': 'middle'}
                ),
                html.Td(str(row.get('idade', 'N/A')), style={'fontSize': '0.8rem', 'verticalAlign': 'middle'}),
                html.Td(str(row.get('acao', 'N/A')), style={'fontSize': '0.75rem', 'verticalAlign': 'middle'}),
                html.Td(str(row.get('sla_resolucao', 'N/A')), 
                       style={'fontSize': '0.75rem', 'fontWeight': '500', 'verticalAlign': 'middle'})
            ], style={'backgroundColor': '#fff' if idx % 2 == 0 else '#f8f9fa'})
        )
    
    if len(df) > 50:
        rows.append(
            html.Tr([
                html.Td(
                    html.Small(f'Mostrando 50 de {len(df)} registros', className='text-muted'),
                    colSpan=6, style={'textAlign': 'center', 'padding': '10px'}
                )
            ])
        )
    
    return dbc.Table(
        [header, html.Tbody(rows)],
        bordered=True,
        hover=True,
        responsive=True,
        size='sm',
        className='mb-0'
    )
