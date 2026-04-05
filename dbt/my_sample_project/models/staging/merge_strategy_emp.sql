{{ config(materialized='incremental',
          alias='merge_ins',
          unique_key='Emp_Id' 
        ) 
}}

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

