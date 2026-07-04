"""Persistência dos nascidos vivos do SINASC em raw_sinasc.nascidos_vivos.

Estratégia de idempotência: delete + insert por partição (ano + município),
mesma justificativa do SIM (ver include/collectors/sim/repository.py): o
SINASC/DN não tem um identificador de registro estável entre execuções, e
o arquivo anual não mistura nascimentos de outros anos (confirmado contra
amostra real: DNRJ2022.dbc: 100% dos registros com DTNASC em 2022).
"""

from __future__ import annotations

import datetime as dt

import psycopg

CREATE_SCHEMA_SQL = "CREATE SCHEMA IF NOT EXISTS raw_sinasc;"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_sinasc.nascidos_vivos (
    origem_informacao TEXT NOT NULL,
    codigo_cnes_estabelecimento TEXT NOT NULL,
    -- Código IBGE de 6 dígitos sem dígito verificador (CODMUNNASC do
    -- SINASC); ver MUNICIPIO_REFERENCIA_CODUFMUN em parser.py.
    cod_municipio_ibge6_nascimento TEXT NOT NULL,
    cod_municipio_ibge6_residencia TEXT NOT NULL,
    data_nascimento TEXT NOT NULL,
    sexo TEXT NOT NULL,
    raca_cor TEXT NOT NULL,
    peso_gramas TEXT NOT NULL,
    semanas_gestacao_faixa TEXT NOT NULL,
    tipo_parto TEXT NOT NULL,
    apgar1 TEXT NOT NULL,
    apgar5 TEXT NOT NULL,
    numero_consultas_prenatal TEXT NOT NULL,
    idade_mae TEXT NOT NULL,
    escolaridade_mae TEXT NOT NULL,
    _loaded_at TIMESTAMPTZ NOT NULL,
    _source_file TEXT NOT NULL,
    _reference_year INTEGER NOT NULL
);
"""

DELETE_PARTICAO_SQL = """
DELETE FROM raw_sinasc.nascidos_vivos
WHERE _reference_year = %(ano)s
  AND cod_municipio_ibge6_nascimento = %(municipio)s;
"""

COLUNAS_INSERT = (
    "origem_informacao",
    "codigo_cnes_estabelecimento",
    "cod_municipio_ibge6_nascimento",
    "cod_municipio_ibge6_residencia",
    "data_nascimento",
    "sexo",
    "raca_cor",
    "peso_gramas",
    "semanas_gestacao_faixa",
    "tipo_parto",
    "apgar1",
    "apgar5",
    "numero_consultas_prenatal",
    "idade_mae",
    "escolaridade_mae",
    "_loaded_at",
    "_source_file",
    "_reference_year",
)


def ensure_schema(conn: psycopg.Connection) -> None:
    """Cria o schema raw_sinasc e a tabela nascidos_vivos, se ainda não existirem."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()


def substituir_nascidos_vivos(
    conn: psycopg.Connection,
    nascidos_vivos: list[dict],
    municipio: str,
    ano: int,
) -> int:
    """Substitui a partição (ano + município) com os nascimentos normalizados.

    Retorna a quantidade de linhas inseridas.
    """
    loaded_at = dt.datetime.now(dt.timezone.utc)

    with conn.cursor() as cur:
        cur.execute(DELETE_PARTICAO_SQL, {"ano": ano, "municipio": municipio})

        with cur.copy(
            f"COPY raw_sinasc.nascidos_vivos ({', '.join(COLUNAS_INSERT)}) FROM STDIN"
        ) as copy:
            for nascido_vivo in nascidos_vivos:
                copy.write_row(
                    (
                        nascido_vivo["origem_informacao"],
                        nascido_vivo["codigo_cnes_estabelecimento"],
                        nascido_vivo["cod_municipio_ibge6_nascimento"],
                        nascido_vivo["cod_municipio_ibge6_residencia"],
                        nascido_vivo["data_nascimento"],
                        nascido_vivo["sexo"],
                        nascido_vivo["raca_cor"],
                        nascido_vivo["peso_gramas"],
                        nascido_vivo["semanas_gestacao_faixa"],
                        nascido_vivo["tipo_parto"],
                        nascido_vivo["apgar1"],
                        nascido_vivo["apgar5"],
                        nascido_vivo["numero_consultas_prenatal"],
                        nascido_vivo["idade_mae"],
                        nascido_vivo["escolaridade_mae"],
                        loaded_at,
                        nascido_vivo["_source_file"],
                        ano,
                    )
                )
    conn.commit()
    return len(nascidos_vivos)
