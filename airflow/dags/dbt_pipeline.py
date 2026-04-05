from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {"start_date": datetime(2024, 1, 1), "retries": 1}

with DAG(
    dag_id="dbt_pipeline",
    default_args=default_args,
    schedule="@daily",
    catchup=False,
    tags=["dbt"],
) as dag:
    # Caminho do projeto dbt dentro do container
    dbt_project_path = "/opt/airflow/dbt_project"

    # Task 1: Executa todos os models do dbt
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {dbt_project_path} && dbt run",
    )

    # Task 2: Executa os testes do dbt (após o run)
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {dbt_project_path} && dbt test",
    )

    # Define a ordem: run -> test
    dbt_run >> dbt_test
