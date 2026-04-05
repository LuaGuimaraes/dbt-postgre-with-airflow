# Airflow e dbT — Explicação do Zero

## O que é o Airflow?

Pensa num **chef de cozinha** que coordena uma receita complexa.

```
Receita: Bolo de Chocolate

Passo 1: Pré-aquecer o forno
Passo 2: Misturar ingredientes secos
Passo 3: Misturar ingredientes líquidos  
Passo 4: Juntar tudo e assar
Passo 5: Fazer a cobertura
Passo 6: Cobrir o bolo
```

O Airflow é esse chef. Ele:
- **Sabe a ordem** dos passos (Passo 4 só depois do 1, 2 e 3)
- **Retenta** se algo dá errado (o forno esfriou? liga de novo)
- **Avisa** quando termina (ou quando falha)
- **Agenda** (todo dia às 8h faz o bolo)

**Importante:** O Airflow não "roda" o código de verdade. Ele **agenda e orquestra**. Quem executa de fato é o worker/container. Pensa num **maestro de orquestra**: ele não toca os instrumentos, só diz quando cada um entra.

---

## O que é uma DAG?

**DAG = Directed Acyclic Graph** = nome chique pra "lista de tarefas com ordem"

- **Directed** = tem direção (seta apontando pra frente)
- **Acyclic** = não volta (não tem loop infinito)
- **Graph** = é um desenho com caixinhas e setinhas

```
Tarefa A  ──▶  Tarefa B  ──▶  Tarefa C
                  │
                  ▼
              Tarefa D
```

No seu projeto:

```
extract_fake_employees  ──▶  dbt_run  ──▶  dbt_test
```

Só isso. Uma DAG é só "faça isso, depois aquilo, depois aquilo outro".

---

## Operadores — Os "Tipos de Tarefa"

Um **operador** é só um **tipo de coisa que o Airflow sabe fazer**.

Pensa assim: na cozinha, o chef tem ferramentas diferentes:
- **Faca** = corta coisas
- **Forno** = assa coisas
- **Batedeira** = mistura coisas

Cada ferramenta faz UMA coisa específica. Operador é a mesma coisa.

### Os que você já usou:

#### 1. `PythonOperator` — "rode essa função Python"

```python
def extrair_dados():
    # conecta no banco, insere dados, etc
    print("dados extraídos!")

extract_data = PythonOperator(
    task_id="extrair",
    python_callable=extrair_dados,  # ← a função que vai rodar
)
```

**Tradução:** "Airflow, quando chegar nessa tarefa, chama essa função Python."

#### 2. `BashOperator` — "rode esse comando de terminal"

```python
dbt_run = BashOperator(
    task_id="rodar_dbt",
    bash_command="cd /opt/airflow/dbt_project && dbt run",
)
```

**Tradução:** "Airflow, abre um terminal e digita esse comando."

É como se você abrisse o terminal e colasse o texto. Só isso.

### Outros operadores comuns:

#### 3. `PostgresOperator` — "rode esse SQL"

```python
criar_tabela = PostgresOperator(
    task_id="criar_tabela",
    postgres_conn_id="meu_banco",
    sql="CREATE TABLE IF NOT EXISTS clientes (id INT, nome TEXT);",
)
```

**Tradução:** "Airflow, conecta nesse banco e roda esse SQL."

#### 4. `S3Operator` — "pega/sobe arquivo do S3"

```python
baixar_arquivo = S3ToLocalOperator(
    task_id="baixar_csv",
    s3_bucket="meus-dados",
    s3_key="raw/clientes.csv",
    local_path="/tmp/clientes.csv",
)
```

**Tradução:** "Airflow, pega esse arquivo do S3 e salva aqui."

#### 5. `DockerOperator` — "roda esse container"

```python
rodar_script = DockerOperator(
    task_id="processar_dados",
    image="python:3.12",
    command="python /scripts/processa.py",
)
```

**Tradução:** "Airflow, sobe esse container Docker e roda esse comando dentro dele."

---

## A estrutura básica de QUALQUER operador:

```python
nome_da_tarefa = NomeDoOperador(
    task_id="nome_unico",        # ← obrigatório: nome da tarefa
    parametro1="valor",          # ← específico de cada operador
    parametro2="valor",
    retries=3,                   # ← opcional: tenta 3x se falhar
    retry_delay=timedelta(minutes=5),  # ← espera 5 min entre tentativas
)
```

