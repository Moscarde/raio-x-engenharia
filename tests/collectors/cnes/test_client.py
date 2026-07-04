import pandas as pd
import pytest

from include.collectors.cnes import client


def test_fetch_estabelecimentos_retorna_registros_do_grupo_st(monkeypatch):
    registros = [{"CNES": "0033979", "CODUFMUN": "330010"}]

    def fake_cnes(state, year, month, group, as_dataframe):
        assert state == "RJ"
        assert year == 2025
        assert month == 12
        assert group == client.GROUP_ESTABELECIMENTOS
        assert as_dataframe is True
        return pd.DataFrame(registros)

    monkeypatch.setattr(client.pysus, "cnes", fake_cnes)

    assert client.fetch_estabelecimentos("RJ", 2025, 12) == registros


def test_fetch_estabelecimentos_rejeita_dataframe_vazio(monkeypatch):
    def fake_cnes(state, year, month, group, as_dataframe):
        return pd.DataFrame()

    monkeypatch.setattr(client.pysus, "cnes", fake_cnes)

    with pytest.raises(RuntimeError, match="RJ"):
        client.fetch_estabelecimentos("RJ", 2025, 12)


def test_source_filename_monta_nome_do_arquivo_dbc():
    assert client.source_filename("RJ", 2025, 12) == "STRJ2512.dbc"
