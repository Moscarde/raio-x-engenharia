"""Ingestão de população estimada do IBGE em `raw_ibge.populacao_estimada`.

Escopo do collector é fixo (municípios de referência do MVP, último ano
disponível no agregado 6579 do SIDRA) — ver
`include/collectors/ibge/run_populacao_estimada.py`. Sem agendamento
automático: disparo manual, mesmo padrão das demais DAGs de coleta.
"""

from __future__ import annotations

from airflow.sdk import dag, task
from pendulum import datetime

from include.collectors.ibge.run_populacao_estimada import (
    run as run_populacao_estimada,
)


@dag(
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "raio-x-engenharia", "retries": 2},
    tags=["collector", "ibge", "raw"],
)
def raw_ibge_populacao():
    @task
    def carregar_populacao_estimada() -> int:
        return run_populacao_estimada()

    carregar_populacao_estimada()


raw_ibge_populacao()
