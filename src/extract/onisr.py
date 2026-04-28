"""Extraction des données BAAC / ONISR (accidents corporels de la circulation).

Source : https://www.data.gouv.fr/fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2023/

Quatre fichiers par année :
  - caract    : caractéristiques de l'accident (date, lieu, conditions)
  - lieux     : description du lieu (route, type d'intersection)
  - vehicules : véhicules impliqués (BAAC — hors fichier immatriculation)
  - usagers   : personnes impliquées (gravité, équipement)

Stratégie : découverte dynamique via l'API data.gouv.fr, en parsant le nom
de fichier dans l'URL (plus stable que le titre qui varie selon les millésimes).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import requests

from src.utils.config import settings
from src.utils.io import read_csv_robust, save_parquet
from src.utils.logger import get_logger

log = get_logger(__name__)

DATASET_SLUG = (
    "bases-de-donnees-annuelles-des-accidents-corporels-de-la-"
    "circulation-routiere-annees-de-2005-a-2023"
)
DATASET_API = f"https://www.data.gouv.fr/api/1/datasets/{DATASET_SLUG}/"

# Patterns sur le BASENAME de l'URL (côté serveur, toujours cohérent).
# Ordre : le premier match gagne → "carcteristiques" avant "caract" pour éviter
# que "caract" ne matche pas "carcteristiques" (les deux commencent par "caract").
_URL_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("caract",    re.compile(r"(?:caract(?:eristiques?)?|carcteristiques?)"
                             r"[-_](\d{4})\.csv$", re.I)),
    ("lieux",     re.compile(r"lieux[-_](\d{4})\.csv$", re.I)),
    ("vehicules", re.compile(r"vehicules[-_](\d{4})\.csv$", re.I)),
    ("usagers",   re.compile(r"usagers[-_](\d{4})\.csv$", re.I)),
]

# On exclut explicitement les fichiers d'immatriculation BAAC (pas des données d'accident)
_EXCLUDE = re.compile(r"immatricul", re.I)


@dataclass(frozen=True)
class OnisrFile:
    year: int
    table: str
    path: Path


def _fetch_resources() -> list[dict]:
    """Récupère la liste des ressources du dataset via l'API data.gouv.fr."""
    log.info(f"API data.gouv.fr : {DATASET_API}")
    r = requests.get(DATASET_API, timeout=30)
    r.raise_for_status()
    resources: list[dict] = r.json().get("resources", [])
    log.info(f"✓ {len(resources)} ressources trouvées")
    return resources


def _build_catalogue(resources: list[dict]) -> dict[int, dict[str, str]]:
    """Construit {année: {table: url}} en parsant le basename de l'URL."""
    catalogue: dict[int, dict[str, str]] = {}
    for res in resources:
        url: str = res.get("url", "") or ""
        if not url or not url.endswith(".csv"):
            continue

        basename = url.split("/")[-1]

        # Exclure les fichiers d'immatriculation
        if _EXCLUDE.search(basename) or _EXCLUDE.search(res.get("title", "")):
            continue

        for table, pat in _URL_PATTERNS:
            m = pat.search(basename)
            if m:
                year = int(m.group(1))
                catalogue.setdefault(year, {})[table] = url
                log.debug(f"  → {table} {year} : {basename}")
                break

    found = sorted(catalogue.keys())
    log.info(f"Années dans le catalogue : {found}")
    for y in found:
        tables = sorted(catalogue[y].keys())
        log.info(f"  {y} : {tables}")
    return catalogue


def _download(url: str, dest: Path) -> Path:
    """Télécharge un fichier CSV en streaming avec cache local."""
    if dest.exists():
        log.info(f"↩ Cache hit : {dest.name}")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    log.info(f"⬇ {dest.name}")
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
    mb = dest.stat().st_size / 1_048_576
    log.info(f"✓ Téléchargé : {dest.name} ({mb:.1f} Mo)")
    return dest


def download_year(year: int, catalogue: dict[int, dict[str, str]]) -> list[OnisrFile]:
    """Télécharge les CSV BAAC d'une année et retourne la liste des fichiers locaux."""
    if year not in catalogue:
        raise ValueError(
            f"Année {year} absente du catalogue. "
            f"Disponibles : {sorted(catalogue.keys())}"
        )
    tables = catalogue[year]
    missing = {"caract", "lieux", "vehicules", "usagers"} - set(tables)
    if missing:
        log.warning(f"⚠ Tables manquantes pour {year} : {missing}")

    out: list[OnisrFile] = []
    for table, url in tables.items():
        dest = settings.raw_dir / "onisr" / str(year) / f"{table}-{year}.csv"
        path = _download(url, dest)
        out.append(OnisrFile(year=year, table=table, path=path))
    return out


def to_parquet(files: list[OnisrFile]) -> list[Path]:
    """Convertit les CSV bruts en Parquet (lecture ~10× plus rapide ensuite)."""
    out: list[Path] = []
    for f in files:
        df = read_csv_robust(f.path, sep=";")
        df["source_year"] = f.year
        dest = settings.processed_dir / "onisr" / f"{f.table}_{f.year}.parquet"
        save_parquet(df, dest)
        out.append(dest)
    return out


def run(years: list[int] | None = None) -> dict[int, list[Path]]:
    """Pipeline ONISR : découverte → téléchargement → Parquet."""
    years = years or settings.years
    log.info(f"== Extraction ONISR : années {years} ==")

    resources = _fetch_resources()
    catalogue = _build_catalogue(resources)

    results: dict[int, list[Path]] = {}
    for y in years:
        if y not in catalogue:
            log.warning(f"⚠ Année {y} introuvable — ignorée.")
            continue
        files = download_year(y, catalogue)
        results[y] = to_parquet(files)

    log.info("✓ Extraction ONISR terminée.")
    return results


if __name__ == "__main__":
    run()
