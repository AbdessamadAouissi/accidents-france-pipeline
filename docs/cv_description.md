# Descriptif pour CV

## Version courte (4-5 lignes — recommandée pour CV papier)

> **Pipeline data end-to-end — Accidents de la route en France** *(2025)*
> Conception et industrialisation d'un pipeline ETL/ELT complet sur les accidents corporels (ONISR + INSEE + Météo) : extraction Python automatisée, validation Great Expectations, warehouse DuckDB, transformations dbt, modèles ML (DBSCAN pour hotspots, RandomForest pour gravité), API FastAPI et dashboard Streamlit. Orchestration Apache Airflow, conteneurisation Docker, CI/CD GitHub Actions, tests pytest (>80% couverture).
> **Stack** : Python · pandas · GeoPandas · DuckDB · dbt · Airflow · scikit-learn · FastAPI · Streamlit · Docker · Git · pytest

---

## Version longue (LinkedIn / portfolio détaillé)

### 🚦 Pipeline géospatial accidents de la route en France

**Contexte** — Construire une plateforme analytique end-to-end (de l'ingestion à la visualisation) pour identifier les facteurs de risque routier, en démontrant la maîtrise d'un stack data moderne de qualité production.

**Réalisations**

- **Ingestion multi-sources** : pipeline Python automatisé téléchargeant et fusionnant les données ONISR (accidents corporels), INSEE (population) et Open-Meteo (météo journalière par département). Détection automatique d'encodage, retry, cache local.
- **Data warehouse** : modélisation en couches (raw → staging → marts) sur **DuckDB**, avec **dbt** pour les transformations SQL versionnées, tests automatiques (`unique`, `not_null`, expressions custom) et lineage documenté.
- **Data Quality** : suite de validations (Great Expectations-style) intégrée au DAG Airflow — fait échouer le pipeline si pass-rate < 80%.
- **Analyses géospatiales** : conversion GeoPandas, filtrage défensif (bounding-box métropole), indexation H3, cartographie Folium (heatmap + clusters).
- **Machine Learning** :
    - Détection de **hotspots** par clustering DBSCAN (métrique haversine, paramétrable en km).
    - Classifieur de gravité (RandomForest + StratifiedKFold 5 folds), F1-macro / ROC-AUC reportés.
- **Exposition** : API REST **FastAPI** (Pydantic v2, OpenAPI auto) + dashboard **Streamlit multi-pages** (KPIs filtrables, carte interactive, tendances, prédiction live).
- **Industrialisation** :
    - Orchestration **Airflow** (DAG quotidien, retry exponentiel, alerting).
    - Conteneurisation **Docker** + **docker-compose** (4 services).
    - **CI/CD GitHub Actions** : lint (black, ruff, mypy), tests pytest avec couverture, dbt compile, build des images.
    - **pre-commit** hooks + versioning données via **DVC**.

**Stack technique**
`Python 3.11` · `pandas` · `GeoPandas` · `Shapely` · `Folium` · `H3` · `DuckDB` · `dbt-duckdb` · `Great Expectations` · `scikit-learn` · `Apache Airflow 2.x` · `FastAPI` · `Pydantic v2` · `Streamlit` · `Plotly` · `Docker` · `GitHub Actions` · `pytest` · `Make`

**Code & démo** — [github.com/<user>/accidents-france-pipeline](#)

---

## Points à mettre en avant à l'oral

1. **Pipeline réellement orchestré** (pas un notebook unique) → démontre la maturité industrielle.
2. **Couverture des tests** > 80% → démontre la rigueur.
3. **Trois types de tests** : unitaires (pytest) + qualité données (GE) + tests SQL (dbt).
4. **Choix d'architecture justifiés** (DuckDB vs Postgres, DBSCAN vs K-means) → démontre la réflexion.
5. **Production-ready** : Docker, CI/CD, secrets via .env, healthchecks → démontre l'autonomie déploiement.