**Todo operador tem `task_id`.** É o nome da caixinha no desenho da DAG.

---

## Como ligar as tarefas (as setinhas):

```python
tarefa_a >> tarefa_b >> tarefa_c     # A → B → C (sequencial)

tarefa_a >> [tarefa_b, tarefa_c]     # A → B e A → C (paralelo)

tarefa_a >> tarefa_b
tarefa_a >> tarefa_c                 # mesma coisa, escrito diferente
```

O `>>` é só uma seta. Significa "depois de".

---

## Decoradores — A forma "moderna" de escrever

Aqui é onde confunde muita gente. Vou explicar devagar.

### O que é um decorador?

Um decorador é um **envelope** que você coloca em volta de uma função. Ele muda como a função se comporta sem mudar o código dela.

```python
@meu_decorador
def minha_funcao():
    print("olá")
```

É a mesma coisa que:

```python
def minha_funcao():
    print("olá")

minha_funcao = meu_decorador(minha_funcao)  # ← o decorador "embrulha" a função
```

### O `@task` do Airflow (TaskFlow API):

Antigamente, você precisava do `PythonOperator` assim:

```python
# FORMA ANTIGA (verbosa)
def extrair():
    return [1, 2, 3]

def transformar(lista):
    return [x * 2 for x in lista]

def carregar(resultado):
    print(resultado)

extrair_task = PythonOperator(
    task_id="extrair",
    python_callable=extrair,
)

transformar_task = PythonOperator(
    task_id="transformar",
    python_callable=transformar,
    op_kwargs={"lista": "{{ ti.xcom_pull(task_ids='extrair') }}"},  # ← feio né?
)

carregar_task = PythonOperator(
    task_id="carregar",
    python_callable=carregar,
    op_kwargs={"resultado": "{{ ti.xcom_pull(task_ids='transformar') }}"},
)

extrair_task >> transformar_task >> carregar_task
```

Com decorador, fica assim:

```python
# FORMA NOVA (TaskFlow API) — muito mais limpa
from airflow.decorators import task

@task
def extrair():
    return [1, 2, 3]

@task
def transformar(lista):
    return [x * 2 for x in lista]

@task
def carregar(resultado):
    print(resultado)

# As setinhas funcionam igual
extrair() >> transformar() >> carregar()
```

**O que o `@task` faz?** Ele pega sua função Python normal e automaticamente transforma numa tarefa do Airflow. Sem precisar escrever `PythonOperator(...)`.

### O `@dag` — define a DAG inteira como função:

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id="meu_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
)
def meu_pipeline():
    
    @task
    def extrair():
        return [1, 2, 3]
    
    @task
    def transformar(lista):
        return [x * 2 for x in lista]
    
    @task
    def carregar(resultado):
        print(resultado)
    
    # Define a ordem
    dados = extrair()
    resultado = transformar(dados)
    carregar(resultado)

# "Chama" a função para registrar a DAG no Airflow
meu_pipeline()
```

### Comparação lado a lado:

| Forma antiga (Operators) | Forma nova (Decorators) |
|---|---|
| `PythonOperator(task_id=..., python_callable=...)` | `@task` em cima da função |
| Passar dados com `XCom` manual | Passar dados como argumento normal de função |
| `>>` para ligar tarefas | Chamar funções em sequência |
| Mais verboso | Mais Pythonico |

### Quando usar qual?

- **Decorators (`@task`)** → quando a tarefa é Python puro (funções simples)
- **Operators** → quando precisa de algo específico (rodar SQL, bash, Docker, S3)

No seu projeto, `dbt_run` e `dbt_test` **precisam** ser `BashOperator` porque rodam comando de terminal. Não tem como usar `@task` pra isso (pelo menos não de forma limpa).

---

## O que é o dbt?

Pensa assim: você tem uma **cozinha bagunçada** com ingredientes crus. O dbt é o **cozinheiro** que organiza, limpa, corta e monta o prato final.

```
Dados crus (Bronze)     →     Dados limpos (Silver)     →     Dados prontos (Gold)
raw_employees                  stg_employees                  dim_employee
(sujo, sem padrão)             (padronizado)                  (pronto pro BI)
```

### O dbt só faz UMA coisa:

**Lê dados do banco → transforma com SQL → escreve de volta no banco.**

Só isso. Não extrai dados de APIs. Não sobe arquivos no S3. Só SQL.

### Os conceitos do dbt:

#### 1. **Model** = um arquivo `.sql` que vira uma tabela

```sql
-- models/staging/stg_employees.sql
select
    employee_id,
    lower(first_name) as first_name,
    upper(department) as department
