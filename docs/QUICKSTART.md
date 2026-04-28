# Quickstart — premier run en 10 minutes

## 1. Installation

```bash
# Cloner
git clone https://github.com/<user>/accidents-france-pipeline.git
cd accidents-france-pipeline

# Créer venv + installer
python -m venv .venv
.venv/Scripts/activate         # Windows
# source .venv/bin/activate    # Linux/Mac
pip install -r requirements.txt

# Copier la config
cp .env.example .env
```

## 2. Premier run du pipeline

```bash
# Étape 1 : extraction (téléchargement ONISR + Météo + INSEE)
python -m src.extract.run_all

# Étape 2 : nettoyage & jointures
python -m src.transform.run

# Étape 3 : chargement DuckDB
python -m src.load.duckdb_loader

# Étape 4 : modèles dbt
cd dbt_project
dbt deps --profiles-dir .
dbt run --profiles-dir .
dbt test --profiles-dir .
cd ..

# Étape 5 : ML
python -m src.ml.train_all
```

## 3. Lancer les services

### Dashboard Streamlit
```bash
streamlit run dashboard/Home.py
# → http://localhost:8501
```

### API FastAPI
```bash
uvicorn src.api.main:app --reload
# → http://localhost:8000/docs
```

### Airflow (optionnel)
```bash
export AIRFLOW_HOME=$PWD/airflow
airflow standalone
# → http://localhost:8080  (admin / admin auto-généré)
```

## 4. Avec Docker (tout-en-un)

```bash
docker compose up -d --build api dashboard
# Streamlit  → http://localhost:8501
# FastAPI    → http://localhost:8000/docs

# Pipeline à la demande
docker compose run pipeline python -m src.extract.run_all

# Airflow (profile séparé)
docker compose --profile airflow up -d
```

## 5. Tests

```bash
pytest                           # tous les tests
pytest -m unit                   # uniquement unitaires
pytest --cov=src --cov-report=html
```

## 6. Troubleshooting

| Problème | Solution |
|---|---|
| `geopandas install fails` | Installer GDAL système : `apt-get install libgdal-dev` (Linux) ou `conda install gdal` (Windows) |
| `dbt: source not found` | Lancer d'abord `python -m src.load.duckdb_loader` |
| `No module named src` | S'assurer d'être à la racine du projet |
| `predict 503` | Lancer `python -m src.ml.train_all` d'abord |
