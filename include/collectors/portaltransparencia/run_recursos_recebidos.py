"""Entrypoint manual da ingestão de recursos recebidos (Portal da Transparência).

Uso:
    python -m include.collectors.portaltransparencia.run_recursos_recebidos
"""

from __future__ import annotations

import logging
import time

from include.collectors.portaltransparencia.client import (
    ENDPOINT_RECURSOS_RECEBIDOS,
    fetch_recursos_recebidos,
    resolve_api_key,
)
from include.collectors.portaltransparencia.db import get_connection
from include.collectors.portaltransparencia.parser import (
    MUNICIPIOS_REFERENCIA_CNPJ,
    parse_recursos_recebidos,
)
from include.collectors.portaltransparencia.repository import (
    ensure_schema,
    substituir_recursos_recebidos,
)

# Escopo MVP (docs/fontes.md#escopo-de-volume-para-o-mvp): municípios de
# referência, ano de 2025, órgão superior Ministério da Saúde (filtro padrão
# do client). Complementa raw_fns.repasses (só cobre o recorte "Programa
# Ágil" do Fundo a Fundo): esta fonte traz o financiamento federal de saúde
# de forma mais completa, por qualquer órgão/unidade vinculada ao
# Ministério da Saúde que tenha pago recursos ao ente municipal.
ANO = 2025
MES_ANO_INICIO = f"01/{ANO}"
MES_ANO_FIM = f"12/{ANO}"

logger = logging.getLogger(__name__)


def run() -> int:
    """Busca, normaliza e grava os recursos de 2025 em raw_portaltransparencia.

    1 chamada paginada por CNPJ de referência — delete+insert por partição
    (cnpj_favorecido + ano), como run_indicador_desempenho.py (SISAB).
    """
    start = time.monotonic()
    total_geral = 0
    chave_api = resolve_api_key()

    with get_connection() as conn:
        ensure_schema(conn)

        for cnpj in MUNICIPIOS_REFERENCIA_CNPJ:
            raw_linhas = fetch_recursos_recebidos(
                chave_api, cnpj, MES_ANO_INICIO, MES_ANO_FIM
            )
            linhas = parse_recursos_recebidos(raw_linhas)
            total_cnpj = substituir_recursos_recebidos(
                conn, linhas, cnpj, ANO, ENDPOINT_RECURSOS_RECEBIDOS
            )
            total_geral += total_cnpj
            logger.info(
                "raw_portaltransparencia.recursos_recebidos_saude: %s linhas "
                "carregadas (cnpj=%s, ano=%s)",
                total_cnpj,
                cnpj,
                ANO,
            )

    elapsed = time.monotonic() - start
    logger.info(
        "raw_portaltransparencia.recursos_recebidos_saude: %s linhas no "
        "total, %s municípios, em %.1fs",
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
