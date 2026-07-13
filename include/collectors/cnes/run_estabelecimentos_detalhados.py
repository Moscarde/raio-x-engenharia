"""Entrypoint manual da ingestão de estabelecimentos detalhados do CNES (DEMAS).

Uso:
    python -m include.collectors.cnes.run_estabelecimentos_detalhados
"""

from __future__ import annotations

import logging
import time

from include.collectors.cnes.client import (
    ENDPOINT_ESTABELECIMENTOS_DETALHADOS,
    fetch_estabelecimentos_detalhados,
)
from include.collectors.cnes.db import get_connection
from include.collectors.cnes.parser import parse_estabelecimentos_detalhados
from include.collectors.cnes.repository import (
    ensure_schema_estabelecimentos_detalhados,
    upsert_estabelecimentos_detalhados,
)

# Municípios de referência do MVP (id_municipio em raw_ibge.municipios:
# Rio de Janeiro 3304557, Paraty 3303807, Nova Iguaçu 3303500), pelo
# código IBGE de 6 dígitos que a API DEMAS espera em codigo_municipio —
# mesmos códigos de MUNICIPIOS_REFERENCIA_CODUFMUN em parser.py.
MUNICIPIOS_REFERENCIA_CODIGO_MUNICIPIO = (330455, 330380, 330350)

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava estabelecimentos detalhados em raw_cnes.estabelecimentos_detalhados.

    API pagina 20 por vez sem total exposto — cada município leva vários
    minutos pra paginar por completo (ex.: Rio de Janeiro, ~18 mil
    estabelecimentos, ~900 páginas).
    """
    start = time.monotonic()
    total_geral = 0

    with get_connection() as conn:
        ensure_schema_estabelecimentos_detalhados(conn)

        for municipio in MUNICIPIOS_REFERENCIA_CODIGO_MUNICIPIO:
            inicio_municipio = time.monotonic()
            raw_estabelecimentos = fetch_estabelecimentos_detalhados(municipio)
            estabelecimentos = parse_estabelecimentos_detalhados(raw_estabelecimentos)
            total_municipio = upsert_estabelecimentos_detalhados(
                conn, estabelecimentos, ENDPOINT_ESTABELECIMENTOS_DETALHADOS
            )
            total_geral += total_municipio
            logger.info(
                "raw_cnes.estabelecimentos_detalhados: %s linhas carregadas em "
                "%.1fs (municipio=%s)",
                total_municipio,
                time.monotonic() - inicio_municipio,
                municipio,
            )

    elapsed = time.monotonic() - start
    logger.info(
        "raw_cnes.estabelecimentos_detalhados: %s linhas no total, %s "
        "municípios, em %.1fs",
        total_geral,
        len(MUNICIPIOS_REFERENCIA_CODIGO_MUNICIPIO),
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
