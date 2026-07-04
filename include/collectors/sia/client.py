"""Cliente para produção ambulatorial (SIA, grupo PA) via FTP do DATASUS.

Não usa `pysus.sia()`: o catálogo público do pysus indexa só 1 arquivo por
competência quando o SIA distribui múltiplas partes (sufixo a, b, c...),
descartando as demais silenciosamente (confirmado contra amostra real — ver
docs/COLLECTOR_TEMPLATE.md). Este client fala direto com o FTP (ftplib,
biblioteca padrão) para garantir que todas as partes de uma competência sejam
buscadas, e reaproveita só os decodificadores de baixo nível do pysus
(pyreaddbc para DBC->DBF, pysus.data.dbf_reader.read_dbf_fast para DBF->
tabular) em vez do dbfread puro-Python, que é a mesma ordem de grandeza de
lentidão para os volumes do SIA (~450s/milhão de linhas medido contra amostra
real; read_dbf_fast com colunas restritas mediu ~150s/milhão de linhas).
"""

from __future__ import annotations

import ftplib
import re
import tempfile
from pathlib import Path

from pyreaddbc import dbc2dbf
from pysus.data.dbf_reader import read_dbf_fast

FTP_HOST = "ftp.datasus.gov.br"
FTP_DIRETORIO = "/dissemin/publicos/SIASUS/200801_/Dados"
GRUPO_PRODUCAO_AMBULATORIAL = "PA"

COLUNAS = [
    "PA_CODUNI",
    "PA_UFMUN",
    "PA_MUNPCN",
    "PA_CMP",
    "PA_PROC_ID",
    "PA_CBOCOD",
    "PA_CATEND",
    "PA_IDADE",
    "PA_SEXO",
    "PA_RACACOR",
    "PA_QTDPRO",
    "PA_QTDAPR",
    "PA_VALPRO",
    "PA_VALAPR",
    "PA_DOCORIG",
]


def _prefixo_arquivo(uf: str, ano: int, mes: int) -> str:
    return f"{GRUPO_PRODUCAO_AMBULATORIAL}{uf.upper()}{ano % 100:02d}{mes:02d}"


def list_arquivos(uf: str, ano: int, mes: int) -> list[str]:
    """Lista no FTP do DATASUS os arquivos DBC de uma competência do SIA/PA.

    Uma competência pode estar dividida em mais de um arquivo (sufixo a, b,
    c...) quando o volume do estado excede o limite de um único DBC.

    Exemplo:
        >>> list_arquivos("RJ", 2025, 12)
        ['PARJ2512a.dbc', 'PARJ2512b.dbc']
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
            f"para {prefixo}*.dbc; esperado ao menos 1 arquivo (ex.: {prefixo}a.dbc)."
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


def fetch_producao_ambulatorial(uf: str, ano: int, mes: int) -> list[dict]:
    """Busca a produção ambulatorial (SIA, grupo PA) do DATASUS para uf/ano/mes.

    Não faz parsing nem filtro por município: retorna um dict por linha,
    juntando todas as partes (a, b, c...) da competência, com a chave extra
    "_arquivo_origem" indicando de qual arquivo a linha veio.

    Exemplo:
        >>> registros = fetch_producao_ambulatorial("RJ", 2025, 12)
        >>> registros[0]["PA_CMP"]
        '202512'
    """
    registros: list[dict] = []
    for nome_arquivo in list_arquivos(uf, ano, mes):
        registros.extend(_baixar_e_decodificar(nome_arquivo))
    return registros