from {{ source('raw', 'raw_employees') }}
```

Roda `dbt run` → o dbt pega esse SQL, executa no banco, e cria a tabela `stg_employees`.

#### 2. **Materialização** = como o dbt salva o resultado

| Tipo | O que faz | Analogia |
|---|---|---|
| `table` | Cria uma tabela física | Escreve o resultado num caderno novo |
| `view` | Cria uma view (tabela virtual) | Cola a receita na geladeira (não escreve de novo) |
| `incremental` | Só adiciona dados novos | Só escreve as páginas novas do diário |
| `ephemeral` | Não salva, usa como CTE | Rascunho que você joga fora depois |

#### 3. **Source** = de onde vêm os dados brutos

```yaml
sources:
  - name: raw
    tables:
      - name: raw_employees
```

"dbt, essa tabela `raw_employees` eu não criei. Veio de fora. Só vou ler dela."

#### 4. **Test** = verificação de qualidade

```yaml
columns:
  - name: email
    tests:
      - unique      # não pode ter email duplicado
      - not_null    # não pode ter email vazio
```

Roda `dbt test` → o dbt roda queries que verificam se os dados estão corretos.

---

## Como Airflow e dbt trabalham juntos

```
Airflow (chef/maestro)                    dbt (cozinheiro)
─────────────────────                     ─────────────────
1. Extrai dados de uma API              
2. Salva em raw_employees (Bronze)      
                                      3. dbt run:
                                         - Lê raw_employees
                                         - Limpa → stg_employees (Silver)
                                         - Transforma → dim_employee (Gold)
                                      4. dbt test:
                                         - Verifica qualidade
5. Se tudo passou → sucesso!
   Se falhou → alerta no Slack
```

O Airflow **orquestra** (decide quando e em que ordem). O dbt **transforma** (roda os SQLs).

---

## Resumo em 1 frase cada:

| Conceito | O que é |
|---|---|
| **Airflow** | Maestro que agenda e orquestra tarefas na ordem certa |
| **DAG** | A receita (lista de passos com ordem) |
| **Operador** | Ferramenta específica (faca, forno, batedeira) |
| **Decorador `@task`** | Atalho pra transformar função Python em tarefa |
| **dbt** | Cozinheiro que transforma dados crus em dados limpos usando SQL |
| **Model** | Um arquivo SQL que vira tabela |
| **Test** | Verificação de qualidade dos dados |

---

## Entendendo o papel de cada ferramenta

### Airflow = O orquestrador (maestro)

O Airflow **não processa dados**. Ele **manda processar**.

- Ele decide **QUANDO** rodar (schedule: todo dia às 8h, de hora em hora, etc.)
- Ele decide **EM QUE ORDEM** (primeiro extrai, depois transforma, depois valida)
- Ele **monitora** (se falhou, retenta. Se deu certo, avisa)
- Ele **registra** (histórico de execuções, logs, métricas)

O Airflow é como um **dev automatizado** — ele aperta os botões no horário certo, na sequência certa.

### dbt = Uma peça do pipeline (poderia ser outra)

O dbt é **uma ferramenta de transformação**. Ele ocupa **uma etapa** do pipeline.

No lugar do dbt, poderia ser:
- **Spark** — para processar bilhões de registros
- **Python/Pandas** — para transformações complexas
- **SQL scripts** — queries soltas rodando direto
- **Qualquer outra coisa** que transforme dados

O Airflow não se importa. Ele só "aperta o botão" na hora certa:

```python
# Com dbt:
BashOperator(bash_command="dbt run")

# Com Spark:
BashOperator(bash_command="spark-submit transforma.py")

# Com Python:
BashOperator(bash_command="python transforma.py")

# Com script SQL:
PostgresOperator(sql="transform.sql")
```

### A relação entre os dois:

```
Airflow = QUEM manda + QUANDO manda + EM QUE ORDEM
dbt     = O QUE faz (transforma dados com SQL)
```

O Airflow é o **processo**. O dbt é **uma etapa** desse processo.
