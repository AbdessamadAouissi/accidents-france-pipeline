"""Entraîne tous les modèles ML à partir des données du warehouse DuckDB.

Ordre de priorité pour la source de données :
  1. marts.fct_accidents  (table dbt enrichie — preferred)
  2. Jointure manuelle staging.accidents × staging.severity  (fallback si dbt pas encore tourné)

Filtre géographique : France métropolitaine uniquement (exclut DOM-TOM).
"""

from __future__ import annotations

import pandas as pd

from src.load.duckdb_loader import get_connection
from src.ml.hotspots import HotspotConfig, fit_dbscan, summarize_clusters
from src.ml.severity_classifier import train
from src.utils.config import settings
from src.utils.io import save_parquet
from src.utils.logger import get_logger

log = get_logger(__name__)

# Bounding-box France métropolitaine (exclut DOM-TOM)
LAT_MIN, LAT_MAX = 41.0, 51.5
LON_MIN, LON_MAX = -5.5, 10.0


def _load_data() -> pd.DataFrame:
    """Charge fct_accidents depuis le meilleur schéma disponible.

    Ordre d'essai :
      1. marts.fct_accidents        (dbt avec macro generate_schema_name)
      2. main_marts.fct_accidents   (dbt sans macro, comportement par défaut dbt-duckdb)
      3. Jointure staging manuelle  (fallback si dbt n'a pas tourné du tout)
    """
    con = get_connection(read_only=True)
    try:
        candidates = ["marts.fct_accidents", "main_marts.fct_accidents"]
        df: pd.DataFrame | None = None
        for table in candidates:
            try:
                df = con.execute(f"SELECT * FROM {table}").df()
                log.info(f"Source : {table} ({len(df):,} lignes)")
                break
            except Exception:
                continue

        if df is None:
            log.warning("⚠ fct_accidents introuvable — jointure fallback (staging.*)")
            df = con.execute(
                """
                SELECT
                    a.*,
                    s.nb_usagers,
                    s.nb_tues,
                    s.nb_blesses_hosp,
                    s.nb_blesses_legers,
                    s.worst_gravity,
                    s.is_fatal
                FROM staging.accidents a
                LEFT JOIN staging.severity s USING (accident_id)
                """
            ).df()
            log.info(f"Source : staging.accidents × staging.severity ({len(df):,} lignes)")
    finally:
        con.close()
    return df


def _filter_metropole(df: pd.DataFrame) -> pd.DataFrame:
    """Filtre les coordonnées hors France métropolitaine (DOM-TOM, erreurs)."""
    before = len(df)
    mask = (
        df["lat"].between(LAT_MIN, LAT_MAX)
        & df["lon"].between(LON_MIN, LON_MAX)
    )
    out = df[mask].copy()
    excluded = before - len(out)
    if excluded > 0:
        log.info(f"✓ Filtre géo : {excluded:,} points hors métropole exclus ({len(out):,} conservés)")
    return out


def main() -> None:
    log.info("======== ML TRAINING ========")

    df = _load_data()

    # Filtre géographique avant tout traitement ML
    df_metro = _filter_metropole(df)

    # 1. Hotspots (DBSCAN sur France métropolitaine uniquement)
    log.info("--- Hotspots DBSCAN ---")
    clustered = fit_dbscan(df_metro, HotspotConfig(eps_km=0.3, min_samples=10))
    summary = summarize_clusters(clustered)
    save_parquet(summary, settings.processed_dir / "ml" / "hotspots_summary.parquet")

    top5 = summary.head()
    log.info(f"Top 5 hotspots (métropole) :\n{top5.to_string(index=False)}")

    # 2. Classifieur de gravité
    log.info("--- Classifieur gravité ---")
    if "is_fatal" in df.columns and df["is_fatal"].notna().any():
        result = train(df)  # utilise df complet (pas besoin du filtre geo ici)
        log.info(f"Résultat : F1={result.cv_f1_mean:.3f} ± {result.cv_f1_std:.3f} | AUC={result.cv_auc_mean:.3f}")
    else:
        log.warning("⚠ Colonne is_fatal manquante ou vide — classifieur ignoré.")
        log.info("  → Relancer après dbt : cd dbt_project && dbt run --profiles-dir .")

    log.info("✓ ML terminé.")


if __name__ == "__main__":
    main()
