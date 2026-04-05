-- ============================================================================
-- stg_employees — Camada Silver (limpeza e padronização)
-- ============================================================================
-- Lê da tabela raw_employees (criada pelo Python no Airflow) e aplica:
--   - Padronização de texto: lower() em nomes, upper() em departamento
--   - Remoção de espaços: trim() em todas as strings
--   - Conversão de tipos: cast() para numeric e date
--   - Filtro de nulos: remove registros sem dados obrigatórios
--   - Timestamp de processamento: now() como processed_at
--
-- Materialização: table → recria a tabela inteira a cada execução.
-- Dependência: source('raw', 'raw_employees')
-- ============================================================================
{{ config(materialized='table', alias='stg_employees') }}

select
    employee_id,
    lower(trim(first_name)) as first_name,       -- padroniza nomes para lowercase
    lower(trim(last_name)) as last_name,
    lower(trim(email)) as email,                 -- emails sempre lowercase
    upper(trim(department)) as department,       -- departamentos sempre UPPERCASE
    initcap(trim(city)) as city,                 -- cidades com primeira letra maiúscula
    cast(salary as numeric(10,2)) as salary,     -- garante precisão decimal
    cast(hire_date as date) as hire_date,        -- garante tipo date
    extracted_at,
    now() as processed_at                        -- timestamp de quando o dbt processou
from {{ source('raw', 'raw_employees') }}
where employee_id is not null
  and first_name is not null
  and email is not null
