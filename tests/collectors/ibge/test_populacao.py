import pytest

from include.collectors.ibge import client, parser

CORPO_AGREGADO = [
    {
        "id": "9324",
        "variavel": "População residente estimada",
        "unidade": "Pessoas",
        "resultados": [
            {
                "classificacoes": [],
                "series": [
                    {
                        "localidade": {
                            "id": "3304557",
                            "nivel": {"id": "N6", "nome": "Município"},
                            "nome": "Rio de Janeiro (RJ)",
                        },
                        "serie": {"2025": "6730729"},
                    },
                    {
                        "localidade": {
                            "id": "3303807",
                            "nivel": {"id": "N6", "nome": "Município"},
                            "nome": "Paraty (RJ)",
                        },
                        "serie": {"2025": "47668"},
                    },
                ],
            }
        ],
    }
]


class FakeRespostaIBGE:
    """Substitui requests.Response para testar fetch_populacao_estimada sem rede."""

    def __init__(self, status_code: int, payload: list[dict]):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> list[dict]:
        return self._payload


def test_fetch_populacao_estimada_retorna_json_decodificado(monkeypatch):
    def fake_get(url, params, timeout):
        assert url == client.POPULACAO_URL
        assert params == {"localidades": "N6[3304557,3303807]"}
        return FakeRespostaIBGE(status_code=200, payload=CORPO_AGREGADO)

    monkeypatch.setattr(client.requests, "get", fake_get)

    assert client.fetch_populacao_estimada((3304557, 3303807)) == CORPO_AGREGADO


def test_fetch_populacao_estimada_rejeita_status_diferente_de_200(monkeypatch):
    def fake_get(url, params, timeout):
        return FakeRespostaIBGE(status_code=500, payload=[])

    monkeypatch.setattr(client.requests, "get", fake_get)

    with pytest.raises(RuntimeError, match="500"):
        client.fetch_populacao_estimada((3304557,))


def test_fetch_populacao_estimada_uf_usa_localidade_aninhada(monkeypatch):
    def fake_get(url, params, timeout):
        assert url == client.POPULACAO_URL
        assert params == {"localidades": "N6[N3[33]]"}
        return FakeRespostaIBGE(status_code=200, payload=CORPO_AGREGADO)

    monkeypatch.setattr(client.requests, "get", fake_get)

    assert client.fetch_populacao_estimada_uf(33) == CORPO_AGREGADO


def test_fetch_populacao_estimada_uf_rejeita_status_diferente_de_200(monkeypatch):
    def fake_get(url, params, timeout):
        return FakeRespostaIBGE(status_code=500, payload=[])

    monkeypatch.setattr(client.requests, "get", fake_get)

    with pytest.raises(RuntimeError, match="500"):
        client.fetch_populacao_estimada_uf(33)


def test_parse_populacao_estimada_normaliza_uma_linha_por_municipio():
    resultado = parser.parse_populacao_estimada(CORPO_AGREGADO)

    assert resultado == [
        {
            "id_municipio": 3304557,
            "nome_municipio": "Rio de Janeiro (RJ)",
            "ano_referencia": 2025,
            "populacao_estimada": 6730729,
        },
        {
            "id_municipio": 3303807,
            "nome_municipio": "Paraty (RJ)",
            "ano_referencia": 2025,
            "populacao_estimada": 47668,
        },
    ]


def test_parse_populacao_estimada_rejeita_corpo_sem_series():
    with pytest.raises(ValueError, match="series"):
        parser.parse_populacao_estimada([{"resultados": [{}]}])
