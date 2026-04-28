"""Page d'accueil du dashboard Streamlit."""

import sys
from pathlib import Path

# Streamlit ajoute le dossier du script (dashboard/) à sys.path mais pas la racine projet.
# On l'injecte pour que `from dashboard.utils import ...` et `from src.* import ...` résolvent.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402

from dashboard.utils import get_global_kpis  # noqa: E402

st.set_page_config(
    page_title="Accidents France — Dashboard",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🚦 Accidents de la route en France")
st.caption("Pipeline data end-to-end — ONISR × Météo × INSEE × ML")

st.markdown(
    """
Ce dashboard exploite un pipeline data complet :
**Extraction (Python) → Validation (Great Expectations) → Warehouse (DuckDB)
→ Transformations (dbt) → ML (sklearn) → API (FastAPI) → Visualisation (Streamlit)**.

**Navigation** (menu latéral) :
- 📊 **KPIs** — chiffres clés filtrables
- 🗺️ **Carte** — heatmap géographique des accidents
- 📈 **Tendances** — saisonnalité & patterns temporels
- 🎯 **Hotspots** — zones à risque (DBSCAN)
- 🤖 **Prédiction** — gravité estimée d'un accident
"""
)

st.divider()

# KPIs résumé
try:
    k = get_global_kpis()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Accidents", f"{k['nb_accidents']:,}".replace(",", " "))
    c2.metric("Tués", f"{k['nb_tues']:,}".replace(",", " "))
    c3.metric("Blessés hosp.", f"{k['nb_blesses_hosp']:,}".replace(",", " "))
    c4.metric("Blessés légers", f"{k['nb_blesses_legers']:,}".replace(",", " "))
except Exception as e:
    st.warning(
        f"⚠ Données indisponibles : {e}\n\n"
        "Lancer le pipeline : `make pipeline` puis `make dbt-run`."
    )

st.divider()
with st.expander("🛠 Stack technique", expanded=False):
    st.markdown(
        """
| Couche | Outil |
|---|---|
| ETL | Python, pandas, requests, httpx |
| Géospatial | GeoPandas, Shapely, Folium, H3 |
| Warehouse | DuckDB |
| Transformations | dbt-duckdb |
| Qualité | Great Expectations, pytest |
| ML | scikit-learn (DBSCAN + RandomForest) |
| Orchestration | Apache Airflow |
| API | FastAPI + Pydantic |
| Dashboard | Streamlit + Plotly + Folium |
| DevOps | Docker, GitHub Actions, pre-commit |
"""
    )
