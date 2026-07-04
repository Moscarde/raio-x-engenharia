"""Parsing dos registros brutos de produção ambulatorial do SIA (grupo PA)."""

from __future__ import annotations

REQUIRED_FIELDS = (
    "PA_CODUNI",
    "PA_UFMUN",
    "PA_MUNPCN",
    "PA_CMP",
    "PA_PROC_ID",
    "PA_CBOCOD",
    "PA_CATEND",
    "PA_IDADE",
    "PA_SEXO",
    "PA_RACACOR",
    "PA_QTDPRO",
    "PA_QTDAPR",
    "PA_VALPRO",
    "PA_VALAPR",
    "PA_DOCORIG",
    "_arquivo_origem",
)

# Rio de Janeiro: id_municipio 3304557 em raw_ibge.municipios. O SIA usa
# PA_UFMUN, o mesmo código IBGE de 6 dígitos sem dígito verificador do CNES
# (include/collectors/cnes/parser.py). Escopo MVP restringe a este município
# (docs/fontes.md#escopo-de-volume-para-o-mvp). O filtro acontece aqui, não
# no client, porque o arquivo do SIA é distribuído por UF inteira, sem
# recorte por município.
MUNICIPIO_REFERENCIA_CODUFMUN = "330455"


def parse_producao_ambulatorial(raw: dict) -> dict:
    """Normaliza um registro bruto de produção ambulatorial do SIA/PA.

    Espera os campos retornados por
    `include.collectors.sia.client.fetch_producao_ambulatorial`.

    Exemplo:
        >>> parse_producao_ambulatorial(raw)["competencia"]
        '202512'
    """
    valores = {}
    for campo in REQUIRED_FIELDS:
        try:
            valores[campo] = raw[campo]
        except KeyError as exc:
            raise ValueError(
                f"Registro de produção ambulatorial {raw!r} sem campo obrigatório "
                f"{exc}; esperado {REQUIRED_FIELDS}."
            ) from exc

    return {
        "codigo_cnes_estabelecimento": valores["PA_CODUNI"],
        "cod_municipio_ibge6_estabelecimento": valores["PA_UFMUN"],
        "cod_municipio_ibge6_paciente": valores["PA_MUNPCN"],
        "competencia": valores["PA_CMP"],
        "codigo_procedimento": valores["PA_PROC_ID"],
        "codigo_cbo": valores["PA_CBOCOD"],
        "carater_atendimento": valores["PA_CATEND"],
        "idade_paciente": valores["PA_IDADE"],
        "sexo_paciente": valores["PA_SEXO"],
        "raca_cor_paciente": valores["PA_RACACOR"],
        "quantidade_produzida": valores["PA_QTDPRO"],
        "quantidade_aprovada": valores["PA_QTDAPR"],
        "valor_produzido": valores["PA_VALPRO"],
        "valor_aprovado": valores["PA_VALAPR"],
        "origem_documento": valores["PA_DOCORIG"],
        "_source_file": valores["_arquivo_origem"],
    }


def parse_producoes_ambulatoriais(raw_producoes: list[dict]) -> list[dict]:
    """Filtra pelo município de referência do MVP e normaliza cada registro."""
    do_municipio = [
        raw
        for raw in raw_producoes
        if raw.get("PA_UFMUN") == MUNICIPIO_REFERENCIA_CODUFMUN
    ]
    return [parse_producao_ambulatorial(raw) for raw in do_municipio]
