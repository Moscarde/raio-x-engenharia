"""Persistência da produção ambulatorial do SIA em raw_sia.producao_ambulatorial.

Estratégia de idempotência: delete + insert por partição (competência),
não upsert por chave natural. O SIA/PA não tem um identificador único por
linha (é produção agregada por procedimento/CBO/paciente/competência);
"delete + insert por partição" é uma das estratégias aceitas para esse
formato (ver CLAUDE.md, seção Idempotência).

A tabela cobre o estado (UF) inteiro, não só o município de referência do
MVP — client.py já decodifica o arquivo inteiro antes de qualquer filtro
ser possível, então persistir tudo reaproveita o trabalho de decode em vez
de descartar ~38% das linhas já processadas (ver parser.py e ROADMAP.md).
A partição de delete é só por competência, não por competência+município.

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
    competencia TEXT NOT NULL,
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

DELETE_COMPETENCIA_SQL = """
DELETE FROM raw_sia.producao_ambulatorial
WHERE competencia = %(competencia)s;
"""

COLUNAS_INSERT = (
    "codigo_cnes_estabelecimento",
    "cod_municipio_ibge6_estabelecimento",
    "cod_municipio_ibge6_paciente",
    "competencia",
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


def ensure_schema(conn: psycopg.Connection) -> None:
    """Cria o schema raw_sia e a tabela producao_ambulatorial, se ainda não existirem."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()


def substituir_producao_ambulatorial(
    conn: psycopg.Connection,
    producoes: list[dict],
) -> int:
    """Substitui as partições (competência real) presentes no lote.

    A partição apagada/substituída é a competência de cada linha
    (`producao["competencia"]`, vindo de PA_CMP), não o mês do arquivo
    buscado: um arquivo do SIA de uma competência (ex. STRJ2512) pode conter
    linhas de competências anteriores, processadas com atraso (confirmado
    contra dado real — ver limitação conhecida em
    docs/COLLECTOR_TEMPLATE.md). Retorna a quantidade de linhas inseridas.
    """
    loaded_at = dt.datetime.now(dt.timezone.utc)
    competencias = {p["competencia"] for p in producoes}

    with conn.cursor() as cur:
        for competencia in competencias:
            cur.execute(DELETE_COMPETENCIA_SQL, {"competencia": competencia})

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
