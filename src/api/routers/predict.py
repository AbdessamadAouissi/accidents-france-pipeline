"""Endpoint prédiction de gravité (modèle ML)."""

from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from src.ml.severity_classifier import load_model, predict_proba

router = APIRouter()


class PredictPayload(BaseModel):
    hour: int = Field(..., ge=0, le=23, description="Heure (0-23)")
    month: int = Field(..., ge=1, le=12)
    day_of_week: int = Field(..., ge=0, le=6, description="0=lundi, 6=dimanche")
    light_condition: str = Field("plein_jour", description="ex: plein_jour, nuit_eclairage_allume")
    weather_condition: str = Field("normale", description="ex: normale, pluie_legere, brouillard_fumee")
    time_of_day: str = Field("apres_midi")
    weather_category: str = Field("normal", description="ex: normal, pluvieux, neigeux")
    temp_max: float | None = None
    precipitation: float | None = None
    wind_max: float | None = None


class PredictResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    fatality_probability: float = Field(..., ge=0.0, le=1.0)
    risk_level: str
    model_version: str = "severity_rf_v1"


@lru_cache(maxsize=1)
def _model():
    try:
        return load_model()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@router.post("/predict", response_model=PredictResponse, summary="Prédiction de gravité")
def predict(payload: PredictPayload) -> PredictResponse:
    proba = predict_proba(_model(), payload.model_dump())
    if proba >= 0.5:
        risk = "élevé"
    elif proba >= 0.2:
        risk = "modéré"
    else:
        risk = "faible"
    return PredictResponse(fatality_probability=round(proba, 4), risk_level=risk)
