import pandas as pd
from sqlalchemy import text
from src.models import get_engine
from datetime import datetime, timedelta
from src.cache import cached


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


def _build_where_clause(year=None, health_unit=None, region=None, conformity_status=None, exclude_outliers=False, age_range=None, birads=None, priority=None):
    conditions = []
    params = {}
    
    if exclude_outliers:
        conditions.extend(_get_outlier_exclusion_conditions())
    
    if year:
        conditions.append("year = :year")
        params['year'] = year
    
    if health_unit:
        conditions.append("(unidade_de_saude__nome = :health_unit OR prestador_de_servico__nome = :health_unit)")
        params['health_unit'] = health_unit
    
    if conformity_status:
        conditions.append("conformity_status = :conformity_status")
        params['conformity_status'] = conformity_status
    
    if region:
        conditions.append("distrito_sanitario = :region")
        params['region'] = region
    
    if age_range:
        if age_range == '0-39':
            conditions.append("paciente__idade < 40")
        elif age_range == '40-49':
            conditions.append("paciente__idade >= 40 AND paciente__idade < 50")
        elif age_range == '50-69':
            conditions.append("paciente__idade >= 50 AND paciente__idade < 70")
        elif age_range == '70+':
            conditions.append("paciente__idade >= 70")
    
    if birads:
        conditions.append("birads_max = :birads")
        params['birads'] = birads
    
    if priority:
        if priority == 'CRITICA':
            conditions.append("birads_max IN ('4', '5')")
        elif priority == 'ALTA':
            conditions.append("birads_max = '0'")
        elif priority == 'MEDIA':
            conditions.append("birads_max = '3'")
        elif priority == 'MONITORAMENTO':
            conditions.append("birads_max = '6'")
        elif priority == 'ROTINA':
            conditions.append("birads_max IN ('1', '2')")
    
    where_clause = ""
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
    
    return where_clause, params


def get_years():
    return [2026, 2025, 2024, 2023]


@cached(ttl=600)
def get_health_units():
    engine = get_engine()
    query = """
        SELECT DISTINCT name FROM (
            SELECT unidade_de_saude__nome AS name FROM exam_records WHERE unidade_de_saude__nome IS NOT NULL
            UNION
            SELECT prestador_de_servico__nome AS name FROM exam_records WHERE prestador_de_servico__nome IS NOT NULL
        ) combined
        ORDER BY name LIMIT 500
    """
    with engine.connect() as conn:
        result = conn.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df['name'].dropna().tolist()


@cached(ttl=600)
def get_regions():
    engine = get_engine()
    query = "SELECT DISTINCT distrito_sanitario FROM exam_records WHERE distrito_sanitario IS NOT NULL ORDER BY distrito_sanitario"
    with engine.connect() as conn:
        result = conn.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df['distrito_sanitario'].dropna().tolist()


@cached(ttl=120)
def get_kpi_data_sql(year=None, health_unit=None, region=None, conformity_status=None, age_range=None, birads=None, priority=None):
    where_clause, params = _build_where_clause(year, health_unit, region, conformity_status, exclude_outliers=True, age_range=age_range, birads=birads, priority=priority)
    
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


@cached(ttl=120)
def get_monthly_volume_sql(year=None, health_unit=None, region=None, conformity_status=None, age_range=None, birads=None, priority=None):
    where_clause, params = _build_where_clause(year, health_unit, region, conformity_status, exclude_outliers=True, age_range=age_range, birads=birads, priority=priority)
    
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


@cached(ttl=120)
def get_birads_distribution_sql(year=None, health_unit=None, region=None, conformity_status=None, age_range=None, birads=None, priority=None):
    where_clause, params = _build_where_clause(year, health_unit, region, conformity_status, exclude_outliers=True, age_range=age_range, birads=birads, priority=priority)
    
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


@cached(ttl=120)
def get_conformity_by_unit_sql(year=None, health_unit=None, region=None, conformity_status=None, age_range=None, birads=None, priority=None):
    where_clause, params = _build_where_clause(year, health_unit, region, conformity_status, exclude_outliers=True, age_range=age_range, birads=birads, priority=priority)
    
    query = f"""
    SELECT 
        unidade_de_saude__nome as health_unit,
        COUNT(*) as total,
        COUNT(CASE WHEN conformity_status = 'Dentro do Prazo' THEN 1 END) as dentro_prazo,
        COUNT(CASE WHEN conformity_status = 'Fora do Prazo' THEN 1 END) as fora_prazo,
        ROUND(COUNT(CASE WHEN conformity_status = 'Dentro do Prazo' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 1) as conformity_rate
    FROM exam_records
    {where_clause}
    {"AND" if where_clause else "WHERE"} unidade_de_saude__nome IS NOT NULL
    GROUP BY unidade_de_saude__nome
    ORDER BY conformity_rate DESC NULLS LAST
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    if not df.empty:
        df['Dentro do Prazo'] = df['dentro_prazo']
        df['Fora do Prazo'] = df['fora_prazo']
    
    return df


@cached(ttl=120)
def get_high_risk_cases_sql(year=None, health_unit=None, region=None, conformity_status=None, age_range=None, birads=None, priority=None, limit=20):
    where_clause, params = _build_where_clause(year, health_unit, region, conformity_status, exclude_outliers=True, age_range=age_range, birads=birads, priority=priority)
    
    query = f"""
    SELECT 
        patient_unique_id as patient_id,
        paciente__nome as patient_name,
        paciente__cartao_sus as patient_cns,
        paciente__telefone as patient_phone,
        unidade_de_saude__nome as health_unit,
        birads_max as birads_category,
        wait_days,
        conformity_status,
        unidade_de_saude__data_da_solicitacao as request_date,
        prestador_de_servico__data_da_realizacao as completion_date
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


