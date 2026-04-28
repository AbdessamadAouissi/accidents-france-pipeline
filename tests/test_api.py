"""Tests d'intégration de l'API FastAPI (smoke tests sans DB)."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.unit
def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "accidents-france-api"


@pytest.mark.unit
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.unit
def test_openapi_schema(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    paths = schema["paths"]
    assert "/api/v1/kpis" in paths
    assert "/api/v1/accidents" in paths
    assert "/api/v1/hotspots" in paths
    assert "/api/v1/predict" in paths
