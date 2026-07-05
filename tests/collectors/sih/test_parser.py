import pytest

from include.collectors.sih.parser import (
    MUNICIPIOS_REFERENCIA_CODUFMUN,
    parse_internacao,
    parse_internacoes,
)

RAW_INTERNACAO = {
    "N_AIH": "3325100954329",
    "CNES": "6586767",
    "MUNIC_MOV": MUNICIPIOS_REFERENCIA_CODUFMUN[0],
    "MUNIC_RES": "330600",
    "ANO_CMPT": "2025",
    "MES_CMPT": "12",
    "PROC_REA": "0303040068",
    "CBOR": "223505",
    "IDADE": "45",
    "SEXO": "1",
    "RACA_COR": "01",
    "DIAG_PRINC": "O800",
    "VAL_TOT": "1234.56",
    "DT_INTER": "20251125",
    "DT_SAIDA": "20251128",
    "DIAS_PERM": "3",
    "MORTE": "0",
    "_arquivo_origem": "RDRJ2512.dbc",
}


def test_parse_internacao_normaliza_campos():
    resultado = parse_internacao(RAW_INTERNACAO)

    assert resultado == {
        "numero_aih": "3325100954329",
        "codigo_cnes_estabelecimento": "6586767",
        "cod_municipio_ibge6_estabelecimento": MUNICIPIOS_REFERENCIA_CODUFMUN[0],
        "cod_municipio_ibge6_paciente": "330600",
        "competencia": "202512",
        "codigo_procedimento": "0303040068",
        "codigo_cbo": "223505",
        "idade_paciente": "45",
        "sexo_paciente": "1",
        "raca_cor_paciente": "01",
        "diagnostico_principal": "O800",
        "valor_total": "1234.56",
        "data_internacao": "20251125",
        "data_saida": "20251128",
        "dias_permanencia": "3",
        "indicador_obito": "0",
        "_source_file": "RDRJ2512.dbc",
    }


@pytest.mark.parametrize("campo_ausente", list(RAW_INTERNACAO))
def test_parse_internacao_rejeita_registro_sem_campo_obrigatorio(campo_ausente):
    raw_incompleto = {k: v for k, v in RAW_INTERNACAO.items() if k != campo_ausente}

    with pytest.raises(ValueError, match=campo_ausente):
        parse_internacao(raw_incompleto)


def test_parse_internacoes_filtra_pelo_municipio_de_referencia():
    outro_municipio = {**RAW_INTERNACAO, "N_AIH": "999", "MUNIC_MOV": "330010"}

    resultado = parse_internacoes([RAW_INTERNACAO, outro_municipio])

    assert len(resultado) == 1
    assert (
        resultado[0]["cod_municipio_ibge6_estabelecimento"]
        == MUNICIPIOS_REFERENCIA_CODUFMUN[0]
    )


def test_parse_internacoes_processa_lista_completa_do_municipio():
    outra_internacao = {**RAW_INTERNACAO, "N_AIH": "3325100954330"}

    resultado = parse_internacoes([RAW_INTERNACAO, outra_internacao])

    assert len(resultado) == 2


def test_parse_internacoes_inclui_todos_os_municipios_de_referencia():
    de_cada_municipio = [
        {**RAW_INTERNACAO, "N_AIH": f"999{i}", "MUNIC_MOV": codigo}
        for i, codigo in enumerate(MUNICIPIOS_REFERENCIA_CODUFMUN)
    ]

    resultado = parse_internacoes(de_cada_municipio)

    assert len(resultado) == len(MUNICIPIOS_REFERENCIA_CODUFMUN)
