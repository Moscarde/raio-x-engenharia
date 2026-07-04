"""Entrypoint manual da ingestão de produção ambulatorial do SIA.

Uso:
    python -m include.collectors.sia.run_producao_ambulatorial
"""

from __future__ import annotations

import logging
import time

from include.collectors.sia.client import fetch_producao_ambulatorial
from include.collectors.sia.db import get_connection
from include.collectors.sia.parser import (
    MUNICIPIO_REFERENCIA_CODUFMUN,
    parse_producoes_ambulatoriais,
)
from include.collectors.sia.repository import (
    ensure_schema,
    substituir_producao_ambulatorial,
)

# Escopo MVP (docs/fontes.md#escopo-de-volume-para-o-mvp): 1 município de
# referência (Rio de Janeiro) e ano de 2025. Diferente do CNES (cadastro,
# 1 competência basta), o SIA é produção mensal (série de eventos): o ano
# completo exige buscar as 12 competências.
UF = "RJ"
ANO = 2025
MESES = range(1, 13)

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava a produção ambulatorial de 2025 em raw_sia.producao_ambulatorial.

    Processa uma competência (mês) por vez: busca, filtra pelo município de
    referência, substitui a partição no Postgres e segue para o próximo mês.
    Isso mantém o uso de memória limitado a 1 mês por vez e torna a execução
    retomável — se falhar no mês 7, os meses 1-6 já foram gravados.
    """
    start = time.monotonic()
    total_geral = 0

    with get_connection() as conn:
        ensure_schema(conn)

        for mes in MESES:
            inicio_mes = time.monotonic()
            raw_producoes = fetch_producao_ambulatorial(UF, ANO, mes)
            producoes = parse_producoes_ambulatoriais(raw_producoes)
            total_mes = substituir_producao_ambulatorial(
                conn, producoes, MUNICIPIO_REFERENCIA_CODUFMUN
            )
            total_geral += total_mes
            logger.info(
                "raw_sia.producao_ambulatorial: %s linhas carregadas em %.1fs "
                "(competencia=%s-%02d)",
                total_mes,
                time.monotonic() - inicio_mes,
                ANO,
                mes,
            )

    elapsed = time.monotonic() - start
    logger.info(
        "raw_sia.producao_ambulatorial: %s linhas no total, %s competências, em %.1fs",
        total_geral,
        len(MESES),
        elapsed,
    )
    return total_geral


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    run()
