"""Ingestão do RREO-Anexo 14 (SICONFI) em `raw_siops.rreo_anexo14`.

Escopo do collector é fixo (Rio de Janeiro, ano de 2025, bimestre de
fechamento) — ver `include/collectors/siops/run_rreo_anexo14.py`. Sem
agendamento automático: disparo manual até o escopo virar parametrizável.
"""

from __future__ import annotations

from airflow.sdk import dag, task
from pendulum import datetime

from include.collectors.siops.run_rreo_anexo14 import run as run_rreo_anexo14


@dag(
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "raio-x-engenharia", "retries": 2},
    tags=["collector", "siops", "raw"],
)
def raw_siops():
    @task
    def carregar_rreo_anexo14() -> int:
        return run_rreo_anexo14()

    carregar_rreo_anexo14()


raw_siops()
