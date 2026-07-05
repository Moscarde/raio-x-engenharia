"""Parsing dos registros brutos de nascidos vivos do SINASC (grupo DN)."""

from __future__ import annotations

REQUIRED_FIELDS = (
    "ORIGEM",
    "CODESTAB",
    "CODMUNNASC",
    "CODMUNRES",
    "DTNASC",
    "SEXO",
    "RACACOR",
    "PESO",
    "GESTACAO",
    "PARTO",
    "APGAR1",
    "APGAR5",
    "CONSULTAS",
    "IDADEMAE",
    "ESCMAE",
    "_arquivo_origem",
)

# Municípios de referência (id_municipio em raw_ibge.municipios: Rio de
# Janeiro 3304557, Paraty 3303807, Nova Iguaçu 3303500). O SINASC usa
# CODMUNNASC para o município de nascimento (hospital), mesmo código IBGE de
# 6 dígitos sem dígito verificador do CNES/SIA/SIH/SIM (confirmado contra
# amostra real: CODMUNNASC "330455" concentra os nascimentos do Rio em
# DNRJ2022.dbc). CODMUNRES é o município de residência da mãe, mantido como
# dimensão, não como filtro. Escopo MVP restringe a estes municípios (ver
# docs/fontes.md#escopo-de-volume-para-o-mvp).
MUNICIPIOS_REFERENCIA_CODUFMUN = ("330455", "330380", "330350")


def parse_nascido_vivo(raw: dict) -> dict:
    """Normaliza um registro bruto de nascido vivo do SINASC/DN.

    Espera os campos retornados por
    `include.collectors.sinasc.client.fetch_nascidos_vivos`.

    Exemplo:
        >>> parse_nascido_vivo(raw)["peso_gramas"]
        '3235'
    """
    valores = {}
    for campo in REQUIRED_FIELDS:
        try:
            valores[campo] = raw[campo]
        except KeyError as exc:
            raise ValueError(
                f"Registro de nascido vivo {raw!r} sem campo obrigatório {exc}; "
                f"esperado {REQUIRED_FIELDS}."
            ) from exc

    return {
        "origem_informacao": valores["ORIGEM"],
        "codigo_cnes_estabelecimento": valores["CODESTAB"],
        "cod_municipio_ibge6_nascimento": valores["CODMUNNASC"],
        "cod_municipio_ibge6_residencia": valores["CODMUNRES"],
        "data_nascimento": valores["DTNASC"],
        "sexo": valores["SEXO"],
        "raca_cor": valores["RACACOR"],
        "peso_gramas": valores["PESO"],
        "semanas_gestacao_faixa": valores["GESTACAO"],
        "tipo_parto": valores["PARTO"],
        "apgar1": valores["APGAR1"],
        "apgar5": valores["APGAR5"],
        "numero_consultas_prenatal": valores["CONSULTAS"],
        "idade_mae": valores["IDADEMAE"],
        "escolaridade_mae": valores["ESCMAE"],
        "_source_file": valores["_arquivo_origem"],
    }


def parse_nascidos_vivos(raw_nascidos_vivos: list[dict]) -> list[dict]:
    """Filtra pelos municípios de referência do MVP e normaliza cada registro.

    O filtro por município acontece aqui (não no client) porque é escopo de
    ingestão do MVP, não uma limitação da fonte: o arquivo SINASC é
    distribuído por UF inteira, sem recorte por município.
    """
    dos_municipios = [
        raw
        for raw in raw_nascidos_vivos
        if raw.get("CODMUNNASC") in MUNICIPIOS_REFERENCIA_CODUFMUN
    ]
    return [parse_nascido_vivo(raw) for raw in dos_municipios]
