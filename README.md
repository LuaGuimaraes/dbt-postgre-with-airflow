# Employee Data Pipeline — Airflow + dbt + PostgreSQL

A complete ELT (Extract, Load, Transform) pipeline that simulates a real-world data engineering workflow using the **Medallion Architecture** (Bronze → Silver → Gold).

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Pipeline Walkthrough](#pipeline-walkthrough)
- [dbt Models](#dbt-models)
- [Data Quality Tests](#data-quality-tests)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Technologies](#technologies)

---

## Overview

This project demonstrates a full data pipeline that:

1. **Extracts** — Generates fake employee data and loads it into a raw table (Bronze layer)
2. **Transforms** — Cleans, standardizes, and models the data using dbt (Silver → Gold layers)
3. **Validates** — Runs 16 data quality tests to ensure correctness

Everything is orchestrated by **Apache Airflow** and runs locally via **Docker Compose**.

---

## Architecture

### High-Level Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   EXTRACTION    │────▶│     BRONZE       │────▶│   SILVER / GOLD  │────▶│    VALIDATION    │
│   (Python)      │     │  raw_employees   │     │      (dbt)       │     │   (dbt test)     │
└─────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DOCKER COMPOSE                                  │
│                                                                         │
│  ┌──────────────┐    ┌───────────────────────────────────────────────┐  │
│  │              │    │              AIRFLOW                          │  │
│  │  PostgreSQL  │    │                                               │  │
│  │   (dw)       │◀──▶│  extract_employees ──▶ dbt_run ──▶ dbt_test  │  │
│  │  :5432       │    │       (Python)        (Bash)     (Bash)      │  │
│  │              │    │                                               │  │
│  │  raw_employees (Bronze)                                           │  │
│  │  stg_employees  (Silver)                                          │  │
│  │  dim_employee   (Gold)                                            │  │
│  │  fct_dept_summary (Gold)                                          │  │
│  └──────────────┘    └───────────────────────────────────────────────┘  │
│                                                                         │
│  Ports: 5000→5432 (PostgreSQL)  |  8080→8080 (Airflow UI)              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed
- Minimum 4GB RAM available for containers

### 1. Start the environment

```bash
docker compose up -d
```

This starts 4 containers:
- **dw** — PostgreSQL 18 (data warehouse)
- **airflow-init** — Database migration + admin user (runs once, then exits)
- **airflow-webserver** — Web UI on `http://localhost:8080`
- **airflow-scheduler** — Detects and triggers DAG runs

> **Wait ~30 seconds** for all services to initialize. The first run builds the Docker image (installs dbt + drivers), which takes a bit longer.

### 2. Access Airflow UI

Open [http://localhost:8080](http://localhost:8080)

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin` |

### 3. Trigger the pipeline

**Via UI:** Click the play button ▶ on `employee_data_pipeline` → **Trigger DAG**

**Via CLI:**
```bash
docker compose exec airflow-scheduler \
  airflow dags trigger employee_data_pipeline
```

### 4. Verify results

```bash
# List all tables created
docker compose exec dw psql -U dw_user -d dw -c "\dt"

# Query transformed data
docker compose exec dw psql -U dw_user -d dw -c "SELECT * FROM stg_employees LIMIT 5;"
docker compose exec dw psql -U dw_user -d dw -c "SELECT * FROM dim_employee LIMIT 5;"
docker compose exec dw psql -U dw_user -d dw -c "SELECT * FROM fct_department_summary;"
```

### 5. Tear down

```bash
# Stop containers (keeps data)
docker compose down

# Stop containers and delete all data
docker compose down -v
```

---

## Pipeline Walkthrough

### Step 1 — Extraction (`extract_fake_employees`)

| Property | Value |
|----------|-------|
| **Operator** | `PythonOperator` |
| **File** | `airflow/dags/extract_employees.py` |
| **What it does** | Generates 5–15 fake employee records and inserts them into `raw_employees` |

The extraction function:
1. Generates random employee data (name, email, department, salary, etc.)
2. Connects to PostgreSQL via `psycopg2`
3. Creates the `raw_employees` table if it doesn't exist
4. Truncates previous data to prevent duplicates between runs
5. Inserts the new records

> **In production**, this step would be replaced by reading from a real source: S3 files, an API, a CDC stream, etc.

### Step 2 — Transformation (`dbt_run`)

| Property | Value |
|----------|-------|
| **Operator** | `BashOperator` |
| **Command** | `cd /opt/airflow/dbt_project && dbt run` |
| **What it does** | Executes all dbt models in dependency order |

dbt reads from `raw_employees` and creates:
- `stg_employees` — cleaned and standardized data
- `dim_employee` — dimensional table with calculated fields
- `fct_department_summary` — aggregated metrics by department
- Plus 4 demo models showing incremental strategies

### Step 3 — Validation (`dbt_test`)

| Property | Value |
|----------|-------|
| **Operator** | `BashOperator` |
| **Command** | `cd /opt/airflow/dbt_project && dbt test` |
| **What it does** | Runs 16 data quality tests |

Tests verify:
- **Uniqueness** — no duplicate IDs or emails
- **Completeness** — no null values in required columns
- **Validity** — department values match the allowed list, salary bands are correct

---

## dbt Models

### Core Models (used by the main pipeline)

| Model | Layer | Materialization | Description |
|-------|-------|-----------------|-------------|
| `stg_employees` | Silver | `table` | Cleans and standardizes `raw_employees` — lowercases names, uppercases departments, casts types, filters nulls |
| `dim_employee` | Gold | `table` | Employee dimension with calculated fields: `full_name`, `years_of_service`, `salary_band` (Junior/Mid/Senior) |
| `fct_department_summary` | Gold | `table` | Department-level aggregations: employee count, avg/min/max salary, avg tenure, cities count |

### Demo Models (incremental strategies)

| Model | Strategy | Description |
|-------|----------|-------------|
| `raw_data_source` | `table` | Static seed data (3 hardcoded records) used as source for demo models |
| `overwrite_insert_strategy` | `delete+insert` | Deletes existing records matching `unique_key`, inserts fresh data |
| `merge_strategy_emp` | `merge` (default) | UPSERT — updates existing records, inserts new ones |
| `incremental_append` | `append` | Only inserts new records (no updates or deletes) |

---

## Data Quality Tests

All tests are defined in `dbt/my_sample_project/models/schema.yml`:

| Model | Column | Test | Purpose |
|-------|--------|------|---------|
| `stg_employees` | `employee_id` | `unique`, `not_null` | Each employee has a unique, non-null ID |
| `stg_employees` | `email` | `unique`, `not_null` | No duplicate or missing emails |
| `stg_employees` | `department` | `not_null`, `accepted_values` | Department is required and must be one of 6 valid values |
| `stg_employees` | `salary` | `not_null` | Salary is required |
| `stg_employees` | `hire_date` | `not_null` | Hire date is required |
| `dim_employee` | `employee_sk` | `unique`, `not_null` | Surrogate key is unique and required |
| `dim_employee` | `full_name` | `not_null` | Full name is required |
| `dim_employee` | `salary_band` | `accepted_values` | Must be Junior, Mid, or Senior |
| `fct_department_summary` | `department` | `unique`, `not_null` | One row per department |
| `fct_department_summary` | `employee_count` | `not_null` | Count is required |
| `fct_department_summary` | `avg_salary` | `not_null` | Average salary is required |

---

## Project Structure

```
├── docker-compose.yaml              # Container orchestration (4 services)
├── .env                             # Environment variables (AIRFLOW_UID)
├── .gitignore                       # Files excluded from version control
│
├── airflow/
│   ├── Dockerfile                   # Custom image: Airflow 2.10.5 + dbt + psycopg2
│   ├── profiles.yml                 # dbt connection config (PostgreSQL credentials)
│   └── dags/
│       ├── employee_data_pipeline.py   # Main DAG: extract → dbt run → dbt test
│       └── extract_employees.py        # Extraction logic (separate module)
│
└── dbt/my_sample_project/
    ├── dbt_project.yml              # dbt project configuration
    └── models/
        ├── sources.yml              # External data source definitions
        ├── schema.yml               # Data quality tests per column
        ├── source/
        │   └── raw_data_source.sql     # Static seed data (demo)
        ├── staging/
        │   ├── stg_employees.sql       # Silver layer: clean raw_employees
        │   ├── overwrite_insert_strategy.sql  # Demo: delete+insert
        │   └── merge_strategy_emp.sql       # Demo: merge/UPSERT
        └── mart/
            ├── dim_employee.sql          # Gold: employee dimension
            ├── fct_department_summary.sql # Gold: department metrics
            └── incremental_append.sql    # Demo: append-only incremental
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AIRFLOW_UID` | `50000` | User ID for Airflow containers (fixes permission issues on Linux) |

### Service Ports

| Service | Host Port | Container Port | Purpose |
|---------|-----------|----------------|---------|
| PostgreSQL | `5000` | `5432` | Data warehouse — connect with any SQL client |
| Airflow UI | `8080` | `8080` | Web dashboard for monitoring and triggering DAGs |

### Credentials

| Service | Host | User | Password | Database |
|---------|------|------|----------|----------|
| **PostgreSQL** | `localhost:5000` | `dw_user` | `dw_password` | `dw` |
| **Airflow UI** | `localhost:8080` | `admin` | `admin` | — |

### dbt Profile

Defined in `airflow/profiles.yml`:

```yaml
my_sample_project:
  target: dev
  outputs:
    dev:
      type: postgres
      host: dw
      user: dw_user
      password: dw_password
      port: 5432
      dbname: dw
      schema: public
      threads: 4
```

> **Production note:** Never store passwords in plain text. Use environment variables, AWS Secrets Manager, HashiCorp Vault, or similar.

---

## Troubleshooting

### PostgreSQL won't start

The PostgreSQL 18 image requires the volume to be mounted at `/var/lib/postgresql` (not `/var/lib/postgresql/data`). If you see errors about `pg_type_typname_nsp_index`, clean up and restart:

```bash
docker compose down -v && docker compose up -d
```

### Airflow webserver shows "database not initialized"

The webserver started before `airflow-init` finished. The `docker-compose.yaml` uses `depends_on` with conditions to prevent this, but if it happens:

```bash
docker compose down -v && docker compose up -d
```

### DAG tasks fail with "duplicate key" or "up_for_retry"

This happens when two DAG runs execute simultaneously. The DAG is configured with `max_active_runs=1` and `schedule=None` to prevent this. If you see it, clear old runs:

```bash
docker compose exec airflow-scheduler \
  airflow dags delete employee_data_pipeline -y
```

Then trigger a fresh run.

### dbt tests fail

Common causes:
- **Department test fails** — data from previous runs accumulated. The `TRUNCATE` in `extract_employees.py` prevents this.
- **Email uniqueness fails** — random name combinations can collide. The fix uses UUIDs for emails.

### View container logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f dw
docker compose logs -f airflow-webserver
docker compose logs -f airflow-scheduler
```

---

## Technologies

| Technology | Version | Role |
|------------|---------|------|
| **PostgreSQL** | 18 | Data warehouse — stores raw and transformed data |
| **Apache Airflow** | 2.10.5 | Pipeline orchestration — schedules, monitors, retries |
| **dbt (data build tool)** | 1.11.7 | Data transformation — SQL-based models and tests |
| **dbt-postgres** | 1.10.0 | PostgreSQL adapter for dbt |
| **psycopg2** | binary | Python PostgreSQL driver (used in extraction) |
| **Docker Compose** | — | Local development environment |

---

## License

Educational project — free to use and modify.
