"""Ingestão de estabelecimentos detalhados do CNES (DEMAS) em
`raw_cnes.estabelecimentos_detalhados`.

Escopo do collector é fixo (3 municípios de referência) — ver
`include/collectors/cnes/run_estabelecimentos_detalhados.py`. Complementa
`raw_cnes.estabelecimentos` (grupo "ST" do FTP, sem nome/endereço) com
nome, endereço, geolocalização e esfera administrativa decodificada. Sem
agendamento automático: disparo manual, mesmo padrão das demais DAGs de
coleta. Execução leva vários minutos (API pagina 20 registros por vez, sem
total exposto).
"""

from __future__ import annotations

from airflow.sdk import dag, task
from pendulum import datetime

from include.collectors.cnes.run_estabelecimentos_detalhados import (
    run as run_estabelecimentos_detalhados,
)


@dag(
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "raio-x-engenharia", "retries": 2},
    tags=["collector", "cnes", "raw"],
)
def raw_cnes_estabelecimentos_detalhados():
    @task
    def carregar_estabelecimentos_detalhados() -> int:
        return run_estabelecimentos_detalhados()

    carregar_estabelecimentos_detalhados()


raw_cnes_estabelecimentos_detalhados()
