"""Orquestra `dbt seed`/`dbt run`/`dbt test` sobre os models em `dbt/`.

dbt roda isolado do Python do próprio Airflow: `dbt-core`/`dbt-postgres`
ficam de propósito fora da imagem (ver `requirements-dev.txt` e
CLAUDE.md#dependências — instalar junto com o Airflow colide com as
dependências dele). Cada task garante um venv dedicado em `.dbt_venv/`
via `uv` (já presente na imagem Astro), criado só na 1ª execução e
reaproveitado depois — não precisa reinstalar dbt a cada run.

Sem agendamento automático (`schedule=None`), mesmo padrão das DAGs de
coleta em `dags/raw_<fonte>.py`: a orquestração completa (esperar as DAGs
de fonte terminarem antes de rodar dbt) fica para quando o escopo dos
collectors virar parametrizável por execução (ver ROADMAP.md).
"""

from __future__ import annotations

from airflow.sdk import dag, task
from pendulum import datetime

# Caminhos absolutos: o BashOperator/task.bash roda o comando num cwd
# próprio (tmpdir), não em /usr/local/airflow — caminho relativo aqui
# resultava em "Path 'dbt' does not exist" (confirmado via `airflow tasks
# test`).
AIRFLOW_HOME = "/usr/local/airflow"
DBT_PROJECT_DIR = f"{AIRFLOW_HOME}/dbt"
DBT_PROFILES_DIR = f"{AIRFLOW_HOME}/dbt"
DBT_VENV_DIR = f"{AIRFLOW_HOME}/.dbt_venv"

SETUP_VENV = f"""
set -e
if [ ! -x "{DBT_VENV_DIR}/bin/dbt" ]; then
    uv venv {DBT_VENV_DIR}
    uv pip install --python {DBT_VENV_DIR}/bin/python dbt-core dbt-postgres
fi
""".strip()


def _dbt_bash_command(subcomando: str) -> str:
    """Monta o comando bash: garante o venv e roda `dbt <subcomando>`."""
    dbt_bin = f"{DBT_VENV_DIR}/bin/dbt"
    return (
        f"{SETUP_VENV}\n"
        f"{dbt_bin} {subcomando} "
        f"--project-dir {DBT_PROJECT_DIR} --profiles-dir {DBT_PROFILES_DIR}"
    )


@dag(
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "raio-x-engenharia", "retries": 1},
    tags=["dbt", "transform"],
)
def dbt_transform():
    @task.bash(task_id="dbt_seed")
    def dbt_seed() -> str:
        return _dbt_bash_command("seed")

    @task.bash(task_id="dbt_run")
    def dbt_run() -> str:
        return _dbt_bash_command("run")

    @task.bash(task_id="dbt_test")
    def dbt_test() -> str:
        return _dbt_bash_command("test")

    dbt_seed() >> dbt_run() >> dbt_test()


dbt_transform()
