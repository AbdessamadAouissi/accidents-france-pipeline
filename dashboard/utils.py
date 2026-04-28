"""Helpers du dashboard : connexion DuckDB, chargements cachés."""

from __future__ import annotations

import duckdb
import pandas as pd
import streamlit as st

from src.utils.config import settings


@st.cache_resource
def get_con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(settings.duckdb_path), read_only=True)


@st.cache_data(ttl=600)
def query(sql: str) -> pd.DataFrame:
    return get_con().execute(sql).df()


@st.cache_data(ttl=600)
def get_global_kpis() -> dict:
    row = get_con().execute(
        """
        SELECT
            COUNT(*)                                AS nb_accidents,
            COALESCE(SUM(nb_tues), 0)               AS nb_tues,
            COALESCE(SUM(nb_blesses_hosp), 0)       AS nb_blesses_hosp,
            COALESCE(SUM(nb_blesses_legers), 0)     AS nb_blesses_legers
        FROM marts.fct_accidents
        """
    ).fetchone()
    return {
        "nb_accidents": row[0],
        "nb_tues": row[1],
        "nb_blesses_hosp": row[2],
        "nb_blesses_legers": row[3],
    }


@st.cache_data(ttl=600)
def get_years() -> list[int]:
    df = query("SELECT DISTINCT year FROM marts.fct_accidents ORDER BY year")
    return df["year"].dropna().astype(int).tolist()


@st.cache_data(ttl=600)
def get_departements() -> list[str]:
    df = query("SELECT DISTINCT dep FROM marts.fct_accidents ORDER BY dep")
    return df["dep"].dropna().tolist()
