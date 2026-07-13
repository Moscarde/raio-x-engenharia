"""Entrypoint manual da ingestão de população estimada de todos os municípios do RJ.

Uso:
    python -m include.collectors.ibge.run_populacao_estimada_rj

Escopo mais amplo que run_populacao_estimada.py (3 municípios de
referência): alimenta a demanda "Comparação entre pares" (ver ROADMAP.md),
que precisa de um universo de municípios maior que os 3 do MVP. Grava na
mesma tabela raw_ibge.populacao_estimada — upsert por (id_municipio,
ano_referencia), então roda sem conflito com run_populacao_estimada.py e
já inclui os 3 municípios de referência como subconjunto.
"""

from __future__ import annotations

import logging
import time

from include.collectors.ibge.client import POPULACAO_URL, fetch_populacao_estimada_uf
from include.collectors.ibge.db import get_connection
from include.collectors.ibge.parser import parse_populacao_estimada
from include.collectors.ibge.repository import (
    ensure_schema_populacao,
    upsert_populacao_estimada,
)

CODIGO_UF_RJ = 33

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava a população estimada de todos os municípios do RJ.

    Usa a sintaxe de localidade aninhada do SIDRA (N6[N3[33]]) — 1 chamada
    HTTP retorna os 92 municípios do estado, sem precisar de uma lista fixa
    de ids nem de paginação.
    """
    start = time.monotonic()
    corpo = fetch_populacao_estimada_uf(CODIGO_UF_RJ)
    populacao = parse_populacao_estimada(corpo)

    with get_connection() as conn:
        ensure_schema_populacao(conn)
        total = upsert_populacao_estimada(conn, populacao)

    elapsed = time.monotonic() - start
    logger.info(
        "raw_ibge.populacao_estimada: %s linhas carregadas em %.1fs (uf=RJ, fonte=%s)",
        total,
        elapsed,
        POPULACAO_URL,
    )
    return total


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    run()
