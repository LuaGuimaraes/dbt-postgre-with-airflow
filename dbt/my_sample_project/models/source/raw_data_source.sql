-- ============================================================================
-- raw_data_source — Dados hardcoded de exemplo (Source / Bronze)
-- ============================================================================
-- Este model simula uma tabela fonte com dados estáticos.
-- Em producao, seria substituido por uma source real.
--
-- Materialização: table → cria uma tabela física no banco.
-- Alias: raw_data → nome da tabela criada no PostgreSQL.
--
-- Colunas:
--   Emp_Id      → ID do funcionário
--   First_Name  → Nome
--   Last_Name   → Sobrenome
--   DOB         → Data de nascimento (formato DD-MM-YYYY)
--   DOJ         → Data de admissão (Date of Joining)
--   Record_Date → Data do registro (usada para controle incremental)
-- ============================================================================
{{ config(materialized='table', alias='raw_data') }}

with source_data as (
    select
        1 as Emp_Id,
        'Ron' as First_Name,
        'Paul' as Last_Name,
        '21-08-1969' as DOB,
        '2022-08-01 09:00:00' as DOJ,
        '2022-09-01' as Record_Date
    union all
    select
        2 as Emp_Id,
        'Ben' as First_Name,
        'Stack' as Last_Name,
        '14-04-1972' as DOB,
        '2022-08-01 09:00:00' as DOJ,
        '2022-09-01' as Record_Date
    union all
    select
        3 as Emp_Id,
        'Tacy' as First_Name,
        'Jen' as Last_Name,
        '08-11-1981' as DOB,
        '2022-08-01 09:00:00' as DOJ,
        '2022-09-01' as Record_Date
)

select * from source_data
