from dash import Input, Output, State, html, dcc, callback_context
from datetime import datetime
import pandas as pd
from src.data_layer import (
    get_kpi_data_sql, get_monthly_volume_sql,
    get_birads_distribution_sql, get_conformity_by_unit_sql, get_high_risk_cases_sql,
    get_outliers_audit_sql, get_outliers_summary_sql
)
from src.components.cards import create_kpi_card, create_chart_card
from src.components.charts import (
    create_line_chart, create_birads_bar_chart,
    create_conformity_chart, create_gauge_chart, create_pie_chart
)
from src.components.tables import create_high_risk_table, create_outliers_table, create_outliers_summary_cards


def build_dashboard_content(year=None, health_unit=None, region=None, conformity=None):
    kpis = get_kpi_data_sql(year, health_unit, region, conformity)
    monthly_df = get_monthly_volume_sql(year, health_unit, region, conformity)
    birads_df = get_birads_distribution_sql(year, health_unit, region, conformity)
    conformity_df = get_conformity_by_unit_sql(year, health_unit, region, conformity)
    high_risk_df = get_high_risk_cases_sql(year, health_unit, region, conformity)
    
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
        'Casos Alto Risco',
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
        Output('last-update-display', 'children'),
        Input('refresh-btn', 'n_clicks'),
        State('year-filter', 'value'),
        State('health-unit-filter', 'value'),
        State('region-filter', 'value'),
        State('conformity-filter', 'value'),
        prevent_initial_call=True
    )
    def update_dashboard(n_clicks, year, health_unit, region, conformity):
        try:
            content = build_dashboard_content(year, health_unit, region, conformity)
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
                error_card, error_card, error_card, error_card, error_message
            )
