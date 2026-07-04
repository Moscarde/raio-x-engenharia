"""Conexão com o PostgreSQL local a partir de variáveis de ambiente."""

from __future__ import annotations

import os

import psycopg

REQUIRED_ENV_VARS = (
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
)


def get_connection() -> psycopg.Connection:
    """Abre conexão com o Postgres usando POSTGRES_* do ambiente.

    Ver .env.example para os valores esperados em desenvolvimento local.
    """
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            f"Variáveis de ambiente ausentes: {missing}; "
            "defina-as no .env local (copie a partir de .env.example)."
        )
    return psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
