"""Charge les Parquet processed/ dans DuckDB (warehouse local).

DuckDB est un OLAP in-process — pas de serveur, scan Parquet hyper-rapide.
"""

from __future__ import annotations

import duckdb

from src.utils.config import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


# Mapping table DuckDB -> chemin Parquet (peut être un glob)
TABLES: dict[str, str] = {
    "raw_caract": "onisr/caract_*.parquet",
    "raw_lieux": "onisr/lieux_*.parquet",
    "raw_vehicules": "onisr/vehicules_*.parquet",
    "raw_usagers": "onisr/usagers_*.parquet",
    "stg_accidents": "accidents_caract.parquet",
    "stg_usagers": "accidents_usagers.parquet",
    "stg_severity": "accidents_severity.parquet",
    "fct_accidents": "accidents_final.parquet",
    "stg_meteo": "meteo/meteo_daily.parquet",
    "stg_population": "insee/population.parquet",
}


def get_connection(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Ouvre une connexion DuckDB sur le warehouse."""
    settings.warehouse_dir.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(settings.duckdb_path), read_only=read_only)


def load_all() -> None:
    """Crée/remplace les tables raw + stg dans DuckDB depuis les Parquet."""
    con = get_connection()
    con.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    con.execute("CREATE SCHEMA IF NOT EXISTS staging;")
    con.execute("CREATE SCHEMA IF NOT EXISTS marts;")

    for table, glob in TABLES.items():
        path = settings.processed_dir / glob
        # Le pattern peut contenir un wildcard
        pattern = str(path).replace("\\", "/")
        schema = "raw" if table.startswith("raw_") else "staging"
        full_name = f"{schema}.{table.removeprefix('raw_').removeprefix('stg_')}"
        try:
            con.execute(
                f"CREATE OR REPLACE TABLE {full_name} AS "
                f"SELECT * FROM read_parquet('{pattern}', union_by_name=true)"
            )
            n = con.execute(f"SELECT COUNT(*) FROM {full_name}").fetchone()[0]
            log.info(f"✓ {full_name} : {n:,} lignes")
        except duckdb.Error as e:
            log.warning(f"⚠ Skip {table} ({pattern}) : {e}")

    # Crée des vues aliases "marts.*" sur les tables dbt (qui peuvent être en main_marts.*)
    # pour que l'API et le dashboard fonctionnent quel que soit l'état de dbt.
    con.execute("CREATE SCHEMA IF NOT EXISTS marts;")
    dbt_aliases = {
        # staging.fct_accidents (Python loader) en priorité : toujours fresh.
        # main_marts.fct_accidents (dbt) utilisé seulement si staging absent.
        "marts.fct_accidents": ["staging.fct_accidents", "main_marts.fct_accidents"],
        "marts.agg_accidents_by_dep": ["main_marts.agg_accidents_by_dep"],
        "marts.agg_temporal_patterns": ["main_marts.agg_temporal_patterns"],
    }
    for view_name, sources in dbt_aliases.items():
        for src in sources:
            try:
                con.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM {src}")
                log.info(f"✓ Vue alias : {view_name} → {src}")
                break
            except duckdb.Error:
                continue

    con.close()
    log.info(f"✓ DuckDB warehouse prêt : {settings.duckdb_path}")


if __name__ == "__main__":
    load_all()
