"""Parsing das linhas brutas do RREO-Anexo 14 retornadas pelo SICONFI."""

from __future__ import annotations

REQUIRED_FIELDS = (
    "exercicio",
    "demonstrativo",
    "periodo",
    "periodicidade",
    "instituicao",
    "cod_ibge",
    "uf",
    "populacao",
    "anexo",
    "esfera",
    "rotulo",
    "coluna",
    "cod_conta",
    "conta",
    "valor",
)

# Rio de Janeiro: mesmo id_municipio (7 dígitos) de raw_ibge.municipios —
# o SICONFI identifica o ente pelo código IBGE completo (cod_ibge), sem
# truncamento nem dígito verificador ausente como nas fontes DATASUS
# (CODUFMUN/MUNIC_MOV/CODMUNOCOR de 6 dígitos). Escopo MVP restringe a este
# município (ver docs/fontes.md#escopo-de-volume-para-o-mvp).
MUNICIPIO_REFERENCIA_ID_ENTE = 3304557


def parse_linha_rreo(raw: dict) -> dict:
    """Normaliza uma linha bruta do RREO-Anexo 14 para raw_siops.rreo_anexo14.

    Espera os campos retornados por
    `include.collectors.siops.client.fetch_rreo_anexo14`.

    Exemplo:
        >>> parse_linha_rreo(raw)["descricao_conta"]
        'Despesas com Ações e Serviços Públicos de Saúde Executadas com Recursos de Impostos'
    """
    valores = {}
    for campo in REQUIRED_FIELDS:
        try:
            valores[campo] = raw[campo]
        except KeyError as exc:
            raise ValueError(
                f"Linha do RREO {raw!r} sem campo obrigatório {exc}; "
                f"esperado {REQUIRED_FIELDS}."
            ) from exc

    return {
        "ano_exercicio": valores["exercicio"],
        "tipo_demonstrativo": valores["demonstrativo"],
        "periodo_bimestre": valores["periodo"],
        "periodicidade": valores["periodicidade"],
        "instituicao": valores["instituicao"],
        "id_municipio": valores["cod_ibge"],
        "uf": valores["uf"],
        "populacao": valores["populacao"],
        "anexo": valores["anexo"],
        "esfera": valores["esfera"],
        "rotulo": valores["rotulo"],
        "coluna": valores["coluna"],
        "codigo_conta": valores["cod_conta"],
        "descricao_conta": valores["conta"],
        "valor": valores["valor"],
    }


def parse_linhas_rreo(raw_linhas: list[dict]) -> list[dict]:
    """Aplica parse_linha_rreo a cada item da lista bruta do SICONFI."""
    return [parse_linha_rreo(raw) for raw in raw_linhas]
