"""Persistência dos estabelecimentos do CNES em raw_cnes.estabelecimentos."""

from __future__ import annotations

import datetime as dt

import psycopg

CREATE_SCHEMA_SQL = "CREATE SCHEMA IF NOT EXISTS raw_cnes;"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_cnes.estabelecimentos (
    codigo_cnes TEXT NOT NULL,
    -- Código IBGE de 6 dígitos sem dígito verificador (CODUFMUN do CNES);
    -- ver MUNICIPIOS_REFERENCIA_CODUFMUN em parser.py.
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
    -- Chave composta com codigo_cnes (não mais chave simples): cada
    -- competência carregada vira 1 linha nova por estabelecimento, em vez
    -- de sobrescrever a anterior — é o que dá série histórica pra "Histórico
    -- de rede CNES" (ver ROADMAP.md). dim_estabelecimento (dbt) filtra pra
    -- competência mais recente por codigo_cnes, preservando o contrato
    -- "1 linha por estabelecimento" de quem já consome a dimensão.
    competencia TEXT NOT NULL,
    data_atualizacao TEXT NOT NULL,
    _loaded_at TIMESTAMPTZ NOT NULL,
    _source_file TEXT NOT NULL,
    _reference_year INTEGER NOT NULL,
    _reference_month INTEGER NOT NULL,
    PRIMARY KEY (codigo_cnes, competencia)
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
ON CONFLICT (codigo_cnes, competencia) DO UPDATE SET
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


CREATE_TABLE_EQUIPES_APS_SQL = """
CREATE TABLE IF NOT EXISTS raw_cnes.equipes_aps (
    -- Identificador da equipe, estável entre competências (permite
    -- acompanhar ativação/desativação da mesma equipe ao longo do tempo).
    id_equipe TEXT PRIMARY KEY,
    codigo_cnes TEXT NOT NULL,
    cod_municipio_ibge6 TEXT NOT NULL,
    codigo_tipo_equipe TEXT NOT NULL,
    nome_equipe TEXT NOT NULL,
    competencia_ativacao TEXT NOT NULL,
    -- Sentinela "900001" quando a equipe segue ativa (confirmado contra
    -- dado real); de-para fica para staging/dbt, não para o raw layer.
    competencia_desativacao TEXT NOT NULL,
    motivo_desativacao TEXT NOT NULL,
    tipo_desativacao TEXT NOT NULL,
    competencia TEXT NOT NULL,
    id_area TEXT NOT NULL,
    nome_area TEXT NOT NULL,
    id_segmento TEXT NOT NULL,
    descricao_segmento TEXT NOT NULL,
    tipo_segmento TEXT NOT NULL,
    _loaded_at TIMESTAMPTZ NOT NULL,
    _source_file TEXT NOT NULL,
    _reference_year INTEGER NOT NULL,
    _reference_month INTEGER NOT NULL
);
"""

UPSERT_EQUIPES_APS_SQL = """
INSERT INTO raw_cnes.equipes_aps (
    id_equipe, codigo_cnes, cod_municipio_ibge6, codigo_tipo_equipe, nome_equipe,
    competencia_ativacao, competencia_desativacao, motivo_desativacao,
    tipo_desativacao, competencia, id_area, nome_area, id_segmento,
    descricao_segmento, tipo_segmento, _loaded_at, _source_file,
    _reference_year, _reference_month
) VALUES (
    %(id_equipe)s, %(codigo_cnes)s, %(cod_municipio_ibge6)s, %(codigo_tipo_equipe)s, %(nome_equipe)s,
    %(competencia_ativacao)s, %(competencia_desativacao)s, %(motivo_desativacao)s,
    %(tipo_desativacao)s, %(competencia)s, %(id_area)s, %(nome_area)s, %(id_segmento)s,
    %(descricao_segmento)s, %(tipo_segmento)s, %(_loaded_at)s, %(_source_file)s,
    %(_reference_year)s, %(_reference_month)s
)
ON CONFLICT (id_equipe) DO UPDATE SET
    codigo_cnes = EXCLUDED.codigo_cnes,
    cod_municipio_ibge6 = EXCLUDED.cod_municipio_ibge6,
    codigo_tipo_equipe = EXCLUDED.codigo_tipo_equipe,
    nome_equipe = EXCLUDED.nome_equipe,
    competencia_ativacao = EXCLUDED.competencia_ativacao,
    competencia_desativacao = EXCLUDED.competencia_desativacao,
    motivo_desativacao = EXCLUDED.motivo_desativacao,
    tipo_desativacao = EXCLUDED.tipo_desativacao,
    competencia = EXCLUDED.competencia,
    id_area = EXCLUDED.id_area,
    nome_area = EXCLUDED.nome_area,
    id_segmento = EXCLUDED.id_segmento,
    descricao_segmento = EXCLUDED.descricao_segmento,
    tipo_segmento = EXCLUDED.tipo_segmento,
    _loaded_at = EXCLUDED._loaded_at,
    _source_file = EXCLUDED._source_file,
    _reference_year = EXCLUDED._reference_year,
    _reference_month = EXCLUDED._reference_month;
"""


def ensure_schema_equipes_aps(conn: psycopg.Connection) -> None:
    """Cria o schema raw_cnes e a tabela equipes_aps, se ainda não existirem."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_EQUIPES_APS_SQL)
    conn.commit()


def upsert_equipes_aps(
    conn: psycopg.Connection,
    equipes: list[dict],
    source_file: str,
    ano: int,
    mes: int,
) -> int:
    """Faz upsert em lote das equipes de APS normalizadas, usando id_equipe como chave.

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
        for e in equipes
    ]
    with conn.cursor() as cur:
        cur.executemany(UPSERT_EQUIPES_APS_SQL, rows)
    conn.commit()
    return len(rows)


