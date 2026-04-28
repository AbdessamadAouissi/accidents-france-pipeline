"""Prédiction interactive de gravité d'un accident."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st  # noqa: E402

from src.ml.severity_classifier import load_model, predict_proba  # noqa: E402

st.set_page_config(page_title="Prédiction", page_icon="🤖", layout="centered")
st.title("🤖 Prédiction de gravité")
st.caption("Modèle RandomForest entraîné sur les accidents 2021-2023 (cible : décès).")

try:
    model = load_model()
except FileNotFoundError as e:
    st.error(f"⚠ {e}")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    hour = st.slider("Heure", 0, 23, 18)
    month = st.slider("Mois", 1, 12, 6)
    dow = st.slider("Jour de semaine (0=lundi)", 0, 6, 4)
    light = st.selectbox(
        "Luminosité",
        ["plein_jour", "crepuscule_aube", "nuit_sans_eclairage", "nuit_eclairage_allume"],
    )
with col2:
    weather = st.selectbox(
        "Météo",
        ["normale", "pluie_legere", "pluie_forte", "neige_grele", "brouillard_fumee", "vent_fort_tempete"],
    )
    weather_cat = st.selectbox("Catégorie météo", ["normal", "pluvieux", "neigeux", "venteux"])
    time_of_day = st.selectbox("Période", ["matin", "midi", "apres_midi", "soiree", "nuit"])
    temp = st.number_input("Température max (°C)", value=15.0)
    rain = st.number_input("Précipitations (mm)", value=0.0, min_value=0.0)
    wind = st.number_input("Vent max (km/h)", value=20.0, min_value=0.0)

if st.button("🔮 Prédire", type="primary"):
    payload = {
        "hour": hour, "month": month, "day_of_week": dow,
        "light_condition": light, "weather_condition": weather,
        "time_of_day": time_of_day, "weather_category": weather_cat,
        "temp_max": temp, "precipitation": rain, "wind_max": wind,
    }
    proba = predict_proba(model, payload)
    risk = "🔴 ÉLEVÉ" if proba >= 0.5 else "🟠 MODÉRÉ" if proba >= 0.2 else "🟢 FAIBLE"
    st.metric("Probabilité d'accident mortel", f"{proba:.1%}")
    st.success(f"Niveau de risque : **{risk}**")
    st.json(payload)
