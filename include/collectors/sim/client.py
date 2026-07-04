"""Cliente para óbitos (SIM, grupo DO, CID-10) via FTP do DATASUS.

Não usa `pysus.sim()`: o catálogo do pysus retorna vazio para o grupo DO
(confirmado contra amostra real: `pysus.sim(state="RJ", year=2024,
group="DO")` retorna DataFrame vazio, mesmo o arquivo existindo no FTP com
148156 linhas) — mesma classe de problema documentada para SIA e SIH (ver
docs/COLLECTOR_TEMPLATE.md). Este client fala direto com o FTP (ftplib,
biblioteca padrão) e reaproveita só os decodificadores de baixo nível do
pysus (pyreaddbc para DBC->DBF, pysus.data.dbf_reader.read_dbf_fast para
DBF->tabular).
"""

from __future__ import annotations

import ftplib
import re
import tempfile
from pathlib import Path

from pyreaddbc import dbc2dbf
from pysus.data.dbf_reader import read_dbf_fast

FTP_HOST = "ftp.datasus.gov.br"
FTP_DIRETORIO = "/dissemin/publicos/SIM/CID10/DORES"
GRUPO_MORTALIDADE_GERAL = "DO"

COLUNAS = [
    "ORIGEM",
    "CODESTAB",
    "CODMUNOCOR",
    "CODMUNRES",
    "DTOBITO",
    "DTNASC",
    "IDADE",
    "SEXO",
    "RACACOR",
    "ESTCIV",
    "ESC",
    "LOCOCOR",
    "CAUSABAS",
    "CIRCOBITO",
    "ASSISTMED",
]


def _prefixo_arquivo(uf: str, ano: int) -> str:
    return f"{GRUPO_MORTALIDADE_GERAL}{uf.upper()}{ano}"


def list_arquivos(uf: str, ano: int) -> list[str]:
    """Lista no FTP do DATASUS os arquivos DBC de um ano do SIM/DO.

    Diferente de SIA/SIH (competência mensal), o SIM/DO é anual: 1 arquivo
    por UF/ano, com o ano em 4 dígitos no nome (confirmado contra amostra
    real: DORJ2024.dbc). O padrão aceita sufixo (a, b, c...) pelo mesmo risco
    de volume dos outros grupos DATASUS, embora não confirmado para o SIM.

    Exemplo:
        >>> list_arquivos("RJ", 2024)
        ['DORJ2024.dbc']
    """
    prefixo = _prefixo_arquivo(uf, ano)
    ftp = ftplib.FTP(FTP_HOST, timeout=60)
    try:
        ftp.login()
        ftp.cwd(FTP_DIRETORIO)
        arquivos = ftp.nlst()
    finally:
        ftp.quit()

    padrao = re.compile(rf"^{prefixo}[a-z]?\.dbc$", re.IGNORECASE)
    encontrados = sorted(a for a in arquivos if padrao.match(a))
    if not encontrados:
        raise RuntimeError(
            f"Nenhum arquivo encontrado em ftp://{FTP_HOST}{FTP_DIRETORIO} "
            f"para {prefixo}*.dbc; esperado ao menos 1 arquivo (ex.: {prefixo}.dbc)."
        )
    return encontrados


def _baixar_e_decodificar(nome_arquivo: str) -> list[dict]:
    with tempfile.TemporaryDirectory() as diretorio_temporario:
        caminho_dbc = Path(diretorio_temporario) / nome_arquivo
        caminho_dbf = caminho_dbc.with_suffix(".dbf")

        ftp = ftplib.FTP(FTP_HOST, timeout=60)
        try:
            ftp.login()
            ftp.cwd(FTP_DIRETORIO)
            with open(caminho_dbc, "wb") as arquivo:
                ftp.retrbinary(f"RETR {nome_arquivo}", arquivo.write)
        finally:
            ftp.quit()

        dbc2dbf(str(caminho_dbc), str(caminho_dbf))
        dataframe = read_dbf_fast(str(caminho_dbf), columns=COLUNAS)

    registros = dataframe.to_dict("records")
    for registro in registros:
        registro["_arquivo_origem"] = nome_arquivo
    return registros


def fetch_obitos(uf: str, ano: int) -> list[dict]:
    """Busca óbitos (SIM, grupo DO) do DATASUS para uf/ano.

    Não faz parsing nem filtro por município: retorna um dict por linha (um
    óbito), com a chave extra "_arquivo_origem".

    Exemplo:
        >>> registros = fetch_obitos("RJ", 2024)
        >>> registros[0]["CODMUNOCOR"]
        '330455'
    """
    registros: list[dict] = []
    for nome_arquivo in list_arquivos(uf, ano):
        registros.extend(_baixar_e_decodificar(nome_arquivo))
    return registros
