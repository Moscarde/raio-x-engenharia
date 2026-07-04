import pytest

from include.collectors.ibge.parser import parse_municipio, parse_municipios

RAW_MUNICIPIO = {
    "id": 1100015,
    "nome": "Alta Floresta D'Oeste",
    "microrregiao": {
        "id": 11006,
        "nome": "Cacoal",
        "mesorregiao": {
            "id": 1102,
            "nome": "Leste Rondoniense",
            "UF": {
                "id": 11,
                "sigla": "RO",
                "nome": "Rondônia",
                "regiao": {"id": 1, "sigla": "N", "nome": "Norte"},
            },
        },
    },
}


def test_parse_municipio_normaliza_campos_territoriais():
    resultado = parse_municipio(RAW_MUNICIPIO)

    assert resultado == {
        "id_municipio": 1100015,
        "nome_municipio": "Alta Floresta D'Oeste",
        "id_microrregiao": 11006,
        "nome_microrregiao": "Cacoal",
        "id_mesorregiao": 1102,
        "nome_mesorregiao": "Leste Rondoniense",
        "id_uf": 11,
        "sigla_uf": "RO",
        "nome_uf": "Rondônia",
        "id_regiao": 1,
        "sigla_regiao": "N",
        "nome_regiao": "Norte",
    }


def test_parse_municipios_processa_lista_completa():
    resultado = parse_municipios([RAW_MUNICIPIO, RAW_MUNICIPIO])

    assert len(resultado) == 2
    assert resultado[0]["id_municipio"] == 1100015


@pytest.mark.parametrize("campo_ausente", ["id", "nome"])
def test_parse_municipio_rejeita_registro_sem_campo_obrigatorio(campo_ausente):
    raw_incompleto = {k: v for k, v in RAW_MUNICIPIO.items() if k != campo_ausente}

    with pytest.raises(ValueError, match=campo_ausente):
        parse_municipio(raw_incompleto)


def test_parse_municipio_rejeita_cadeia_territorial_incompleta():
    raw_sem_uf = {
        **RAW_MUNICIPIO,
        "microrregiao": {
            "id": 11006,
            "nome": "Cacoal",
            "mesorregiao": {"id": 1102, "nome": "Leste Rondoniense"},
        },
    }

    with pytest.raises(ValueError, match="UF"):
        parse_municipio(raw_sem_uf)


def test_parse_municipio_sem_microrregiao_usa_regiao_imediata():
    """Limitação conhecida da API: municípios recém-criados ainda sem
    microrregiao/mesorregiao cadastradas (ex.: id 5101837, Boa Esperança do
    Norte/MT) resolvem UF/regiao via regiao-imediata.regiao-intermediaria.UF.
    """
    raw_sem_microrregiao = {
        "id": 5101837,
        "nome": "Boa Esperança do Norte",
        "microrregiao": None,
        "regiao-imediata": {
            "id": 510008,
            "nome": "Sorriso",
            "regiao-intermediaria": {
                "id": 5103,
                "nome": "Sinop",
                "UF": {
                    "id": 51,
                    "sigla": "MT",
                    "nome": "Mato Grosso",
                    "regiao": {"id": 5, "sigla": "CO", "nome": "Centro-Oeste"},
                },
            },
        },
    }

    resultado = parse_municipio(raw_sem_microrregiao)

    assert resultado["id_microrregiao"] is None
    assert resultado["nome_microrregiao"] is None
    assert resultado["id_mesorregiao"] is None
    assert resultado["nome_mesorregiao"] is None
    assert resultado["sigla_uf"] == "MT"
    assert resultado["sigla_regiao"] == "CO"


def test_parse_municipio_rejeita_sem_microrregiao_e_sem_regiao_imediata():
    raw_sem_nada = {
        "id": 5101837,
        "nome": "Boa Esperança do Norte",
        "microrregiao": None,
    }

    with pytest.raises(ValueError, match="regiao-imediata"):
        parse_municipio(raw_sem_nada)
