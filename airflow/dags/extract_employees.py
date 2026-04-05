"""
extract_employees.py — Script de extração de dados de funcionários

Gera dados fake e carrega na tabela raw_employees do PostgreSQL.
No mercado, esse script seria substituído por:
  - Leitura de um arquivo CSV/S3
  - Consulta a uma API externa
  - Replicação de um banco transacional (CDC)

É chamado pelo Airflow via PythonOperator na DAG employee_data_pipeline.
"""

import random
import uuid
from datetime import date, datetime


def extract_fake_employees(**kwargs):
    """
    Gera dados fake de funcionários e insere na tabela raw_employees.

    Passo a passo:
      1. Gera entre 5 e 15 registros com dados aleatórios
      2. Conecta ao PostgreSQL
      3. Cria a tabela se não existir
      4. Limpa dados anteriores (TRUNCATE) para evitar duplicatas entre runs
      5. Insere os novos registros
    """
    import psycopg2

    # ========================================================================
    # Dados de exemplo (pools para escolha aleatória)
    # ========================================================================
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

    # ========================================================================
    # Gera registros aleatórios
    # ========================================================================
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

    # ========================================================================
    # Conecta ao PostgreSQL e carrega os dados
    # ========================================================================
    conn = psycopg2.connect(
        host="dw",
        port=5432,
        dbname="dw",
        user="dw_user",
        password="dw_password",
    )
    cur = conn.cursor()

    # Cria a tabela se não existir (camada Bronze)
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

    # Limpa dados anteriores para evitar duplicatas entre execuções
    cur.execute("TRUNCATE TABLE raw_employees;")

    # Insere os registros
    for r in records:
        cur.execute(
            """
            INSERT INTO raw_employees
                (employee_id, first_name, last_name, email, department,
                 city, salary, hire_date, extracted_at)
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
