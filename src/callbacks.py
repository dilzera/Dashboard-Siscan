import dash
from dash import Input, Output, State, html, dcc, callback_context, no_update, ALL, MATCH
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.cache import clear_cache


def _normalize_filter(value):
    if value is None:
        return None
    if isinstance(value, list):
        filtered = [v for v in value if v is not None and v != 'ALL' and v != '']
        return filtered if filtered else None
    if value == 'ALL' or value == '':
        return None
    return value


def _enforce_access(region, health_unit):
    from flask_login import current_user
    if not current_user or not current_user.is_authenticated:
        return region, health_unit
    access_level = getattr(current_user, 'access_level', 'secretaria') or 'secretaria'
    user_district = getattr(current_user, 'district', None)
    user_health_unit = getattr(current_user, 'health_unit', None)
    if access_level == 'distrito' and user_district:
        region = user_district
    elif access_level == 'unidade' and user_health_unit:
        health_unit = user_health_unit
    return region, health_unit
from src.data_layer import (
    get_kpi_data_sql, get_monthly_volume_sql,
    get_birads_distribution_sql, get_conformity_by_unit_sql, get_high_risk_cases_sql,
    get_other_birads_cases_sql,
    get_outliers_audit_sql, get_outliers_summary_sql,
    get_patient_navigation_summary_sql, get_patient_navigation_list_sql, get_patient_navigation_stats_sql,
    get_patient_data_list_sql, get_patient_data_count_sql,
    get_unit_kpis_sql, get_unit_demographics_sql, get_unit_agility_sql,
    get_unit_wait_time_trend_sql, get_unit_follow_up_overdue_sql, get_unit_follow_up_count_sql,
    get_indicators_data_sql, get_unit_high_risk_patients_sql, get_all_high_risk_patients_sql,
    get_termo_linkage_summary_sql, get_termo_linkage_data_sql, get_termo_linkage_count_sql,
    get_unit_prioritization_sql, get_unit_priority_summary_sql,
    get_pending_access_requests, approve_access_request, reject_access_request
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
    create_high_risk_table, create_other_birads_table, create_outliers_table, create_outliers_summary_cards,
    create_patient_navigation_stats_cards, create_patient_navigation_table,
    create_patient_data_table, create_follow_up_overdue_table, create_unit_kpi_cards,
    create_priority_summary_cards, create_priority_table,
    mask_name, mask_cns, mask_cpf, mask_phone,
    create_table_legend
)


def build_dashboard_content(year=None, health_unit=None, region=None, age_range=None, birads=None, priority=None, is_masked=True):
    kpis = get_kpi_data_sql(year, health_unit, region, age_range=age_range, birads=birads, priority=priority)
    monthly_df = get_monthly_volume_sql(year, health_unit, region, age_range=age_range, birads=birads, priority=priority)
    birads_df = get_birads_distribution_sql(year, health_unit, region, age_range=age_range, birads=birads, priority=priority)
    conformity_df = get_conformity_by_unit_sql(year, health_unit, region, age_range=age_range, birads=birads, priority=priority)
    high_risk_df = get_high_risk_cases_sql(year, health_unit, region, age_range=age_range, birads=birads, priority=priority)
    
    kpi_mean = create_kpi_card(
        'Média de Espera',
        f'{kpis["mean_wait"]} dias',
        'Tempo médio entre solicitação e realização',
        color='info',
        tip_id='tip-kpi-mean',
        tip_text='Média aritmética do tempo (em dias) entre a data de solicitação e a data de realização do exame de mamografia.'
    )
    
    kpi_median = create_kpi_card(
        'Mediana de Espera',
        f'{kpis["median_wait"]} dias',
        'Metade dos exames realizados em até este período',
        color='primary',
        tip_id='tip-kpi-median',
        tip_text='Valor central da distribuição de tempos de espera. Metade dos exames foram realizados em até este número de dias.'
    )
    
    conformity_color = 'success' if kpis['conformity_rate'] >= 70 else 'warning' if kpis['conformity_rate'] >= 50 else 'danger'
    kpi_conformity = create_kpi_card(
        'Taxa de Conformidade',
        f'{kpis["conformity_rate"]}%',
        f'{kpis["total_exams"]:,} exames no período'.replace(',', '.'),
        color=conformity_color,
        tip_id='tip-kpi-conformity',
        tip_text='Percentual de exames realizados dentro do prazo de 30 dias após a solicitação. Meta INCA: ≥70%.'
    )
    
    risk_color = 'danger' if kpis['high_risk_count'] > 100 else 'warning' if kpis['high_risk_count'] > 50 else 'info'
    kpi_risk = create_kpi_card(
        'Alto Risco',
        f'{kpis["high_risk_count"]:,}'.replace(',', '.'),
        'BI-RADS 4 e 5',
        color=risk_color,
        tip_id='tip-kpi-risk',
        tip_text='Quantidade de exames classificados como BI-RADS 4 (suspeito) ou 5 (altamente suspeito). Requerem biópsia e encaminhamento prioritário.'
    )
    
    chart_volume = create_chart_card(
        'Volume de Exames por Mês',
        create_line_chart(monthly_df, 'month_year', 'count'),
        'Tendência temporal de solicitações',
        tip_id='tip-chart-volume',
        tip_text='Gráfico de linha mostrando a evolução mensal do número de exames de mamografia realizados no período selecionado.'
    )
    
    gauge_chart = create_chart_card(
        'Taxa de Conformidade',
        create_gauge_chart(kpis['conformity_rate'], 'Meta: 70%'),
        'Exames realizados em até 30 dias',
        tip_id='tip-chart-gauge',
        tip_text='Indicador visual da taxa de conformidade (exames realizados em até 30 dias). Verde ≥70%, amarelo 50-69%, vermelho <50%.'
    )
    
    chart_conformity = create_chart_card(
        'Conformidade',
        create_conformity_chart(conformity_df),
        'Unidades ordenadas por taxa de conformidade',
        tip_id='tip-chart-conformity',
        tip_text='Gráfico de barras comparando a taxa de conformidade entre as unidades de saúde. Ordenado da maior para a menor taxa.'
    )
    
    chart_birads = create_chart_card(
        'Distribuição BI-RADS',
        create_birads_bar_chart(birads_df),
        'Classificação de risco dos exames',
        tip_id='tip-chart-birads',
        tip_text='Distribuição dos exames por categoria BI-RADS (0 a 6). Categorias 4 e 5 indicam suspeita de malignidade.'
    )
    
    chart_birads_pie = create_chart_card(
        'Proporção BI-RADS',
        create_pie_chart(birads_df, 'birads_category', 'count'),
        'Distribuição percentual',
        tip_id='tip-chart-birads-pie',
        tip_text='Gráfico de pizza mostrando a proporção percentual de cada categoria BI-RADS no total de exames.'
    )
    
    table_risk = create_high_risk_table(high_risk_df, is_masked)
    
    other_birads_df = get_other_birads_cases_sql(year, health_unit, region, age_range=age_range)
    table_other_birads = create_other_birads_table(other_birads_df, is_masked)
    
    outliers_df = get_outliers_audit_sql(year, health_unit, region)
    outliers_summary_df = get_outliers_summary_sql(year, health_unit, region)
    outliers_table = create_outliers_table(outliers_df, is_masked)
    outliers_summary = create_outliers_summary_cards(outliers_summary_df)
    
    navigation_stats = get_patient_navigation_stats_sql(year, health_unit, region, age_range=age_range, birads=birads, priority=priority)
    navigation_list_df = get_patient_navigation_list_sql(year, health_unit, region, min_exams=2, limit=50, age_range=age_range, birads=birads, priority=priority)
    navigation_stats_cards = create_patient_navigation_stats_cards(navigation_stats)
    navigation_table = create_patient_navigation_table(navigation_list_df, is_masked)
    
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
        'table_other_birads': table_other_birads,
        'outliers_table': outliers_table,
        'outliers_summary': outliers_summary,
        'navigation_stats': navigation_stats_cards,
        'navigation_table': navigation_table,
        'last_update': last_update
    }


