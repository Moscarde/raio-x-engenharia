"""Entrypoint manual da ingestão de óbitos do SIM.

Uso:
    python -m include.collectors.sim.run_obitos
"""

from __future__ import annotations

import logging
import time

from include.collectors.sim.client import fetch_obitos
from include.collectors.sim.db import get_connection
from include.collectors.sim.parser import MUNICIPIO_REFERENCIA_CODUFMUN, parse_obitos
from include.collectors.sim.repository import ensure_schema, substituir_obitos

UF = "RJ"

# O SIM/DO é anual e consolidado com atraso: 2025 ainda não está publicado
# no FTP do DATASUS (confirmado; o último ano disponível para RJ é 2024).
# Diferente do escopo padrão do MVP (ano 2025, ver
# docs/fontes.md#escopo-de-volume-para-o-mvp), esta fonte usa o último ano
# realmente disponível.
ANO = 2024

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava os óbitos de ANO em raw_sim.obitos."""
    start = time.monotonic()
    raw_obitos = fetch_obitos(UF, ANO)
    obitos = parse_obitos(raw_obitos)

    with get_connection() as conn:
        ensure_schema(conn)
        total = substituir_obitos(conn, obitos, MUNICIPIO_REFERENCIA_CODUFMUN, ANO)

    elapsed = time.monotonic() - start
    logger.info(
        "raw_sim.obitos: %s linhas carregadas em %.1fs (ano=%s)",
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
