"""Ingestão do universo de comparação entre pares (município do RJ inteiro).

Duas fontes independentes, cada uma alimentando um atributo de
`mart_comparacao_municipios_rj` (ver ROADMAP.md "Comparação entre pares"):
população estimada do IBGE e porte de rede (contagem de estabelecimentos)
do CNES, para os 92 municípios do RJ — não só os 3 de referência das demais
DAGs. Sem agendamento automático: disparo manual, mesmo padrão das demais
DAGs de coleta.
"""

from __future__ import annotations

from airflow.sdk import dag, task
from pendulum import datetime

from include.collectors.cnes.run_rede_porte_municipio import (
    run as run_rede_porte_municipio,
)
from include.collectors.ibge.run_populacao_estimada_rj import (
    run as run_populacao_estimada_rj,
)


@dag(
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "raio-x-engenharia", "retries": 2},
    tags=["collector", "ibge", "cnes", "raw"],
)
def raw_comparacao_municipios_rj():
    @task
    def carregar_populacao_estimada_rj() -> int:
        return run_populacao_estimada_rj()

    @task
    def carregar_rede_porte_municipio() -> int:
        return run_rede_porte_municipio()

    carregar_populacao_estimada_rj()
    carregar_rede_porte_municipio()


raw_comparacao_municipios_rj()
