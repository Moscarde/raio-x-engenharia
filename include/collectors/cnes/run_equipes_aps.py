"""Entrypoint manual da ingestão de equipes de APS do CNES.

Uso:
    python -m include.collectors.cnes.run_equipes_aps
"""

from __future__ import annotations

import logging
import time

from include.collectors.cnes.client import (
    GROUP_EQUIPES_APS,
    fetch_equipes_aps,
    source_filename,
)
from include.collectors.cnes.db import get_connection
from include.collectors.cnes.parser import parse_equipes_aps
from include.collectors.cnes.repository import (
    ensure_schema_equipes_aps,
    upsert_equipes_aps,
)

# Mesmo escopo do run_estabelecimentos.py: 3 municípios de referência do
# MVP, competência dez/2025 (grupo "EP" é cadastro/situação por competência,
# igual ao "ST" — 1 snapshot mensal já retrata o período).
UF = "RJ"
ANO = 2025
MES = 12

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava equipes de APS do CNES em raw_cnes.equipes_aps."""
    start = time.monotonic()
    raw_equipes = fetch_equipes_aps(UF, ANO, MES)
    equipes = parse_equipes_aps(raw_equipes)
    arquivo_origem = source_filename(UF, ANO, MES, GROUP_EQUIPES_APS)

    with get_connection() as conn:
        ensure_schema_equipes_aps(conn)
        total = upsert_equipes_aps(conn, equipes, arquivo_origem, ANO, MES)

    elapsed = time.monotonic() - start
    logger.info(
        "raw_cnes.equipes_aps: %s linhas carregadas em %.1fs "
        "(competencia=%s-%02d, fonte=%s)",
        total,
        elapsed,
        ANO,
        MES,
        arquivo_origem,
    )
    return total


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    run()
