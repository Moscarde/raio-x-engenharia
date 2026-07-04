import pytest

from include.collectors.sisab.parser import (
    MUNICIPIO_REFERENCIA_CODIGO_MUNICIPIO,
    parse_indicador_desempenho,
    parse_indicadores_desempenho,
)

RAW_INDICADOR = {
    "uf": "RJ",
    "municipio": "RIO DE JANEIRO",
    "codigo_municipio": MUNICIPIO_REFERENCIA_CODIGO_MUNICIPIO,
    "quadrimestre": "2024Q3",
    "competencia": 202412,
    "codigo_tipo_indicador": 10,
    "visao_equipe": "validas",
    "numerador": 10541.0,
    "denominador_utilizador": 21538.0,
    "denominador_identificado": 14918.0,
    "denominador_estimado": 21538.0,
    "percentual": 69,
    "percentual_quadrimestre": 49.0,
    "cadastro": 5602965.0,
    "base_externa": 23876,
    "populacao": 6211223,
}


def test_parse_indicador_desempenho_normaliza_campos():
    resultado = parse_indicador_desempenho(RAW_INDICADOR)

    assert resultado == RAW_INDICADOR


@pytest.mark.parametrize("campo_ausente", list(RAW_INDICADOR))
def test_parse_indicador_desempenho_rejeita_registro_sem_campo_obrigatorio(
    campo_ausente,
):
    raw_incompleto = {k: v for k, v in RAW_INDICADOR.items() if k != campo_ausente}

    with pytest.raises(ValueError, match=campo_ausente):
        parse_indicador_desempenho(raw_incompleto)


def test_parse_indicadores_desempenho_processa_lista_completa():
    resultado = parse_indicadores_desempenho([RAW_INDICADOR, RAW_INDICADOR])

    assert len(resultado) == 2
    assert resultado[0]["codigo_municipio"] == MUNICIPIO_REFERENCIA_CODIGO_MUNICIPIO
