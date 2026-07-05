"""Parsing dos registros brutos de internações hospitalares do SIH (grupo RD)."""

from __future__ import annotations

REQUIRED_FIELDS = (
    "N_AIH",
    "CNES",
    "MUNIC_MOV",
    "MUNIC_RES",
    "ANO_CMPT",
    "MES_CMPT",
    "PROC_REA",
    "CBOR",
    "IDADE",
    "SEXO",
    "RACA_COR",
    "DIAG_PRINC",
    "VAL_TOT",
    "DT_INTER",
    "DT_SAIDA",
    "DIAS_PERM",
    "MORTE",
    "_arquivo_origem",
)

# Municípios de referência (id_municipio em raw_ibge.municipios: Rio de
# Janeiro 3304557, Paraty 3303807, Nova Iguaçu 3303500). O SIH usa
# MUNIC_MOV para o município do estabelecimento (hospital), mesmo código
# IBGE de 6 dígitos sem dígito verificador do CNES/SIA (confirmado contra
# amostra real: MUNIC_MOV "330455" concentra as internações do Rio em
# RDRJ2512.dbc). MUNIC_RES é o município de residência do paciente, mantido
# como dimensão, não como filtro. Escopo MVP restringe a estes municípios
# (ver docs/fontes.md#escopo-de-volume-para-o-mvp).
MUNICIPIOS_REFERENCIA_CODUFMUN = ("330455", "330380", "330350")


def parse_internacao(raw: dict) -> dict:
    """Normaliza um registro bruto de internação hospitalar do SIH/RD.

    Espera os campos retornados por
    `include.collectors.sih.client.fetch_internacoes`.

    Exemplo:
        >>> parse_internacao(raw)["numero_aih"]
        '3325100954329'
    """
    valores = {}
    for campo in REQUIRED_FIELDS:
        try:
            valores[campo] = raw[campo]
        except KeyError as exc:
            raise ValueError(
                f"Registro de internação {raw!r} sem campo obrigatório {exc}; "
                f"esperado {REQUIRED_FIELDS}."
            ) from exc

    competencia = f"{valores['ANO_CMPT']}{int(valores['MES_CMPT']):02d}"

    return {
        "numero_aih": valores["N_AIH"],
        "codigo_cnes_estabelecimento": valores["CNES"],
        "cod_municipio_ibge6_estabelecimento": valores["MUNIC_MOV"],
        "cod_municipio_ibge6_paciente": valores["MUNIC_RES"],
        "competencia": competencia,
        "codigo_procedimento": valores["PROC_REA"],
        "codigo_cbo": valores["CBOR"],
        "idade_paciente": valores["IDADE"],
        "sexo_paciente": valores["SEXO"],
        "raca_cor_paciente": valores["RACA_COR"],
        "diagnostico_principal": valores["DIAG_PRINC"],
        "valor_total": valores["VAL_TOT"],
        "data_internacao": valores["DT_INTER"],
        "data_saida": valores["DT_SAIDA"],
        "dias_permanencia": valores["DIAS_PERM"],
        "indicador_obito": valores["MORTE"],
        "_source_file": valores["_arquivo_origem"],
    }


def parse_internacoes(raw_internacoes: list[dict]) -> list[dict]:
    """Filtra pelos municípios de referência do MVP e normaliza cada registro.

    O filtro por município acontece aqui (não no client) porque é escopo de
    ingestão do MVP, não uma limitação da fonte: o arquivo SIH é distribuído
    por UF inteira, sem recorte por município.
    """
    dos_municipios = [
        raw
        for raw in raw_internacoes
        if raw.get("MUNIC_MOV") in MUNICIPIOS_REFERENCIA_CODUFMUN
    ]
    return [parse_internacao(raw) for raw in dos_municipios]
