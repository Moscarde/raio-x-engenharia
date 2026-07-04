import pytest

from include.collectors.fns import client


class FakeResposta:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_fetch_lancamentos_retorna_registros_da_api(monkeypatch):
    registros = [{"id_lancamento_gestao_financeira": 1}]

    def fake_get(url, params, timeout):
        assert url == client.ENDPOINT_LANCAMENTOS
        assert ("cnpj_ente_solicitante_gestao_financeira", "eq.42498733000148") in params
        assert ("data_lancamento_gestao_financeira", "gte.2025-01-01") in params
        assert ("data_lancamento_gestao_financeira", "lte.2025-12-31") in params
        return FakeResposta(200, registros)

    monkeypatch.setattr(client.requests, "get", fake_get)

    assert client.fetch_lancamentos("42498733000148", 2025) == registros


def test_fetch_lancamentos_rejeita_status_diferente_de_200(monkeypatch):
    monkeypatch.setattr(
        client.requests, "get", lambda url, params, timeout: FakeResposta(500, [])
    )

    with pytest.raises(RuntimeError, match="500"):
        client.fetch_lancamentos("42498733000148", 2025)


def test_fetch_lancamentos_rejeita_lista_vazia(monkeypatch):
    monkeypatch.setattr(
        client.requests, "get", lambda url, params, timeout: FakeResposta(200, [])
    )

    with pytest.raises(RuntimeError, match="42498733000148"):
        client.fetch_lancamentos("42498733000148", 2025)


def test_fetch_lancamentos_rejeita_possivel_truncamento(monkeypatch):
    registros = [{"id_lancamento_gestao_financeira": i} for i in range(client.LIMITE_PAGINA)]
    monkeypatch.setattr(
        client.requests, "get", lambda url, params, timeout: FakeResposta(200, registros)
    )

    with pytest.raises(RuntimeError, match="LIMITE_PAGINA"):
        client.fetch_lancamentos("42498733000148", 2025)
