"""Entrypoint manual da ingestão de internações hospitalares do SIH.

Uso:
    python -m include.collectors.sih.run_internacoes
"""

from __future__ import annotations

import logging
import time

from include.collectors.sih.client import fetch_internacoes
from include.collectors.sih.db import get_connection
from include.collectors.sih.parser import parse_internacoes
from include.collectors.sih.repository import ensure_schema, upsert_internacoes

# Escopo MVP (docs/fontes.md#escopo-de-volume-para-o-mvp): 1 município de
# referência (Rio de Janeiro) e ano de 2025. Como o SIA, o SIH é produção
# mensal (série de eventos): o ano completo exige buscar as 12 competências.
UF = "RJ"
ANO = 2025
MESES = range(1, 13)

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava as internações de 2025 em raw_sih.internacoes.

    Processa uma competência (mês) por vez: busca, filtra pelo município de
    referência e faz upsert no Postgres antes de seguir para o próximo mês.
    Isso mantém o uso de memória limitado a 1 mês por vez e torna a execução
    retomável — se falhar no mês 7, os meses 1-6 já foram gravados.
    """
    start = time.monotonic()
    total_geral = 0

    with get_connection() as conn:
        ensure_schema(conn)

        for mes in MESES:
            inicio_mes = time.monotonic()
            raw_internacoes = fetch_internacoes(UF, ANO, mes)
            internacoes = parse_internacoes(raw_internacoes)
            total_mes = upsert_internacoes(conn, internacoes, ANO, mes)
            total_geral += total_mes
            logger.info(
                "raw_sih.internacoes: %s linhas carregadas em %.1fs "
                "(competencia=%s-%02d)",
                total_mes,
                time.monotonic() - inicio_mes,
                ANO,
                mes,
            )

    elapsed = time.monotonic() - start
    logger.info(
        "raw_sih.internacoes: %s linhas no total, %s competências, em %.1fs",
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
