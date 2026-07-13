"""Ingestão de equipes de APS do CNES em `raw_cnes.equipes_aps`.

Escopo do collector é fixo (Rio de Janeiro, Paraty e Nova Iguaçu, competência
2025-12) — ver `include/collectors/cnes/run_equipes_aps.py`. Sem
agendamento automático: mesmo padrão de disparo manual das demais DAGs de
coleta.
"""

from __future__ import annotations

from airflow.sdk import dag, task
from pendulum import datetime

from include.collectors.cnes.run_equipes_aps import run as run_equipes_aps


@dag(
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "raio-x-engenharia", "retries": 2},
    tags=["collector", "cnes", "raw"],
)
def raw_cnes_equipes():
    @task
    def carregar_equipes_aps() -> int:
        return run_equipes_aps()

    carregar_equipes_aps()


raw_cnes_equipes()