CREATE_TABLE_ESTABELECIMENTOS_DETALHADOS_SQL = """
CREATE TABLE IF NOT EXISTS raw_cnes.estabelecimentos_detalhados (
    -- Cadastro "vivo" do DEMAS (não tem competência mensal como o "ST" do
    -- FTP) — upsert por codigo_cnes sobrescreve com o estado mais recente
    -- a cada carga, sem histórico. data_atualizacao (da própria API)
    -- indica quando o CNES atualizou o registro pela última vez.
    codigo_cnes TEXT PRIMARY KEY,
    nome_razao_social TEXT,
    nome_fantasia TEXT,
    codigo_tipo_unidade TEXT,
    codigo_cep TEXT,
    endereco TEXT,
    numero_endereco TEXT,
    bairro TEXT,
    numero_telefone TEXT,
    latitude NUMERIC,
    longitude NUMERIC,
    email TEXT,
    descricao_turno_atendimento TEXT,
    faz_atendimento_ambulatorial_sus TEXT,
    -- Já vem decodificada pela própria API DEMAS (ex. "MUNICIPAL"),
    -- diferente do esfera_administrativa cru de raw_cnes.estabelecimentos
    -- (ver docs/COLLECTOR_TEMPLATE.md).
    descricao_esfera_administrativa TEXT,
    codigo_motivo_desabilitacao TEXT,
    possui_centro_cirurgico INTEGER,
    possui_centro_obstetrico INTEGER,
    possui_centro_neonatal INTEGER,
    possui_atendimento_hospitalar INTEGER,
    possui_servico_apoio INTEGER,
    possui_atendimento_ambulatorial INTEGER,
    data_atualizacao TEXT,
    _loaded_at TIMESTAMPTZ NOT NULL,
    _source_url TEXT NOT NULL
);
"""

UPSERT_ESTABELECIMENTOS_DETALHADOS_SQL = """
INSERT INTO raw_cnes.estabelecimentos_detalhados (
    codigo_cnes, nome_razao_social, nome_fantasia, codigo_tipo_unidade,
    codigo_cep, endereco, numero_endereco, bairro, numero_telefone,
    latitude, longitude, email, descricao_turno_atendimento,
    faz_atendimento_ambulatorial_sus, descricao_esfera_administrativa,
    codigo_motivo_desabilitacao, possui_centro_cirurgico,
    possui_centro_obstetrico, possui_centro_neonatal,
    possui_atendimento_hospitalar, possui_servico_apoio,
    possui_atendimento_ambulatorial, data_atualizacao, _loaded_at, _source_url
) VALUES (
    %(codigo_cnes)s, %(nome_razao_social)s, %(nome_fantasia)s, %(codigo_tipo_unidade)s,
    %(codigo_cep)s, %(endereco)s, %(numero_endereco)s, %(bairro)s, %(numero_telefone)s,
    %(latitude)s, %(longitude)s, %(email)s, %(descricao_turno_atendimento)s,
    %(faz_atendimento_ambulatorial_sus)s, %(descricao_esfera_administrativa)s,
    %(codigo_motivo_desabilitacao)s, %(possui_centro_cirurgico)s,
    %(possui_centro_obstetrico)s, %(possui_centro_neonatal)s,
    %(possui_atendimento_hospitalar)s, %(possui_servico_apoio)s,
    %(possui_atendimento_ambulatorial)s, %(data_atualizacao)s, %(_loaded_at)s, %(_source_url)s
)
ON CONFLICT (codigo_cnes) DO UPDATE SET
    nome_razao_social = EXCLUDED.nome_razao_social,
    nome_fantasia = EXCLUDED.nome_fantasia,
    codigo_tipo_unidade = EXCLUDED.codigo_tipo_unidade,
    codigo_cep = EXCLUDED.codigo_cep,
    endereco = EXCLUDED.endereco,
    numero_endereco = EXCLUDED.numero_endereco,
    bairro = EXCLUDED.bairro,
    numero_telefone = EXCLUDED.numero_telefone,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    email = EXCLUDED.email,
    descricao_turno_atendimento = EXCLUDED.descricao_turno_atendimento,
    faz_atendimento_ambulatorial_sus = EXCLUDED.faz_atendimento_ambulatorial_sus,
    descricao_esfera_administrativa = EXCLUDED.descricao_esfera_administrativa,
    codigo_motivo_desabilitacao = EXCLUDED.codigo_motivo_desabilitacao,
    possui_centro_cirurgico = EXCLUDED.possui_centro_cirurgico,
    possui_centro_obstetrico = EXCLUDED.possui_centro_obstetrico,
    possui_centro_neonatal = EXCLUDED.possui_centro_neonatal,
    possui_atendimento_hospitalar = EXCLUDED.possui_atendimento_hospitalar,
    possui_servico_apoio = EXCLUDED.possui_servico_apoio,
    possui_atendimento_ambulatorial = EXCLUDED.possui_atendimento_ambulatorial,
    data_atualizacao = EXCLUDED.data_atualizacao,
    _loaded_at = EXCLUDED._loaded_at,
    _source_url = EXCLUDED._source_url;
"""


