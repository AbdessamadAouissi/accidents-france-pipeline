"""Pipeline de transformation : lit les Parquet bruts, nettoie, écrit en processed/."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.transform.cleaning import (
    aggregate_severity,
    clean_caracteristiques,
    clean_usagers,
)
from src.utils.config import settings
from src.utils.io import save_parquet
from src.utils.logger import get_logger

log = get_logger(__name__)


def _read_concat(table: str) -> pd.DataFrame:
    """Concatène les Parquet d'une même table sur toutes les années."""
    files = sorted((settings.processed_dir / "onisr").glob(f"{table}_*.parquet"))
    if not files:
        raise FileNotFoundError(f"Aucun fichier {table}_*.parquet — lancer extract d'abord.")
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def main() -> None:
    log.info("======== TRANSFORM ========")

    # 1. Caractéristiques
    caract = _read_concat("caract")
    caract_clean = clean_caracteristiques(caract)
    save_parquet(caract_clean, settings.processed_dir / "accidents_caract.parquet")

    # 2. Usagers + agrégation gravité
    usagers = _read_concat("usagers")
    usagers_clean = clean_usagers(usagers)
    save_parquet(usagers_clean, settings.processed_dir / "accidents_usagers.parquet")

    severity = aggregate_severity(usagers_clean)
    save_parquet(severity, settings.processed_dir / "accidents_severity.parquet")

    # 3. Jointure finale
    final = caract_clean.merge(severity, on="accident_id", how="left")
    save_parquet(final, settings.processed_dir / "accidents_final.parquet")

    log.info("✓ TRANSFORM terminé.")


if __name__ == "__main__":
    main()
