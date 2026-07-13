"""Cliente para estabelecimentos de saúde (CNES) via pysus (FTP/DBC) e DEMAS (API)."""

from __future__ import annotations

import pysus
import requests

GROUP_ESTABELECIMENTOS = "ST"
GROUP_EQUIPES_APS = "EP"

# O grupo "ST" do FTP/DBC (fetch_estabelecimentos acima) não tem nome de
# estabelecimento nem endereço — só códigos (ver
# docs/COLLECTOR_TEMPLATE.md). A API de Dados Abertos do Ministério da
# Saúde (DEMAS) expõe um cadastro de estabelecimentos complementar, com
# nome_fantasia/nome_razao_social, endereço, geolocalização e
# esfera_administrativa já decodificada (diferente do valor cru do DBC) —
# usada pela demanda "Rede CNES detalhada" (ver ROADMAP.md).
DEMAS_API_BASE_URL = "https://apidadosabertos.saude.gov.br"
ENDPOINT_ESTABELECIMENTOS_DETALHADOS = f"{DEMAS_API_BASE_URL}/cnes/estabelecimentos"

# Confirmado contra a API real: limit é hard-capped em 20 por página,
# mesmo pedindo um valor maior (limit=1000 retorna só 20 linhas).
LIMITE_PAGINA_DEMAS = 20


def source_filename(
    uf: str, ano: int, mes: int, group: str = GROUP_ESTABELECIMENTOS
) -> str:
    """Nome do arquivo DBC de origem no FTP do DATASUS para uf/ano/mes.

    Exemplo:
        >>> source_filename("RJ", 2025, 12)
        'STRJ2512.dbc'
        >>> source_filename("RJ", 2025, 12, GROUP_EQUIPES_APS)
        'EPRJ2512.dbc'
    """
    return f"{group}{uf.upper()}{ano % 100:02d}{mes:02d}.dbc"


def fetch_estabelecimentos(uf: str, ano: int, mes: int) -> list[dict]:
    """Busca estabelecimentos de saúde do CNES (grupo Estabelecimentos) para uf/ano/mes.

    Não faz parsing: retorna um dict por estabelecimento com as colunas
    originais do grupo "ST", cru. `pysus` resolve o download FTP do arquivo
    DBC e a decompressão para tabular.

    Exemplo:
        >>> registros = fetch_estabelecimentos("RJ", 2025, 12)
        >>> registros[0]["CODUFMUN"]
        '330010'
    """
    dataframe = pysus.cnes(
        state=uf, year=ano, month=mes, group=GROUP_ESTABELECIMENTOS, as_dataframe=True
    )
    if dataframe.empty:
        raise RuntimeError(
            f"CNES não retornou registros para uf={uf!r}, ano={ano}, mes={mes}, "
            f"grupo={GROUP_ESTABELECIMENTOS!r} ({source_filename(uf, ano, mes)}); "
            "esperado DataFrame não vazio."
        )
    return dataframe.to_dict("records")


def fetch_equipes_aps(uf: str, ano: int, mes: int) -> list[dict]:
    """Busca o cadastro CNES de equipes de APS (grupo Equipes) para uf/ano/mes.

    Não faz parsing: retorna um dict por equipe com as colunas originais do
    grupo "EP", cru — inclui equipes de todos os tipos (eSF, eSB/odonto,
    NASF etc.), não só as de APS; o filtro por tipo acontece no parser
    (confirmado contra amostra real: 6.861 linhas para RJ dez/2025, campos
    de equipe — IDEQUIPE, TIPO_EQP, NOME_EQP, DT_ATIVA/DT_DESAT — misturados
    com as colunas de estabelecimento do grupo "ST").

    Exemplo:
        >>> registros = fetch_equipes_aps("RJ", 2025, 12)
        >>> registros[0]["TIPO_EQP"]
        '71'
    """
    dataframe = pysus.cnes(
        state=uf, year=ano, month=mes, group=GROUP_EQUIPES_APS, as_dataframe=True
    )
    if dataframe.empty:
        raise RuntimeError(
            f"CNES não retornou equipes para uf={uf!r}, ano={ano}, mes={mes}, "
            f"grupo={GROUP_EQUIPES_APS!r} "
            f"({source_filename(uf, ano, mes, GROUP_EQUIPES_APS)}); "
            "esperado DataFrame não vazio."
        )
    return dataframe.to_dict("records")


def fetch_estabelecimentos_detalhados(
    codigo_municipio: int, timeout: int = 30
) -> list[dict]:
    """Busca todos os estabelecimentos detalhados (nome, endereço, geo) via DEMAS.

    Pagina via offset até uma página vir vazia — API sem campo de total.
    Não filtra por status (ativo/inativo): traz o cadastro completo, igual
    ao grupo "ST" do FTP, pra manter a mesma filosofia de raw completo.

    Exemplo:
        >>> registros = fetch_estabelecimentos_detalhados(330455)
        >>> registros[0]["nome_fantasia"]
        'JUACIARA CARDEAL DE MIRANDA'
    """
    linhas: list[dict] = []
    offset = 0
    while True:
        pagina = _fetch_pagina_estabelecimentos_detalhados(
            codigo_municipio, offset, timeout
        )
        if not pagina:
            break
        linhas.extend(pagina)
        offset += LIMITE_PAGINA_DEMAS
    if not linhas:
        raise RuntimeError(
            f"DEMAS não retornou estabelecimentos para codigo_municipio="
            f"{codigo_municipio} em {ENDPOINT_ESTABELECIMENTOS_DETALHADOS}; "
            "esperado ao menos 1 registro."
        )
    return linhas


def _fetch_pagina_estabelecimentos_detalhados(
    codigo_municipio: int, offset: int, timeout: int
) -> list[dict]:
    params = {
        "codigo_municipio": codigo_municipio,
        "limit": LIMITE_PAGINA_DEMAS,
        "offset": offset,
    }
    response = requests.get(
        ENDPOINT_ESTABELECIMENTOS_DETALHADOS, params=params, timeout=timeout
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"DEMAS respondeu status {response.status_code} para "
            f"{ENDPOINT_ESTABELECIMENTOS_DETALHADOS} "
            f"(codigo_municipio={codigo_municipio}, offset={offset}); "
            "esperado 200 com lista JSON."
        )
    corpo = response.json()
    linhas = corpo.get("estabelecimentos")
    if linhas is None:
        raise RuntimeError(
            "Resposta do DEMAS sem campo 'estabelecimentos' para "
            f"codigo_municipio={codigo_municipio}, offset={offset}: {corpo!r}."
        )
    return linhas
