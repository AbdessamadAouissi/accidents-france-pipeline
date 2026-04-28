"""API FastAPI : KPIs, accidents, hotspots, prédiction de gravité."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import accidents, hotspots, kpis, predict
from src.utils.config import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(f"🚀 API démarrée — env={settings.app_env}")
    yield
    log.info("👋 API arrêtée")


app = FastAPI(
    title="Accidents France API",
    description="API REST pour l'analyse des accidents de la route en France.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(kpis.router, prefix=settings.api_prefix, tags=["KPIs"])
app.include_router(accidents.router, prefix=settings.api_prefix, tags=["Accidents"])
app.include_router(hotspots.router, prefix=settings.api_prefix, tags=["Hotspots"])
app.include_router(predict.router, prefix=settings.api_prefix, tags=["Predict"])


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "accidents-france-api",
        "version": "0.1.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
