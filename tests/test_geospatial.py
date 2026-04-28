"""Tests du module géospatial."""

import pandas as pd
import pytest

from src.transform.geospatial import to_geodataframe


@pytest.mark.unit
def test_to_gdf_filters_invalid_coords():
    df = pd.DataFrame(
        {
            "lat": [48.85, 90.0, None, 43.30],   # 90 hors France, None invalide
            "lon": [2.35, 50.0, 1.0, 5.37],
            "id": [1, 2, 3, 4],
        }
    )
    gdf = to_geodataframe(df)
    assert len(gdf) == 2
    assert gdf.crs.to_epsg() == 4326


@pytest.mark.unit
def test_to_gdf_keeps_attributes():
    df = pd.DataFrame({"lat": [48.85], "lon": [2.35], "label": ["A"]})
    gdf = to_geodataframe(df)
    assert gdf["label"].iloc[0] == "A"
