"""Ingestão de internações do SIH em `raw_sih.internacoes`.

Escopo do collector é fixo (Rio de Janeiro, 12 competências de 2025) — ver
`include/collectors/sih/run_internacoes.py` e
`docs/fontes.md#escopo-de-volume-para-o-mvp`. Sem agendamento automático:
disparo manual até o escopo virar parametrizável.
"""

from __future__ import annotations

from airflow.sdk import dag, task
from pendulum import datetime

from include.collectors.sih.run_internacoes import run as run_internacoes


@dag(
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "raio-x-engenharia", "retries": 2},
    tags=["collector", "sih", "raw"],
)
def raw_sih():
    @task
    def carregar_internacoes() -> int:
        return run_internacoes()

    carregar_internacoes()


raw_sih()
