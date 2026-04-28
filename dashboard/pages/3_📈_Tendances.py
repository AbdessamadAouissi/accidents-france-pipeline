"""Tendances temporelles et météo."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from dashboard.utils import query  # noqa: E402

st.set_page_config(page_title="Tendances", page_icon="📈", layout="wide")
st.title("📈 Tendances & saisonnalité")

# === Heatmap heure × jour ===
st.subheader("Heatmap accidents — heure × jour de semaine")
df_heat = query(
    """
    SELECT day_of_week, hour, COUNT(*) AS n
    FROM marts.fct_accidents
    WHERE hour IS NOT NULL
    GROUP BY day_of_week, hour
    ORDER BY day_of_week, hour
    """
)
if not df_heat.empty:
    days = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    df_heat["jour"] = df_heat["day_of_week"].map(lambda i: days[(int(i) - 1) % 7])
    pivot = df_heat.pivot(index="jour", columns="hour", values="n").reindex(days)
    fig = px.imshow(
        pivot,
        labels=dict(x="Heure", y="Jour", color="Accidents"),
        color_continuous_scale="YlOrRd",
        aspect="auto",
    )
    st.plotly_chart(fig, use_container_width=True)

# === Saisonnalité mensuelle ===
st.subheader("Saisonnalité mensuelle")
df_month = query(
    """
    SELECT year, month, COUNT(*) AS nb_accidents,
           SUM(nb_tues) AS nb_tues
    FROM marts.fct_accidents
    GROUP BY year, month ORDER BY year, month
    """
)
if not df_month.empty:
    fig2 = px.line(
        df_month,
        x="month",
        y="nb_accidents",
        color="year",
        markers=True,
        title="Accidents par mois",
    )
    st.plotly_chart(fig2, use_container_width=True)

# === Météo vs gravité ===
st.subheader("Météo & gravité")
df_meteo = query(
    """
    SELECT weather_category,
           COUNT(*)                                  AS nb_accidents,
           SUM(CASE WHEN is_fatal THEN 1 ELSE 0 END) AS nb_mortels,
           ROUND(100.0 * SUM(CASE WHEN is_fatal THEN 1 ELSE 0 END) / COUNT(*), 2) AS taux_mortalite
    FROM marts.fct_accidents
    WHERE weather_category IS NOT NULL
    GROUP BY weather_category ORDER BY nb_accidents DESC
    """
)
if not df_meteo.empty:
    c1, c2 = st.columns(2)
    c1.plotly_chart(
        px.bar(df_meteo, x="weather_category", y="nb_accidents", title="Volume"),
        use_container_width=True,
    )
    c2.plotly_chart(
        px.bar(
            df_meteo,
            x="weather_category",
            y="taux_mortalite",
            color="taux_mortalite",
            color_continuous_scale="Reds",
            title="Taux de mortalité (%)",
        ),
        use_container_width=True,
    )
