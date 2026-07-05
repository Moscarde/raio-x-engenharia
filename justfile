# Comandos operacionais do projeto raio-x-engenharia — backup/restore do
# Postgres e subida separada de Postgres/Airflow. Requer `just`
# (https://github.com/casey/just) e o Astro CLI já configurados
# (ver CLAUDE.md#contexto-técnico).
#
# Uso típico pra levar o estado atual do banco pro servidor frango sem
# reprocessar collectors/dbt:
#   just up-postgres
#   just restore-db backups/<arquivo>.dump
#   just up-airflow

set dotenv-load := true

backup_dir := "backups"

# Container do Postgres gerenciado pelo Astro CLI (docker compose),
# descoberto pelas labels do compose em vez de hardcoded — o nome do
# projeto compose que o Astro gera (ex. raio-x-engenharia_785cf4) varia
# por checkout/máquina, então não dá pra fixar no justfile.
postgres_running := `docker ps -q --filter "label=com.docker.compose.project.working_dir=$(pwd)" --filter "label=com.docker.compose.service=postgres" 2>/dev/null || true`
postgres_any := `docker ps -aq --filter "label=com.docker.compose.project.working_dir=$(pwd)" --filter "label=com.docker.compose.service=postgres" 2>/dev/null || true`

# Lista os comandos disponíveis.
default:
    @just --list

# Sobe só o container do Postgres (mais rápido e mais leve que o stack
# Airflow inteiro) — útil pra rodar collectors manualmente ou restaurar um
# backup sem esperar webserver/scheduler/triggerer subirem. Exige que o
# container já exista: rode `just up-airflow` ao menos 1 vez antes (é o
# `astro dev start` que cria o container na 1ª vez).
up-postgres:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -z "{{postgres_any}}" ]; then
        echo "Container do Postgres ainda não existe. Rode 'just up-airflow' (astro dev start) uma vez para criá-lo." >&2
        exit 1
    fi
    docker start {{postgres_any}}

# Sobe o stack completo do Astro (Postgres + Airflow: webserver, scheduler,
# triggerer, dag-processor). Único jeito de criar os containers na 1ª vez
# — o Astro CLI não expõe um jeito de subir só 1 serviço do stack.
up-airflow:
    astro dev start

# Backup de todas as camadas de dados (schemas raw_*, staging,
# intermediate, marts) num arquivo único comprimido — usa
# --exclude-schema=public pra deixar de fora os metadados internos do
# Airflow (DAGs, task instances, logs: não é dado do projeto, e cresce sem
# parar). Formato "custom" do pg_dump (-Fc): já vem comprimido (~16x sobre
# os ~28GB em disco, medido) e permite restore seletivo — bem mais leve
# que dump em texto puro. Compressão no nível padrão do formato custom, não
# --compress=9: testado nesta sessão, o nível 9 ficou visivelmente mais
# lento (não terminou em 5min o que o padrão fez em ~5min completos) pra
# ganho de tamanho marginal. Usar pra levar o estado atual do banco pro
# servidor frango sem reprocessar collectors/dbt.
backup-db name=`date +%Y%m%d_%H%M%S`:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -z "{{postgres_running}}" ]; then
        echo "Postgres não está rodando. Rode 'just up-postgres' ou 'just up-airflow' primeiro." >&2
        exit 1
    fi
    mkdir -p {{backup_dir}}
    docker exec {{postgres_running}} pg_dump \
        -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        --format=custom --no-owner \
        --exclude-schema=public \
        > {{backup_dir}}/{{name}}.dump
    echo "Backup salvo em {{backup_dir}}/{{name}}.dump ($(du -h {{backup_dir}}/{{name}}.dump | cut -f1))"

# Restaura um backup gerado por `backup-db`. --clean --if-exists: derruba
# e recria os objetos existentes nos schemas do dump antes de restaurar,
# então funciona tanto num banco vazio (deploy novo no frango) quanto por
# cima de um banco já populado (idempotente). Rodar depois de
# `just up-postgres` (ou `up-airflow`).
restore-db file:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -z "{{postgres_running}}" ]; then
        echo "Postgres não está rodando. Rode 'just up-postgres' ou 'just up-airflow' primeiro." >&2
        exit 1
    fi
    if [ ! -f "{{file}}" ]; then
        echo "Arquivo de backup não encontrado: {{file}}" >&2
        exit 1
    fi
    docker exec -i {{postgres_running}} pg_restore \
        -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        --no-owner --clean --if-exists \
        < {{file}}
    echo "Restore de {{file}} concluído."
