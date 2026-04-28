"""Page KPIs avec filtres."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from dashboard.utils import get_departements, get_years, query  # noqa: E402

st.set_page_config(page_title="KPIs", page_icon="📊", layout="wide")
st.title("📊 KPIs filtrables")

# === Sidebar : filtres ===
with st.sidebar:
    st.header("Filtres")
    years = get_years()
    deps = get_departements()
    sel_years = st.multiselect("Années", years, default=years)
    sel_deps = st.multiselect("Départements", deps, default=[])

# === Construction WHERE ===
where = ["1=1"]
if sel_years:
    where.append(f"year IN ({','.join(map(str, sel_years))})")
if sel_deps:
    deps_sql = ",".join(f"'{d}'" for d in sel_deps)
    where.append(f"dep IN ({deps_sql})")
clause = " AND ".join(where)

# === KPIs ===
row = query(
    f"""
    SELECT
        COUNT(*)                            AS nb_accidents,
        COALESCE(SUM(nb_tues), 0)           AS nb_tues,
        COALESCE(SUM(nb_blesses_hosp), 0)   AS nb_blesses_hosp,
        COALESCE(SUM(nb_blesses_legers), 0) AS nb_blesses_legers,
        ROUND(100.0 * SUM(CASE WHEN is_fatal THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2)
                                            AS taux_mortalite_pct
    FROM marts.fct_accidents WHERE {clause}
    """
).iloc[0]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Accidents", f"{int(row.nb_accidents):,}".replace(",", " "))
c2.metric("Tués", f"{int(row.nb_tues):,}".replace(",", " "))
c3.metric("Blessés hosp.", f"{int(row.nb_blesses_hosp):,}".replace(",", " "))
c4.metric("Blessés légers", f"{int(row.nb_blesses_legers):,}".replace(",", " "))
c5.metric("Taux mortalité (%)", f"{row.taux_mortalite_pct or 0:.2f}")

st.divider()

# === Évolution annuelle ===
df_year = query(
    f"""
    SELECT year, COUNT(*) AS nb_accidents,
           SUM(nb_tues) AS nb_tues,
           SUM(CASE WHEN is_fatal THEN 1 ELSE 0 END) AS nb_mortels
    FROM marts.fct_accidents WHERE {clause}
    GROUP BY year ORDER BY year
    """
)
if not df_year.empty:
    fig = px.line(
        df_year,
        x="year",
        y=["nb_accidents", "nb_mortels", "nb_tues"],
        markers=True,
        title="Évolution annuelle",
        labels={"value": "Nombre", "year": "Année", "variable": "Indicateur"},
    )
    st.plotly_chart(fig, use_container_width=True)

# === Top départements ===
df_dep = query(
    f"""
    SELECT dep, COUNT(*) AS nb_accidents, SUM(nb_tues) AS nb_tues
    FROM marts.fct_accidents WHERE {clause}
    GROUP BY dep ORDER BY nb_accidents DESC LIMIT 20
    """
)
if not df_dep.empty:
    fig2 = px.bar(
        df_dep,
        x="dep",
        y="nb_accidents",
        color="nb_tues",
        color_continuous_scale="Reds",
        title="Top 20 départements (accidents)",
    )
    st.plotly_chart(fig2, use_container_width=True)
