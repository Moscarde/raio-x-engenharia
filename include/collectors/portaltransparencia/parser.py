"""Parsing dos registros brutos de recursos recebidos (Portal da Transparência)."""

from __future__ import annotations

import re

REQUIRED_FIELDS = (
    "anoMes",
    "codigoPessoa",
    "nomePessoa",
    "tipoPessoa",
    "municipioPessoa",
    "siglaUFPessoa",
    "codigoUG",
    "nomeUG",
    "codigoOrgao",
    "nomeOrgao",
    "codigoOrgaoSuperior",
    "nomeOrgaoSuperior",
    "valor",
)

# Mesmos 3 CNPJs de Fundo Municipal de Saúde já usados pelo collector FNS
# (include/collectors/fns/parser.py) — descobertos consultando a própria API
# do FNS por nome do ente, documentado em ROADMAP.md. Repetido aqui (não
# importado do módulo fns) para manter as duas fontes independentes, como
# as demais fontes deste projeto.
MUNICIPIOS_REFERENCIA_CNPJ = (
    "42498733000148",
    "29172475000147",
    "29138278000101",
)


def _somente_digitos(cnpj: str) -> str:
    return re.sub(r"\D", "", cnpj)


def parse_recurso_recebido(raw: dict) -> dict:
    """Normaliza um registro bruto de recurso recebido para raw_portaltransparencia.

    Espera os campos retornados por
    `include.collectors.portaltransparencia.client.fetch_recursos_recebidos`.
    `codigoPessoa` vem formatado com pontuação (ex.: "42.498.733/0001-48");
    normalizado para só dígitos, mesmo formato usado por
    `raw_fns.repasses.cnpj_ente_solicitante`.

    Exemplo:
        >>> parse_recurso_recebido(raw)["cnpj_favorecido"]
        '42498733000148'
    """
    valores = {}
    for campo in REQUIRED_FIELDS:
        try:
            valores[campo] = raw[campo]
        except KeyError as exc:
            raise ValueError(
                f"Registro de recurso recebido {raw!r} sem campo obrigatório "
                f"{exc}; esperado {REQUIRED_FIELDS}."
            ) from exc

    return {
        "competencia": valores["anoMes"],
        "cnpj_favorecido": _somente_digitos(valores["codigoPessoa"]),
        "nome_favorecido": valores["nomePessoa"],
        "tipo_favorecido": valores["tipoPessoa"],
        "municipio_favorecido": valores["municipioPessoa"],
        "sigla_uf_favorecido": valores["siglaUFPessoa"],
        "codigo_ug": valores["codigoUG"],
        "nome_ug": valores["nomeUG"],
        "codigo_orgao": valores["codigoOrgao"],
        "nome_orgao": valores["nomeOrgao"],
        "codigo_orgao_superior": valores["codigoOrgaoSuperior"],
        "nome_orgao_superior": valores["nomeOrgaoSuperior"],
        # Pode ser negativo — estorno/devolução de recurso (confirmado
        # contra amostra real: -R$ 222.835,44 num lançamento do INCA-RJ para
        # o Rio de Janeiro em fev/2025). Não é erro do collector nem do
        # parser; mantido como veio da fonte.
        "valor": valores["valor"],
    }


def parse_recursos_recebidos(raw_linhas: list[dict]) -> list[dict]:
    """Aplica parse_recurso_recebido a cada item da lista bruta da API."""
    return [parse_recurso_recebido(raw) for raw in raw_linhas]
