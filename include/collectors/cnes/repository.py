"""Persistência dos estabelecimentos do CNES em raw_cnes.estabelecimentos."""

from __future__ import annotations

import datetime as dt

import psycopg

CREATE_SCHEMA_SQL = "CREATE SCHEMA IF NOT EXISTS raw_cnes;"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_cnes.estabelecimentos (
    codigo_cnes TEXT PRIMARY KEY,
    -- Código IBGE de 6 dígitos sem dígito verificador (CODUFMUN do CNES);
    -- ver MUNICIPIO_REFERENCIA_CODUFMUN em parser.py.
    cod_municipio_ibge6 TEXT NOT NULL,
    tipo_pessoa TEXT NOT NULL,
    nivel_dependencia TEXT NOT NULL,
    tipo_unidade TEXT NOT NULL,
    natureza_organizacao TEXT NOT NULL,
    natureza_juridica TEXT NOT NULL,
    atividade_ensino TEXT NOT NULL,
    vinculo_sus TEXT NOT NULL,
    tipo_gestao TEXT NOT NULL,
    esfera_administrativa TEXT NOT NULL,
    competencia TEXT NOT NULL,
    data_atualizacao TEXT NOT NULL,
    _loaded_at TIMESTAMPTZ NOT NULL,
    _source_file TEXT NOT NULL,
    _reference_year INTEGER NOT NULL,
    _reference_month INTEGER NOT NULL
);
"""

UPSERT_SQL = """
INSERT INTO raw_cnes.estabelecimentos (
    codigo_cnes, cod_municipio_ibge6, tipo_pessoa, nivel_dependencia,
    tipo_unidade, natureza_organizacao, natureza_juridica, atividade_ensino,
    vinculo_sus, tipo_gestao, esfera_administrativa, competencia,
    data_atualizacao, _loaded_at, _source_file, _reference_year, _reference_month
) VALUES (
    %(codigo_cnes)s, %(cod_municipio_ibge6)s, %(tipo_pessoa)s, %(nivel_dependencia)s,
    %(tipo_unidade)s, %(natureza_organizacao)s, %(natureza_juridica)s, %(atividade_ensino)s,
    %(vinculo_sus)s, %(tipo_gestao)s, %(esfera_administrativa)s, %(competencia)s,
    %(data_atualizacao)s, %(_loaded_at)s, %(_source_file)s, %(_reference_year)s, %(_reference_month)s
)
ON CONFLICT (codigo_cnes) DO UPDATE SET
    cod_municipio_ibge6 = EXCLUDED.cod_municipio_ibge6,
    tipo_pessoa = EXCLUDED.tipo_pessoa,
    nivel_dependencia = EXCLUDED.nivel_dependencia,
    tipo_unidade = EXCLUDED.tipo_unidade,
    natureza_organizacao = EXCLUDED.natureza_organizacao,
    natureza_juridica = EXCLUDED.natureza_juridica,
    atividade_ensino = EXCLUDED.atividade_ensino,
    vinculo_sus = EXCLUDED.vinculo_sus,
    tipo_gestao = EXCLUDED.tipo_gestao,
    esfera_administrativa = EXCLUDED.esfera_administrativa,
    competencia = EXCLUDED.competencia,
    data_atualizacao = EXCLUDED.data_atualizacao,
    _loaded_at = EXCLUDED._loaded_at,
    _source_file = EXCLUDED._source_file,
    _reference_year = EXCLUDED._reference_year,
    _reference_month = EXCLUDED._reference_month;
"""


def ensure_schema(conn: psycopg.Connection) -> None:
    """Cria o schema raw_cnes e a tabela estabelecimentos, se ainda não existirem."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()


def upsert_estabelecimentos(
    conn: psycopg.Connection,
    estabelecimentos: list[dict],
    source_file: str,
    ano: int,
    mes: int,
) -> int:
    """Faz upsert em lote dos estabelecimentos normalizados, usando codigo_cnes como chave.

    Retorna a quantidade de registros enviados.
    """
    loaded_at = dt.datetime.now(dt.timezone.utc)
    rows = [
        {
            **e,
            "_loaded_at": loaded_at,
            "_source_file": source_file,
            "_reference_year": ano,
            "_reference_month": mes,
        }
        for e in estabelecimentos
    ]
    with conn.cursor() as cur:
        cur.executemany(UPSERT_SQL, rows)
    conn.commit()
    return len(rows)
