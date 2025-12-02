import pandas as pd
from sqlalchemy import text
from src.models import get_engine
from datetime import datetime, timedelta
import random


def get_dataframe(query=None, params=None):
    engine = get_engine()
    if query is None:
        query = "SELECT * FROM exam_records"
    return pd.read_sql(query, engine, params=params)


def get_years():
    engine = get_engine()
    query = "SELECT DISTINCT year FROM exam_records ORDER BY year DESC"
    df = pd.read_sql(query, engine)
    return df['year'].tolist()


def get_health_units():
    engine = get_engine()
    query = "SELECT DISTINCT health_unit FROM exam_records ORDER BY health_unit"
    df = pd.read_sql(query, engine)
    return df['health_unit'].tolist()


def get_regions():
    engine = get_engine()
    query = "SELECT DISTINCT region FROM exam_records ORDER BY region"
    df = pd.read_sql(query, engine)
    return df['region'].tolist()


def get_filtered_data(year=None, health_unit=None, conformity_status=None, region=None):
    conditions = []
    params = {}
    
    if year:
        conditions.append("year = :year")
        params['year'] = year
    
    if health_unit:
        conditions.append("health_unit = :health_unit")
        params['health_unit'] = health_unit
    
    if conformity_status:
        conditions.append("conformity_status = :conformity_status")
        params['conformity_status'] = conformity_status
    
    if region:
        conditions.append("region = :region")
        params['region'] = region
    
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
            'high_risk_count': 0
        }
    
    mean_wait = df['wait_days'].mean()
    median_wait = df['wait_days'].median()
    conformity_rate = (df['conformity_status'] == 'Dentro do Prazo').sum() / len(df) * 100
    total_exams = len(df)
    high_risk_count = df[df['birads_category'].isin(['4', '5'])].shape[0]
    
    return {
        'mean_wait': round(mean_wait, 1),
        'median_wait': round(median_wait, 1),
        'conformity_rate': round(conformity_rate, 1),
        'total_exams': total_exams,
        'high_risk_count': high_risk_count
    }


def get_monthly_volume(df):
    if df.empty:
        return pd.DataFrame()
    
    df['month_year'] = pd.to_datetime(df['request_date']).dt.to_period('M')
    monthly = df.groupby('month_year').size().reset_index(name='count')
    monthly['month_year'] = monthly['month_year'].astype(str)
    return monthly


def get_birads_distribution(df):
    if df.empty:
        return pd.DataFrame()
    
    dist = df.groupby('birads_category').size().reset_index(name='count')
    dist = dist.sort_values('birads_category')
    return dist


def get_conformity_by_unit(df):
    if df.empty:
        return pd.DataFrame()
    
    grouped = df.groupby(['health_unit', 'conformity_status']).size().unstack(fill_value=0)
    grouped = grouped.reset_index()
    
    if 'Dentro do Prazo' in grouped.columns and 'Fora do Prazo' in grouped.columns:
        grouped['total'] = grouped['Dentro do Prazo'] + grouped['Fora do Prazo']
        grouped['conformity_rate'] = (grouped['Dentro do Prazo'] / grouped['total'] * 100).round(1)
    else:
        grouped['total'] = 0
        grouped['conformity_rate'] = 0
    
    return grouped.sort_values('total', ascending=False).head(10)


def get_high_risk_cases(df):
    if df.empty:
        return pd.DataFrame()
    
    high_risk = df[df['birads_category'].isin(['4', '5'])].copy()
    high_risk = high_risk.sort_values('wait_days', ascending=False)
    return high_risk.head(20)


def populate_sample_data():
    from src.models import ExamRecord, get_session, init_db
    
    init_db()
    session = get_session()
    
    existing = session.query(ExamRecord).count()
    if existing > 0:
        session.close()
        return
    
    health_units = [
        'UBS Central', 'Hospital Municipal', 'Clinica Santa Maria',
        'Centro de Saude Norte', 'UBS Sul', 'Hospital Regional',
        'Clinica Sao Jose', 'Centro Diagnostico', 'UBS Leste', 'Hospital Universitario'
    ]
    
    regions = ['Norte', 'Sul', 'Leste', 'Oeste', 'Centro']
    
    municipalities = ['Sao Paulo', 'Campinas', 'Santos', 'Ribeirao Preto', 'Sorocaba']
    
    birads_weights = ['0', '1', '2', '3', '4', '5']
    birads_probs = [0.1, 0.25, 0.30, 0.20, 0.10, 0.05]
    
    age_groups = ['40-49', '50-59', '60-69', '70+']
    
    records = []
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2024, 11, 30)
    
    for i in range(2000):
        request_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        wait_days = random.choices(
            [random.randint(1, 20), random.randint(21, 35), random.randint(36, 90)],
            weights=[0.6, 0.25, 0.15]
        )[0]
        completion_date = request_date + timedelta(days=wait_days)
        
        birads = random.choices(birads_weights, weights=birads_probs)[0]
        
        conformity_status = 'Dentro do Prazo' if wait_days <= 30 else 'Fora do Prazo'
        
        health_unit = random.choice(health_units)
        region = random.choice(regions)
        
        record = ExamRecord(
            patient_id=f'PAC{i+1:06d}',
            health_unit=health_unit,
            health_unit_code=f'US{health_units.index(health_unit)+1:03d}',
            region=region,
            municipality=random.choice(municipalities),
            request_date=request_date.date(),
            completion_date=completion_date.date(),
            wait_days=wait_days,
            birads_category=birads,
            exam_type='Mamografia',
            age_group=random.choice(age_groups),
            conformity_status=conformity_status,
            year=request_date.year,
            month=request_date.month
        )
        records.append(record)
    
    session.bulk_save_objects(records)
    session.commit()
    session.close()
