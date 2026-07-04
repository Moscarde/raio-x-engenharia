"""Parsing dos registros brutos de óbitos do SIM (grupo DO, CID-10)."""

from __future__ import annotations

REQUIRED_FIELDS = (
    "ORIGEM",
    "CODESTAB",
    "CODMUNOCOR",
    "CODMUNRES",
    "DTOBITO",
    "DTNASC",
    "IDADE",
    "SEXO",
    "RACACOR",
    "ESTCIV",
    "ESC",
    "LOCOCOR",
    "CAUSABAS",
    "CIRCOBITO",
    "ASSISTMED",
    "_arquivo_origem",
)

# Rio de Janeiro: id_municipio 3304557 em raw_ibge.municipios. O SIM usa
# CODMUNOCOR para o município de ocorrência do óbito, mesmo código IBGE de
# 6 dígitos sem dígito verificador do CNES/SIA/SIH (confirmado contra
# amostra real: CODMUNOCOR "330455" concentra os óbitos do Rio em
# DORJ2024.dbc). CODMUNRES é o município de residência do falecido, mantido
# como dimensão, não como filtro. Escopo MVP restringe a este município (ver
# docs/fontes.md#escopo-de-volume-para-o-mvp).
MUNICIPIO_REFERENCIA_CODUFMUN = "330455"


def parse_obito(raw: dict) -> dict:
    """Normaliza um registro bruto de óbito do SIM/DO.

    Espera os campos retornados por `include.collectors.sim.client.fetch_obitos`.

    Exemplo:
        >>> parse_obito(raw)["causa_basica"]
        'I219'
    """
    valores = {}
    for campo in REQUIRED_FIELDS:
        try:
            valores[campo] = raw[campo]
        except KeyError as exc:
            raise ValueError(
                f"Registro de óbito {raw!r} sem campo obrigatório {exc}; "
                f"esperado {REQUIRED_FIELDS}."
            ) from exc

    return {
        "origem_informacao": valores["ORIGEM"],
        "codigo_cnes_estabelecimento": valores["CODESTAB"],
        "cod_municipio_ibge6_ocorrencia": valores["CODMUNOCOR"],
        "cod_municipio_ibge6_residencia": valores["CODMUNRES"],
        "data_obito": valores["DTOBITO"],
        "data_nascimento": valores["DTNASC"],
        "idade": valores["IDADE"],
        "sexo": valores["SEXO"],
        "raca_cor": valores["RACACOR"],
        "estado_civil": valores["ESTCIV"],
        "escolaridade": valores["ESC"],
        "local_ocorrencia": valores["LOCOCOR"],
        "causa_basica": valores["CAUSABAS"],
        "circunstancia_obito": valores["CIRCOBITO"],
        "assistencia_medica": valores["ASSISTMED"],
        "_source_file": valores["_arquivo_origem"],
    }


def parse_obitos(raw_obitos: list[dict]) -> list[dict]:
    """Filtra pelo município de referência do MVP e normaliza cada registro.

    O filtro por município acontece aqui (não no client) porque é escopo de
    ingestão do MVP, não uma limitação da fonte: o arquivo SIM é distribuído
    por UF inteira, sem recorte por município.
    """
    do_municipio = [
        raw
        for raw in raw_obitos
        if raw.get("CODMUNOCOR") == MUNICIPIO_REFERENCIA_CODUFMUN
    ]
    return [parse_obito(raw) for raw in do_municipio]
