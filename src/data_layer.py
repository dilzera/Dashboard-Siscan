import pandas as pd
from sqlalchemy import text
from src.models import get_engine
from datetime import datetime, timedelta


def _get_outlier_exclusion_conditions():
    """
    Returns SQL conditions to exclude outliers from performance calculations.
    Outlier categories:
    - A: Request dates before 2023-01-01 (only show data from Jan 2023 onwards)
    - B: Completion/release dates before request date (negative delta)
    - C: Invalid BI-RADS values (NULL, empty, or non-numeric)
    - D: Wait time > 365 days
    """
    return [
        "unidade_de_saude__data_da_solicitacao >= '2023-01-01'",
        "(prestador_de_servico__data_da_realizacao IS NULL OR prestador_de_servico__data_da_realizacao >= unidade_de_saude__data_da_solicitacao)",
        "(responsavel_pelo_resultado__data_da_liberacao IS NULL OR responsavel_pelo_resultado__data_da_liberacao >= unidade_de_saude__data_da_solicitacao)",
        "(wait_days IS NULL OR wait_days <= 365)",
        "(birads_max IS NOT NULL AND birads_max != '' AND birads_max ~ '^[0-9]+$')"
    ]


def _build_where_clause(year=None, health_unit=None, region=None, conformity_status=None, exclude_outliers=False):
    conditions = []
    params = {}
    
    if exclude_outliers:
        conditions.extend(_get_outlier_exclusion_conditions())
    
    if year:
        conditions.append("year = :year")
        params['year'] = year
    
    if health_unit:
        conditions.append("unidade_de_saude__nome = :health_unit")
        params['health_unit'] = health_unit
    
    if conformity_status:
        conditions.append("conformity_status = :conformity_status")
        params['conformity_status'] = conformity_status
    
    if region:
        conditions.append("unidade_de_saude__uf = :region")
        params['region'] = region
    
    where_clause = ""
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
    
    return where_clause, params


def get_years():
    return [2026, 2025, 2024, 2023]


def get_health_units():
    engine = get_engine()
    query = "SELECT DISTINCT unidade_de_saude__nome FROM exam_records WHERE unidade_de_saude__nome IS NOT NULL ORDER BY unidade_de_saude__nome LIMIT 500"
    with engine.connect() as conn:
        result = conn.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df['unidade_de_saude__nome'].dropna().tolist()


def get_regions():
    engine = get_engine()
    query = "SELECT DISTINCT unidade_de_saude__uf FROM exam_records WHERE unidade_de_saude__uf IS NOT NULL ORDER BY unidade_de_saude__uf"
    with engine.connect() as conn:
        result = conn.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df['unidade_de_saude__uf'].dropna().tolist()


