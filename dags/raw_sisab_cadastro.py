"""Ingestão de cadastro vinculado do Previne Brasil (SISAB) em
`raw_sisab.cadastro_vinculado`.

Escopo do collector é fixo (municípios de referência, competência 202412 —
última disponível, o Previne Brasil foi extinto em 2024, ver ROADMAP.md) —
ver `include/collectors/sisab/run_cadastro_vinculado.py`. Sem agendamento
automático: a série não recebe mais dados novos.
"""

from __future__ import annotations

from airflow.sdk import dag, task
from pendulum import datetime

from include.collectors.sisab.run_cadastro_vinculado import (
    run as run_cadastro_vinculado,
)


@dag(
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "raio-x-engenharia", "retries": 2},
    tags=["collector", "sisab", "raw"],
)
def raw_sisab_cadastro():
    @task
    def carregar_cadastro_vinculado() -> int:
        return run_cadastro_vinculado()

    carregar_cadastro_vinculado()


raw_sisab_cadastro()