@cached(ttl=120)
def get_other_birads_cases_sql(year=None, health_unit=None, region=None, conformity_status=None, age_range=None, birads_filter=None, limit=50):
    where_clause, params = _build_where_clause(year, health_unit, region, conformity_status, exclude_outliers=True, age_range=age_range)
    
    birads_condition = "birads_max IN ('0', '1', '2', '3')"
    if birads_filter and birads_filter in ['0', '1', '2', '3']:
        birads_condition = f"birads_max = '{birads_filter}'"
    
    query = f"""
    SELECT 
        patient_unique_id as patient_id,
        paciente__nome as patient_name,
        paciente__cartao_sus as patient_cns,
        paciente__telefone as patient_phone,
        unidade_de_saude__nome as health_unit,
        birads_max as birads_category,
        wait_days,
        conformity_status,
        unidade_de_saude__data_da_solicitacao as request_date,
        prestador_de_servico__data_da_realizacao as completion_date
    FROM exam_records
    {where_clause}
    {"AND" if where_clause else "WHERE"} {birads_condition}
    ORDER BY 
        CASE birads_max 
            WHEN '0' THEN 1 
            WHEN '3' THEN 2 
            WHEN '2' THEN 3 
            WHEN '1' THEN 4 
        END,
        wait_days DESC NULLS LAST
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
        conditions.append("(unidade_de_saude__nome = :health_unit OR prestador_de_servico__nome = :health_unit)")
        params['health_unit'] = health_unit
    
    if conformity_status:
        conditions.append("conformity_status = :conformity_status")
        params['conformity_status'] = conformity_status
    
    if region:
        conditions.append("distrito_sanitario = :region")
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


def get_outliers_audit_sql(year=None, health_unit=None, region=None):
    conditions = []
    params = {}
    
    if year:
        conditions.append("year = :year")
        params['year'] = year
    
    if health_unit:
        conditions.append("(unidade_de_saude__nome = :health_unit OR prestador_de_servico__nome = :health_unit)")
        params['health_unit'] = health_unit
    
    if region:
        conditions.append("distrito_sanitario = :region")
        params['region'] = region
    
    where_filter = ""
    if conditions:
        where_filter = " AND " + " AND ".join(conditions)
    
    query = f"""
    WITH outliers AS (
        SELECT 
            paciente__nome AS nome_paciente,
            paciente__cartao_sus AS cartao_sus,
            unidade_de_saude__nome AS unidade_saude,
            distrito_sanitario AS distrito_saude,
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
        WHERE 1=1 {where_filter}
    )
    SELECT 
        nome_paciente,
        cartao_sus,
        distrito_saude,
        unidade_saude,
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
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_outliers_summary_sql(year=None, health_unit=None, region=None):
    conditions = []
    params = {}
    
    if year:
        conditions.append("year = :year")
        params['year'] = year
    
    if health_unit:
        conditions.append("(unidade_de_saude__nome = :health_unit OR prestador_de_servico__nome = :health_unit)")
        params['health_unit'] = health_unit
    
    if region:
        conditions.append("distrito_sanitario = :region")
        params['region'] = region
    
    where_filter = ""
    if conditions:
        where_filter = " WHERE " + " AND ".join(conditions)
    
    query = f"""
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
        {where_filter}
    ) subquery
    WHERE motivo_outlier IS NOT NULL
    GROUP BY motivo_outlier, descricao
    ORDER BY motivo_outlier
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def _build_navigation_where_clause(year=None, health_unit=None, region=None, conformity=None, table_prefix=""):
    """Build a safe parameterized WHERE clause for patient navigation queries"""
    conditions = ["patient_unique_id IS NOT NULL", "unidade_de_saude__data_da_solicitacao >= '2023-01-01'"]
    params = {}
    
    prefix = f"{table_prefix}." if table_prefix else ""
    
    if year:
        conditions.append(f"EXTRACT(YEAR FROM {prefix}unidade_de_saude__data_da_solicitacao) = :nav_year")
        params['nav_year'] = year
    if health_unit:
        conditions.append(f"({prefix}unidade_de_saude__nome = :nav_health_unit OR {prefix}prestador_de_servico__nome = :nav_health_unit)")
        params['nav_health_unit'] = health_unit
    if region:
        conditions.append(f"{prefix}distrito_sanitario = :nav_region")
        params['nav_region'] = region
    if conformity:
        conditions.append(f"{prefix}conformity_status = :nav_conformity")
        params['nav_conformity'] = conformity
    
    if table_prefix:
        conditions = [c.replace("patient_unique_id", f"{table_prefix}.patient_unique_id") 
                     .replace("unidade_de_saude__data_da_solicitacao", f"{table_prefix}.unidade_de_saude__data_da_solicitacao")
                     if "patient_unique_id" in c and table_prefix not in c else c 
                     for c in conditions]
        conditions[0] = f"{table_prefix}.patient_unique_id IS NOT NULL"
        conditions[1] = f"{table_prefix}.unidade_de_saude__data_da_solicitacao >= '2023-01-01'"
    
    return " AND ".join(conditions), params


def get_patient_navigation_summary_sql(year=None, health_unit=None, region=None, conformity=None):
    """Get summary of patients with multiple exams"""
    where_clause, params = _build_navigation_where_clause(year, health_unit, region, conformity)
    
    query = f"""
    WITH patient_exam_counts AS (
        SELECT 
            patient_unique_id,
            COUNT(*) as total_exames
        FROM exam_records
        WHERE {where_clause}
        GROUP BY patient_unique_id
        HAVING COUNT(*) > 1
    )
    SELECT 
        total_exames as numero_atendimentos,
        COUNT(*) as total_pacientes
    FROM patient_exam_counts
    GROUP BY total_exames
    ORDER BY total_exames
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_patient_navigation_list_sql(year=None, health_unit=None, region=None, conformity=None, min_exams=2, limit=100, evolution_filter=None):
    """Get list of patients with multiple exams and their exam history
    
    evolution_filter: 'positive' (BI-RADS desceu), 'negative' (BI-RADS subiu), None (todos)
    """
    where_clause, params = _build_navigation_where_clause(year, health_unit, region, conformity)
    where_clause_e, _ = _build_navigation_where_clause(year, health_unit, region, conformity, table_prefix="e")
    
    params['min_exams'] = min_exams
    params['row_limit'] = limit * 10
    
    query = f"""
    WITH patient_exam_counts AS (
        SELECT 
            patient_unique_id,
            COUNT(*) as total_exames,
            MAX(paciente__nome) as nome_paciente,
            MAX(paciente__cartao_sus) as cartao_sus
        FROM exam_records
        WHERE {where_clause}
        GROUP BY patient_unique_id
        HAVING COUNT(*) >= :min_exams
    ),
    patient_exams AS (
        SELECT 
            e.patient_unique_id,
            p.nome_paciente,
            p.cartao_sus,
            p.total_exames,
            e.unidade_de_saude__data_da_solicitacao as data_solicitacao,
            e.prestador_de_servico__data_da_realizacao as data_realizacao,
            e.responsavel_pelo_resultado__data_da_liberacao as data_liberacao,
            e.birads_max,
            e.birads_direita,
            e.birads_esquerda,
            e.unidade_de_saude__nome as unidade_saude,
            e.prestador_de_servico__nome as prestador_executante,
            e.distrito_sanitario,
            e.wait_days,
            e.conformity_status,
            e.abertura_aih,
            COALESCE(e.conclusao_apac, '') as conclusao_apac,
            CASE 
                WHEN e.birads_max IN ('4', '5') THEN 
                    CASE WHEN e.wait_days IS NOT NULL AND e.wait_days <= 30 THEN 'Tempestivo' ELSE 'Atrasado' END
                WHEN e.birads_max = '0' THEN 
                    CASE WHEN e.wait_days IS NOT NULL AND e.wait_days <= 30 THEN 'Tempestivo' ELSE 'Atrasado' END
                WHEN e.birads_max = '3' THEN 
                    CASE WHEN e.wait_days IS NOT NULL AND e.wait_days <= 180 THEN 'Tempestivo' ELSE 'Atrasado' END
                WHEN e.birads_max IN ('1', '2') THEN 
                    CASE WHEN e.wait_days IS NOT NULL AND e.wait_days <= 365 THEN 'Tempestivo' ELSE 'Atrasado' END
                ELSE ''
            END as tempestividade,
            ROW_NUMBER() OVER (PARTITION BY e.patient_unique_id ORDER BY e.unidade_de_saude__data_da_solicitacao) as exam_order
        FROM exam_records e
        INNER JOIN patient_exam_counts p ON e.patient_unique_id = p.patient_unique_id
        WHERE {where_clause_e}
    ),
    patient_evolution AS (
        SELECT 
            patient_unique_id,
            MAX(CASE WHEN exam_order = 1 THEN CAST(NULLIF(birads_max, '') AS INTEGER) END) as first_birads,
            MAX(CASE WHEN exam_order = total_exames THEN CAST(NULLIF(birads_max, '') AS INTEGER) END) as last_birads
        FROM patient_exams
        WHERE birads_max ~ '^[0-9]+$'
        GROUP BY patient_unique_id
    )
    SELECT 
        pe.patient_unique_id,
        pe.nome_paciente,
        pe.cartao_sus,
        pe.total_exames,
        pe.exam_order,
        pe.data_solicitacao,
        pe.data_realizacao,
        pe.data_liberacao,
        pe.birads_max,
        pe.birads_direita,
        pe.birads_esquerda,
        pe.unidade_saude,
        pe.prestador_executante,
        pe.distrito_sanitario,
        pe.wait_days,
        pe.conformity_status,
        pe.abertura_aih,
        pe.conclusao_apac,
        pe.tempestividade,
        COALESCE(ev.first_birads, 0) as first_birads,
        COALESCE(ev.last_birads, 0) as last_birads,
        CASE WHEN ev.first_birads IN (3,4,5) AND ev.last_birads NOT IN (3,4,5) THEN 1 ELSE 0 END as evolucao_positiva,
        CASE WHEN ev.first_birads IN (0,1,2,6) AND ev.last_birads IN (3,4,5) THEN 1 ELSE 0 END as evolucao_negativa,
        CASE WHEN ev.first_birads IN (0,1,2) AND ev.last_birads IN (0,1,2) THEN 1 ELSE 0 END as evolucao_normal
    FROM patient_exams pe
    LEFT JOIN patient_evolution ev ON pe.patient_unique_id = ev.patient_unique_id
    """
    
    if evolution_filter == 'positive':
        query += " WHERE ev.first_birads IN (3,4,5) AND ev.last_birads NOT IN (3,4,5) "
    elif evolution_filter == 'negative':
        query += " WHERE ev.first_birads IN (0,1,2,6) AND ev.last_birads IN (3,4,5) "
    elif evolution_filter == 'normal':
        query += " WHERE ev.first_birads IN (0,1,2) AND ev.last_birads IN (0,1,2) "
    
    query += """
    ORDER BY 
        CASE WHEN ev.first_birads IN (3,4,5) AND ev.last_birads NOT IN (3,4,5) THEN 0 ELSE 1 END,
        pe.total_exames DESC, 
        pe.nome_paciente, 
        pe.exam_order
    LIMIT :row_limit
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_patient_navigation_stats_sql(year=None, health_unit=None, region=None, conformity=None):
    """Get overall statistics for patient navigation"""
    where_clause, params = _build_navigation_where_clause(year, health_unit, region, conformity)
    
    query = f"""
    WITH patient_exam_counts AS (
        SELECT 
            patient_unique_id,
            COUNT(*) as total_exames
        FROM exam_records
        WHERE {where_clause}
        GROUP BY patient_unique_id
    )
    SELECT 
        COUNT(*) FILTER (WHERE total_exames > 1) as pacientes_multiplos_exames,
        COUNT(*) as total_pacientes,
        SUM(total_exames) FILTER (WHERE total_exames > 1) as total_exames_multiplos,
        MAX(total_exames) as max_exames_paciente,
        ROUND(AVG(total_exames) FILTER (WHERE total_exames > 1), 1) as media_exames_por_paciente
    FROM patient_exam_counts
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        row = result.fetchone()
    
    return {
        'pacientes_multiplos_exames': row[0] or 0,
        'total_pacientes': row[1] or 0,
        'total_exames_multiplos': row[2] or 0,
        'max_exames_paciente': row[3] or 0,
        'media_exames_por_paciente': float(row[4]) if row[4] else 0
    }


def _build_patient_data_where_clause(year=None, health_unit=None, region=None, conformity=None, 
                                      patient_name=None, sex=None, birads=None, table_prefix="e"):
    """Build a safe parameterized WHERE clause for patient data queries"""
    p = f"{table_prefix}." if table_prefix else ""
    conditions = [f"{p}unidade_de_saude__data_da_solicitacao >= '2023-01-01'"]
    params = {}
    
    if year:
        conditions.append(f"EXTRACT(YEAR FROM {p}unidade_de_saude__data_da_solicitacao) = :pd_year")
        params['pd_year'] = year
    if health_unit:
        conditions.append(f"({p}unidade_de_saude__nome = :pd_health_unit OR {p}prestador_de_servico__nome = :pd_health_unit)")
        params['pd_health_unit'] = health_unit
    if region:
        conditions.append(f"{p}distrito_sanitario = :pd_region")
        params['pd_region'] = region
    if conformity:
        conditions.append(f"{p}conformity_status = :pd_conformity")
        params['pd_conformity'] = conformity
    if patient_name:
        conditions.append(f"UPPER({p}paciente__nome) LIKE UPPER(:pd_patient_name)")
        params['pd_patient_name'] = f"%{patient_name}%"
    if sex:
        conditions.append(f"{p}paciente__sexo = :pd_sex")
        params['pd_sex'] = sex
    if birads:
        conditions.append(f"{p}birads_max = :pd_birads")
        params['pd_birads'] = birads
    
    return " AND ".join(conditions), params


