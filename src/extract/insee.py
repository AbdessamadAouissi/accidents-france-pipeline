"""Extraction des données INSEE : population par département.

Source : https://www.insee.fr/fr/statistiques/2012713 (estimations population)
On utilise un dataset stable hébergé sur data.gouv.fr pour la reproductibilité.
"""

from __future__ import annotations

from pathlib import Path

import requests

from src.utils.config import settings
from src.utils.io import read_csv_robust, save_parquet
from src.utils.logger import get_logger

log = get_logger(__name__)

# Population légale 2021 par département (données officielles INSEE)
# Source utilisée : https://www.data.gouv.fr/fr/datasets/population/
INSEE_POPULATION_URL = (
    "https://www.data.gouv.fr/fr/datasets/r/dbe8a621-a9c4-4bc3-9cae-be1699c5ff25"
)


def download_population(dest: Path | None = None) -> Path:
    dest = dest or (settings.raw_dir / "insee" / "population.csv")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        log.info(f"↩ Cache hit : {dest.name}")
        return dest
    log.info(f"⬇ INSEE population : {INSEE_POPULATION_URL}")
    r = requests.get(INSEE_POPULATION_URL, timeout=60)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def run() -> Path:
    log.info("== Extraction INSEE ==")
    raw = download_population()
    df = read_csv_robust(raw, sep=",")
    dest = settings.processed_dir / "insee" / "population.parquet"
    save_parquet(df, dest)
    return dest


if __name__ == "__main__":
    run()
