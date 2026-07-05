"""Persistência da produção ambulatorial do SIA em raw_sia.producao_ambulatorial.

Estratégia de idempotência: delete + insert por partição (competência do
ARQUIVO buscado, `competencia_arquivo`), não upsert por chave natural nem
partição pela competência real da linha. O SIA/PA não tem um identificador
único por linha (é produção agregada por procedimento/CBO/paciente/
competência); "delete + insert por partição" é uma das estratégias aceitas
para esse formato (ver CLAUDE.md, seção Idempotência).

Bug real encontrado e corrigido em 2026-07-05: a versão anterior particionava
o delete pela competência REAL de cada linha (`producao["competencia"]`,
vindo de PA_CMP), não pelo mês do arquivo buscado. Um arquivo do SIA de uma
competência (ex. PARJ2509) pode conter linhas de competências muito
anteriores, processadas com atraso (confirmado contra dado real: o arquivo
de set/2025 trouxe linhas com competência real de até out/2024). Como
`run_producao_ambulatorial.py` processa os 12 meses em sequência dentro da
mesma execução, cada fetch posterior que continha alguma linha retroativa
pra uma competência já carregada por um fetch anterior **apagava o dado
completo daquele mês e substituía só pelo pedaço retroativo do arquivo
mais recente** — confirmado contra dado real: depois de rodar jan-set/2025
em sequência, jan/2025 só tinha ~39 mil linhas no banco (contra os ~7,5
milhões que o próprio fetch de janeiro relatou ter carregado), porque os
fetches de fev-set continham pequenos trechos retroativos de janeiro e
foram sobrescrevendo o mês inteiro a cada rodada. A partição agora é pela
competência do arquivo buscado (UF/ano/mês passados pro fetch), que é
exclusiva por chamada — processar os 12 meses em qualquer ordem não afeta
mais os outros. `competencia` (a competência real de cada linha, PA_CMP)
continua gravada para uso analítico, só não é mais a chave de partição.

A tabela cobre o estado (UF) inteiro, não só o município de referência do
MVP — client.py já decodifica o arquivo inteiro antes de qualquer filtro
ser possível, então persistir tudo reaproveita o trabalho de decode em vez
de descartar ~38% das linhas já processadas (ver parser.py e ROADMAP.md).

Insere em lote via COPY (não INSERT/executemany): o volume de uma única
competência do estado inteiro já passa de milhões de linhas (medido: ~4,7
milhões em nov/2025), e o custo por round-trip do INSERT/executemany não
escala para esse volume.
"""

from __future__ import annotations

import datetime as dt

import psycopg

