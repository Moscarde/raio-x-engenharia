import pytest

from include.collectors.fns.parser import (
    MUNICIPIO_REFERENCIA_CNPJ,
    parse_lancamento,
    parse_lancamentos,
)

RAW_LANCAMENTO = {
    "id_lancamento_gestao_financeira": 2977057,
    "cnpj_ente_solicitante_gestao_financeira": MUNICIPIO_REFERENCIA_CNPJ,
    "nome_ente_solicitante_gestao_financeira": "MUNICIPIO DE RIO DE JANEIRO",
    "codigo_programa_agil_ente_solicitante_gestao_financeira": "140",
    "tipo_operacao_gestao_financeira": "C",
    "descricao_tipo_operacao_gestao_financeira": "Crédito",
    "descricao_gestao_financeira": "Resgate BB Fix",
    "data_lancamento_gestao_financeira": "2025-01-02",
    "data_evento_lancamento_gestao_financeira": "2025-01-02",
    "numero_referencia_unica_gestao_financeira": "1200078",
    "tipo_favorecido_gestao_financeira": 0,
    "descricao_tipo_favorecido_gestao_financeira": "Não Identificado",
    "nome_favorecido_gestao_financeira": "",
    "valor_lancamento_gestao_financeira": 397148.48,
    "id_categoria_despesa_gestao_financeira": 0,
    "quantidade_subtransacoes_lancamento_gestao_financeira": 0,
}


def test_parse_lancamento_normaliza_campos():
    resultado = parse_lancamento(RAW_LANCAMENTO)

    assert resultado == {
        "id_lancamento": 2977057,
        "cnpj_ente_solicitante": MUNICIPIO_REFERENCIA_CNPJ,
        "nome_ente_solicitante": "MUNICIPIO DE RIO DE JANEIRO",
        "codigo_programa_agil": "140",
        "tipo_operacao": "C",
        "descricao_tipo_operacao": "Crédito",
        "descricao_lancamento": "Resgate BB Fix",
        "data_lancamento": "2025-01-02",
        "data_evento_lancamento": "2025-01-02",
        "numero_referencia_unica": "1200078",
        "tipo_favorecido": 0,
        "descricao_tipo_favorecido": "Não Identificado",
        "nome_favorecido": "",
        "valor_lancamento": 397148.48,
        "id_categoria_despesa": 0,
        "quantidade_subtransacoes": 0,
    }


@pytest.mark.parametrize(
    "campo_ausente",
    [
        "id_lancamento_gestao_financeira",
        "cnpj_ente_solicitante_gestao_financeira",
        "nome_ente_solicitante_gestao_financeira",
        "tipo_operacao_gestao_financeira",
        "descricao_tipo_operacao_gestao_financeira",
        "descricao_gestao_financeira",
        "data_lancamento_gestao_financeira",
        "data_evento_lancamento_gestao_financeira",
        "valor_lancamento_gestao_financeira",
    ],
)
def test_parse_lancamento_rejeita_registro_sem_campo_obrigatorio(campo_ausente):
    raw_incompleto = {k: v for k, v in RAW_LANCAMENTO.items() if k != campo_ausente}

    with pytest.raises(ValueError, match=campo_ausente):
        parse_lancamento(raw_incompleto)


def test_parse_lancamento_aceita_campos_opcionais_ausentes():
    raw_minimo = {
        "id_lancamento_gestao_financeira": 1,
        "cnpj_ente_solicitante_gestao_financeira": MUNICIPIO_REFERENCIA_CNPJ,
        "nome_ente_solicitante_gestao_financeira": "MUNICIPIO DE RIO DE JANEIRO",
        "tipo_operacao_gestao_financeira": "D",
        "descricao_tipo_operacao_gestao_financeira": "Débito",
        "descricao_gestao_financeira": "TED Transf.Eletr.Disponivel",
        "data_lancamento_gestao_financeira": "2025-01-02",
        "data_evento_lancamento_gestao_financeira": "2025-01-02",
        "valor_lancamento_gestao_financeira": 100.0,
    }

    resultado = parse_lancamento(raw_minimo)

    assert resultado["numero_referencia_unica"] is None
    assert resultado["nome_favorecido"] is None
    assert resultado["id_categoria_despesa"] is None


def test_parse_lancamentos_processa_lista_completa():
    resultado = parse_lancamentos([RAW_LANCAMENTO, RAW_LANCAMENTO])

    assert len(resultado) == 2
    assert resultado[0]["id_lancamento"] == 2977057
