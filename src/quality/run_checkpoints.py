"""Exécute les suites de validation sur les tables clés du warehouse."""

from __future__ import annotations

import sys

import pandas as pd

from src.load.duckdb_loader import get_connection
from src.quality.expectations import run_suite_accidents, summarize
from src.utils.logger import get_logger

log = get_logger(__name__)


def main() -> int:
    log.info("======== DATA QUALITY ========")
    con = get_connection(read_only=True)
    try:
        df: pd.DataFrame = con.execute("SELECT * FROM staging.accidents").df()
    finally:
        con.close()

    checks = run_suite_accidents(df)
    summary = summarize(checks)
    log.info(f"Résumé : {summary}")

    # Exit non-zero si > 20% d'échecs (configurable)
    if summary["pass_rate"] < 0.8:
        log.error("✗ Trop d'échecs — failing the pipeline.")
        return 1
    log.info("✓ Validation OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
