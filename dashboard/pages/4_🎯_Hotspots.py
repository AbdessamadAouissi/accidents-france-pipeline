"""Hotspots — top zones à risque (DBSCAN)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import folium  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from streamlit_folium import st_folium  # noqa: E402

from src.utils.config import settings  # noqa: E402

st.set_page_config(page_title="Hotspots", page_icon="🎯", layout="wide")
st.title("🎯 Hotspots — zones à risque (DBSCAN)")

path: Path = settings.processed_dir / "ml" / "hotspots_summary.parquet"
if not path.exists():
    st.error(
        "Aucun hotspot calculé. Lancer : `python -m src.ml.train_all`."
    )
    st.stop()

df = pd.read_parquet(path)

with st.sidebar:
    min_size = st.slider("Taille min du cluster", 5, 200, 10)
    top = st.slider("Nombre de hotspots", 5, 200, 30)

df_f = df[df["size"] >= min_size].head(top)
st.metric("Hotspots affichés", len(df_f))
st.dataframe(df_f, use_container_width=True)

# Carte
if not df_f.empty:
    m = folium.Map(
        location=[df_f["centroid_lat"].mean(), df_f["centroid_lon"].mean()],
        zoom_start=6,
        tiles="cartodbpositron",
    )
    for _, r in df_f.iterrows():
        folium.CircleMarker(
            location=[r["centroid_lat"], r["centroid_lon"]],
            radius=min(20, max(5, r["size"] / 5)),
            color="crimson",
            fill=True,
            fill_opacity=0.6,
            popup=(
                f"<b>Cluster #{int(r['cluster'])}</b><br>"
                f"Accidents : {int(r['size'])}<br>"
                f"Taux mortalité : {r.get('fatality_rate', 'N/A')}"
            ),
        ).add_to(m)
    st_folium(m, width=None, height=600, returned_objects=[])
