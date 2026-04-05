# DBT + Airflow + PostgreSQL — Employee Data Pipeline

Projeto educacional que simula um pipeline ELT completo de dados, usando a arquitetura **Medalhão** (Bronze → Silver → Gold).

## O que este projeto faz

Gera dados fake de funcionários, carrega num banco PostgreSQL, transforma com dbt e valida a qualidade — tudo orquestrado pelo Apache Airflow.

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  EXTRAÇÃO   │────▶│   BRONZE     │────▶│  SILVER/GOLD│────▶│  VALIDAÇÃO   │
│  (Python)   │     │ raw_employees│     │   (dbt)     │     │  (dbt test)  │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
```

## Como rodar

```bash
# 1. Subir todos os containers (PostgreSQL + Airflow)
docker compose up -d

# 2. Aguardar o Airflow iniciar (~30 segundos)
#    Acesse: http://localhost:8080 (admin / admin)

# 3. Disparar a DAG manualmente pela UI ou via CLI:
docker compose exec airflow-scheduler \
  airflow dags trigger employee_data_pipeline

# 4. Verificar tabelas criadas no PostgreSQL:
docker compose exec dw psql -U dw_user -d dw -c "\dt"

# 5. Consultar dados transformados:
docker compose exec dw psql -U dw_user -d dw -c "SELECT * FROM stg_employees;"
docker compose exec dw psql -U dw_user -d dw -c "SELECT * FROM dim_employee;"
docker compose exec dw psql -U dw_user -d dw -c "SELECT * FROM fct_department_summary;"

# 6. Parar e limpar tudo:
docker compose down -v
```

## Pipeline: employee_data_pipeline

| Etapa | Task | Tipo | O que faz |
|-------|------|------|-----------|
| 1. Extração | `extract_fake_employees` | PythonOperator | Gera 5-15 registros fake, cria tabela `raw_employees` e insere os dados |
| 2. Transformação | `dbt_run` | BashOperator | Executa `dbt run` — transforma Bronze → Silver → Gold |
| 3. Validação | `dbt_test` | BashOperator | Executa `dbt test` — 16 testes de qualidade (unique, not_null, accepted_values) |

## Models dbt

| Model | Camada | Materialização | Descrição |
|-------|--------|----------------|-----------|
| `raw_data_source` | Source | table | Dados hardcoded de exemplo (3 registros) |
| `stg_employees` | Staging (Silver) | table | Limpa e padroniza `raw_employees` |
| `dim_employee` | Mart (Gold) | table | Dimensão dimensional com colunas calculadas |
| `fct_department_summary` | Mart (Gold) | table | Métricas agregadas por departamento |
| `overwrite_insert_strategy` | Staging | incremental | Demo: estratégia delete+insert |
| `merge_strategy_emp` | Staging | incremental | Demo: estratégia merge/UPSERT |
| `incremental_append` | Mart | incremental | Demo: estratégia append-only |

## Estrutura de arquivos

```
├── docker-compose.yaml          # Orquestração dos 4 containers
├── .env                         # Variáveis de ambiente (AIRFLOW_UID)
├── airflow/
│   ├── Dockerfile               # Imagem custom: Airflow + dbt + psycopg2
│   ├── profiles.yml             # Config de conexão do dbt com PostgreSQL
│   ├── dags/
│   │   └── employee_data_pipeline.py   # DAG principal (extração → dbt → testes)
│   └── logs/                    # Logs de execução das tasks
└── dbt/my_sample_project/
    ├── dbt_project.yml          # Config central do dbt
    └── models/
        ├── sources.yml          # Definição das fontes externas
        ├── schema.yml           # Testes de qualidade por coluna
        ├── source/              # Models de dados estáticos
        ├── staging/             # Camada Silver (limpeza)
        └── mart/                # Camada Gold (consumo)
```

## Arquitetura Medalhão

| Camada | Pasta | O que faz |
|--------|-------|-----------|
| **Bronze** | `raw_employees` (tabela) | Dados brutos da ingestão, sem transformação |
| **Silver** | `models/staging/` | Limpeza, padronização, conversão de tipos, filtros |
| **Gold** | `models/mart/` | Tabelas dimensionais e fatos prontos para BI |

## Credenciais

| Serviço | Acesso |
|---------|--------|
| **Airflow UI** | http://localhost:8080 — user: `admin` / pass: `admin` |
| **PostgreSQL** | localhost:5000 — user: `dw_user` / pass: `dw_password` / db: `dw` |

## Tecnologias

- **PostgreSQL 18** — Data Warehouse
- **Apache Airflow 2.10.5** — Orquestração de pipelines
- **dbt 1.11.7** — Transformação de dados (ELT)
- **Docker Compose** — Ambiente local de desenvolvimento
