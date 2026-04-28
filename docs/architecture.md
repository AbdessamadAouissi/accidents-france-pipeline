# Architecture technique

## Vue d'ensemble

Pipeline data **end-to-end** orchestré, modulaire et testé.

```
┌─────────────────┐
│  Data Sources   │  ONISR · INSEE · Open-Meteo
│  (data.gouv.fr) │
└────────┬────────┘
         │  (Python : requests, httpx)
         ▼
┌─────────────────┐
│   EXTRACT       │  src/extract/
│   - onisr.py    │  Téléchargement, cache local, conversion Parquet
│   - meteo.py    │
│   - insee.py    │
└────────┬────────┘
         │  (Parquet brut → data/processed/)
         ▼
┌─────────────────┐
│  TRANSFORM      │  src/transform/
│  - cleaning     │  Nettoyage typage + mapping codes ONISR
│  - geospatial   │  GeoDataFrame + filtre métropolitain
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   QUALITY       │  src/quality/
│   (GE-style)    │  Pass-rate >= 80% sinon failing pipeline
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LOAD (DuckDB)  │  src/load/duckdb_loader.py
│  3 schémas :    │
│  - raw          │  CSV ONISR bruts
│  - staging      │  Tables nettoyées
│  - marts        │  (créées par dbt)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  TRANSFORM dbt  │  dbt_project/
│  staging →      │  Modèles SQL versionnés + tests
│  intermediate → │  Doc auto + lineage
│  marts          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   ML            │  src/ml/
│   - hotspots    │  DBSCAN haversine
│   - classifier  │  RandomForest + StratifiedKFold
└────┬────────┬───┘
     │        │
     ▼        ▼
┌──────────┐ ┌──────────────┐
│ FastAPI  │ │  Streamlit   │
│ (REST)   │ │  Dashboard   │
└──────────┘ └──────────────┘

Orchestration : Airflow (DAG quotidien)
DevOps : Docker + GitHub Actions + pre-commit
Versioning data : DVC
```

## Décisions d'architecture

### Pourquoi DuckDB ?
- **OLAP in-process** : pas de serveur, démarrage instantané.
- **Lit nativement Parquet** (zéro copie, scan vectorisé).
- **SQL standard** + extensions analytiques (window functions).
- Idéal en **dev/portfolio** ; migration PostgreSQL/BigQuery triviale.

### Pourquoi dbt ?
- Sépare **logique métier (SQL)** du code Python.
- Tests intégrés (`unique`, `not_null`, expressions custom).
- **Lineage** auto + documentation générée.
- Standard de l'industrie data.

### Pourquoi DBSCAN pour les hotspots ?
- Pas besoin de fixer le nombre de clusters.
- Détecte des **formes arbitraires** (routes, intersections).
- Identifie le **bruit** (accidents isolés non significatifs).
- Métrique **haversine** pour respecter la sphéricité terrestre.

### Pourquoi RandomForest pour la gravité ?
- **Baseline robuste** sur données mixtes (num + cat).
- Peu sensible à la mise à l'échelle.
- Probabilités calibrées correctement (out-of-the-box).
- Importance des features interprétable.

### Pourquoi FastAPI ?
- **Pydantic v2** : validation auto des inputs.
- **OpenAPI / Swagger** auto-généré.
- Async natif, performance proche de Go/Node.
- Standard moderne pour API Python.

## Flux de données

| Étape | Entrée | Sortie | Outil |
|---|---|---|---|
| Extract | data.gouv.fr (CSV) | `data/processed/*.parquet` | Python + requests |
| Transform Python | Parquet | Parquet enrichi | pandas + GeoPandas |
| Quality | Parquet | Rapport pass/fail | GE-style |
| Load | Parquet | DuckDB tables `raw.*`, `staging.*` | DuckDB |
| dbt | DuckDB staging | DuckDB marts | dbt-duckdb |
| ML | marts.fct_accidents | `models/*.joblib` + parquets | scikit-learn |
| Serve | DuckDB + modèles | API JSON / dashboard | FastAPI / Streamlit |

## Sécurité & secrets

- Aucun secret hard-codé : tout passe par `.env` (pydantic-settings).
- `.env` exclu du Git (`.gitignore`).
- Pre-commit `detect-private-key` actif.
