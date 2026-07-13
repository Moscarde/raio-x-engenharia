import pandas as pd
import pytest

from include.collectors.cnes import client, parser


def equipe_bruta(**overrides):
    equipe = {
        "IDEQUIPE": "330455001234567890",
        "CNES": "1234567",
        "CODUFMUN": "330455",
        "TIPO_EQP": "70",
        "NOME_EQP": "ESF EXEMPLO",
        "DT_ATIVA": "202001",
        "DT_DESAT": "900001",
        "MOTDESAT": "00",
        "TP_DESAT": "0",
        "COMPETEN": "202512",
        "ID_AREA": "3304550012",
        "NOMEAREA": "AREA EXEMPLO",
        "ID_SEGM": "33045501",
        "DESCSEGM": "SEGMENTO EXEMPLO",
        "TIPOSEGM": "1",
    }
    return {**equipe, **overrides}


def test_fetch_equipes_aps_retorna_registros_do_grupo_ep(monkeypatch):
    registros = [equipe_bruta()]

    def fake_cnes(state, year, month, group, as_dataframe):
        assert (state, year, month, group, as_dataframe) == ("RJ", 2025, 12, "EP", True)
        return pd.DataFrame(registros)

    monkeypatch.setattr(client.pysus, "cnes", fake_cnes)

    assert client.fetch_equipes_aps("RJ", 2025, 12) == registros


def test_fetch_equipes_aps_rejeita_dataframe_vazio(monkeypatch):
    monkeypatch.setattr(client.pysus, "cnes", lambda **kwargs: pd.DataFrame())

    with pytest.raises(RuntimeError, match="EP"):
        client.fetch_equipes_aps("RJ", 2025, 12)


def test_source_filename_monta_nome_do_arquivo_ep():
    assert client.source_filename("RJ", 2025, 12, "EP") == "EPRJ2512.dbc"


def test_parse_equipe_aps_normaliza_campos_do_contrato_raw():
    parsed = parser.parse_equipe_aps(equipe_bruta())

    assert parsed["id_equipe"] == "330455001234567890"
    assert parsed["codigo_tipo_equipe"] == "70"
    assert parsed["competencia_desativacao"] == "900001"


def test_parse_equipe_aps_rejeita_campo_obrigatorio_ausente():
    raw = equipe_bruta()
    del raw["NOME_EQP"]

    with pytest.raises(ValueError, match="NOME_EQP"):
        parser.parse_equipe_aps(raw)


def test_parse_equipes_aps_filtra_municipio_e_tipo_de_equipe():
    equipes = [
        equipe_bruta(),
        equipe_bruta(IDEQUIPE="fora-do-municipio", CODUFMUN="330010"),
        equipe_bruta(IDEQUIPE="fora-da-aps", TIPO_EQP="71"),
    ]

    assert parser.parse_equipes_aps(equipes) == [parser.parse_equipe_aps(equipes[0])]