def ensure_schema_estabelecimentos_detalhados(conn: psycopg.Connection) -> None:
    """Cria o schema raw_cnes e a tabela estabelecimentos_detalhados, se ainda não existirem."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_ESTABELECIMENTOS_DETALHADOS_SQL)
    conn.commit()


def upsert_estabelecimentos_detalhados(
    conn: psycopg.Connection, estabelecimentos: list[dict], source_url: str
) -> int:
    """Faz upsert em lote dos estabelecimentos detalhados, usando codigo_cnes como chave.

    Retorna a quantidade de registros enviados.
    """
    loaded_at = dt.datetime.now(dt.timezone.utc)
    rows = [
        {**e, "_loaded_at": loaded_at, "_source_url": source_url}
        for e in estabelecimentos
    ]
    with conn.cursor() as cur:
        cur.executemany(UPSERT_ESTABELECIMENTOS_DETALHADOS_SQL, rows)
    conn.commit()
    return len(rows)


CREATE_TABLE_REDE_PORTE_MUNICIPIO_SQL = """
CREATE TABLE IF NOT EXISTS raw_cnes.rede_porte_municipio (
    cod_municipio_ibge6 TEXT NOT NULL,
    competencia TEXT NOT NULL,
    quantidade_estabelecimentos INTEGER NOT NULL,
    _loaded_at TIMESTAMPTZ NOT NULL,
    _source_file TEXT NOT NULL,
    PRIMARY KEY (cod_municipio_ibge6, competencia)
);
"""

DELETE_PARTICAO_REDE_PORTE_MUNICIPIO_SQL = """
DELETE FROM raw_cnes.rede_porte_municipio
WHERE competencia = %(competencia)s;
"""

INSERT_REDE_PORTE_MUNICIPIO_SQL = """
INSERT INTO raw_cnes.rede_porte_municipio (
    cod_municipio_ibge6, competencia, quantidade_estabelecimentos,
    _loaded_at, _source_file
) VALUES (
    %(cod_municipio_ibge6)s, %(competencia)s, %(quantidade_estabelecimentos)s,
    %(_loaded_at)s, %(_source_file)s
);
"""


def ensure_schema_rede_porte_municipio(conn: psycopg.Connection) -> None:
    """Cria o schema raw_cnes e a tabela rede_porte_municipio, se ainda não existirem."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_SQL)
        cur.execute(CREATE_TABLE_REDE_PORTE_MUNICIPIO_SQL)
    conn.commit()


def substituir_rede_porte_municipio(
    conn: psycopg.Connection,
    contagens: list[dict],
    competencia: str,
    source_file: str,
) -> int:
    """Substitui a partição (competência) com as contagens normalizadas.

    delete + insert por competência (não upsert): a "chave natural" real
    aqui é o conjunto de municípios da UF na competência, que não muda
    linha a linha — mais simples reconstruir a partição inteira a cada
    carga do que fazer upsert 1 a 1. Retorna a quantidade de linhas
    inseridas.
    """
    loaded_at = dt.datetime.now(dt.timezone.utc)
    rows = [
        {**c, "_loaded_at": loaded_at, "_source_file": source_file} for c in contagens
    ]
    with conn.cursor() as cur:
        cur.execute(
            DELETE_PARTICAO_REDE_PORTE_MUNICIPIO_SQL, {"competencia": competencia}
        )
        cur.executemany(INSERT_REDE_PORTE_MUNICIPIO_SQL, rows)
    conn.commit()
    return len(rows)
