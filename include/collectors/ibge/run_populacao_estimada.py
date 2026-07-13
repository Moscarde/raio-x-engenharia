"""Entrypoint manual da ingestão de população estimada do IBGE.

Uso:
    python -m include.collectors.ibge.run_populacao_estimada
"""

from __future__ import annotations

import logging
import time

from include.collectors.ibge.client import POPULACAO_URL, fetch_populacao_estimada
from include.collectors.ibge.db import get_connection
from include.collectors.ibge.parser import (
    MUNICIPIOS_REFERENCIA_ID_MUNICIPIO,
    parse_populacao_estimada,
)
from include.collectors.ibge.repository import (
    ensure_schema_populacao,
    upsert_populacao_estimada,
)

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava a população estimada em raw_ibge.populacao_estimada.

    Escopo MVP: mesmos municípios de referência das demais fontes (ver
    docs/fontes.md#escopo-de-volume-para-o-mvp). O agregado 6579 cobre o
    Brasil inteiro, mas o filtro por município já acontece na própria
    consulta (parâmetro `localidades`), então não há necessidade de
    descartar linhas depois de buscar.
    """
    start = time.monotonic()
    corpo = fetch_populacao_estimada(MUNICIPIOS_REFERENCIA_ID_MUNICIPIO)
    populacao = parse_populacao_estimada(corpo)

    with get_connection() as conn:
        ensure_schema_populacao(conn)
        total = upsert_populacao_estimada(conn, populacao)

    elapsed = time.monotonic() - start
    logger.info(
        "raw_ibge.populacao_estimada: %s linhas carregadas em %.1fs (fonte=%s)",
        total,
        elapsed,
        POPULACAO_URL,
    )
    return total


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    run()
