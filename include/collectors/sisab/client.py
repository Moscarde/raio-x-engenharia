"""Cliente HTTP para indicadores de desempenho do Previne Brasil (SISAB) via DEMAS.

A rota original do SISAB (`sisab.saude.gov.br`, painel de indicadores) exige
navegação restrita/sessão, sem download simples (ver docs/fontes.md e
ROADMAP.md). A rota real é a **API de Dados Abertos do Ministério da Saúde
(DEMAS)**, `https://apidadosabertos.saude.gov.br/`, documentada em
`/v1` (Swagger) — API REST JSON pública, sem autenticação, que expõe os
mesmos indicadores de desempenho do Programa Previne Brasil que o SISAB
calcula, com filtro nativo por código IBGE do município.
"""

from __future__ import annotations

import requests

API_BASE_URL = "https://apidadosabertos.saude.gov.br"
ENDPOINT_INDICADOR_DESEMPENHO = (
    f"{API_BASE_URL}/atencao-primaria/indicador-desempenho-programa-previne-brasil"
)

# Confirmado contra a API real: o Rio de Janeiro tem 18 linhas por
# quadrimestre (6 tipos de indicador x 3 visões de equipe), bem abaixo do
# limite de página abaixo (folga generosa para não truncar silenciosamente).
LIMITE_PAGINA = 1000


def fetch_indicadores_desempenho(
    codigo_municipio: int, quadrimestre: str, timeout: int = 30
) -> list[dict]:
    """Busca os indicadores de desempenho do Previne Brasil para município/quadrimestre.

    Não faz parsing: retorna a lista de dicts como veio da API, uma linha
    por combinação de tipo de indicador e visão de equipe.

    Exemplo:
        >>> linhas = fetch_indicadores_desempenho(330455, "2024Q3")
        >>> linhas[0]["codigo_municipio"]
        330455
    """
    params = {
        "codigo_municipio": codigo_municipio,
        "quadrimestre": quadrimestre,
        "limit": LIMITE_PAGINA,
    }
    response = requests.get(
        ENDPOINT_INDICADOR_DESEMPENHO, params=params, timeout=timeout
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"DEMAS respondeu status {response.status_code} para "
            f"{ENDPOINT_INDICADOR_DESEMPENHO} (codigo_municipio={codigo_municipio}, "
            f"quadrimestre={quadrimestre!r}); esperado 200 com lista JSON de "
            "indicadores."
        )

    corpo = response.json()
    linhas = corpo.get("sisab_indicador_desempenho")
    if linhas is None:
        raise RuntimeError(
            "Resposta do DEMAS sem campo 'sisab_indicador_desempenho' para "
            f"codigo_municipio={codigo_municipio}, quadrimestre={quadrimestre!r}: "
            f"{corpo!r}."
        )
    if not linhas:
        raise RuntimeError(
            f"DEMAS não retornou indicadores para codigo_municipio={codigo_municipio}, "
            f"quadrimestre={quadrimestre!r} em {ENDPOINT_INDICADOR_DESEMPENHO}; "
            "esperado ao menos 1 registro."
        )
    if len(linhas) >= LIMITE_PAGINA:
        raise RuntimeError(
            f"Resposta do DEMAS atingiu LIMITE_PAGINA={LIMITE_PAGINA} para "
            f"codigo_municipio={codigo_municipio}, quadrimestre={quadrimestre!r}; "
            "possível truncamento silencioso — aumentar LIMITE_PAGINA ou "
            "implementar paginação via offset."
        )
    return linhas