def get_patient_data_list_sql(year=None, health_unit=None, region=None, conformity=None,
                               patient_name=None, sex=None, birads=None, 
                               page=1, page_size=50):
    """Get paginated list of patient data with all clinical details"""
    where_clause, params = _build_patient_data_where_clause(
        year, health_unit, region, conformity, patient_name, sex, birads
    )
    
    offset = (page - 1) * page_size
    params['pd_limit'] = page_size
    params['pd_offset'] = offset
    
    query = f"""
    SELECT 
        e.paciente__nome as nome,
        e.paciente__idade as idade,
        e.paciente__sexo as sexo,
        e.paciente__data_do_nascimento as data_nascimento,
        e.paciente__mae as nome_mae,
        e.unidade_de_saude__nome as unidade_saude,
        e.unidade_de_saude__data_da_solicitacao as data_solicitacao,
        e.prestador_de_servico__data_da_realizacao as data_realizacao,
        e.responsavel_pelo_resultado__data_da_liberacao as data_liberacao,
        e.prestador_de_servico__nome as prestador_servico,
        e.unidade_de_saude__n_do_exame as numero_exame,
        COALESCE(e.resultado_exame__indicacao__tipo_de_mamografia, e.resultado_exame__indicacao__mamografia_de_rastreamento) as tipo_mamografia,
        COALESCE(e.resultado_exame__mama_direita__tipo_de_mama, e.resultado_exame__mama_esquerda__tipo_de_mama) as tipo_mama,
        e.resultado_exame__linfonodos_axilares__linfonodos_axilares as linfonodos_axilares,
        e.resultado_exame__achados_benignos__achados_benignos as achados_benignos,
        '' as nodulos,
        '' as microcalcificacoes,
        e.resultado_exame__classificacao_radiologica__mama_direita as birads_direita_class,
        e.resultado_exame__classificacao_radiologica__mama_esquerda as birads_esquerda_class,
        e.resultado_exame__recomendacoes as recomendacoes,
        e.birads_max,
        e.distrito_sanitario,
        e.conformity_status,
        e.wait_days,
        COALESCE(t.ultima_apac_cancer::text, e.conclusao_apac, '') as conclusao_apac,
        e.abertura_aih,
        CASE 
            WHEN e.birads_max IN ('4', '5') THEN 
                CASE WHEN e.wait_days IS NOT NULL AND e.wait_days <= 30 THEN 'Tempestivo' ELSE 'Atrasado' END
            WHEN e.birads_max = '0' THEN 
                CASE WHEN e.wait_days IS NOT NULL AND e.wait_days <= 30 THEN 'Tempestivo' ELSE 'Atrasado' END
            WHEN e.birads_max = '3' THEN 
                CASE WHEN e.wait_days IS NOT NULL AND e.wait_days <= 180 THEN 'Tempestivo' ELSE 'Atrasado' END
            WHEN e.birads_max IN ('1', '2') THEN 
                CASE WHEN e.wait_days IS NOT NULL AND e.wait_days <= 365 THEN 'Tempestivo' ELSE 'Atrasado' END
            ELSE ''
        END as tempestividade
    FROM exam_records e
    LEFT JOIN termo_linkage t ON e.paciente__cartao_sus = t.cartao_sus
    WHERE {where_clause}
    ORDER BY e.unidade_de_saude__data_da_solicitacao DESC, e.paciente__nome
    LIMIT :pd_limit OFFSET :pd_offset
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_patient_data_count_sql(year=None, health_unit=None, region=None, conformity=None,
                                patient_name=None, sex=None, birads=None):
    """Get total count of patient records for pagination"""
    where_clause, params = _build_patient_data_where_clause(
        year, health_unit, region, conformity, patient_name, sex, birads, table_prefix=""
    )
    
    query = f"""
    SELECT COUNT(*) as total
    FROM exam_records
    WHERE {where_clause}
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        row = result.fetchone()
    
    return row[0] or 0


def get_sex_options():
    """Get distinct sex values for filter"""
    engine = get_engine()
    query = """
    SELECT DISTINCT paciente__sexo 
    FROM exam_records 
    WHERE paciente__sexo IS NOT NULL 
    ORDER BY paciente__sexo
    """
    with engine.connect() as conn:
        result = conn.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df['paciente__sexo'].dropna().tolist()


def get_birads_options():
    """Get distinct BI-RADS values for filter"""
    engine = get_engine()
    query = """
    SELECT DISTINCT birads_max 
    FROM exam_records 
    WHERE birads_max IS NOT NULL AND birads_max != ''
    ORDER BY birads_max
    """
    with engine.connect() as conn:
        result = conn.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df['birads_max'].dropna().tolist()


def _build_unit_where_clause(health_unit, year=None, region=None, table_prefix=""):
    """Build WHERE clause for health unit specific queries"""
    p = f"{table_prefix}." if table_prefix else ""
    conditions = [
        f"({p}unidade_de_saude__nome = :unit_name OR {p}prestador_de_servico__nome = :unit_name)",
        f"{p}unidade_de_saude__data_da_solicitacao >= '2023-01-01'",
        f"({p}prestador_de_servico__data_da_realizacao IS NULL OR {p}prestador_de_servico__data_da_realizacao >= {p}unidade_de_saude__data_da_solicitacao)",
        f"({p}wait_days IS NULL OR ({p}wait_days >= 0 AND {p}wait_days <= 365))"
    ]
    params = {'unit_name': health_unit}
    
    if year:
        conditions.append(f"EXTRACT(YEAR FROM {p}unidade_de_saude__data_da_solicitacao) = :unit_year")
        params['unit_year'] = year
    if region:
        conditions.append(f"{p}distrito_sanitario = :unit_region")
        params['unit_region'] = region
    
    return " AND ".join(conditions), params


