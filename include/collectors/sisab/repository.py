"""Persistência dos indicadores de desempenho do Previne Brasil em
raw_sisab.indicador_desempenho.

Estratégia de idempotência: delete + insert por partição (município +
quadrimestre). A API não expõe um identificador de linha estável; dentro de
uma partição, a combinação (codigo_tipo_indicador, visao_equipe) já é
única (confirmado contra amostra real: 18 linhas = 6 tipos x 3 visões, sem
duplicata), mas refazer a partição inteira evita depender dessa garantia
implícita da fonte.
"""

from __future__ import annotations

import datetime as dt

import psycopg

CREATE_SCHEMA_SQL = "CREATE SCHEMA IF NOT EXISTS raw_sisab;"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_sisab.indicador_desempenho (
    uf TEXT NOT NULL,
    municipio TEXT NOT NULL,
    -- Código IBGE de 6 dígitos sem dígito verificador; ver
    -- MUNICIPIOS_REFERENCIA_CODIGO_MUNICIPIO em parser.py.
    codigo_municipio INTEGER NOT NULL,
    quadrimestre TEXT NOT NULL,
    competencia INTEGER NOT NULL,
    codigo_tipo_indicador INTEGER NOT NULL,
    visao_equipe TEXT NOT NULL,
    numerador NUMERIC NOT NULL,
    denominador_utilizador NUMERIC NOT NULL,
    denominador_identificado NUMERIC NOT NULL,
    denominador_estimado NUMERIC NOT NULL,
    percentual NUMERIC NOT NULL,
    percentual_quadrimestre NUMERIC NOT NULL,
    cadastro NUMERIC NOT NULL,
    base_externa NUMERIC NOT NULL,
    populacao BIGINT NOT NULL,
    _loaded_at TIMESTAMPTZ NOT NULL,
    _source_url TEXT NOT NULL
);
"""

DELETE_PARTICAO_SQL = """
DELETE FROM raw_sisab.indicador_desempenho
WHERE codigo_municipio = %(municipio)s
  AND quadrimestre = %(quadrimestre)s;
"""

COLUNAS_INSERT = (
    "uf",
    "municipio",
    "codigo_municipio",
    "quadrimestre",
    "competencia",
    "codigo_tipo_indicador",
    "visao_equipe",
    "numerador",
    "denominador_utilizador",
    "denominador_identificado",
    "denominador_estimado",
    "percentual",
    "percentual_quadrimestre",
    "cadastro",
    "base_externa",
    "populacao",
    "_loaded_at",
    "_source_url",
)


def ensure_schema(conn: psycopg.Connection) -> None:
    """Cria o schema raw_sisab e a tabela indicador_desempenho, se ainda não existirem."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()


def substituir_indicadores_desempenho(
    conn: psycopg.Connection,
    indicadores: list[dict],
    municipio: int,
    quadrimestre: str,
    source_url: str,
) -> int:
    """Substitui a partição (município + quadrimestre) com os indicadores normalizados.

    Retorna a quantidade de linhas inseridas.
    """
    loaded_at = dt.datetime.now(dt.timezone.utc)

    with conn.cursor() as cur:
        cur.execute(
            DELETE_PARTICAO_SQL,
            {"municipio": municipio, "quadrimestre": quadrimestre},
        )

        with cur.copy(
            f"COPY raw_sisab.indicador_desempenho ({', '.join(COLUNAS_INSERT)}) FROM STDIN"
        ) as copy:
            for indicador in indicadores:
                copy.write_row(
                    (
                        indicador["uf"],
                        indicador["municipio"],
                        indicador["codigo_municipio"],
                        indicador["quadrimestre"],
                        indicador["competencia"],
                        indicador["codigo_tipo_indicador"],
                        indicador["visao_equipe"],
                        indicador["numerador"],
                        indicador["denominador_utilizador"],
                        indicador["denominador_identificado"],
                        indicador["denominador_estimado"],
                        indicador["percentual"],
                        indicador["percentual_quadrimestre"],
                        indicador["cadastro"],
                        indicador["base_externa"],
                        indicador["populacao"],
                        loaded_at,
                        source_url,
                    )
                )
    conn.commit()
    return len(indicadores)


