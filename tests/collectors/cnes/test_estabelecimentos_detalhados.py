import pytest

from include.collectors.cnes import client, parser


class FakeResposta:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def estabelecimento_bruto(**overrides):
    estabelecimento = {
        "codigo_cnes": 1082493,
        "nome_razao_social": "JUACIARA CARDEAL DE MIRANDA",
        "nome_fantasia": "JUACIARA CARDEAL DE MIRANDA",
        "codigo_tipo_unidade": 22,
        "codigo_cep_estabelecimento": "23080200",
        "endereco_estabelecimento": "R IVO DO PRADO",
        "numero_estabelecimento": "79",
        "bairro_estabelecimento": "CAMPO GRANDE",
        "numero_telefone_estabelecimento": None,
        "latitude_estabelecimento_decimo_grau": -22.90207,
        "longitude_estabelecimento_decimo_grau": -43.56484,
        "endereco_email_estabelecimento": None,
        "codigo_identificador_turno_atendimento": "01",
        "descricao_turno_atendimento": "ATENDIMENTO SOMENTE PELA MANHA",
        "estabelecimento_faz_atendimento_ambulatorial_sus": "NAO",
        "codigo_municipio": 330455,
        "descricao_esfera_administrativa": "MUNICIPAL",
        "codigo_motivo_desabilitacao_estabelecimento": "08",
        "estabelecimento_possui_centro_cirurgico": 0,
        "estabelecimento_possui_centro_obstetrico": 0,
        "estabelecimento_possui_centro_neonatal": 0,
        "estabelecimento_possui_atendimento_hospitalar": 0,
        "estabelecimento_possui_servico_apoio": 0,
        "estabelecimento_possui_atendimento_ambulatorial": 0,
        "data_atualizacao": "2025-09-03",
    }
    return {**estabelecimento, **overrides}


def test_fetch_estabelecimentos_detalhados_pagina_ate_pagina_vazia(monkeypatch):
    primeira_pagina = [
        estabelecimento_bruto() for _ in range(client.LIMITE_PAGINA_DEMAS)
    ]
    segunda_pagina = [estabelecimento_bruto(codigo_cnes=999)]
    terceira_pagina: list[dict] = []

    def fake_get(url, params, timeout):
        assert url == client.ENDPOINT_ESTABELECIMENTOS_DETALHADOS
        offset = params["offset"]
        return {
            0: FakeResposta(200, {"estabelecimentos": primeira_pagina}),
            client.LIMITE_PAGINA_DEMAS: FakeResposta(
                200, {"estabelecimentos": segunda_pagina}
            ),
            2
            * client.LIMITE_PAGINA_DEMAS: FakeResposta(
                200, {"estabelecimentos": terceira_pagina}
            ),
        }[offset]

    monkeypatch.setattr(client.requests, "get", fake_get)

    resultado = client.fetch_estabelecimentos_detalhados(330455)

    assert resultado == primeira_pagina + segunda_pagina


def test_fetch_estabelecimentos_detalhados_rejeita_status_diferente_de_200(monkeypatch):
    monkeypatch.setattr(
        client.requests, "get", lambda *args, **kwargs: FakeResposta(500, {})
    )

    with pytest.raises(RuntimeError, match="500"):
        client.fetch_estabelecimentos_detalhados(330455)


def test_fetch_estabelecimentos_detalhados_rejeita_lista_vazia(monkeypatch):
    monkeypatch.setattr(
        client.requests,
        "get",
        lambda *args, **kwargs: FakeResposta(200, {"estabelecimentos": []}),
    )

    with pytest.raises(RuntimeError, match="330455"):
        client.fetch_estabelecimentos_detalhados(330455)


def test_parse_estabelecimento_detalhado_preenche_zero_a_esquerda():
    parsed = parser.parse_estabelecimento_detalhado(
        estabelecimento_bruto(codigo_cnes=33979)
    )

    assert parsed["codigo_cnes"] == "0033979"
    assert parsed["nome_fantasia"] == "JUACIARA CARDEAL DE MIRANDA"
    assert parsed["descricao_esfera_administrativa"] == "MUNICIPAL"


def test_parse_estabelecimento_detalhado_aceita_campos_opcionais_nulos():
    raw = estabelecimento_bruto(
        nome_fantasia=None, latitude_estabelecimento_decimo_grau=None
    )

    parsed = parser.parse_estabelecimento_detalhado(raw)

    assert parsed["nome_fantasia"] is None
    assert parsed["latitude"] is None


def test_parse_estabelecimento_detalhado_rejeita_sem_codigo_cnes():
    raw = estabelecimento_bruto()
    del raw["codigo_cnes"]

    with pytest.raises(ValueError, match="codigo_cnes"):
        parser.parse_estabelecimento_detalhado(raw)
