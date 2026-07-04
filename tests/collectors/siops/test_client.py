import pytest

from include.collectors.siops import client


class FakeResposta:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_fetch_rreo_anexo14_retorna_items_da_api(monkeypatch):
    linhas = [{"cod_ibge": 3304557}]

    def fake_get(url, params, timeout):
        assert url == client.ENDPOINT_RREO
        assert params == {
            "an_exercicio": 2025,
            "nr_periodo": 6,
            "co_tipo_demonstrativo": "RREO",
            "no_anexo": client.ANEXO_DEMONSTRATIVO_SIMPLIFICADO,
            "id_ente": 3304557,
        }
        return FakeResposta(200, {"items": linhas})

    monkeypatch.setattr(client.requests, "get", fake_get)

    assert client.fetch_rreo_anexo14(3304557, 2025, 6) == linhas


def test_fetch_rreo_anexo14_rejeita_status_diferente_de_200(monkeypatch):
    monkeypatch.setattr(
        client.requests, "get", lambda url, params, timeout: FakeResposta(500, {})
    )

    with pytest.raises(RuntimeError, match="500"):
        client.fetch_rreo_anexo14(3304557, 2025, 6)


def test_fetch_rreo_anexo14_rejeita_resposta_sem_items(monkeypatch):
    monkeypatch.setattr(
        client.requests, "get", lambda url, params, timeout: FakeResposta(200, {})
    )

    with pytest.raises(RuntimeError, match="items"):
        client.fetch_rreo_anexo14(3304557, 2025, 6)


def test_fetch_rreo_anexo14_rejeita_lista_vazia(monkeypatch):
    monkeypatch.setattr(
        client.requests,
        "get",
        lambda url, params, timeout: FakeResposta(200, {"items": []}),
    )

    with pytest.raises(RuntimeError, match="3304557"):
        client.fetch_rreo_anexo14(3304557, 2025, 6)
