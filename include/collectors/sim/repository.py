"""Persistência dos óbitos do SIM em raw_sim.obitos.

Estratégia de idempotência: delete + insert por partição (ano + município),
não upsert por chave natural. O SIM/DO não tem um identificador de registro
estável entre execuções (o campo CONTADOR é só um contador sequencial local
ao arquivo, sem garantia de unicidade entre arquivos de anos diferentes);
"delete + insert por partição" é uma das estratégias aceitas para esse
formato (ver CLAUDE.md, seção Idempotência). Confirmado contra amostra real
que o arquivo anual do SIM não mistura óbitos de outros anos (DORJ2024.dbc:
100% dos registros com DTOBITO em 2024), então a partição por ano do
arquivo é equivalente à partição pelo ano real do óbito.
"""

from __future__ import annotations

import datetime as dt

import psycopg

CREATE_SCHEMA_SQL = "CREATE SCHEMA IF NOT EXISTS raw_sim;"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_sim.obitos (
    origem_informacao TEXT NOT NULL,
    codigo_cnes_estabelecimento TEXT NOT NULL,
    -- Código IBGE de 6 dígitos sem dígito verificador (CODMUNOCOR do SIM);
    -- ver MUNICIPIO_REFERENCIA_CODUFMUN em parser.py.
    cod_municipio_ibge6_ocorrencia TEXT NOT NULL,
    cod_municipio_ibge6_residencia TEXT NOT NULL,
    data_obito TEXT NOT NULL,
    data_nascimento TEXT NOT NULL,
    idade TEXT NOT NULL,
    sexo TEXT NOT NULL,
    raca_cor TEXT NOT NULL,
    estado_civil TEXT NOT NULL,
    escolaridade TEXT NOT NULL,
    local_ocorrencia TEXT NOT NULL,
    causa_basica TEXT NOT NULL,
    circunstancia_obito TEXT NOT NULL,
    assistencia_medica TEXT NOT NULL,
    _loaded_at TIMESTAMPTZ NOT NULL,
    _source_file TEXT NOT NULL,
    _reference_year INTEGER NOT NULL
);
"""

DELETE_PARTICAO_SQL = """
DELETE FROM raw_sim.obitos
WHERE _reference_year = %(ano)s
  AND cod_municipio_ibge6_ocorrencia = %(municipio)s;
"""

COLUNAS_INSERT = (
    "origem_informacao",
    "codigo_cnes_estabelecimento",
    "cod_municipio_ibge6_ocorrencia",
    "cod_municipio_ibge6_residencia",
    "data_obito",
    "data_nascimento",
    "idade",
    "sexo",
    "raca_cor",
    "estado_civil",
    "escolaridade",
    "local_ocorrencia",
    "causa_basica",
    "circunstancia_obito",
    "assistencia_medica",
    "_loaded_at",
    "_source_file",
    "_reference_year",
)


def ensure_schema(conn: psycopg.Connection) -> None:
    """Cria o schema raw_sim e a tabela obitos, se ainda não existirem."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()


def substituir_obitos(
    conn: psycopg.Connection,
    obitos: list[dict],
    municipio: str,
    ano: int,
) -> int:
    """Substitui a partição (ano + município) com os óbitos normalizados.

    Retorna a quantidade de linhas inseridas.
    """
    loaded_at = dt.datetime.now(dt.timezone.utc)

    with conn.cursor() as cur:
        cur.execute(DELETE_PARTICAO_SQL, {"ano": ano, "municipio": municipio})

        with cur.copy(
            f"COPY raw_sim.obitos ({', '.join(COLUNAS_INSERT)}) FROM STDIN"
        ) as copy:
            for obito in obitos:
                copy.write_row(
                    (
                        obito["origem_informacao"],
                        obito["codigo_cnes_estabelecimento"],
                        obito["cod_municipio_ibge6_ocorrencia"],
                        obito["cod_municipio_ibge6_residencia"],
                        obito["data_obito"],
                        obito["data_nascimento"],
                        obito["idade"],
                        obito["sexo"],
                        obito["raca_cor"],
                        obito["estado_civil"],
                        obito["escolaridade"],
                        obito["local_ocorrencia"],
                        obito["causa_basica"],
                        obito["circunstancia_obito"],
                        obito["assistencia_medica"],
                        loaded_at,
                        obito["_source_file"],
                        ano,
                    )
                )
    conn.commit()
    return len(obitos)
