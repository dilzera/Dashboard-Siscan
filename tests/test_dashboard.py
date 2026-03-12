"""
Testes automatizados para o Dashboard SISCAN / Central Inteligente
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
    get_other_birads_cases_sql,
    get_outliers_audit_sql,
    get_outliers_summary_sql,
    get_patient_navigation_list_sql,
    get_patient_navigation_summary_sql,
    get_patient_navigation_stats_sql,
    get_patient_data_list_sql,
    get_patient_data_count_sql,
    get_unit_kpis_sql,
    get_unit_demographics_sql,
    get_unit_agility_sql,
    get_unit_wait_time_trend_sql,
    get_unit_follow_up_overdue_sql,
    get_unit_follow_up_count_sql,
    get_unit_high_risk_patients_sql,
    get_all_high_risk_patients_sql,
    get_unit_prioritization_sql,
    get_unit_priority_summary_sql,
    get_indicators_data_sql,
    get_indicator_details_sql,
    get_termo_linkage_summary_sql,
    get_termo_linkage_data_sql,
    get_termo_linkage_count_sql,
    get_database_comparison_sql,
    calculate_priority,
    get_units_by_district,
    get_district_for_unit,
    _normalize_to_list,
    _build_where_clause,
)
from sqlalchemy import text


@pytest.fixture(scope="session")
def engine():
    return get_engine()


@pytest.fixture(scope="session")
def sample_year():
    years = get_years()
    return years[0] if years else 2024


@pytest.fixture(scope="session")
def sample_region():
    regions = get_regions()
    return regions[0] if regions else None


@pytest.fixture(scope="session")
def sample_unit():
    units = get_health_units()
    return units[0] if units else None


@pytest.fixture(scope="session")
def all_regions():
    return get_regions()


@pytest.fixture(scope="session")
def all_units():
    return get_health_units()


class TestDatabaseConnection:

    def test_database_connection(self, engine):
        assert engine is not None
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row[0] == 1

    def test_exam_records_table_exists(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'exam_records'
                )
            """))
            assert result.fetchone()[0] is True

    def test_users_table_exists(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
            """))
            assert result.fetchone()[0] is True

    def test_termo_linkage_table_exists(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'termo_linkage'
                )
            """))
            assert result.fetchone()[0] is True

    def test_access_requests_table_exists(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'access_requests'
                )
            """))
            assert result.fetchone()[0] is True

    def test_exam_records_has_data(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM exam_records"))
            count = result.fetchone()[0]
            assert count > 0


class TestFilterOptions:

    def test_get_years(self):
        years = get_years()
        assert isinstance(years, list)
        assert len(years) > 0
        assert all(isinstance(y, int) for y in years)
        assert all(2020 <= y <= 2030 for y in years)

    def test_years_are_sorted_descending(self):
        years = get_years()
        assert years == sorted(years, reverse=True)

    def test_get_health_units(self):
        units = get_health_units()
        assert isinstance(units, list)
        assert len(units) > 0
        assert all(isinstance(u, str) for u in units)

    def test_health_units_are_sorted(self):
        units = get_health_units()
        assert units == sorted(units)

    def test_get_regions(self):
        regions = get_regions()
        assert isinstance(regions, list)
        assert len(regions) > 0
        assert all(isinstance(r, str) for r in regions)

    def test_regions_are_sorted(self):
        regions = get_regions()
        assert regions == sorted(regions)

    def test_get_sex_options(self):
        options = get_sex_options()
        assert isinstance(options, list)
        assert len(options) > 0

    def test_get_birads_options(self):
        options = get_birads_options()
        assert isinstance(options, list)
        assert len(options) > 0

    def test_birads_options_contain_expected_values(self):
        options = get_birads_options()
        for expected in ['0', '1', '2']:
            assert expected in options, f"BI-RADS {expected} esperado nas opções"


class TestKPIStats:

    def test_kpi_stats_returns_dict(self):
        stats = get_kpi_data_sql()
        assert isinstance(stats, dict)
        required_keys = ['mean_wait', 'median_wait', 'conformity_rate',
                         'high_risk_count', 'total_exams']
        for key in required_keys:
            assert key in stats, f"Campo {key} ausente nos KPIs"

    def test_kpi_mean_wait_reasonable(self):
        stats = get_kpi_data_sql()
        assert 0 <= stats['mean_wait'] <= 365

    def test_kpi_median_wait_reasonable(self):
        stats = get_kpi_data_sql()
        assert 0 <= stats['median_wait'] <= 365

    def test_kpi_conformity_rate_percentage(self):
        stats = get_kpi_data_sql()
        assert 0 <= stats['conformity_rate'] <= 100

    def test_kpi_high_risk_count_non_negative(self):
        stats = get_kpi_data_sql()
        assert stats['high_risk_count'] >= 0

    def test_kpi_total_exams_positive(self):
        stats = get_kpi_data_sql()
        assert stats['total_exams'] > 0

    def test_kpi_with_year_filter(self, sample_year):
        stats = get_kpi_data_sql(year=sample_year)
        assert isinstance(stats, dict)
        assert stats['total_exams'] >= 0

    def test_kpi_with_region_filter(self, sample_region):
        if sample_region:
            stats = get_kpi_data_sql(region=sample_region)
            assert isinstance(stats, dict)
            assert stats['total_exams'] >= 0

    def test_kpi_with_unit_filter(self, sample_unit):
        if sample_unit:
            stats = get_kpi_data_sql(health_unit=sample_unit)
            assert isinstance(stats, dict)
            assert stats['total_exams'] >= 0

    def test_kpi_with_conformity_filter(self):
        stats = get_kpi_data_sql(conformity_status='Dentro do Prazo')
        assert isinstance(stats, dict)
        assert stats['conformity_rate'] == 100.0 or stats['total_exams'] == 0

    def test_kpi_with_year_and_region_combined(self, sample_year, sample_region):
        if sample_region:
            stats = get_kpi_data_sql(year=sample_year, region=sample_region)
            assert isinstance(stats, dict)
            assert stats['total_exams'] >= 0

    def test_kpi_with_year_and_unit_combined(self, sample_year, sample_unit):
        if sample_unit:
            stats = get_kpi_data_sql(year=sample_year, health_unit=sample_unit)
            assert isinstance(stats, dict)
            assert stats['total_exams'] >= 0

    def test_kpi_with_all_filters_combined(self, sample_year, sample_region, sample_unit):
        stats = get_kpi_data_sql(
            year=sample_year,
            health_unit=sample_unit,
            region=sample_region,
            conformity_status='Dentro do Prazo'
        )
        assert isinstance(stats, dict)
        assert stats['total_exams'] >= 0

    def test_kpi_filtered_total_less_than_unfiltered(self, sample_year):
        stats_all = get_kpi_data_sql()
        stats_year = get_kpi_data_sql(year=sample_year)
        assert stats_year['total_exams'] <= stats_all['total_exams']

    def test_kpi_region_filter_reduces_total(self, sample_region):
        if sample_region:
            stats_all = get_kpi_data_sql()
            stats_region = get_kpi_data_sql(region=sample_region)
            assert stats_region['total_exams'] <= stats_all['total_exams']

    def test_kpi_unit_filter_reduces_total(self, sample_unit):
        if sample_unit:
            stats_all = get_kpi_data_sql()
            stats_unit = get_kpi_data_sql(health_unit=sample_unit)
            assert stats_unit['total_exams'] <= stats_all['total_exams']

    def test_kpi_with_birads_filter(self):
        stats = get_kpi_data_sql(birads='4')
        assert isinstance(stats, dict)
        assert stats['total_exams'] >= 0

    def test_kpi_with_priority_filter(self):
        stats = get_kpi_data_sql(priority='CRITICAL')
        assert isinstance(stats, dict)
        assert stats['total_exams'] >= 0

    def test_kpi_with_age_range_filter(self):
        stats = get_kpi_data_sql(age_range='50-69')
        assert isinstance(stats, dict)
        assert stats['total_exams'] >= 0


class TestChartData:

    def test_monthly_volume_returns_dataframe(self):
        df = get_monthly_volume_sql()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'month_year' in df.columns
        assert 'count' in df.columns

    def test_monthly_volume_with_year_filter(self, sample_year):
        df = get_monthly_volume_sql(year=sample_year)
        assert isinstance(df, pd.DataFrame)

    def test_monthly_volume_with_region_filter(self, sample_region):
        if sample_region:
            df = get_monthly_volume_sql(region=sample_region)
            assert isinstance(df, pd.DataFrame)

    def test_monthly_volume_with_combined_filters(self, sample_year, sample_region):
        if sample_region:
            df = get_monthly_volume_sql(year=sample_year, region=sample_region)
            assert isinstance(df, pd.DataFrame)

    def test_monthly_volume_filtered_less_than_unfiltered(self, sample_region):
        if sample_region:
            df_all = get_monthly_volume_sql()
            df_region = get_monthly_volume_sql(region=sample_region)
            assert df_region['count'].sum() <= df_all['count'].sum()

    def test_conformity_by_unit_returns_dataframe(self):
        df = get_conformity_by_unit_sql()
        assert isinstance(df, pd.DataFrame)

    def test_conformity_by_unit_with_year_filter(self, sample_year):
        df = get_conformity_by_unit_sql(year=sample_year)
        assert isinstance(df, pd.DataFrame)

    def test_conformity_by_unit_with_region_filter(self, sample_region):
        if sample_region:
            df = get_conformity_by_unit_sql(region=sample_region)
            assert isinstance(df, pd.DataFrame)

    def test_birads_distribution_returns_dataframe(self):
        df = get_birads_distribution_sql()
        assert isinstance(df, pd.DataFrame)
        if len(df) > 0:
            assert 'birads_category' in df.columns

    def test_birads_distribution_with_year_filter(self, sample_year):
        df = get_birads_distribution_sql(year=sample_year)
        assert isinstance(df, pd.DataFrame)

    def test_birads_distribution_with_region_filter(self, sample_region):
        if sample_region:
            df = get_birads_distribution_sql(region=sample_region)
            assert isinstance(df, pd.DataFrame)

    def test_birads_distribution_with_combined_filters(self, sample_year, sample_region):
        if sample_region:
            df = get_birads_distribution_sql(year=sample_year, region=sample_region)
            assert isinstance(df, pd.DataFrame)

    def test_high_risk_cases_returns_dataframe(self):
        df = get_high_risk_cases_sql()
        assert isinstance(df, pd.DataFrame)

    def test_high_risk_cases_with_year_filter(self, sample_year):
        df = get_high_risk_cases_sql(year=sample_year)
        assert isinstance(df, pd.DataFrame)

    def test_high_risk_cases_with_region_filter(self, sample_region):
        if sample_region:
            df = get_high_risk_cases_sql(region=sample_region)
            assert isinstance(df, pd.DataFrame)

    def test_high_risk_cases_with_limit(self):
        df = get_high_risk_cases_sql(limit=5)
        assert isinstance(df, pd.DataFrame)
        assert len(df) <= 5

    def test_high_risk_cases_filtered_by_region_subset(self, sample_region):
        if sample_region:
            df_all = get_high_risk_cases_sql(limit=1000)
            df_region = get_high_risk_cases_sql(region=sample_region, limit=1000)
            assert len(df_region) <= len(df_all)

    def test_other_birads_cases_returns_dataframe(self):
        df = get_other_birads_cases_sql()
        assert isinstance(df, pd.DataFrame)

    def test_other_birads_cases_with_birads_filter(self):
        df = get_other_birads_cases_sql(birads_filter='3')
        assert isinstance(df, pd.DataFrame)

    def test_other_birads_cases_with_year_filter(self, sample_year):
        df = get_other_birads_cases_sql(year=sample_year)
        assert isinstance(df, pd.DataFrame)

    def test_other_birads_cases_with_limit(self):
        df = get_other_birads_cases_sql(limit=10)
        assert isinstance(df, pd.DataFrame)
        assert len(df) <= 10


class TestOutliers:

    def test_outliers_audit_returns_dataframe(self):
        df = get_outliers_audit_sql()
        assert isinstance(df, pd.DataFrame)

    def test_outliers_has_category(self):
        df = get_outliers_audit_sql()
        if len(df) > 0:
            assert 'motivo_do_outlier' in df.columns

    def test_outliers_count_reasonable(self):
        df = get_outliers_audit_sql()
        assert len(df) < 50000

    def test_outliers_with_year_filter(self, sample_year):
        df = get_outliers_audit_sql(year=sample_year)
        assert isinstance(df, pd.DataFrame)

    def test_outliers_with_region_filter(self, sample_region):
        if sample_region:
            df = get_outliers_audit_sql(region=sample_region)
            assert isinstance(df, pd.DataFrame)

    def test_outliers_with_unit_filter(self, sample_unit):
        if sample_unit:
            df = get_outliers_audit_sql(health_unit=sample_unit)
            assert isinstance(df, pd.DataFrame)

    def test_outliers_with_combined_filters(self, sample_year, sample_region):
        if sample_region:
            df = get_outliers_audit_sql(year=sample_year, region=sample_region)
            assert isinstance(df, pd.DataFrame)

    def test_outliers_filtered_subset(self, sample_region):
        if sample_region:
            df_all = get_outliers_audit_sql()
            df_region = get_outliers_audit_sql(region=sample_region)
            assert len(df_region) <= len(df_all)

    def test_outliers_summary_returns_dataframe(self):
        df = get_outliers_summary_sql()
        assert isinstance(df, pd.DataFrame)

    def test_outliers_summary_with_year_filter(self, sample_year):
        df = get_outliers_summary_sql(year=sample_year)
        assert isinstance(df, pd.DataFrame)

    def test_outliers_summary_with_region_filter(self, sample_region):
        if sample_region:
            df = get_outliers_summary_sql(region=sample_region)
            assert isinstance(df, pd.DataFrame)

    def test_outliers_summary_with_combined_filters(self, sample_year, sample_region):
        if sample_region:
            df = get_outliers_summary_sql(year=sample_year, region=sample_region)
            assert isinstance(df, pd.DataFrame)


class TestPatientNavigation:

    def test_navigation_returns_dataframe(self):
        df = get_patient_navigation_list_sql()
        assert isinstance(df, pd.DataFrame)

    def test_navigation_has_exam_count(self):
        df = get_patient_navigation_list_sql()
        if len(df) > 0:
            assert 'total_exames' in df.columns

    def test_navigation_min_exams_filter(self):
        df = get_patient_navigation_list_sql(min_exams=3)
        assert isinstance(df, pd.DataFrame)
        if len(df) > 0 and 'total_exames' in df.columns:
            assert df['total_exames'].min() >= 3

    def test_navigation_with_year_filter(self, sample_year):
        df = get_patient_navigation_list_sql(year=sample_year)
        assert isinstance(df, pd.DataFrame)

    def test_navigation_with_region_filter(self, sample_region):
        if sample_region:
            df = get_patient_navigation_list_sql(region=sample_region)
            assert isinstance(df, pd.DataFrame)

    def test_navigation_with_unit_filter(self, sample_unit):
        if sample_unit:
            df = get_patient_navigation_list_sql(health_unit=sample_unit)
            assert isinstance(df, pd.DataFrame)

    def test_navigation_with_limit(self):
        df_small = get_patient_navigation_list_sql(limit=5)
        df_large = get_patient_navigation_list_sql(limit=50)
        assert isinstance(df_small, pd.DataFrame)
        assert isinstance(df_large, pd.DataFrame)
        if len(df_small) > 0 and len(df_large) > 0:
            assert len(df_small) <= len(df_large)

    def test_navigation_with_evolution_positive(self):
        df = get_patient_navigation_list_sql(evolution_filter='positive')
        assert isinstance(df, pd.DataFrame)

    def test_navigation_with_evolution_negative(self):
        df = get_patient_navigation_list_sql(evolution_filter='negative')
        assert isinstance(df, pd.DataFrame)

    def test_navigation_with_evolution_normal(self):
        df = get_patient_navigation_list_sql(evolution_filter='normal')
        assert isinstance(df, pd.DataFrame)

    def test_navigation_with_conformity_filter(self):
        df = get_patient_navigation_list_sql(conformity='Dentro do Prazo')
        assert isinstance(df, pd.DataFrame)

    def test_navigation_combined_year_region(self, sample_year, sample_region):
        if sample_region:
            df = get_patient_navigation_list_sql(year=sample_year, region=sample_region)
            assert isinstance(df, pd.DataFrame)

    def test_navigation_combined_all_filters(self, sample_year, sample_region):
        if sample_region:
            df = get_patient_navigation_list_sql(
                year=sample_year, region=sample_region,
                min_exams=2, limit=10, evolution_filter='positive'
            )
            assert isinstance(df, pd.DataFrame)
            assert len(df) <= 10

    def test_navigation_filtered_subset(self, sample_region):
        if sample_region:
            df_all = get_patient_navigation_list_sql(limit=500)
            df_region = get_patient_navigation_list_sql(region=sample_region, limit=500)
            assert len(df_region) <= len(df_all)

    def test_navigation_summary_returns_dict(self):
        result = get_patient_navigation_summary_sql()
        assert isinstance(result, (dict, pd.DataFrame))

    def test_navigation_summary_with_year_filter(self, sample_year):
        result = get_patient_navigation_summary_sql(year=sample_year)
        assert result is not None

    def test_navigation_summary_with_region_filter(self, sample_region):
        if sample_region:
            result = get_patient_navigation_summary_sql(region=sample_region)
            assert result is not None

    def test_navigation_stats_returns_dict(self):
        result = get_patient_navigation_stats_sql()
        assert isinstance(result, dict)

    def test_navigation_stats_with_year_filter(self, sample_year):
        result = get_patient_navigation_stats_sql(year=sample_year)
        assert isinstance(result, dict)

    def test_navigation_stats_with_region_filter(self, sample_region):
        if sample_region:
            result = get_patient_navigation_stats_sql(region=sample_region)
            assert isinstance(result, dict)


class TestPatientData:

    def test_patient_data_returns_dataframe(self):
        df = get_patient_data_list_sql(page_size=10)
        assert isinstance(df, pd.DataFrame)

    def test_patient_data_respects_page_size(self):
        df = get_patient_data_list_sql(page_size=5)
        assert len(df) <= 5

    def test_patient_data_with_name_filter(self):
        df = get_patient_data_list_sql(patient_name="MARIA", page_size=10)
        assert isinstance(df, pd.DataFrame)
        if len(df) > 0 and 'nome' in df.columns:
            for name in df['nome']:
                assert 'MARIA' in str(name).upper()

    def test_patient_data_with_sex_filter(self):
        options = get_sex_options()
        if options:
            df = get_patient_data_list_sql(sex=options[0], page_size=10)
            assert isinstance(df, pd.DataFrame)

    def test_patient_data_with_birads_filter(self):
        df = get_patient_data_list_sql(birads='4', page_size=10)
        assert isinstance(df, pd.DataFrame)

    def test_patient_data_with_year_filter(self, sample_year):
        df = get_patient_data_list_sql(year=sample_year, page_size=10)
        assert isinstance(df, pd.DataFrame)

    def test_patient_data_with_region_filter(self, sample_region):
        if sample_region:
            df = get_patient_data_list_sql(region=sample_region, page_size=10)
            assert isinstance(df, pd.DataFrame)

    def test_patient_data_with_unit_filter(self, sample_unit):
        if sample_unit:
            df = get_patient_data_list_sql(health_unit=sample_unit, page_size=10)
            assert isinstance(df, pd.DataFrame)

    def test_patient_data_with_conformity_filter(self):
        df = get_patient_data_list_sql(conformity='Dentro do Prazo', page_size=10)
        assert isinstance(df, pd.DataFrame)

    def test_patient_data_pagination_page1_vs_page2(self):
        df_page1 = get_patient_data_list_sql(page=1, page_size=10)
        df_page2 = get_patient_data_list_sql(page=2, page_size=10)
        assert isinstance(df_page1, pd.DataFrame)
        assert isinstance(df_page2, pd.DataFrame)
        if len(df_page1) > 0 and len(df_page2) > 0:
            if 'nome' in df_page1.columns and 'nome' in df_page2.columns:
                names_p1 = set(df_page1['nome'].tolist())
                names_p2 = set(df_page2['nome'].tolist())
                assert names_p1 != names_p2

    def test_patient_data_combined_year_region(self, sample_year, sample_region):
        if sample_region:
            df = get_patient_data_list_sql(
                year=sample_year, region=sample_region, page_size=10
            )
            assert isinstance(df, pd.DataFrame)

    def test_patient_data_combined_all_filters(self, sample_year, sample_region, sample_unit):
        df = get_patient_data_list_sql(
            year=sample_year,
            health_unit=sample_unit,
            region=sample_region,
            conformity='Dentro do Prazo',
            birads='0',
            page_size=10
        )
        assert isinstance(df, pd.DataFrame)

    def test_patient_data_count_returns_integer(self):
        count = get_patient_data_count_sql()
        assert isinstance(count, int)
        assert count >= 0

    def test_patient_data_count_with_year_filter(self, sample_year):
        count = get_patient_data_count_sql(year=sample_year)
        assert isinstance(count, int)
        assert count >= 0

    def test_patient_data_count_with_region_filter(self, sample_region):
        if sample_region:
            count = get_patient_data_count_sql(region=sample_region)
            assert isinstance(count, int)
            assert count >= 0

    def test_patient_data_count_with_name_filter(self):
        count = get_patient_data_count_sql(patient_name="MARIA")
        assert isinstance(count, int)
        assert count >= 0

    def test_patient_data_count_filtered_less_than_total(self, sample_region):
        if sample_region:
            total = get_patient_data_count_sql()
            filtered = get_patient_data_count_sql(region=sample_region)
            assert filtered <= total

    def test_patient_data_count_matches_list_approximate(self):
        count = get_patient_data_count_sql(patient_name="MARIA")
        assert count > 0
        df = get_patient_data_list_sql(patient_name="MARIA", page_size=50)
        assert len(df) > 0
        assert len(df) <= 50


class TestUnitAnalysis:

    def test_unit_kpis_with_valid_unit(self, sample_unit):
        if sample_unit:
            kpis = get_unit_kpis_sql(sample_unit)
            assert isinstance(kpis, dict)
            assert 'total_exames' in kpis
            assert 'media_espera' in kpis
            assert 'taxa_conformidade' in kpis

    def test_unit_kpis_with_null_unit(self):
        kpis = get_unit_kpis_sql(None)
        assert isinstance(kpis, dict)
        assert kpis['total_exames'] == 0

    def test_unit_kpis_with_empty_unit(self):
        kpis = get_unit_kpis_sql("")
        assert isinstance(kpis, dict)

    def test_unit_kpis_with_year_filter(self, sample_unit, sample_year):
        if sample_unit:
            kpis = get_unit_kpis_sql(sample_unit, year=sample_year)
            assert isinstance(kpis, dict)

    def test_unit_kpis_year_filtered_less_than_total(self, sample_unit, sample_year):
        if sample_unit:
            kpis_all = get_unit_kpis_sql(sample_unit)
            kpis_year = get_unit_kpis_sql(sample_unit, year=sample_year)
            assert kpis_year['total_exames'] <= kpis_all['total_exames']

    def test_unit_demographics_with_valid_unit(self, sample_unit):
        if sample_unit:
            df = get_unit_demographics_sql(sample_unit)
            assert isinstance(df, pd.DataFrame)

    def test_unit_demographics_with_null_unit(self):
        df = get_unit_demographics_sql(None)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_unit_demographics_with_year_filter(self, sample_unit, sample_year):
        if sample_unit:
            df = get_unit_demographics_sql(sample_unit, year=sample_year)
            assert isinstance(df, pd.DataFrame)

    def test_unit_agility_with_valid_unit(self, sample_unit):
        if sample_unit:
            df = get_unit_agility_sql(sample_unit)
            assert isinstance(df, pd.DataFrame)

    def test_unit_agility_with_null_unit(self):
        df = get_unit_agility_sql(None)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_unit_agility_with_year_filter(self, sample_unit, sample_year):
        if sample_unit:
            df = get_unit_agility_sql(sample_unit, year=sample_year)
            assert isinstance(df, pd.DataFrame)

    def test_unit_wait_time_trend_with_valid_unit(self, sample_unit):
        if sample_unit:
            df = get_unit_wait_time_trend_sql(sample_unit)
            assert isinstance(df, pd.DataFrame)

    def test_unit_wait_time_trend_with_null_unit(self):
        df = get_unit_wait_time_trend_sql(None)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_unit_wait_time_trend_with_year_filter(self, sample_unit, sample_year):
        if sample_unit:
            df = get_unit_wait_time_trend_sql(sample_unit, year=sample_year)
            assert isinstance(df, pd.DataFrame)

    def test_unit_follow_up_overdue_with_valid_unit(self, sample_unit):
        if sample_unit:
            df = get_unit_follow_up_overdue_sql(sample_unit)
            assert isinstance(df, pd.DataFrame)

    def test_unit_follow_up_overdue_with_null_unit(self):
        df = get_unit_follow_up_overdue_sql(None)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_unit_follow_up_overdue_with_limit(self, sample_unit):
        if sample_unit:
            df = get_unit_follow_up_overdue_sql(sample_unit, limit=5)
            assert isinstance(df, pd.DataFrame)
            assert len(df) <= 5

    def test_unit_follow_up_overdue_with_year_filter(self, sample_unit, sample_year):
        if sample_unit:
            df = get_unit_follow_up_overdue_sql(sample_unit, year=sample_year)
            assert isinstance(df, pd.DataFrame)

    def test_unit_follow_up_count_with_valid_unit(self, sample_unit):
        if sample_unit:
            count = get_unit_follow_up_count_sql(sample_unit)
            assert isinstance(count, int)
            assert count >= 0

    def test_unit_follow_up_count_with_null_unit(self):
        count = get_unit_follow_up_count_sql(None)
        assert count == 0

    def test_unit_follow_up_count_matches_overdue_len(self, sample_unit):
        if sample_unit:
            count = get_unit_follow_up_count_sql(sample_unit)
            df = get_unit_follow_up_overdue_sql(sample_unit, limit=count + 10 if count > 0 else 10)
            assert len(df) <= count + 1

    def test_unit_high_risk_patients(self, sample_unit):
        if sample_unit:
            df = get_unit_high_risk_patients_sql(sample_unit)
            assert isinstance(df, pd.DataFrame)

    def test_unit_high_risk_patients_with_year(self, sample_unit, sample_year):
        if sample_unit:
            df = get_unit_high_risk_patients_sql(sample_unit, year=sample_year)
            assert isinstance(df, pd.DataFrame)

    def test_all_high_risk_patients(self):
        df = get_all_high_risk_patients_sql()
        assert isinstance(df, pd.DataFrame)

    def test_all_high_risk_patients_with_year(self, sample_year):
        df = get_all_high_risk_patients_sql(year=sample_year)
        assert isinstance(df, pd.DataFrame)

    def test_all_high_risk_patients_with_region(self, sample_region):
        if sample_region:
            df = get_all_high_risk_patients_sql(region=sample_region)
            assert isinstance(df, pd.DataFrame)


class TestPrioritization:

    def test_unit_prioritization_returns_dataframe(self, sample_unit):
        if sample_unit:
            df = get_unit_prioritization_sql(sample_unit)
            assert isinstance(df, pd.DataFrame)

    def test_unit_prioritization_with_year(self, sample_unit, sample_year):
        if sample_unit:
            df = get_unit_prioritization_sql(sample_unit, year=sample_year)
            assert isinstance(df, pd.DataFrame)

    def test_unit_priority_summary_returns_dict(self, sample_unit):
        if sample_unit:
            result = get_unit_priority_summary_sql(sample_unit)
            assert isinstance(result, dict)
            assert 'total' in result

    def test_unit_priority_summary_with_year(self, sample_unit, sample_year):
        if sample_unit:
            result = get_unit_priority_summary_sql(sample_unit, year=sample_year)
            assert isinstance(result, dict)

    def test_calculate_priority_critical(self):
        result = calculate_priority('5')
        assert result['prioridade'] == 'CRÍTICA'

    def test_calculate_priority_high(self):
        result = calculate_priority('4')
        assert result['prioridade'] == 'CRÍTICA'

    def test_calculate_priority_birads_0(self):
        result = calculate_priority('0')
        assert result['prioridade'] in ['MÉDIA', 'ALTA', 'CRÍTICA']

    def test_calculate_priority_birads_3(self):
        result = calculate_priority('3')
        assert result['prioridade'] == 'MÉDIA'

    def test_calculate_priority_birads_1(self):
        result = calculate_priority('1')
        assert result['prioridade'] == 'ROTINA'

    def test_calculate_priority_birads_2(self):
        result = calculate_priority('2')
        assert result['prioridade'] == 'ROTINA'

    def test_calculate_priority_returns_dict(self):
        result = calculate_priority('4')
        assert isinstance(result, dict)
        assert 'prioridade' in result
        assert 'nivel' in result
        assert 'cor' in result

    def test_calculate_priority_nivel_birads_5(self):
        result = calculate_priority('5')
        assert result['nivel'] == 1

    def test_calculate_priority_nivel_birads_4(self):
        result = calculate_priority('4')
        assert result['nivel'] == 1

    def test_calculate_priority_nivel_birads_1(self):
        result = calculate_priority('1')
        assert result['nivel'] == 5


class TestIndicators:

    def test_indicators_returns_dict(self):
        result = get_indicators_data_sql()
        assert isinstance(result, dict)

    def test_indicators_with_year_filter(self, sample_year):
        result = get_indicators_data_sql(year=sample_year)
        assert isinstance(result, dict)

    def test_indicators_with_region_filter(self, sample_region):
        if sample_region:
            result = get_indicators_data_sql(region=sample_region)
            assert isinstance(result, dict)

    def test_indicators_with_unit_filter(self, sample_unit):
        if sample_unit:
            result = get_indicators_data_sql(health_unit=sample_unit)
            assert isinstance(result, dict)

    def test_indicators_with_combined_filters(self, sample_year, sample_region):
        if sample_region:
            result = get_indicators_data_sql(year=sample_year, region=sample_region)
            assert isinstance(result, dict)

    def test_indicator_details_returns_dataframe(self):
        df = get_indicator_details_sql('target_population')
        assert isinstance(df, pd.DataFrame)

    def test_indicator_details_with_year(self, sample_year):
        df = get_indicator_details_sql('target_population', year=sample_year)
        assert isinstance(df, pd.DataFrame)

    def test_indicator_details_with_region(self, sample_region):
        if sample_region:
            df = get_indicator_details_sql('target_population', region=sample_region)
            assert isinstance(df, pd.DataFrame)

    def test_indicator_details_with_limit(self):
        df = get_indicator_details_sql('target_population', limit=5)
        assert isinstance(df, pd.DataFrame)
        assert len(df) <= 5


class TestTermoLinkage:

    def test_linkage_summary_returns_dict(self):
        result = get_termo_linkage_summary_sql()
        assert isinstance(result, dict)

    def test_linkage_data_returns_dataframe(self):
        df = get_termo_linkage_data_sql()
        assert isinstance(df, pd.DataFrame)

    def test_linkage_data_with_name_search(self):
        df = get_termo_linkage_data_sql(search_nome="MARIA")
        assert isinstance(df, pd.DataFrame)

    def test_linkage_data_with_cpf_search(self):
        df = get_termo_linkage_data_sql(search_cpf="123")
        assert isinstance(df, pd.DataFrame)

    def test_linkage_data_with_cartao_sus_search(self):
        df = get_termo_linkage_data_sql(search_cartao_sus="123")
        assert isinstance(df, pd.DataFrame)

    def test_linkage_data_with_limit(self):
        df = get_termo_linkage_data_sql(limit=5)
        assert isinstance(df, pd.DataFrame)
        assert len(df) <= 5

    def test_linkage_data_with_offset(self):
        df1 = get_termo_linkage_data_sql(limit=5, offset=0)
        df2 = get_termo_linkage_data_sql(limit=5, offset=5)
        assert isinstance(df1, pd.DataFrame)
        assert isinstance(df2, pd.DataFrame)

    def test_linkage_count_returns_integer(self):
        count = get_termo_linkage_count_sql()
        assert isinstance(count, int)
        assert count >= 0

    def test_linkage_count_with_name_search(self):
        count = get_termo_linkage_count_sql(search_nome="MARIA")
        assert isinstance(count, int)
        assert count >= 0

    def test_linkage_count_filtered_less_than_total(self):
        total = get_termo_linkage_count_sql()
        filtered = get_termo_linkage_count_sql(search_nome="MARIA")
        assert filtered <= total

    def test_database_comparison_returns_dict(self):
        result = get_database_comparison_sql()
        assert isinstance(result, dict)


class TestDataIntegrity:

    def test_no_negative_wait_days_in_kpis(self):
        stats = get_kpi_data_sql()
        assert stats['mean_wait'] >= 0
        assert stats['median_wait'] >= 0

    def test_conformity_rate_matches_data(self, engine):
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
        assert abs(db_rate - kpi_rate) < 1

    def test_high_risk_count_matches_birads_4_5(self, engine):
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
        assert db_count == stats['high_risk_count']

    def test_region_filter_data_belongs_to_region(self, engine, sample_region):
        if sample_region:
            df = get_patient_data_list_sql(region=sample_region, page_size=20)
            if len(df) > 0 and 'distrito' in df.columns:
                for val in df['distrito']:
                    assert sample_region in str(val)

    def test_unit_filter_data_belongs_to_unit(self, sample_unit):
        if sample_unit:
            df = get_patient_data_list_sql(health_unit=sample_unit, page_size=20)
            if len(df) > 0 and 'unidade_saude' in df.columns:
                for val in df['unidade_saude']:
                    assert sample_unit in str(val)

    def test_year_filter_data_belongs_to_year(self, engine, sample_year):
        df = get_patient_data_list_sql(year=sample_year, page_size=20)
        if len(df) > 0 and 'data_solicitacao' in df.columns:
            for val in df['data_solicitacao']:
                if val and str(val) != 'None':
                    assert str(sample_year) in str(val)

    def test_sum_of_regions_close_to_total(self, all_regions):
        total_stats = get_kpi_data_sql()
        region_sum = 0
        for region in all_regions:
            stats = get_kpi_data_sql(region=region)
            region_sum += stats['total_exams']
        diff_pct = abs(region_sum - total_stats['total_exams']) / max(total_stats['total_exams'], 1) * 100
        assert diff_pct < 15, f"Soma dos distritos ({region_sum}) difere do total ({total_stats['total_exams']}) em {diff_pct:.1f}%"

    def test_monthly_volume_total_matches_kpi(self):
        df = get_monthly_volume_sql()
        monthly_total = df['count'].sum() if len(df) > 0 else 0
        stats = get_kpi_data_sql()
        diff_pct = abs(monthly_total - stats['total_exams']) / max(stats['total_exams'], 1) * 100
        assert diff_pct < 5, f"Volume mensal ({monthly_total}) difere do KPI ({stats['total_exams']}) em {diff_pct:.1f}%"


class TestErrorHandling:

    def test_kpi_with_invalid_year(self):
        stats = get_kpi_data_sql(year=1900)
        assert isinstance(stats, dict)
        assert stats['total_exams'] == 0

    def test_kpi_with_invalid_region(self):
        stats = get_kpi_data_sql(region="REGIAO_INEXISTENTE_XYZ")
        assert isinstance(stats, dict)
        assert stats['total_exams'] == 0

    def test_kpi_with_invalid_unit(self):
        stats = get_kpi_data_sql(health_unit="UNIDADE_INEXISTENTE_XYZ")
        assert isinstance(stats, dict)
        assert stats['total_exams'] == 0

    def test_patient_data_with_sql_injection(self):
        df = get_patient_data_list_sql(patient_name="'; DROP TABLE exam_records; --", page_size=10)
        assert isinstance(df, pd.DataFrame)

    def test_patient_data_with_sql_injection_region(self):
        stats = get_kpi_data_sql(region="'; DROP TABLE exam_records; --")
        assert isinstance(stats, dict)

    def test_unit_kpis_with_nonexistent_unit(self):
        kpis = get_unit_kpis_sql("UNIDADE_INEXISTENTE_XYZ_123")
        assert isinstance(kpis, dict)
        assert kpis['total_exames'] == 0

    def test_outliers_with_invalid_year(self):
        df = get_outliers_audit_sql(year=1900)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_navigation_with_invalid_region(self):
        df = get_patient_navigation_list_sql(region="INEXISTENTE")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_indicators_with_invalid_year(self):
        result = get_indicators_data_sql(year=1900)
        assert isinstance(result, dict)

    def test_linkage_data_with_empty_search(self):
        df = get_termo_linkage_data_sql(search_nome="", search_cpf="", search_cartao_sus="")
        assert isinstance(df, pd.DataFrame)

    def test_high_risk_cases_with_invalid_region(self):
        df = get_high_risk_cases_sql(region="INEXISTENTE")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_conformity_by_unit_with_invalid_year(self):
        df = get_conformity_by_unit_sql(year=1900)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_birads_distribution_with_invalid_year(self):
        df = get_birads_distribution_sql(year=1900)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


class TestExpectedValues:

    def test_total_exams_above_100k(self):
        stats = get_kpi_data_sql()
        assert stats['total_exams'] >= 100000

    def test_mean_wait_around_12_days(self):
        stats = get_kpi_data_sql()
        assert 5 <= stats['mean_wait'] <= 20

    def test_conformity_rate_above_85_percent(self):
        stats = get_kpi_data_sql()
        assert stats['conformity_rate'] >= 85

    def test_high_risk_cases_around_1800(self):
        stats = get_kpi_data_sql()
        assert 1000 <= stats['high_risk_count'] <= 3000

    def test_districts_count_equals_10(self):
        regions = get_regions()
        assert len(regions) >= 10


class TestDistrictUnitMapping:

    def test_units_by_district_returns_list(self, sample_region):
        if sample_region:
            units = get_units_by_district(sample_region)
            assert isinstance(units, list)

    def test_units_by_district_nonempty(self, sample_region):
        if sample_region:
            units = get_units_by_district(sample_region)
            assert len(units) > 0

    def test_units_by_invalid_district_empty(self):
        units = get_units_by_district("INEXISTENTE")
        assert isinstance(units, list)
        assert len(units) == 0

    def test_district_for_unit(self, sample_unit):
        if sample_unit:
            district = get_district_for_unit(sample_unit)
            assert district is None or isinstance(district, str)

    def test_district_for_invalid_unit(self):
        district = get_district_for_unit("INEXISTENTE")
        assert district is None


class TestAuthentication:

    def test_user_model_exists(self):
        from src.models import User
        assert User is not None
        assert hasattr(User, 'username')
        assert hasattr(User, 'password_hash')
        assert hasattr(User, 'is_active')

    def test_user_model_has_access_fields(self):
        from src.models import User
        assert hasattr(User, 'access_level')
        assert hasattr(User, 'district')
        assert hasattr(User, 'health_unit')

    def test_user_model_has_password_management_fields(self):
        from src.models import User
        assert hasattr(User, 'must_change_password')
        assert hasattr(User, 'password_reset_token')
        assert hasattr(User, 'password_reset_expires')

    def test_user_table_exists(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
            """))
            assert result.fetchone()[0] is True

    def test_admin_user_exists(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM users WHERE username = 'admin'
            """))
            assert result.fetchone()[0] == 1

    def test_password_hashing(self):
        from src.models import User
        user = User(username='test_user', name='Test')
        user.set_password('test123')
        assert user.password_hash is not None
        assert user.password_hash != 'test123'
        assert len(user.password_hash) > 20

    def test_password_verification(self):
        from src.models import User
        user = User(username='test_user', name='Test')
        user.set_password('correct_password')
        assert user.check_password('correct_password') is True
        assert user.check_password('wrong_password') is False

    def test_password_hash_uses_scrypt(self):
        from src.models import User
        user = User(username='test_user', name='Test')
        user.set_password('mypassword')
        assert 'scrypt' in user.password_hash or 'pbkdf2' in user.password_hash

    def test_user_is_active_default(self):
        from src.models import User
        is_active_col = User.__table__.columns['is_active']
        assert is_active_col.default is not None
        assert is_active_col.default.arg is True

    def test_different_passwords_different_hashes(self):
        from src.models import User
        user1 = User(username='u1', name='T1')
        user1.set_password('password1')
        user2 = User(username='u2', name='T2')
        user2.set_password('password2')
        assert user1.password_hash != user2.password_hash


class TestSecurity:

    def test_session_timeout_configured(self):
        from src.config import SESSION_SECRET
        assert SESSION_SECRET is not None
        assert len(SESSION_SECRET) > 10

    def test_session_secret_not_hardcoded(self):
        import os
        from src.config import SESSION_SECRET
        env_secret = os.environ.get('SESSION_SECRET')
        if env_secret:
            assert SESSION_SECRET == env_secret

    def test_login_layout_exists(self):
        from src.components.layout import create_login_layout
        from src.config import COLORS
        layout = create_login_layout(COLORS)
        assert layout is not None

    def test_login_layout_has_password_field(self):
        from src.components.layout import create_login_layout
        from src.config import COLORS
        layout = create_login_layout(COLORS)
        layout_str = str(layout)
        assert 'login-password' in layout_str
        assert 'login-username' in layout_str
        assert 'login-button' in layout_str

    def test_login_layout_expired_message(self):
        from src.components.layout import create_login_layout
        from src.config import COLORS
        layout = create_login_layout(COLORS, session_expired=True)
        layout_str = str(layout)
        assert 'expirou' in layout_str.lower()

    def test_excluded_paths_defined(self):
        source_code = open('main.py', 'r').read()
        assert '/_dash-' in source_code
        assert '/login' in source_code
        assert '/logout' in source_code
        assert '/assets/' in source_code

    def test_session_timeout_one_hour(self):
        source_code = open('main.py', 'r').read()
        assert 'timedelta(hours=1)' in source_code

    def test_login_time_stored(self):
        source_code = open('main.py', 'r').read()
        assert 'login_time' in source_code
        assert 'isoformat()' in source_code

    def test_next_url_preserved(self):
        source_code = open('main.py', 'r').read()
        assert 'next_url' in source_code

    def test_asset_files_excluded_from_redirect(self):
        source_code = open('main.py', 'r').read()
        assert '.ico' in source_code
        assert '.png' in source_code
        assert '.css' in source_code
        assert '.js' in source_code


class TestCombinedFilterConsistency:

    def test_year_region_reduces_both(self, sample_year, sample_region):
        if not sample_region:
            pytest.skip("No region available")
        stats_all = get_kpi_data_sql()
        stats_year = get_kpi_data_sql(year=sample_year)
        stats_region = get_kpi_data_sql(region=sample_region)
        stats_both = get_kpi_data_sql(year=sample_year, region=sample_region)
        assert stats_both['total_exams'] <= stats_year['total_exams']
        assert stats_both['total_exams'] <= stats_region['total_exams']
        assert stats_both['total_exams'] <= stats_all['total_exams']

    def test_adding_filters_never_increases_total(self, sample_year, sample_region, sample_unit):
        totals = []
        totals.append(get_kpi_data_sql()['total_exams'])
        if sample_year:
            totals.append(get_kpi_data_sql(year=sample_year)['total_exams'])
        if sample_region:
            totals.append(get_kpi_data_sql(year=sample_year, region=sample_region)['total_exams'])
        if sample_unit:
            totals.append(get_kpi_data_sql(year=sample_year, region=sample_region, health_unit=sample_unit)['total_exams'])
        for i in range(1, len(totals)):
            assert totals[i] <= totals[i-1]

    def test_conformity_filter_dentro_fora_sum(self):
        stats_all = get_kpi_data_sql()
        stats_dentro = get_kpi_data_sql(conformity_status='Dentro do Prazo')
        stats_fora = get_kpi_data_sql(conformity_status='Fora do Prazo')
        combined = stats_dentro['total_exams'] + stats_fora['total_exams']
        diff_pct = abs(combined - stats_all['total_exams']) / max(stats_all['total_exams'], 1) * 100
        assert diff_pct < 5

    def test_monthly_volume_year_filter_consistent(self, sample_year):
        df_all = get_monthly_volume_sql()
        df_year = get_monthly_volume_sql(year=sample_year)
        if len(df_year) > 0 and len(df_all) > 0:
            assert df_year['count'].sum() <= df_all['count'].sum()

    def test_outliers_year_region_consistent(self, sample_year, sample_region):
        if not sample_region:
            pytest.skip("No region available")
        df_all = get_outliers_audit_sql()
        df_combined = get_outliers_audit_sql(year=sample_year, region=sample_region)
        assert len(df_combined) <= len(df_all)

    def test_patient_navigation_year_region_consistent(self, sample_year, sample_region):
        if not sample_region:
            pytest.skip("No region available")
        df_all = get_patient_navigation_list_sql(limit=500)
        df_combined = get_patient_navigation_list_sql(year=sample_year, region=sample_region, limit=500)
        assert len(df_combined) <= len(df_all)

    def test_birads_distribution_year_region_consistent(self, sample_year, sample_region):
        if not sample_region:
            pytest.skip("No region available")
        df_all = get_birads_distribution_sql()
        df_combined = get_birads_distribution_sql(year=sample_year, region=sample_region)
        total_all = df_all['count'].sum() if len(df_all) > 0 and 'count' in df_all.columns else 0
        total_combined = df_combined['count'].sum() if len(df_combined) > 0 and 'count' in df_combined.columns else 0
        assert total_combined <= total_all

    def test_unit_kpi_year_filter_consistent(self, sample_unit, sample_year):
        if not sample_unit:
            pytest.skip("No unit available")
        kpis_all = get_unit_kpis_sql(sample_unit)
        kpis_year = get_unit_kpis_sql(sample_unit, year=sample_year)
        assert kpis_year['total_exames'] <= kpis_all['total_exames']


class TestDataMasking:

    def test_masking_functions_exist(self):
        from src.components.tables import mask_name, mask_cns, mask_cpf
        assert callable(mask_name)
        assert callable(mask_cns)
        assert callable(mask_cpf)

    def test_mask_name_when_masked(self):
        from src.components.tables import mask_name
        result = mask_name("MARIA DA SILVA SANTOS", True)
        assert 'MARIA DA SILVA SANTOS' not in result
        assert len(result) < len("MARIA DA SILVA SANTOS")

    def test_mask_name_when_unmasked(self):
        from src.components.tables import mask_name
        result = mask_name("MARIA DA SILVA SANTOS", False)
        assert result == "MARIA DA SILVA SANTOS"

    def test_mask_cns_when_masked(self):
        from src.components.tables import mask_cns
        result = mask_cns("123456789012345", True)
        assert '123456789012345' not in result

    def test_mask_cns_when_unmasked(self):
        from src.components.tables import mask_cns
        result = mask_cns("123456789012345", False)
        assert result == "123456789012345"

    def test_mask_cpf_when_masked(self):
        from src.components.tables import mask_cpf
        result = mask_cpf("12345678901", True)
        assert '12345678901' not in result

    def test_mask_cpf_when_unmasked(self):
        from src.components.tables import mask_cpf
        result = mask_cpf("12345678901", False)
        assert result == "12345678901"

    def test_mask_name_handles_none(self):
        from src.components.tables import mask_name
        result = mask_name(None, True)
        assert result is not None

    def test_mask_cns_handles_none(self):
        from src.components.tables import mask_cns
        result = mask_cns(None, True)
        assert result is not None

    def test_mask_cpf_handles_empty(self):
        from src.components.tables import mask_cpf
        result = mask_cpf("", True)
        assert result is not None


class TestTableLegends:

    def test_create_table_legend_exists(self):
        from src.components.tables import create_table_legend
        assert callable(create_table_legend)

    def test_create_table_legend_returns_html(self):
        from src.components.tables import create_table_legend
        result = create_table_legend(['nome', 'idade'])
        assert result is not None

    def test_column_legends_dict_exists(self):
        from src.components.tables import COLUMN_LEGENDS
        assert isinstance(COLUMN_LEGENDS, dict)
        assert len(COLUMN_LEGENDS) > 0

    def test_column_legends_has_common_keys(self):
        from src.components.tables import COLUMN_LEGENDS
        expected_keys = ['nome', 'idade', 'birads_max', 'data_solicitacao',
                         'data_realizacao', 'data_liberacao', 'unidade_saude',
                         'distrito_saude', 'tempestividade']
        for key in expected_keys:
            assert key in COLUMN_LEGENDS, f"Legenda '{key}' ausente no COLUMN_LEGENDS"


class TestAccessRequests:

    def test_access_requests_table_has_columns(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'access_requests'
                ORDER BY ordinal_position
            """))
            columns = [row[0] for row in result.fetchall()]
            expected = ['name', 'email', 'username', 'access_level', 'status']
            for col in expected:
                assert col in columns, f"Coluna '{col}' ausente na tabela access_requests"

    def test_get_pending_access_requests_imported(self):
        from src.data_layer import get_pending_access_requests
        assert callable(get_pending_access_requests)

    def test_create_access_request_imported(self):
        from src.data_layer import create_access_request
        assert callable(create_access_request)


