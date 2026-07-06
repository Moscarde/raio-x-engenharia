# Comandos operacionais do projeto raio-x-engenharia. Requer `just`
# (https://github.com/casey/just) e o Astro CLI já configurados
# (ver CLAUDE.md#contexto-técnico).
#
# backup-db/restore-db (docker exec no Postgres local do Astro) foram
# removidos: banco de produção agora é Postgres externo em nuvem, fora do
# stack Astro — não dá pra descobrir via `docker ps`. Backup/restore desse
# banco usam pg_dump/pg_restore direto contra POSTGRES_HOST:POSTGRES_PORT
# do .env, fora do escopo deste justfile por ora.

set dotenv-load := true

# Lista os comandos disponíveis.
default:
    @just --list

# Sobe o stack completo do Astro (Postgres + Airflow: webserver, scheduler,
# triggerer, dag-processor). Postgres local aqui serve só os metadados do
# Airflow — dados do projeto ficam no Postgres externo (ver .env).
up-airflow:
    astro dev start
