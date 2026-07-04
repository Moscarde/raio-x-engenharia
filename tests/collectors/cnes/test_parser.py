import pytest

from include.collectors.cnes.parser import (
    MUNICIPIO_REFERENCIA_CODUFMUN,
    parse_estabelecimento,
    parse_estabelecimentos,
)

RAW_ESTABELECIMENTO = {
    "CNES": "0033979",
    "CODUFMUN": MUNICIPIO_REFERENCIA_CODUFMUN,
    "PF_PJ": "1",
    "NIV_DEP": "1",
    "TP_UNID": "22",
    "NATUREZA": "4000",
    "NAT_JUR": "04",
    "ATIVIDAD": "0",
    "VINC_SUS": "M",
    "TPGESTAO": "M",
    "ESFERA_A": "3",
    "COMPETEN": "202512",
    "DT_ATUAL": "202512",
}


def test_parse_estabelecimento_normaliza_campos():
    resultado = parse_estabelecimento(RAW_ESTABELECIMENTO)

    assert resultado == {
        "codigo_cnes": "0033979",
        "cod_municipio_ibge6": MUNICIPIO_REFERENCIA_CODUFMUN,
        "tipo_pessoa": "1",
        "nivel_dependencia": "1",
        "tipo_unidade": "22",
        "natureza_organizacao": "4000",
        "natureza_juridica": "04",
        "atividade_ensino": "0",
        "vinculo_sus": "M",
        "tipo_gestao": "M",
        "esfera_administrativa": "3",
        "competencia": "202512",
        "data_atualizacao": "202512",
    }


@pytest.mark.parametrize("campo_ausente", list(RAW_ESTABELECIMENTO))
def test_parse_estabelecimento_rejeita_registro_sem_campo_obrigatorio(campo_ausente):
    raw_incompleto = {
        k: v for k, v in RAW_ESTABELECIMENTO.items() if k != campo_ausente
    }

    with pytest.raises(ValueError, match=campo_ausente):
        parse_estabelecimento(raw_incompleto)


def test_parse_estabelecimentos_filtra_pelo_municipio_de_referencia():
    outro_municipio = {**RAW_ESTABELECIMENTO, "CNES": "9999999", "CODUFMUN": "330010"}

    resultado = parse_estabelecimentos([RAW_ESTABELECIMENTO, outro_municipio])

    assert len(resultado) == 1
    assert resultado[0]["codigo_cnes"] == "0033979"


def test_parse_estabelecimentos_processa_lista_completa_do_municipio():
    resultado = parse_estabelecimentos([RAW_ESTABELECIMENTO, RAW_ESTABELECIMENTO])

    assert len(resultado) == 2
    assert resultado[0]["codigo_cnes"] == "0033979"
