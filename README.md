# 🚦 Accidents de la route en France — Pipeline Data End-to-End

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![DuckDB](https://img.shields.io/badge/warehouse-DuckDB-yellow.svg)](https://duckdb.org/)
[![dbt](https://img.shields.io/badge/transform-dbt--duckdb-orange.svg)](https://www.getdbt.com/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/dashboard-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Pipeline **data end-to-end** sur les accidents corporels en France : **221 044 accidents** (2021–2024), **1 056 hotspots** détectés en métropole, **classifieur de gravité** (RandomForest, AUC 0.72), API REST et dashboard interactif.

---

## 🎯 Ce que fait le projet

1. **Extraction** dynamique depuis `data.gouv.fr` (ONISR), Open-Meteo (climat) et INSEE (population) — pas d'IDs hardcodés.
2. **Nettoyage** & jointures spatio-temporelles (pandas + DuckDB).
3. **Modélisation analytique** avec dbt (staging → intermediate → marts).
4. **ML** : DBSCAN haversine pour les hotspots géographiques + RandomForest pour la gravité fatale.
5. **API REST** FastAPI (4 routers) + **dashboard Streamlit** (5 pages interactives).
6. **Orchestration** Airflow + **CI** GitHub Actions + conteneurisation Docker.

---

## 📊 Résultats sur 2021–2024

| Métrique | Valeur |
|---|---:|
| Accidents corporels | **221 044** |
| Usagers impliqués | 506 886 |
| Accidents mortels (`is_fatal`) | 12 798 |
| Hotspots DBSCAN (métropole) | **1 056** |
| Couverture météo | 20 départements × 4 ans (28 122 lignes) |

**Top 5 hotspots** (DBSCAN, ε=300 m, min=10) :

| Rang | Zone | Accidents | Mortels | Taux fatalité |
|---:|---|---:|---:|---:|
| 1 | **Paris centre** (48.86, 2.36) | 47 391 | 414 | 0.9 % |
| 2 | **Lyon** (45.75, 4.85) | 4 189 | 61 | 1.5 % |
| 3 | **Marseille** (43.31, 5.39) | 3 743 | 80 | 2.1 % |
| 4 | **Angers** (47.47, −0.55) | 812 | 11 | 1.4 % |
| 5 | **Reims** (49.25, 4.03) | 783 | 7 | 0.9 % |

**Classifieur** `is_fatal` (RandomForest, 5-fold CV) : **F1-macro 0.426**, **ROC-AUC 0.720** — sur un problème très déséquilibré (5.8 % de positifs).

---

## 🏗️ Architecture

```
┌──────────────────┐    ┌────────────────┐    ┌──────────────────┐
│  data.gouv.fr    │    │  EXTRACT       │    │  TRANSFORM       │
│  ONISR (BAAC)    │───▶│  Python +      │───▶│  pandas +        │
│  Open-Meteo      │    │  requests      │    │  Parquet         │
│  INSEE           │    └────────────────┘    └────────┬─────────┘
└──────────────────┘                                   │
                                                       ▼
┌──────────────────┐    ┌────────────────┐    ┌──────────────────┐
│  STREAMLIT       │◀───│  FastAPI       │◀───│  DuckDB          │
│  5 pages         │    │  4 routers     │    │  warehouse       │
│  + Folium/Plotly │    │  + Pydantic v2 │    │  (in-process)    │
└──────────────────┘    └────────────────┘    └────────▲─────────┘
                                                       │
                              ┌────────────────────────┴─────┐
                              │  dbt-duckdb (7 modèles)      │
                              │  ML (DBSCAN + RandomForest)  │
                              └──────────────────────────────┘

   Airflow (DAG)  ·  GitHub Actions (CI)  ·  Docker  ·  Great Expectations
```

---

## 🛠️ Stack technique

| Couche | Outils |
|---|---|
| **Langages** | Python 3.11, SQL |
| **Extraction** | `requests`, `httpx`, `pandas` |
| **Stockage** | DuckDB, Parquet |
| **Transformations** | `dbt-duckdb` (staging / intermediate / marts) |
| **Qualité** | Great Expectations, `pytest` |
| **ML** | scikit-learn (DBSCAN haversine, RandomForest, `StratifiedKFold`) |
| **Géospatial** | Folium, GeoPandas, Shapely |
| **API** | FastAPI + Uvicorn + Pydantic v2 |
| **Dashboard** | Streamlit + Plotly + Folium |
| **Orchestration** | Apache Airflow |
| **DevOps** | Docker, docker-compose, GitHub Actions, pre-commit, `ruff`, `black`, `mypy` |

---

## 🚀 Démarrage

### Prérequis
- Python 3.11+
- (optionnel) Docker + Docker Compose

### Installation

```bash
git clone https://github.com/<votre-user>/accidents-france-pipeline.git
cd accidents-france-pipeline

python -m venv .venv
.venv/Scripts/activate          # Windows
# source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
cp .env.example .env
```

### Pipeline complet (~5 min)

```bash
# 1. Extraction (ONISR + Open-Meteo + INSEE)
python -m src.extract.run_all

# 2. Chargement DuckDB
python -m src.load.duckdb_loader

# 3. Transformations dbt (7 modèles)
cd dbt_project && dbt run --profiles-dir . && cd ..

# 4. Entraînement ML (DBSCAN + RandomForest)
python -m src.ml.train_all
```

> Avec `make` : `make pipeline`

### Lancer les services

```bash
# API REST  → http://localhost:8000/docs
uvicorn src.api.main:app --reload --port 8000

# Dashboard → http://localhost:8501
streamlit run dashboard/Home.py
```

### Avec Docker

```bash
docker-compose up -d
# Streamlit  : http://localhost:8501
# FastAPI    : http://localhost:8000/docs
# Airflow UI : http://localhost:8080
```

---

## 📂 Structure

```
.
├── src/
│   ├── extract/        # Extraction ONISR / Open-Meteo / INSEE
│   ├── transform/      # Nettoyage, mappings, dérivés temporels
│   ├── load/           # Loader DuckDB (raw → staging → marts vues)
│   ├── quality/        # Suites Great Expectations
│   ├── ml/             # hotspots.py (DBSCAN), severity_classifier.py (RF)
│   ├── api/            # FastAPI : routers/{kpis,accidents,hotspots,predict}
│   └── utils/          # config (Pydantic Settings), logger (loguru), io
├── dbt_project/
│   ├── models/staging/        # 1:1 sur sources, typages
│   ├── models/intermediate/   # int_accidents_enriched (jointure météo)
│   ├── models/marts/          # fct_accidents, agg_accidents_by_dep, ...
│   └── macros/generate_schema_name.sql  # évite le préfixe "main_"
├── dashboard/          # Home.py + 5 pages (KPIs, Carte, Tendances, Hotspots, Prediction)
├── airflow/dags/       # accidents_pipeline_daily
├── tests/              # pytest (extract, transform, ml, api)
├── data/
│   ├── raw/            # parquet bruts
│   ├── processed/      # tables nettoyées + ml/hotspots_summary.parquet
│   └── warehouse/      # accidents.duckdb
├── models/             # severity_rf.joblib (pickle scikit-learn)
└── docker-compose.yml  # API + dashboard + Airflow
```

---

## 🔁 Couches dbt

| Couche | Modèles | Rôle |
|---|---|---|
| **staging** | `stg_accidents`, `stg_meteo`, `stg_severity` | Cast, renommage, 1 ligne = 1 entité |
| **intermediate** | `int_accidents_enriched` | Jointure accidents × météo (sur `dep` × `date`) |
| **marts** | `fct_accidents`, `agg_accidents_by_dep`, `agg_temporal_patterns` | Tables analytiques denormalisées (26 colonnes pour la fact) |

`dbt run` reconstruit les 7 modèles en ~5 s. Tests : `dbt test` (13 tests : `unique`, `not_null`, ranges).

---

## 🤖 Modèles ML

### 1. Hotspots — DBSCAN haversine

- **Filtre métropole** d'abord (bbox lat 41–51.5, lon −5.5 à 10) — exclut DOM-TOM.
- DBSCAN en métrique haversine, ε = 300 m, min_samples = 10.
- 847 clusters trouvés sur 157 561 points (91 993 marqués bruit).

### 2. Classifieur de gravité — RandomForest

- **Cible** : `is_fatal` (≥ 1 décès), 5.7 % de positifs.
- **Features de base** (toujours dispo) : `hour`, `month`, `day_of_week`, `light_condition`, `weather_condition`, `time_of_day`.
- **Features optionnelles** (depuis dbt) : `temp_max`, `precipitation`, `wind_max`, `weather_category`.
- Pipeline sklearn : `SimpleImputer` + `StandardScaler` (num) / `OneHotEncoder` (cat) + `RandomForest(n=300, max_depth=12, class_weight='balanced')`.
- Sélection automatique des features non-vides (`prepare()` skip les colonnes 100 % NaN).
- Évaluation : `StratifiedKFold(5)`, **F1-macro 0.449 ± 0.004**, **ROC-AUC 0.692**.

---

## 📡 API — Exemples

```bash
# KPIs globaux
curl http://localhost:8000/api/v1/kpis
# → {"nb_accidents":166642,"nb_tues":10167,"nb_blesses_hosp":57624, ...}

# Accidents (filtres : year, dep, severity, limit, offset)
curl "http://localhost:8000/api/v1/accidents?limit=3"

# Hotspots (top clusters DBSCAN)
curl "http://localhost:8000/api/v1/hotspots?limit=5"

# Prédiction de gravité
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"hour":2,"month":12,"day_of_week":5,
       "light_condition":"nuit_sans_eclairage",
       "weather_condition":"pluie_forte",
       "time_of_day":"nuit"}'
# → {"fatality_probability":0.6752,"risk_level":"élevé","model_version":"severity_rf_v1"}
```

Doc Swagger auto-générée : `http://localhost:8000/docs`.

---

## 📊 Dashboard Streamlit

5 pages interactives :

| Page | Contenu |
|---|---|
| 📊 **KPIs** | Filtres période / dép. / gravité, métriques clés, breakdown par département |
| 🗺️ **Carte** | Heatmap Folium + clusters de marqueurs (filtrable) |
| 📈 **Tendances** | Saisonnalité (heatmap heure × jour), corrélation météo ↔ gravité |
| 🎯 **Hotspots** | Top zones DBSCAN sur Folium (cercles dimensionnés au taux de fatalité) |
| 🤖 **Prédiction** | Formulaire interactif → appel modèle, jauge de risque |

---

## 🧪 Qualité & tests

```bash
make test        # pytest -v
make lint        # black + ruff + mypy
make ge          # Great Expectations checkpoints
make dbt-test    # 13 tests dbt
```

CI sur push/PR : `lint → test → ge → dbt-test` (voir `.github/workflows/`).

---

## 📚 Sources de données

| Source | Description | Lien |
|---|---|---|
| **ONISR / BAAC** | Accidents corporels (caractéristiques, lieux, véhicules, usagers) | [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2023/) |
| **Open-Meteo** | Climat quotidien (T°, précipitations, vent) — API gratuite | [open-meteo.com](https://open-meteo.com/) |
| **INSEE** | Population communale | [insee.fr](https://www.insee.fr/) |

---

## 🗓️ Orchestration (Airflow)

DAG `accidents_pipeline_daily` :

```
extract_onisr  ─┐
extract_meteo  ─┼─▶ validate_ge ─▶ load_duckdb ─▶ dbt_run ─▶ dbt_test ─▶ train_ml
extract_insee  ─┘
```

`@daily`, retry exponentiel.

---

## 🔭 Limites connues & suite

- **Couverture météo** : 20 départements (zones les plus accidentogènes). À étendre aux 96 pour gagner sur les features ML.
- **Classifieur** : baseline RF — tester XGBoost / LightGBM avec calibration des proba (Platt / isotonic).
- **MLflow** : pas encore intégré (à venir pour le tracking d'expériences).
- **Année 2025** : ONISR a un délai de ~12 mois ; le millésime 2025 sortira fin 2026. Le pattern d'extraction est dynamique — ajouter une année = changer `ONISR_YEARS` dans `.env`.

---

## 📄 Licence

MIT — voir [LICENSE](LICENSE).