def get_unit_high_risk_patients_sql(health_unit, year=None, region=None):
    """Get high-risk patients (BI-RADS 4/5) for a specific health unit for CSV export"""
    if not health_unit:
        return pd.DataFrame()
    
    where_clause, params = _build_unit_where_clause(health_unit, year, region)
    
    query = f"""
    SELECT 
        paciente__nome as nome_paciente,
        paciente__cartao_sus as cartao_sus,
        paciente__idade as idade,
        paciente__sexo as sexo,
        unidade_de_saude__nome as unidade_saude,
        distrito_sanitario,
        birads_max,
        birads_direita,
        birads_esquerda,
        unidade_de_saude__data_da_solicitacao as data_solicitacao,
        prestador_de_servico__data_da_realizacao as data_realizacao,
        responsavel_pelo_resultado__data_da_liberacao as data_liberacao,
        wait_days as dias_espera,
        conformity_status as status_conformidade,
        resultado_exame__indicacao__mamografia_de_rastreamento as tipo_mamografia,
        prestador_de_servico__cnpj as cnpj_prestador,
        prestador_de_servico__nome as prestador_servico
    FROM exam_records
    WHERE {where_clause}
    AND birads_max IN ('4', '5')
    ORDER BY unidade_de_saude__data_da_solicitacao DESC
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_all_high_risk_patients_sql(year=None, health_unit=None, region=None):
    """Get all high-risk patients (BI-RADS 4/5) for CSV export with global filters"""
    where_clause, params = _build_where_clause(year, health_unit, region, exclude_outliers=True)
    
    query = f"""
    SELECT 
        paciente__nome as nome_paciente,
        paciente__cartao_sus as cartao_sus,
        paciente__idade as idade,
        paciente__sexo as sexo,
        unidade_de_saude__nome as unidade_saude,
        distrito_sanitario,
        birads_max,
        birads_direita,
        birads_esquerda,
        unidade_de_saude__data_da_solicitacao as data_solicitacao,
        prestador_de_servico__data_da_realizacao as data_realizacao,
        responsavel_pelo_resultado__data_da_liberacao as data_liberacao,
        wait_days as dias_espera,
        conformity_status as status_conformidade,
        resultado_exame__indicacao__mamografia_de_rastreamento as tipo_mamografia,
        prestador_de_servico__cnpj as cnpj_prestador,
        prestador_de_servico__nome as prestador_servico
    FROM exam_records
    {where_clause}
    {"AND" if where_clause else "WHERE"} birads_max IN ('4', '5')
    ORDER BY unidade_de_saude__data_da_solicitacao DESC
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_unit_kpis_sql(health_unit, year=None, region=None):
    """Get KPIs for a specific health unit"""
    if not health_unit:
        return {
            'total_exames': 0,
            'total_pacientes': 0,
            'media_espera': 0,
            'mediana_espera': 0,
            'taxa_conformidade': 0,
            'casos_alto_risco': 0
        }
    
    where_clause, params = _build_unit_where_clause(health_unit, year, region)
    
    query = f"""
    SELECT 
        COUNT(*) as total_exames,
        COUNT(DISTINCT patient_unique_id) as total_pacientes,
        COALESCE(AVG(wait_days), 0) as media_espera,
        COALESCE(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY wait_days), 0) as mediana_espera,
        COALESCE(COUNT(CASE WHEN conformity_status = 'Dentro do Prazo' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 0) as taxa_conformidade,
        COUNT(CASE WHEN birads_max IN ('4', '5') THEN 1 END) as casos_alto_risco,
        COALESCE(AVG(
            CASE WHEN responsavel_pelo_resultado__data_da_liberacao IS NOT NULL 
                 AND prestador_de_servico__data_da_realizacao IS NOT NULL
                 AND responsavel_pelo_resultado__data_da_liberacao >= prestador_de_servico__data_da_realizacao
            THEN (responsavel_pelo_resultado__data_da_liberacao - prestador_de_servico__data_da_realizacao)
            END
        ), 0) as media_realizacao_liberacao,
        COALESCE(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY 
            CASE WHEN responsavel_pelo_resultado__data_da_liberacao IS NOT NULL 
                 AND prestador_de_servico__data_da_realizacao IS NOT NULL
                 AND responsavel_pelo_resultado__data_da_liberacao >= prestador_de_servico__data_da_realizacao
            THEN (responsavel_pelo_resultado__data_da_liberacao - prestador_de_servico__data_da_realizacao)
            END
        ), 0) as mediana_realizacao_liberacao
    FROM exam_records
    WHERE {where_clause}
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        row = result.fetchone()
    
    if not row:
        return {
            'total_exames': 0,
            'total_pacientes': 0,
            'media_espera': 0,
            'mediana_espera': 0,
            'taxa_conformidade': 0,
            'casos_alto_risco': 0,
            'media_realizacao_liberacao': 0,
            'mediana_realizacao_liberacao': 0
        }
    
    return {
        'total_exames': int(row[0]) if row[0] else 0,
        'total_pacientes': int(row[1]) if row[1] else 0,
        'media_espera': round(float(row[2]) if row[2] else 0, 1),
        'mediana_espera': round(float(row[3]) if row[3] else 0, 1),
        'taxa_conformidade': round(float(row[4]) if row[4] else 0, 1),
        'casos_alto_risco': int(row[5]) if row[5] else 0,
        'media_realizacao_liberacao': round(float(row[6]) if row[6] else 0, 1),
        'mediana_realizacao_liberacao': round(float(row[7]) if row[7] else 0, 1)
    }


def get_unit_demographics_sql(health_unit, year=None, region=None):
    """Get patient demographics by age group and BI-RADS for a health unit"""
    if not health_unit:
        return pd.DataFrame()
    
    where_clause, params = _build_unit_where_clause(health_unit, year, region)
    
    query = f"""
    SELECT faixa_etaria, birads_max, total FROM (
        SELECT 
            CASE 
                WHEN paciente__idade IS NULL THEN 'Não informado'
                WHEN paciente__idade < 30 THEN '< 30 anos'
                WHEN paciente__idade BETWEEN 30 AND 39 THEN '30-39 anos'
                WHEN paciente__idade BETWEEN 40 AND 49 THEN '40-49 anos'
                WHEN paciente__idade BETWEEN 50 AND 59 THEN '50-59 anos'
                WHEN paciente__idade BETWEEN 60 AND 69 THEN '60-69 anos'
                ELSE '70+ anos'
            END as faixa_etaria,
            CASE 
                WHEN paciente__idade IS NULL THEN 7
                WHEN paciente__idade < 30 THEN 1
                WHEN paciente__idade BETWEEN 30 AND 39 THEN 2
                WHEN paciente__idade BETWEEN 40 AND 49 THEN 3
                WHEN paciente__idade BETWEEN 50 AND 59 THEN 4
                WHEN paciente__idade BETWEEN 60 AND 69 THEN 5
                ELSE 6
            END as ordem_faixa,
            birads_max,
            COUNT(*) as total
        FROM exam_records
        WHERE {where_clause}
        GROUP BY 
            CASE 
                WHEN paciente__idade IS NULL THEN 'Não informado'
                WHEN paciente__idade < 30 THEN '< 30 anos'
                WHEN paciente__idade BETWEEN 30 AND 39 THEN '30-39 anos'
                WHEN paciente__idade BETWEEN 40 AND 49 THEN '40-49 anos'
                WHEN paciente__idade BETWEEN 50 AND 59 THEN '50-59 anos'
                WHEN paciente__idade BETWEEN 60 AND 69 THEN '60-69 anos'
                ELSE '70+ anos'
            END,
            CASE 
                WHEN paciente__idade IS NULL THEN 7
                WHEN paciente__idade < 30 THEN 1
                WHEN paciente__idade BETWEEN 30 AND 39 THEN 2
                WHEN paciente__idade BETWEEN 40 AND 49 THEN 3
                WHEN paciente__idade BETWEEN 50 AND 59 THEN 4
                WHEN paciente__idade BETWEEN 60 AND 69 THEN 5
                ELSE 6
            END,
            birads_max
    ) sub
    ORDER BY ordem_faixa, birads_max
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_unit_agility_sql(health_unit, year=None, region=None):
    """Get service agility distribution (wait time buckets) for a health unit"""
    if not health_unit:
        return pd.DataFrame()
    
    where_clause, params = _build_unit_where_clause(health_unit, year, region)
    
    query = f"""
    SELECT faixa_espera, total, percentual FROM (
        SELECT 
            CASE 
                WHEN wait_days IS NULL THEN 'Não informado'
                WHEN wait_days <= 7 THEN 'Até 7 dias'
                WHEN wait_days <= 14 THEN '8-14 dias'
                WHEN wait_days <= 30 THEN '15-30 dias'
                WHEN wait_days <= 60 THEN '31-60 dias'
                ELSE '> 60 dias'
            END as faixa_espera,
            CASE 
                WHEN wait_days IS NULL THEN 6
                WHEN wait_days <= 7 THEN 1
                WHEN wait_days <= 14 THEN 2
                WHEN wait_days <= 30 THEN 3
                WHEN wait_days <= 60 THEN 4
                ELSE 5
            END as ordem_faixa,
            COUNT(*) as total,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentual
        FROM exam_records
        WHERE {where_clause}
        GROUP BY 
            CASE 
                WHEN wait_days IS NULL THEN 'Não informado'
                WHEN wait_days <= 7 THEN 'Até 7 dias'
                WHEN wait_days <= 14 THEN '8-14 dias'
                WHEN wait_days <= 30 THEN '15-30 dias'
                WHEN wait_days <= 60 THEN '31-60 dias'
                ELSE '> 60 dias'
            END,
            CASE 
                WHEN wait_days IS NULL THEN 6
                WHEN wait_days <= 7 THEN 1
                WHEN wait_days <= 14 THEN 2
                WHEN wait_days <= 30 THEN 3
                WHEN wait_days <= 60 THEN 4
                ELSE 5
            END
    ) sub
    ORDER BY ordem_faixa
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_unit_wait_time_trend_sql(health_unit, year=None, region=None):
    """Get monthly average wait time trend for a health unit"""
    if not health_unit:
        return pd.DataFrame()
    
    where_clause, params = _build_unit_where_clause(health_unit, year, region)
    
    query = f"""
    SELECT 
        TO_CHAR(unidade_de_saude__data_da_solicitacao, 'YYYY-MM') as mes,
        COUNT(*) as total_exames,
        ROUND(AVG(wait_days)::numeric, 1) as media_espera,
        ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY wait_days))::numeric, 1) as mediana_espera
    FROM exam_records
    WHERE {where_clause}
        AND wait_days IS NOT NULL
    GROUP BY TO_CHAR(unidade_de_saude__data_da_solicitacao, 'YYYY-MM')
    ORDER BY mes
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_unit_follow_up_overdue_sql(health_unit, year=None, region=None, limit=100):
    """
    Get patients who had exams but haven't returned for follow-up.
    Follow-up intervals based on BI-RADS:
    - BI-RADS 0: Additional imaging needed - 30 days
    - BI-RADS 3: Probably benign, short-term follow-up - 180 days (6 months)
    - BI-RADS 4/5: Suspicious/Malignant - 30 days (biopsy needed)
    - BI-RADS 1/2: Normal/Benign - 365 days (annual screening)
    """
    if not health_unit:
        return pd.DataFrame()
    
    where_clause, params = _build_unit_where_clause(health_unit, year, region, table_prefix="e")
    params['follow_limit'] = limit
    
    query = f"""
    WITH latest_exams AS (
        SELECT 
            e.patient_unique_id,
            e.paciente__nome,
            e.paciente__cartao_sus,
            e.paciente__idade,
            e.birads_max,
            e.birads_direita,
            e.birads_esquerda,
            e.unidade_de_saude__data_da_solicitacao as data_exame,
            e.prestador_de_servico__data_da_realizacao as data_realizacao,
            e.responsavel_pelo_resultado__data_da_liberacao as data_liberacao,
            e.prestador_de_servico__nome as prestador_servico,
            e.wait_days,
            e.abertura_aih,
            COALESCE(e.conclusao_apac, '') as conclusao_apac,
            CASE 
                WHEN e.birads_max IN ('4', '5') THEN 
                    CASE WHEN e.wait_days IS NOT NULL AND e.wait_days <= 30 THEN 'Tempestivo' ELSE 'Atrasado' END
                WHEN e.birads_max = '0' THEN 
                    CASE WHEN e.wait_days IS NOT NULL AND e.wait_days <= 30 THEN 'Tempestivo' ELSE 'Atrasado' END
                WHEN e.birads_max = '3' THEN 
                    CASE WHEN e.wait_days IS NOT NULL AND e.wait_days <= 180 THEN 'Tempestivo' ELSE 'Atrasado' END
                ELSE ''
            END as tempestividade,
            ROW_NUMBER() OVER (PARTITION BY e.patient_unique_id ORDER BY e.unidade_de_saude__data_da_solicitacao DESC) as rn
        FROM exam_records e
        WHERE {where_clause}
    ),
    patients_with_followup AS (
        SELECT 
            patient_unique_id,
            paciente__nome,
            paciente__cartao_sus,
            paciente__idade,
            birads_max,
            birads_direita,
            birads_esquerda,
            data_exame,
            data_realizacao,
            data_liberacao,
            prestador_servico,
            wait_days,
            abertura_aih,
            conclusao_apac,
            tempestividade,
            CASE 
                WHEN birads_max = '0' THEN 30
                WHEN birads_max = '3' THEN 180
                WHEN birads_max IN ('4', '5') THEN 30
                ELSE 365
            END as intervalo_retorno_dias,
            CASE 
                WHEN birads_max = '0' THEN 'Necessita imagem adicional'
                WHEN birads_max = '3' THEN 'Provavelmente benigno - acompanhamento'
                WHEN birads_max IN ('4', '5') THEN 'Suspeito - biópsia recomendada'
                ELSE 'Rastreamento anual'
            END as motivo_retorno
        FROM latest_exams
        WHERE rn = 1
            AND birads_max IN ('0', '3', '4', '5')
    )
    SELECT 
        paciente__nome as nome,
        paciente__cartao_sus as cartao_sus,
        paciente__idade as idade,
        birads_max,
        birads_direita,
        birads_esquerda,
        data_exame,
        data_realizacao,
        data_liberacao,
        prestador_servico,
        wait_days as espera_dias,
        intervalo_retorno_dias,
        motivo_retorno,
        abertura_aih,
        conclusao_apac,
        tempestividade,
        (COALESCE(data_realizacao, data_exame) + (intervalo_retorno_dias || ' days')::INTERVAL)::DATE as data_prevista_retorno,
        (CURRENT_DATE - (COALESCE(data_realizacao, data_exame) + (intervalo_retorno_dias || ' days')::INTERVAL)::DATE) as dias_atraso
    FROM patients_with_followup
    WHERE (COALESCE(data_realizacao, data_exame) + (intervalo_retorno_dias || ' days')::INTERVAL)::DATE < CURRENT_DATE
    ORDER BY dias_atraso DESC
    LIMIT :follow_limit
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_unit_follow_up_count_sql(health_unit, year=None, region=None):
    """Get count of patients with overdue follow-up"""
    if not health_unit:
        return 0
    
    where_clause, params = _build_unit_where_clause(health_unit, year, region)
    
    query = f"""
    WITH latest_exams AS (
        SELECT 
            patient_unique_id,
            birads_max,
            unidade_de_saude__data_da_solicitacao as data_exame,
            prestador_de_servico__data_da_realizacao as data_realizacao,
            ROW_NUMBER() OVER (PARTITION BY patient_unique_id ORDER BY unidade_de_saude__data_da_solicitacao DESC) as rn
        FROM exam_records
        WHERE {where_clause}
    ),
    patients_with_followup AS (
        SELECT 
            patient_unique_id,
            birads_max,
            data_exame,
            data_realizacao,
            CASE 
                WHEN birads_max = '0' THEN 30
                WHEN birads_max = '3' THEN 180
                WHEN birads_max IN ('4', '5') THEN 30
                ELSE 365
            END as intervalo_retorno_dias
        FROM latest_exams
        WHERE rn = 1
            AND birads_max IN ('0', '3', '4', '5')
    )
    SELECT COUNT(*) as total
    FROM patients_with_followup
    WHERE (COALESCE(data_realizacao, data_exame) + (intervalo_retorno_dias || ' days')::INTERVAL)::DATE < CURRENT_DATE
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        row = result.fetchone()
    
    if not row:
        return 0
    return int(row[0]) if row[0] else 0


