{{ config(materialized='incremental', 
   alias='inc_ap',
   ) 
}}

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
where Record_Date = '{{ var("execution_date") }}'
{% endif %}
)

select * 
from sql_query