import pandas as pd
import pytest

from include.collectors.sia import client


class FakeFTP:
    """Substitui ftplib.FTP para testar list_arquivos/fetch sem rede real."""

    def __init__(self, arquivos_disponiveis, conteudo_por_arquivo=None):
        self._arquivos_disponiveis = arquivos_disponiveis
        self._conteudo_por_arquivo = conteudo_por_arquivo or {}

    def __call__(self, host, timeout=60):
        return self

    def login(self):
        pass

    def cwd(self, diretorio):
        assert diretorio == client.FTP_DIRETORIO

    def nlst(self):
        return self._arquivos_disponiveis

    def retrbinary(self, comando, callback):
        nome_arquivo = comando.split(" ", 1)[1]
        callback(self._conteudo_por_arquivo.get(nome_arquivo, b"conteudo-fake"))

    def quit(self):
        pass


def test_list_arquivos_encontra_todas_as_partes_da_competencia(monkeypatch):
    fake_ftp = FakeFTP(
        [
            "PARJ2512a.dbc",
            "PARJ2512b.dbc",
            "PARJ2511a.dbc",
            "outrofile.txt",
        ]
    )
    monkeypatch.setattr(client.ftplib, "FTP", fake_ftp)

    assert client.list_arquivos("RJ", 2025, 12) == ["PARJ2512a.dbc", "PARJ2512b.dbc"]


def test_list_arquivos_rejeita_quando_nao_encontra_nenhum_arquivo(monkeypatch):
    fake_ftp = FakeFTP(["PARJ2511a.dbc"])
    monkeypatch.setattr(client.ftplib, "FTP", fake_ftp)

    with pytest.raises(RuntimeError, match="PARJ2512"):
        client.list_arquivos("RJ", 2025, 12)


def test_fetch_producao_ambulatorial_junta_partes_e_marca_arquivo_origem(monkeypatch):
    fake_ftp = FakeFTP(["PARJ2512a.dbc", "PARJ2512b.dbc"])
    monkeypatch.setattr(client.ftplib, "FTP", fake_ftp)
    monkeypatch.setattr(client, "dbc2dbf", lambda origem, destino: None)

    dataframes = {
        "PARJ2512a.dbc": pd.DataFrame([{"PA_CMP": "202512", "PA_UFMUN": "330455"}]),
        "PARJ2512b.dbc": pd.DataFrame([{"PA_CMP": "202512", "PA_UFMUN": "330010"}]),
    }

    def fake_read_dbf_fast(caminho_dbf, columns):
        nome_arquivo = caminho_dbf.replace(".dbf", ".dbc").split("/")[-1]
        return dataframes[nome_arquivo]

    monkeypatch.setattr(client, "read_dbf_fast", fake_read_dbf_fast)

    registros = client.fetch_producao_ambulatorial("RJ", 2025, 12)

    assert len(registros) == 2
    assert registros[0]["_arquivo_origem"] == "PARJ2512a.dbc"
    assert registros[1]["_arquivo_origem"] == "PARJ2512b.dbc"
