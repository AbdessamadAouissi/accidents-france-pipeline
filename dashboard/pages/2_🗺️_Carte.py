"""Carte interactive (heatmap Folium)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import folium  # noqa: E402
import streamlit as st  # noqa: E402
from folium.plugins import HeatMap, MarkerCluster  # noqa: E402
from streamlit_folium import st_folium  # noqa: E402

from dashboard.utils import get_departements, get_years, query  # noqa: E402

st.set_page_config(page_title="Carte", page_icon="🗺️", layout="wide")
st.title("🗺️ Carte interactive des accidents")

with st.sidebar:
    st.header("Filtres")
    sel_year = st.selectbox("Année", get_years(), index=len(get_years()) - 1)
    sel_dep = st.selectbox("Département", ["(tous)", *get_departements()])
    fatal_only = st.checkbox("Accidents mortels uniquement", value=False)
    sample = st.slider("Échantillon (max points)", 500, 20_000, 5_000, step=500)
    layer = st.radio("Affichage", ["Heatmap", "Clusters"], horizontal=True)

# === Filtres SQL ===
where = [f"year = {sel_year}", "lat IS NOT NULL", "lon IS NOT NULL"]
if sel_dep != "(tous)":
    where.append(f"dep = '{sel_dep}'")
if fatal_only:
    where.append("is_fatal = TRUE")
clause = " AND ".join(where)

df = query(
    f"""
    SELECT lat, lon, accident_id, accident_date, worst_gravity, nb_tues
    FROM marts.fct_accidents
    WHERE {clause}
    USING SAMPLE {sample}
    """
)

st.caption(f"{len(df):,} accidents affichés")

if df.empty:
    st.warning("Aucun accident avec ces filtres.")
else:
    centre = [df["lat"].mean(), df["lon"].mean()]
    m = folium.Map(location=centre, zoom_start=6, tiles="cartodbpositron")

    if layer == "Heatmap":
        HeatMap(df[["lat", "lon"]].values.tolist(), radius=10, blur=15).add_to(m)
    else:
        cluster = MarkerCluster().add_to(m)
        for _, r in df.iterrows():
            folium.CircleMarker(
                location=[r["lat"], r["lon"]],
                radius=4,
                color="red" if r.get("nb_tues", 0) > 0 else "blue",
                fill=True,
                fill_opacity=0.6,
                popup=f"{r['accident_date']} — gravité : {r['worst_gravity']}",
            ).add_to(cluster)

    st_folium(m, width=None, height=650, returned_objects=[])
