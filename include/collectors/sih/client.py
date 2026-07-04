"""Cliente para internações hospitalares (SIH, grupo RD) via FTP do DATASUS.

Não usa `pysus.sih()`: o catálogo do pysus retorna vazio para o grupo RD
(confirmado contra amostra real: `pysus.sih(state="RJ", year=2025, month=12,
group="RD")` retorna lista vazia, mesmo o arquivo existindo no FTP com
76169 linhas) — mesma classe de problema documentada para o SIA (ver
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
FTP_DIRETORIO = "/dissemin/publicos/SIHSUS/200801_/Dados"
GRUPO_AIH_REDUZIDA = "RD"

COLUNAS = [
    "N_AIH",
    "CNES",
    "MUNIC_MOV",
    "MUNIC_RES",
    "ANO_CMPT",
    "MES_CMPT",
    "PROC_REA",
    "CBOR",
    "IDADE",
    "SEXO",
    "RACA_COR",
    "DIAG_PRINC",
    "VAL_TOT",
    "DT_INTER",
    "DT_SAIDA",
    "DIAS_PERM",
    "MORTE",
]


def _prefixo_arquivo(uf: str, ano: int, mes: int) -> str:
    return f"{GRUPO_AIH_REDUZIDA}{uf.upper()}{ano % 100:02d}{mes:02d}"


def list_arquivos(uf: str, ano: int, mes: int) -> list[str]:
    """Lista no FTP do DATASUS os arquivos DBC de uma competência do SIH/RD.

    Uma competência do RD é normalmente 1 arquivo (confirmado contra amostra
    real: RDRJ2512.dbc), mas o padrão aceita sufixo (a, b, c...) pelo mesmo
    motivo do SIA — estados grandes podem exceder o limite de um único DBC.

    Exemplo:
        >>> list_arquivos("RJ", 2025, 12)
        ['RDRJ2512.dbc']
    """
    prefixo = _prefixo_arquivo(uf, ano, mes)
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


def fetch_internacoes(uf: str, ano: int, mes: int) -> list[dict]:
    """Busca internações hospitalares (SIH, grupo RD) do DATASUS para uf/ano/mes.

    Não faz parsing nem filtro por município: retorna um dict por linha (uma
    AIH), juntando todas as partes da competência, com a chave extra
    "_arquivo_origem" indicando de qual arquivo a linha veio.

    Exemplo:
        >>> registros = fetch_internacoes("RJ", 2025, 12)
        >>> registros[0]["N_AIH"]
        '3325100954329'
    """
    registros: list[dict] = []
    for nome_arquivo in list_arquivos(uf, ano, mes):
        registros.extend(_baixar_e_decodificar(nome_arquivo))
    return registros
