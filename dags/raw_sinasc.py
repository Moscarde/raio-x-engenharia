"""Ingestão de nascidos vivos do SINASC em `raw_sinasc.nascidos_vivos`.

Escopo do collector é fixo (Rio de Janeiro, ano de 2022 — último ano
publicado no FTP do DATASUS, ver ROADMAP.md) — ver
`include/collectors/sinasc/run_nascidos_vivos.py`. Sem agendamento
automático: disparo manual até o escopo virar parametrizável.
"""

from __future__ import annotations

from airflow.sdk import dag, task
from pendulum import datetime

from include.collectors.sinasc.run_nascidos_vivos import run as run_nascidos_vivos


@dag(
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "raio-x-engenharia", "retries": 2},
    tags=["collector", "sinasc", "raw"],
)
def raw_sinasc():
    @task
    def carregar_nascidos_vivos() -> int:
        return run_nascidos_vivos()

    carregar_nascidos_vivos()


raw_sinasc()
