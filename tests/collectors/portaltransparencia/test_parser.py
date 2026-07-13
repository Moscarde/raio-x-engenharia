import pytest

from include.collectors.portaltransparencia import parser


def recurso_bruto(**overrides):
    recurso = {
        "anoMes": 202508,
        "codigoPessoa": "42.498.733/0001-48",
        "nomePessoa": "MUNICIPIO DE RIO DE JANEIRO",
        "tipoPessoa": "Administração Pública Municipal",
        "municipioPessoa": "RIO DE JANEIRO",
        "siglaUFPessoa": "RJ",
        "codigoUG": "250006",
        "nomeUG": "COORDENACAO-GERAL DE GESTAO DE PESSOAS",
        "codigoOrgao": "36000",
        "nomeOrgao": "Ministério da Saúde - Unidades com vínculo direto",
        "codigoOrgaoSuperior": "36000",
        "nomeOrgaoSuperior": "Ministério da Saúde",
        "valor": 5257.76,
    }
    return {**recurso, **overrides}


def test_parse_recurso_recebido_normaliza_cnpj_para_so_digitos():
    parsed = parser.parse_recurso_recebido(recurso_bruto())

    assert parsed["cnpj_favorecido"] == "42498733000148"
    assert parsed["competencia"] == 202508
    assert parsed["valor"] == 5257.76


def test_parse_recurso_recebido_preserva_valor_negativo():
    parsed = parser.parse_recurso_recebido(recurso_bruto(valor=-222835.44))

    assert parsed["valor"] == -222835.44


def test_parse_recurso_recebido_rejeita_campo_obrigatorio_ausente():
    raw = recurso_bruto()
    del raw["nomeOrgaoSuperior"]

    with pytest.raises(ValueError, match="nomeOrgaoSuperior"):
        parser.parse_recurso_recebido(raw)


def test_parse_recursos_recebidos_aplica_a_lista_inteira():
    resultado = parser.parse_recursos_recebidos([recurso_bruto(), recurso_bruto()])

    assert len(resultado) == 2
