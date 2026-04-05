# ============================================================================
# Dockerfile customizado para o Airflow
# A imagem oficial do Airflow não inclui o dbt, então criamos uma imagem
# derivada que adiciona o dbt-postgres como dependência.
# ============================================================================
FROM apache/airflow:2.10.5

# Instala o adapter do PostgreSQL para o dbt.
# --no-cache-dir: reduz o tamanho da imagem removendo cache do pip.
# dbt-postgres: permite que o dbt se conecte a bancos PostgreSQL.
RUN pip install --no-cache-dir dbt-postgres psycopg2-binary
