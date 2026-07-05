"""Persistência do RREO-Anexo 14 (SICONFI) em raw_siops.rreo_anexo14.

Estratégia de idempotência: delete + insert por partição (município + ano +
bimestre). O RREO não tem um identificador de linha estável — cada bimestre
é uma republicação completa do demonstrativo, e entes podem retificar um
bimestre já enviado; refazer a partição inteira evita duplicata sem
depender de uma chave que a fonte não fornece.
"""

from __future__ import annotations

import datetime as dt

import psycopg

CREATE_SCHEMA_SQL = "CREATE SCHEMA IF NOT EXISTS raw_siops;"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_siops.rreo_anexo14 (
    ano_exercicio INTEGER NOT NULL,
    tipo_demonstrativo TEXT NOT NULL,
    periodo_bimestre INTEGER NOT NULL,
    periodicidade TEXT NOT NULL,
    instituicao TEXT NOT NULL,
    -- Código IBGE completo (7 dígitos), mesmo id_municipio de
    -- raw_ibge.municipios; ver MUNICIPIOS_REFERENCIA_ID_ENTE em parser.py.
    id_municipio INTEGER NOT NULL,
    uf TEXT NOT NULL,
    populacao BIGINT NOT NULL,
    anexo TEXT NOT NULL,
    esfera TEXT NOT NULL,
    rotulo TEXT NOT NULL,
    coluna TEXT NOT NULL,
    codigo_conta TEXT NOT NULL,
    descricao_conta TEXT NOT NULL,
    valor NUMERIC NOT NULL,
    _loaded_at TIMESTAMPTZ NOT NULL,
    _source_url TEXT NOT NULL
);
"""

DELETE_PARTICAO_SQL = """
DELETE FROM raw_siops.rreo_anexo14
WHERE id_municipio = %(municipio)s
  AND ano_exercicio = %(ano)s
  AND periodo_bimestre = %(periodo)s;
"""

COLUNAS_INSERT = (
    "ano_exercicio",
    "tipo_demonstrativo",
    "periodo_bimestre",
    "periodicidade",
    "instituicao",
    "id_municipio",
    "uf",
    "populacao",
    "anexo",
    "esfera",
    "rotulo",
    "coluna",
    "codigo_conta",
    "descricao_conta",
    "valor",
    "_loaded_at",
    "_source_url",
)


def ensure_schema(conn: psycopg.Connection) -> None:
    """Cria o schema raw_siops e a tabela rreo_anexo14, se ainda não existirem."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()


def substituir_rreo_anexo14(
    conn: psycopg.Connection,
    linhas: list[dict],
    municipio: int,
    ano: int,
    periodo: int,
    source_url: str,
) -> int:
    """Substitui a partição (município + ano + bimestre) com as linhas normalizadas.

    Retorna a quantidade de linhas inseridas.
    """
    loaded_at = dt.datetime.now(dt.timezone.utc)

    with conn.cursor() as cur:
        cur.execute(
            DELETE_PARTICAO_SQL,
            {"municipio": municipio, "ano": ano, "periodo": periodo},
        )

        with cur.copy(
            f"COPY raw_siops.rreo_anexo14 ({', '.join(COLUNAS_INSERT)}) FROM STDIN"
        ) as copy:
            for linha in linhas:
                copy.write_row(
                    (
                        linha["ano_exercicio"],
                        linha["tipo_demonstrativo"],
                        linha["periodo_bimestre"],
                        linha["periodicidade"],
                        linha["instituicao"],
                        linha["id_municipio"],
                        linha["uf"],
                        linha["populacao"],
                        linha["anexo"],
                        linha["esfera"],
                        linha["rotulo"],
                        linha["coluna"],
                        linha["codigo_conta"],
                        linha["descricao_conta"],
                        linha["valor"],
                        loaded_at,
                        source_url,
                    )
                )
    conn.commit()
    return len(linhas)