def get_kpi_data_sql(year=None, health_unit=None, region=None, conformity_status=None):
    where_clause, params = _build_where_clause(year, health_unit, region, conformity_status, exclude_outliers=True)
    
    query = f"""
    SELECT 
        COUNT(*) as total_exams,
        COALESCE(AVG(wait_days), 0) as mean_wait,
        COALESCE(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY wait_days), 0) as median_wait,
        COUNT(CASE WHEN conformity_status = 'Dentro do Prazo' THEN 1 END) as conformity_count,
        COUNT(CASE WHEN birads_max IN ('4', '5') THEN 1 END) as high_risk_count,
        COUNT(DISTINCT patient_unique_id) as unique_patients
    FROM exam_records
    {where_clause}
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        row = result.fetchone()
    
    total_exams = row[0] or 0
    mean_wait = float(row[1]) if row[1] else 0
    median_wait = float(row[2]) if row[2] else 0
    conformity_count = row[3] or 0
    high_risk_count = row[4] or 0
    unique_patients = row[5] or 0
    
    conformity_rate = (conformity_count / total_exams * 100) if total_exams > 0 else 0
    
    return {
        'mean_wait': round(mean_wait, 1),
        'median_wait': round(median_wait, 1),
        'conformity_rate': round(conformity_rate, 1),
        'total_exams': total_exams,
        'high_risk_count': high_risk_count,
        'unique_patients': unique_patients
    }


def get_monthly_volume_sql(year=None, health_unit=None, region=None, conformity_status=None):
    where_clause, params = _build_where_clause(year, health_unit, region, conformity_status, exclude_outliers=True)
    
    query = f"""
    SELECT 
        TO_CHAR(unidade_de_saude__data_da_solicitacao, 'YYYY-MM') as month_year,
        COUNT(*) as count
    FROM exam_records
    {where_clause}
    {"AND" if where_clause else "WHERE"} unidade_de_saude__data_da_solicitacao IS NOT NULL
    GROUP BY TO_CHAR(unidade_de_saude__data_da_solicitacao, 'YYYY-MM')
    ORDER BY month_year
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_birads_distribution_sql(year=None, health_unit=None, region=None, conformity_status=None):
    where_clause, params = _build_where_clause(year, health_unit, region, conformity_status, exclude_outliers=True)
    
    query = f"""
    SELECT 
        birads_max as birads_category,
        COUNT(*) as count
    FROM exam_records
    {where_clause}
    GROUP BY birads_max
    ORDER BY birads_max
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_conformity_by_unit_sql(year=None, health_unit=None, region=None, conformity_status=None):
    where_clause, params = _build_where_clause(year, health_unit, region, conformity_status, exclude_outliers=True)
    
    query = f"""
    SELECT 
        unidade_de_saude__nome as health_unit,
        COUNT(*) as total,
        COUNT(CASE WHEN conformity_status = 'Dentro do Prazo' THEN 1 END) as dentro_prazo,
        COUNT(CASE WHEN conformity_status = 'Fora do Prazo' THEN 1 END) as fora_prazo
    FROM exam_records
    {where_clause}
    {"AND" if where_clause else "WHERE"} unidade_de_saude__nome IS NOT NULL
    GROUP BY unidade_de_saude__nome
    ORDER BY total DESC
    LIMIT 10
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    if not df.empty:
        df['Dentro do Prazo'] = df['dentro_prazo']
        df['Fora do Prazo'] = df['fora_prazo']
        df['conformity_rate'] = (df['Dentro do Prazo'] / df['total'] * 100).round(1)
    
    return df


def get_high_risk_cases_sql(year=None, health_unit=None, region=None, conformity_status=None, limit=20):
    where_clause, params = _build_where_clause(year, health_unit, region, conformity_status, exclude_outliers=True)
    
    query = f"""
    SELECT 
        patient_unique_id as patient_id,
        paciente__nome as patient_name,
        unidade_de_saude__nome as health_unit,
        birads_max as birads_category,
        wait_days,
        conformity_status,
        unidade_de_saude__data_da_solicitacao as request_date
    FROM exam_records
    {where_clause}
    {"AND" if where_clause else "WHERE"} birads_max IN ('4', '5')
    ORDER BY wait_days DESC NULLS LAST
    LIMIT :limit_val
    """
    params['limit_val'] = limit
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_filtered_data(year=None, health_unit=None, conformity_status=None, region=None, municipality=None):
    conditions = []
    params = {}
    
    if year:
        conditions.append("year = :year")
        params['year'] = year
    
    if health_unit:
        conditions.append("unidade_de_saude__nome = :health_unit")
        params['health_unit'] = health_unit
    
    if conformity_status:
        conditions.append("conformity_status = :conformity_status")
        params['conformity_status'] = conformity_status
    
    if region:
        conditions.append("unidade_de_saude__uf = :region")
        params['region'] = region
    
    if municipality:
        conditions.append("unidade_de_saude__municipio = :municipality")
        params['municipality'] = municipality
    
    query = "SELECT * FROM exam_records"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " LIMIT 1000"
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df


def get_kpi_data(df):
    if df.empty:
        return {
            'mean_wait': 0,
            'median_wait': 0,
            'conformity_rate': 0,
            'total_exams': 0,
            'high_risk_count': 0,
            'unique_patients': 0
        }
    
    wait_df = df['wait_days'].dropna()
    mean_wait = wait_df.mean() if len(wait_df) > 0 else 0
    median_wait = wait_df.median() if len(wait_df) > 0 else 0
    
    conformity_df = df['conformity_status'].dropna()
    if len(conformity_df) > 0:
        conformity_rate = (conformity_df == 'Dentro do Prazo').sum() / len(conformity_df) * 100
    else:
        conformity_rate = 0
    
    total_exams = len(df)
    high_risk_count = df[df['birads_max'].isin(['4', '5'])].shape[0]
    unique_patients = df['patient_unique_id'].nunique()
    
    return {
        'mean_wait': round(mean_wait, 1) if pd.notna(mean_wait) else 0,
        'median_wait': round(median_wait, 1) if pd.notna(median_wait) else 0,
        'conformity_rate': round(conformity_rate, 1),
        'total_exams': total_exams,
        'high_risk_count': high_risk_count,
        'unique_patients': unique_patients
    }


