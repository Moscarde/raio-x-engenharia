"""Persistência das internações hospitalares do SIH em raw_sih.internacoes.

Estratégia de idempotência: upsert por chave natural (numero_aih), não
delete+insert por partição. Diferente do SIA/PA (produção agregada, sem
identificador único por linha), cada linha do SIH/RD é uma AIH (internação)
com número próprio (N_AIH); upsert por chave natural é uma das estratégias
aceitas para esse formato (ver CLAUDE.md, seção Idempotência).
"""

from __future__ import annotations

import datetime as dt

import psycopg

CREATE_SCHEMA_SQL = "CREATE SCHEMA IF NOT EXISTS raw_sih;"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_sih.internacoes (
    numero_aih TEXT PRIMARY KEY,
    codigo_cnes_estabelecimento TEXT NOT NULL,
    -- Código IBGE de 6 dígitos sem dígito verificador (MUNIC_MOV do SIH);
    -- ver MUNICIPIO_REFERENCIA_CODUFMUN em parser.py.
    cod_municipio_ibge6_estabelecimento TEXT NOT NULL,
    cod_municipio_ibge6_paciente TEXT NOT NULL,
    competencia TEXT NOT NULL,
    codigo_procedimento TEXT NOT NULL,
    codigo_cbo TEXT NOT NULL,
    idade_paciente TEXT NOT NULL,
    sexo_paciente TEXT NOT NULL,
    raca_cor_paciente TEXT NOT NULL,
    diagnostico_principal TEXT NOT NULL,
    valor_total TEXT NOT NULL,
    data_internacao TEXT NOT NULL,
    data_saida TEXT NOT NULL,
    dias_permanencia TEXT NOT NULL,
    indicador_obito TEXT NOT NULL,
    _loaded_at TIMESTAMPTZ NOT NULL,
    _source_file TEXT NOT NULL,
    _reference_year INTEGER NOT NULL,
    _reference_month INTEGER NOT NULL
);
"""

UPSERT_SQL = """
INSERT INTO raw_sih.internacoes (
    numero_aih, codigo_cnes_estabelecimento, cod_municipio_ibge6_estabelecimento,
    cod_municipio_ibge6_paciente, competencia, codigo_procedimento, codigo_cbo,
    idade_paciente, sexo_paciente, raca_cor_paciente, diagnostico_principal,
    valor_total, data_internacao, data_saida, dias_permanencia, indicador_obito,
    _loaded_at, _source_file, _reference_year, _reference_month
) VALUES (
    %(numero_aih)s, %(codigo_cnes_estabelecimento)s, %(cod_municipio_ibge6_estabelecimento)s,
    %(cod_municipio_ibge6_paciente)s, %(competencia)s, %(codigo_procedimento)s, %(codigo_cbo)s,
    %(idade_paciente)s, %(sexo_paciente)s, %(raca_cor_paciente)s, %(diagnostico_principal)s,
    %(valor_total)s, %(data_internacao)s, %(data_saida)s, %(dias_permanencia)s, %(indicador_obito)s,
    %(_loaded_at)s, %(_source_file)s, %(_reference_year)s, %(_reference_month)s
)
ON CONFLICT (numero_aih) DO UPDATE SET
    codigo_cnes_estabelecimento = EXCLUDED.codigo_cnes_estabelecimento,
    cod_municipio_ibge6_estabelecimento = EXCLUDED.cod_municipio_ibge6_estabelecimento,
    cod_municipio_ibge6_paciente = EXCLUDED.cod_municipio_ibge6_paciente,
    competencia = EXCLUDED.competencia,
    codigo_procedimento = EXCLUDED.codigo_procedimento,
    codigo_cbo = EXCLUDED.codigo_cbo,
    idade_paciente = EXCLUDED.idade_paciente,
    sexo_paciente = EXCLUDED.sexo_paciente,
    raca_cor_paciente = EXCLUDED.raca_cor_paciente,
    diagnostico_principal = EXCLUDED.diagnostico_principal,
    valor_total = EXCLUDED.valor_total,
    data_internacao = EXCLUDED.data_internacao,
    data_saida = EXCLUDED.data_saida,
    dias_permanencia = EXCLUDED.dias_permanencia,
    indicador_obito = EXCLUDED.indicador_obito,
    _loaded_at = EXCLUDED._loaded_at,
    _source_file = EXCLUDED._source_file,
    _reference_year = EXCLUDED._reference_year,
    _reference_month = EXCLUDED._reference_month;
"""


def ensure_schema(conn: psycopg.Connection) -> None:
    """Cria o schema raw_sih e a tabela internacoes, se ainda não existirem."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()


def upsert_internacoes(
    conn: psycopg.Connection,
    internacoes: list[dict],
    ano: int,
    mes: int,
) -> int:
    """Faz upsert em lote das internações normalizadas, usando numero_aih como chave.

    Retorna a quantidade de registros enviados.
    """
    loaded_at = dt.datetime.now(dt.timezone.utc)
    rows = [
        {
            **internacao,
            "_loaded_at": loaded_at,
            "_reference_year": ano,
            "_reference_month": mes,
        }
        for internacao in internacoes
    ]
    with conn.cursor() as cur:
        cur.executemany(UPSERT_SQL, rows)
    conn.commit()
    return len(rows)
