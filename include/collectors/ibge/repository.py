"""Persistência dos municípios do IBGE em raw_ibge.municipios."""

from __future__ import annotations

import datetime as dt

import psycopg

from include.collectors.ibge.client import MUNICIPIOS_URL, POPULACAO_URL

CREATE_SCHEMA_SQL = "CREATE SCHEMA IF NOT EXISTS raw_ibge;"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_ibge.municipios (
    id_municipio INTEGER PRIMARY KEY,
    nome_municipio TEXT NOT NULL,
    -- NULL para municípios muito recentes ainda sem microrregiao/mesorregiao
    -- cadastradas na API do IBGE (ex.: id 5101837, Boa Esperança do Norte/MT).
    id_microrregiao INTEGER,
    nome_microrregiao TEXT,
    id_mesorregiao INTEGER,
    nome_mesorregiao TEXT,
    id_uf INTEGER NOT NULL,
    sigla_uf TEXT NOT NULL,
    nome_uf TEXT NOT NULL,
    id_regiao INTEGER NOT NULL,
    sigla_regiao TEXT NOT NULL,
    nome_regiao TEXT NOT NULL,
    _loaded_at TIMESTAMPTZ NOT NULL,
    _source_url TEXT NOT NULL
);
"""

UPSERT_SQL = """
INSERT INTO raw_ibge.municipios (
    id_municipio, nome_municipio, id_microrregiao, nome_microrregiao,
    id_mesorregiao, nome_mesorregiao, id_uf, sigla_uf, nome_uf,
    id_regiao, sigla_regiao, nome_regiao, _loaded_at, _source_url
) VALUES (
    %(id_municipio)s, %(nome_municipio)s, %(id_microrregiao)s, %(nome_microrregiao)s,
    %(id_mesorregiao)s, %(nome_mesorregiao)s, %(id_uf)s, %(sigla_uf)s, %(nome_uf)s,
    %(id_regiao)s, %(sigla_regiao)s, %(nome_regiao)s, %(_loaded_at)s, %(_source_url)s
)
ON CONFLICT (id_municipio) DO UPDATE SET
    nome_municipio = EXCLUDED.nome_municipio,
    id_microrregiao = EXCLUDED.id_microrregiao,
    nome_microrregiao = EXCLUDED.nome_microrregiao,
    id_mesorregiao = EXCLUDED.id_mesorregiao,
    nome_mesorregiao = EXCLUDED.nome_mesorregiao,
    id_uf = EXCLUDED.id_uf,
    sigla_uf = EXCLUDED.sigla_uf,
    nome_uf = EXCLUDED.nome_uf,
    id_regiao = EXCLUDED.id_regiao,
    sigla_regiao = EXCLUDED.sigla_regiao,
    nome_regiao = EXCLUDED.nome_regiao,
    _loaded_at = EXCLUDED._loaded_at,
    _source_url = EXCLUDED._source_url;
"""


def ensure_schema(conn: psycopg.Connection) -> None:
    """Cria o schema raw_ibge e a tabela municipios, se ainda não existirem."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()


def upsert_municipios(conn: psycopg.Connection, municipios: list[dict]) -> int:
    """Faz upsert em lote dos municípios normalizados, usando id_municipio como chave.

    Retorna a quantidade de registros enviados.
    """
    loaded_at = dt.datetime.now(dt.timezone.utc)
    rows = [
        {**m, "_loaded_at": loaded_at, "_source_url": MUNICIPIOS_URL}
        for m in municipios
    ]
    with conn.cursor() as cur:
        cur.executemany(UPSERT_SQL, rows)
    conn.commit()
    return len(rows)


CREATE_TABLE_POPULACAO_SQL = """
CREATE TABLE IF NOT EXISTS raw_ibge.populacao_estimada (
    id_municipio INTEGER NOT NULL,
    nome_municipio TEXT NOT NULL,
    -- Estimativa TCU/IBGE tem 1 valor por ano (referência 1º de julho), não
    -- por competência mensal — chave natural é município + ano.
    ano_referencia INTEGER NOT NULL,
    populacao_estimada BIGINT NOT NULL,
    _loaded_at TIMESTAMPTZ NOT NULL,
    _source_url TEXT NOT NULL,
    PRIMARY KEY (id_municipio, ano_referencia)
);
"""

UPSERT_POPULACAO_SQL = """
INSERT INTO raw_ibge.populacao_estimada (
    id_municipio, nome_municipio, ano_referencia, populacao_estimada,
    _loaded_at, _source_url
) VALUES (
    %(id_municipio)s, %(nome_municipio)s, %(ano_referencia)s, %(populacao_estimada)s,
    %(_loaded_at)s, %(_source_url)s
)
ON CONFLICT (id_municipio, ano_referencia) DO UPDATE SET
    nome_municipio = EXCLUDED.nome_municipio,
    populacao_estimada = EXCLUDED.populacao_estimada,
    _loaded_at = EXCLUDED._loaded_at,
    _source_url = EXCLUDED._source_url;
"""


def ensure_schema_populacao(conn: psycopg.Connection) -> None:
    """Cria o schema raw_ibge e a tabela populacao_estimada, se ainda não existirem."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_POPULACAO_SQL)
    conn.commit()


def upsert_populacao_estimada(conn: psycopg.Connection, populacao: list[dict]) -> int:
    """Faz upsert em lote da população estimada, usando (id_municipio, ano) como chave.

    Retorna a quantidade de registros enviados.
    """
    loaded_at = dt.datetime.now(dt.timezone.utc)
    rows = [
        {**p, "_loaded_at": loaded_at, "_source_url": POPULACAO_URL} for p in populacao
    ]
    with conn.cursor() as cur:
        cur.executemany(UPSERT_POPULACAO_SQL, rows)
    conn.commit()
    return len(rows)