CREATE_SCHEMA_SQL = "CREATE SCHEMA IF NOT EXISTS raw_sia;"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_sia.producao_ambulatorial (
    codigo_cnes_estabelecimento TEXT NOT NULL,
    -- Código IBGE de 6 dígitos sem dígito verificador (PA_UFMUN do SIA).
    -- Cobre o estado (UF) inteiro, sem filtro de município — ver parser.py.
    cod_municipio_ibge6_estabelecimento TEXT NOT NULL,
    cod_municipio_ibge6_paciente TEXT NOT NULL,
    -- Competência real da linha (PA_CMP) — uso analítico, não é chave de
    -- partição (ver docstring do módulo).
    competencia TEXT NOT NULL,
    -- Competência do arquivo buscado (ano/mês passados pro fetch, formato
    -- "AAAAMM") — chave de partição do delete+insert.
    competencia_arquivo TEXT NOT NULL,
    codigo_procedimento TEXT NOT NULL,
    codigo_cbo TEXT NOT NULL,
    carater_atendimento TEXT NOT NULL,
    idade_paciente TEXT NOT NULL,
    sexo_paciente TEXT NOT NULL,
    raca_cor_paciente TEXT NOT NULL,
    quantidade_produzida TEXT NOT NULL,
    quantidade_aprovada TEXT NOT NULL,
    valor_produzido TEXT NOT NULL,
    valor_aprovado TEXT NOT NULL,
    origem_documento TEXT NOT NULL,
    _loaded_at TIMESTAMPTZ NOT NULL,
    _source_file TEXT NOT NULL,
    _reference_year INTEGER NOT NULL,
    _reference_month INTEGER NOT NULL
);
"""

DELETE_COMPETENCIA_ARQUIVO_SQL = """
DELETE FROM raw_sia.producao_ambulatorial
WHERE competencia_arquivo = %(competencia_arquivo)s;
"""

COLUNAS_INSERT = (
    "codigo_cnes_estabelecimento",
    "cod_municipio_ibge6_estabelecimento",
    "cod_municipio_ibge6_paciente",
    "competencia",
    "competencia_arquivo",
    "codigo_procedimento",
    "codigo_cbo",
    "carater_atendimento",
    "idade_paciente",
    "sexo_paciente",
    "raca_cor_paciente",
    "quantidade_produzida",
    "quantidade_aprovada",
    "valor_produzido",
    "valor_aprovado",
    "origem_documento",
    "_loaded_at",
    "_source_file",
    "_reference_year",
    "_reference_month",
)


CREATE_INDEX_COMPETENCIA_ARQUIVO_SQL = """
CREATE INDEX IF NOT EXISTS ix_producao_ambulatorial_competencia_arquivo
ON raw_sia.producao_ambulatorial (competencia_arquivo);
"""


def ensure_schema(conn: psycopg.Connection) -> None:
    """Cria o schema raw_sia, a tabela producao_ambulatorial e seu índice, se ainda não existirem.

    O índice em `competencia_arquivo` é usado tanto pelo delete+insert por
    partição desta tabela quanto pela carga em chunks do dbt (ver
    ROADMAP_DBT.md, etapa 5) — sem ele, cada chunk faz full scan nos 99.9M+
    registros.
    """
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_SQL)
        cur.execute(CREATE_INDEX_COMPETENCIA_ARQUIVO_SQL)
    conn.commit()


def substituir_producao_ambulatorial(
    conn: psycopg.Connection,
    producoes: list[dict],
    ano_arquivo: int,
    mes_arquivo: int,
) -> int:
    """Substitui a partição (competência do arquivo buscado) com o lote.

    `ano_arquivo`/`mes_arquivo` são o ano/mês passados pro fetch (não a
    competência real de cada linha) — cada chamada de fetch tem uma
    partição exclusiva, então rodar os 12 meses em sequência não sobrescreve
    dado de outro mês mesmo quando o arquivo buscado contém linhas
    retroativas de competências bem anteriores. Retorna a quantidade de
    linhas inseridas.
    """
    loaded_at = dt.datetime.now(dt.timezone.utc)
    competencia_arquivo = f"{ano_arquivo}{mes_arquivo:02d}"

    with conn.cursor() as cur:
        cur.execute(
            DELETE_COMPETENCIA_ARQUIVO_SQL,
            {"competencia_arquivo": competencia_arquivo},
        )

        with cur.copy(
            f"COPY raw_sia.producao_ambulatorial ({', '.join(COLUNAS_INSERT)}) FROM STDIN"
        ) as copy:
            for producao in producoes:
                competencia = producao["competencia"]
                copy.write_row(
                    (
                        producao["codigo_cnes_estabelecimento"],
                        producao["cod_municipio_ibge6_estabelecimento"],
                        producao["cod_municipio_ibge6_paciente"],
                        competencia,
                        competencia_arquivo,
                        producao["codigo_procedimento"],
                        producao["codigo_cbo"],
                        producao["carater_atendimento"],
                        producao["idade_paciente"],
                        producao["sexo_paciente"],
                        producao["raca_cor_paciente"],
                        producao["quantidade_produzida"],
                        producao["quantidade_aprovada"],
                        producao["valor_produzido"],
                        producao["valor_aprovado"],
                        producao["origem_documento"],
                        loaded_at,
                        producao["_source_file"],
                        int(competencia[:4]),
                        int(competencia[4:6]),
                    )
                )
    conn.commit()
    return len(producoes)
