import plotly.express as px
import plotly.graph_objects as go
from dash import dcc
from src.config import COLORS, BIRADS_COLORS, CONFORMITY_TARGET


def create_empty_figure(message="Sem dados disponíveis"):
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color=COLORS['text_muted'])
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        height=300
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def create_line_chart(df, x_col, y_col, title=None):
    if df.empty:
        return create_empty_figure()
    
    fig = px.line(
        df, 
        x=x_col, 
        y=y_col,
        markers=True,
        color_discrete_sequence=[COLORS['secondary']]
    )
    
    fig.update_traces(
        line=dict(width=3),
        marker=dict(size=8)
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=20, t=30, b=40),
        height=350,
        xaxis=dict(
            title='',
            gridcolor='rgba(0,0,0,0.05)',
            tickangle=-45
        ),
        yaxis=dict(
            title='Volume',
            gridcolor='rgba(0,0,0,0.05)'
        ),
        hovermode='x unified'
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': True, 'displaylogo': False})


def create_bar_chart(df, x_col, y_col, orientation='v', color=None, title=None):
    if df.empty:
        return create_empty_figure()
    
    if orientation == 'v':
        fig = px.bar(
            df, 
            x=x_col, 
            y=y_col,
            color=color,
            color_discrete_sequence=[COLORS['secondary']]
        )
    else:
        fig = px.bar(
            df, 
            x=y_col, 
            y=x_col,
            orientation='h',
            color=color,
            color_discrete_sequence=[COLORS['secondary']]
        )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=20, t=30, b=40),
        height=350,
        xaxis=dict(
            gridcolor='rgba(0,0,0,0.05)'
        ),
        yaxis=dict(
            gridcolor='rgba(0,0,0,0.05)'
        ),
        showlegend=False
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': True, 'displaylogo': False})


def create_birads_bar_chart(df):
    if df.empty:
        return create_empty_figure()
    
    colors = [BIRADS_COLORS.get(str(cat), COLORS['secondary']) for cat in df['birads_category']]
    
    fig = go.Figure(data=[
        go.Bar(
            x=df['birads_category'],
            y=df['count'],
            marker_color=colors,
            text=df['count'],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=20, t=30, b=40),
        height=350,
        xaxis=dict(
            title='Categoria BI-RADS',
            gridcolor='rgba(0,0,0,0.05)'
        ),
        yaxis=dict(
            title='Quantidade',
            gridcolor='rgba(0,0,0,0.05)'
        )
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': True, 'displaylogo': False})


def create_conformity_chart(df):
    if df.empty:
        return create_empty_figure()
    
    num_units = len(df)
    chart_height = max(400, num_units * 25)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df['health_unit'],
        x=df['conformity_rate'],
        orientation='h',
        marker_color=[
            COLORS['success'] if rate >= 70 else COLORS['warning'] if rate >= 50 else COLORS['danger']
            for rate in df['conformity_rate']
        ],
        text=[f'{rate:.1f}%' for rate in df['conformity_rate']],
        textposition='auto'
    ))
    
    fig.add_vline(
        x=70,
        line_dash="dash",
        line_color=COLORS['success'],
        annotation_text="Meta (70%)",
        annotation_position="top right"
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=200, r=30, t=30, b=40),
        height=chart_height,
        xaxis=dict(
            title='Taxa de Conformidade (%)',
            range=[0, 100],
            gridcolor='rgba(0,0,0,0.05)'
        ),
        yaxis=dict(
            title='',
            gridcolor='rgba(0,0,0,0.05)',
            tickfont=dict(size=11)
        )
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': True, 'displaylogo': False})


def create_pie_chart(df, names_col, values_col):
    if df.empty:
        return create_empty_figure()
    
    fig = px.pie(
        df,
        names=names_col,
        values=values_col,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label'
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=30, b=20),
        height=350,
        showlegend=False
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': True, 'displaylogo': False})


