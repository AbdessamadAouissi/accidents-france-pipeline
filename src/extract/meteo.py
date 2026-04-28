"""Extraction de données météo journalières par département.

Utilise l'API Open-Meteo (gratuite, sans clé) pour obtenir un historique
quotidien par centroïde de département (températures, précipitations, vent).

Doc API : https://open-meteo.com/en/docs/historical-weather-api
"""

from __future__ import annotations

from datetime import date

import httpx
import pandas as pd

from src.utils.config import settings
from src.utils.io import save_parquet
from src.utils.logger import get_logger

log = get_logger(__name__)

# Centroïdes approximatifs des 20 plus gros départements (couverture ~70% des accidents).
# Open-Meteo est gratuit & sans clé : 1 appel par dep × année.
DEPARTMENT_CENTROIDS: dict[str, tuple[float, float]] = {
    "75": (48.8566, 2.3522),    # Paris
    "13": (43.5297, 5.4474),    # Bouches-du-Rhône (Marseille)
    "69": (45.7640, 4.8357),    # Rhône (Lyon)
    "31": (43.6047, 1.4442),    # Haute-Garonne (Toulouse)
    "59": (50.6292, 3.0573),    # Nord (Lille)
    "33": (44.8378, -0.5792),   # Gironde (Bordeaux)
    "44": (47.2184, -1.5536),   # Loire-Atlantique (Nantes)
    "06": (43.7102, 7.2620),    # Alpes-Maritimes (Nice)
    "67": (48.5734, 7.7521),    # Bas-Rhin (Strasbourg)
    "92": (48.8924, 2.2150),    # Hauts-de-Seine
    "93": (48.9136, 2.4824),    # Seine-Saint-Denis
    "94": (48.7791, 2.4615),    # Val-de-Marne
    "77": (48.6173, 2.9276),    # Seine-et-Marne
    "78": (48.8014, 2.1300),    # Yvelines
    "91": (48.5300, 2.2400),    # Essonne
    "95": (49.0000, 2.1500),    # Val-d'Oise
    "34": (43.6112, 3.8767),    # Hérault (Montpellier)
    "35": (48.1173, -1.6778),   # Ille-et-Vilaine (Rennes)
    "38": (45.1885, 5.7245),    # Isère (Grenoble)
    "76": (49.4431, 1.0993),    # Seine-Maritime (Rouen)
}

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_one(dep: str, lat: float, lon: float, year: int) -> pd.DataFrame:
    """Récupère la météo quotidienne d'un département pour une année."""
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(
            [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "rain_sum",
                "snowfall_sum",
                "windspeed_10m_max",
            ]
        ),
        "timezone": "Europe/Paris",
    }
    log.info(f"⬇ Météo dep={dep} year={year}")
    r = httpx.get(OPEN_METEO_URL, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()["daily"]
    df = pd.DataFrame(data)
    df["dep"] = dep
    df.rename(columns={"time": "date"}, inplace=True)
    df["date"] = pd.to_datetime(df["date"])
    return df


def run(years: list[int] | None = None) -> pd.DataFrame:
    years = years or settings.years
    log.info(f"== Extraction Météo : années {years} ==")
    frames: list[pd.DataFrame] = []
    for y in years:
        for dep, (lat, lon) in DEPARTMENT_CENTROIDS.items():
            try:
                frames.append(fetch_one(dep, lat, lon, y))
            except Exception as e:  # noqa: BLE001
                log.error(f"✗ Échec dep={dep} year={y}: {e}")

    df = pd.concat(frames, ignore_index=True)
    dest = settings.processed_dir / "meteo" / "meteo_daily.parquet"
    save_parquet(df, dest)
    return df


if __name__ == "__main__":
    run()
