from dash import Input, Output, State, html, dcc, callback_context, no_update
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_layer import (
    get_kpi_data_sql, get_monthly_volume_sql,
    get_birads_distribution_sql, get_conformity_by_unit_sql, get_high_risk_cases_sql,
    get_outliers_audit_sql, get_outliers_summary_sql,
    get_patient_navigation_summary_sql, get_patient_navigation_list_sql, get_patient_navigation_stats_sql,
    get_patient_data_list_sql, get_patient_data_count_sql,
    get_unit_kpis_sql, get_unit_demographics_sql, get_unit_agility_sql,
    get_unit_wait_time_trend_sql, get_unit_follow_up_overdue_sql, get_unit_follow_up_count_sql,
    get_indicators_data_sql, get_unit_high_risk_patients_sql, get_all_high_risk_patients_sql,
    get_termo_linkage_summary_sql, get_termo_linkage_data_sql, get_termo_linkage_count_sql,
    get_unit_prioritization_sql, get_unit_priority_summary_sql
)
from src.config import COLORS
from src.components.cards import create_kpi_card, create_chart_card
from src.components.charts import (
    create_line_chart, create_birads_bar_chart,
    create_conformity_chart, create_gauge_chart, create_pie_chart,
    create_demographics_heatmap, create_agility_chart, create_wait_time_trend_chart,
    create_empty_figure
)
from src.components.tables import (
    create_high_risk_table, create_outliers_table, create_outliers_summary_cards,
    create_patient_navigation_stats_cards, create_patient_navigation_table,
    create_patient_data_table, create_follow_up_overdue_table, create_unit_kpi_cards,
    create_priority_summary_cards, create_priority_table
)


def build_dashboard_content(year=None, health_unit=None, region=None, age_range=None, birads=None, priority=None):
    kpis = get_kpi_data_sql(year, health_unit, region, age_range=age_range, birads=birads, priority=priority)
    monthly_df = get_monthly_volume_sql(year, health_unit, region, age_range=age_range, birads=birads, priority=priority)
    birads_df = get_birads_distribution_sql(year, health_unit, region, age_range=age_range, birads=birads, priority=priority)
    conformity_df = get_conformity_by_unit_sql(year, health_unit, region, age_range=age_range, birads=birads, priority=priority)
    high_risk_df = get_high_risk_cases_sql(year, health_unit, region, age_range=age_range, birads=birads, priority=priority)
    
    kpi_mean = create_kpi_card(
        'Média de Espera',
        f'{kpis["mean_wait"]} dias',
        'Tempo médio entre solicitação e realização',
        color='info'
    )
    
    kpi_median = create_kpi_card(
        'Mediana de Espera',
        f'{kpis["median_wait"]} dias',
        'Metade dos exames realizados em até este período',
        color='primary'
    )
    
    conformity_color = 'success' if kpis['conformity_rate'] >= 70 else 'warning' if kpis['conformity_rate'] >= 50 else 'danger'
    kpi_conformity = create_kpi_card(
        'Taxa de Conformidade',
        f'{kpis["conformity_rate"]}%',
        f'{kpis["total_exams"]:,} exames no período'.replace(',', '.'),
        color=conformity_color
    )
    
    risk_color = 'danger' if kpis['high_risk_count'] > 100 else 'warning' if kpis['high_risk_count'] > 50 else 'info'
    kpi_risk = create_kpi_card(
        'Alto Risco',
        f'{kpis["high_risk_count"]:,}'.replace(',', '.'),
        'BI-RADS 4 e 5',
        color=risk_color
    )
    
    chart_volume = create_chart_card(
        'Volume de Exames por Mês',
        create_line_chart(monthly_df, 'month_year', 'count'),
        'Tendência temporal de solicitações'
    )
    
    gauge_chart = create_chart_card(
        'Taxa de Conformidade',
        create_gauge_chart(kpis['conformity_rate'], 'Meta: 70%'),
        'Exames realizados em até 30 dias'
    )
    
    chart_conformity = create_chart_card(
        'Conformidade por Unidade de Saúde',
        create_conformity_chart(conformity_df),
        'Top 10 unidades por volume'
    )
    
    chart_birads = create_chart_card(
        'Distribuição BI-RADS',
        create_birads_bar_chart(birads_df),
        'Classificação de risco dos exames'
    )
    
    chart_birads_pie = create_chart_card(
        'Proporção BI-RADS',
        create_pie_chart(birads_df, 'birads_category', 'count'),
        'Distribuição percentual'
    )
    
    table_risk = create_high_risk_table(high_risk_df)
    
    outliers_df = get_outliers_audit_sql()
    outliers_summary_df = get_outliers_summary_sql()
    outliers_table = create_outliers_table(outliers_df)
    outliers_summary = create_outliers_summary_cards(outliers_summary_df)
    
    navigation_stats = get_patient_navigation_stats_sql(year, health_unit, region)
    navigation_list_df = get_patient_navigation_list_sql(year, health_unit, region, min_exams=2, limit=50)
    navigation_stats_cards = create_patient_navigation_stats_cards(navigation_stats)
    navigation_table = create_patient_navigation_table(navigation_list_df)
    
    last_update = f'Última atualização: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'
    
    return {
        'kpi_mean': kpi_mean,
        'kpi_median': kpi_median,
        'kpi_conformity': kpi_conformity,
        'kpi_risk': kpi_risk,
        'chart_volume': chart_volume,
        'gauge_chart': gauge_chart,
        'chart_conformity': chart_conformity,
        'chart_birads': chart_birads,
        'chart_birads_pie': chart_birads_pie,
        'table_risk': table_risk,
        'outliers_table': outliers_table,
        'outliers_summary': outliers_summary,
        'navigation_stats': navigation_stats_cards,
        'navigation_table': navigation_table,
        'last_update': last_update
    }


