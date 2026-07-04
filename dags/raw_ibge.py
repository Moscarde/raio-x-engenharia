"""Ingestão de municípios do IBGE em `raw_ibge.municipios`.

Escopo do collector é fixo (todos os municípios do Brasil, sem filtro de
ano/competência) — ver `include/collectors/ibge/run_municipios.py`. Sem
agendamento automático: o cadastro de municípios muda raramente, então o
disparo é manual.
"""

from __future__ import annotations

from airflow.sdk import dag, task
from pendulum import datetime

from include.collectors.ibge.run_municipios import run as run_municipios


@dag(
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "raio-x-engenharia", "retries": 2},
    tags=["collector", "ibge", "raw"],
)
def raw_ibge():
    @task
    def carregar_municipios() -> int:
        return run_municipios()

    carregar_municipios()


raw_ibge()
