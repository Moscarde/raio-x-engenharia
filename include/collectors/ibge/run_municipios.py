"""Entrypoint manual da ingestão de municípios do IBGE.

Uso:
    python -m include.collectors.ibge.run_municipios
"""

from __future__ import annotations

import logging
import time

from include.collectors.ibge.client import MUNICIPIOS_URL, fetch_municipios
from include.collectors.ibge.db import get_connection
from include.collectors.ibge.parser import parse_municipios
from include.collectors.ibge.repository import ensure_schema, upsert_municipios

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava municípios do IBGE em raw_ibge.municipios."""
    start = time.monotonic()
    raw_municipios = fetch_municipios()
    municipios = parse_municipios(raw_municipios)

    with get_connection() as conn:
        ensure_schema(conn)
        total = upsert_municipios(conn, municipios)

    elapsed = time.monotonic() - start
    logger.info(
        "raw_ibge.municipios: %s linhas carregadas em %.1fs (fonte=%s)",
        total,
        elapsed,
        MUNICIPIOS_URL,
    )
    return total


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    run()
