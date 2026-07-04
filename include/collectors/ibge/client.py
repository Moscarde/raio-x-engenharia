"""Cliente HTTP para a API pública de localidades do IBGE."""

from __future__ import annotations

import requests

MUNICIPIOS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"


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
