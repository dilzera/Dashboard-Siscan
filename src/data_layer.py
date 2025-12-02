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
        conditions.append("distrito_sanitario = :region")
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
    query = "SELECT DISTINCT distrito_sanitario FROM exam_records WHERE distrito_sanitario IS NOT NULL ORDER BY distrito_sanitario"
    with engine.connect() as conn:
        result = conn.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df['distrito_sanitario'].dropna().tolist()


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


def _build_navigation_where_clause(year=None, health_unit=None, region=None, conformity=None, table_prefix=""):
    """Build a safe parameterized WHERE clause for patient navigation queries"""
    conditions = ["patient_unique_id IS NOT NULL", "unidade_de_saude__data_da_solicitacao >= '2023-01-01'"]
    params = {}
    
    prefix = f"{table_prefix}." if table_prefix else ""
    
    if year:
        conditions.append(f"EXTRACT(YEAR FROM {prefix}unidade_de_saude__data_da_solicitacao) = :nav_year")
        params['nav_year'] = year
    if health_unit:
        conditions.append(f"{prefix}unidade_de_saude__nome = :nav_health_unit")
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


def get_patient_navigation_list_sql(year=None, health_unit=None, region=None, conformity=None, min_exams=2, limit=100):
    """Get list of patients with multiple exams and their exam history"""
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
            e.birads_max,
            e.birads_direita,
            e.birads_esquerda,
            e.unidade_de_saude__nome as unidade_saude,
            e.distrito_sanitario,
            e.wait_days,
            e.conformity_status,
            ROW_NUMBER() OVER (PARTITION BY e.patient_unique_id ORDER BY e.unidade_de_saude__data_da_solicitacao) as exam_order
        FROM exam_records e
        INNER JOIN patient_exam_counts p ON e.patient_unique_id = p.patient_unique_id
        WHERE {where_clause_e}
    )
    SELECT 
        patient_unique_id,
        nome_paciente,
        cartao_sus,
        total_exames,
        exam_order,
        data_solicitacao,
        data_realizacao,
        birads_max,
        birads_direita,
        birads_esquerda,
        unidade_saude,
        distrito_sanitario,
        wait_days,
        conformity_status
    FROM patient_exams
    ORDER BY total_exames DESC, nome_paciente, exam_order
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
                                      patient_name=None, sex=None, birads=None):
    """Build a safe parameterized WHERE clause for patient data queries"""
    conditions = ["unidade_de_saude__data_da_solicitacao >= '2023-01-01'"]
    params = {}
    
    if year:
        conditions.append("EXTRACT(YEAR FROM unidade_de_saude__data_da_solicitacao) = :pd_year")
        params['pd_year'] = year
    if health_unit:
        conditions.append("unidade_de_saude__nome = :pd_health_unit")
        params['pd_health_unit'] = health_unit
    if region:
        conditions.append("distrito_sanitario = :pd_region")
        params['pd_region'] = region
    if conformity:
        conditions.append("conformity_status = :pd_conformity")
        params['pd_conformity'] = conformity
    if patient_name:
        conditions.append("UPPER(paciente__nome) LIKE UPPER(:pd_patient_name)")
        params['pd_patient_name'] = f"%{patient_name}%"
    if sex:
        conditions.append("paciente__sexo = :pd_sex")
        params['pd_sex'] = sex
    if birads:
        conditions.append("birads_max = :pd_birads")
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
        paciente__nome as nome,
        paciente__idade as idade,
        paciente__sexo as sexo,
        paciente__data_do_nascimento as data_nascimento,
        paciente__mae as nome_mae,
        unidade_de_saude__nome as unidade_saude,
        unidade_de_saude__data_da_solicitacao as data_solicitacao,
        prestador_de_servico__data_da_realizacao as data_realizacao,
        responsavel_pelo_resultado__data_da_liberacao as data_liberacao,
        prestador_de_servico__nome as prestador_servico,
        unidade_de_saude__n_do_exame as numero_exame,
        COALESCE(resultado_exame__indicacao__tipo_de_mamografia, resultado_exame__indicacao__mamografia_de_rastreamento) as tipo_mamografia,
        COALESCE(resultado_exame__mama_direita__tipo_de_mama, resultado_exame__mama_esquerda__tipo_de_mama) as tipo_mama,
        resultado_exame__linfonodos_axilares__linfonodos_axilares as linfonodos_axilares,
        resultado_exame__achados_benignos__achados_benignos as achados_benignos,
        resultado_exame__classificacao_radiologica__mama_direita as birads_direita_class,
        resultado_exame__classificacao_radiologica__mama_esquerda as birads_esquerda_class,
        resultado_exame__recomendacoes as recomendacoes,
        birads_max,
        distrito_sanitario,
        conformity_status,
        wait_days
    FROM exam_records
    WHERE {where_clause}
    ORDER BY unidade_de_saude__data_da_solicitacao DESC, paciente__nome
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
        year, health_unit, region, conformity, patient_name, sex, birads
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


def _build_unit_where_clause(health_unit, year=None, region=None):
    """Build WHERE clause for health unit specific queries"""
    conditions = [
        "unidade_de_saude__nome = :unit_name",
        "unidade_de_saude__data_da_solicitacao >= '2023-01-01'",
        "(prestador_de_servico__data_da_realizacao IS NULL OR prestador_de_servico__data_da_realizacao >= unidade_de_saude__data_da_solicitacao)",
        "(wait_days IS NULL OR (wait_days >= 0 AND wait_days <= 365))"
    ]
    params = {'unit_name': health_unit}
    
    if year:
        conditions.append("EXTRACT(YEAR FROM unidade_de_saude__data_da_solicitacao) = :unit_year")
        params['unit_year'] = year
    if region:
        conditions.append("distrito_sanitario = :unit_region")
        params['unit_region'] = region
    
    return " AND ".join(conditions), params


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
        COUNT(CASE WHEN birads_max IN ('4', '5') THEN 1 END) as casos_alto_risco
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
            'casos_alto_risco': 0
        }
    
    return {
        'total_exames': int(row[0]) if row[0] else 0,
        'total_pacientes': int(row[1]) if row[1] else 0,
        'media_espera': round(float(row[2]) if row[2] else 0, 1),
        'mediana_espera': round(float(row[3]) if row[3] else 0, 1),
        'taxa_conformidade': round(float(row[4]) if row[4] else 0, 1),
        'casos_alto_risco': int(row[5]) if row[5] else 0
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
    
    where_clause, params = _build_unit_where_clause(health_unit, year, region)
    params['follow_limit'] = limit
    
    query = f"""
    WITH latest_exams AS (
        SELECT 
            patient_unique_id,
            paciente__nome,
            paciente__cartao_sus,
            paciente__idade,
            birads_max,
            birads_direita,
            birads_esquerda,
            unidade_de_saude__data_da_solicitacao as data_exame,
            prestador_de_servico__data_da_realizacao as data_realizacao,
            wait_days,
            ROW_NUMBER() OVER (PARTITION BY patient_unique_id ORDER BY unidade_de_saude__data_da_solicitacao DESC) as rn
        FROM exam_records
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
            wait_days,
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
        wait_days as espera_dias,
        intervalo_retorno_dias,
        motivo_retorno,
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