def get_monthly_volume(df):
    if df.empty:
        return pd.DataFrame()
    
    df_copy = df.copy()
    df_copy['request_date'] = pd.to_datetime(df_copy['unidade_de_saude__data_da_solicitacao'])
    df_copy = df_copy.dropna(subset=['request_date'])
    
    if df_copy.empty:
        return pd.DataFrame()
    
    df_copy['month_year'] = df_copy['request_date'].dt.to_period('M')
    monthly = df_copy.groupby('month_year').size().reset_index(name='count')
    monthly['month_year'] = monthly['month_year'].astype(str)
    return monthly


def get_birads_distribution(df):
    if df.empty:
        return pd.DataFrame()
    
    df_copy = df.copy()
    df_copy = df_copy[df_copy['birads_max'].notna()]
    
    if df_copy.empty:
        return pd.DataFrame()
    
    dist = df_copy.groupby('birads_max').size().reset_index(name='count')
    dist.columns = ['birads_category', 'count']
    dist = dist.sort_values('birads_category')
    return dist


def get_conformity_by_unit(df):
    if df.empty:
        return pd.DataFrame()
    
    df_copy = df.copy()
    df_copy = df_copy[df_copy['unidade_de_saude__nome'].notna() & df_copy['conformity_status'].notna()]
    
    if df_copy.empty:
        return pd.DataFrame()
    
    grouped = df_copy.groupby(['unidade_de_saude__nome', 'conformity_status']).size().unstack(fill_value=0)
    grouped = grouped.reset_index()
    grouped.columns.name = None
    
    if 'Dentro do Prazo' in grouped.columns and 'Fora do Prazo' in grouped.columns:
        grouped['total'] = grouped['Dentro do Prazo'] + grouped['Fora do Prazo']
        grouped['conformity_rate'] = (grouped['Dentro do Prazo'] / grouped['total'] * 100).round(1)
    elif 'Dentro do Prazo' in grouped.columns:
        grouped['total'] = grouped['Dentro do Prazo']
        grouped['conformity_rate'] = 100.0
    elif 'Fora do Prazo' in grouped.columns:
        grouped['total'] = grouped['Fora do Prazo']
        grouped['conformity_rate'] = 0.0
    else:
        grouped['total'] = 0
        grouped['conformity_rate'] = 0.0
    
    grouped = grouped.rename(columns={'unidade_de_saude__nome': 'health_unit'})
    return grouped.sort_values('total', ascending=False).head(10)


def get_high_risk_cases(df):
    if df.empty:
        return pd.DataFrame()
    
    high_risk = df[df['birads_max'].isin(['4', '5'])].copy()
    
    if high_risk.empty:
        return pd.DataFrame()
    
    high_risk = high_risk.sort_values('wait_days', ascending=False, na_position='last')
    
    result = high_risk[['patient_unique_id', 'paciente__nome', 'unidade_de_saude__nome', 
                        'birads_max', 'wait_days', 'conformity_status', 
                        'unidade_de_saude__data_da_solicitacao']].head(20)
    
    result = result.rename(columns={
        'patient_unique_id': 'patient_id',
        'paciente__nome': 'patient_name',
        'unidade_de_saude__nome': 'health_unit',
        'birads_max': 'birads_category',
        'unidade_de_saude__data_da_solicitacao': 'request_date'
    })
    
    return result


