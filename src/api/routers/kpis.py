"""Endpoints KPIs."""

from fastapi import APIRouter, Depends, Query

from src.api.deps import db_conn

router = APIRouter()


@router.get("/kpis", summary="KPIs globaux")
def get_kpis(
    year: int | None = Query(None, ge=2000, le=2100),
    dep: str | None = Query(None, max_length=3),
    con=Depends(db_conn),
) -> dict:
    where: list[str] = []
    if year:
        where.append(f"year = {year}")
    if dep:
        where.append(f"dep = '{dep}'")
    clause = "WHERE " + " AND ".join(where) if where else ""

    row = con.execute(
        f"""
        SELECT
            COUNT(*)                                AS nb_accidents,
            COALESCE(SUM(nb_tues), 0)               AS nb_tues,
            COALESCE(SUM(nb_blesses_hosp), 0)       AS nb_blesses_hosp,
            COALESCE(SUM(nb_blesses_legers), 0)     AS nb_blesses_legers,
            COALESCE(SUM(CASE WHEN is_fatal THEN 1 ELSE 0 END), 0) AS nb_mortels
        FROM marts.fct_accidents
        {clause}
        """
    ).fetchone()

    return {
        "nb_accidents": row[0],
        "nb_tues": row[1],
        "nb_blesses_hosp": row[2],
        "nb_blesses_legers": row[3],
        "nb_accidents_mortels": row[4],
        "filters": {"year": year, "dep": dep},
    }
