import pytest

from include.collectors.sisab import client


class FakeResposta:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_fetch_indicadores_desempenho_retorna_linhas_da_api(monkeypatch):
    linhas = [{"codigo_municipio": 330455}]

    def fake_get(url, params, timeout):
        assert url == client.ENDPOINT_INDICADOR_DESEMPENHO
        assert params == {
            "codigo_municipio": 330455,
            "quadrimestre": "2024Q3",
            "limit": client.LIMITE_PAGINA,
        }
        return FakeResposta(200, {"sisab_indicador_desempenho": linhas})

    monkeypatch.setattr(client.requests, "get", fake_get)

    assert client.fetch_indicadores_desempenho(330455, "2024Q3") == linhas


def test_fetch_indicadores_desempenho_rejeita_status_diferente_de_200(monkeypatch):
    monkeypatch.setattr(
        client.requests, "get", lambda url, params, timeout: FakeResposta(500, {})
    )

    with pytest.raises(RuntimeError, match="500"):
        client.fetch_indicadores_desempenho(330455, "2024Q3")


def test_fetch_indicadores_desempenho_rejeita_resposta_sem_campo_esperado(monkeypatch):
    monkeypatch.setattr(
        client.requests, "get", lambda url, params, timeout: FakeResposta(200, {})
    )

    with pytest.raises(RuntimeError, match="sisab_indicador_desempenho"):
        client.fetch_indicadores_desempenho(330455, "2024Q3")


def test_fetch_indicadores_desempenho_rejeita_lista_vazia(monkeypatch):
    monkeypatch.setattr(
        client.requests,
        "get",
        lambda url, params, timeout: FakeResposta(
            200, {"sisab_indicador_desempenho": []}
        ),
    )

    with pytest.raises(RuntimeError, match="330455"):
        client.fetch_indicadores_desempenho(330455, "2024Q3")


def test_fetch_indicadores_desempenho_rejeita_possivel_truncamento(monkeypatch):
    linhas = [{"codigo_municipio": 330455} for _ in range(client.LIMITE_PAGINA)]
    monkeypatch.setattr(
        client.requests,
        "get",
        lambda url, params, timeout: FakeResposta(
            200, {"sisab_indicador_desempenho": linhas}
        ),
    )

    with pytest.raises(RuntimeError, match="LIMITE_PAGINA"):
        client.fetch_indicadores_desempenho(330455, "2024Q3")
