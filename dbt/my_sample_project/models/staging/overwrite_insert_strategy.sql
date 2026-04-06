-- ============================================================================
-- overwrite_insert_strategy — Modelo incremental (delete+insert)
-- ============================================================================
-- Demonstra a estratégia incremental "delete+insert":
--   1. Deleta registros existentes que batem com o unique_key
--   2. Insere os novos registros no lugar
--
-- Materialização: incremental
-- unique_key: Emp_Id → identifica registros para sobrescrever
-- incremental_strategy: delete+insert
--
-- CTE de_dup: remove duplicatas mantendo o registro mais recente
--   (ROW_NUMBER particionado por emp_id, ordenado por record_date DESC)
-- ============================================================================
{{ config(
    materialized='incremental',
    alias='del_ins',
    unique_key='Emp_Id',
    incremental_strategy='delete+insert'
) }}

with sql_query as (
    select
        CAST(Emp_Id AS INTEGER) AS emp_id,
        First_Name as first_name,
        Last_Name as last_name,
        TO_DATE(DOB, 'DD-MM-YYYY') as birth_date,
        DOJ as date_of_joining,
        Record_Date as record_date
    from {{ ref('raw_data_source') }}
),

de_dup as (
    select
        *,
        ROW_NUMBER() OVER (partition by emp_id order by record_date desc) as rank
    from sql_query
)

select emp_id, first_name, last_name, birth_date, date_of_joining, record_date
from de_dup
where rank = 1
