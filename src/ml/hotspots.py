"""Détection de hotspots d'accidents par clustering DBSCAN.

DBSCAN est adapté car :
  - Pas besoin de spécifier le nombre de clusters a priori.
  - Détecte des clusters de forme arbitraire (utile pour des routes/intersections).
  - Identifie automatiquement le bruit (accidents isolés).

On utilise la métrique haversine (en radians) pour respecter la sphéricité terrestre.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

from src.utils.logger import get_logger

log = get_logger(__name__)

EARTH_RADIUS_KM = 6371.0088


@dataclass
class HotspotConfig:
    eps_km: float = 0.3        # rayon en km
    min_samples: int = 10      # nombre minimal d'accidents par cluster

    @property
    def eps_radians(self) -> float:
        return self.eps_km / EARTH_RADIUS_KM


def fit_dbscan(df: pd.DataFrame, cfg: HotspotConfig | None = None) -> pd.DataFrame:
    """Ajoute une colonne 'cluster' (-1 = bruit) au DataFrame."""
    cfg = cfg or HotspotConfig()
    coords = np.radians(df[["lat", "lon"]].dropna().values)
    log.info(f"DBSCAN sur {len(coords):,} points (eps={cfg.eps_km} km, min={cfg.min_samples})")

    model = DBSCAN(
        eps=cfg.eps_radians,
        min_samples=cfg.min_samples,
        metric="haversine",
        algorithm="ball_tree",
        n_jobs=-1,
    )
    labels = model.fit_predict(coords)

    out = df.dropna(subset=["lat", "lon"]).copy()
    out["cluster"] = labels
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    log.info(f"✓ {n_clusters} clusters trouvés ({n_noise:,} points bruit)")
    return out


def summarize_clusters(df_clustered: pd.DataFrame) -> pd.DataFrame:
    """Résume chaque cluster (centroïde, taille, gravité moyenne)."""
    valid = df_clustered[df_clustered["cluster"] != -1]
    agg_dict = {
        "lat": "mean",
        "lon": "mean",
        "accident_id": "count",
    }
    if "is_fatal" in valid.columns:
        agg_dict["is_fatal"] = "sum"
    summary = valid.groupby("cluster").agg(agg_dict).rename(
        columns={"accident_id": "size", "lat": "centroid_lat", "lon": "centroid_lon"}
    )
    if "is_fatal" in summary.columns:
        summary["fatality_rate"] = (summary["is_fatal"] / summary["size"]).round(3)
    return summary.sort_values("size", ascending=False).reset_index()
