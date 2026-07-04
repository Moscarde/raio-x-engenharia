import pandas as pd
import pytest

from include.collectors.sim import client


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


def test_list_arquivos_encontra_o_arquivo_do_ano(monkeypatch):
    fake_ftp = FakeFTP(["DORJ2024.dbc", "DORJ2023.dbc", "outrofile.txt"])
    monkeypatch.setattr(client.ftplib, "FTP", fake_ftp)

    assert client.list_arquivos("RJ", 2024) == ["DORJ2024.dbc"]


def test_list_arquivos_rejeita_quando_nao_encontra_nenhum_arquivo(monkeypatch):
    fake_ftp = FakeFTP(["DORJ2023.dbc"])
    monkeypatch.setattr(client.ftplib, "FTP", fake_ftp)

    with pytest.raises(RuntimeError, match="DORJ2024"):
        client.list_arquivos("RJ", 2024)


def test_fetch_obitos_marca_arquivo_origem(monkeypatch):
    fake_ftp = FakeFTP(["DORJ2024.dbc"])
    monkeypatch.setattr(client.ftplib, "FTP", fake_ftp)
    monkeypatch.setattr(client, "dbc2dbf", lambda origem, destino: None)

    dataframes = {
        "DORJ2024.dbc": pd.DataFrame([{"CODMUNOCOR": "330455"}]),
    }

    def fake_read_dbf_fast(caminho_dbf, columns):
        nome_arquivo = caminho_dbf.replace(".dbf", ".dbc").split("/")[-1]
        return dataframes[nome_arquivo]

    monkeypatch.setattr(client, "read_dbf_fast", fake_read_dbf_fast)

    registros = client.fetch_obitos("RJ", 2024)

    assert len(registros) == 1
    assert registros[0]["_arquivo_origem"] == "DORJ2024.dbc"