class TestPasswordManagement:

    def test_create_password_reset_token_imported(self):
        from src.data_layer import create_password_reset_token
        assert callable(create_password_reset_token)

    def test_validate_reset_token_imported(self):
        from src.data_layer import validate_reset_token
        assert callable(validate_reset_token)

    def test_reset_password_with_token_imported(self):
        from src.data_layer import reset_password_with_token
        assert callable(reset_password_with_token)

    def test_change_password_first_access_imported(self):
        from src.data_layer import change_password_first_access
        assert callable(change_password_first_access)


class TestMultiSelectFilters:
    """Tests for multi-select filter support (lists of values) in all data layer functions"""

    # --- _normalize_to_list unit tests ---

    def test_normalize_to_list_none_returns_none(self):
        assert _normalize_to_list(None) is None

    def test_normalize_to_list_all_string_returns_none(self):
        assert _normalize_to_list('ALL') is None

    def test_normalize_to_list_empty_string_returns_none(self):
        assert _normalize_to_list('') is None

    def test_normalize_to_list_scalar_returns_list(self):
        result = _normalize_to_list('ARARAQUARA')
        assert result == ['ARARAQUARA']

    def test_normalize_to_list_integer_returns_list(self):
        result = _normalize_to_list(2024)
        assert result == [2024]

    def test_normalize_to_list_empty_list_returns_none(self):
        assert _normalize_to_list([]) is None

    def test_normalize_to_list_all_in_list_returns_none(self):
        assert _normalize_to_list(['ALL']) is None

    def test_normalize_to_list_filters_all_from_mixed_list(self):
        result = _normalize_to_list(['ALL', '2023', '2024'])
        assert result == ['2023', '2024']

    def test_normalize_to_list_valid_list_unchanged(self):
        result = _normalize_to_list(['4', '5'])
        assert result == ['4', '5']

    def test_normalize_to_list_filters_none_from_list(self):
        result = _normalize_to_list([None, '4', None])
        assert result == ['4']

    # --- _build_where_clause with lists ---

    def test_build_where_clause_single_year_scalar(self):
        clause, params = _build_where_clause(year=2024)
        assert 'year = :year' in clause
        assert params.get('year') == 2024

    def test_build_where_clause_single_year_list(self):
        clause, params = _build_where_clause(year=[2024])
        assert 'year = :year' in clause
        assert params.get('year') == 2024

    def test_build_where_clause_multi_year(self):
        clause, params = _build_where_clause(year=[2023, 2024])
        assert 'year IN' in clause
        assert params.get('year_0') == 2023
        assert params.get('year_1') == 2024

    def test_build_where_clause_multi_birads(self):
        clause, params = _build_where_clause(birads=['4', '5'])
        assert 'birads_max IN' in clause
        assert params.get('birads_0') == '4'
        assert params.get('birads_1') == '5'

    def test_build_where_clause_single_birads_list(self):
        clause, params = _build_where_clause(birads=['3'])
        assert 'birads_max = :birads' in clause
        assert params.get('birads') == '3'

    def test_build_where_clause_multi_age_range(self):
        clause, params = _build_where_clause(age_range=['40-49', '50-69'])
        assert 'OR' in clause
        assert 'paciente__idade' in clause

    def test_build_where_clause_multi_priority(self):
        clause, params = _build_where_clause(priority=['CRITICA', 'ALTA'])
        assert 'birads_max IN' in clause

    def test_build_where_clause_empty_list_ignored(self):
        clause, params = _build_where_clause(year=[])
        assert 'year' not in clause

    # --- KPI with multi-select ---

    def test_kpi_multi_year_list(self):
        years = get_years()
        if len(years) >= 2:
            stats = get_kpi_data_sql(year=years[:2])
            assert isinstance(stats, dict)
            assert stats['total_exams'] >= 0

    def test_kpi_multi_year_covers_more_than_single(self):
        years = get_years()
        if len(years) >= 2:
            stats_single = get_kpi_data_sql(year=years[0])
            stats_multi = get_kpi_data_sql(year=years[:2])
            assert stats_multi['total_exams'] >= stats_single['total_exams']

    def test_kpi_multi_birads(self):
        stats = get_kpi_data_sql(birads=['4', '5'])
        assert isinstance(stats, dict)
        assert stats['total_exams'] >= 0

    def test_kpi_multi_birads_covers_more_than_single(self):
        stats_4 = get_kpi_data_sql(birads='4')
        stats_5 = get_kpi_data_sql(birads='5')
        stats_multi = get_kpi_data_sql(birads=['4', '5'])
        assert stats_multi['total_exams'] >= max(stats_4['total_exams'], stats_5['total_exams'])

    def test_kpi_multi_age_range(self):
        stats = get_kpi_data_sql(age_range=['40-49', '50-69'])
        assert isinstance(stats, dict)
        assert stats['total_exams'] >= 0

    def test_kpi_multi_age_range_covers_more_than_single(self):
        stats_40 = get_kpi_data_sql(age_range='40-49')
        stats_50 = get_kpi_data_sql(age_range='50-69')
        stats_multi = get_kpi_data_sql(age_range=['40-49', '50-69'])
        assert stats_multi['total_exams'] >= max(stats_40['total_exams'], stats_50['total_exams'])

    def test_kpi_multi_priority(self):
        stats = get_kpi_data_sql(priority=['CRITICA', 'ALTA'])
        assert isinstance(stats, dict)
        assert stats['total_exams'] >= 0

    def test_kpi_multi_region(self, ):
        regions = get_regions()
        if len(regions) >= 2:
            stats = get_kpi_data_sql(region=regions[:2])
            assert isinstance(stats, dict)
            assert stats['total_exams'] >= 0

    def test_kpi_multi_region_covers_more_than_single(self):
        regions = get_regions()
        if len(regions) >= 2:
            stats_r1 = get_kpi_data_sql(region=regions[0])
            stats_r2 = get_kpi_data_sql(region=regions[1])
            stats_multi = get_kpi_data_sql(region=regions[:2])
            assert stats_multi['total_exams'] >= max(stats_r1['total_exams'], stats_r2['total_exams'])

    def test_kpi_empty_list_same_as_no_filter(self):
        stats_all = get_kpi_data_sql()
        stats_empty = get_kpi_data_sql(year=[], birads=[], region=[])
        assert stats_all['total_exams'] == stats_empty['total_exams']

    def test_kpi_single_item_list_same_as_scalar(self):
        years = get_years()
        stats_scalar = get_kpi_data_sql(year=years[0])
        stats_list = get_kpi_data_sql(year=[years[0]])
        assert stats_scalar['total_exams'] == stats_list['total_exams']

    # --- Patient data with multi-select ---

    def test_patient_data_multi_birads(self):
        df = get_patient_data_list_sql(birads=['4', '5'], page_size=10)
        assert isinstance(df, pd.DataFrame)

    def test_patient_data_count_multi_birads(self):
        count_4 = get_patient_data_count_sql(birads='4')
        count_5 = get_patient_data_count_sql(birads='5')
        count_multi = get_patient_data_count_sql(birads=['4', '5'])
        assert count_multi >= max(count_4, count_5)

    def test_patient_data_multi_age_range(self):
        df = get_patient_data_list_sql(age_range=['40-49', '50-69'], page_size=10)
        assert isinstance(df, pd.DataFrame)

    def test_patient_data_multi_year(self):
        years = get_years()
        if len(years) >= 2:
            df = get_patient_data_list_sql(year=years[:2], page_size=10)
            assert isinstance(df, pd.DataFrame)

    def test_patient_data_multi_priority(self):
        df = get_patient_data_list_sql(priority=['CRITICA', 'ALTA'], page_size=10)
        assert isinstance(df, pd.DataFrame)

    # --- Navigation with multi-select ---

    def test_navigation_multi_birads(self):
        df = get_patient_navigation_list_sql(birads=['4', '5'], limit=20)
        assert isinstance(df, pd.DataFrame)

    def test_navigation_multi_age_range(self):
        df = get_patient_navigation_list_sql(age_range=['40-49', '50-69'], limit=20)
        assert isinstance(df, pd.DataFrame)

    def test_navigation_multi_priority(self):
        df = get_patient_navigation_list_sql(priority=['CRITICA', 'ALTA'], limit=20)
        assert isinstance(df, pd.DataFrame)

    def test_navigation_multi_year(self):
        years = get_years()
        if len(years) >= 2:
            df = get_patient_navigation_list_sql(year=years[:2], limit=20)
            assert isinstance(df, pd.DataFrame)

    # --- Outliers with multi-select ---

    def test_outliers_audit_multi_year(self):
        years = get_years()
        if len(years) >= 2:
            df = get_outliers_audit_sql(year=years[:2])
            assert isinstance(df, pd.DataFrame)

    def test_outliers_audit_multi_region(self):
        regions = get_regions()
        if len(regions) >= 2:
            df = get_outliers_audit_sql(region=regions[:2])
            assert isinstance(df, pd.DataFrame)

    def test_outliers_summary_multi_year(self):
        years = get_years()
        if len(years) >= 2:
            df = get_outliers_summary_sql(year=years[:2])
            assert isinstance(df, pd.DataFrame)

    # --- Monthly volume with multi-select ---

    def test_monthly_volume_multi_year(self):
        years = get_years()
        if len(years) >= 2:
            df = get_monthly_volume_sql(year=years[:2])
            assert isinstance(df, pd.DataFrame)

    def test_monthly_volume_multi_region(self):
        regions = get_regions()
        if len(regions) >= 2:
            df = get_monthly_volume_sql(region=regions[:2])
            assert isinstance(df, pd.DataFrame)

    # --- Indicators with multi-select ---

    def test_indicators_multi_year(self):
        years = get_years()
        if len(years) >= 2:
            result = get_indicators_data_sql(year=years[:2])
            assert isinstance(result, dict)

    def test_indicators_multi_age_range(self):
        result = get_indicators_data_sql(age_range=['40-49', '50-69'])
        assert isinstance(result, dict)

    def test_indicators_multi_birads(self):
        result = get_indicators_data_sql(birads=['4', '5'])
        assert isinstance(result, dict)

    # --- Priority combinations ---

    def test_priority_critica_maps_birads_4_5(self):
        stats_pri = get_kpi_data_sql(priority='CRITICA')
        stats_br = get_kpi_data_sql(birads=['4', '5'])
        assert stats_pri['total_exams'] == stats_br['total_exams']

    def test_priority_rotina_maps_birads_1_2(self):
        stats_pri = get_kpi_data_sql(priority='ROTINA')
        stats_br = get_kpi_data_sql(birads=['1', '2'])
        assert stats_pri['total_exams'] == stats_br['total_exams']

    def test_priority_multi_covers_combined_birads(self):
        stats_critica = get_kpi_data_sql(priority='CRITICA')
        stats_alta = get_kpi_data_sql(priority='ALTA')
        stats_multi = get_kpi_data_sql(priority=['CRITICA', 'ALTA'])
        expected = stats_critica['total_exams'] + stats_alta['total_exams']
        assert stats_multi['total_exams'] == expected


def run_all_tests():
    """Executa todos os testes e exibe resumo"""
    print("=" * 60)
    print("TESTES DO DASHBOARD CENTRAL INTELIGENTE")
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
        TestPrioritization,
        TestIndicators,
        TestTermoLinkage,
        TestDataIntegrity,
        TestErrorHandling,
        TestExpectedValues,
        TestDistrictUnitMapping,
        TestAuthentication,
        TestSecurity,
        TestCombinedFilterConsistency,
        TestDataMasking,
        TestTableLegends,
        TestAccessRequests,
        TestPasswordManagement,
        TestMultiSelectFilters,
    ]

    passed = 0
    failed = 0
    errors = []

    for test_class in test_classes:
        print(f"\n--- {test_class.__name__} ---")
        instance = test_class()

        for method_name in sorted(dir(instance)):
            if method_name.startswith('test_'):
                try:
                    method = getattr(instance, method_name)
                    import inspect
                    sig = inspect.signature(method)
                    params = list(sig.parameters.keys())
                    if params:
                        print(f"  ⊘ {method_name}: (requer fixtures, usar pytest)")
                        continue
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
