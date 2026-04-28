"""Opérations géospatiales : conversion en GeoDataFrame, jointures spatiales, H3."""

from __future__ import annotations

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from src.utils.logger import get_logger

log = get_logger(__name__)


def to_geodataframe(df: pd.DataFrame, lat_col: str = "lat", lon_col: str = "lon") -> gpd.GeoDataFrame:
    """Convertit un DataFrame en GeoDataFrame WGS84 (EPSG:4326)."""
    df = df.dropna(subset=[lat_col, lon_col]).copy()
    # Borner à la France métropolitaine (filtrage défensif)
    df = df[
        df[lat_col].between(41.0, 51.5) & df[lon_col].between(-5.5, 10.0)
    ]
    geom = [Point(xy) for xy in zip(df[lon_col], df[lat_col], strict=True)]
    gdf = gpd.GeoDataFrame(df, geometry=geom, crs="EPSG:4326")
    log.info(f"✓ GeoDataFrame : {len(gdf):,} points valides")
    return gdf


def add_h3_index(df: pd.DataFrame, resolution: int = 8) -> pd.DataFrame:
    """Ajoute un index H3 (hexagones uber) — utile pour binning spatial."""
    import h3

    df = df.copy()
    df["h3"] = df.apply(
        lambda r: h3.geo_to_h3(r["lat"], r["lon"], resolution)
        if pd.notna(r["lat"]) and pd.notna(r["lon"])
        else None,
        axis=1,
    )
    return df
