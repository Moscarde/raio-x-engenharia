import pytest

from include.collectors.siops.parser import (
    MUNICIPIO_REFERENCIA_ID_ENTE,
    parse_linha_rreo,
    parse_linhas_rreo,
)

RAW_LINHA = {
    "exercicio": 2025,
    "demonstrativo": "RREO",
    "periodo": 6,
    "periodicidade": "B",
    "instituicao": "Prefeitura Municipal do Rio de Janeiro - RJ",
    "cod_ibge": MUNICIPIO_REFERENCIA_ID_ENTE,
    "uf": "RJ",
    "populacao": 6625849,
    "anexo": "RREO-Anexo 14",
    "esfera": "M",
    "rotulo": "Padrão",
    "coluna": "Valor Apurado Até o Bimestre",
    "cod_conta": "AplicacaoTotalDasDespesasComAcoesEServicosPublicosDeSaude",
    "conta": "Despesas com Ações e Serviços Públicos de Saúde Executadas com Recursos de Impostos",
    "valor": 3803434655.38,
}


def test_parse_linha_rreo_normaliza_campos():
    resultado = parse_linha_rreo(RAW_LINHA)

    assert resultado == {
        "ano_exercicio": 2025,
        "tipo_demonstrativo": "RREO",
        "periodo_bimestre": 6,
        "periodicidade": "B",
        "instituicao": "Prefeitura Municipal do Rio de Janeiro - RJ",
        "id_municipio": MUNICIPIO_REFERENCIA_ID_ENTE,
        "uf": "RJ",
        "populacao": 6625849,
        "anexo": "RREO-Anexo 14",
        "esfera": "M",
        "rotulo": "Padrão",
        "coluna": "Valor Apurado Até o Bimestre",
        "codigo_conta": "AplicacaoTotalDasDespesasComAcoesEServicosPublicosDeSaude",
        "descricao_conta": "Despesas com Ações e Serviços Públicos de Saúde Executadas com Recursos de Impostos",
        "valor": 3803434655.38,
    }


@pytest.mark.parametrize("campo_ausente", list(RAW_LINHA))
def test_parse_linha_rreo_rejeita_registro_sem_campo_obrigatorio(campo_ausente):
    raw_incompleto = {k: v for k, v in RAW_LINHA.items() if k != campo_ausente}

    with pytest.raises(ValueError, match=campo_ausente):
        parse_linha_rreo(raw_incompleto)


def test_parse_linhas_rreo_processa_lista_completa():
    resultado = parse_linhas_rreo([RAW_LINHA, RAW_LINHA])

    assert len(resultado) == 2
    assert resultado[0]["id_municipio"] == MUNICIPIO_REFERENCIA_ID_ENTE
