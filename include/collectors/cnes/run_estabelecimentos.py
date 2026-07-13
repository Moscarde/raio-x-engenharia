"""Entrypoint manual da ingestão de estabelecimentos do CNES.

Uso:
    python -m include.collectors.cnes.run_estabelecimentos
"""

from __future__ import annotations

import logging
import time

from include.collectors.cnes.client import fetch_estabelecimentos, source_filename
from include.collectors.cnes.db import get_connection
from include.collectors.cnes.parser import parse_estabelecimentos
from include.collectors.cnes.repository import ensure_schema, upsert_estabelecimentos

# Escopo MVP (docs/fontes.md#escopo-de-volume-para-o-mvp): 3 municípios de
# referência, ano de 2025. Diferente da carga original (1 única competência,
# dez/2025), agora carrega os 12 meses do ano: raw_cnes.estabelecimentos
# passou a ter chave (codigo_cnes, competencia) em vez de codigo_cnes só,
# então cada mês vira uma linha nova em vez de sobrescrever a anterior — é
# o que dá série histórica para a demanda "Histórico de rede CNES" (ver
# ROADMAP.md). dim_estabelecimento (dbt) segue expondo só a competência mais
# recente por estabelecimento.
UF = "RJ"
ANO = 2025
MESES = range(1, 13)

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava os 12 meses de 2025 em raw_cnes.estabelecimentos.

    Processa uma competência (mês) por vez, como run_internacoes.py (SIH):
    mantém uso de memória limitado a 1 mês e torna a execução retomável.
    """
    start = time.monotonic()
    total_geral = 0

    with get_connection() as conn:
        ensure_schema(conn)

        for mes in MESES:
            inicio_mes = time.monotonic()
            raw_estabelecimentos = fetch_estabelecimentos(UF, ANO, mes)
            estabelecimentos = parse_estabelecimentos(raw_estabelecimentos)
            arquivo_origem = source_filename(UF, ANO, mes)
            total_mes = upsert_estabelecimentos(
                conn, estabelecimentos, arquivo_origem, ANO, mes
            )
            total_geral += total_mes
            logger.info(
                "raw_cnes.estabelecimentos: %s linhas carregadas em %.1fs "
                "(competencia=%s-%02d, fonte=%s)",
                total_mes,
                time.monotonic() - inicio_mes,
                ANO,
                mes,
                arquivo_origem,
            )

    elapsed = time.monotonic() - start
    logger.info(
        "raw_cnes.estabelecimentos: %s linhas no total, %s competências, em %.1fs",
        total_geral,
        len(MESES),
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
