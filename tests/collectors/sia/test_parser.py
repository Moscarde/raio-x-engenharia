import pytest

from include.collectors.sia.parser import (
    parse_producao_ambulatorial,
    parse_producoes_ambulatoriais,
)

RAW_PRODUCAO = {
    "PA_CODUNI": "6631169",
    "PA_UFMUN": "330455",
    "PA_MUNPCN": "330455",
    "PA_CMP": "202512",
    "PA_PROC_ID": "0301100012",
    "PA_CBOCOD": "223505",
    "PA_CATEND": "02",
    "PA_IDADE": "011",
    "PA_SEXO": "F",
    "PA_RACACOR": "03",
    "PA_QTDPRO": "1",
    "PA_QTDAPR": "1",
    "PA_VALPRO": "0.63",
    "PA_VALAPR": "0.63",
    "PA_DOCORIG": "I",
    "_arquivo_origem": "PARJ2512a.dbc",
}


def test_parse_producao_ambulatorial_normaliza_campos():
    resultado = parse_producao_ambulatorial(RAW_PRODUCAO)

    assert resultado == {
        "codigo_cnes_estabelecimento": "6631169",
        "cod_municipio_ibge6_estabelecimento": "330455",
        "cod_municipio_ibge6_paciente": "330455",
        "competencia": "202512",
        "codigo_procedimento": "0301100012",
        "codigo_cbo": "223505",
        "carater_atendimento": "02",
        "idade_paciente": "011",
        "sexo_paciente": "F",
        "raca_cor_paciente": "03",
        "quantidade_produzida": "1",
        "quantidade_aprovada": "1",
        "valor_produzido": "0.63",
        "valor_aprovado": "0.63",
        "origem_documento": "I",
        "_source_file": "PARJ2512a.dbc",
    }


@pytest.mark.parametrize("campo_ausente", list(RAW_PRODUCAO))
def test_parse_producao_ambulatorial_rejeita_registro_sem_campo_obrigatorio(
    campo_ausente,
):
    raw_incompleto = {k: v for k, v in RAW_PRODUCAO.items() if k != campo_ausente}

    with pytest.raises(ValueError, match=campo_ausente):
        parse_producao_ambulatorial(raw_incompleto)


def test_parse_producoes_ambulatoriais_processa_o_estado_inteiro_sem_filtrar():
    outro_municipio = {**RAW_PRODUCAO, "PA_UFMUN": "330010"}

    resultado = parse_producoes_ambulatoriais([RAW_PRODUCAO, outro_municipio])

    assert len(resultado) == 2
    assert {r["cod_municipio_ibge6_estabelecimento"] for r in resultado} == {
        "330455",
        "330010",
    }


def test_parse_producoes_ambulatoriais_processa_lista_completa():
    resultado = parse_producoes_ambulatoriais([RAW_PRODUCAO, RAW_PRODUCAO])

    assert len(resultado) == 2
