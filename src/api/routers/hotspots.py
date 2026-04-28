"""Endpoint hotspots (clusters DBSCAN)."""

from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.utils.config import settings

router = APIRouter()

_HOTSPOTS_PATH: Path = settings.processed_dir / "ml" / "hotspots_summary.parquet"


@router.get("/hotspots", summary="Top zones à risque (clusters DBSCAN)")
def get_hotspots(
    top: int = Query(50, ge=1, le=1000),
    min_size: int = Query(10, ge=1),
) -> dict:
    if not _HOTSPOTS_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Aucun hotspot calculé — exécuter `python -m src.ml.train_all`.",
        )
    df: pd.DataFrame = pd.read_parquet(_HOTSPOTS_PATH)
    df = df[df["size"] >= min_size].head(top)
    return {
        "count": len(df),
        "results": df.to_dict(orient="records"),
    }
