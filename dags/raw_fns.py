"""Ingestão de repasses Fundo a Fundo do FNS em `raw_fns.repasses`.

Escopo do collector é fixo (Rio de Janeiro, ano de 2025) — ver
`include/collectors/fns/run_repasses.py` e
`docs/fontes.md#escopo-de-volume-para-o-mvp`. Sem agendamento automático:
disparo manual até o escopo virar parametrizável.
"""

from __future__ import annotations

from airflow.sdk import dag, task
from pendulum import datetime

from include.collectors.fns.run_repasses import run as run_repasses


@dag(
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "raio-x-engenharia", "retries": 2},
    tags=["collector", "fns", "raw"],
)
def raw_fns():
    @task
    def carregar_repasses() -> int:
        return run_repasses()

    carregar_repasses()


raw_fns()
