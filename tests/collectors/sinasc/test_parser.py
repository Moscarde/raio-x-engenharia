import pytest

from include.collectors.sinasc.parser import (
    MUNICIPIO_REFERENCIA_CODUFMUN,
    parse_nascido_vivo,
    parse_nascidos_vivos,
)

RAW_NASCIDO_VIVO = {
    "ORIGEM": "1",
    "CODESTAB": "2269899",
    "CODMUNNASC": MUNICIPIO_REFERENCIA_CODUFMUN,
    "CODMUNRES": MUNICIPIO_REFERENCIA_CODUFMUN,
    "DTNASC": "05042022",
    "SEXO": "2",
    "RACACOR": "1",
    "PESO": "3235",
    "GESTACAO": "5",
    "PARTO": "1",
    "APGAR1": "9",
    "APGAR5": "10",
    "CONSULTAS": "4",
    "IDADEMAE": "28",
    "ESCMAE": "4",
    "_arquivo_origem": "DNRJ2022.dbc",
}


def test_parse_nascido_vivo_normaliza_campos():
    resultado = parse_nascido_vivo(RAW_NASCIDO_VIVO)

    assert resultado == {
        "origem_informacao": "1",
        "codigo_cnes_estabelecimento": "2269899",
        "cod_municipio_ibge6_nascimento": MUNICIPIO_REFERENCIA_CODUFMUN,
        "cod_municipio_ibge6_residencia": MUNICIPIO_REFERENCIA_CODUFMUN,
        "data_nascimento": "05042022",
        "sexo": "2",
        "raca_cor": "1",
        "peso_gramas": "3235",
        "semanas_gestacao_faixa": "5",
        "tipo_parto": "1",
        "apgar1": "9",
        "apgar5": "10",
        "numero_consultas_prenatal": "4",
        "idade_mae": "28",
        "escolaridade_mae": "4",
        "_source_file": "DNRJ2022.dbc",
    }


@pytest.mark.parametrize("campo_ausente", list(RAW_NASCIDO_VIVO))
def test_parse_nascido_vivo_rejeita_registro_sem_campo_obrigatorio(campo_ausente):
    raw_incompleto = {
        k: v for k, v in RAW_NASCIDO_VIVO.items() if k != campo_ausente
    }

    with pytest.raises(ValueError, match=campo_ausente):
        parse_nascido_vivo(raw_incompleto)


def test_parse_nascidos_vivos_filtra_pelo_municipio_de_referencia():
    outro_municipio = {**RAW_NASCIDO_VIVO, "CODMUNNASC": "330010"}

    resultado = parse_nascidos_vivos([RAW_NASCIDO_VIVO, outro_municipio])

    assert len(resultado) == 1
    assert (
        resultado[0]["cod_municipio_ibge6_nascimento"] == MUNICIPIO_REFERENCIA_CODUFMUN
    )


def test_parse_nascidos_vivos_processa_lista_completa_do_municipio():
    resultado = parse_nascidos_vivos([RAW_NASCIDO_VIVO, RAW_NASCIDO_VIVO])

    assert len(resultado) == 2
