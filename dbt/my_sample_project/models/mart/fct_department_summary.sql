-- ============================================================================
-- fct_department_summary — Fato agregado por departamento (Camada Gold)
-- ============================================================================
-- Tabela de métricas gerenciais agrupadas por departamento.
-- Usada para dashboards, relatórios e análises de RH.
--
-- Métricas calculadas:
--   - employee_count       → total de funcionários
--   - avg_salary           → salário médio
--   - min/max_salary       → faixa salarial
--   - avg_years_of_service → tempo médio de casa
--   - cities_count         → em quantas cidades o departamento atua
--
-- Materialização: table → recria a tabela inteira a cada execução.
-- ============================================================================
{{ config(materialized='table', alias='fct_department_summary') }}

select
    department,
    count(*) as employee_count,
    round(avg(salary), 2) as avg_salary,
    min(salary) as min_salary,
    max(salary) as max_salary,
    round(avg(extract(year from age(now(), hire_date))), 1) as avg_years_of_service,
    count(distinct city) as cities_count,
    processed_at
from {{ ref('stg_employees') }}
group by department, processed_at
