.PHONY: help setup install clean lint format test test-cov \
        extract transform load pipeline ml \
        dashboard api airflow ge dbt-run dbt-test docker-up docker-down

help:
	@echo "Cibles disponibles :"
	@echo "  setup        - Installer venv + dépendances + pre-commit"
	@echo "  install      - Installer requirements"
	@echo "  clean        - Nettoyer caches & artefacts"
	@echo "  lint         - black + ruff + mypy"
	@echo "  format       - Formater le code"
	@echo "  test         - Lancer pytest"
	@echo "  test-cov     - Pytest avec couverture"
	@echo "  extract      - Extraire les données sources"
	@echo "  transform    - Transformer (Python)"
	@echo "  load         - Charger dans DuckDB"
	@echo "  ml           - Entraîner les modèles ML"
	@echo "  pipeline     - Pipeline complet (extract -> ml)"
	@echo "  dashboard    - Lancer Streamlit"
	@echo "  api          - Lancer FastAPI"
	@echo "  airflow      - Lancer Airflow standalone"
	@echo "  ge           - Validation Great Expectations"
	@echo "  dbt-run      - Exécuter dbt"
	@echo "  dbt-test     - Tests dbt"
	@echo "  docker-up    - Lancer toute la stack Docker"
	@echo "  docker-down  - Arrêter Docker"

setup:
	python -m venv .venv
	.venv/Scripts/pip install --upgrade pip
	.venv/Scripts/pip install -r requirements.txt
	.venv/Scripts/pre-commit install

install:
	pip install -r requirements.txt

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true

lint:
	black --check src tests dashboard
	ruff check src tests dashboard
	mypy src --ignore-missing-imports

format:
	black src tests dashboard
	ruff check --fix src tests dashboard

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

extract:
	python -m src.extract.run_all

transform:
	python -m src.transform.run

load:
	python -m src.load.duckdb_loader

ml:
	python -m src.ml.train_all

pipeline: extract load dbt-run ml
	@echo "Pipeline terminé."

dashboard:
	streamlit run dashboard/Home.py

api:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

airflow:
	export AIRFLOW_HOME=$(PWD)/airflow && airflow standalone

ge:
	python -m src.quality.run_checkpoints

dbt-run:
	cd dbt_project && dbt run --profiles-dir .

dbt-test:
	cd dbt_project && dbt test --profiles-dir .

docker-up:
	docker-compose up -d --build

docker-down:
	docker-compose down
