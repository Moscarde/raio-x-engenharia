"""Entrypoint manual da ingestão de repasses de Fundo a Fundo do FNS.

Uso:
    python -m include.collectors.fns.run_repasses
"""

from __future__ import annotations

import logging
import time

from include.collectors.fns.client import fetch_lancamentos
from include.collectors.fns.db import get_connection
from include.collectors.fns.parser import MUNICIPIO_REFERENCIA_CNPJ, parse_lancamentos
from include.collectors.fns.repository import ensure_schema, upsert_repasses

# Escopo MVP (docs/fontes.md#escopo-de-volume-para-o-mvp): 1 município de
# referência (Rio de Janeiro) e ano de 2025. Diferente das fontes DBC, a API
# do FNS filtra por CNPJ + intervalo de datas na própria consulta, então o
# ano completo é buscado em 1 única chamada, sem precisar iterar por mês.
ANO = 2025

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava os repasses de 2025 em raw_fns.repasses."""
    start = time.monotonic()
    raw_lancamentos = fetch_lancamentos(MUNICIPIO_REFERENCIA_CNPJ, ANO)
    lancamentos = parse_lancamentos(raw_lancamentos)

    with get_connection() as conn:
        ensure_schema(conn)
        total = upsert_repasses(conn, lancamentos, ANO)

    elapsed = time.monotonic() - start
    logger.info(
        "raw_fns.repasses: %s linhas carregadas em %.1fs (ano=%s, cnpj=%s)",
        total,
        elapsed,
        ANO,
        MUNICIPIO_REFERENCIA_CNPJ,
    )
    return total


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    run()
