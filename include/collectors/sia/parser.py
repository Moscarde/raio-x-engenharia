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
    """Normaliza cada registro bruto, sem filtro por município.

    O SIA não filtra mais por município de referência: o raw cobre o
    estado (UF) inteiro, não só o Rio de Janeiro. Motivo: `client.py` já
    decodifica o arquivo inteiro (`to_dict`) antes de qualquer filtro ser
    possível — o custo de CPU do decode é pago independente do recorte, e
    descartar ~38% das linhas já decodificadas sem persistir jogava fora
    trabalho que poderia ser reaproveitado para outros municípios do
    estado no futuro. Ver ROADMAP.md e docs/fontes.md#escopo-de-volume-para-o-mvp.
    """
    return [parse_producao_ambulatorial(raw) for raw in raw_producoes]
