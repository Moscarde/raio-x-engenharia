"""Ingestão de produção ambulatorial do SIA em `raw_sia.producao_ambulatorial`.

Escopo do collector é fixo (Rio de Janeiro, 12 competências de 2025) — ver
`include/collectors/sia/run_producao_ambulatorial.py` e
`docs/fontes.md#escopo-de-volume-para-o-mvp`. Carga do ano completo é
pesada (~1,5-2h, ver ROADMAP.md), então o disparo é manual em vez de
agendado.
"""

from __future__ import annotations

from airflow.sdk import dag, task
from pendulum import datetime

from include.collectors.sia.run_producao_ambulatorial import (
    run as run_producao_ambulatorial,
)


@dag(
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "raio-x-engenharia", "retries": 2},
    tags=["collector", "sia", "raw"],
)
def raw_sia():
    @task
    def carregar_producao_ambulatorial() -> int:
        return run_producao_ambulatorial()

    carregar_producao_ambulatorial()


raw_sia()
