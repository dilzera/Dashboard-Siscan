import pandas as pd
import os
from src.models import TermoLinkage, get_session, get_engine, Base

def import_termo_linkage():
    engine = get_engine()
    Base.metadata.create_all(engine, tables=[TermoLinkage.__table__])
    
    db_session = get_session()
    try:
        count = db_session.query(TermoLinkage).count()
        if count > 0:
            print(f"Tabela termo_linkage ja possui {count} registros. Pulando importacao.")
            return
        
        excel_path = 'attached_assets/Relatorio_final_DADOS_SISCAN_2023_2025__1765810928026.xlsx'
        if not os.path.exists(excel_path):
            print(f"Arquivo Excel nao encontrado: {excel_path}")
            return
        
        print("Importando dados de termo_linkage do Excel...")
        df = pd.read_excel(excel_path, engine='openpyxl')
        print(f"Lendo {len(df)} registros do Excel...")
        
        def convert_cpf(cpf_value):
            if pd.isna(cpf_value):
                return None
            try:
                cpf_int = int(float(cpf_value))
                cpf_str = str(cpf_int).zfill(11)
                return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:11]}"
            except:
                return str(cpf_value) if cpf_value else None
        
        def parse_date(date_value):
            if pd.isna(date_value):
                return None
            try:
                if isinstance(date_value, str):
                    return pd.to_datetime(date_value).date()
                return pd.Timestamp(date_value).date()
            except:
                return None
        
        records = []
        batch_count = 0
        for idx, row in df.iterrows():
            cartao_sus = row.get('paciente__cartao_sus')
            if pd.isna(cartao_sus):
                continue
            
            record = TermoLinkage(
                cartao_sus=int(cartao_sus) if not pd.isna(cartao_sus) else None,
                cpf=convert_cpf(row.get('CPF')),
                telefone=str(row.get('paciente__telefone', ''))[:50] if not pd.isna(row.get('paciente__telefone')) else None,
                data_nascimento=str(row.get('paciente__data_do_nascimento', ''))[:20] if not pd.isna(row.get('paciente__data_do_nascimento')) else None,
                data_solicitacao_esaude=parse_date(row.get('DATA SOLICITACAO MAMOGRAFIA ESAUDE')),
                data_insercao_resultado_esaude=parse_date(row.get('DATA INSERÇÃO RESULTADO MAMOGRAFIA ESAUDE')),
                ultima_apac_cancer=parse_date(row.get('ULTIMA APAC CANCER ESAUDE - SE HOUVER')),
                nome_esaude=str(row.get('Nome no esaude', ''))[:300] if not pd.isna(row.get('Nome no esaude')) else None,
                comparacao_nomes=str(row.get('Comparação de nomes', ''))[:50] if not pd.isna(row.get('Comparação de nomes')) else None
            )
            records.append(record)
            
            if len(records) >= 5000:
                db_session.bulk_save_objects(records)
                db_session.commit()
                batch_count += len(records)
                print(f"Importados {batch_count} registros...")
                records = []
        
        if records:
            db_session.bulk_save_objects(records)
            db_session.commit()
            batch_count += len(records)
        
        final_count = db_session.query(TermoLinkage).count()
        print(f"Termo Linkage: {final_count} registros importados com sucesso!")
    except Exception as e:
        print(f"Erro ao importar termo_linkage: {e}")
        import traceback
        traceback.print_exc()
        db_session.rollback()
    finally:
        db_session.close()

if __name__ == '__main__':
    import_termo_linkage()
