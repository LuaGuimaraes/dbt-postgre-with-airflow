# DBT - Data Build Tool

## O que é o DBT?

DBT é a camada de **Transformação** (o "T" do ELT). Ele não ingere dados — transforma dados que já estão no warehouse.

## Arquitetura Medalhão no DBT

| Camada | Pasta | O que faz |
|---|---|---|
| **Bronze** | `models/staging/` | Dados crus da fonte, limpeza básica, padronização de tipos, renomeação |
| **Silver** | `models/intermediate/` | Junções, deduplicação, regras de negócio, modelagem dimensional |
| **Gold** | `models/mart/` | Tabelas prontas para consumo, métricas, agregações |

## Onde fica cada coisa

- **Staging** — normalização, conversão de tipos, padronização de nomes, filtros básicos. Uma tabela fonte → um model staging.
- **Dimensões e Fatos** — ficam em `models/intermediate/` (ou `models/silver/`). É onde você faz joins, cria chaves surrogate, aplica regras de negócio.
- **Marts** — tabelas finais para BI/análise. Agregações, métricas calculadas, vistas denormalizadas prontas pro consumidor.

## Tabela Receptora (Landing/Bronze)

Não é criada pelo dbt. Ela vem do processo de ingestão (Airflow, Fivetran, etc). O dbt lê dela via `source()` e transforma.

## Configurações dos Models

### `alias`

Define o nome da tabela no banco. Sem ele, o dbt usa o nome do arquivo `.sql`.

```sql
{{ config(materialized='table', alias='minha_tabela') }}
```

### `materialized` — Tipos

| Tipo | O que faz |
|---|---|
| `view` | Cria uma view (padrão) |
| `table` | Cria tabela física, recria toda vez |
| `incremental` | Insere/atualiza só dados novos (precisa de `unique_key`) |
| `ephemeral` | Não cria tabela, funciona como CTE reutilizável |
