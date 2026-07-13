import pytest

from include.collectors.sisab import client, parser


class FakeResposta:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def cadastro_bruto(**overrides):
    cadastro = {
        "competencia_referencia": 202412,
        "sigla_unidade_federacao": "RJ",
        "codigo_municipio_ibge": 330455,
        "nome_municipio": "RIO DE JANEIRO",
        "estimativa_populacional_ibge": 6729894,
        "tipo_equipe": 70,
        "sigla_equipe": "eSF",
        "situacao_equipe": "todas",
        "pessoas_vinculadas_criterios_ponderacao": "Não",
        "pessoas_vinculadas_equipe_municipio": 5566876.0,
    }
    return {**cadastro, **overrides}


def test_fetch_cadastro_vinculado_pagina_ate_terminar(monkeypatch):
    primeira_pagina = [{"linha": indice} for indice in range(client.LIMITE_PAGINA)]
    segunda_pagina = [{"linha": client.LIMITE_PAGINA}]

    def fake_get(url, params, timeout):
        assert url == client.ENDPOINT_CADASTRO_VINCULADO
        assert timeout == 30
        if params["offset"] == 0:
            return FakeResposta(200, {"sisab_cadastro_vinculado": primeira_pagina})
        assert params["offset"] == client.LIMITE_PAGINA
        return FakeResposta(200, {"sisab_cadastro_vinculado": segunda_pagina})

    monkeypatch.setattr(client.requests, "get", fake_get)

    assert client.fetch_cadastro_vinculado(330455, 202412) == (
        primeira_pagina + segunda_pagina
    )


def test_fetch_cadastro_vinculado_rejeita_status_diferente_de_200(monkeypatch):
    monkeypatch.setattr(
        client.requests, "get", lambda *args, **kwargs: FakeResposta(500, {})
    )

    with pytest.raises(RuntimeError, match="500"):
        client.fetch_cadastro_vinculado(330455, 202412)


def test_fetch_cadastro_vinculado_rejeita_resposta_sem_campo(monkeypatch):
    monkeypatch.setattr(
        client.requests, "get", lambda *args, **kwargs: FakeResposta(200, {})
    )

    with pytest.raises(RuntimeError, match="sisab_cadastro_vinculado"):
        client.fetch_cadastro_vinculado(330455, 202412)


def test_fetch_cadastro_vinculado_rejeita_lista_vazia(monkeypatch):
    monkeypatch.setattr(
        client.requests,
        "get",
        lambda *args, **kwargs: FakeResposta(200, {"sisab_cadastro_vinculado": []}),
    )

    with pytest.raises(RuntimeError, match="330455"):
        client.fetch_cadastro_vinculado(330455, 202412)


def test_parse_cadastro_vinculado_normaliza_campos_do_contrato_raw():
    parsed = parser.parse_cadastro_vinculado(cadastro_bruto())

    assert parsed["sigla_equipe"] == "eSF"
    assert parsed["pessoas_vinculadas_equipe_municipio"] == 5566876.0


def test_parse_cadastro_vinculado_rejeita_campo_obrigatorio_ausente():
    raw = cadastro_bruto()
    del raw["situacao_equipe"]

    with pytest.raises(ValueError, match="situacao_equipe"):
        parser.parse_cadastro_vinculado(raw)
