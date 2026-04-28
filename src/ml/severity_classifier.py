"""Classifieur de gravité d'accident.

Cible binaire : `is_fatal` (au moins un décès).
Algorithme : RandomForest (baseline robuste, peu sensible aux distributions).
Évaluation : StratifiedKFold (5 folds), métriques F1-macro & ROC-AUC.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.utils.config import settings
from src.utils.logger import get_logger

log = get_logger(__name__)

# Features toujours disponibles depuis les données ONISR brutes
BASE_NUM = ["hour", "month", "day_of_week"]
# Features optionnelles (viennent du join météo dbt — absentes si dbt n'a pas tourné)
OPT_NUM = ["temp_max", "precipitation", "wind_max"]
# Catégorielles — certaines peuvent être absentes (ex: weather_category vient du dbt)
BASE_CAT = ["light_condition", "weather_condition", "time_of_day"]
OPT_CAT = ["weather_category"]
ALL_NUM = BASE_NUM + OPT_NUM
ALL_CAT = BASE_CAT + OPT_CAT
TARGET = "is_fatal"


@dataclass
class TrainResult:
    cv_f1_mean: float
    cv_f1_std: float
    cv_auc_mean: float
    model_path: Path


def build_pipeline(num_features: list[str], cat_features: list[str]) -> Pipeline:
    """Construit le pipeline sklearn avec les features réellement disponibles."""
    num_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    transformers = []
    if num_features:
        transformers.append(("num", num_pipe, num_features))
    if cat_features:
        transformers.append(("cat", cat_pipe, cat_features))

    pre = ColumnTransformer(transformers=transformers)
    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=20,
        n_jobs=-1,
        class_weight="balanced",
        random_state=settings.random_seed,
    )
    return Pipeline([("preprocess", pre), ("model", clf)])


def prepare(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, list[str], list[str]]:
    """Sélectionne les features disponibles + target. Injecte NaN pour les colonnes optionnelles manquantes."""
    # Injecter les colonnes optionnelles manquantes avec NaN (l'imputer les gérera)
    for col in OPT_NUM + OPT_CAT:
        if col not in df.columns:
            df = df.copy()
            df[col] = np.nan

    num_feats = [c for c in ALL_NUM if c in df.columns and df[c].notna().any()]
    cat_feats = [c for c in ALL_CAT if c in df.columns and df[c].notna().any()]
    all_feats = num_feats + cat_feats

    df = df[all_feats + [TARGET]].dropna(subset=[TARGET])
    y = df[TARGET].astype(int)
    X = df[all_feats]
    return X, y, num_feats, cat_feats


def train(df: pd.DataFrame, model_name: str = "severity_rf.joblib") -> TrainResult:
    X, y, num_feats, cat_feats = prepare(df)
    log.info(f"Entraînement sur {len(X):,} accidents (positifs={y.sum():,})")

    pipe = build_pipeline(num_feats, cat_feats)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=settings.random_seed)

    f1 = cross_val_score(pipe, X, y, cv=cv, scoring="f1_macro", n_jobs=-1)
    log.info(f"F1-macro CV : {f1.mean():.3f} ± {f1.std():.3f}")

    pipe.fit(X, y)
    proba = pipe.predict_proba(X)[:, 1]
    auc = roc_auc_score(y, proba)
    log.info(f"ROC-AUC (in-sample) : {auc:.3f}")
    log.info("\n" + classification_report(y, pipe.predict(X)))

    settings.model_dir.mkdir(parents=True, exist_ok=True)
    path = settings.model_dir / model_name
    joblib.dump(pipe, path)
    log.info(f"✓ Modèle sauvegardé : {path}")

    return TrainResult(
        cv_f1_mean=float(f1.mean()),
        cv_f1_std=float(f1.std()),
        cv_auc_mean=float(auc),
        model_path=path,
    )


def load_model(model_name: str = "severity_rf.joblib") -> Pipeline:
    path = settings.model_dir / model_name
    if not path.exists():
        raise FileNotFoundError(f"Modèle introuvable : {path}. Entraîner d'abord.")
    return joblib.load(path)


def predict_proba(model: Pipeline, payload: dict) -> float:
    """Prédit la probabilité de gravité fatale pour un dict de features."""
    df = pd.DataFrame([payload])
    for c in ALL_NUM:
        if c not in df.columns:
            df[c] = np.nan
    for c in ALL_CAT:
        if c not in df.columns:
            df[c] = np.nan
    return float(model.predict_proba(df)[:, 1][0])
