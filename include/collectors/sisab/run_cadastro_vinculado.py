"""Entrypoint manual da ingestão de cadastro vinculado do Previne Brasil (SISAB).

Uso:
    python -m include.collectors.sisab.run_cadastro_vinculado
"""

from __future__ import annotations

import logging
import time

from include.collectors.sisab.client import (
    ENDPOINT_CADASTRO_VINCULADO,
    fetch_cadastro_vinculado,
)
from include.collectors.sisab.db import get_connection
from include.collectors.sisab.parser import (
    MUNICIPIOS_REFERENCIA_CODIGO_MUNICIPIO,
    parse_cadastros_vinculados,
)
from include.collectors.sisab.repository import (
    ensure_schema_cadastro_vinculado,
    substituir_cadastro_vinculado,
)

# Mesma extinção do Previne Brasil documentada em run_indicador_desempenho.py
# (Portaria GM/MS Nº 3.493/2024) — confirmado contra a API real que o
# cadastro vinculado também para em dez/2024 (202501-202512 sem dado).
COMPETENCIA_REFERENCIA = 202412

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava o cadastro vinculado em raw_sisab.cadastro_vinculado.

    Dá população estimada do IBGE (embutida na própria resposta do DEMAS) e
    pessoas vinculadas por tipo/situação de equipe (eSF/eAP/eAPP/eCR) — a
    base oficial de cobertura de APS que fundamenta o cofinanciamento
    federal. Como em run_indicador_desempenho.py, a API filtra por
    município na própria consulta, então itera os municípios de referência.
    """
    start = time.monotonic()
    total_geral = 0

    with get_connection() as conn:
        ensure_schema_cadastro_vinculado(conn)

        for municipio in MUNICIPIOS_REFERENCIA_CODIGO_MUNICIPIO:
            raw_linhas = fetch_cadastro_vinculado(municipio, COMPETENCIA_REFERENCIA)
            linhas = parse_cadastros_vinculados(raw_linhas)
            total_municipio = substituir_cadastro_vinculado(
                conn,
                linhas,
                municipio,
                COMPETENCIA_REFERENCIA,
                ENDPOINT_CADASTRO_VINCULADO,
            )
            total_geral += total_municipio
            logger.info(
                "raw_sisab.cadastro_vinculado: %s linhas carregadas (municipio=%s, competencia=%s)",
                total_municipio,
                municipio,
                COMPETENCIA_REFERENCIA,
            )

    elapsed = time.monotonic() - start
    logger.info(
        "raw_sisab.cadastro_vinculado: %s linhas no total, %s municípios, em %.1fs",
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