CREATE_TABLE_CADASTRO_VINCULADO_SQL = """
CREATE TABLE IF NOT EXISTS raw_sisab.cadastro_vinculado (
    competencia_referencia INTEGER NOT NULL,
    sigla_unidade_federacao TEXT NOT NULL,
    -- Código IBGE de 6 dígitos sem dígito verificador, mesmo padrão de
    -- indicador_desempenho.codigo_municipio.
    codigo_municipio_ibge INTEGER NOT NULL,
    nome_municipio TEXT NOT NULL,
    estimativa_populacional_ibge BIGINT NOT NULL,
    tipo_equipe INTEGER NOT NULL,
    sigla_equipe TEXT NOT NULL,
    situacao_equipe TEXT NOT NULL,
    pessoas_vinculadas_criterios_ponderacao TEXT NOT NULL,
    pessoas_vinculadas_equipe_municipio NUMERIC NOT NULL,
    _loaded_at TIMESTAMPTZ NOT NULL,
    _source_url TEXT NOT NULL
);
"""

DELETE_PARTICAO_CADASTRO_VINCULADO_SQL = """
DELETE FROM raw_sisab.cadastro_vinculado
WHERE codigo_municipio_ibge = %(municipio)s
  AND competencia_referencia = %(competencia)s;
"""

COLUNAS_INSERT_CADASTRO_VINCULADO = (
    "competencia_referencia",
    "sigla_unidade_federacao",
    "codigo_municipio_ibge",
    "nome_municipio",
    "estimativa_populacional_ibge",
    "tipo_equipe",
    "sigla_equipe",
    "situacao_equipe",
    "pessoas_vinculadas_criterios_ponderacao",
    "pessoas_vinculadas_equipe_municipio",
    "_loaded_at",
    "_source_url",
)


def ensure_schema_cadastro_vinculado(conn: psycopg.Connection) -> None:
    """Cria o schema raw_sisab e a tabela cadastro_vinculado, se ainda não existirem."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_CADASTRO_VINCULADO_SQL)
    conn.commit()


def substituir_cadastro_vinculado(
    conn: psycopg.Connection,
    linhas: list[dict],
    municipio: int,
    competencia: int,
    source_url: str,
) -> int:
    """Substitui a partição (município + competência) com as linhas normalizadas.

    Mesma estratégia de idempotência de substituir_indicadores_desempenho:
    a API não expõe identificador de linha estável, então a partição
    inteira é refeita a cada carga.
    """
    loaded_at = dt.datetime.now(dt.timezone.utc)

    with conn.cursor() as cur:
        cur.execute(
            DELETE_PARTICAO_CADASTRO_VINCULADO_SQL,
            {"municipio": municipio, "competencia": competencia},
        )

        with cur.copy(
            "COPY raw_sisab.cadastro_vinculado "
            f"({', '.join(COLUNAS_INSERT_CADASTRO_VINCULADO)}) FROM STDIN"
        ) as copy:
            for linha in linhas:
                copy.write_row(
                    (
                        linha["competencia_referencia"],
                        linha["sigla_unidade_federacao"],
                        linha["codigo_municipio_ibge"],
                        linha["nome_municipio"],
                        linha["estimativa_populacional_ibge"],
                        linha["tipo_equipe"],
                        linha["sigla_equipe"],
                        linha["situacao_equipe"],
                        linha["pessoas_vinculadas_criterios_ponderacao"],
                        linha["pessoas_vinculadas_equipe_municipio"],
                        loaded_at,
                        source_url,
                    )
                )
    conn.commit()
    return len(linhas)
