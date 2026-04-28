"""Nettoyage des données ONISR.

Conventions ONISR (extrait) :
  - lat / long : coordonnées (parfois "0", parfois en virgule décimale)
  - grav (usagers) : 1=indemne, 2=tué, 3=blessé hospitalisé, 4=blessé léger
  - lum : 1=plein jour, 2=crépuscule, 3=nuit sans éclairage, 4=avec éclairage non allumé, 5=allumé
  - atm (météo) : 1=normale, 2=pluie légère, 3=pluie forte, 7=brouillard, 8=vent, ...
"""

from __future__ import annotations

import pandas as pd

from src.utils.logger import get_logger

log = get_logger(__name__)

# ===== Mappings explicites pour lisibilité =====
GRAVITY_MAP = {
    1: "indemne",
    2: "tue",
    3: "blesse_hospitalise",
    4: "blesse_leger",
}

LIGHT_MAP = {
    1: "plein_jour",
    2: "crepuscule_aube",
    3: "nuit_sans_eclairage",
    4: "nuit_eclairage_non_allume",
    5: "nuit_eclairage_allume",
}

WEATHER_MAP = {
    1: "normale",
    2: "pluie_legere",
    3: "pluie_forte",
    4: "neige_grele",
    5: "brouillard_fumee",
    6: "vent_fort_tempete",
    7: "temps_eblouissant",
    8: "temps_couvert",
    9: "autre",
}


def _to_float_coord(s: pd.Series) -> pd.Series:
    """Convertit les coordonnées ONISR (string avec virgule, parfois '0') en float."""
    if s.dtype == object:
        s = s.astype(str).str.replace(",", ".", regex=False)
    out = pd.to_numeric(s, errors="coerce")
    out = out.where(out != 0)
    return out


def clean_caracteristiques(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie le fichier 'caracteristiques' (1 ligne = 1 accident)."""
    df = df.copy()
    df.columns = [c.lower().strip() for c in df.columns]

    # ID accident — le nom de colonne change selon les millésimes ONISR :
    #   2021- : Num_Acc  →  num_acc  (après lowercase)
    #   2022+ : Accident_Id  →  accident_id  (déjà le bon nom)
    # Quand on concatène plusieurs années, les deux colonnes coexistent avec des NaN
    # croisés → on combine via coalesce (première valeur non-nulle gagne).
    num_acc_vals = pd.to_numeric(df.get("num_acc"), errors="coerce") if "num_acc" in df.columns else None
    acc_id_vals = pd.to_numeric(df.get("accident_id"), errors="coerce") if "accident_id" in df.columns else None

    combined: pd.Series | None = None
    if num_acc_vals is not None and acc_id_vals is not None:
        combined = num_acc_vals.combine_first(acc_id_vals)
    elif num_acc_vals is not None:
        combined = num_acc_vals
    elif acc_id_vals is not None:
        combined = acc_id_vals

    if combined is not None:
        # to_numeric → Int64 évite l'artifact '202100000001.0' quand pandas lit en float
        df["accident_id"] = combined.astype("Int64").astype(str)

    # Date
    if {"an", "mois", "jour"}.issubset(df.columns):
        # Année peut être '21' (2021) ou '2021' selon les fichiers
        an = pd.to_numeric(df["an"], errors="coerce")
        an = an.where(an >= 100, an + 2000)
        df["date"] = pd.to_datetime(
            dict(
                year=an.astype("Int64"),
                month=pd.to_numeric(df["mois"], errors="coerce").astype("Int64"),
                day=pd.to_numeric(df["jour"], errors="coerce").astype("Int64"),
            ),
            errors="coerce",
        )

    # Heure + dérivés temporels utiles pour le ML
    if "hrmn" in df.columns:
        df["hour"] = (
            df["hrmn"].astype(str).str.zfill(4).str[:2].pipe(pd.to_numeric, errors="coerce")
        )

    if "date" in df.columns:
        df["month"] = df["date"].dt.month
        df["day_of_week"] = df["date"].dt.dayofweek  # 0=lundi
        df["time_of_day"] = df["hour"].map(
            lambda h: (
                "matin"      if pd.notna(h) and 6  <= h <= 9  else
                "midi"       if pd.notna(h) and 10 <= h <= 13 else
                "apres_midi" if pd.notna(h) and 14 <= h <= 17 else
                "soiree"     if pd.notna(h) and 18 <= h <= 21 else
                "nuit"
            )
        )

    # Coordonnées
    if "lat" in df.columns:
        df["lat"] = _to_float_coord(df["lat"])
    if "long" in df.columns:
        df["lon"] = _to_float_coord(df["long"])

    # Mappings lisibles
    if "lum" in df.columns:
        df["light_condition"] = pd.to_numeric(df["lum"], errors="coerce").map(LIGHT_MAP)
    if "atm" in df.columns:
        df["weather_condition"] = pd.to_numeric(df["atm"], errors="coerce").map(WEATHER_MAP)

    # Département (préserve les zéros & corse '2A'/'2B')
    if "dep" in df.columns:
        df["dep"] = df["dep"].astype(str).str.zfill(2).str.upper()

    # Commune
    if "com" in df.columns:
        df["com"] = df["com"].astype(str)

    log.info(f"✓ caracteristiques nettoyé : {len(df):,} accidents")
    return df


def clean_usagers(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie le fichier 'usagers' (1 ligne = 1 personne impliquée)."""
    df = df.copy()
    df.columns = [c.lower().strip() for c in df.columns]
    if "num_acc" in df.columns:
        # to_numeric → Int64 évite le artifact '202100000001.0' quand pandas lit en float
        df["accident_id"] = (
            pd.to_numeric(df["num_acc"], errors="coerce")
            .astype("Int64")
            .astype(str)
        )
    if "grav" in df.columns:
        df["gravity"] = pd.to_numeric(df["grav"], errors="coerce").map(GRAVITY_MAP)
    if "an_nais" in df.columns and "source_year" in df.columns:
        df["age"] = pd.to_numeric(df["source_year"], errors="coerce") - pd.to_numeric(
            df["an_nais"], errors="coerce"
        )
    log.info(f"✓ usagers nettoyé : {len(df):,} personnes")
    return df


def aggregate_severity(usagers: pd.DataFrame) -> pd.DataFrame:
    """Agrège la gravité par accident (worst-case + nb usagers)."""
    rank = {"indemne": 0, "blesse_leger": 1, "blesse_hospitalise": 2, "tue": 3}
    u = usagers.copy()
    u["gravity_rank"] = u["gravity"].map(rank).fillna(0)
    grp = u.groupby("accident_id").agg(
        nb_usagers=("gravity", "size"),
        nb_tues=("gravity", lambda s: (s == "tue").sum()),
        nb_blesses_hosp=("gravity", lambda s: (s == "blesse_hospitalise").sum()),
        nb_blesses_legers=("gravity", lambda s: (s == "blesse_leger").sum()),
        worst_gravity_rank=("gravity_rank", "max"),
    )
    inv = {v: k for k, v in rank.items()}
    grp["worst_gravity"] = grp["worst_gravity_rank"].map(inv)
    grp["is_fatal"] = grp["nb_tues"] > 0
    return grp.reset_index()
