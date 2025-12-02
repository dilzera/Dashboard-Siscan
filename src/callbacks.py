from dash import Input, Output, State, callback
from datetime import datetime
from src.data_layer import (
    get_filtered_data, get_kpi_data, get_monthly_volume,
    get_birads_distribution, get_conformity_by_unit, get_high_risk_cases
)
from src.components.cards import create_kpi_card, create_chart_card
from src.components.charts import (
    create_line_chart, create_birads_bar_chart,
    create_conformity_chart, create_gauge_chart, create_pie_chart
)
from src.components.tables import create_high_risk_table


def register_callbacks(app):
    
    @app.callback(
        [
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
            Output('last-update', 'children')
        ],
        [
            Input('year-filter', 'value'),
            Input('health-unit-filter', 'value'),
            Input('region-filter', 'value'),
            Input('conformity-filter', 'value'),
            Input('refresh-btn', 'n_clicks'),
            Input('interval-component', 'n_intervals')
        ]
    )
    def update_dashboard(year, health_unit, region, conformity, n_clicks, n_intervals):
        df = get_filtered_data(
            year=year,
            health_unit=health_unit,
            conformity_status=conformity,
            region=region
        )
        
        kpis = get_kpi_data(df)
        
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
            f'{kpis["total_exams"]} exames no período',
            color=conformity_color
        )
        
        risk_color = 'danger' if kpis['high_risk_count'] > 100 else 'warning' if kpis['high_risk_count'] > 50 else 'info'
        kpi_risk = create_kpi_card(
            'Casos Alto Risco',
            str(kpis['high_risk_count']),
            'BI-RADS 4 e 5',
            color=risk_color
        )
        
        monthly_df = get_monthly_volume(df)
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
        
        conformity_df = get_conformity_by_unit(df)
        chart_conformity = create_chart_card(
            'Conformidade por Unidade de Saúde',
            create_conformity_chart(conformity_df),
            'Top 10 unidades por volume'
        )
        
        birads_df = get_birads_distribution(df)
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
        
        high_risk_df = get_high_risk_cases(df)
        table_risk = create_high_risk_table(high_risk_df)
        
        last_update = f'Última atualização: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'
        
        return (
            kpi_mean, kpi_median, kpi_conformity, kpi_risk,
            chart_volume, gauge_chart, chart_conformity,
            chart_birads, chart_birads_pie, table_risk,
            last_update
        )
