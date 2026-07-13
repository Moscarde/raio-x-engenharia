"""Cliente HTTP para a API de Dados do Portal da Transparência (Governo Federal).

Diferente das demais fontes deste projeto, esta API exige autenticação: uma
chave pessoal (`chave-api-dados`), obtida registrando um e-mail em
https://api.portaldatransparencia.gov.br/api-de-dados/cadastrar-email. A
chave é injetada por parâmetro nas funções deste módulo (nunca lida
diretamente do ambiente aqui) — `resolve_api_key()` faz essa leitura, e é
o `run_recursos_recebidos.py` quem chama e repassa o valor.

Endpoint usado: `/api-de-dados/despesas/recursos-recebidos` ("Recebimento de
recursos por favorecido"). Não existe mais, nesta API, um endpoint dedicado
a "transferências a municípios" (a rota antiga `/api-de-dados/transferencias`
responde 403 — descontinuada); o substituto de fato é filtrar
recursos-recebidos pelo CNPJ do próprio ente municipal como favorecido
(mesmo CNPJ já usado pelo collector FNS) e pelo órgão superior pagador,
não pelo `codigoIBGE` (que filtra pelo município de residência do
favorecido, não pela entidade que recebeu o recurso — confirmado contra a
API real: com `codigoIBGE` sozinho a resposta vem vazia para o Rio de
Janeiro, mas com `codigoFavorecido=<cnpj do município>` vêm registros reais).
"""

from __future__ import annotations

import os

import requests

API_BASE_URL = "https://api.portaldatransparencia.gov.br"
ENDPOINT_RECURSOS_RECEBIDOS = f"{API_BASE_URL}/api-de-dados/despesas/recursos-recebidos"

API_KEY_ENV_VAR = "PORTAL_TRANSPARENCIA_API_KEY"

# Código SIAFI do órgão superior "Ministério da Saúde - Unidades com vínculo
# direto" (confirmado contra /api-de-dados/orgaos-siafi). Filtra o escopo
# desta demanda ("financiamento municipal completo" de saúde) sem trazer
# repasses de outros ministérios que também aparecem para o mesmo CNPJ
# municipal (Educação, Cidades, folha de pagamento etc.).
ORGAO_SUPERIOR_MINISTERIO_DA_SAUDE = "36000"


def resolve_api_key() -> str:
    """Lê a chave de API do Portal da Transparência do ambiente.

    Ver .env.example — a chave é pessoal, registrada por e-mail em
    api.portaldatransparencia.gov.br/api-de-dados/cadastrar-email.
    """
    chave = os.environ.get(API_KEY_ENV_VAR)
    if not chave:
        raise RuntimeError(
            f"Variável de ambiente {API_KEY_ENV_VAR} ausente; defina-a no "
            ".env local com a chave pessoal registrada em "
            "api.portaldatransparencia.gov.br/api-de-dados/cadastrar-email "
            "(ver .env.example)."
        )
    return chave


def fetch_recursos_recebidos(
    chave_api: str,
    codigo_favorecido: str,
    mes_ano_inicio: str,
    mes_ano_fim: str,
    orgao_superior: str = ORGAO_SUPERIOR_MINISTERIO_DA_SAUDE,
    timeout: int = 30,
) -> list[dict]:
    """Busca todos os recursos recebidos por um favorecido (CNPJ) no período.

    Pagina via `pagina` até uma página vir vazia — a API não expõe total de
    resultados, só páginas de até 15 itens.

    Exemplo:
        >>> linhas = fetch_recursos_recebidos(
        ...     chave_api, "42498733000148", "01/2025", "12/2025"
        ... )
        >>> linhas[0]["nomeOrgaoSuperior"]
        'Ministério da Saúde'
    """
    linhas: list[dict] = []
    pagina = 1
    while True:
        pagina_linhas = _fetch_pagina_recursos_recebidos(
            chave_api,
            codigo_favorecido,
            mes_ano_inicio,
            mes_ano_fim,
            orgao_superior,
            pagina,
            timeout,
        )
        if not pagina_linhas:
            break
        linhas.extend(pagina_linhas)
        pagina += 1
    return linhas


def _fetch_pagina_recursos_recebidos(
    chave_api: str,
    codigo_favorecido: str,
    mes_ano_inicio: str,
    mes_ano_fim: str,
    orgao_superior: str,
    pagina: int,
    timeout: int,
) -> list[dict]:
    params = {
        "codigoFavorecido": codigo_favorecido,
        "orgaoSuperior": orgao_superior,
        "mesAnoInicio": mes_ano_inicio,
        "mesAnoFim": mes_ano_fim,
        "pagina": pagina,
    }
    headers = {"chave-api-dados": chave_api}
    response = requests.get(
        ENDPOINT_RECURSOS_RECEBIDOS, params=params, headers=headers, timeout=timeout
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"Portal da Transparência respondeu status {response.status_code} para "
            f"{ENDPOINT_RECURSOS_RECEBIDOS} (codigoFavorecido={codigo_favorecido!r}, "
            f"periodo={mes_ano_inicio}-{mes_ano_fim}, pagina={pagina}); esperado 200 "
            "com lista JSON (verifique se a chave em PORTAL_TRANSPARENCIA_API_KEY "
            "ainda é válida)."
        )
    return response.json()
