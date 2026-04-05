-- ============================================================================
-- dim_employee — Dimensão de funcionários (Camada Gold)
-- ============================================================================
-- Tabela dimensional pronta para consumo por BI/análise.
--
-- Derivada do stg_employees, adiciona colunas calculadas:
--   - employee_sk    → surrogate key (mesmo valor do employee_id)
--   - full_name      → concatenação de first_name + last_name
--   - years_of_service → tempo de casa em anos (calculado com age())
--   - salary_band    → classificação salarial (Junior/Mid/Senior)
--   - processed_at   → timestamp de quando o dbt processou
--
-- Materialização: table → recria a tabela inteira a cada execução.
-- ============================================================================
{{ config(materialized='table', alias='dim_employee') }}

select
    employee_id as employee_sk,              -- surrogate key
    first_name,
    last_name,
    first_name || ' ' || last_name as full_name,  -- nome completo
    email,
    department,
    city,
    salary,
    hire_date,
    extract(year from age(now(), hire_date)) as years_of_service,  -- tempo de casa
    case
        when salary < 5000 then 'Junior'
        when salary < 10000 then 'Mid'
        else 'Senior'
    end as salary_band,                      -- faixa salarial
    processed_at
from {{ ref('stg_employees') }}
