"""Parsing das linhas brutas de indicadores de desempenho do Previne Brasil (DEMAS)."""

from __future__ import annotations

REQUIRED_FIELDS = (
    "uf",
    "municipio",
    "codigo_municipio",
    "quadrimestre",
    "competencia",
    "codigo_tipo_indicador",
    "visao_equipe",
    "numerador",
    "denominador_utilizador",
    "denominador_identificado",
    "denominador_estimado",
    "percentual",
    "percentual_quadrimestre",
    "cadastro",
    "base_externa",
    "populacao",
)

# Municípios de referência: mesmo código IBGE de 6 dígitos sem dígito
# verificador do CNES/SIA/SIH/SIM/SINASC (confirmado contra a API real:
# "codigo_municipio": 330455 para "RIO DE JANEIRO", 330380 para "PARATY",
# 330350 para "NOVA IGUAÇU"). Escopo MVP restringe a estes municípios (ver
# docs/fontes.md#escopo-de-volume-para-o-mvp).
MUNICIPIOS_REFERENCIA_CODIGO_MUNICIPIO = (330455, 330380, 330350)


def parse_indicador_desempenho(raw: dict) -> dict:
    """Normaliza uma linha bruta de indicador de desempenho do Previne Brasil.

    Espera os campos retornados por
    `include.collectors.sisab.client.fetch_indicadores_desempenho`.

    Exemplo:
        >>> parse_indicador_desempenho(raw)["codigo_tipo_indicador"]
        10
    """
    valores = {}
    for campo in REQUIRED_FIELDS:
        try:
            valores[campo] = raw[campo]
        except KeyError as exc:
            raise ValueError(
                f"Linha de indicador de desempenho {raw!r} sem campo obrigatório "
                f"{exc}; esperado {REQUIRED_FIELDS}."
            ) from exc

    return {campo: valores[campo] for campo in REQUIRED_FIELDS}


def parse_indicadores_desempenho(raw_linhas: list[dict]) -> list[dict]:
    """Aplica parse_indicador_desempenho a cada item da lista bruta do DEMAS."""
    return [parse_indicador_desempenho(raw) for raw in raw_linhas]


REQUIRED_CADASTRO_VINCULADO_FIELDS = (
    "competencia_referencia",
    "sigla_unidade_federacao",
    "codigo_municipio_ibge",
    "nome_municipio",
    "estimativa_populacional_ibge",
    "tipo_equipe",
    "sigla_equipe",
    "situacao_equipe",
    "pessoas_vinculadas_criterios_ponderacao",
    "pessoas_vinculadas_equipe_municipio",
)


def parse_cadastro_vinculado(raw: dict) -> dict:
    """Normaliza uma linha DEMAS de população vinculada por equipe (cadastro vinculado).

    Espera os campos retornados por
    `include.collectors.sisab.client.fetch_cadastro_vinculado`.

    Exemplo:
        >>> parse_cadastro_vinculado(raw)["sigla_equipe"]
        'eSF'
    """
    valores = {}
    for campo in REQUIRED_CADASTRO_VINCULADO_FIELDS:
        try:
            valores[campo] = raw[campo]
        except KeyError as exc:
            raise ValueError(
                f"Linha de cadastro vinculado {raw!r} sem campo obrigatório {exc}; "
                f"esperado {REQUIRED_CADASTRO_VINCULADO_FIELDS}."
            ) from exc
    return {campo: valores[campo] for campo in REQUIRED_CADASTRO_VINCULADO_FIELDS}


def parse_cadastros_vinculados(raw_linhas: list[dict]) -> list[dict]:
    """Normaliza cada linha de cadastro vinculado retornada pelo DEMAS."""
    return [parse_cadastro_vinculado(raw) for raw in raw_linhas]
