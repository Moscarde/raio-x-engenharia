"""Entrypoint manual da ingestão de indicadores de desempenho do Previne Brasil (SISAB).

Uso:
    python -m include.collectors.sisab.run_indicador_desempenho
"""

from __future__ import annotations

import logging
import time

from include.collectors.sisab.client import (
    ENDPOINT_INDICADOR_DESEMPENHO,
    fetch_indicadores_desempenho,
)
from include.collectors.sisab.db import get_connection
from include.collectors.sisab.parser import (
    MUNICIPIOS_REFERENCIA_CODIGO_MUNICIPIO,
    parse_indicadores_desempenho,
)
from include.collectors.sisab.repository import (
    ensure_schema,
    substituir_indicadores_desempenho,
)

# O Programa Previne Brasil (fonte destes indicadores) foi extinto pela
# Portaria GM/MS Nº 3.493/2024 e substituído por nova metodologia de
# cofinanciamento — a série de dados para no fim no 3º quadrimestre de
# 2024 (confirmado: 2025Q1/Q2/Q3 não retornam dado na API). Diferente do
# escopo padrão do MVP (ano 2025), esta fonte usa o último quadrimestre
# realmente disponível.
QUADRIMESTRE = "2024Q3"

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava os indicadores de QUADRIMESTRE em raw_sisab.indicador_desempenho.

    A API do DEMAS filtra por município na própria consulta (client.py), não
    tem recorte por UF inteira como as fontes DBC — por isso 1 município por
    chamada, iterando os municípios de referência do MVP.
    """
    start = time.monotonic()
    total_geral = 0

    with get_connection() as conn:
        ensure_schema(conn)

        for municipio in MUNICIPIOS_REFERENCIA_CODIGO_MUNICIPIO:
            raw_linhas = fetch_indicadores_desempenho(municipio, QUADRIMESTRE)
            indicadores = parse_indicadores_desempenho(raw_linhas)
            total_municipio = substituir_indicadores_desempenho(
                conn,
                indicadores,
                municipio,
                QUADRIMESTRE,
                ENDPOINT_INDICADOR_DESEMPENHO,
            )
            total_geral += total_municipio
            logger.info(
                "raw_sisab.indicador_desempenho: %s linhas carregadas (municipio=%s, quadrimestre=%s)",
                total_municipio,
                municipio,
                QUADRIMESTRE,
            )

    elapsed = time.monotonic() - start
    logger.info(
        "raw_sisab.indicador_desempenho: %s linhas no total, %s municípios, em %.1fs",
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
