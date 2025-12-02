import pandas as pd
from sqlalchemy import text
from src.models import get_engine
from datetime import datetime, timedelta


def get_dataframe(query=None, params=None):
    engine = get_engine()
    if query is None:
        query = "SELECT * FROM exam_records"
    return pd.read_sql(query, engine, params=params)


def get_years():
    engine = get_engine()
    query = "SELECT DISTINCT year FROM exam_records WHERE year IS NOT NULL ORDER BY year DESC"
    df = pd.read_sql(query, engine)
    return [int(y) for y in df['year'].dropna().tolist()]


def get_health_units():
    engine = get_engine()
    query = "SELECT DISTINCT unidade_de_saude__nome FROM exam_records WHERE unidade_de_saude__nome IS NOT NULL ORDER BY unidade_de_saude__nome"
    df = pd.read_sql(query, engine)
    return df['unidade_de_saude__nome'].dropna().tolist()


def get_regions():
    engine = get_engine()
    query = "SELECT DISTINCT unidade_de_saude__uf FROM exam_records WHERE unidade_de_saude__uf IS NOT NULL ORDER BY unidade_de_saude__uf"
    df = pd.read_sql(query, engine)
    return df['unidade_de_saude__uf'].dropna().tolist()


def get_municipalities():
    engine = get_engine()
    query = "SELECT DISTINCT unidade_de_saude__municipio FROM exam_records WHERE unidade_de_saude__municipio IS NOT NULL ORDER BY unidade_de_saude__municipio"
    df = pd.read_sql(query, engine)
    return df['unidade_de_saude__municipio'].dropna().tolist()


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
    
    return get_dataframe(query, params)


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
