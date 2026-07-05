"""Entrypoint manual da ingestão do RREO-Anexo 14 (SICONFI) para o Rio de Janeiro.

Uso:
    python -m include.collectors.siops.run_rreo_anexo14
"""

from __future__ import annotations

import logging
import time

from include.collectors.siops.client import ENDPOINT_RREO, fetch_rreo_anexo14
from include.collectors.siops.db import get_connection
from include.collectors.siops.parser import (
    MUNICIPIOS_REFERENCIA_ID_ENTE,
    parse_linhas_rreo,
)
from include.collectors.siops.repository import ensure_schema, substituir_rreo_anexo14

ANO = 2025

# Os valores do RREO são cumulativos "até o bimestre" dentro do exercício,
# não incrementais por bimestre (confirmado: "Despesas Empenhadas" no
# periodo=6 já é o total do ano). Por isso basta buscar o 6º bimestre
# (fechamento do exercício), diferente de SIA/SIH (série de eventos por
# competência, onde os 12 meses precisam ser somados).
PERIODO_FECHAMENTO_EXERCICIO = 6

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava o RREO-Anexo 14 de ANO em raw_siops.rreo_anexo14.

    1 chamada por id_ente (código IBGE completo) de referência — a API do
    SICONFI filtra por ente na própria consulta, sem recorte por UF inteira.
    """
    start = time.monotonic()
    total_geral = 0

    with get_connection() as conn:
        ensure_schema(conn)

        for id_ente in MUNICIPIOS_REFERENCIA_ID_ENTE:
            raw_linhas = fetch_rreo_anexo14(id_ente, ANO, PERIODO_FECHAMENTO_EXERCICIO)
            linhas = parse_linhas_rreo(raw_linhas)
            total_ente = substituir_rreo_anexo14(
                conn,
                linhas,
                id_ente,
                ANO,
                PERIODO_FECHAMENTO_EXERCICIO,
                ENDPOINT_RREO,
            )
            total_geral += total_ente
            logger.info(
                "raw_siops.rreo_anexo14: %s linhas carregadas (id_ente=%s, ano=%s, bimestre=%s)",
                total_ente,
                id_ente,
                ANO,
                PERIODO_FECHAMENTO_EXERCICIO,
            )

    elapsed = time.monotonic() - start
    logger.info(
        "raw_siops.rreo_anexo14: %s linhas no total, %s municípios, em %.1fs",
        total_geral,
        len(MUNICIPIOS_REFERENCIA_ID_ENTE),
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