def create_gauge_chart(value, title, max_value=100):
    color = COLORS['success'] if value >= 70 else COLORS['warning'] if value >= 50 else COLORS['danger']
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 14}},
        number={'suffix': '%', 'font': {'size': 28}},
        gauge={
            'axis': {'range': [0, max_value], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': 'white',
            'borderwidth': 2,
            'bordercolor': 'gray',
            'steps': [
                {'range': [0, 50], 'color': 'rgba(231, 76, 60, 0.2)'},
                {'range': [50, 70], 'color': 'rgba(243, 156, 18, 0.2)'},
                {'range': [70, 100], 'color': 'rgba(39, 174, 96, 0.2)'}
            ],
            'threshold': {
                'line': {'color': COLORS['success'], 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=50, b=20),
        height=250
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def create_demographics_heatmap(df):
    """Create heatmap showing patients by age group and BI-RADS"""
    if df.empty:
        return create_empty_figure("Selecione uma unidade de saúde")
    
    pivot_df = df.pivot_table(
        index='faixa_etaria', 
        columns='birads_max', 
        values='total', 
        fill_value=0,
        aggfunc='sum'
    )
    
    age_order = ['< 30 anos', '30-39 anos', '40-49 anos', '50-59 anos', '60-69 anos', '70+ anos', 'Não informado']
    existing_ages = [a for a in age_order if a in pivot_df.index]
    pivot_df = pivot_df.reindex(existing_ages)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns.tolist(),
        y=pivot_df.index.tolist(),
        colorscale='Blues',
        text=pivot_df.values,
        texttemplate='%{text}',
        textfont={'size': 12},
        hovertemplate='Faixa Etária: %{y}<br>BI-RADS: %{x}<br>Total: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=100, r=20, t=30, b=40),
        height=350,
        xaxis=dict(
            title='BI-RADS',
            side='bottom'
        ),
        yaxis=dict(
            title='Faixa Etária',
            autorange='reversed'
        )
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': True, 'displaylogo': False})


def create_agility_chart(df):
    """Create bar chart showing service agility distribution"""
    if df.empty:
        return create_empty_figure("Selecione uma unidade de saúde")
    
    colors = {
        'Até 7 dias': COLORS['success'],
        '8-14 dias': '#52c41a',
        '15-30 dias': COLORS['warning'],
        '31-60 dias': '#fa8c16',
        '> 60 dias': COLORS['danger'],
        'Não informado': COLORS['text_muted']
    }
    
    bar_colors = [colors.get(cat, COLORS['secondary']) for cat in df['faixa_espera']]
    
    fig = go.Figure(data=[
        go.Bar(
            x=df['faixa_espera'],
            y=df['total'],
            marker_color=bar_colors,
            text=[f'{t} ({p}%)' for t, p in zip(df['total'], df['percentual'])],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=20, t=30, b=60),
        height=350,
        xaxis=dict(
            title='Tempo de Espera',
            gridcolor='rgba(0,0,0,0.05)',
            tickangle=-30
        ),
        yaxis=dict(
            title='Quantidade de Exames',
            gridcolor='rgba(0,0,0,0.05)'
        )
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': True, 'displaylogo': False})


def create_wait_time_trend_chart(df):
    """Create line chart showing monthly average wait time trend"""
    if df.empty:
        return create_empty_figure("Selecione uma unidade de saúde")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['mes'],
        y=df['media_espera'],
        mode='lines+markers',
        name='Média',
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['mes'],
        y=df['mediana_espera'],
        mode='lines+markers',
        name='Mediana',
        line=dict(color=COLORS['secondary'], width=2, dash='dash'),
        marker=dict(size=6)
    ))
    
    fig.add_hline(
        y=30,
        line_dash="dot",
        line_color=COLORS['danger'],
        annotation_text="Meta 30 dias",
        annotation_position="right"
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=20, t=30, b=60),
        height=350,
        xaxis=dict(
            title='Mês',
            gridcolor='rgba(0,0,0,0.05)',
            tickangle=-45
        ),
        yaxis=dict(
            title='Dias de Espera',
            gridcolor='rgba(0,0,0,0.05)'
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        hovermode='x unified'
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': True, 'displaylogo': False})
