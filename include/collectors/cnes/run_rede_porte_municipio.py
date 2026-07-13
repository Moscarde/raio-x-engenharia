"""Entrypoint manual da contagem de estabelecimentos de saúde por município do RJ.

Uso:
    python -m include.collectors.cnes.run_rede_porte_municipio

Alimenta a demanda "Comparação entre pares" (ver ROADMAP.md) com um atributo
de porte de rede (quantidade de estabelecimentos) para todos os municípios
do RJ, não só os 3 de referência. Reaproveita fetch_estabelecimentos (mesmo
grupo "ST" já usado por run_estabelecimentos.py) — só 1 competência (a mais
recente), porque porte de rede aqui é um atributo de comparação/pareamento,
não uma série histórica.
"""

from __future__ import annotations

import logging
import time

from include.collectors.cnes.client import fetch_estabelecimentos, source_filename
from include.collectors.cnes.db import get_connection
from include.collectors.cnes.parser import parse_rede_porte_municipio
from include.collectors.cnes.repository import (
    ensure_schema_rede_porte_municipio,
    substituir_rede_porte_municipio,
)

UF = "RJ"
ANO = 2025
MES = 12

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, agrega e grava a contagem de estabelecimentos em raw_cnes.rede_porte_municipio."""
    start = time.monotonic()
    raw_estabelecimentos = fetch_estabelecimentos(UF, ANO, MES)
    contagens = parse_rede_porte_municipio(raw_estabelecimentos)
    source_file = source_filename(UF, ANO, MES)

    with get_connection() as conn:
        ensure_schema_rede_porte_municipio(conn)
        competencia = contagens[0]["competencia"] if contagens else f"{ANO}{MES:02d}"
        total = substituir_rede_porte_municipio(
            conn, contagens, competencia, source_file
        )

    elapsed = time.monotonic() - start
    logger.info(
        "raw_cnes.rede_porte_municipio: %s municípios em %.1fs (uf=%s, competencia=%s)",
        total,
        elapsed,
        UF,
        ANO * 100 + MES,
    )
    return total


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    run()
