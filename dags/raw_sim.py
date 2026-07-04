"""Ingestão de óbitos do SIM em `raw_sim.obitos`.

Escopo do collector é fixo (Rio de Janeiro, ano de 2024 — último ano
publicado no FTP do DATASUS, ver ROADMAP.md) — ver
`include/collectors/sim/run_obitos.py`. Sem agendamento automático:
disparo manual até o escopo virar parametrizável.
"""

from __future__ import annotations

from airflow.sdk import dag, task
from pendulum import datetime

from include.collectors.sim.run_obitos import run as run_obitos


@dag(
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "raio-x-engenharia", "retries": 2},
    tags=["collector", "sim", "raw"],
)
def raw_sim():
    @task
    def carregar_obitos() -> int:
        return run_obitos()

    carregar_obitos()


raw_sim()
