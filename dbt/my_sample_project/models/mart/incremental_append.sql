-- ============================================================================
-- incremental_append — Modelo incremental (append only)
-- ============================================================================
-- Demonstra a estratégia incremental padrão (append):
--   - Na primeira execução: cria a tabela com todos os dados
--   - Nas execuções seguintes: insere APENAS registros novos
--     (filtrados pela variável execution_date)
--
-- Materialização: incremental
--
-- is_incremental() → macro do dbt que retorna true quando a tabela já existe.
-- var("execution_date") → variável definida no dbt_project.yml (fixa em '2022-09-01').
--
-- BUG: A variável execution_date é hardcoded, então este modelo só funciona
-- para dados daquela data específica. Em produção, usaria algo dinâmico
-- como {{ var("execution_date", modules.datetime.date.today()) }}.
-- ============================================================================
{{ config(
    materialized='incremental',
    alias='inc_ap'
) }}

with sql_query as (
    select
        CAST(Emp_Id AS INTEGER) AS emp_id,
        First_Name as first_name,
        Last_Name as last_name,
        birth_date as birth_date,
        date_of_joning as date_of_joning,
        Record_Date as record_date
    from {{ ref('merge_strategy_emp') }}
    {% if is_incremental() %}
    -- Só executa este filtro quando a tabela já existe (execuções incrementais)
    where Record_Date = '{{ var("execution_date") }}'
    {% endif %}
)

select * from sql_query
