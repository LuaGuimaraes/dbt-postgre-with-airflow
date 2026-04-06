"""
employee_data_pipeline.py — DAG principal

Pipeline ELT completo:
  1. EXTRAÇÃO     → Gera dados fake e carrega em raw_employees (Bronze)
  2. TRANSFORMAÇÃO → dbt limpa, padroniza e modela (Silver → Gold)
  3. VALIDAÇÃO    → dbt test verifica qualidade dos dados
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime

# Importa a função de extração de um arquivo separado
from extract_employees import extract_fake_employees


# ============================================================================
# Configuração padrão da DAG
# ============================================================================
default_args = {
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
}

with DAG(
    dag_id="employee_data_pipeline",
    default_args=default_args,
    schedule=None,  # Sem agendamento automático — dispara manualmente
    catchup=False,  # Não executa execuções passadas pendentes
    max_active_runs=1,  # Impede execuções concorrentes
    tags=["dbt", "employee", "bronze-silver-gold"],
    description="Pipeline completo: extração → bronze → silver → gold",
) as dag:
    # -----------------------------------------------------------------------
    # CAMADA 1: EXTRAÇÃO (Bronze — dados brutos)
    # -----------------------------------------------------------------------
    extract_data = PythonOperator(
        task_id="extract_fake_employees",
        python_callable=extract_fake_employees,
    )

    # -----------------------------------------------------------------------
    # CAMADA 2: TRANSFORMAÇÃO (Silver → Gold via dbt)
    # -----------------------------------------------------------------------
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt_project && dbt run",
    )

    # -----------------------------------------------------------------------
    # CAMADA 3: VALIDAÇÃO (Testes de qualidade)
    # -----------------------------------------------------------------------
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt_project && dbt test",
    )

    # -----------------------------------------------------------------------
    # ORDEM DE EXECUÇÃO
    # -----------------------------------------------------------------------
    extract_data >> dbt_run >> dbt_test
