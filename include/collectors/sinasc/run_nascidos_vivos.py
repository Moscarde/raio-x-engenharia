"""Entrypoint manual da ingestão de nascidos vivos do SINASC.

Uso:
    python -m include.collectors.sinasc.run_nascidos_vivos
"""

from __future__ import annotations

import logging
import time

from include.collectors.sinasc.client import fetch_nascidos_vivos
from include.collectors.sinasc.db import get_connection
from include.collectors.sinasc.parser import (
    MUNICIPIO_REFERENCIA_CODUFMUN,
    parse_nascidos_vivos,
)
from include.collectors.sinasc.repository import ensure_schema, substituir_nascidos_vivos

UF = "RJ"

# O SINASC/DN é anual e consolidado com atraso maior que o SIM: 2025 e 2023
# ainda não estão publicados no FTP do DATASUS (confirmado; o último ano
# disponível para RJ é 2022). Diferente do escopo padrão do MVP (ano 2025,
# ver docs/fontes.md#escopo-de-volume-para-o-mvp), esta fonte usa o último
# ano realmente disponível.
ANO = 2022

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava os nascidos vivos de ANO em raw_sinasc.nascidos_vivos."""
    start = time.monotonic()
    raw_nascidos_vivos = fetch_nascidos_vivos(UF, ANO)
    nascidos_vivos = parse_nascidos_vivos(raw_nascidos_vivos)

    with get_connection() as conn:
        ensure_schema(conn)
        total = substituir_nascidos_vivos(
            conn, nascidos_vivos, MUNICIPIO_REFERENCIA_CODUFMUN, ANO
        )

    elapsed = time.monotonic() - start
    logger.info(
        "raw_sinasc.nascidos_vivos: %s linhas carregadas em %.1fs (ano=%s)",
        total,
        elapsed,
        ANO,
    )
    return total


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    run()
