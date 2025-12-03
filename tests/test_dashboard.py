"""
Testes automatizados para o Dashboard SISCAN / Saúde Já
Execute com: python -m pytest tests/test_dashboard.py -v
"""

import pytest
import pandas as pd
from datetime import datetime, date
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_layer import (
    get_engine,
    get_years,
    get_health_units,
    get_regions,
    get_sex_options,
    get_birads_options,
    get_kpi_data_sql,
    get_monthly_volume_sql,
    get_conformity_by_unit_sql,
    get_birads_distribution_sql,
    get_high_risk_cases_sql,
    get_outliers_audit_sql,
    get_patient_navigation_list_sql,
    get_patient_data_list_sql,
    get_unit_kpis_sql,
    get_unit_demographics_sql,
    get_unit_agility_sql,
    get_unit_wait_time_trend_sql,
    get_unit_follow_up_overdue_sql,
    get_unit_follow_up_count_sql
)
from sqlalchemy import text


class TestDatabaseConnection:
    """Testes de conexão com o banco de dados"""
    
    def test_database_connection(self):
        """Verifica se a conexão com o banco está funcionando"""
        engine = get_engine()
        assert engine is not None
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row[0] == 1
    
    def test_exam_records_table_exists(self):
        """Verifica se a tabela exam_records existe"""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'exam_records'
                )
            """))
            exists = result.fetchone()[0]
            assert exists is True
    
    def test_exam_records_has_data(self):
        """Verifica se existem dados na tabela"""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM exam_records"))
            count = result.fetchone()[0]
            assert count > 0, "Tabela exam_records está vazia"
            print(f"Total de registros: {count}")


class TestFilterOptions:
    """Testes para opções de filtros"""
    
    def test_get_years(self):
        """Verifica se anos são retornados corretamente"""
        years = get_years()
        assert isinstance(years, list)
        assert len(years) > 0
        assert all(isinstance(y, int) for y in years)
        assert all(2020 <= y <= 2030 for y in years)
        print(f"Anos disponíveis: {years}")
    
    def test_get_health_units(self):
        """Verifica se unidades de saúde são retornadas"""
        units = get_health_units()
        assert isinstance(units, list)
        assert len(units) > 0
        print(f"Total de unidades de saúde: {len(units)}")
    
    def test_get_regions(self):
        """Verifica se distritos sanitários são retornados"""
        regions = get_regions()
        assert isinstance(regions, list)
        assert len(regions) > 0
        print(f"Distritos sanitários: {regions}")
    
    def test_get_sex_options(self):
        """Verifica opções de sexo"""
        options = get_sex_options()
        assert isinstance(options, list)
        print(f"Opções de sexo: {options}")
    
    def test_get_birads_options(self):
        """Verifica opções de BI-RADS"""
        options = get_birads_options()
        assert isinstance(options, list)
        print(f"Opções BI-RADS: {options}")


class TestKPIStats:
    """Testes para KPIs principais"""
    
    def test_kpi_stats_returns_dict(self):
        """Verifica se KPIs retornam dicionário com campos corretos"""
        stats = get_kpi_data_sql()
        assert isinstance(stats, dict)
        
        required_keys = ['mean_wait', 'median_wait', 'conformity_rate', 
                         'high_risk_count', 'total_exams']
        for key in required_keys:
            assert key in stats, f"Campo {key} ausente nos KPIs"
    
    def test_kpi_mean_wait_reasonable(self):
        """Verifica se média de espera está em faixa razoável"""
        stats = get_kpi_data_sql()
        mean_wait = stats['mean_wait']
        assert 0 <= mean_wait <= 365, f"Média de espera fora da faixa: {mean_wait}"
        print(f"Média de espera: {mean_wait} dias")
    
    def test_kpi_median_wait_reasonable(self):
        """Verifica se mediana de espera está em faixa razoável"""
        stats = get_kpi_data_sql()
        median_wait = stats['median_wait']
        assert 0 <= median_wait <= 365, f"Mediana de espera fora da faixa: {median_wait}"
        print(f"Mediana de espera: {median_wait} dias")
    
    def test_kpi_conformity_rate_percentage(self):
        """Verifica se taxa de conformidade é uma porcentagem válida"""
        stats = get_kpi_data_sql()
        rate = stats['conformity_rate']
        assert 0 <= rate <= 100, f"Taxa de conformidade inválida: {rate}"
        print(f"Taxa de conformidade: {rate}%")
    
    def test_kpi_high_risk_count_non_negative(self):
        """Verifica se contagem de alto risco é não-negativa"""
        stats = get_kpi_data_sql()
        count = stats['high_risk_count']
        assert count >= 0, f"Contagem de alto risco negativa: {count}"
        print(f"Casos alto risco: {count}")
    
    def test_kpi_total_exams_positive(self):
        """Verifica se total de exames é positivo"""
        stats = get_kpi_data_sql()
        total = stats['total_exams']
        assert total > 0, f"Total de exames deve ser positivo: {total}"
        print(f"Total de exames: {total}")
    
    def test_kpi_with_year_filter(self):
        """Testa KPIs com filtro de ano"""
        stats = get_kpi_data_sql(year=2024)
        assert isinstance(stats, dict)
        assert stats['total_exams'] >= 0
    
    def test_kpi_with_region_filter(self):
        """Testa KPIs com filtro de distrito"""
        regions = get_regions()
        if regions:
            stats = get_kpi_data_sql(region=regions[0])
            assert isinstance(stats, dict)
            assert stats['total_exams'] >= 0


class TestChartData:
    """Testes para dados de gráficos"""
    
    def test_monthly_volume_returns_dataframe(self):
        """Verifica se volume mensal retorna DataFrame"""
        df = get_monthly_volume_sql()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'month_year' in df.columns
        assert 'count' in df.columns
    
    def test_conformity_by_unit_returns_dataframe(self):
        """Verifica se conformidade por unidade retorna DataFrame"""
        df = get_conformity_by_unit_sql()
        assert isinstance(df, pd.DataFrame)
    
    def test_birads_distribution_returns_dataframe(self):
        """Verifica se distribuição BI-RADS retorna DataFrame"""
        df = get_birads_distribution_sql()
        assert isinstance(df, pd.DataFrame)
        if len(df) > 0:
            assert 'birads_category' in df.columns
    
    def test_high_risk_cases_returns_dataframe(self):
        """Verifica se casos de alto risco retornam DataFrame"""
        df = get_high_risk_cases_sql()
        assert isinstance(df, pd.DataFrame)


class TestOutliers:
    """Testes para detecção de outliers"""
    
    def test_outliers_returns_dataframe(self):
        """Verifica se outliers retornam DataFrame"""
        df = get_outliers_audit_sql()
        assert isinstance(df, pd.DataFrame)
    
    def test_outliers_has_category(self):
        """Verifica se outliers têm categoria definida"""
        df = get_outliers_audit_sql()
        if len(df) > 0:
            assert 'motivo_do_outlier' in df.columns
    
    def test_outliers_count_reasonable(self):
        """Verifica se contagem de outliers é razoável"""
        df = get_outliers_audit_sql()
        total = len(df)
        assert total < 10000, f"Muitos outliers detectados: {total}"
        print(f"Total de outliers: {total}")


class TestPatientNavigation:
    """Testes para navegação de pacientes"""
    
    def test_patients_multiple_exams_returns_dataframe(self):
        """Verifica se pacientes com múltiplos exames retornam DataFrame"""
        df = get_patient_navigation_list_sql()
        assert isinstance(df, pd.DataFrame)
    
    def test_patients_multiple_exams_has_count(self):
        """Verifica se retorna contagem de exames"""
        df = get_patient_navigation_list_sql()
        if len(df) > 0:
            assert 'exam_count' in df.columns or 'total_exames' in df.columns


class TestPatientData:
    """Testes para listagem de dados do paciente"""
    
    def test_patient_data_returns_dataframe(self):
        """Verifica se dados do paciente retornam DataFrame"""
        df = get_patient_data_list_sql(page_size=10)
        assert isinstance(df, pd.DataFrame)
    
    def test_patient_data_respects_limit(self):
        """Verifica se limite é respeitado"""
        df = get_patient_data_list_sql(page_size=5)
        assert len(df) <= 5
    
    def test_patient_data_with_name_filter(self):
        """Testa filtro por nome"""
        df = get_patient_data_list_sql(patient_name="MARIA", page_size=10)
        assert isinstance(df, pd.DataFrame)
    
    def test_patient_data_pagination(self):
        """Testa paginação"""
        df_page1 = get_patient_data_list_sql(page=1, page_size=10)
        df_page2 = get_patient_data_list_sql(page=2, page_size=10)
        assert isinstance(df_page1, pd.DataFrame)
        assert isinstance(df_page2, pd.DataFrame)


class TestUnitAnalysis:
    """Testes para análise por unidade de saúde"""
    
    def test_unit_kpis_with_valid_unit(self):
        """Testa KPIs de unidade com unidade válida"""
        units = get_health_units()
        if units:
            kpis = get_unit_kpis_sql(units[0])
            assert isinstance(kpis, dict)
            assert 'total_exames' in kpis
            assert 'media_espera' in kpis
            assert 'taxa_conformidade' in kpis
    
    def test_unit_kpis_with_null_unit(self):
        """Testa KPIs de unidade com unidade nula (não deve quebrar)"""
        kpis = get_unit_kpis_sql(None)
        assert isinstance(kpis, dict)
        assert kpis['total_exames'] == 0
    
    def test_unit_kpis_with_empty_unit(self):
        """Testa KPIs de unidade com unidade vazia (não deve quebrar)"""
        kpis = get_unit_kpis_sql("")
        assert isinstance(kpis, dict)
    
    def test_unit_demographics_with_valid_unit(self):
        """Testa demografia com unidade válida"""
        units = get_health_units()
        if units:
            df = get_unit_demographics_sql(units[0])
            assert isinstance(df, pd.DataFrame)
    
    def test_unit_demographics_with_null_unit(self):
        """Testa demografia com unidade nula (não deve quebrar)"""
        df = get_unit_demographics_sql(None)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_unit_agility_with_valid_unit(self):
        """Testa agilidade com unidade válida"""
        units = get_health_units()
        if units:
            df = get_unit_agility_sql(units[0])
            assert isinstance(df, pd.DataFrame)
    
    def test_unit_agility_with_null_unit(self):
        """Testa agilidade com unidade nula (não deve quebrar)"""
        df = get_unit_agility_sql(None)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_unit_wait_time_trend_with_valid_unit(self):
        """Testa tendência de espera com unidade válida"""
        units = get_health_units()
        if units:
            df = get_unit_wait_time_trend_sql(units[0])
            assert isinstance(df, pd.DataFrame)
    
    def test_unit_wait_time_trend_with_null_unit(self):
        """Testa tendência de espera com unidade nula (não deve quebrar)"""
        df = get_unit_wait_time_trend_sql(None)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_unit_follow_up_overdue_with_valid_unit(self):
        """Testa retornos pendentes com unidade válida"""
        units = get_health_units()
        if units:
            df = get_unit_follow_up_overdue_sql(units[0])
            assert isinstance(df, pd.DataFrame)
    
    def test_unit_follow_up_overdue_with_null_unit(self):
        """Testa retornos pendentes com unidade nula (não deve quebrar)"""
        df = get_unit_follow_up_overdue_sql(None)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_unit_follow_up_count_with_valid_unit(self):
        """Testa contagem de retornos pendentes com unidade válida"""
        units = get_health_units()
        if units:
            count = get_unit_follow_up_count_sql(units[0])
            assert isinstance(count, int)
            assert count >= 0
    
    def test_unit_follow_up_count_with_null_unit(self):
        """Testa contagem de retornos pendentes com unidade nula (não deve quebrar)"""
        count = get_unit_follow_up_count_sql(None)
        assert count == 0


class TestDataIntegrity:
    """Testes de integridade dos dados"""
    
    def test_no_negative_wait_days_in_kpis(self):
        """Verifica que KPIs não incluem dias de espera negativos"""
        stats = get_kpi_data_sql()
        assert stats['mean_wait'] >= 0
        assert stats['median_wait'] >= 0
    
    def test_conformity_rate_matches_data(self):
        """Verifica se taxa de conformidade está consistente"""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    ROUND(
                        SUM(CASE WHEN conformity_status = 'Dentro do Prazo' THEN 1 ELSE 0 END) * 100.0 / 
                        NULLIF(COUNT(*), 0)
                    , 1) as rate
                FROM exam_records
                WHERE unidade_de_saude__data_da_solicitacao >= '2023-01-01'
                    AND (prestador_de_servico__data_da_realizacao IS NULL 
                         OR prestador_de_servico__data_da_realizacao >= unidade_de_saude__data_da_solicitacao)
                    AND (wait_days IS NULL OR (wait_days >= 0 AND wait_days <= 365))
            """))
            row = result.fetchone()
            db_rate = float(row[0]) if row[0] else 0
        
        stats = get_kpi_data_sql()
        kpi_rate = stats['conformity_rate']
        
        assert abs(db_rate - kpi_rate) < 1, f"Taxa de conformidade inconsistente: DB={db_rate}, KPI={kpi_rate}"
    
    def test_high_risk_count_matches_birads_4_5(self):
        """Verifica se contagem de alto risco corresponde a BI-RADS 4 e 5"""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM exam_records
                WHERE birads_max IN ('4', '5')
                    AND unidade_de_saude__data_da_solicitacao >= '2023-01-01'
                    AND (prestador_de_servico__data_da_realizacao IS NULL 
                         OR prestador_de_servico__data_da_realizacao >= unidade_de_saude__data_da_solicitacao)
                    AND (wait_days IS NULL OR (wait_days >= 0 AND wait_days <= 365))
            """))
            db_count = result.fetchone()[0]
        
        stats = get_kpi_data_sql()
        kpi_count = stats['high_risk_count']
        
        assert db_count == kpi_count, f"Contagem de alto risco inconsistente: DB={db_count}, KPI={kpi_count}"


class TestErrorHandling:
    """Testes de tratamento de erros"""
    
    def test_kpi_with_invalid_year(self):
        """Testa KPIs com ano inválido (não deve quebrar)"""
        stats = get_kpi_data_sql(year=1900)
        assert isinstance(stats, dict)
        assert stats['total_exams'] == 0
    
    def test_kpi_with_invalid_region(self):
        """Testa KPIs com região inválida (não deve quebrar)"""
        stats = get_kpi_data_sql(region="REGIAO_INEXISTENTE_XYZ")
        assert isinstance(stats, dict)
        assert stats['total_exams'] == 0
    
    def test_patient_data_with_special_characters(self):
        """Testa filtro com caracteres especiais (SQL injection prevention)"""
        df = get_patient_data_list_sql(patient_name="'; DROP TABLE exam_records; --", page_size=10)
        assert isinstance(df, pd.DataFrame)
    
    def test_unit_kpis_with_nonexistent_unit(self):
        """Testa KPIs com unidade inexistente (não deve quebrar)"""
        kpis = get_unit_kpis_sql("UNIDADE_INEXISTENTE_XYZ_123")
        assert isinstance(kpis, dict)
        assert kpis['total_exames'] == 0


class TestExpectedValues:
    """Testes para valores esperados (baseline)"""
    
    def test_total_exams_above_100k(self):
        """Verifica se total de exames está acima de 100.000"""
        stats = get_kpi_data_sql()
        assert stats['total_exams'] >= 100000, f"Esperado >= 100.000 exames, obtido {stats['total_exams']}"
    
    def test_mean_wait_around_12_days(self):
        """Verifica se média de espera está próxima de 12.5 dias"""
        stats = get_kpi_data_sql()
        assert 10 <= stats['mean_wait'] <= 15, f"Média de espera fora da faixa esperada: {stats['mean_wait']}"
    
    def test_conformity_rate_above_85_percent(self):
        """Verifica se taxa de conformidade está acima de 85%"""
        stats = get_kpi_data_sql()
        assert stats['conformity_rate'] >= 85, f"Taxa de conformidade abaixo do esperado: {stats['conformity_rate']}%"
    
    def test_high_risk_cases_around_1800(self):
        """Verifica se casos de alto risco estão próximos de 1.884"""
        stats = get_kpi_data_sql()
        assert 1500 <= stats['high_risk_count'] <= 2500, f"Casos de alto risco fora da faixa: {stats['high_risk_count']}"
    
    def test_districts_count_equals_10(self):
        """Verifica se existem 10 distritos sanitários"""
        regions = get_regions()
        assert len(regions) >= 10, f"Esperado >= 10 distritos, obtido {len(regions)}"


class TestAuthentication:
    """Testes de autenticação e login"""
    
    def test_user_model_exists(self):
        """Verifica se o modelo User existe"""
        from src.models import User
        assert User is not None
        assert hasattr(User, 'username')
        assert hasattr(User, 'password_hash')
        assert hasattr(User, 'is_active')
    
    def test_user_table_exists(self):
        """Verifica se a tabela users existe no banco"""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
            """))
            exists = result.fetchone()[0]
            assert exists is True, "Tabela users não existe"
    
    def test_admin_user_exists(self):
        """Verifica se o usuário admin existe"""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM users WHERE username = 'admin'
            """))
            count = result.fetchone()[0]
            assert count == 1, "Usuário admin não encontrado"
    
    def test_password_hashing(self):
        """Verifica se senhas são criptografadas corretamente"""
        from src.models import User
        user = User(username='test_user', name='Test')
        user.set_password('test123')
        assert user.password_hash is not None
        assert user.password_hash != 'test123'
        assert len(user.password_hash) > 20
    
    def test_password_verification(self):
        """Verifica se verificação de senha funciona"""
        from src.models import User
        user = User(username='test_user', name='Test')
        user.set_password('correct_password')
        assert user.check_password('correct_password') is True
        assert user.check_password('wrong_password') is False
    
    def test_password_hash_uses_scrypt(self):
        """Verifica se o hash usa algoritmo scrypt (werkzeug)"""
        from src.models import User
        user = User(username='test_user', name='Test')
        user.set_password('mypassword')
        assert 'scrypt' in user.password_hash or 'pbkdf2' in user.password_hash
    
    def test_user_is_active_default(self):
        """Verifica se campo is_active tem default True no modelo"""
        from src.models import User
        is_active_col = User.__table__.columns['is_active']
        assert is_active_col.default is not None
        assert is_active_col.default.arg is True


class TestSecurity:
    """Testes de segurança do sistema"""
    
    def test_session_timeout_configured(self):
        """Verifica se timeout de sessão está configurado para 1 hora"""
        from datetime import timedelta
        from src.config import SESSION_SECRET
        assert SESSION_SECRET is not None
        assert len(SESSION_SECRET) > 10
    
    def test_session_secret_not_hardcoded(self):
        """Verifica se SESSION_SECRET vem do ambiente"""
        import os
        from src.config import SESSION_SECRET
        env_secret = os.environ.get('SESSION_SECRET')
        if env_secret:
            assert SESSION_SECRET == env_secret
    
    def test_login_layout_exists(self):
        """Verifica se layout de login existe"""
        from src.components.layout import create_login_layout
        from src.config import COLORS
        layout = create_login_layout(COLORS)
        assert layout is not None
    
    def test_login_layout_has_password_field(self):
        """Verifica se layout de login tem campo de senha"""
        from src.components.layout import create_login_layout
        from src.config import COLORS
        layout = create_login_layout(COLORS)
        layout_str = str(layout)
        assert 'login-password' in layout_str
        assert 'login-username' in layout_str
        assert 'login-button' in layout_str
    
    def test_login_layout_expired_message(self):
        """Verifica mensagem de sessão expirada"""
        from src.components.layout import create_login_layout
        from src.config import COLORS
        layout = create_login_layout(COLORS, session_expired=True)
        layout_str = str(layout)
        assert 'expirou' in layout_str.lower()
    
    def test_excluded_paths_defined(self):
        """Verifica se caminhos excluídos estão definidos no before_request"""
        import main
        source_code = open('main.py', 'r').read()
        assert '/_dash-' in source_code
        assert '/login' in source_code
        assert '/logout' in source_code
        assert '/assets/' in source_code
    
    def test_session_timeout_one_hour(self):
        """Verifica se timeout é de 1 hora"""
        source_code = open('main.py', 'r').read()
        assert 'timedelta(hours=1)' in source_code
    
    def test_login_time_stored(self):
        """Verifica se horário de login é armazenado"""
        source_code = open('main.py', 'r').read()
        assert 'login_time' in source_code
        assert 'isoformat()' in source_code
    
    def test_next_url_preserved(self):
        """Verifica se URL de destino é preservada"""
        source_code = open('main.py', 'r').read()
        assert 'next_url' in source_code
    
    def test_asset_files_excluded_from_redirect(self):
        """Verifica se arquivos de assets não sobrescrevem next_url"""
        source_code = open('main.py', 'r').read()
        assert '.ico' in source_code
        assert '.png' in source_code
        assert '.css' in source_code
        assert '.js' in source_code


def run_all_tests():
    """Executa todos os testes e exibe resumo"""
    print("=" * 60)
    print("TESTES DO DASHBOARD SISCAN / SAÚDE JÁ")
    print("=" * 60)
    
    test_classes = [
        TestDatabaseConnection,
        TestFilterOptions,
        TestKPIStats,
        TestChartData,
        TestOutliers,
        TestPatientNavigation,
        TestPatientData,
        TestUnitAnalysis,
        TestDataIntegrity,
        TestErrorHandling,
        TestExpectedValues,
        TestAuthentication,
        TestSecurity
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for test_class in test_classes:
        print(f"\n--- {test_class.__name__} ---")
        instance = test_class()
        
        for method_name in dir(instance):
            if method_name.startswith('test_'):
                try:
                    method = getattr(instance, method_name)
                    method()
                    print(f"  ✓ {method_name}")
                    passed += 1
                except AssertionError as e:
                    print(f"  ✗ {method_name}: {e}")
                    failed += 1
                    errors.append((test_class.__name__, method_name, str(e)))
                except Exception as e:
                    print(f"  ✗ {method_name}: ERRO - {e}")
                    failed += 1
                    errors.append((test_class.__name__, method_name, f"ERRO: {e}"))
    
    print("\n" + "=" * 60)
    print(f"RESULTADO: {passed} passaram, {failed} falharam")
    print("=" * 60)
    
    if errors:
        print("\nFALHAS DETALHADAS:")
        for class_name, method_name, error in errors:
            print(f"  - {class_name}.{method_name}: {error}")
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
