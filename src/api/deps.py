"""Dépendances FastAPI partagées (connexion DuckDB read-only)."""

from collections.abc import Generator

import duckdb

from src.load.duckdb_loader import get_connection


def db_conn() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    con = get_connection(read_only=True)
    try:
        yield con
    finally:
        con.close()
