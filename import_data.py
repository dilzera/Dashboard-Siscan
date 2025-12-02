import pandas as pd
from datetime import datetime
from sqlalchemy import text
from src.models import get_engine, init_db, drop_all_tables, generate_patient_id
import hashlib

def parse_date(date_str):
    if pd.isna(date_str) or date_str == '' or date_str is None:
        return None
    try:
        if isinstance(date_str, datetime):
            return date_str.date()
        return datetime.strptime(str(date_str), '%d/%m/%Y').date()
    except:
        try:
            return datetime.strptime(str(date_str), '%Y-%m-%d').date()
        except:
            return None


def extract_birads(classification):
    if pd.isna(classification) or classification is None:
        return None
    classification = str(classification).strip()
    if classification.startswith('Categoria '):
        return classification.split(' ')[1]
    return None


def get_max_birads(birads_d, birads_e):
    values = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6}
    d_val = values.get(str(birads_d) if pd.notna(birads_d) else '', -1)
    e_val = values.get(str(birads_e) if pd.notna(birads_e) else '', -1)
    max_val = max(d_val, e_val)
    for k, v in values.items():
        if v == max_val:
            return k
    return None


def gen_patient_id(row):
    key_string = f"{row['paciente__cartao_sus'] if pd.notna(row['paciente__cartao_sus']) else ''}|{row['paciente__nome'] if pd.notna(row['paciente__nome']) else ''}|{row['paciente__mae'] if pd.notna(row['paciente__mae']) else ''}".upper().strip()
    return hashlib.sha256(key_string.encode()).hexdigest()[:16]


