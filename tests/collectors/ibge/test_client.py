import pytest

from include.collectors.ibge import client


class FakeRespostaIBGE:
    """Substitui requests.Response para testar fetch_municipios sem rede."""

    def __init__(self, status_code: int, payload: list[dict]):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> list[dict]:
        return self._payload


def test_fetch_municipios_retorna_json_decodificado(monkeypatch):
    payload = [{"id": 1100015, "nome": "Alta Floresta D'Oeste"}]

    def fake_get(url, timeout):
        assert url == client.MUNICIPIOS_URL
        return FakeRespostaIBGE(status_code=200, payload=payload)

    monkeypatch.setattr(client.requests, "get", fake_get)

    assert client.fetch_municipios() == payload


def test_fetch_municipios_rejeita_status_diferente_de_200(monkeypatch):
    def fake_get(url, timeout):
        return FakeRespostaIBGE(status_code=500, payload=[])

    monkeypatch.setattr(client.requests, "get", fake_get)

    with pytest.raises(RuntimeError, match="500"):
        client.fetch_municipios()
