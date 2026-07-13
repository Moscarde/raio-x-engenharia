import pytest

from include.collectors.portaltransparencia import client


class FakeResposta:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_resolve_api_key_le_do_ambiente(monkeypatch):
    monkeypatch.setenv("PORTAL_TRANSPARENCIA_API_KEY", "abc123")

    assert client.resolve_api_key() == "abc123"


def test_resolve_api_key_rejeita_ambiente_sem_chave(monkeypatch):
    monkeypatch.delenv("PORTAL_TRANSPARENCIA_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="PORTAL_TRANSPARENCIA_API_KEY"):
        client.resolve_api_key()


def test_fetch_recursos_recebidos_pagina_ate_pagina_vazia(monkeypatch):
    primeira_pagina = [{"linha": 1}, {"linha": 2}]
    segunda_pagina = [{"linha": 3}]
    terceira_pagina: list[dict] = []

    def fake_get(url, params, headers, timeout):
        assert url == client.ENDPOINT_RECURSOS_RECEBIDOS
        assert headers == {"chave-api-dados": "abc123"}
        assert params["codigoFavorecido"] == "42498733000148"
        pagina = params["pagina"]
        return {
            1: FakeResposta(200, primeira_pagina),
            2: FakeResposta(200, segunda_pagina),
            3: FakeResposta(200, terceira_pagina),
        }[pagina]

    monkeypatch.setattr(client.requests, "get", fake_get)

    resultado = client.fetch_recursos_recebidos(
        "abc123", "42498733000148", "01/2025", "12/2025"
    )

    assert resultado == primeira_pagina + segunda_pagina


def test_fetch_recursos_recebidos_rejeita_status_diferente_de_200(monkeypatch):
    monkeypatch.setattr(
        client.requests, "get", lambda *args, **kwargs: FakeResposta(403, {})
    )

    with pytest.raises(RuntimeError, match="403"):
        client.fetch_recursos_recebidos(
            "abc123", "42498733000148", "01/2025", "12/2025"
        )
