-- Optimized Views for SISCAN Dashboard
-- These views pre-aggregate common queries to improve dashboard performance

-- View: KPI Summary by Year and Unit
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kpi_summary AS
SELECT 
    year,
    unidade_de_saude__nome as health_unit,
    distrito_sanitario as region,
    COUNT(*) as total_exams,
    AVG(wait_days) as mean_wait,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY wait_days) as median_wait,
    COUNT(CASE WHEN conformity_status = 'Dentro do Prazo' THEN 1 END) as conformity_count,
    COUNT(CASE WHEN birads_max IN ('4', '5') THEN 1 END) as high_risk_count,
    COUNT(DISTINCT patient_unique_id) as unique_patients
FROM exam_records
WHERE unidade_de_saude__data_da_solicitacao >= '2023-01-01'
    AND (wait_days IS NULL OR wait_days <= 365)
    AND (birads_max IS NOT NULL AND birads_max != '' AND birads_max ~ '^[0-9]+$')
GROUP BY year, unidade_de_saude__nome, distrito_sanitario;

CREATE INDEX IF NOT EXISTS idx_mv_kpi_year ON mv_kpi_summary(year);
CREATE INDEX IF NOT EXISTS idx_mv_kpi_unit ON mv_kpi_summary(health_unit);
CREATE INDEX IF NOT EXISTS idx_mv_kpi_region ON mv_kpi_summary(region);

-- View: Monthly Volume Summary
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_monthly_volume AS
SELECT 
    year,
    TO_CHAR(unidade_de_saude__data_da_solicitacao, 'YYYY-MM') as month_year,
    unidade_de_saude__nome as health_unit,
    distrito_sanitario as region,
    COUNT(*) as count
FROM exam_records
WHERE unidade_de_saude__data_da_solicitacao >= '2023-01-01'
    AND (wait_days IS NULL OR wait_days <= 365)
    AND (birads_max IS NOT NULL AND birads_max != '' AND birads_max ~ '^[0-9]+$')
GROUP BY year, TO_CHAR(unidade_de_saude__data_da_solicitacao, 'YYYY-MM'), unidade_de_saude__nome, distrito_sanitario;

CREATE INDEX IF NOT EXISTS idx_mv_volume_year ON mv_monthly_volume(year);
CREATE INDEX IF NOT EXISTS idx_mv_volume_month ON mv_monthly_volume(month_year);

-- View: BI-RADS Distribution Summary
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_birads_distribution AS
SELECT 
    year,
    unidade_de_saude__nome as health_unit,
    distrito_sanitario as region,
    birads_max as birads_category,
    COUNT(*) as count
FROM exam_records
WHERE unidade_de_saude__data_da_solicitacao >= '2023-01-01'
    AND (birads_max IS NOT NULL AND birads_max != '' AND birads_max ~ '^[0-9]+$')
GROUP BY year, unidade_de_saude__nome, distrito_sanitario, birads_max;

CREATE INDEX IF NOT EXISTS idx_mv_birads_year ON mv_birads_distribution(year);
CREATE INDEX IF NOT EXISTS idx_mv_birads_category ON mv_birads_distribution(birads_category);

-- View: Conformity by Unit Summary
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_conformity_by_unit AS
SELECT 
    year,
    unidade_de_saude__nome as health_unit,
    distrito_sanitario as region,
    COUNT(*) as total,
    COUNT(CASE WHEN conformity_status = 'Dentro do Prazo' THEN 1 END) as dentro_prazo,
    COUNT(CASE WHEN conformity_status = 'Fora do Prazo' THEN 1 END) as fora_prazo,
    ROUND(COUNT(CASE WHEN conformity_status = 'Dentro do Prazo' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 1) as conformity_rate
FROM exam_records
WHERE unidade_de_saude__data_da_solicitacao >= '2023-01-01'
    AND (wait_days IS NULL OR wait_days <= 365)
    AND (birads_max IS NOT NULL AND birads_max != '' AND birads_max ~ '^[0-9]+$')
GROUP BY year, unidade_de_saude__nome, distrito_sanitario;

CREATE INDEX IF NOT EXISTS idx_mv_conformity_year ON mv_conformity_by_unit(year);
CREATE INDEX IF NOT EXISTS idx_mv_conformity_unit ON mv_conformity_by_unit(health_unit);

-- Refresh command (run periodically or after data imports):
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_kpi_summary;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_volume;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_birads_distribution;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_conformity_by_unit;

-- Index for exam_records table to improve query performance
CREATE INDEX IF NOT EXISTS idx_exam_year ON exam_records(year);
CREATE INDEX IF NOT EXISTS idx_exam_unit ON exam_records(unidade_de_saude__nome);
CREATE INDEX IF NOT EXISTS idx_exam_region ON exam_records(distrito_sanitario);
CREATE INDEX IF NOT EXISTS idx_exam_birads ON exam_records(birads_max);
CREATE INDEX IF NOT EXISTS idx_exam_request_date ON exam_records(unidade_de_saude__data_da_solicitacao);
CREATE INDEX IF NOT EXISTS idx_exam_conformity ON exam_records(conformity_status);
CREATE INDEX IF NOT EXISTS idx_exam_wait_days ON exam_records(wait_days);
CREATE INDEX IF NOT EXISTS idx_exam_patient ON exam_records(patient_unique_id);

-- Composite indexes for common filter combinations
CREATE INDEX IF NOT EXISTS idx_exam_year_unit ON exam_records(year, unidade_de_saude__nome);
CREATE INDEX IF NOT EXISTS idx_exam_year_region ON exam_records(year, distrito_sanitario);
CREATE INDEX IF NOT EXISTS idx_exam_year_birads ON exam_records(year, birads_max);
