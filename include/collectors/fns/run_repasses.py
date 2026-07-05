"""Entrypoint manual da ingestão de repasses de Fundo a Fundo do FNS.

Uso:
    python -m include.collectors.fns.run_repasses
"""

from __future__ import annotations

import logging
import time

from include.collectors.fns.client import fetch_lancamentos
from include.collectors.fns.db import get_connection
from include.collectors.fns.parser import MUNICIPIOS_REFERENCIA_CNPJ, parse_lancamentos
from include.collectors.fns.repository import ensure_schema, upsert_repasses

# Escopo MVP (docs/fontes.md#escopo-de-volume-para-o-mvp): municípios de
# referência e ano de 2025. Diferente das fontes DBC, a API do FNS filtra
# por CNPJ + intervalo de datas na própria consulta, então o ano completo de
# cada município é buscado em 1 única chamada, sem precisar iterar por mês.
ANO = 2025

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava os repasses de 2025 em raw_fns.repasses.

    1 chamada por CNPJ de referência — upsert por id_lancamento (chave
    global da própria API do FNS, não precisa de partição por município).
    """
    start = time.monotonic()
    total_geral = 0

    with get_connection() as conn:
        ensure_schema(conn)

        for cnpj in MUNICIPIOS_REFERENCIA_CNPJ:
            raw_lancamentos = fetch_lancamentos(cnpj, ANO)
            lancamentos = parse_lancamentos(raw_lancamentos)
            total_cnpj = upsert_repasses(conn, lancamentos, ANO)
            total_geral += total_cnpj
            logger.info(
                "raw_fns.repasses: %s linhas carregadas (ano=%s, cnpj=%s)",
                total_cnpj,
                ANO,
                cnpj,
            )

    elapsed = time.monotonic() - start
    logger.info(
        "raw_fns.repasses: %s linhas no total, %s municípios, em %.1fs",
        total_geral,
        len(MUNICIPIOS_REFERENCIA_CNPJ),
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
