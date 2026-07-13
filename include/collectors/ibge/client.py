"""Cliente HTTP para as APIs públicas de localidades e agregados do IBGE."""

from __future__ import annotations

import requests

MUNICIPIOS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

# Agregado 6579 (SIDRA): Estimativas da população residente para os
# municípios, referência 1º de julho de cada ano — a mesma base usada pelo
# TCU/FPM. Variável 9324 é a população residente estimada (a única variável
# do agregado). Confirmado contra a API real: período "-1" retorna o último
# ano disponível (2025 em 2026-07), sem precisar descobrir o ano na mão.
POPULACAO_AGREGADO = 6579
POPULACAO_VARIAVEL = 9324
POPULACAO_URL = (
    f"https://servicodados.ibge.gov.br/api/v3/agregados/{POPULACAO_AGREGADO}"
    f"/periodos/-1/variaveis/{POPULACAO_VARIAVEL}"
)


def fetch_municipios(timeout: int = 30) -> list[dict]:
    """Busca a lista bruta de municípios na API do IBGE.

    Não faz parsing: retorna o JSON decodificado como veio da API.

    Exemplo:
        >>> municipios = fetch_municipios()
        >>> municipios[0]["nome"]
        "Alta Floresta D'Oeste"
    """
    response = requests.get(MUNICIPIOS_URL, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(
            f"IBGE respondeu status {response.status_code} para {MUNICIPIOS_URL}; "
            "esperado 200 com lista JSON de municípios."
        )
    return response.json()


def fetch_populacao_estimada(
    ids_municipio: tuple[int, ...], timeout: int = 30
) -> list[dict]:
    """Busca a população residente estimada (agregado 6579) para os municípios dados.

    Não faz parsing: retorna o JSON decodificado como veio da API (formato
    "agregados" do SIDRA, uma série por município dentro de `resultados`).

    Exemplo:
        >>> corpo = fetch_populacao_estimada((3304557,))
        >>> corpo[0]["variavel"]
        'População residente estimada'
    """
    localidades = ",".join(str(i) for i in ids_municipio)
    params = {"localidades": f"N6[{localidades}]"}
    return _fetch_populacao_estimada(params, timeout, contexto=str(ids_municipio))


def fetch_populacao_estimada_uf(codigo_uf: int, timeout: int = 30) -> list[dict]:
    """Busca a população estimada (agregado 6579) de todos os municípios de uma UF.

    Sintaxe de localidade aninhada do SIDRA (`N6[N3[uf]]` = "todos os
    municípios dentro do estado uf") confirmada contra a API real: RJ (33)
    retorna 92 municípios numa chamada só, em vez de uma lista fixa de ids.

    Exemplo:
        >>> corpo = fetch_populacao_estimada_uf(33)
        >>> len(corpo[0]["resultados"][0]["series"])
        92
    """
    params = {"localidades": f"N6[N3[{codigo_uf}]]"}
    return _fetch_populacao_estimada(params, timeout, contexto=f"uf={codigo_uf}")


def _fetch_populacao_estimada(params: dict, timeout: int, contexto: str) -> list[dict]:
    response = requests.get(POPULACAO_URL, params=params, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(
            f"IBGE respondeu status {response.status_code} para {POPULACAO_URL} "
            f"({contexto}); esperado 200 com JSON de agregados."
        )
    return response.json()
