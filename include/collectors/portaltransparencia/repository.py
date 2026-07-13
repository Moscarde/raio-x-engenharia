"""Persistência dos recursos recebidos em raw_portaltransparencia.recursos_recebidos_saude.

Estratégia de idempotência: delete + insert por partição (CNPJ do
favorecido + ano). A API não expõe identificador de linha estável — mesmo
padrão de SIA/SIM/SINASC/SIOPS/SISAB.
"""

from __future__ import annotations

import datetime as dt

import psycopg

CREATE_SCHEMA_SQL = "CREATE SCHEMA IF NOT EXISTS raw_portaltransparencia;"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_portaltransparencia.recursos_recebidos_saude (
    competencia INTEGER NOT NULL,
    -- CNPJ do ente favorecido, só dígitos — mesmo formato de
    -- raw_fns.repasses.cnpj_ente_solicitante; ver MUNICIPIOS_REFERENCIA_CNPJ
    -- em parser.py.
    cnpj_favorecido TEXT NOT NULL,
    nome_favorecido TEXT NOT NULL,
    tipo_favorecido TEXT NOT NULL,
    municipio_favorecido TEXT NOT NULL,
    sigla_uf_favorecido TEXT NOT NULL,
    codigo_ug TEXT NOT NULL,
    nome_ug TEXT NOT NULL,
    codigo_orgao TEXT NOT NULL,
    nome_orgao TEXT NOT NULL,
    codigo_orgao_superior TEXT NOT NULL,
    nome_orgao_superior TEXT NOT NULL,
    -- Pode ser negativo (estorno/devolução) — ver comentário em parser.py.
    valor NUMERIC NOT NULL,
    _loaded_at TIMESTAMPTZ NOT NULL,
    _source_url TEXT NOT NULL,
    _reference_year INTEGER NOT NULL
);
"""

DELETE_PARTICAO_SQL = """
DELETE FROM raw_portaltransparencia.recursos_recebidos_saude
WHERE cnpj_favorecido = %(cnpj_favorecido)s
  AND _reference_year = %(ano)s;
"""

COLUNAS_INSERT = (
    "competencia",
    "cnpj_favorecido",
    "nome_favorecido",
    "tipo_favorecido",
    "municipio_favorecido",
    "sigla_uf_favorecido",
    "codigo_ug",
    "nome_ug",
    "codigo_orgao",
    "nome_orgao",
    "codigo_orgao_superior",
    "nome_orgao_superior",
    "valor",
    "_loaded_at",
    "_source_url",
    "_reference_year",
)


def ensure_schema(conn: psycopg.Connection) -> None:
    """Cria o schema raw_portaltransparencia e a tabela, se ainda não existirem."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()


def substituir_recursos_recebidos(
    conn: psycopg.Connection,
    linhas: list[dict],
    cnpj_favorecido: str,
    ano: int,
    source_url: str,
) -> int:
    """Substitui a partição (CNPJ do favorecido + ano) com as linhas normalizadas.

    Retorna a quantidade de linhas inseridas.
    """
    loaded_at = dt.datetime.now(dt.timezone.utc)

    with conn.cursor() as cur:
        cur.execute(
            DELETE_PARTICAO_SQL, {"cnpj_favorecido": cnpj_favorecido, "ano": ano}
        )

        with cur.copy(
            "COPY raw_portaltransparencia.recursos_recebidos_saude "
            f"({', '.join(COLUNAS_INSERT)}) FROM STDIN"
        ) as copy:
            for linha in linhas:
                copy.write_row(
                    (
                        linha["competencia"],
                        linha["cnpj_favorecido"],
                        linha["nome_favorecido"],
                        linha["tipo_favorecido"],
                        linha["municipio_favorecido"],
                        linha["sigla_uf_favorecido"],
                        linha["codigo_ug"],
                        linha["nome_ug"],
                        linha["codigo_orgao"],
                        linha["nome_orgao"],
                        linha["codigo_orgao_superior"],
                        linha["nome_orgao_superior"],
                        linha["valor"],
                        loaded_at,
                        source_url,
                        ano,
                    )
                )
    conn.commit()
    return len(linhas)
