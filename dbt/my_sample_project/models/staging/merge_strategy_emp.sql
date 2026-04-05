-- ============================================================================
-- merge_strategy_emp — Modelo incremental (merge/UPSERT)
-- ============================================================================
-- Demonstra a estratégia incremental "merge" (padrão do PostgreSQL):
--   - Se o registro existe (pelo unique_key), atualiza os campos
--   - Se não existe, insere como novo
--
-- Materialização: incremental
-- unique_key: Emp_Id → identifica registros para atualizar/inserir
--
-- CTE de_dup: remove duplicatas mantendo o registro mais recente
--   (ROW_NUMBER particionado por emp_id, ordenado por record_date DESC)
--
-- BUG conhecido: a coluna 'rank' está sendo exposta no SELECT final.
-- Deveria ser excluída pois é um artefato interno de deduplicação.
-- ============================================================================
{{ config(
    materialized='incremental',
    alias='merge_ins',
    unique_key='Emp_Id'
) }}

with sql_query as (
    select
        CAST(Emp_Id AS INTEGER) AS emp_id,
        First_Name as first_name,
        Last_Name as last_name,
        TO_DATE(DOB, 'DD-MM-YYYY') as birth_date,
        DOJ as date_of_joning,
        Record_Date as record_date
    from {{ ref('raw_data_source') }}
),

de_dup as (
    select
        *,
        ROW_NUMBER() OVER (partition by emp_id order by record_date desc) as rank
    from sql_query
)

select emp_id, first_name, last_name, birth_date, date_of_joning, record_date, rank
from de_dup
where rank = 1
