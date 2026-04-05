from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime
with DAG(
    dag_id="hello_world",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False
) as dag:
    
    BashOperator(
        task_id="print_hello",
        bash_command="echo 'Airflow está funcionando!'"
    )