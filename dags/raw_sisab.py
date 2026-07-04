"""Ingestão de indicadores de desempenho do Previne Brasil (SISAB) em
`raw_sisab.indicador_desempenho`.

Escopo do collector é fixo (Rio de Janeiro, quadrimestre 2024Q3 — último
quadrimestre disponível, o Previne Brasil foi extinto em 2024, ver
ROADMAP.md) — ver `include/collectors/sisab/run_indicador_desempenho.py`.
Sem agendamento automático: a série não recebe mais dados novos.
"""

from __future__ import annotations

from airflow.sdk import dag, task
from pendulum import datetime

from include.collectors.sisab.run_indicador_desempenho import (
    run as run_indicador_desempenho,
)


@dag(
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "raio-x-engenharia", "retries": 2},
    tags=["collector", "sisab", "raw"],
)
def raw_sisab():
    @task
    def carregar_indicador_desempenho() -> int:
        return run_indicador_desempenho()

    carregar_indicador_desempenho()


raw_sisab()
