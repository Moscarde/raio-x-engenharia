"""Entrypoint manual da ingestão de estabelecimentos do CNES.

Uso:
    python -m include.collectors.cnes.run_estabelecimentos
"""

from __future__ import annotations

import logging
import time

from include.collectors.cnes.client import fetch_estabelecimentos, source_filename
from include.collectors.cnes.db import get_connection
from include.collectors.cnes.parser import parse_estabelecimentos
from include.collectors.cnes.repository import ensure_schema, upsert_estabelecimentos

# Escopo MVP (docs/fontes.md#escopo-de-volume-para-o-mvp): 1 município de
# referência (Rio de Janeiro) e 1 competência de 2025. CNES é cadastro
# (snapshot mensal), não série de eventos, então uma única competência já
# retrata o ano; dez/2025 é a mais recente disponível no ano.
UF = "RJ"
ANO = 2025
MES = 12

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava estabelecimentos do CNES em raw_cnes.estabelecimentos."""
    start = time.monotonic()
    raw_estabelecimentos = fetch_estabelecimentos(UF, ANO, MES)
    estabelecimentos = parse_estabelecimentos(raw_estabelecimentos)
    arquivo_origem = source_filename(UF, ANO, MES)

    with get_connection() as conn:
        ensure_schema(conn)
        total = upsert_estabelecimentos(
            conn, estabelecimentos, arquivo_origem, ANO, MES
        )

    elapsed = time.monotonic() - start
    logger.info(
        "raw_cnes.estabelecimentos: %s linhas carregadas em %.1fs "
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