def register_callbacks(app):
    @app.callback(
        [Output('active-sidebar-tab', 'data', allow_duplicate=True),
         Output('year-filter', 'value'),
         Output('health-unit-filter', 'value'),
         Output('age-range-filter', 'value'),
         Output('birads-filter', 'value'),
         Output('priority-filter', 'value')],
        [Input('header-title-link', 'n_clicks')],
        prevent_initial_call=True
    )
    def go_to_overview_on_title_click(n_clicks):
        if n_clicks:
            return 'tab-performance', None, None, None, None, None
        return no_update, no_update, no_update, no_update, no_update, no_update

    all_tab_ids = ['tab-performance', 'tab-audit', 'tab-outliers', 'tab-indicators',
                   'tab-navigation', 'tab-patient-data', 'tab-health-unit', 'tab-linkage', 'tab-access-management']

    @app.callback(
        [Output(f'content-{tid}', 'style') for tid in all_tab_ids] +
        [Output(f'sidebar-{tid}', 'className') for tid in all_tab_ids],
        [Input('active-sidebar-tab', 'data')],
        prevent_initial_call=True
    )
    def switch_tab_content(active_tab):
        styles = []
        classes = []
        for tid in all_tab_ids:
            if tid == active_tab:
                styles.append({'display': 'block'})
                classes.append('sidebar-btn text-start w-100 mb-1 d-flex align-items-center active-nav')
            else:
                styles.append({'display': 'none'})
                classes.append('sidebar-btn text-start w-100 mb-1 d-flex align-items-center')
        return styles + classes

    sidebar_inputs = [Input(f'sidebar-{tid}', 'n_clicks') for tid in all_tab_ids]

    @app.callback(
        Output('active-sidebar-tab', 'data', allow_duplicate=True),
        sidebar_inputs,
        prevent_initial_call=True
    )
    def sidebar_nav_click(*args):
        ctx = dash.callback_context
        if not ctx.triggered:
            return no_update
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        tab_id = triggered_id.replace('sidebar-', '')
        return tab_id

    @app.callback(
        [Output('sidebar', 'className'),
         Output('main-content', 'className'),
         Output('sidebar-state', 'data'),
         Output('sidebar-toggle-floating', 'style')],
        [Input('sidebar-toggle', 'n_clicks'),
         Input('sidebar-toggle-floating', 'n_clicks')],
        [State('sidebar-state', 'data')],
        prevent_initial_call=True
    )
    def toggle_sidebar(n_clicks_sidebar, n_clicks_floating, current_state):
        floating_hidden = {
            'position': 'fixed', 'top': '12px', 'left': '12px', 'zIndex': '1060',
            'background': 'linear-gradient(135deg, #148a9e, #117a8b)', 'border': 'none',
            'color': 'white', 'padding': '8px 12px', 'borderRadius': '8px',
            'cursor': 'pointer', 'display': 'none', 'boxShadow': '0 2px 8px rgba(0,0,0,0.2)',
        }
        floating_visible = {**floating_hidden, 'display': 'block'}

        ctx = callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else ''

        if triggered_id == 'sidebar-toggle-floating':
            return 'sidebar-expanded', 'main-content-expanded', 'expanded', floating_hidden

        if current_state == 'expanded':
            return 'sidebar-collapsed', 'main-content-collapsed', 'collapsed', floating_hidden
        elif current_state == 'collapsed':
            return 'sidebar-hidden', 'main-content-hidden', 'hidden', floating_visible
        return 'sidebar-expanded', 'main-content-expanded', 'expanded', floating_hidden

    @app.callback(
        Output('sidebar-config-collapse', 'is_open'),
        [Input('sidebar-config-toggle', 'n_clicks')],
        [State('sidebar-config-collapse', 'is_open')],
        prevent_initial_call=True
    )
    def toggle_config_submenu(n_clicks, is_open):
        return not is_open
    
    app.clientside_callback(
        """
        function(n_clicks, year, unit, region, age, birads, priority) {
            var ctx = window.dash_clientside.callback_context;
            if (!ctx.triggered || ctx.triggered.length === 0) {
                return window.dash_clientside.no_update;
            }
            return {
                'position': 'fixed', 'top': '0', 'left': '0', 'right': '0', 'bottom': '0',
                'backgroundColor': 'rgba(245,247,250,0.95)', 'zIndex': '1040',
                'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'
            };
        }
        """,
        Output('dashboard-loading-overlay', 'style', allow_duplicate=True),
        [Input('refresh-btn', 'n_clicks'),
         Input('year-filter', 'value'),
         Input('health-unit-filter', 'value'),
         Input('region-filter', 'value'),
         Input('age-range-filter', 'value'),
         Input('birads-filter', 'value'),
         Input('priority-filter', 'value')],
        prevent_initial_call=True
    )

    @app.callback(
        Output('priority-filter', 'value', allow_duplicate=True),
        Output('priority-filter', 'disabled'),
        Input('birads-filter', 'value'),
        prevent_initial_call=True
    )
    def birads_clears_priority(birads_val):
        birads_val = _normalize_filter(birads_val)
        if birads_val:
            return [], True
        return no_update, False

    @app.callback(
        Output('birads-filter', 'value', allow_duplicate=True),
        Output('birads-filter', 'disabled'),
        Input('priority-filter', 'value'),
        prevent_initial_call=True
    )
    def priority_clears_birads(priority_val):
        priority_val = _normalize_filter(priority_val)
        if priority_val:
            return [], True
        return no_update, False

    @app.callback(
        Output('patient-data-birads-filter', 'disabled'),
        Output('patient-data-birads-filter', 'value', allow_duplicate=True),
        Input('birads-filter', 'value'),
        prevent_initial_call=True
    )
    def lock_local_birads_when_global_set(birads_global):
        birads_global = _normalize_filter(birads_global)
        if birads_global:
            return True, None
        return False, no_update

    @app.callback(
        [Output('health-unit-filter', 'options'),
         Output('health-unit-filter', 'value', allow_duplicate=True),
         Output('unit-analysis-selector', 'options')],
        [Input('region-filter', 'value')],
        [State('user-access-level-store', 'data'),
         State('user-health-unit-store', 'data')],
        prevent_initial_call=True
    )
    def update_units_by_district(region, access_level, user_health_unit):
        from src.data_layer import get_health_units, get_units_by_district
        region = _normalize_filter(region)

        if access_level == 'unidade':
            opts = [{'label': user_health_unit, 'value': user_health_unit}]
            return opts, user_health_unit, opts

        if region:
            region_list = region if isinstance(region, list) else [region]
            seen = set()
            units = []
            for r in region_list:
                for u in get_units_by_district(r):
                    if u not in seen:
                        seen.add(u)
                        units.append(u)
            units.sort()
        else:
            units = get_health_units()

        unit_opts = [{'label': u, 'value': u} for u in units]
        return unit_opts, [], unit_opts

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
        Output('table-other-birads', 'children'),
        Output('outliers-summary', 'children'),
        Output('outliers-table', 'children'),
        Output('navigation-stats', 'children'),
        Output('navigation-table', 'children', allow_duplicate=True),
        Output('last-update-display', 'children'),
        Output('dashboard-loading-overlay', 'style'),
        Input('refresh-btn', 'n_clicks'),
        Input('data-masked-store', 'data'),
        Input('initial-load-trigger', 'data'),
        Input('year-filter', 'value'),
        Input('health-unit-filter', 'value'),
        Input('region-filter', 'value'),
        Input('age-range-filter', 'value'),
        Input('birads-filter', 'value'),
        Input('priority-filter', 'value'),
        prevent_initial_call='initial_duplicate'
    )
    def update_dashboard(n_clicks, is_masked, initial_trigger, year, health_unit, region, age_range, birads, priority):
        try:
            ctx = callback_context
            if ctx.triggered and ctx.triggered[0]['prop_id'].split('.')[0] == 'refresh-btn':
                clear_cache()
            
            year, health_unit, region, age_range, birads, priority = [_normalize_filter(v) for v in [year, health_unit, region, age_range, birads, priority]]
            region, health_unit = _enforce_access(region, health_unit)
            content = build_dashboard_content(year, health_unit, region, age_range, birads, priority, is_masked)
            hide_overlay = {'display': 'none'}
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
                content['table_other_birads'],
                content['outliers_summary'],
                content['outliers_table'],
                content['navigation_stats'],
                content['navigation_table'],
                content['last_update'],
                hide_overlay
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
                error_card, error_card, error_card, error_message,
                {'display': 'none'}
            )
    
    @app.callback(
        Output('navigation-table', 'children', allow_duplicate=True),
        [Input('navigation-apply-filter-btn', 'n_clicks')],
        [State('navigation-evolution-filter', 'value'),
         State('year-filter', 'value'),
         State('health-unit-filter', 'value'),
         State('region-filter', 'value'),
         State('age-range-filter', 'value'),
         State('birads-filter', 'value'),
         State('priority-filter', 'value'),
         State('data-masked-store', 'data')],
        prevent_initial_call=True
    )
    def update_navigation_with_evolution_filter(n_clicks, evolution_filter, year, health_unit, region, age_range, birads, priority, is_masked):
        if not n_clicks:
            return no_update
        
        try:
            year, health_unit, region, age_range, birads, priority = [_normalize_filter(v) for v in [year, health_unit, region, age_range, birads, priority]]
            region, health_unit = _enforce_access(region, health_unit)
            navigation_list_df = get_patient_navigation_list_sql(
                year, health_unit, region, 
                min_exams=2, limit=50, 
                evolution_filter=evolution_filter,
                age_range=age_range, birads=birads, priority=priority
            )
            return create_patient_navigation_table(navigation_list_df, is_masked)
        except Exception as e:
            print(f"Erro ao filtrar navegação: {e}")
            return html.Div([html.P(f'Erro ao filtrar: {str(e)}', className='text-danger')])
    
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
        Input('data-masked-store', 'data'),
        Input('year-filter', 'value'),
        Input('health-unit-filter', 'value'),
        Input('region-filter', 'value'),
        Input('age-range-filter', 'value'),
        Input('birads-filter', 'value'),
        Input('priority-filter', 'value'),
        State('patient-data-name-filter', 'value'),
        State('patient-data-cpf-filter', 'value'),
        State('patient-data-cns-filter', 'value'),
        State('patient-data-sex-filter', 'value'),
        State('patient-data-birads-filter', 'value'),
        State('patient-data-page-size', 'value'),
        State('patient-data-current-page', 'data'),
        prevent_initial_call=True
    )
    def update_patient_data(search_clicks, prev_clicks, next_clicks, refresh_clicks, is_masked,
                            year, health_unit, region, age_range, birads_global, priority,
                            patient_name, cpf_filter, cns_filter, sex, birads, page_size, current_page):
        year, health_unit, region, age_range, birads_global, priority = [_normalize_filter(v) for v in [year, health_unit, region, age_range, birads_global, priority]]
        birads = _normalize_filter(birads)
        if birads_global:
            birads = birads_global
        region, health_unit = _enforce_access(region, health_unit)
        try:
            ctx = callback_context
            if not ctx.triggered:
                return no_update, no_update, no_update, no_update, no_update, no_update
            
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            filter_changed = triggered_id in ['year-filter', 'health-unit-filter', 'region-filter',
                                                'age-range-filter', 'birads-filter', 'priority-filter']
            if triggered_id in ['patient-data-search-btn', 'refresh-btn'] or filter_changed:
                current_page = 1
            elif triggered_id == 'patient-data-prev-btn':
                current_page = max(1, current_page - 1)
            elif triggered_id == 'patient-data-next-btn':
                current_page = current_page + 1
            
            page_size = page_size or 50
            
            total_count = get_patient_data_count_sql(
                year, health_unit, region, None,
                patient_name, sex, birads,
                age_range=age_range, priority=priority,
                cpf=cpf_filter, cns=cns_filter
            )
            
            total_pages = max(1, (total_count + page_size - 1) // page_size)
            current_page = min(current_page, total_pages)
            
            df = get_patient_data_list_sql(
                year, health_unit, region, None,
                patient_name, sex, birads,
                page=current_page, page_size=page_size,
                age_range=age_range, priority=priority,
                cpf=cpf_filter, cns=cns_filter
            )
            
            table = create_patient_data_table(df, is_masked)
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
        Input('data-masked-store', 'data'),
        Input('year-filter', 'value'),
        Input('region-filter', 'value'),
        Input('age-range-filter', 'value'),
        Input('birads-filter', 'value'),
        Input('priority-filter', 'value'),
        State('unit-analysis-selector', 'value'),
        prevent_initial_call=True
    )
    def update_health_unit_analysis(btn_clicks, refresh_clicks, is_masked, year, region,
                                     age_range, birads, priority, selected_unit):
        year, region, age_range, birads, priority = [_normalize_filter(v) for v in [year, region, age_range, birads, priority]]
        region, _ = _enforce_access(region, None)
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
            
            kpis = get_unit_kpis_sql(selected_unit, year, region, age_range=age_range, birads=birads, priority=priority)
            kpi_cards = create_unit_kpi_cards(kpis)
            
            demographics_df = get_unit_demographics_sql(selected_unit, year, region, age_range=age_range, birads=birads, priority=priority)
            demographics_chart = create_demographics_heatmap(demographics_df)
            
            agility_df = get_unit_agility_sql(selected_unit, year, region, age_range=age_range, birads=birads, priority=priority)
            agility_chart = create_agility_chart(agility_df)
            
            wait_time_df = get_unit_wait_time_trend_sql(selected_unit, year, region, age_range=age_range, birads=birads, priority=priority)
            wait_time_chart = create_wait_time_trend_chart(wait_time_df)
            
            follow_up_df = get_unit_follow_up_overdue_sql(selected_unit, year, region, limit=100, age_range=age_range, birads=birads, priority=priority)
            follow_up_table = create_follow_up_overdue_table(follow_up_df, is_masked)
            
            follow_up_count = get_unit_follow_up_count_sql(selected_unit, year, region, age_range=age_range, birads=birads, priority=priority)
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
        [Input('unit-analysis-btn', 'n_clicks'),
         Input('data-masked-store', 'data'),
         Input('year-filter', 'value'),
         Input('region-filter', 'value'),
         Input('age-range-filter', 'value'),
         Input('birads-filter', 'value'),
         Input('priority-filter', 'value')],
        [State('unit-analysis-selector', 'value')],
        prevent_initial_call=True
    )
    def update_unit_prioritization(n_clicks, is_masked, year, region, age_range, birads, priority, selected_unit):
        year, region, age_range, birads, priority = [_normalize_filter(v) for v in [year, region, age_range, birads, priority]]
        region, _ = _enforce_access(region, None)
        if not selected_unit:
            empty_msg = html.Div(
                html.P('Selecione uma unidade para ver a priorização.', className='text-muted text-center py-3')
            )
            return empty_msg, empty_msg
        
        try:
            summary = get_unit_priority_summary_sql(selected_unit, year, region, age_range=age_range, birads=birads, priority=priority)
            summary_cards = create_priority_summary_cards(summary)
            
            priority_df = get_unit_prioritization_sql(selected_unit, year, region, age_range=age_range, birads=birads, priority=priority)
            priority_table = create_priority_table(priority_df, is_masked)
            
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
        Output('indicator-11-card', 'children'),
        Input('refresh-btn', 'n_clicks'),
        Input('year-filter', 'value'),
        Input('region-filter', 'value'),
        Input('health-unit-filter', 'value'),
        Input('age-range-filter', 'value'),
        Input('birads-filter', 'value'),
        Input('priority-filter', 'value'),
        prevent_initial_call=False
    )
    def update_indicators(n_clicks, year, region, health_unit, age_range, birads, priority):
        try:
            year, region, health_unit, age_range, birads, priority = [_normalize_filter(v) for v in [year, region, health_unit, age_range, birads, priority]]
            region, health_unit = _enforce_access(region, health_unit)
            indicators = get_indicators_data_sql(year, region, health_unit, age_range=age_range, birads=birads, priority=priority)
            
            total = indicators.get('total_exames', 1)
            
            rastreamento_50_69 = indicators.get('rastreamento_50_69', 0)
            ind1 = create_indicator_card(
                'Cobertura Mamográfica (50-69 anos)',
                'Ref. INCA: Razão de exames de mamografia de rastreamento em mulheres de 50 a 69 anos. Meta ≥70%.',
                rastreamento_50_69,
                percentage=(rastreamento_50_69 / total * 100) if total > 0 else 0,
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
                        html.H6('Cobertura por Unidade/Distrito (50-69 anos)', className='mb-3', style={'fontSize': '0.95rem', 'fontWeight': '600'}),
                        html.P('Ref. INCA: Distribuição da cobertura mamográfica de rastreamento (50-69 anos) por unidade de saúde ou distrito sanitário.', 
                               className='text-muted mb-3', style={'fontSize': '0.8rem'}),
                        dbc.Tabs([
                            dbc.Tab(chart_distrito, label='Por Distrito'),
                            dbc.Tab(chart_unidade, label='Por Unidade')
                        ], className='nav-tabs-sm')
                    ])
                ], className='h-100 shadow-sm', style={'borderLeft': f'4px solid {COLORS["primary"]}'})
            ])
            
            tempo_sol_lib = indicators.get('tempo_solicitacao_liberacao', {'media': 0, 'mediana': 0, 'percentual_30_dias': 0, 'dentro_30_dias': 0, 'total_com_datas': 0})
            pct_30 = tempo_sol_lib.get('percentual_30_dias', 0)
            dentro_30 = tempo_sol_lib.get('dentro_30_dias', 0)
            total_datas = tempo_sol_lib.get('total_com_datas', 0)
            ind3 = create_indicator_card(
                'Resultado em até 30 dias',
                f'Ref. INCA: Percentual de mamografias com resultado liberado em até 30 dias da solicitação. {dentro_30:,} de {total_datas:,} exames.'.replace(',', '.'),
                f'{pct_30}%',
                icon_class='fas fa-hourglass-half',
                color='success' if pct_30 >= 70 else 'warning' if pct_30 >= 50 else 'danger'
            )
            
            tempo_real_lib = indicators.get('tempo_realizacao_liberacao', {'media': 0, 'mediana': 0})
            ind4 = create_time_indicator_card(
                'Realização até Liberação do Resultado',
                'Ref. INCA: Tempo entre a realização do exame e a liberação do laudo. Mede a eficiência do prestador.',
                tempo_real_lib['media'],
                tempo_real_lib['mediana'],
                icon_class='fas fa-file-medical'
            )
            
            total_rastreamento = indicators.get('total_rastreamento', 0)
            cat0_rastreamento = indicators.get('categoria_0_rastreamento', 0)
            pct_cat0 = round(cat0_rastreamento / total_rastreamento * 100, 1) if total_rastreamento > 0 else 0
            ind5 = create_indicator_card(
                'BI-RADS 0 no Rastreamento',
                f'Ref. INCA: Proporção de exames BI-RADS 0 (inconclusivos) no rastreamento. Meta <10%. Total Cat. 0: {indicators.get("categoria_0", 0):,}.'.replace(',', '.'),
                cat0_rastreamento,
                percentage=pct_cat0,
                icon_class='fas fa-search-plus',
                color='success' if pct_cat0 < 10 else 'warning' if pct_cat0 < 15 else 'danger'
            )
            
            cat3_nodulo = indicators.get('categoria_3_nodulo', 0)
            cat3_total = indicators.get('categoria_3_total', 0)
            ind6 = create_indicator_card(
                'Categoria 3 com Nódulo',
                f'Ref. INCA: Exames BI-RADS 3 com presença de nódulo. Encaminhamento para US de mamas e Mastologia. Total Cat. 3: {cat3_total:,}.'.replace(',', '.'),
                cat3_nodulo,
                percentage=(cat3_nodulo / cat3_total * 100) if cat3_total > 0 else 0,
                icon_class='fas fa-notes-medical'
            )
            
            cat45_rastr = indicators.get('categoria_4_5_rastreamento', 0)
            pct_cat45 = round(cat45_rastr / total_rastreamento * 100, 1) if total_rastreamento > 0 else 0
            ind7 = create_indicator_card(
                'BI-RADS 4/5 no Rastreamento',
                f'Ref. INCA: Proporção de resultados alterados (BI-RADS 4/5) no rastreamento. Necessidade de biópsia. Taxa de detecção esperada: ~6‰.',
                cat45_rastr,
                percentage=pct_cat45,
                icon_class='fas fa-exclamation-circle'
            )
            
            ind8 = create_indicator_card(
                '50-69 anos: Mamas Densas ou Cat. 0',
                'Ref. INCA: Mulheres na faixa etária alvo (50-69 anos) com mamas densas ou BI-RADS 0. Encaminhamento para US de mamas.',
                indicators.get('idade_50_69_densas_cat0', 0),
                percentage=(indicators.get('idade_50_69_densas_cat0', 0) / total * 100) if total > 0 else 0,
                icon_class='fas fa-female'
            )
            
            ind9 = create_indicator_card(
                'Idade < 49 anos: Categoria 4/5',
                'Ref. INCA: Casos suspeitos (BI-RADS 4/5) fora da faixa etária de rastreamento. Monitoramento de incidência em mulheres jovens.',
                indicators.get('idade_menor_49_cat_4_5', 0),
                icon_class='fas fa-user-clock'
            )
            
            ind10 = create_indicator_card(
                'Idade < 40 anos com Nódulo',
                'Ref. INCA: Mulheres abaixo de 40 anos com presença de nódulo no laudo. Encaminhamento para US de mamas.',
                indicators.get('idade_menor_40_nodulo', 0),
                icon_class='fas fa-user-md'
            )
            
            diag = indicators.get('diagnostico_estagio_inicial', {'rastreamento': 0, 'total': 0, 'percentual': 0})
            ind11 = create_indicator_card(
                'Diagnóstico em Estágio Inicial',
                f'Ref. INCA: Proporção de casos BI-RADS 4/5 detectados via mamografia de rastreamento. {diag["rastreamento"]:,} de {diag["total"]:,} casos.'.replace(',', '.'),
                f'{diag["percentual"]}%',
                icon_class='fas fa-microscope',
                color='success' if diag['percentual'] >= 70 else 'warning' if diag['percentual'] >= 50 else 'info'
            )
            
            return ind1, ind2, ind3, ind4, ind5, ind6, ind7, ind8, ind9, ind10, ind11
            
        except Exception as e:
            error_card = html.Div([
                html.P(f'Erro ao carregar indicadores: {str(e)}', className='text-danger')
            ])
            return (error_card,) * 11
    
    @app.callback(
        Output('download-busca-ativa-csv', 'data'),
        Input('download-busca-ativa-btn', 'n_clicks'),
        State('unit-analysis-selector', 'value'),
        State('year-filter', 'value'),
        State('region-filter', 'value'),
        prevent_initial_call=True
    )
    def download_busca_ativa_csv(n_clicks, selected_unit, year, region):
        year, region = _normalize_filter(year), _normalize_filter(region)
        region, _ = _enforce_access(region, None)
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
         Output('linkage-nomes-conferem', 'children'),
         Output('linkage-duplicados', 'children')],
        [Input('active-sidebar-tab', 'data')]
    )
    def update_linkage_summary(active_tab):
        if active_tab != 'tab-linkage':
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        try:
            summary = get_termo_linkage_summary_sql()
            duplicados_text = f"{summary['pacientes_duplicados']:,}".replace(',', '.') + f" ({summary['registros_duplicados']:,} reg)".replace(',', '.')
            return (
                f"{summary['total_registros']:,}".replace(',', '.'),
                f"{summary['com_cpf']:,}".replace(',', '.'),
                f"{summary['com_telefone']:,}".replace(',', '.'),
                f"{summary['com_nome_esaude']:,}".replace(',', '.'),
                f"{summary['com_apac_cancer']:,}".replace(',', '.'),
                f"{summary['nomes_conferem']:,}".replace(',', '.'),
                duplicados_text
            )
        except Exception as e:
            print(f"Erro ao carregar resumo linkage: {e}")
            return '0', '0', '0', '0', '0', '0', '0'
    
    @app.callback(
        [Output('comparison-exam-records', 'children'),
         Output('comparison-termo-linkage', 'children'),
         Output('comparison-unique-exam', 'children'),
         Output('comparison-unique-termo', 'children'),
         Output('comparison-common-cns', 'children'),
         Output('comparison-only-exam', 'children'),
         Output('comparison-only-termo', 'children')],
        [Input('active-sidebar-tab', 'data')]
    )
    def update_database_comparison(active_tab):
        if active_tab != 'tab-linkage':
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        try:
            from src.data_layer import get_database_comparison_sql
            comparison = get_database_comparison_sql()
            return (
                f"{comparison['total_exam_records']:,}".replace(',', '.'),
                f"{comparison['total_termo_linkage']:,}".replace(',', '.'),
                f"{comparison['unique_cns_exam']:,}".replace(',', '.'),
                f"{comparison['unique_cns_termo']:,}".replace(',', '.'),
                f"{comparison['common_cns']:,}".replace(',', '.'),
                f"{comparison['only_exam_cns']:,}".replace(',', '.'),
                f"{comparison['only_termo_cns']:,}".replace(',', '.')
            )
        except Exception as e:
            print(f"Erro ao carregar comparação: {e}")
            return '0', '0', '0', '0', '0', '0', '0'
    
    @app.callback(
        [Output('linkage-table-container', 'children'),
         Output('linkage-count-display', 'children'),
         Output('linkage-pagination', 'max_value')],
        [Input('linkage-search-button', 'n_clicks'),
         Input('linkage-pagination', 'active_page'),
         Input('data-masked-store', 'data')],
        [State('linkage-search-nome', 'value'),
         State('linkage-search-cpf', 'value'),
         State('linkage-search-cartao', 'value')]
    )
    def update_linkage_table(n_clicks, page, is_masked, search_nome, search_cpf, search_cartao):
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
            
            rows = []
            for row in df.to_dict('records'):
                is_dup = row.get('is_duplicado', False)
                qtd_dup = row.get('qtd_registros_cns', 1)
                row_style = {'backgroundColor': '#fff3cd'} if is_dup else {}
                
                cartao_masked = mask_cns(row.get('cartao_sus', ''), is_masked)
                dup_badge = html.Span([
                    dbc.Badge(f'{qtd_dup}x', color='warning', className='me-1'),
                    cartao_masked[:18]
                ]) if is_dup else cartao_masked
                
                tempest = row.get('tempestividade', '')
                tempest_cell = dbc.Badge('Tempestivo', color='success', className='px-1') if tempest == 'Tempestivo' else (dbc.Badge('Atrasado', color='danger', className='px-1') if tempest == 'Atrasado' else '-')
                
                rows.append(html.Tr([
                    html.Td(mask_name(row.get('nome_siscan', ''), is_masked), style={'fontSize': '0.75rem'}),
                    html.Td(mask_name(row.get('nome_esaude', ''), is_masked), style={'fontSize': '0.75rem'}),
                    html.Td(
                        html.I(className='fas fa-check text-success') if row.get('comparacao_nomes') in ['True', 'Sim'] else html.I(className='fas fa-times text-danger') if row.get('comparacao_nomes') else '-',
                        style={'fontSize': '0.75rem', 'textAlign': 'center'}
                    ),
                    html.Td(dup_badge, style={'fontSize': '0.75rem'}),
                    html.Td(mask_cpf(row.get('cpf', ''), is_masked), style={'fontSize': '0.75rem'}),
                    html.Td(str(row.get('data_realizacao', ''))[:10] if row.get('data_realizacao') else '-', style={'fontSize': '0.75rem'}),
                    html.Td(str(row.get('data_liberacao', ''))[:10] if row.get('data_liberacao') else '-', style={'fontSize': '0.75rem'}),
                    html.Td(str(row.get('prestador_servico', ''))[:20] if row.get('prestador_servico') else '-', style={'fontSize': '0.75rem'}),
                    html.Td(row.get('birads_max', '') if row.get('birads_max') else '-', style={'fontSize': '0.75rem'}),
                    html.Td(row.get('unidade_saude', '')[:25] if row.get('unidade_saude') else '-', style={'fontSize': '0.75rem'}),
                    html.Td(str(row.get('conclusao_apac', ''))[:10] if row.get('conclusao_apac') and str(row.get('conclusao_apac')).strip() else '-', style={'fontSize': '0.75rem'}),
                    html.Td(tempest_cell, style={'fontSize': '0.75rem', 'textAlign': 'center'})
                ], style=row_style))
            
            legend = create_table_legend([
                'nome_siscan', 'nome_esaude', 'nomes_ok', 'cartao_sus', 'cpf',
                'data_realizacao', 'data_liberacao', 'prestador_servico',
                'birads_max', 'unidade_saude', 'conclusao_apac', 'tempestividade'
            ])

            table = html.Div([
                dbc.Table([
                    html.Thead([
                        html.Tr([
                            html.Th('Nome SISCAN', style={'fontSize': '0.8rem'}),
                            html.Th('Nome eSaude', style={'fontSize': '0.8rem'}),
                            html.Th('Nomes OK', style={'fontSize': '0.8rem'}),
                            html.Th('Cartao SUS', style={'fontSize': '0.8rem'}),
                            html.Th('CPF', style={'fontSize': '0.8rem'}),
                            html.Th('Data Exame', style={'fontSize': '0.8rem'}),
                            html.Th('Liberação', style={'fontSize': '0.8rem'}),
                            html.Th('Prestador', style={'fontSize': '0.8rem'}),
                            html.Th('BI-RADS', style={'fontSize': '0.8rem'}),
                            html.Th('Unidade', style={'fontSize': '0.8rem'}),
                            html.Th('APAC', style={'fontSize': '0.8rem'}),
                            html.Th('Tempest.', style={'fontSize': '0.8rem'})
                        ])
                    ]),
                    html.Tbody(rows)
                ], bordered=True, hover=True, responsive=True, striped=True, size='sm'),
                legend
            ])
            
            count_text = f'Mostrando {offset + 1}-{min(offset + limit, total)} de {total:,} registros'.replace(',', '.')
            
            return table, count_text, max_pages
        except Exception as e:
            print(f"Erro ao carregar tabela linkage: {e}")
            return html.P(f'Erro ao carregar dados', className='text-danger text-center p-4'), '', 1
    
    @app.callback(
        Output('outliers-table', 'children', allow_duplicate=True),
        Input('outliers-sort-btn', 'n_clicks'),
        [State('outliers-sort-field', 'value'),
         State('outliers-sort-order', 'value'),
         State('year-filter', 'value'),
         State('health-unit-filter', 'value'),
         State('region-filter', 'value'),
         State('data-masked-store', 'data')],
        prevent_initial_call=True
    )
    def sort_outliers_table(n_clicks, sort_field, sort_order, year, health_unit, region, is_masked):
        if not n_clicks:
            return no_update
        
        try:
            year, health_unit, region = [_normalize_filter(v) for v in [year, health_unit, region]]
            region, health_unit = _enforce_access(region, health_unit)
            outliers_df = get_outliers_audit_sql(year, health_unit, region)
            return create_outliers_table(outliers_df, is_masked, sort_field, sort_order)
        except Exception as e:
            print(f"Erro ao ordenar outliers: {e}")
            return html.P('Erro ao ordenar dados', className='text-danger text-center p-4')
    
    @app.callback(
        Output('access-requests-table', 'children'),
        Input('refresh-access-requests-btn', 'n_clicks'),
        [State('user-access-level-store', 'data'),
         State('user-district-store', 'data')],
        prevent_initial_call=True
    )
    def refresh_access_requests(n_clicks, user_access_level, user_district):
        if not n_clicks:
            return no_update
        
        try:
            df = get_pending_access_requests(user_access_level, user_district)
            
            if df.empty:
                return dbc.Alert([
                    html.I(className='fas fa-check-circle me-2'),
                    'Não há solicitações pendentes.'
                ], color='success')
            
            access_labels = {
                'secretaria': 'Secretaria de Saúde',
                'distrito': 'Gestor de Distrito',
                'unidade': 'Unidade de Saúde'
            }
            
            rows = []
            for _, row in df.iterrows():
                location = row.get('district') or row.get('health_unit') or '-'
                rows.append(
                    html.Tr([
                        html.Td(row['name'], style={'fontSize': '0.85rem'}),
                        html.Td(row['email'], style={'fontSize': '0.85rem'}),
                        html.Td(row['matricula'], style={'fontSize': '0.85rem'}),
                        html.Td(row['username'], style={'fontSize': '0.85rem'}),
                        html.Td(access_labels.get(row['access_level'], row['access_level']), style={'fontSize': '0.85rem'}),
                        html.Td(location, style={'fontSize': '0.85rem'}),
                        html.Td(str(row['created_at'])[:10] if row['created_at'] else '-', style={'fontSize': '0.85rem'}),
                        html.Td([
                            dbc.Button(
                                html.I(className='fas fa-check'),
                                id={'type': 'approve-btn', 'index': row['id']},
                                color='success',
                                size='sm',
                                className='me-1',
                                title='Aprovar'
                            ),
                            dbc.Button(
                                html.I(className='fas fa-times'),
                                id={'type': 'reject-btn', 'index': row['id']},
                                color='danger',
                                size='sm',
                                title='Rejeitar'
                            )
                        ])
                    ])
                )
            
            access_legend = html.Details([
                html.Summary(
                    html.Small([
                        html.I(className='fas fa-info-circle me-1'),
                        'Legenda das colunas'
                    ], style={'color': COLORS['primary'], 'cursor': 'pointer', 'fontWeight': '500'}),
                ),
                html.Div(
                    html.Div([
                        html.Div([
                            html.Strong('Nome: ', style={'fontSize': '0.75rem'}),
                            html.Span('Nome completo do solicitante', style={'fontSize': '0.75rem', 'color': '#666'})
                        ], className='mb-1'),
                        html.Div([
                            html.Strong('E-mail: ', style={'fontSize': '0.75rem'}),
                            html.Span('E-mail institucional do solicitante', style={'fontSize': '0.75rem', 'color': '#666'})
                        ], className='mb-1'),
                        html.Div([
                            html.Strong('Matrícula: ', style={'fontSize': '0.75rem'}),
                            html.Span('Matrícula funcional do servidor', style={'fontSize': '0.75rem', 'color': '#666'})
                        ], className='mb-1'),
                        html.Div([
                            html.Strong('Usuário: ', style={'fontSize': '0.75rem'}),
                            html.Span('Nome de usuário desejado para login', style={'fontSize': '0.75rem', 'color': '#666'})
                        ], className='mb-1'),
                        html.Div([
                            html.Strong('Tipo Acesso: ', style={'fontSize': '0.75rem'}),
                            html.Span('Nível solicitado: Secretaria (total), Distrito (distrital) ou Unidade (local)', style={'fontSize': '0.75rem', 'color': '#666'})
                        ], className='mb-1'),
                        html.Div([
                            html.Strong('Localização: ', style={'fontSize': '0.75rem'}),
                            html.Span('Distrito ou unidade de saúde vinculada ao solicitante', style={'fontSize': '0.75rem', 'color': '#666'})
                        ], className='mb-1'),
                        html.Div([
                            html.Strong('Data: ', style={'fontSize': '0.75rem'}),
                            html.Span('Data em que a solicitação de acesso foi enviada', style={'fontSize': '0.75rem', 'color': '#666'})
                        ], className='mb-1'),
                        html.Div([
                            html.Strong('Ações: ', style={'fontSize': '0.75rem'}),
                            html.Span('Aprovar (cria usuário com senha temporária) ou Rejeitar a solicitação', style={'fontSize': '0.75rem', 'color': '#666'})
                        ], className='mb-1'),
                    ]),
                    style={
                        'padding': '8px 12px',
                        'marginTop': '6px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '6px',
                        'border': '1px solid #e9ecef'
                    }
                )
            ], className='mt-2 mb-0')

            table = html.Div([
                dbc.Table([
                    html.Thead([
                        html.Tr([
                            html.Th('Nome'),
                            html.Th('E-mail'),
                            html.Th('Matrícula'),
                            html.Th('Usuário'),
                            html.Th('Tipo Acesso'),
                            html.Th('Localização'),
                            html.Th('Data'),
                            html.Th('Ações')
                        ], style={'backgroundColor': COLORS['primary'], 'color': 'white'})
                    ]),
                    html.Tbody(rows)
                ], bordered=True, hover=True, responsive=True, striped=True, size='sm'),
                access_legend
            ])
            
            return dbc.Card([
                dbc.CardBody([
                    html.H6(f'{len(df)} solicitação(ões) pendente(s)', className='mb-3'),
                    table,
                    html.Div(id='access-action-result', className='mt-3')
                ])
            ])
        except Exception as e:
            return dbc.Alert(f'Erro ao carregar solicitações: {str(e)}', color='danger')
    
    @app.callback(
        Output('access-action-result', 'children'),
        Input({'type': 'approve-btn', 'index': ALL}, 'n_clicks'),
        Input({'type': 'reject-btn', 'index': ALL}, 'n_clicks'),
        prevent_initial_call=True
    )
    def handle_access_request_action(approve_clicks, reject_clicks):
        import dash
        ctx = callback_context
        
        if not ctx.triggered:
            return no_update
        
        triggered = ctx.triggered[0]
        prop_id = triggered['prop_id']
        
        if triggered['value'] is None:
            return no_update
        
        import json
        try:
            button_id = json.loads(prop_id.split('.')[0])
            action_type = button_id['type']
            request_id = button_id['index']
        except:
            return no_update
        
        from flask_login import current_user
        reviewed_by = getattr(current_user, 'username', 'admin')
        
        if action_type == 'approve-btn':
            result = approve_access_request(request_id, reviewed_by)
            if result['success']:
                temp_password = result.get('temp_password', '')
                return dbc.Alert([
                    html.I(className='fas fa-check-circle me-2'),
                    html.Div([
                        html.Strong('Solicitação aprovada com sucesso!'),
                        html.P([
                            'Senha temporária: ',
                            html.Code(temp_password, style={'fontSize': '1.1rem', 'backgroundColor': '#f8f9fa', 'padding': '5px 10px', 'borderRadius': '4px'})
                        ], className='mb-0 mt-2'),
                        html.Small('Forneça esta senha ao usuário. Ele deverá alterá-la no primeiro acesso.', className='text-muted'),
                        html.Hr(),
                        html.Small('Atualize a página ou troque de aba para ver a lista atualizada.', className='text-info')
                    ])
                ], color='success', dismissable=True)
            else:
                return dbc.Alert([
                    html.I(className='fas fa-exclamation-circle me-2'),
                    result.get('message', 'Erro ao aprovar solicitação')
                ], color='danger', dismissable=True)
        
        elif action_type == 'reject-btn':
            result = reject_access_request(request_id)
            if result['success']:
                return dbc.Alert([
                    html.I(className='fas fa-check-circle me-2'),
                    'Solicitação rejeitada. Atualize a página ou troque de aba para ver a lista atualizada.'
                ], color='warning', dismissable=True)
            else:
                return dbc.Alert([
                    html.I(className='fas fa-exclamation-circle me-2'),
                    result.get('message', 'Erro ao rejeitar solicitação')
                ], color='danger', dismissable=True)
        
        return no_update
