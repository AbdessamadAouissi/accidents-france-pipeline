"""Tests du module transform.cleaning."""

import pandas as pd
import pytest

from src.transform.cleaning import (
    aggregate_severity,
    clean_caracteristiques,
    clean_usagers,
)


@pytest.mark.unit
class TestCleanCaracteristiques:
    def test_creates_accident_id(self, sample_caracteristiques):
        out = clean_caracteristiques(sample_caracteristiques)
        assert "accident_id" in out.columns
        assert out["accident_id"].notna().all()

    def test_parses_date(self, sample_caracteristiques):
        out = clean_caracteristiques(sample_caracteristiques)
        assert pd.api.types.is_datetime64_any_dtype(out["date"])
        assert out["date"].dt.year.iloc[0] == 2021

    def test_parses_hour(self, sample_caracteristiques):
        out = clean_caracteristiques(sample_caracteristiques)
        assert out["hour"].iloc[0] == 8
        assert out["hour"].iloc[1] == 18

    def test_zero_coordinates_become_nan(self, sample_caracteristiques):
        out = clean_caracteristiques(sample_caracteristiques)
        assert pd.isna(out["lat"].iloc[2])
        assert pd.isna(out["lon"].iloc[2])

    def test_comma_decimal_parsed(self, sample_caracteristiques):
        out = clean_caracteristiques(sample_caracteristiques)
        assert out["lat"].iloc[0] == pytest.approx(48.8566)
        assert out["lon"].iloc[0] == pytest.approx(2.3522)

    def test_dep_zfill(self, sample_caracteristiques):
        df = sample_caracteristiques.copy()
        df["dep"] = ["1", "75", "2A"]
        out = clean_caracteristiques(df)
        assert out["dep"].tolist() == ["01", "75", "2A"]

    def test_lum_atm_mapping(self, sample_caracteristiques):
        out = clean_caracteristiques(sample_caracteristiques)
        assert out["light_condition"].iloc[0] == "plein_jour"
        assert out["weather_condition"].iloc[1] == "pluie_legere"


@pytest.mark.unit
class TestCleanUsagers:
    def test_gravity_mapping(self, sample_usagers):
        out = clean_usagers(sample_usagers)
        assert "tue" in out["gravity"].values
        assert "blesse_leger" in out["gravity"].values

    def test_age_computed(self, sample_usagers):
        out = clean_usagers(sample_usagers)
        assert "age" in out.columns
        assert out["age"].iloc[0] == 31


@pytest.mark.unit
class TestAggregateSeverity:
    def test_worst_gravity_per_accident(self, sample_usagers):
        u = clean_usagers(sample_usagers)
        agg = aggregate_severity(u)
        # Accident 2 contient un tué => is_fatal=True
        a2 = agg.loc[agg["accident_id"] == "202100000002"].iloc[0]
        assert a2["is_fatal"]
        assert a2["nb_tues"] == 1

    def test_counts_match(self, sample_usagers):
        u = clean_usagers(sample_usagers)
        agg = aggregate_severity(u)
        a3 = agg.loc[agg["accident_id"] == "202100000003"].iloc[0]
        assert a3["nb_usagers"] == 3
        assert a3["nb_blesses_legers"] == 2