def import_excel_data(excel_path):
    print(f"Reading Excel file: {excel_path}")
    df = pd.read_excel(excel_path)
    print(f"Total rows to import: {len(df)}")
    
    engine = get_engine()
    
    print("Dropping existing table...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS exam_records CASCADE"))
        conn.commit()
    
    print("Processing data...")
    
    df['unidade_de_saude__data_da_solicitacao'] = df['unidade_de_saude__data_da_solicitacao'].apply(parse_date)
    df['prestador_de_servico__data_da_realizacao'] = df['prestador_de_servico__data_da_realizacao'].apply(parse_date)
    df['paciente__data_do_nascimento'] = df['paciente__data_do_nascimento'].apply(parse_date)
    df['responsavel_pelo_resultado__data_da_liberacao_do_resultado'] = df['responsavel_pelo_resultado__data_da_liberacao_do_resultado'].apply(parse_date)
    
    df['birads_direita'] = df['resultado_exame__classificacao_radiologica__mama_direita'].apply(extract_birads)
    df['birads_esquerda'] = df['resultado_exame__classificacao_radiologica__mama_esquerda'].apply(extract_birads)
    df['birads_max'] = df.apply(lambda row: get_max_birads(row['birads_direita'], row['birads_esquerda']), axis=1)
    
    def calc_wait_days(row):
        if pd.notna(row['unidade_de_saude__data_da_solicitacao']) and pd.notna(row['prestador_de_servico__data_da_realizacao']):
            days = (row['prestador_de_servico__data_da_realizacao'] - row['unidade_de_saude__data_da_solicitacao']).days
            return max(0, days)
        return None
    
    df['wait_days'] = df.apply(calc_wait_days, axis=1)
    df['conformity_status'] = df['wait_days'].apply(lambda x: 'Dentro do Prazo' if pd.notna(x) and x <= 30 else ('Fora do Prazo' if pd.notna(x) else None))
    
    df['year'] = df['unidade_de_saude__data_da_solicitacao'].apply(lambda x: x.year if pd.notna(x) else None)
    df['month'] = df['unidade_de_saude__data_da_solicitacao'].apply(lambda x: x.month if pd.notna(x) else None)
    
    print("Generating patient IDs...")
    df['patient_unique_id'] = df.apply(gen_patient_id, axis=1)
    
    column_mapping = {
        'patient_unique_id': 'patient_unique_id',
        'geral__emissao': 'geral__emissao',
        'geral__hora': 'geral__hora',
        'geral__uf': 'geral__uf',
        'unidade_de_saude__nome': 'unidade_de_saude__nome',
        'unidade_de_saude__cnes': 'unidade_de_saude__cnes',
        'unidade_de_saude__data_da_solicitacao': 'unidade_de_saude__data_da_solicitacao',
        'unidade_de_saude__uf': 'unidade_de_saude__uf',
        'unidade_de_saude__municipio': 'unidade_de_saude__municipio',
        'unidade_de_saude__n_do_exame': 'unidade_de_saude__n_do_exame',
        'unidade_de_saude__n_do_protocolo': 'unidade_de_saude__n_do_protocolo',
        'unidade_de_saude__n_do_prontuario': 'unidade_de_saude__n_do_prontuario',
        'paciente__cartao_sus': 'paciente__cartao_sus',
        'paciente__sexo': 'paciente__sexo',
        'paciente__nome': 'paciente__nome',
        'paciente__idade': 'paciente__idade',
        'paciente__data_do_nascimento': 'paciente__data_do_nascimento',
        'paciente__telefone': 'paciente__telefone',
        'paciente__mae': 'paciente__mae',
        'paciente__bairro': 'paciente__bairro',
        'paciente__endereco': 'paciente__endereco',
        'paciente__municipio': 'paciente__municipio',
        'paciente__uf': 'paciente__uf',
        'paciente__cep': 'paciente__cep',
        'paciente__numero': 'paciente__numero',
        'paciente__complemento': 'paciente__complemento',
        'prestador_de_servico__nome': 'prestador_de_servico__nome',
        'prestador_de_servico__cnes': 'prestador_de_servico__cnes',
        'prestador_de_servico__cnpj': 'prestador_de_servico__cnpj',
        'prestador_de_servico__data_da_realizacao': 'prestador_de_servico__data_da_realizacao',
        'prestador_de_servico__uf': 'prestador_de_servico__uf',
        'prestador_de_servico__municipio': 'prestador_de_servico__municipio',
        'resultado_exame__indicacao__tipo_de_mamografia': 'resultado_exame__indicacao__tipo_de_mamografia',
        'resultado_exame__indicacao__mamografia_de_rastreamento': 'resultado_exame__indicacao__mamografia_de_rastreamento',
        'resultado_exame__mamografia__numero_de_filmes': 'resultado_exame__mamografia__numero_de_filmes',
        'resultado_exame__mama_direita__pele': 'resultado_exame__mama_direita__pele',
        'resultado_exame__mama_direita__tipo_de_mama': 'resultado_exame__mama_direita__tipo_de_mama',
        'resultado_exame__linfonodos_axilares__linfonodos_axilares': 'resultado_exame__linfonodos_axilares__linfonodos_axilares',
        'resultado_exame__achados_benignos__achados_benignos': 'resultado_exame__achados_benignos__achados_benignos',
        'resultado_exame__mama_esquerda__pele': 'resultado_exame__mama_esquerda__pele',
        'resultado_exame__mama_esquerda__tipo_de_mama': 'resultado_exame__mama_esquerda__tipo_de_mama',
        'resultado_exame__classificacao_radiologica__mama_direita': 'resultado_exame__classificacao_radiologica__mama_direita',
        'resultado_exame__classificacao_radiologica__mama_esquerda': 'resultado_exame__classificacao_radiologica__mama_esquerda',
        'resultado_exame__recomendacoes': 'resultado_exame__recomendacoes',
        'responsavel_pelo_resultado__responsavel': 'responsavel_pelo_resultado__responsavel',
        'responsavel_pelo_resultado__conselho': 'responsavel_pelo_resultado__conselho',
        'responsavel_pelo_resultado__cns': 'responsavel_pelo_resultado__cns',
        'responsavel_pelo_resultado__data_da_liberacao_do_resultado': 'responsavel_pelo_resultado__data_da_liberacao',
        'birads_direita': 'birads_direita',
        'birads_esquerda': 'birads_esquerda',
        'birads_max': 'birads_max',
        'wait_days': 'wait_days',
        'conformity_status': 'conformity_status',
        'year': 'year',
        'month': 'month',
    }
    
    df_export = df[[col for col in column_mapping.keys() if col in df.columns]].copy()
    df_export.columns = [column_mapping[col] for col in df_export.columns]
    
    print(f"Importing {len(df_export)} records to database...")
    df_export.to_sql('exam_records', engine, if_exists='replace', index=True, index_label='id', chunksize=5000)
    
    print("Creating indexes...")
    with engine.connect() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_patient_id ON exam_records(patient_unique_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_year ON exam_records(year)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_birads ON exam_records(birads_max)"))
        conn.commit()
    
    print("Import completed successfully!")
    print(f"Total records: {len(df_export)}")


if __name__ == '__main__':
    import_excel_data('attached_assets/17112025-consolidated_report_resultsv2_1764696924024.xlsx')
