"""Parsing dos registros brutos de estabelecimentos retornados pelo CNES (grupo ST)."""

from __future__ import annotations

REQUIRED_FIELDS = (
    "CNES",
    "CODUFMUN",
    "PF_PJ",
    "NIV_DEP",
    "TP_UNID",
    "NATUREZA",
    "NAT_JUR",
    "ATIVIDAD",
    "VINC_SUS",
    "TPGESTAO",
    "ESFERA_A",
    "COMPETEN",
    "DT_ATUAL",
)

# Municípios de referência (id_municipio em raw_ibge.municipios: Rio de
# Janeiro 3304557, Paraty 3303807, Nova Iguaçu 3303500). O CNES usa
# CODUFMUN, código IBGE de 6 dígitos sem o dígito verificador (confirmado
# contra amostra real do CNES: CODUFMUN "330455" para as ~17k linhas do RJ
# capital em STRJ2512.dbc). Escopo MVP restringe a estes municípios (ver
# docs/fontes.md#escopo-de-volume-para-o-mvp).
MUNICIPIOS_REFERENCIA_CODUFMUN = ("330455", "330380", "330350")


def parse_estabelecimento(raw: dict) -> dict:
    """Normaliza um registro bruto de estabelecimento para raw_cnes.estabelecimentos.

    Espera os campos do grupo "ST" (Estabelecimentos) do CNES, conforme
    retornado por `include.collectors.cnes.client.fetch_estabelecimentos`.
    Os campos são códigos DATASUS (ex.: TP_UNID, NAT_JUR); o de-para para
    valores legíveis fica para as camadas staging/dbt, não para o raw layer.

    Exemplo:
        >>> parse_estabelecimento(raw)["codigo_cnes"]
        '0033979'
    """
    valores = {}
    for campo in REQUIRED_FIELDS:
        try:
            valores[campo] = raw[campo]
        except KeyError as exc:
            raise ValueError(
                f"Registro de estabelecimento {raw!r} sem campo obrigatório {exc}; "
                f"esperado {REQUIRED_FIELDS}."
            ) from exc

    return {
        "codigo_cnes": valores["CNES"],
        "cod_municipio_ibge6": valores["CODUFMUN"],
        "tipo_pessoa": valores["PF_PJ"],
        "nivel_dependencia": valores["NIV_DEP"],
        "tipo_unidade": valores["TP_UNID"],
        "natureza_organizacao": valores["NATUREZA"],
        "natureza_juridica": valores["NAT_JUR"],
        "atividade_ensino": valores["ATIVIDAD"],
        "vinculo_sus": valores["VINC_SUS"],
        "tipo_gestao": valores["TPGESTAO"],
        "esfera_administrativa": valores["ESFERA_A"],
        "competencia": valores["COMPETEN"],
        "data_atualizacao": valores["DT_ATUAL"],
    }


def parse_estabelecimentos(raw_estabelecimentos: list[dict]) -> list[dict]:
    """Filtra pelos municípios de referência do MVP e normaliza cada registro.

    O filtro por município acontece aqui (não no client) porque é escopo de
    ingestão do MVP, não uma limitação da fonte: o arquivo CNES é distribuído
    por UF inteira, sem recorte por município.
    """
    dos_municipios = [
        raw
        for raw in raw_estabelecimentos
        if raw.get("CODUFMUN") in MUNICIPIOS_REFERENCIA_CODUFMUN
    ]
    return [parse_estabelecimento(raw) for raw in dos_municipios]
