"""Parsing dos registros brutos de município retornados pela API do IBGE."""

from __future__ import annotations

REQUIRED_CHAIN = "id, nome e microrregiao.mesorregiao.UF.regiao"


def _resolve_territorio(raw: dict) -> dict:
    """Resolve microrregiao/mesorregiao/UF/regiao de um município bruto do IBGE.

    Limitação conhecida da fonte: municípios muito recentes (ex.: Boa Esperança
    do Norte/MT, id 5101837, criado em 2024) ainda não têm microrregiao nem
    mesorregiao cadastradas na API; nesse caso UF/regiao vêm da cadeia
    regiao-imediata.regiao-intermediaria.UF, e os campos de micro/mesorregiao
    ficam None.
    """
    microrregiao = raw.get("microrregiao")
    if microrregiao is None:
        try:
            uf = raw["regiao-imediata"]["regiao-intermediaria"]["UF"]
        except KeyError as exc:
            raise ValueError(
                f"Município {raw!r} sem microrregiao e sem "
                "regiao-imediata.regiao-intermediaria.UF; não é possível resolver UF/regiao."
            ) from exc
        return {
            "id_microrregiao": None,
            "nome_microrregiao": None,
            "id_mesorregiao": None,
            "nome_mesorregiao": None,
            "uf": uf,
        }

    try:
        mesorregiao = microrregiao["mesorregiao"]
        uf = mesorregiao["UF"]
    except KeyError as exc:
        raise ValueError(
            f"Município {raw!r} com microrregiao sem mesorregiao.UF; "
            f"esperado {REQUIRED_CHAIN}."
        ) from exc
    return {
        "id_microrregiao": microrregiao["id"],
        "nome_microrregiao": microrregiao["nome"],
        "id_mesorregiao": mesorregiao["id"],
        "nome_mesorregiao": mesorregiao["nome"],
        "uf": uf,
    }


def parse_municipio(raw: dict) -> dict:
    """Normaliza um registro bruto de município para as colunas de raw_ibge.municipios.

    Espera o formato retornado por
    https://servicodados.ibge.gov.br/api/v1/localidades/municipios.

    Exemplo:
        >>> parse_municipio(raw)["id_municipio"]
        1100015
    """
    try:
        municipio_id = raw["id"]
        nome_municipio = raw["nome"]
    except KeyError as exc:
        raise ValueError(
            f"Registro de município {raw!r} sem campo obrigatório {exc}; esperado id e nome."
        ) from exc

    territorio = _resolve_territorio(raw)
    uf = territorio.pop("uf")
    try:
        regiao = uf["regiao"]
        return {
            "id_municipio": municipio_id,
            "nome_municipio": nome_municipio,
            **territorio,
            "id_uf": uf["id"],
            "sigla_uf": uf["sigla"],
            "nome_uf": uf["nome"],
            "id_regiao": regiao["id"],
            "sigla_regiao": regiao["sigla"],
            "nome_regiao": regiao["nome"],
        }
    except KeyError as exc:
        raise ValueError(
            f"Município {raw!r} com UF sem regiao; esperado UF.regiao com id/sigla/nome."
        ) from exc


def parse_municipios(raw_municipios: list[dict]) -> list[dict]:
    """Aplica parse_municipio a cada item da lista bruta da API do IBGE."""
    return [parse_municipio(raw) for raw in raw_municipios]


# Municípios de referência do MVP (mesmo conjunto do CNES/SIH/SIM/SINASC,
# aqui pelo id_municipio de 7 dígitos, formato nativo do agregado do IBGE —
# ver docs/fontes.md#escopo-de-volume-para-o-mvp).
MUNICIPIOS_REFERENCIA_ID_MUNICIPIO = (3304557, 3303807, 3303500)


def parse_populacao_estimada(corpo_agregado: list[dict]) -> list[dict]:
    """Normaliza a resposta do agregado 6579 (SIDRA) para 1 linha por município.

    Espera o formato retornado por
    `include.collectors.ibge.client.fetch_populacao_estimada`: uma lista com
    1 variável, cujas `resultados[].series[]` trazem 1 localidade cada, com
    `serie` mapeando ano (string) -> população (string).

    Exemplo:
        >>> parse_populacao_estimada(corpo)[0]["populacao_estimada"]
        6730729
    """
    try:
        variavel = corpo_agregado[0]
        series = variavel["resultados"][0]["series"]
    except (IndexError, KeyError) as exc:
        raise ValueError(
            f"Resposta do agregado de população {corpo_agregado!r} sem "
            "resultados[0].series; formato inesperado da API do IBGE."
        ) from exc

    linhas = []
    for item in series:
        try:
            localidade = item["localidade"]
            id_municipio = int(localidade["id"])
            ano, populacao = next(iter(item["serie"].items()))
        except (KeyError, StopIteration) as exc:
            raise ValueError(
                f"Série de população {item!r} sem localidade.id ou serie "
                "não vazia; formato inesperado da API do IBGE."
            ) from exc
        linhas.append(
            {
                "id_municipio": id_municipio,
                "nome_municipio": localidade["nome"],
                "ano_referencia": int(ano),
                "populacao_estimada": int(populacao),
            }
        )
    return linhas
