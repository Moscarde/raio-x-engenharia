import pytest

from include.collectors.sim.parser import (
    MUNICIPIOS_REFERENCIA_CODUFMUN,
    parse_obito,
    parse_obitos,
)

RAW_OBITO = {
    "ORIGEM": "1",
    "CODESTAB": "2269899",
    "CODMUNOCOR": MUNICIPIOS_REFERENCIA_CODUFMUN[0],
    "CODMUNRES": "330490",
    "DTOBITO": "01012024",
    "DTNASC": "05051960",
    "IDADE": "464",
    "SEXO": "2",
    "RACACOR": "1",
    "ESTCIV": "3",
    "ESC": "3",
    "LOCOCOR": "1",
    "CAUSABAS": "I219",
    "CIRCOBITO": "9",
    "ASSISTMED": "1",
    "_arquivo_origem": "DORJ2024.dbc",
}


def test_parse_obito_normaliza_campos():
    resultado = parse_obito(RAW_OBITO)

    assert resultado == {
        "origem_informacao": "1",
        "codigo_cnes_estabelecimento": "2269899",
        "cod_municipio_ibge6_ocorrencia": MUNICIPIOS_REFERENCIA_CODUFMUN[0],
        "cod_municipio_ibge6_residencia": "330490",
        "data_obito": "01012024",
        "data_nascimento": "05051960",
        "idade": "464",
        "sexo": "2",
        "raca_cor": "1",
        "estado_civil": "3",
        "escolaridade": "3",
        "local_ocorrencia": "1",
        "causa_basica": "I219",
        "circunstancia_obito": "9",
        "assistencia_medica": "1",
        "_source_file": "DORJ2024.dbc",
    }


@pytest.mark.parametrize("campo_ausente", list(RAW_OBITO))
def test_parse_obito_rejeita_registro_sem_campo_obrigatorio(campo_ausente):
    raw_incompleto = {k: v for k, v in RAW_OBITO.items() if k != campo_ausente}

    with pytest.raises(ValueError, match=campo_ausente):
        parse_obito(raw_incompleto)


def test_parse_obitos_filtra_pelo_municipio_de_referencia():
    outro_municipio = {**RAW_OBITO, "CODMUNOCOR": "330010"}

    resultado = parse_obitos([RAW_OBITO, outro_municipio])

    assert len(resultado) == 1
    assert (
        resultado[0]["cod_municipio_ibge6_ocorrencia"]
        == MUNICIPIOS_REFERENCIA_CODUFMUN[0]
    )


def test_parse_obitos_processa_lista_completa_do_municipio():
    resultado = parse_obitos([RAW_OBITO, RAW_OBITO])

    assert len(resultado) == 2


def test_parse_obitos_inclui_todos_os_municipios_de_referencia():
    de_cada_municipio = [
        {**RAW_OBITO, "CODMUNOCOR": codigo} for codigo in MUNICIPIOS_REFERENCIA_CODUFMUN
    ]

    resultado = parse_obitos(de_cada_municipio)

    assert len(resultado) == len(MUNICIPIOS_REFERENCIA_CODUFMUN)
