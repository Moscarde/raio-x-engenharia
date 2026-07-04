"""Persistência dos municípios do IBGE em raw_ibge.municipios."""

from __future__ import annotations

import datetime as dt

import psycopg

from include.collectors.ibge.client import MUNICIPIOS_URL

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
