# Employee Data Pipeline — Airflow + dbt + PostgreSQL

Pipeline ELT completo que simula um fluxo real de engenharia de dados usando a **Arquitetura Medalhão** (Bronze → Silver → Gold).

---

## Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Como Rodar](#como-rodar)
- [Detalhamento do Pipeline](#detalhamento-do-pipeline)
- [Modelos dbt](#modelos-dbT)
- [Capturas de Tela](#capturas-de-tela)
- [Testes de Qualidade](#testes-de-qualidade-de-dados)
- [Estrutura de Arquivos](#estrutura-de-arquivos)
- [Configuração](#configuração)
- [Solução de Problemas](#solução-de-problemas)
- [Tecnologias](#tecnologias)
- [English Version](#english-version)

---

## Visão Geral

Este projeto demonstra um pipeline completo de dados que:

1. **Extrai** — Gera dados fake de funcionários e carrega numa tabela bruta (camada Bronze)
2. **Transforma** — Limpa, padroniza e modela os dados com dbt (camadas Silver → Gold)
3. **Valida** — Executa 16 testes de qualidade de dados

Tudo é orquestrado pelo **Apache Airflow** e roda localmente via **Docker Compose**.

> Você **não precisa** ter Python, dbt ou PostgreSQL instalados na sua máquina. Tudo roda dentro de containers Docker. Basta ter o Docker instalado.
>
> 💡 **Sobre este projeto:** Este repositório é uma demonstração educacional que construí para consolidar meus conhecimentos em engenharia de dados. Ele simula um pipeline real de mercado, mas com dados fictícios. O objetivo é demonstrar que entendo a arquitetura, as ferramentas e — principalmente — sei explicar o porquê de cada decisão técnica.

---

## Arquitetura

### Fluxo Geral

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   EXTRAÇÃO      │────▶│     BRONZE       │────▶│   SILVER / GOLD  │────▶│    VALIDAÇÃO     │
│   (Python)      │     │  raw_employees   │     │      (dbt)       │     │   (dbt test)     │
└─────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘
```

### Diagrama de Componentes

![Architecture Diagram](images/architecture.png)

> O arquivo `architecture.drawio` pode ser aberto e editado em [app.diagrams.net](https://app.diagrams.net).

---

## Como Rodar

### Pré-requisitos

| Requisito | Por quê |
|-----------|---------|
| [Docker](https://docs.docker.com/get-docker/) + [Docker Compose](https://docs.docker.com/compose/install/) | Roda todos os serviços em containers |
| Mínimo 4GB de RAM | Airflow + PostgreSQL precisam de memória |
| Terminal | Para rodar os comandos Docker |

### 1. Subir os containers

```bash
docker compose up -d
```

Isso inicia 4 containers:

| Container | Função |
|-----------|--------|
| **dw** | PostgreSQL 18 (data warehouse) |
| **airflow-init** | Migração do banco + criação do usuário admin (roda uma vez e encerra) |
| **airflow-webserver** | Interface web em `http://localhost:8080` |
| **airflow-scheduler** | Detecta e dispara execuções das DAGs |

> ⏳ Aguarde ~30 segundos para tudo inicializar. Na primeira vez demora mais porque o Docker constrói a imagem (instala dbt + drivers).

### 2. Acessar a interface do Airflow

Abra [http://localhost:8080](http://localhost:8080) no navegador.

| Campo | Valor |
|-------|-------|
| Usuário | `admin` |
| Senha | `admin` |

### 3. Disparar o pipeline

**Pela interface:** Clique no botão ▶ da DAG `employee_data_pipeline` → **Trigger DAG**

**Pelo terminal:**
```bash
docker compose exec airflow-scheduler \
  airflow dags trigger employee_data_pipeline
```

### 4. Verificar resultados

```bash
# Listar todas as tabelas criadas
docker compose exec dw psql -U dw_user -d dw -c "\dt"

# Consultar dados transformados
docker compose exec dw psql -U dw_user -d dw -c "SELECT * FROM stg_employees LIMIT 5;"
docker compose exec dw psql -U dw_user -d dw -c "SELECT * FROM dim_employee;"
docker compose exec dw psql -U dw_user -d dw -c "SELECT * FROM fct_department_summary;"

# Rodar testes dbt manualmente
docker compose exec airflow-scheduler \
  bash -c "cd /opt/airflow/dbt_project && dbt test"
```

### 5. Parar tudo

```bash
# Parar containers (mantém os dados)
docker compose down

# Parar e apagar tudo (dados incluídos)
docker compose down -v
```

---

## Detalhamento do Pipeline

### Etapa 1 — Extração (`extract_fake_employees`)

| Propriedade | Valor |
|-------------|-------|
| **Operador** | `PythonOperator` |
| **Arquivo** | `airflow/dags/extract_employees.py` |
| **O que faz** | Gera 5–15 registros fake de funcionários e insere na tabela `raw_employees` |

A função de extração:
1. Gera dados aleatórios (nome, email, departamento, salário, etc.)
2. Conecta ao PostgreSQL via `psycopg2`
3. Cria a tabela `raw_employees` se não existir
4. Limpa dados anteriores (`TRUNCATE`) para evitar duplicatas entre execuções
5. Insere os novos registros

> **Em produção**, esta etapa seria substituída pela leitura de uma fonte real: arquivos S3, uma API externa, replicação de banco transacional (CDC), etc. O código de extração que escrevi aqui simula esse comportamento de forma simplificada para fins didáticos.

### Etapa 2 — Transformação (`dbt_run`)

| Propriedade | Valor |
|-------------|-------|
| **Operador** | `BashOperator` |
| **Comando** | `cd /opt/airflow/dbt_project && dbt run` |
| **O que faz** | Executa todos os modelos dbt na ordem de dependência |

O dbt lê de `raw_employees` e cria:
- `stg_employees` — dados limpos e padronizados
- `dim_employee` — tabela dimensional com colunas calculadas
- `fct_department_summary` — métricas agregadas por departamento

### Etapa 3 — Validação (`dbt_test`)

| Propriedade | Valor |
|-------------|-------|
| **Operador** | `BashOperator` |
| **Comando** | `cd /opt/airflow/dbt_project && dbt test` |
| **O que faz** | Executa 16 testes de qualidade de dados |

Os testes verificam:
- **Unicidade** — sem IDs ou emails duplicados
- **Completude** — sem valores nulos em colunas obrigatórias
- **Validade** — departamentos correspondem à lista permitida, faixas salariais corretas

---

## Modelos dbt

### Modelos Principais (usados pelo pipeline)

| Modelo | Camada | Materialização | Descrição |
|--------|--------|----------------|-----------|
| `stg_employees` | Silver | `table` | Limpa e padroniza `raw_employees` |
| `dim_employee` | Gold | `table` | Dimensão de funcionários com colunas calculadas: `full_name`, `years_of_service`, `salary_band` |
| `fct_department_summary` | Gold | `table` | Agregações por departamento: contagem, salário médio/mín/máx, tempo médio de casa |

### Modelos de Demonstração (estratégias incrementais)

| Modelo | Estratégia | Descrição |
|--------|------------|-----------|
| `raw_data_source` | `table` | Dados estáticos (3 registros hardcoded) |
| `overwrite_insert_strategy` | `delete+insert` | Deleta registros existentes, insere novos |
| `merge_strategy_emp` | `merge` | UPSERT — atualiza existentes, insere novos |
| `incremental_append` | `append` | Apenas insere registros novos |

---

## Capturas de Tela

### 1. Visão Gráfica da DAG

![DAG Graph View](images/01-dag-graph-view.png)

A DAG mostra 3 tarefas conectadas em sequência: extrair → transformar → validar.

### 2. Execução Bem-Sucedida

![DAG Run Success](images/02-dag-run-success.png)

Todas as 3 tarefas foram concluídas com sucesso (verde). O pipeline rodou do início ao fim sem erros.

### 3. Resultados dos Testes dbt

![dbt Test Results](images/03-dbt-test-results.png)

Todos os 16 testes de qualidade de dados passaram: **16/16 PASS**. Sem avisos, sem erros.

### 4. Tabelas no PostgreSQL

![PostgreSQL Tables](images/04-postgresql-tables.png)

Todas as tabelas do pipeline foram criadas: `raw_employees`, `stg_employees`, `dim_employee`, `fct_department_summary`, mais os modelos de demonstração.

### 5. Saída da Dimensão de Funcionários

![dim_employee Output](images/05-dim-employee-output.png)

A tabela Gold `dim_employee` com colunas calculadas: `full_name`, `years_of_service`, `salary_band` (Junior/Mid/Senior).

### 6. Saída do Resumo por Departamento

![fct_department_summary Output](images/06-fct-department-summary.png)

Métricas agregadas por departamento: contagem de funcionários, salário médio/mínimo/máximo, tempo médio de casa, quantidade de cidades.

---

## Testes de Qualidade de Dados

Todos os testes estão definidos em `dbt/my_sample_project/models/schema.yml`:

| Modelo | Coluna | Teste | Propósito |
|--------|--------|-------|-----------|
| `stg_employees` | `employee_id` | `unique`, `not_null` | Cada funcionário tem ID único e obrigatório |
| `stg_employees` | `email` | `unique`, `not_null` | Sem emails duplicados ou ausentes |
| `stg_employees` | `department` | `not_null`, `accepted_values` | Departamento obrigatório, deve ser um dos 6 válidos |
| `stg_employees` | `salary` | `not_null` | Salário obrigatório |
| `stg_employees` | `hire_date` | `not_null` | Data de admissão obrigatória |
| `dim_employee` | `employee_sk` | `unique`, `not_null` | Chave substituta única e obrigatória |
| `dim_employee` | `full_name` | `not_null` | Nome completo obrigatório |
| `dim_employee` | `salary_band` | `accepted_values` | Deve ser Junior, Mid ou Senior |
| `fct_department_summary` | `department` | `unique`, `not_null` | Um registro por departamento |
| `fct_department_summary` | `employee_count` | `not_null` | Contagem obrigatória |
| `fct_department_summary` | `avg_salary` | `not_null` | Média salarial obrigatória |

---

## Estrutura de Arquivos

```
├── docker-compose.yaml              # Orquestração dos 4 containers
├── .env                             # Variáveis de ambiente (AIRFLOW_UID)
├── .gitignore                       # Arquivos excluídos do versionamento
├── architecture.drawio              # Diagrama de arquitetura (abrir no diagrams.net)
│
├── airflow/
│   ├── Dockerfile                   # Imagem custom: Airflow 2.10.5 + dbt + psycopg2
│   ├── profiles.yml                 # Config de conexão do dbt com PostgreSQL
│   └── dags/
│       ├── employee_data_pipeline.py   # DAG principal: extração → dbt run → dbt test
│       └── extract_employees.py        # Lógica de extração (módulo separado)
│
├── dbt/my_sample_project/
│   ├── dbt_project.yml              # Configuração central do dbt
│   └── models/
│       ├── sources.yml              # Definição das fontes externas
│       ├── schema.yml               # Testes de qualidade por coluna
│       ├── source/
│       │   └── raw_data_source.sql     # Dados estáticos (demo)
│       ├── staging/
│       │   ├── stg_employees.sql       # Camada Silver: limpa raw_employees
│       │   ├── overwrite_insert_strategy.sql  # Demo: delete+insert
│       │   └── merge_strategy_emp.sql       # Demo: merge/UPSERT
│       └── mart/
│           ├── dim_employee.sql          # Gold: dimensão de funcionários
│           ├── fct_department_summary.sql # Gold: métricas por departamento
│           └── incremental_append.sql    # Demo: append-only incremental
│
└── images/                          # Capturas de tela para documentação
    ├── architecture.png
    ├── 01-dag-graph-view.png
    ├── 02-dag-run-success.png
    ├── 03-dbt-test-results.png
    ├── 04-postgresql-tables.png
    ├── 05-dim-employee-output.png
    └── 06-fct-department-summary.png
```

---

## Configuração

### Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `AIRFLOW_UID` | `50000` | ID do usuário nos containers Airflow (corrige permissões no Linux) |

### Portas dos Serviços

| Serviço | Porta Local | Porta do Container | Finalidade |
|---------|-------------|--------------------|------------|
| PostgreSQL | `5000` | `5432` | Data warehouse — conecte com qualquer cliente SQL |
| Airflow UI | `8080` | `8080` | Dashboard web para monitorar e disparar DAGs |

### Credenciais

| Serviço | Host | Usuário | Senha | Banco |
|---------|------|---------|-------|-------|
| **PostgreSQL** | `localhost:5000` | `dw_user` | `dw_password` | `dw` |
| **Airflow UI** | `localhost:8080` | `admin` | `admin` | — |

### Profile do dbt

Definido em `airflow/profiles.yml`:

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

> ⚠️ **Nota sobre segurança:** Este repositório é uma demonstração educacional. As credenciais estão expostas apenas para facilitar a execução local. **Em um ambiente real, eu jamais armazenaria senhas em texto puro** — utilizaria variáveis de ambiente, AWS Secrets Manager, HashiCorp Vault ou solução equivalente.

---

## Solução de Problemas

### PostgreSQL não inicia

A imagem do PostgreSQL 18 requer o volume montado em `/var/lib/postgresql` (não `/var/lib/postgresql/data`). Se aparecerem erros sobre `pg_type_typname_nsp_index`, limpe e reinicie:

```bash
docker compose down -v && docker compose up -d
```

### Webserver mostra "banco não inicializado"

O webserver iniciou antes do `airflow-init` terminar. O `docker-compose.yaml` usa `depends_on` com condições para prevenir isso, mas se acontecer:

```bash
docker compose down -v && docker compose up -d
```

### Tarefas da DAG falham

Isso pode acontecer quando duas execuções da DAG rodam ao mesmo tempo. A DAG está configurada com `max_active_runs=1` e `schedule=None` para prevenir. Se acontecer, limpe execuções antigas:

```bash
docker compose exec airflow-scheduler \
  airflow dags delete employee_data_pipeline -y
```

Depois dispare uma nova execução.

### Testes dbt falham

Causas comuns:
- **Teste de departamento falha** — dados de execuções anteriores acumularam. O `TRUNCATE` no `extract_employees.py` previne isso.
- **Unicidade de email falha** — combinações aleatórias de nomes podem colidir. A correção usa UUIDs para emails.

### Ver logs dos containers

```bash
# Todos os serviços
docker compose logs -f

# Serviço específico
docker compose logs -f dw
docker compose logs -f airflow-webserver
docker compose logs -f airflow-scheduler
```

---

## Tecnologias

| Tecnologia | Versão | Função |
|------------|--------|--------|
| **PostgreSQL** | 18 | Data warehouse — armazena dados brutos e transformados |
| **Apache Airflow** | 2.10.5 | Orquestração de pipelines — agenda, monitora, retenta |
| **dbt (data build tool)** | 1.11.7 | Transformação de dados — modelos e testes em SQL |
| **dbt-postgres** | 1.10.0 | Adapter PostgreSQL para o dbt |
| **psycopg2** | binary | Driver Python para PostgreSQL (usado na extração) |
| **Docker Compose** | — | Ambiente local de desenvolvimento |

---

## Licença

Projeto educacional — livre para uso e modificação.

---
---

# English Version

## Overview

This project demonstrates a full data pipeline that:

1. **Extracts** — Generates fake employee data and loads it into a raw table (Bronze layer)
2. **Transforms** — Cleans, standardizes, and models the data using dbt (Silver → Gold layers)
3. **Validates** — Runs 16 data quality tests to ensure correctness

Everything is orchestrated by **Apache Airflow** and runs locally via **Docker Compose**.

> You **do not need** Python, dbt, or PostgreSQL installed locally. Everything runs inside Docker containers. Just have Docker installed.
>
> 💡 **About this project:** This repository is an educational demo I built to solidify my data engineering skills. It simulates a real-world production pipeline but with fake data. The goal is to demonstrate that I understand the architecture, the tools, and — most importantly — that I can explain the reasoning behind every technical decision.

## Architecture

### High-Level Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   EXTRACTION    │────▶│     BRONZE       │────▶│   SILVER / GOLD  │────▶│    VALIDATION    │
│   (Python)      │     │  raw_employees   │     │      (dbt)       │     │   (dbt test)     │
└─────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘
```

### Component Diagram

![Architecture Diagram](images/architecture.png)

> Open `architecture.drawio` in [app.diagrams.net](https://app.diagrams.net) to view/edit the vector diagram.

## Quick Start

### Prerequisites

| Requirement | Why |
|-------------|-----|
| [Docker](https://docs.docker.com/get-docker/) + [Docker Compose](https://docs.docker.com/compose/install/) | Runs all services in containers |
| Minimum 4GB RAM | Airflow + PostgreSQL need memory |
| Terminal access | To run Docker commands |

### 1. Start the environment

```bash
docker compose up -d
```

This starts 4 containers:

| Container | Purpose |
|-----------|---------|
| **dw** | PostgreSQL 18 (data warehouse) |
| **airflow-init** | DB migration + admin user (runs once, then exits) |
| **airflow-webserver** | Web UI on `http://localhost:8080` |
| **airflow-scheduler** | Detects and triggers DAG runs |

> ⏳ Wait ~30 seconds for all services to initialize. The first run takes longer because Docker builds the image (installs dbt + drivers).

### 2. Access Airflow UI

Open [http://localhost:8080](http://localhost:8080) in your browser.

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
docker compose exec dw psql -U dw_user -d dw -c "SELECT * FROM dim_employee;"
docker compose exec dw psql -U dw_user -d dw -c "SELECT * FROM fct_department_summary;"

# Run dbt tests manually
docker compose exec airflow-scheduler \
  bash -c "cd /opt/airflow/dbt_project && dbt test"
```

### 5. Tear down

```bash
# Stop containers (keeps data)
docker compose down

# Stop containers and delete all data
docker compose down -v
```

## Pipeline Walkthrough

### Step 1 — Extraction (`extract_fake_employees`)

| Property | Value |
|----------|-------|
| **Operator** | `PythonOperator` |
| **File** | `airflow/dags/extract_employees.py` |
| **What it does** | Generates 5–15 fake employee records and inserts them into `raw_employees` |

> **In production**, this step would be replaced by reading from a real source: S3 files, an API, a CDC stream, etc. The extraction code I wrote here simulates this behavior in a simplified way for educational purposes.

### Step 2 — Transformation (`dbt_run`)

| Property | Value |
|----------|-------|
| **Operator** | `BashOperator` |
| **Command** | `cd /opt/airflow/dbt_project && dbt run` |
| **What it does** | Executes all dbt models in dependency order |

### Step 3 — Validation (`dbt_test`)

| Property | Value |
|----------|-------|
| **Operator** | `BashOperator` |
| **Command** | `cd /opt/airflow/dbt_project && dbt test` |
| **What it does** | Runs 16 data quality tests |

## dbt Models

### Core Models

| Model | Layer | Materialization | Description |
|-------|-------|-----------------|-------------|
| `stg_employees` | Silver | `table` | Cleans and standardizes `raw_employees` |
| `dim_employee` | Gold | `table` | Employee dimension with calculated fields |
| `fct_department_summary` | Gold | `table` | Department-level aggregations |

### Demo Models (incremental strategies)

| Model | Strategy | Description |
|-------|----------|-------------|
| `raw_data_source` | `table` | Static seed data (3 hardcoded records) |
| `overwrite_insert_strategy` | `delete+insert` | Deletes existing records, inserts fresh data |
| `merge_strategy_emp` | `merge` | UPSERT — updates existing, inserts new |
| `incremental_append` | `append` | Only inserts new records |

## Configuration

### Service Ports

| Service | Host Port | Container Port | Purpose |
|---------|-----------|----------------|---------|
| PostgreSQL | `5000` | `5432` | Data warehouse |
| Airflow UI | `8080` | `8080` | Web dashboard |

### Credentials

| Service | Host | User | Password | Database |
|---------|------|------|----------|----------|
| **PostgreSQL** | `localhost:5000` | `dw_user` | `dw_password` | `dw` |
| **Airflow UI** | `localhost:8080` | `admin` | `admin` | — |

> ⚠️ **Security note:** This repository is an educational demo. Credentials are exposed only to make local setup easier. **In a real environment, I would never store passwords in plain text** — I would use environment variables, AWS Secrets Manager, HashiCorp Vault, or an equivalent solution.

## Troubleshooting

### PostgreSQL won't start

The PostgreSQL 18 image requires the volume at `/var/lib/postgresql`. If you see `pg_type_typname_nsp_index` errors:

```bash
docker compose down -v && docker compose up -d
```

### DAG tasks fail

Clear old runs and trigger fresh:

```bash
docker compose exec airflow-scheduler \
  airflow dags delete employee_data_pipeline -y
```

### View container logs

```bash
docker compose logs -f
docker compose logs -f dw
docker compose logs -f airflow-webserver
docker compose logs -f airflow-scheduler
```

## Technologies

| Technology | Version | Role |
|------------|---------|------|
| **PostgreSQL** | 18 | Data warehouse |
| **Apache Airflow** | 2.10.5 | Pipeline orchestration |
| **dbt** | 1.11.7 | Data transformation (SQL-based) |
| **Docker Compose** | — | Local development environment |

---

Educational project — free to use and modify.