def get_indicators_data_sql(year=None, region=None, health_unit=None):
    """Get all indicators data for the Indicadores tab"""
    where_clause, params = _build_where_clause(year, None, region, None, exclude_outliers=True)
    
    if health_unit:
        if where_clause:
            where_clause += " AND (unidade_de_saude__nome = :ind_health_unit OR prestador_de_servico__nome = :ind_health_unit)"
        else:
            where_clause = " WHERE (unidade_de_saude__nome = :ind_health_unit OR prestador_de_servico__nome = :ind_health_unit)"
        params['ind_health_unit'] = health_unit
    
    base_where = where_clause if where_clause else " WHERE 1=1"
    
    engine = get_engine()
    
    indicators = {}
    
    with engine.connect() as conn:
        ind1_query = f"""
        SELECT COUNT(*) as total
        FROM exam_records
        {base_where}
        AND resultado_exame__indicacao__mamografia_de_rastreamento = 'População alvo'
        AND paciente__idade >= 50 AND paciente__idade <= 69
        """
        result = conn.execute(text(ind1_query), params)
        row = result.fetchone()
        indicators['rastreamento_50_69'] = int(row[0]) if row and row[0] else 0
        
        ind2_query = f"""
        SELECT 
            COALESCE(distrito_sanitario, 'Não informado') as distrito,
            COUNT(*) as total
        FROM exam_records
        {base_where}
        AND resultado_exame__indicacao__mamografia_de_rastreamento = 'População alvo'
        AND paciente__idade >= 50 AND paciente__idade <= 69
        GROUP BY distrito_sanitario
        ORDER BY total DESC
        """
        result = conn.execute(text(ind2_query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        indicators['rastreamento_por_distrito'] = df
        
        ind2b_query = f"""
        SELECT 
            unidade_de_saude__nome as unidade,
            COUNT(*) as total
        FROM exam_records
        {base_where}
        AND resultado_exame__indicacao__mamografia_de_rastreamento = 'População alvo'
        AND paciente__idade >= 50 AND paciente__idade <= 69
        GROUP BY unidade_de_saude__nome
        ORDER BY total DESC
        LIMIT 20
        """
        result = conn.execute(text(ind2b_query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        indicators['rastreamento_por_unidade'] = df
        
        ind3_query = f"""
        SELECT 
            ROUND(AVG(
                (responsavel_pelo_resultado__data_da_liberacao - unidade_de_saude__data_da_solicitacao)
            )::numeric, 1) as media_dias,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY (responsavel_pelo_resultado__data_da_liberacao - unidade_de_saude__data_da_solicitacao)
            ) as mediana_dias,
            COUNT(*) FILTER (WHERE (responsavel_pelo_resultado__data_da_liberacao - unidade_de_saude__data_da_solicitacao) <= 30) as dentro_30_dias,
            COUNT(*) as total_com_datas
        FROM exam_records
        {base_where}
        AND responsavel_pelo_resultado__data_da_liberacao IS NOT NULL
        AND unidade_de_saude__data_da_solicitacao IS NOT NULL
        AND responsavel_pelo_resultado__data_da_liberacao >= unidade_de_saude__data_da_solicitacao
        """
        result = conn.execute(text(ind3_query), params)
        row = result.fetchone()
        dentro_30 = int(row[2]) if row and row[2] else 0
        total_datas = int(row[3]) if row and row[3] else 0
        indicators['tempo_solicitacao_liberacao'] = {
            'media': float(row[0]) if row and row[0] else 0,
            'mediana': float(row[1]) if row and row[1] else 0,
            'percentual_30_dias': round(dentro_30 / total_datas * 100, 1) if total_datas > 0 else 0,
            'dentro_30_dias': dentro_30,
            'total_com_datas': total_datas
        }
        
        ind4_query = f"""
        SELECT 
            ROUND(AVG(
                (responsavel_pelo_resultado__data_da_liberacao - prestador_de_servico__data_da_realizacao)
            )::numeric, 1) as media_dias,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY (responsavel_pelo_resultado__data_da_liberacao - prestador_de_servico__data_da_realizacao)
            ) as mediana_dias
        FROM exam_records
        {base_where}
        AND responsavel_pelo_resultado__data_da_liberacao IS NOT NULL
        AND prestador_de_servico__data_da_realizacao IS NOT NULL
        AND responsavel_pelo_resultado__data_da_liberacao >= prestador_de_servico__data_da_realizacao
        """
        result = conn.execute(text(ind4_query), params)
        row = result.fetchone()
        indicators['tempo_realizacao_liberacao'] = {
            'media': float(row[0]) if row and row[0] else 0,
            'mediana': float(row[1]) if row and row[1] else 0
        }
        
        ind_rastreamento_total_query = f"""
        SELECT COUNT(*) as total
        FROM exam_records
        {base_where}
        AND resultado_exame__indicacao__mamografia_de_rastreamento = 'População alvo'
        """
        result = conn.execute(text(ind_rastreamento_total_query), params)
        row = result.fetchone()
        indicators['total_rastreamento'] = int(row[0]) if row and row[0] else 0
        
        ind5_query = f"""
        SELECT COUNT(*) as total
        FROM exam_records
        {base_where}
        AND birads_max = '0'
        AND resultado_exame__indicacao__mamografia_de_rastreamento = 'População alvo'
        """
        result = conn.execute(text(ind5_query), params)
        row = result.fetchone()
        indicators['categoria_0_rastreamento'] = int(row[0]) if row and row[0] else 0
        
        ind5b_query = f"""
        SELECT COUNT(*) as total
        FROM exam_records
        {base_where}
        AND birads_max = '0'
        """
        result = conn.execute(text(ind5b_query), params)
        row = result.fetchone()
        indicators['categoria_0'] = int(row[0]) if row and row[0] else 0
        
        ind6_query = f"""
        SELECT COUNT(*) as total
        FROM exam_records
        {base_where}
        AND birads_max = '3'
        AND (
            resultado_exame__achados_benignos__achados_benignos ILIKE '%nódulo%'
            OR resultado_exame__achados_benignos__achados_benignos ILIKE '%nodulo%'
        )
        """
        result = conn.execute(text(ind6_query), params)
        row = result.fetchone()
        indicators['categoria_3_nodulo'] = int(row[0]) if row and row[0] else 0
        
        ind6b_query = f"""
        SELECT COUNT(*) as total
        FROM exam_records
        {base_where}
        AND birads_max = '3'
        """
        result = conn.execute(text(ind6b_query), params)
        row = result.fetchone()
        indicators['categoria_3_total'] = int(row[0]) if row and row[0] else 0
        
        ind7_query = f"""
        SELECT COUNT(*) as total
        FROM exam_records
        {base_where}
        AND birads_max IN ('4', '5')
        AND resultado_exame__indicacao__mamografia_de_rastreamento = 'População alvo'
        """
        result = conn.execute(text(ind7_query), params)
        row = result.fetchone()
        indicators['categoria_4_5_rastreamento'] = int(row[0]) if row and row[0] else 0
        
        ind8_query = f"""
        SELECT COUNT(*) as total
        FROM exam_records
        {base_where}
        AND paciente__idade >= 50 AND paciente__idade <= 69
        AND (
            birads_max = '0'
            OR resultado_exame__mama_direita__tipo_de_mama IN ('Densa', 'Predominantemente Densa')
            OR resultado_exame__mama_esquerda__tipo_de_mama IN ('Densa', 'Predominantemente Densa')
        )
        """
        result = conn.execute(text(ind8_query), params)
        row = result.fetchone()
        indicators['idade_50_69_densas_cat0'] = int(row[0]) if row and row[0] else 0
        
        ind9_query = f"""
        SELECT COUNT(*) as total
        FROM exam_records
        {base_where}
        AND paciente__idade < 49
        AND birads_max IN ('4', '5')
        """
        result = conn.execute(text(ind9_query), params)
        row = result.fetchone()
        indicators['idade_menor_49_cat_4_5'] = int(row[0]) if row and row[0] else 0
        
        ind10_query = f"""
        SELECT COUNT(*) as total
        FROM exam_records
        {base_where}
        AND paciente__idade < 40
        AND (
            resultado_exame__achados_benignos__achados_benignos ILIKE '%nódulo%'
            OR resultado_exame__achados_benignos__achados_benignos ILIKE '%nodulo%'
        )
        """
        result = conn.execute(text(ind10_query), params)
        row = result.fetchone()
        indicators['idade_menor_40_nodulo'] = int(row[0]) if row and row[0] else 0
        
        ind11_query = f"""
        SELECT 
            COUNT(*) FILTER (WHERE resultado_exame__indicacao__mamografia_de_rastreamento = 'População alvo') as rastreamento,
            COUNT(*) as total
        FROM exam_records
        {base_where}
        AND birads_max IN ('4', '5')
        """
        result = conn.execute(text(ind11_query), params)
        row = result.fetchone()
        cat45_rastreamento = int(row[0]) if row and row[0] else 0
        cat45_total = int(row[1]) if row and row[1] else 0
        indicators['diagnostico_estagio_inicial'] = {
            'rastreamento': cat45_rastreamento,
            'total': cat45_total,
            'percentual': round(cat45_rastreamento / cat45_total * 100, 1) if cat45_total > 0 else 0
        }
        
        total_query = f"""
        SELECT COUNT(*) as total
        FROM exam_records
        {base_where}
        """
        result = conn.execute(text(total_query), params)
        row = result.fetchone()
        indicators['total_exames'] = int(row[0]) if row and row[0] else 0
    
    return indicators


def get_indicator_details_sql(indicator_type, year=None, region=None, health_unit=None, limit=100):
    """Get detailed list of patients for a specific indicator"""
    where_clause, params = _build_where_clause(year, None, region, None, exclude_outliers=True)
    
    if health_unit:
        if where_clause:
            where_clause += " AND (unidade_de_saude__nome = :ind_health_unit OR prestador_de_servico__nome = :ind_health_unit)"
        else:
            where_clause = " WHERE (unidade_de_saude__nome = :ind_health_unit OR prestador_de_servico__nome = :ind_health_unit)"
        params['ind_health_unit'] = health_unit
    
    base_where = where_clause if where_clause else " WHERE 1=1"
    params['detail_limit'] = limit
    
    base_select = """
        paciente__nome as nome,
        paciente__idade as idade,
        paciente__cartao_sus as cartao_sus,
        unidade_de_saude__nome as unidade,
        distrito_sanitario as distrito,
        birads_max as birads,
        unidade_de_saude__data_da_solicitacao as data_solicitacao,
        prestador_de_servico__data_da_realizacao as data_realizacao,
        responsavel_pelo_resultado__data_da_liberacao as data_liberacao
    """
    
    indicator_conditions = {
        'rastreamento_50_69': "AND resultado_exame__indicacao__mamografia_de_rastreamento = 'População alvo' AND paciente__idade >= 50 AND paciente__idade <= 69",
        'rastreamento_50_74': "AND resultado_exame__indicacao__mamografia_de_rastreamento = 'População alvo' AND paciente__idade >= 50 AND paciente__idade <= 69",
        'categoria_0': "AND birads_max = '0'",
        'categoria_0_rastreamento': "AND birads_max = '0' AND resultado_exame__indicacao__mamografia_de_rastreamento = 'População alvo'",
        'categoria_3_nodulo': "AND birads_max = '3' AND (resultado_exame__achados_benignos__achados_benignos ILIKE '%nódulo%' OR resultado_exame__achados_benignos__achados_benignos ILIKE '%nodulo%')",
        'categoria_4_5_rastreamento': "AND birads_max IN ('4', '5') AND resultado_exame__indicacao__mamografia_de_rastreamento = 'População alvo'",
        'idade_50_69_densas_cat0': "AND paciente__idade >= 50 AND paciente__idade <= 69 AND (birads_max = '0' OR resultado_exame__mama_direita__tipo_de_mama IN ('Densa', 'Predominantemente Densa') OR resultado_exame__mama_esquerda__tipo_de_mama IN ('Densa', 'Predominantemente Densa'))",
        'idade_50_74_densas_cat0': "AND paciente__idade >= 50 AND paciente__idade <= 69 AND (birads_max = '0' OR resultado_exame__mama_direita__tipo_de_mama IN ('Densa', 'Predominantemente Densa') OR resultado_exame__mama_esquerda__tipo_de_mama IN ('Densa', 'Predominantemente Densa'))",
        'idade_menor_49_cat_4_5': "AND paciente__idade < 49 AND birads_max IN ('4', '5')",
        'idade_menor_40_nodulo': "AND paciente__idade < 40 AND (resultado_exame__achados_benignos__achados_benignos ILIKE '%nódulo%' OR resultado_exame__achados_benignos__achados_benignos ILIKE '%nodulo%')",
        'diagnostico_estagio_inicial': "AND birads_max IN ('4', '5') AND resultado_exame__indicacao__mamografia_de_rastreamento = 'População alvo'"
    }
    
    condition = indicator_conditions.get(indicator_type, "")
    
    query = f"""
    SELECT {base_select}
    FROM exam_records
    {base_where}
    {condition}
    ORDER BY unidade_de_saude__data_da_solicitacao DESC
    LIMIT :detail_limit
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_termo_linkage_summary_sql():
    query = """
    WITH duplicatas AS (
        SELECT 
            paciente__cartao_sus,
            COUNT(*) as total_registros
        FROM exam_records
        WHERE unidade_de_saude__data_da_solicitacao >= '2023-01-01'
        GROUP BY paciente__cartao_sus
        HAVING COUNT(*) > 1
    )
    SELECT 
        (SELECT COUNT(*) FROM termo_linkage) as total_registros,
        (SELECT COUNT(CASE WHEN cpf IS NOT NULL AND cpf != '' THEN 1 END) FROM termo_linkage) as com_cpf,
        (SELECT COUNT(CASE WHEN telefone IS NOT NULL AND telefone != '' THEN 1 END) FROM termo_linkage) as com_telefone,
        (SELECT COUNT(CASE WHEN nome_esaude IS NOT NULL AND nome_esaude != '' THEN 1 END) FROM termo_linkage) as com_nome_esaude,
        (SELECT COUNT(CASE WHEN ultima_apac_cancer IS NOT NULL THEN 1 END) FROM termo_linkage) as com_apac_cancer,
        (SELECT COUNT(CASE WHEN comparacao_nomes = 'True' OR comparacao_nomes = 'Sim' THEN 1 END) FROM termo_linkage) as nomes_conferem,
        (SELECT COUNT(DISTINCT paciente__cartao_sus) FROM duplicatas) as pacientes_duplicados,
        (SELECT SUM(total_registros) FROM duplicatas) as registros_duplicados
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query))
        row = result.fetchone()
    
    if row:
        return {
            'total_registros': int(row[0]) if row[0] else 0,
            'com_cpf': int(row[1]) if row[1] else 0,
            'com_telefone': int(row[2]) if row[2] else 0,
            'com_nome_esaude': int(row[3]) if row[3] else 0,
            'com_apac_cancer': int(row[4]) if row[4] else 0,
            'nomes_conferem': int(row[5]) if row[5] else 0,
            'pacientes_duplicados': int(row[6]) if row[6] else 0,
            'registros_duplicados': int(row[7]) if row[7] else 0
        }
    return {
        'total_registros': 0,
        'com_cpf': 0,
        'com_telefone': 0,
        'com_nome_esaude': 0,
        'com_apac_cancer': 0,
        'nomes_conferem': 0,
        'pacientes_duplicados': 0,
        'registros_duplicados': 0
    }


def get_database_comparison_sql():
    query = """
    WITH 
    exam_cns AS (
        SELECT DISTINCT paciente__cartao_sus::text as cns 
        FROM exam_records 
        WHERE paciente__cartao_sus IS NOT NULL
    ),
    termo_cns AS (
        SELECT DISTINCT cartao_sus::text as cns 
        FROM termo_linkage 
        WHERE cartao_sus IS NOT NULL
    )
    SELECT 
        (SELECT COUNT(*) FROM exam_records) as total_exam_records,
        (SELECT COUNT(*) FROM termo_linkage) as total_termo_linkage,
        (SELECT COUNT(*) FROM exam_cns) as unique_cns_exam,
        (SELECT COUNT(*) FROM termo_cns) as unique_cns_termo,
        (SELECT COUNT(*) FROM exam_cns e INNER JOIN termo_cns t ON e.cns = t.cns) as common_cns,
        (SELECT COUNT(*) FROM exam_cns e LEFT JOIN termo_cns t ON e.cns = t.cns WHERE t.cns IS NULL) as only_exam_cns,
        (SELECT COUNT(*) FROM termo_cns t LEFT JOIN exam_cns e ON t.cns = e.cns WHERE e.cns IS NULL) as only_termo_cns
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query))
        row = result.fetchone()
    
    if row:
        return {
            'total_exam_records': int(row[0]) if row[0] else 0,
            'total_termo_linkage': int(row[1]) if row[1] else 0,
            'unique_cns_exam': int(row[2]) if row[2] else 0,
            'unique_cns_termo': int(row[3]) if row[3] else 0,
            'common_cns': int(row[4]) if row[4] else 0,
            'only_exam_cns': int(row[5]) if row[5] else 0,
            'only_termo_cns': int(row[6]) if row[6] else 0
        }
    return {
        'total_exam_records': 0,
        'total_termo_linkage': 0,
        'unique_cns_exam': 0,
        'unique_cns_termo': 0,
        'common_cns': 0,
        'only_exam_cns': 0,
        'only_termo_cns': 0
    }


def get_termo_linkage_data_sql(search_nome=None, search_cpf=None, search_cartao_sus=None, limit=50, offset=0):
    conditions = []
    params = {'lim': limit, 'off': offset}
    
    if search_nome:
        conditions.append("(e.paciente__nome ILIKE :search_nome OR t.nome_esaude ILIKE :search_nome)")
        params['search_nome'] = f'%{search_nome}%'
    
    if search_cpf:
        conditions.append("t.cpf LIKE :search_cpf")
        params['search_cpf'] = f'%{search_cpf}%'
    
    if search_cartao_sus:
        conditions.append("CAST(e.paciente__cartao_sus AS TEXT) LIKE :search_cartao_sus")
        params['search_cartao_sus'] = f'%{search_cartao_sus}%'
    
    where_clause = ""
    if conditions:
        where_clause = " AND " + " AND ".join(conditions)
    
    query = f"""
    WITH duplicatas AS (
        SELECT 
            paciente__cartao_sus,
            COUNT(*) as total_registros
        FROM exam_records
        WHERE unidade_de_saude__data_da_solicitacao >= '2023-01-01'
        GROUP BY paciente__cartao_sus
        HAVING COUNT(*) > 1
    )
    SELECT 
        e.paciente__nome as nome_siscan,
        t.nome_esaude,
        t.comparacao_nomes,
        e.paciente__cartao_sus as cartao_sus,
        t.cpf,
        e.paciente__telefone as telefone_siscan,
        t.telefone as telefone_esaude,
        e.paciente__data_do_nascimento as data_nasc_siscan,
        t.data_nascimento as data_nasc_esaude,
        e.unidade_de_saude__data_da_solicitacao as data_solicitacao_siscan,
        e.prestador_de_servico__data_da_realizacao as data_realizacao,
        e.responsavel_pelo_resultado__data_da_liberacao as data_liberacao,
        e.prestador_de_servico__nome as prestador_servico,
        t.data_solicitacao_esaude,
        t.data_insercao_resultado_esaude,
        t.ultima_apac_cancer,
        COALESCE(t.ultima_apac_cancer::text, e.conclusao_apac, '') as conclusao_apac,
        e.abertura_aih,
        e.birads_max,
        e.unidade_de_saude__nome as unidade_saude,
        e.distrito_sanitario,
        CASE 
            WHEN e.birads_max IN ('4', '5') THEN 
                CASE WHEN e.wait_days IS NOT NULL AND e.wait_days <= 30 THEN 'Tempestivo' ELSE 'Atrasado' END
            WHEN e.birads_max = '0' THEN 
                CASE WHEN e.wait_days IS NOT NULL AND e.wait_days <= 30 THEN 'Tempestivo' ELSE 'Atrasado' END
            WHEN e.birads_max = '3' THEN 
                CASE WHEN e.wait_days IS NOT NULL AND e.wait_days <= 180 THEN 'Tempestivo' ELSE 'Atrasado' END
            WHEN e.birads_max IN ('1', '2') THEN 
                CASE WHEN e.wait_days IS NOT NULL AND e.wait_days <= 365 THEN 'Tempestivo' ELSE 'Atrasado' END
            ELSE ''
        END as tempestividade,
        COALESCE(d.total_registros, 1) as qtd_registros_cns,
        CASE WHEN d.total_registros > 1 THEN TRUE ELSE FALSE END as is_duplicado
    FROM exam_records e
    LEFT JOIN termo_linkage t ON e.paciente__cartao_sus = t.cartao_sus
    LEFT JOIN duplicatas d ON e.paciente__cartao_sus = d.paciente__cartao_sus
    WHERE e.unidade_de_saude__data_da_solicitacao >= '2023-01-01'
    {where_clause}
    ORDER BY 
        CASE WHEN d.total_registros > 1 THEN 0 ELSE 1 END,
        d.total_registros DESC NULLS LAST,
        e.unidade_de_saude__data_da_solicitacao DESC
    LIMIT :lim OFFSET :off
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_termo_linkage_count_sql(search_nome=None, search_cpf=None, search_cartao_sus=None):
    conditions = []
    params = {}
    
    if search_nome:
        conditions.append("(e.paciente__nome ILIKE :search_nome OR t.nome_esaude ILIKE :search_nome)")
        params['search_nome'] = f'%{search_nome}%'
    
    if search_cpf:
        conditions.append("t.cpf LIKE :search_cpf")
        params['search_cpf'] = f'%{search_cpf}%'
    
    if search_cartao_sus:
        conditions.append("CAST(e.paciente__cartao_sus AS TEXT) LIKE :search_cartao_sus")
        params['search_cartao_sus'] = f'%{search_cartao_sus}%'
    
    where_clause = ""
    if conditions:
        where_clause = " AND " + " AND ".join(conditions)
    
    query = f"""
    SELECT COUNT(*) as total
    FROM exam_records e
    LEFT JOIN termo_linkage t ON e.paciente__cartao_sus = t.cartao_sus
    WHERE e.unidade_de_saude__data_da_solicitacao >= '2023-01-01'
    {where_clause}
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        row = result.fetchone()
    
    return int(row[0]) if row and row[0] else 0


def calculate_priority(birads, data_liberacao=None, tem_apac_cancer=False, idade=None):
    """
    Calcula a prioridade do paciente baseado no algoritmo de priorização.
    
    Níveis de Prioridade:
    - CRÍTICA (1): BI-RADS 4 ou 5 - Fast-Track para Cancerologia
    - ALTA (2): BI-RADS 0 - Investigação Diagnóstica
    - MÉDIA (3): BI-RADS 3 - Monitoramento Semestral
    - MONITORAMENTO (4): BI-RADS 6 - Seguimento Oncológico
    - ROTINA (5): BI-RADS 1 ou 2 - Rastreamento em 2 anos
    """
    if birads in ['4', '5']:
        return {
            'nivel': 1,
            'prioridade': 'CRÍTICA',
            'cor': '#dc3545',
            'acao': 'Fast-Track Cancerologia',
            'sla_alerta': '24h',
            'sla_resolucao': '3 dias',
            'tipo_vaga': 'Vaga Protegida',
            'icone': 'fa-exclamation-circle'
        }
    elif birads == '0':
        return {
            'nivel': 2,
            'prioridade': 'ALTA',
            'cor': '#fd7e14',
            'acao': 'Investigação Diagnóstica',
            'sla_alerta': '7 dias',
            'sla_resolucao': '45 dias',
            'tipo_vaga': 'Eco-mama/USG',
            'icone': 'fa-search'
        }
    elif birads == '3':
        risco = 'ALTO' if tem_apac_cancer else 'BAIXO'
        return {
            'nivel': 3,
            'prioridade': 'MÉDIA',
            'cor': '#ffc107',
            'acao': f'Monitoramento Semestral ({risco} Risco)',
            'sla_alerta': '150 dias',
            'sla_resolucao': '6 meses',
            'tipo_vaga': 'Acompanhamento',
            'icone': 'fa-clock',
            'risco': risco
        }
    elif birads == '6':
        return {
            'nivel': 4,
            'prioridade': 'MONITORAMENTO',
            'cor': '#6f42c1',
            'acao': 'Seguimento Oncológico',
            'sla_alerta': 'Conforme protocolo',
            'sla_resolucao': 'Contínuo',
            'tipo_vaga': 'Oncologia',
            'icone': 'fa-heartbeat'
        }
    elif birads in ['1', '2']:
        return {
            'nivel': 5,
            'prioridade': 'ROTINA',
            'cor': '#28a745',
            'acao': 'Rastreamento em 2 anos',
            'sla_alerta': 'N/A',
            'sla_resolucao': '24 meses',
            'tipo_vaga': 'Rastreamento',
            'icone': 'fa-check-circle'
        }
    else:
        return {
            'nivel': 99,
            'prioridade': 'INDEFINIDO',
            'cor': '#6c757d',
            'acao': 'Verificar laudo',
            'sla_alerta': 'N/A',
            'sla_resolucao': 'N/A',
            'tipo_vaga': 'N/A',
            'icone': 'fa-question-circle'
        }


def get_unit_prioritization_sql(health_unit, year=None, region=None):
    """Get prioritization data for patients in a specific health unit"""
    if not health_unit:
        return pd.DataFrame()
    
    conditions = [
        "(e.unidade_de_saude__nome = :unit_name OR e.prestador_de_servico__nome = :unit_name)",
        "e.unidade_de_saude__data_da_solicitacao >= '2023-01-01'",
        "(e.prestador_de_servico__data_da_realizacao IS NULL OR e.prestador_de_servico__data_da_realizacao >= e.unidade_de_saude__data_da_solicitacao)",
        "(e.wait_days IS NULL OR (e.wait_days >= 0 AND e.wait_days <= 365))"
    ]
    params = {'unit_name': health_unit}
    
    if year:
        conditions.append("EXTRACT(YEAR FROM e.unidade_de_saude__data_da_solicitacao) = :unit_year")
        params['unit_year'] = year
    if region:
        conditions.append("e.distrito_sanitario = :unit_region")
        params['unit_region'] = region
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
    SELECT 
        e.paciente__nome as nome,
        e.paciente__cartao_sus as cartao_sus,
        e.paciente__idade as idade,
        e.birads_max,
        e.responsavel_pelo_resultado__data_da_liberacao as data_liberacao,
        e.unidade_de_saude__data_da_solicitacao as data_solicitacao,
        e.wait_days as dias_espera,
        e.unidade_de_saude__nome as unidade_saude,
        t.ultima_apac_cancer,
        CASE 
            WHEN t.ultima_apac_cancer IS NOT NULL THEN TRUE 
            ELSE FALSE 
        END as tem_historico_cancer
    FROM exam_records e
    LEFT JOIN termo_linkage t ON e.paciente__cartao_sus = t.cartao_sus
    WHERE {where_clause}
    AND e.birads_max IS NOT NULL 
    AND e.birads_max != ''
    ORDER BY 
        CASE e.birads_max
            WHEN '4' THEN 1
            WHEN '5' THEN 1
            WHEN '0' THEN 2
            WHEN '3' THEN 3
            WHEN '6' THEN 4
            ELSE 5
        END,
        e.responsavel_pelo_resultado__data_da_liberacao DESC
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    if df.empty:
        return df
    
    priorities = []
    for _, row in df.iterrows():
        tem_apac = row.get('tem_historico_cancer', False)
        priority = calculate_priority(
            str(row['birads_max']), 
            row.get('data_liberacao'),
            tem_apac,
            row.get('idade')
        )
        priorities.append(priority)
    
    df['prioridade'] = [p['prioridade'] for p in priorities]
    df['nivel'] = [p['nivel'] for p in priorities]
    df['acao'] = [p['acao'] for p in priorities]
    df['sla_resolucao'] = [p['sla_resolucao'] for p in priorities]
    df['cor'] = [p['cor'] for p in priorities]
    
    return df


def get_unit_priority_summary_sql(health_unit, year=None, region=None):
    """Get summary of priorities for a specific health unit"""
    if not health_unit:
        return {}
    
    where_clause, params = _build_unit_where_clause(health_unit, year, region)
    
    query = f"""
    SELECT 
        CASE 
            WHEN birads_max IN ('4', '5') THEN 'CRÍTICA'
            WHEN birads_max = '0' THEN 'ALTA'
            WHEN birads_max = '3' THEN 'MÉDIA'
            WHEN birads_max = '6' THEN 'MONITORAMENTO'
            WHEN birads_max IN ('1', '2') THEN 'ROTINA'
            ELSE 'INDEFINIDO'
        END as prioridade,
        COUNT(*) as total
    FROM exam_records
    WHERE {where_clause}
    AND birads_max IS NOT NULL AND birads_max != ''
    GROUP BY 1
    ORDER BY 1
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    summary = {
        'CRÍTICA': 0,
        'ALTA': 0,
        'MÉDIA': 0,
        'MONITORAMENTO': 0,
        'ROTINA': 0,
        'INDEFINIDO': 0
    }
    
    for _, row in df.iterrows():
        if row['prioridade'] in summary:
            summary[row['prioridade']] = int(row['total'])
    
    summary['total'] = sum(summary.values())
    
    return summary


def create_access_request(name, email, phone, cpf, matricula, username, access_level, district, health_unit, justification):
    from src.models import AccessRequest, get_session
    
    session = get_session()
    try:
        duplicates = []
        
        if session.execute(text("SELECT id FROM access_requests WHERE username = :val AND status = 'pending'"), {'val': username}).fetchone():
            duplicates.append('Nome de usuário (solicitação pendente)')
        if session.execute(text("SELECT id FROM users WHERE username = :val AND is_active = true"), {'val': username}).fetchone():
            duplicates.append('Nome de usuário (usuário ativo)')
        
        if cpf:
            if session.execute(text("SELECT id FROM access_requests WHERE cpf = :val AND status = 'pending'"), {'val': cpf}).fetchone():
                duplicates.append('CPF (solicitação pendente)')
            if session.execute(text("SELECT id FROM users WHERE cpf = :val AND is_active = true"), {'val': cpf}).fetchone():
                duplicates.append('CPF (usuário ativo)')
        
        if email:
            if session.execute(text("SELECT id FROM access_requests WHERE email = :val AND status = 'pending'"), {'val': email}).fetchone():
                duplicates.append('E-mail (solicitação pendente)')
            if session.execute(text("SELECT id FROM users WHERE email = :val AND is_active = true"), {'val': email}).fetchone():
                duplicates.append('E-mail (usuário ativo)')
        
        if matricula:
            if session.execute(text("SELECT id FROM access_requests WHERE matricula = :val AND status = 'pending'"), {'val': matricula}).fetchone():
                duplicates.append('Matrícula (solicitação pendente)')
            if session.execute(text("SELECT id FROM users WHERE matricula = :val AND is_active = true"), {'val': matricula}).fetchone():
                duplicates.append('Matrícula (usuário ativo)')
        
        if duplicates:
            return {'success': False, 'message': f'Dados duplicados encontrados: {", ".join(duplicates)}'}
        
        session.execute(
            text("""
                INSERT INTO access_requests (name, email, phone, cpf, matricula, username, access_level, district, health_unit, justification, status, created_at)
                VALUES (:name, :email, :phone, :cpf, :matricula, :username, :access_level, :district, :health_unit, :justification, 'pending', NOW())
            """),
            {
                'name': name, 'email': email, 'phone': phone, 'cpf': cpf,
                'matricula': matricula, 'username': username, 'access_level': access_level,
                'district': district, 'health_unit': health_unit, 'justification': justification
            }
        )
        session.commit()
        return {'success': True, 'message': 'Solicitação enviada com sucesso! Aguarde a aprovação.'}
    except Exception as e:
        session.rollback()
        return {'success': False, 'message': f'Erro ao enviar solicitação: {str(e)}'}
    finally:
        session.close()


def get_pending_access_requests(user_access_level=None, user_district=None):
    engine = get_engine()
    
    if user_access_level == 'secretaria':
        query = """
            SELECT id, name, email, phone, cpf, matricula, username, access_level, district, health_unit, justification, created_at
            FROM access_requests 
            WHERE status = 'pending'
            ORDER BY created_at DESC
        """
        params = {}
    elif user_access_level == 'distrito' and user_district:
        query = """
            SELECT id, name, email, phone, cpf, matricula, username, access_level, district, health_unit, justification, created_at
            FROM access_requests 
            WHERE status = 'pending' 
            AND (district = :district OR health_unit IN (
                SELECT DISTINCT unidade_de_saude__nome FROM exam_records WHERE distrito_sanitario = :district
            ))
            ORDER BY created_at DESC
        """
        params = {'district': user_district}
    else:
        return pd.DataFrame()
    
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def approve_access_request(request_id, reviewed_by, temp_password=None):
    from werkzeug.security import generate_password_hash
    import secrets
    import string
    
    if not temp_password:
        chars = string.ascii_letters + string.digits
        temp_password = ''.join(secrets.choice(chars) for _ in range(12))
    
    engine = get_engine()
    
    with engine.connect() as conn:
        request = conn.execute(
            text("SELECT * FROM access_requests WHERE id = :id AND status = 'pending'"),
            {'id': request_id}
        ).fetchone()
        
        if not request:
            return {'success': False, 'message': 'Solicitação não encontrada ou já processada.'}
        
        try:
            password_hash = generate_password_hash(temp_password)
            
            user_role = 'admin' if request.access_level in ('secretaria', 'distrito') else 'viewer'
            
            conn.execute(
                text("""
                    INSERT INTO users (username, password_hash, name, role, access_level, district, health_unit, email, phone, cpf, matricula, is_active, created_at, must_change_password)
                    VALUES (:username, :password_hash, :name, :role, :access_level, :district, :health_unit, :email, :phone, :cpf, :matricula, true, NOW(), true)
                """),
                {
                    'username': request.username,
                    'password_hash': password_hash,
                    'name': request.name,
                    'role': user_role,
                    'access_level': request.access_level,
                    'district': request.district,
                    'health_unit': request.health_unit,
                    'email': request.email,
                    'phone': request.phone,
                    'cpf': request.cpf,
                    'matricula': request.matricula
                }
            )
            
            conn.execute(
                text("""
                    UPDATE access_requests 
                    SET status = 'approved', reviewed_at = NOW(), reviewed_by = :reviewed_by
                    WHERE id = :id
                """),
                {'id': request_id, 'reviewed_by': reviewed_by}
            )
            
            conn.commit()
            return {
                'success': True, 
                'message': f'Acesso aprovado! Usuário: {request.username}',
                'temp_password': temp_password,
                'username': request.username,
                'email': request.email
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': f'Erro ao aprovar: {str(e)}'}


def reject_access_request(request_id, reviewed_by, reason):
    engine = get_engine()
    
    with engine.connect() as conn:
        try:
            conn.execute(
                text("""
                    UPDATE access_requests 
                    SET status = 'rejected', reviewed_at = NOW(), reviewed_by = :reviewed_by, rejection_reason = :reason
                    WHERE id = :id AND status = 'pending'
                """),
                {'id': request_id, 'reviewed_by': reviewed_by, 'reason': reason}
            )
            conn.commit()
            return {'success': True, 'message': 'Solicitação rejeitada.'}
        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': f'Erro ao rejeitar: {str(e)}'}


def get_units_by_district(district):
    engine = get_engine()
    query = """
        SELECT DISTINCT unidade_de_saude__nome 
        FROM exam_records 
        WHERE distrito_sanitario = :district AND unidade_de_saude__nome IS NOT NULL
        ORDER BY unidade_de_saude__nome
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {'district': district})
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df['unidade_de_saude__nome'].tolist() if not df.empty else []


def get_district_for_unit(health_unit):
    engine = get_engine()
    query = """
        SELECT DISTINCT distrito_sanitario 
        FROM exam_records 
        WHERE (unidade_de_saude__nome = :health_unit OR prestador_de_servico__nome = :health_unit) AND distrito_sanitario IS NOT NULL
        LIMIT 1
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {'health_unit': health_unit})
        row = result.fetchone()
    return row[0] if row else None


def create_password_reset_token(email):
    import secrets
    from datetime import datetime, timedelta
    
    engine = get_engine()
    
    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT id, username, email FROM users WHERE email = :email AND is_active = true"),
            {'email': email}
        ).fetchone()
        
        if not user:
            return {'success': False, 'message': 'E-mail não encontrado.'}
        
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=2)
        
        try:
            conn.execute(
                text("""
                    UPDATE users 
                    SET password_reset_token = :token, password_reset_expires = :expires
                    WHERE id = :id
                """),
                {'id': user.id, 'token': token, 'expires': expires}
            )
            conn.commit()
            return {
                'success': True,
                'token': token,
                'username': user.username,
                'email': user.email
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': f'Erro ao gerar token: {str(e)}'}


def validate_reset_token(token):
    from datetime import datetime
    
    engine = get_engine()
    
    with engine.connect() as conn:
        user = conn.execute(
            text("""
                SELECT id, username FROM users 
                WHERE password_reset_token = :token 
                AND password_reset_expires > :now 
                AND is_active = true
            """),
            {'token': token, 'now': datetime.utcnow()}
        ).fetchone()
        
        if user:
            return {'valid': True, 'user_id': user.id, 'username': user.username}
        return {'valid': False}


def reset_password_with_token(token, new_password):
    from werkzeug.security import generate_password_hash
    from datetime import datetime
    
    engine = get_engine()
    
    with engine.connect() as conn:
        user = conn.execute(
            text("""
                SELECT id FROM users 
                WHERE password_reset_token = :token 
                AND password_reset_expires > :now 
                AND is_active = true
            """),
            {'token': token, 'now': datetime.utcnow()}
        ).fetchone()
        
        if not user:
            return {'success': False, 'message': 'Token inválido ou expirado.'}
        
        try:
            password_hash = generate_password_hash(new_password)
            conn.execute(
                text("""
                    UPDATE users 
                    SET password_hash = :password_hash, 
                        password_reset_token = NULL, 
                        password_reset_expires = NULL,
                        must_change_password = false
                    WHERE id = :id
                """),
                {'id': user.id, 'password_hash': password_hash}
            )
            conn.commit()
            return {'success': True, 'message': 'Senha alterada com sucesso!'}
        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': f'Erro ao alterar senha: {str(e)}'}


def change_password_first_access(user_id, new_password):
    from werkzeug.security import generate_password_hash
    
    engine = get_engine()
    
    with engine.connect() as conn:
        try:
            password_hash = generate_password_hash(new_password)
            conn.execute(
                text("""
                    UPDATE users 
                    SET password_hash = :password_hash, must_change_password = false
                    WHERE id = :id
                """),
                {'id': user_id, 'password_hash': password_hash}
            )
            conn.commit()
            return {'success': True, 'message': 'Senha alterada com sucesso!'}
        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': f'Erro ao alterar senha: {str(e)}'}
