"""Ingestão de recursos recebidos (Portal da Transparência) em
`raw_portaltransparencia.recursos_recebidos_saude`.

Escopo do collector é fixo (municípios de referência, ano 2025, órgão
superior Ministério da Saúde) — ver
`include/collectors/portaltransparencia/run_recursos_recebidos.py`. Exige
`PORTAL_TRANSPARENCIA_API_KEY` no ambiente (ver .env.example) — diferente
das demais fontes deste projeto, esta API exige autenticação. Sem
agendamento automático: disparo manual, mesmo padrão das demais DAGs de
coleta.
"""

from __future__ import annotations

from airflow.sdk import dag, task
from pendulum import datetime

from include.collectors.portaltransparencia.run_recursos_recebidos import (
    run as run_recursos_recebidos,
)


@dag(
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "raio-x-engenharia", "retries": 2},
    tags=["collector", "portaltransparencia", "raw"],
)
def raw_portaltransparencia():
    @task
    def carregar_recursos_recebidos() -> int:
        return run_recursos_recebidos()

    carregar_recursos_recebidos()


raw_portaltransparencia()