def register_callbacks(app):
    @app.callback(
        Output('kpi-mean-wait', 'children'),
        Output('kpi-median-wait', 'children'),
        Output('kpi-conformity', 'children'),
        Output('kpi-high-risk', 'children'),
        Output('chart-monthly-volume', 'children'),
        Output('chart-conformity-gauge', 'children'),
        Output('chart-conformity-by-unit', 'children'),
        Output('chart-birads-dist', 'children'),
        Output('chart-birads-pie', 'children'),
        Output('table-high-risk', 'children'),
        Output('outliers-summary', 'children'),
        Output('outliers-table', 'children'),
        Output('navigation-stats', 'children'),
        Output('navigation-table', 'children'),
        Output('last-update-display', 'children'),
        Input('refresh-btn', 'n_clicks'),
        State('year-filter', 'value'),
        State('health-unit-filter', 'value'),
        State('region-filter', 'value'),
        State('age-range-filter', 'value'),
        State('birads-filter', 'value'),
        State('priority-filter', 'value'),
        prevent_initial_call=True
    )
    def update_dashboard(n_clicks, year, health_unit, region, age_range, birads, priority):
        try:
            content = build_dashboard_content(year, health_unit, region, age_range, birads, priority)
            return (
                content['kpi_mean'],
                content['kpi_median'],
                content['kpi_conformity'],
                content['kpi_risk'],
                content['chart_volume'],
                content['gauge_chart'],
                content['chart_conformity'],
                content['chart_birads'],
                content['chart_birads_pie'],
                content['table_risk'],
                content['outliers_summary'],
                content['outliers_table'],
                content['navigation_stats'],
                content['navigation_table'],
                content['last_update']
            )
        except Exception as e:
            error_message = f'Erro ao atualizar: {str(e)}'
            from dash import html
            error_card = html.Div([
                html.P(error_message, className='text-danger')
            ])
            return (
                error_card, error_card, error_card, error_card,
                error_card, error_card, error_card, error_card,
                error_card, error_card, error_card, error_card,
                error_card, error_card, error_message
            )
    
    @app.callback(
        Output('patient-data-table', 'children'),
        Output('patient-data-count', 'children'),
        Output('patient-data-page-info', 'children'),
        Output('patient-data-current-page', 'data'),
        Output('patient-data-prev-btn', 'disabled'),
        Output('patient-data-next-btn', 'disabled'),
        Input('patient-data-search-btn', 'n_clicks'),
        Input('patient-data-prev-btn', 'n_clicks'),
        Input('patient-data-next-btn', 'n_clicks'),
        Input('refresh-btn', 'n_clicks'),
        State('year-filter', 'value'),
        State('health-unit-filter', 'value'),
        State('region-filter', 'value'),
        State('patient-data-name-filter', 'value'),
        State('patient-data-sex-filter', 'value'),
        State('patient-data-birads-filter', 'value'),
        State('patient-data-page-size', 'value'),
        State('patient-data-current-page', 'data'),
        prevent_initial_call=True
    )
    def update_patient_data(search_clicks, prev_clicks, next_clicks, refresh_clicks,
                            year, health_unit, region,
                            patient_name, sex, birads, page_size, current_page):
        try:
            ctx = callback_context
            if not ctx.triggered:
                return no_update, no_update, no_update, no_update, no_update, no_update
            
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if triggered_id in ['patient-data-search-btn', 'refresh-btn']:
                current_page = 1
            elif triggered_id == 'patient-data-prev-btn':
                current_page = max(1, current_page - 1)
            elif triggered_id == 'patient-data-next-btn':
                current_page = current_page + 1
            
            page_size = page_size or 50
            
            total_count = get_patient_data_count_sql(
                year, health_unit, region, None,
                patient_name, sex, birads
            )
            
            total_pages = max(1, (total_count + page_size - 1) // page_size)
            current_page = min(current_page, total_pages)
            
            df = get_patient_data_list_sql(
                year, health_unit, region, None,
                patient_name, sex, birads,
                page=current_page, page_size=page_size
            )
            
            table = create_patient_data_table(df)
            count_text = f'Total de registros: {total_count:,}'.replace(',', '.')
            page_info = f'Página {current_page} de {total_pages}'
            
            prev_disabled = current_page <= 1
            next_disabled = current_page >= total_pages
            
            return table, count_text, page_info, current_page, prev_disabled, next_disabled
            
        except Exception as e:
            error_msg = html.Div([
                html.P(f'Erro ao carregar dados: {str(e)}', className='text-danger')
            ])
            return error_msg, 'Erro', 'Página 1 de 1', 1, True, True
    
    @app.callback(
        Output('unit-kpis', 'children'),
        Output('unit-demographics-chart', 'children'),
        Output('unit-agility-chart', 'children'),
        Output('unit-wait-time-chart', 'children'),
        Output('unit-follow-up-table', 'children'),
        Output('unit-follow-up-count', 'children'),
        Input('unit-analysis-btn', 'n_clicks'),
        Input('refresh-btn', 'n_clicks'),
        State('unit-analysis-selector', 'value'),
        State('year-filter', 'value'),
        State('region-filter', 'value'),
        prevent_initial_call=True
    )
    def update_health_unit_analysis(btn_clicks, refresh_clicks, selected_unit, year, region):
        try:
            if not selected_unit:
                empty_msg = html.Div([
                    html.P('Selecione uma unidade de saúde para visualizar a análise.', 
                           className='text-muted text-center py-4')
                ])
                return (
                    html.Div('Selecione uma unidade para ver os indicadores', className='text-muted'),
                    create_empty_figure("Selecione uma unidade de saúde"),
                    create_empty_figure("Selecione uma unidade de saúde"),
                    create_empty_figure("Selecione uma unidade de saúde"),
                    empty_msg,
                    ""
                )
            
            kpis = get_unit_kpis_sql(selected_unit, year, region)
            kpi_cards = create_unit_kpi_cards(kpis)
            
            demographics_df = get_unit_demographics_sql(selected_unit, year, region)
            demographics_chart = create_demographics_heatmap(demographics_df)
            
            agility_df = get_unit_agility_sql(selected_unit, year, region)
            agility_chart = create_agility_chart(agility_df)
            
            wait_time_df = get_unit_wait_time_trend_sql(selected_unit, year, region)
            wait_time_chart = create_wait_time_trend_chart(wait_time_df)
            
            follow_up_df = get_unit_follow_up_overdue_sql(selected_unit, year, region, limit=100)
            follow_up_table = create_follow_up_overdue_table(follow_up_df)
            
            follow_up_count = get_unit_follow_up_count_sql(selected_unit, year, region)
            follow_up_badge = f'{follow_up_count} pacientes' if follow_up_count > 0 else ''
            
            return (
                kpi_cards,
                demographics_chart,
                agility_chart,
                wait_time_chart,
                follow_up_table,
                follow_up_badge
            )
            
        except Exception as e:
            error_msg = html.Div([
                html.P(f'Erro ao carregar análise: {str(e)}', className='text-danger')
            ])
            return (
                error_msg,
                create_empty_figure(f"Erro: {str(e)[:50]}"),
                create_empty_figure(f"Erro: {str(e)[:50]}"),
                create_empty_figure(f"Erro: {str(e)[:50]}"),
                error_msg,
                ""
            )
    
    @app.callback(
        [Output('unit-priority-summary', 'children'),
         Output('unit-priority-table', 'children')],
        [Input('unit-analysis-btn', 'n_clicks')],
        [State('unit-analysis-selector', 'value'),
         State('year-filter', 'value'),
         State('region-filter', 'value')],
        prevent_initial_call=True
    )
    def update_unit_prioritization(n_clicks, selected_unit, year, region):
        if not n_clicks or not selected_unit:
            empty_msg = html.Div(
                html.P('Selecione uma unidade para ver a priorização.', className='text-muted text-center py-3')
            )
            return empty_msg, empty_msg
        
        try:
            summary = get_unit_priority_summary_sql(selected_unit, year, region)
            summary_cards = create_priority_summary_cards(summary)
            
            priority_df = get_unit_prioritization_sql(selected_unit, year, region)
            priority_table = create_priority_table(priority_df)
            
            return summary_cards, priority_table
            
        except Exception as e:
            error_msg = html.Div([
                html.P(f'Erro ao carregar priorização: {str(e)}', className='text-danger')
            ])
            return error_msg, error_msg
    
    import dash_bootstrap_components as dbc
    from src.components.layout import create_indicator_card, create_time_indicator_card
    
    @app.callback(
        Output('indicator-1-card', 'children'),
        Output('indicator-2-charts', 'children'),
        Output('indicator-3-card', 'children'),
        Output('indicator-4-card', 'children'),
        Output('indicator-5-card', 'children'),
        Output('indicator-6-card', 'children'),
        Output('indicator-7-card', 'children'),
        Output('indicator-8-card', 'children'),
        Output('indicator-9-card', 'children'),
        Output('indicator-10-card', 'children'),
        Input('refresh-btn', 'n_clicks'),
        State('year-filter', 'value'),
        State('region-filter', 'value'),
        State('health-unit-filter', 'value'),
        prevent_initial_call=False
    )
    def update_indicators(n_clicks, year, region, health_unit):
        try:
            indicators = get_indicators_data_sql(year, region, health_unit)
            
            total = indicators.get('total_exames', 1)
            
            ind1 = create_indicator_card(
                'Mamografia de Rastreamento (50-74 anos)',
                'Medir a cobertura da população alvo. Exames de rastreamento em mulheres na faixa etária recomendada.',
                indicators.get('rastreamento_50_74', 0),
                percentage=(indicators.get('rastreamento_50_74', 0) / total * 100) if total > 0 else 0,
                icon_class='fas fa-users'
            )
            
            distrito_df = indicators.get('rastreamento_por_distrito', pd.DataFrame())
            unidade_df = indicators.get('rastreamento_por_unidade', pd.DataFrame())
            
            if not distrito_df.empty:
                fig_distrito = px.bar(
                    distrito_df.head(10),
                    x='total',
                    y='distrito',
                    orientation='h',
                    title='Por Distrito Sanitário',
                    labels={'total': 'Exames', 'distrito': ''},
                    color_discrete_sequence=[COLORS['primary']]
                )
                fig_distrito.update_layout(
                    height=250,
                    margin=dict(l=10, r=10, t=40, b=10),
                    font=dict(size=10),
                    showlegend=False
                )
                chart_distrito = dcc.Graph(figure=fig_distrito, config={'displayModeBar': False})
            else:
                chart_distrito = html.P('Sem dados de distrito', className='text-muted')
            
            if not unidade_df.empty:
                fig_unidade = px.bar(
                    unidade_df.head(10),
                    x='total',
                    y='unidade',
                    orientation='h',
                    title='Top 10 Unidades de Saúde',
                    labels={'total': 'Exames', 'unidade': ''},
                    color_discrete_sequence=[COLORS['secondary']]
                )
                fig_unidade.update_layout(
                    height=250,
                    margin=dict(l=10, r=10, t=40, b=10),
                    font=dict(size=10),
                    showlegend=False
                )
                chart_unidade = dcc.Graph(figure=fig_unidade, config={'displayModeBar': False})
            else:
                chart_unidade = html.P('Sem dados de unidade', className='text-muted')
            
            ind2 = html.Div([
                dbc.Card([
                    dbc.CardBody([
                        html.H6('Cobertura por Unidade/Distrito', className='mb-3', style={'fontSize': '0.95rem', 'fontWeight': '600'}),
                        html.P('Medir a cobertura da população alvo por unidade de saúde ou distrito sanitário.', 
                               className='text-muted mb-3', style={'fontSize': '0.8rem'}),
                        dbc.Tabs([
                            dbc.Tab(chart_distrito, label='Por Distrito'),
                            dbc.Tab(chart_unidade, label='Por Unidade')
                        ], className='nav-tabs-sm')
                    ])
                ], className='h-100 shadow-sm', style={'borderLeft': f'4px solid {COLORS["primary"]}'})
            ])
            
            tempo_sol_lib = indicators.get('tempo_solicitacao_liberacao', {'media': 0, 'mediana': 0})
            ind3 = create_time_indicator_card(
                'Solicitação até Liberação do Laudo',
                'Medir a agilidade de acesso ao exame e tempo de espera total desde a solicitação até a liberação do resultado.',
                tempo_sol_lib['media'],
                tempo_sol_lib['mediana'],
                icon_class='fas fa-hourglass-half'
            )
            
            tempo_real_lib = indicators.get('tempo_realizacao_liberacao', {'media': 0, 'mediana': 0})
            ind4 = create_time_indicator_card(
                'Realização até Liberação do Resultado',
                'Medir a eficiência do prestador na agilidade da entrega dos resultados.',
                tempo_real_lib['media'],
                tempo_real_lib['mediana'],
                icon_class='fas fa-file-medical'
            )
            
            ind5 = create_indicator_card(
                'Exames Categoria 0',
                'Encaminhamento para US de mamas. Exames que necessitam de avaliação adicional por imagem.',
                indicators.get('categoria_0', 0),
                percentage=(indicators.get('categoria_0', 0) / total * 100) if total > 0 else 0,
                icon_class='fas fa-search-plus'
            )
            
            cat3_nodulo = indicators.get('categoria_3_nodulo', 0)
            cat3_total = indicators.get('categoria_3_total', 0)
            ind6 = create_indicator_card(
                'Categoria 3 com Nódulo',
                f'Encaminhamento para US de mamas e Mastologia. Total Cat. 3: {cat3_total:,} exames.',
                cat3_nodulo,
                percentage=(cat3_nodulo / cat3_total * 100) if cat3_total > 0 else 0,
                icon_class='fas fa-notes-medical'
            )
            
            ind7 = create_indicator_card(
                'Categoria 4/5 - Rastreamento',
                'Necessidade de biópsia na população feminina. Encaminhamento para a Cancerologia.',
                indicators.get('categoria_4_5_rastreamento', 0),
                percentage=(indicators.get('categoria_4_5_rastreamento', 0) / total * 100) if total > 0 else 0,
                icon_class='fas fa-exclamation-circle'
            )
            
            ind8 = create_indicator_card(
                '50-74 anos: Mamas Densas ou Cat. 0',
                'Encaminhamento para US de mamas. Pacientes na faixa etária alvo com mamas densas ou classificação BI-RADS 0.',
                indicators.get('idade_50_74_densas_cat0', 0),
                percentage=(indicators.get('idade_50_74_densas_cat0', 0) / total * 100) if total > 0 else 0,
                icon_class='fas fa-female'
            )
            
            ind9 = create_indicator_card(
                'Idade < 49 anos: Categoria 4/5',
                'Mostra incidência de lesão suspeita fora da faixa etária de rastreamento.',
                indicators.get('idade_menor_49_cat_4_5', 0),
                icon_class='fas fa-user-clock'
            )
            
            ind10 = create_indicator_card(
                'Idade < 40 anos com Nódulo',
                'Encaminhamento para US de mamas. Pacientes jovens com presença de nódulo no laudo.',
                indicators.get('idade_menor_40_nodulo', 0),
                icon_class='fas fa-user-md'
            )
            
            return ind1, ind2, ind3, ind4, ind5, ind6, ind7, ind8, ind9, ind10
            
        except Exception as e:
            error_card = html.Div([
                html.P(f'Erro ao carregar indicadores: {str(e)}', className='text-danger')
            ])
            return (error_card,) * 10
    
    @app.callback(
        Output('download-busca-ativa-csv', 'data'),
        Input('download-busca-ativa-btn', 'n_clicks'),
        State('unit-analysis-selector', 'value'),
        State('year-filter', 'value'),
        State('region-filter', 'value'),
        prevent_initial_call=True
    )
    def download_busca_ativa_csv(n_clicks, selected_unit, year, region):
        if not n_clicks or not selected_unit:
            return no_update
        
        try:
            df = get_unit_high_risk_patients_sql(selected_unit, year, region)
            
            if df.empty:
                return no_update
            
            safe_unit_name = selected_unit.replace(' ', '_').replace('/', '_')[:30]
            filter_suffix = f'_{safe_unit_name}'
            if year:
                filter_suffix += f'_{year}'
            if region:
                safe_region = region.replace(' ', '_').replace('/', '_')[:20]
                filter_suffix += f'_{safe_region}'
            
            filename = f'busca_ativa_alto_risco{filter_suffix}_{datetime.now().strftime("%Y%m%d")}.csv'
            
            return dcc.send_data_frame(df.to_csv, filename, index=False, encoding='utf-8-sig')
        except Exception as e:
            print(f"Erro ao gerar CSV busca ativa: {e}")
            return no_update
    
    @app.callback(
        [Output('linkage-total', 'children'),
         Output('linkage-cpf', 'children'),
         Output('linkage-telefone', 'children'),
         Output('linkage-nome-esaude', 'children'),
         Output('linkage-apac', 'children'),
         Output('linkage-nomes-conferem', 'children')],
        [Input('main-tabs', 'active_tab')]
    )
    def update_linkage_summary(active_tab):
        if active_tab != 'tab-linkage':
            return no_update, no_update, no_update, no_update, no_update, no_update
        
        try:
            summary = get_termo_linkage_summary_sql()
            return (
                f"{summary['total_registros']:,}".replace(',', '.'),
                f"{summary['com_cpf']:,}".replace(',', '.'),
                f"{summary['com_telefone']:,}".replace(',', '.'),
                f"{summary['com_nome_esaude']:,}".replace(',', '.'),
                f"{summary['com_apac_cancer']:,}".replace(',', '.'),
                f"{summary['nomes_conferem']:,}".replace(',', '.')
            )
        except Exception as e:
            print(f"Erro ao carregar resumo linkage: {e}")
            return '0', '0', '0', '0', '0', '0'
    
    @app.callback(
        [Output('linkage-table-container', 'children'),
         Output('linkage-count-display', 'children'),
         Output('linkage-pagination', 'max_value')],
        [Input('linkage-search-button', 'n_clicks'),
         Input('linkage-pagination', 'active_page')],
        [State('linkage-search-nome', 'value'),
         State('linkage-search-cpf', 'value'),
         State('linkage-search-cartao', 'value')]
    )
    def update_linkage_table(n_clicks, page, search_nome, search_cpf, search_cartao):
        if not n_clicks:
            return html.P('Clique em Pesquisar para ver os dados', className='text-muted text-center p-4'), '', 1
        
        try:
            page = page or 1
            limit = 50
            offset = (page - 1) * limit
            
            df = get_termo_linkage_data_sql(search_nome, search_cpf, search_cartao, limit, offset)
            total = get_termo_linkage_count_sql(search_nome, search_cpf, search_cartao)
            max_pages = max(1, (total + limit - 1) // limit)
            
            if df.empty:
                return html.P('Nenhum registro encontrado', className='text-muted text-center p-4'), f'0 registros', 1
            
            import dash_bootstrap_components as dbc
            
            table = dbc.Table([
                html.Thead([
                    html.Tr([
                        html.Th('Nome SISCAN', style={'fontSize': '0.8rem'}),
                        html.Th('Nome eSaude', style={'fontSize': '0.8rem'}),
                        html.Th('Nomes OK', style={'fontSize': '0.8rem'}),
                        html.Th('Cartao SUS', style={'fontSize': '0.8rem'}),
                        html.Th('CPF', style={'fontSize': '0.8rem'}),
                        html.Th('Tel SISCAN', style={'fontSize': '0.8rem'}),
                        html.Th('Tel eSaude', style={'fontSize': '0.8rem'}),
                        html.Th('BI-RADS', style={'fontSize': '0.8rem'}),
                        html.Th('Unidade', style={'fontSize': '0.8rem'}),
                        html.Th('APAC Cancer', style={'fontSize': '0.8rem'})
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(row.get('nome_siscan', '')[:30] if row.get('nome_siscan') else '-', style={'fontSize': '0.75rem'}),
                        html.Td(row.get('nome_esaude', '')[:30] if row.get('nome_esaude') else '-', style={'fontSize': '0.75rem'}),
                        html.Td(
                            html.I(className='fas fa-check text-success') if row.get('comparacao_nomes') in ['True', 'Sim'] else html.I(className='fas fa-times text-danger') if row.get('comparacao_nomes') else '-',
                            style={'fontSize': '0.75rem', 'textAlign': 'center'}
                        ),
                        html.Td(str(row.get('cartao_sus', ''))[:20] if row.get('cartao_sus') else '-', style={'fontSize': '0.75rem'}),
                        html.Td(row.get('cpf', '') if row.get('cpf') else '-', style={'fontSize': '0.75rem'}),
                        html.Td(row.get('telefone_siscan', '')[:15] if row.get('telefone_siscan') else '-', style={'fontSize': '0.75rem'}),
                        html.Td(row.get('telefone_esaude', '')[:15] if row.get('telefone_esaude') else '-', style={'fontSize': '0.75rem'}),
                        html.Td(row.get('birads_max', '') if row.get('birads_max') else '-', style={'fontSize': '0.75rem'}),
                        html.Td(row.get('unidade_saude', '')[:25] if row.get('unidade_saude') else '-', style={'fontSize': '0.75rem'}),
                        html.Td(str(row.get('ultima_apac_cancer', ''))[:10] if row.get('ultima_apac_cancer') else '-', style={'fontSize': '0.75rem'})
                    ]) for row in df.to_dict('records')
                ])
            ], bordered=True, hover=True, responsive=True, striped=True, size='sm')
            
            count_text = f'Mostrando {offset + 1}-{min(offset + limit, total)} de {total:,} registros'.replace(',', '.')
            
            return table, count_text, max_pages
        except Exception as e:
            print(f"Erro ao carregar tabela linkage: {e}")
            return html.P(f'Erro ao carregar dados', className='text-danger text-center p-4'), '', 1
