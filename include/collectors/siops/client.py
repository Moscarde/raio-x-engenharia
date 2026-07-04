"""Cliente HTTP para o RREO-Anexo 14 (LC 141/2012) via API SICONFI do Tesouro Nacional.

O site legado do SIOPS (siops.datasus.gov.br) foi investigado primeiro
(rota candidata em docs/fontes.md), mas seu relatório de cálculo do % de
saúde retorna respostas de 300+ MB com valores zerados para o Rio de
Janeiro em 2021-2024 (bug real do sistema legado, confirmado testando
manualmente contra a fonte). O SICONFI (Tesouro Nacional,
https://apidatalake.tesouro.gov.br/) é o substituto de fato: é onde os
entes federativos hoje transmitem o RREO (Relatório Resumido de Execução
Orçamentária), cujo Anexo 14 ("Demonstrativo Simplificado") inclui a linha
"Despesas com Ações e Serviços Públicos de Saúde Executadas com Recursos
de Impostos" — o mesmo indicador de aplicação mínima em saúde da LC 141,
com dado real e atualizado (confirmado: Rio de Janeiro, 2025, todos os 6
bimestres com dado populado).
"""

from __future__ import annotations

import requests

API_BASE_URL = "https://apidatalake.tesouro.gov.br/ords/cdwhprd/siconfi/tt"
ENDPOINT_RREO = f"{API_BASE_URL}/rreo"
ANEXO_DEMONSTRATIVO_SIMPLIFICADO = "RREO-Anexo 14"


def fetch_rreo_anexo14(id_ente: int, ano: int, periodo: int, timeout: int = 30) -> list[dict]:
    """Busca o RREO-Anexo 14 do SICONFI para o ente/ano/bimestre informados.

    Não faz parsing: retorna a lista de dicts como veio da API, uma linha
    por conta do demonstrativo (ex.: "Despesas Empenhadas", "Despesas com
    Ações e Serviços Públicos de Saúde...").

    Exemplo:
        >>> linhas = fetch_rreo_anexo14(3304557, 2025, 6)
        >>> linhas[0]["cod_ibge"]
        3304557
    """
    params = {
        "an_exercicio": ano,
        "nr_periodo": periodo,
        "co_tipo_demonstrativo": "RREO",
        "no_anexo": ANEXO_DEMONSTRATIVO_SIMPLIFICADO,
        "id_ente": id_ente,
    }
    response = requests.get(ENDPOINT_RREO, params=params, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(
            f"SICONFI respondeu status {response.status_code} para "
            f"{ENDPOINT_RREO} (id_ente={id_ente}, ano={ano}, periodo={periodo}); "
            "esperado 200 com lista JSON de contas do RREO."
        )

    corpo = response.json()
    linhas = corpo.get("items")
    if linhas is None:
        raise RuntimeError(
            f"Resposta do SICONFI sem campo 'items' para id_ente={id_ente}, "
            f"ano={ano}, periodo={periodo}: {corpo!r}."
        )
    if not linhas:
        raise RuntimeError(
            f"SICONFI não retornou linhas do {ANEXO_DEMONSTRATIVO_SIMPLIFICADO} "
            f"para id_ente={id_ente}, ano={ano}, periodo={periodo}; "
            "esperado ao menos 1 registro."
        )
    return linhas
