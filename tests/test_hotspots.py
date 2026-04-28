"""Tests du clustering DBSCAN."""

import numpy as np
import pandas as pd
import pytest

from src.ml.hotspots import HotspotConfig, fit_dbscan, summarize_clusters


@pytest.mark.unit
def test_dbscan_finds_clusters():
    rng = np.random.default_rng(42)
    # 2 clusters denses + bruit
    cluster1 = rng.normal(loc=(48.85, 2.35), scale=0.001, size=(30, 2))
    cluster2 = rng.normal(loc=(43.30, 5.37), scale=0.001, size=(30, 2))
    noise = rng.uniform(low=(42, -1), high=(50, 8), size=(20, 2))
    pts = np.vstack([cluster1, cluster2, noise])

    df = pd.DataFrame(pts, columns=["lat", "lon"])
    df["accident_id"] = range(len(df))

    out = fit_dbscan(df, HotspotConfig(eps_km=0.5, min_samples=10))
    n_clusters = len(set(out["cluster"]) - {-1})
    assert n_clusters >= 2


@pytest.mark.unit
def test_summarize_clusters_returns_dataframe():
    df = pd.DataFrame(
        {
            "lat": [48.85, 48.85, 43.30, 43.30],
            "lon": [2.35, 2.35, 5.37, 5.37],
            "cluster": [0, 0, 1, 1],
            "accident_id": [1, 2, 3, 4],
        }
    )
    s = summarize_clusters(df)
    assert len(s) == 2
    assert "centroid_lat" in s.columns
    assert "size" in s.columns
