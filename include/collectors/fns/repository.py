"""Persistência dos lançamentos de Fundo a Fundo do FNS em raw_fns.repasses.

Estratégia de idempotência: upsert por chave natural (id_lancamento), o
identificador sequencial que a própria API do FNS atribui a cada lançamento.
"""

from __future__ import annotations

import datetime as dt

import psycopg

from include.collectors.fns.client import ENDPOINT_LANCAMENTOS

CREATE_SCHEMA_SQL = "CREATE SCHEMA IF NOT EXISTS raw_fns;"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_fns.repasses (
    id_lancamento BIGINT PRIMARY KEY,
    -- Identificação do ente pelo FNS é por CNPJ, não por código IBGE; ver
    -- MUNICIPIO_REFERENCIA_CNPJ em parser.py.
    cnpj_ente_solicitante TEXT NOT NULL,
    nome_ente_solicitante TEXT NOT NULL,
    codigo_programa_agil TEXT,
    tipo_operacao TEXT NOT NULL,
    descricao_tipo_operacao TEXT NOT NULL,
    descricao_lancamento TEXT NOT NULL,
    data_lancamento DATE NOT NULL,
    data_evento_lancamento DATE NOT NULL,
    numero_referencia_unica TEXT,
    tipo_favorecido INTEGER,
    descricao_tipo_favorecido TEXT,
    nome_favorecido TEXT,
    valor_lancamento NUMERIC NOT NULL,
    id_categoria_despesa INTEGER,
    quantidade_subtransacoes INTEGER,
    _loaded_at TIMESTAMPTZ NOT NULL,
    _source_url TEXT NOT NULL,
    _reference_year INTEGER NOT NULL
);
"""

UPSERT_SQL = """
INSERT INTO raw_fns.repasses (
    id_lancamento, cnpj_ente_solicitante, nome_ente_solicitante,
    codigo_programa_agil, tipo_operacao, descricao_tipo_operacao,
    descricao_lancamento, data_lancamento, data_evento_lancamento,
    numero_referencia_unica, tipo_favorecido, descricao_tipo_favorecido,
    nome_favorecido, valor_lancamento, id_categoria_despesa,
    quantidade_subtransacoes, _loaded_at, _source_url, _reference_year
) VALUES (
    %(id_lancamento)s, %(cnpj_ente_solicitante)s, %(nome_ente_solicitante)s,
    %(codigo_programa_agil)s, %(tipo_operacao)s, %(descricao_tipo_operacao)s,
    %(descricao_lancamento)s, %(data_lancamento)s, %(data_evento_lancamento)s,
    %(numero_referencia_unica)s, %(tipo_favorecido)s, %(descricao_tipo_favorecido)s,
    %(nome_favorecido)s, %(valor_lancamento)s, %(id_categoria_despesa)s,
    %(quantidade_subtransacoes)s, %(_loaded_at)s, %(_source_url)s, %(_reference_year)s
)
ON CONFLICT (id_lancamento) DO UPDATE SET
    cnpj_ente_solicitante = EXCLUDED.cnpj_ente_solicitante,
    nome_ente_solicitante = EXCLUDED.nome_ente_solicitante,
    codigo_programa_agil = EXCLUDED.codigo_programa_agil,
    tipo_operacao = EXCLUDED.tipo_operacao,
    descricao_tipo_operacao = EXCLUDED.descricao_tipo_operacao,
    descricao_lancamento = EXCLUDED.descricao_lancamento,
    data_lancamento = EXCLUDED.data_lancamento,
    data_evento_lancamento = EXCLUDED.data_evento_lancamento,
    numero_referencia_unica = EXCLUDED.numero_referencia_unica,
    tipo_favorecido = EXCLUDED.tipo_favorecido,
    descricao_tipo_favorecido = EXCLUDED.descricao_tipo_favorecido,
    nome_favorecido = EXCLUDED.nome_favorecido,
    valor_lancamento = EXCLUDED.valor_lancamento,
    id_categoria_despesa = EXCLUDED.id_categoria_despesa,
    quantidade_subtransacoes = EXCLUDED.quantidade_subtransacoes,
    _loaded_at = EXCLUDED._loaded_at,
    _source_url = EXCLUDED._source_url,
    _reference_year = EXCLUDED._reference_year;
"""


def ensure_schema(conn: psycopg.Connection) -> None:
    """Cria o schema raw_fns e a tabela repasses, se ainda não existirem."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()


def upsert_repasses(conn: psycopg.Connection, lancamentos: list[dict], ano: int) -> int:
    """Faz upsert em lote dos lançamentos normalizados, usando id_lancamento como chave.

    Retorna a quantidade de registros enviados.
    """
    loaded_at = dt.datetime.now(dt.timezone.utc)
    rows = [
        {
            **lancamento,
            "_loaded_at": loaded_at,
            "_source_url": ENDPOINT_LANCAMENTOS,
            "_reference_year": ano,
        }
        for lancamento in lancamentos
    ]
    with conn.cursor() as cur:
        cur.executemany(UPSERT_SQL, rows)
    conn.commit()
    return len(rows)
