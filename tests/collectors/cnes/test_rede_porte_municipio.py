from include.collectors.cnes.parser import parse_rede_porte_municipio

RAW_RIO = {"CODUFMUN": "330455", "COMPETEN": "202512"}
RAW_PARATY = {"CODUFMUN": "330380", "COMPETEN": "202512"}


def test_parse_rede_porte_municipio_conta_por_municipio_sem_filtrar():
    raw_estabelecimentos = [RAW_RIO, RAW_RIO, RAW_RIO, RAW_PARATY]

    resultado = parse_rede_porte_municipio(raw_estabelecimentos)

    por_municipio = {r["cod_municipio_ibge6"]: r for r in resultado}
    assert por_municipio["330455"]["quantidade_estabelecimentos"] == 3
    assert por_municipio["330380"]["quantidade_estabelecimentos"] == 1
    assert all(r["competencia"] == "202512" for r in resultado)


def test_parse_rede_porte_municipio_lista_vazia_retorna_lista_vazia():
    assert parse_rede_porte_municipio([]) == []
