"""Ingestão de estabelecimentos de saúde do CNES em `raw_cnes.estabelecimentos`.

Escopo do collector é fixo (Rio de Janeiro, competência dez/2025) — ver
`include/collectors/cnes/run_estabelecimentos.py` e
`docs/fontes.md#escopo-de-volume-para-o-mvp`. Sem agendamento automático:
mudar a competência exige mudar o código do collector, então o disparo é
manual até o escopo virar parametrizável.
"""

from __future__ import annotations

from airflow.sdk import dag, task
from pendulum import datetime

from include.collectors.cnes.run_estabelecimentos import run as run_estabelecimentos


@dag(
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "raio-x-engenharia", "retries": 2},
    tags=["collector", "cnes", "raw"],
)
def raw_cnes():
    @task
    def carregar_estabelecimentos() -> int:
        return run_estabelecimentos()

    carregar_estabelecimentos()


raw_cnes()
