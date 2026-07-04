"""Parsing dos lançamentos financeiros de Fundo a Fundo retornados pelo FNS."""

from __future__ import annotations

# Campos sempre presentes na resposta da API (confirmado contra amostra
# real); campos opcionais (ex.: numero_referencia_unica, nome_favorecido)
# ficam de fora e são lidos com .get(), porque o PostgREST retorna null
# quando o lançamento não tem essa informação (diferente das fontes DBC, em
# que todo campo de largura fixa sempre existe).
REQUIRED_FIELDS = (
    "id_lancamento_gestao_financeira",
    "cnpj_ente_solicitante_gestao_financeira",
    "nome_ente_solicitante_gestao_financeira",
    "tipo_operacao_gestao_financeira",
    "descricao_tipo_operacao_gestao_financeira",
    "descricao_gestao_financeira",
    "data_lancamento_gestao_financeira",
    "data_evento_lancamento_gestao_financeira",
    "valor_lancamento_gestao_financeira",
)

# Prefeitura do Rio de Janeiro: id_municipio 3304557 em raw_ibge.municipios.
# O FNS identifica o ente por CNPJ, não por código IBGE (confirmado contra a
# API real: cnpj "42498733000148" -> nome_ente "MUNICIPIO DE RIO DE JANEIRO").
# O de-para CNPJ -> id_municipio fica para a camada staging/dbt, não para o
# raw layer. Escopo MVP restringe a este município (ver
# docs/fontes.md#escopo-de-volume-para-o-mvp).
MUNICIPIO_REFERENCIA_CNPJ = "42498733000148"


def parse_lancamento(raw: dict) -> dict:
    """Normaliza um lançamento bruto de Fundo a Fundo para raw_fns.repasses.

    Espera os campos retornados por
    `include.collectors.fns.client.fetch_lancamentos`.

    Exemplo:
        >>> parse_lancamento(raw)["cnpj_ente_solicitante"]
        '42498733000148'
    """
    valores = {}
    for campo in REQUIRED_FIELDS:
        try:
            valores[campo] = raw[campo]
        except KeyError as exc:
            raise ValueError(
                f"Lançamento FNS {raw!r} sem campo obrigatório {exc}; "
                f"esperado {REQUIRED_FIELDS}."
            ) from exc

    return {
        "id_lancamento": valores["id_lancamento_gestao_financeira"],
        "cnpj_ente_solicitante": valores["cnpj_ente_solicitante_gestao_financeira"],
        "nome_ente_solicitante": valores["nome_ente_solicitante_gestao_financeira"],
        "codigo_programa_agil": raw.get(
            "codigo_programa_agil_ente_solicitante_gestao_financeira"
        ),
        "tipo_operacao": valores["tipo_operacao_gestao_financeira"],
        "descricao_tipo_operacao": valores[
            "descricao_tipo_operacao_gestao_financeira"
        ],
        "descricao_lancamento": valores["descricao_gestao_financeira"],
        "data_lancamento": valores["data_lancamento_gestao_financeira"],
        "data_evento_lancamento": valores["data_evento_lancamento_gestao_financeira"],
        "numero_referencia_unica": raw.get(
            "numero_referencia_unica_gestao_financeira"
        ),
        "tipo_favorecido": raw.get("tipo_favorecido_gestao_financeira"),
        "descricao_tipo_favorecido": raw.get(
            "descricao_tipo_favorecido_gestao_financeira"
        ),
        "nome_favorecido": raw.get("nome_favorecido_gestao_financeira"),
        "valor_lancamento": valores["valor_lancamento_gestao_financeira"],
        "id_categoria_despesa": raw.get("id_categoria_despesa_gestao_financeira"),
        "quantidade_subtransacoes": raw.get(
            "quantidade_subtransacoes_lancamento_gestao_financeira"
        ),
    }


def parse_lancamentos(raw_lancamentos: list[dict]) -> list[dict]:
    """Aplica parse_lancamento a cada item da lista bruta da API do FNS."""
    return [parse_lancamento(raw) for raw in raw_lancamentos]
