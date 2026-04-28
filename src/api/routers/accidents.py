"""Endpoints accidents (liste paginée + filtres)."""

from fastapi import APIRouter, Depends, Query

from src.api.deps import db_conn

router = APIRouter()


@router.get("/accidents", summary="Liste paginée d'accidents (filtres optionnels)")
def list_accidents(
    year: int | None = Query(None, ge=2000, le=2100),
    dep: str | None = Query(None, max_length=3),
    fatal_only: bool = False,
    limit: int = Query(100, ge=1, le=10_000),
    offset: int = Query(0, ge=0),
    con=Depends(db_conn),
) -> dict:
    where: list[str] = ["1=1"]
    if year:
        where.append(f"year = {year}")
    if dep:
        where.append(f"dep = '{dep}'")
    if fatal_only:
        where.append("is_fatal = TRUE")
    clause = " AND ".join(where)

    rows = con.execute(
        f"""
        SELECT accident_id, accident_date, hour, lat, lon, dep,
               worst_gravity, nb_tues, weather_category
        FROM marts.fct_accidents
        WHERE {clause}
        ORDER BY accident_date DESC
        LIMIT {limit} OFFSET {offset}
        """
    ).fetchall()

    cols = [
        "accident_id", "accident_date", "hour", "lat", "lon", "dep",
        "worst_gravity", "nb_tues", "weather_category",
    ]
    return {
        "count": len(rows),
        "limit": limit,
        "offset": offset,
        "results": [dict(zip(cols, r, strict=True)) for r in rows],
    }