def get_outliers_audit_sql():
    query = """
    WITH outliers AS (
        SELECT 
            paciente__nome AS nome_paciente,
            paciente__cartao_sus AS cartao_sus,
            unidade_de_saude__data_da_solicitacao AS data_solicitacao,
            prestador_de_servico__data_da_realizacao AS data_realizacao,
            responsavel_pelo_resultado__data_da_liberacao AS data_liberacao,
            birads_max,
            wait_days,
            CASE 
                WHEN unidade_de_saude__data_da_solicitacao < '2020-01-01' THEN 'A'
                WHEN prestador_de_servico__data_da_realizacao < unidade_de_saude__data_da_solicitacao THEN 'B'
                WHEN responsavel_pelo_resultado__data_da_liberacao < unidade_de_saude__data_da_solicitacao THEN 'B'
                WHEN birads_max IS NULL OR birads_max = '' OR birads_max !~ '^[0-9]+$' THEN 'C'
                WHEN wait_days > 365 THEN 'D'
                ELSE NULL
            END AS motivo_outlier,
            CASE 
                WHEN unidade_de_saude__data_da_solicitacao < '2020-01-01' 
                    THEN unidade_de_saude__data_da_solicitacao::TEXT
                WHEN prestador_de_servico__data_da_realizacao < unidade_de_saude__data_da_solicitacao 
                    THEN prestador_de_servico__data_da_realizacao::TEXT
                WHEN responsavel_pelo_resultado__data_da_liberacao < unidade_de_saude__data_da_solicitacao 
                    THEN responsavel_pelo_resultado__data_da_liberacao::TEXT
                WHEN birads_max IS NULL OR birads_max = '' OR birads_max !~ '^[0-9]+$'
                    THEN COALESCE(birads_max, 'NULL')
                WHEN wait_days > 365 
                    THEN unidade_de_saude__data_da_solicitacao::TEXT
                ELSE NULL
            END AS data_inconsistente,
            CASE 
                WHEN unidade_de_saude__data_da_solicitacao < '2020-01-01' 
                    THEN (unidade_de_saude__data_da_solicitacao - '2020-01-01'::DATE) || ' dias antes de 2020'
                WHEN prestador_de_servico__data_da_realizacao < unidade_de_saude__data_da_solicitacao 
                    THEN (prestador_de_servico__data_da_realizacao - unidade_de_saude__data_da_solicitacao) || ' dias (delta negativo)'
                WHEN responsavel_pelo_resultado__data_da_liberacao < unidade_de_saude__data_da_solicitacao 
                    THEN (responsavel_pelo_resultado__data_da_liberacao - unidade_de_saude__data_da_solicitacao) || ' dias (delta negativo)'
                WHEN birads_max IS NULL OR birads_max = '' OR birads_max !~ '^[0-9]+$'
                    THEN 'BI-RADS inválido: ' || COALESCE(birads_max, 'VAZIO')
                WHEN wait_days > 365 
                    THEN wait_days || ' dias de espera'
                ELSE NULL
            END AS valor_critico
        FROM exam_records
    )
    SELECT 
        nome_paciente,
        cartao_sus,
        data_inconsistente,
        valor_critico,
        motivo_outlier AS motivo_do_outlier,
        CASE motivo_outlier
            WHEN 'A' THEN 'Data Absurda (antes de 2020)'
            WHEN 'B' THEN 'Delta Negativo'
            WHEN 'C' THEN 'BI-RADS Inválido'
            WHEN 'D' THEN 'Espera > 365 dias'
        END AS descricao_motivo
    FROM outliers
    WHERE motivo_outlier IS NOT NULL
    ORDER BY motivo_outlier, data_solicitacao
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_outliers_summary_sql():
    query = """
    SELECT 
        motivo_outlier,
        descricao,
        COUNT(*) as total_registros
    FROM (
        SELECT 
            CASE 
                WHEN unidade_de_saude__data_da_solicitacao < '2020-01-01' THEN 'A'
                WHEN prestador_de_servico__data_da_realizacao < unidade_de_saude__data_da_solicitacao THEN 'B'
                WHEN responsavel_pelo_resultado__data_da_liberacao < unidade_de_saude__data_da_solicitacao THEN 'B'
                WHEN birads_max IS NULL OR birads_max = '' OR birads_max !~ '^[0-9]+$' THEN 'C'
                WHEN wait_days > 365 THEN 'D'
                ELSE NULL
            END AS motivo_outlier,
            CASE 
                WHEN unidade_de_saude__data_da_solicitacao < '2020-01-01' THEN 'Data Absurda (antes de 2020)'
                WHEN prestador_de_servico__data_da_realizacao < unidade_de_saude__data_da_solicitacao THEN 'Delta Negativo (realização antes da solicitação)'
                WHEN responsavel_pelo_resultado__data_da_liberacao < unidade_de_saude__data_da_solicitacao THEN 'Delta Negativo (liberação antes da solicitação)'
                WHEN birads_max IS NULL OR birads_max = '' OR birads_max !~ '^[0-9]+$' THEN 'BI-RADS Inválido'
                WHEN wait_days > 365 THEN 'Espera > 365 dias'
                ELSE 'OK'
            END AS descricao
        FROM exam_records
    ) subquery
    WHERE motivo_outlier IS NOT NULL
    GROUP BY motivo_outlier, descricao
    ORDER BY motivo_outlier
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df
