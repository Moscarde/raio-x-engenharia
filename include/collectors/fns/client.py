"""Cliente HTTP para a API pública de Transferências Fundo a Fundo (FNS).

Diferente das fontes DATASUS (DBC por UF inteira, sem recorte), esta API é
um PostgREST (https://api.transferegov.gestao.gov.br/fundoafundo/) que
aceita filtro por CNPJ e data diretamente na consulta — o recorte pelo
município de referência do MVP acontece aqui, na query, não depois no
parser.
"""

from __future__ import annotations

import requests

API_BASE_URL = "https://api.transferegov.gestao.gov.br/fundoafundo"
ENDPOINT_LANCAMENTOS = f"{API_BASE_URL}/gestao_financeira_lancamentos"

# Confirmado contra a API real: a Prefeitura do Rio de Janeiro teve 23
# lançamentos de Fundo a Fundo em 2025 nesta conta, bem abaixo do limite de
# página abaixo (folga generosa para não truncar silenciosamente).
LIMITE_PAGINA = 10_000


def fetch_lancamentos(cnpj: str, ano: int, timeout: int = 30) -> list[dict]:
    """Busca os lançamentos financeiros de Fundo a Fundo do FNS para cnpj/ano.

    Não faz parsing: retorna a lista de dicts como veio da API, cada um um
    lançamento (crédito ou débito) da conta do ente informado.

    Exemplo:
        >>> lancamentos = fetch_lancamentos("42498733000148", 2025)
        >>> lancamentos[0]["nome_ente_solicitante_gestao_financeira"]
        'MUNICIPIO DE RIO DE JANEIRO'
    """
    params = [
        ("cnpj_ente_solicitante_gestao_financeira", f"eq.{cnpj}"),
        ("data_lancamento_gestao_financeira", f"gte.{ano}-01-01"),
        ("data_lancamento_gestao_financeira", f"lte.{ano}-12-31"),
        ("order", "data_lancamento_gestao_financeira.asc"),
        ("limit", str(LIMITE_PAGINA)),
    ]
    response = requests.get(ENDPOINT_LANCAMENTOS, params=params, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(
            f"FNS respondeu status {response.status_code} para "
            f"{ENDPOINT_LANCAMENTOS} (cnpj={cnpj!r}, ano={ano}); esperado 200 "
            "com lista JSON de lançamentos."
        )

    registros = response.json()
    if not registros:
        raise RuntimeError(
            f"FNS não retornou lançamentos para cnpj={cnpj!r}, ano={ano} em "
            f"{ENDPOINT_LANCAMENTOS}; esperado ao menos 1 registro."
        )
    if len(registros) >= LIMITE_PAGINA:
        raise RuntimeError(
            f"Resposta da API FNS atingiu LIMITE_PAGINA={LIMITE_PAGINA} para "
            f"cnpj={cnpj!r}, ano={ano}; possível truncamento silencioso — "
            "aumentar LIMITE_PAGINA ou implementar paginação via range/offset."
        )
    return registros
