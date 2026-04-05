"""
Pipeline completo de dados: Extração → Bronze → Silver → Gold

Simula o fluxo real de mercado:
1. EXTRAÇÃO: Gera dados fake de funcionários e carrega na tabela raw (bronze)
2. TRANSFORMAÇÃO: dbt limpa, padroniza e modela (silver → gold)
3. VALIDAÇÃO: dbt test verifica qualidade dos dados
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
import random
import uuid
from datetime import date


# ============================================================================
# Função de Extração (simula ingestão de dados de uma fonte externa)
# ============================================================================
def extract_fake_employees(**kwargs):
    """
    Gera dados fake de funcionários e insere na tabela raw_employees.
    No mercado, essa tarefa seria substituída por:
    - Leitura de um arquivo CSV/S3
    - Consulta a uma API externa
    - Replicação de um banco transacional
    """
    import psycopg2

    first_names = [
        "Ana",
        "Carlos",
        "Maria",
        "João",
        "Pedro",
        "Lucia",
        "Rafael",
        "Julia",
        "Marcos",
        "Fernanda",
    ]
    last_names = [
        "Silva",
        "Santos",
        "Oliveira",
        "Souza",
        "Lima",
        "Pereira",
        "Costa",
        "Ferreira",
        "Almeida",
        "Ribeiro",
    ]
    departments = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations"]
    cities = [
        "São Paulo",
        "Rio de Janeiro",
        "Belo Horizonte",
        "Curitiba",
        "Porto Alegre",
    ]

    # Gera entre 5 e 15 registros fake
    num_records = random.randint(5, 15)
    records = []

    for _ in range(num_records):
        records.append(
            {
                "employee_id": str(uuid.uuid4())[:8],
                "first_name": random.choice(first_names),
                "last_name": random.choice(last_names),
                "email": f"{uuid.uuid4().hex[:8]}@empresa.com",
                "department": random.choice(departments),
                "city": random.choice(cities),
                "salary": round(random.uniform(3000, 15000), 2),
                "hire_date": date(
                    random.randint(2018, 2025),
                    random.randint(1, 12),
                    random.randint(1, 28),
                ).isoformat(),
                "extracted_at": datetime.now().isoformat(),
            }
        )

    # Conecta ao PostgreSQL e insere os dados
    conn = psycopg2.connect(
        host="dw", port=5432, dbname="dw", user="dw_user", password="dw_password"
    )
    cur = conn.cursor()

    # Cria a tabela raw se não existir
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_employees (
            employee_id VARCHAR(50),
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            email VARCHAR(200),
            department VARCHAR(100),
            city VARCHAR(100),
            salary NUMERIC(10,2),
            hire_date DATE,
            extracted_at TIMESTAMP
        );
    """)

    # Limpa dados anteriores para evitar duplicatas entre runs
    cur.execute("TRUNCATE TABLE raw_employees;")

    # Insere os registros
    for r in records:
        cur.execute(
            """
            INSERT INTO raw_employees (employee_id, first_name, last_name, email, department, city, salary, hire_date, extracted_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                r["employee_id"],
                r["first_name"],
                r["last_name"],
                r["email"],
                r["department"],
                r["city"],
                r["salary"],
                r["hire_date"],
                r["extracted_at"],
            ),
        )

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ {num_records} registros extraídos e carregados na tabela raw_employees")


# ============================================================================
# Definição da DAG
# ============================================================================
default_args = {
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
}

with DAG(
    dag_id="employee_data_pipeline",
    default_args=default_args,
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["dbt", "employee", "bronze-silver-gold"],
    description="Pipeline completo: extração → bronze → silver → gold",
) as dag:
    # -----------------------------------------------------------------------
    # CAMADA 1: EXTRAÇÃO (Bronze - dados brutos)
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
