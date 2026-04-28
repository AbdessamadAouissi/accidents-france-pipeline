"""Fixtures pytest partagées."""

import pandas as pd
import pytest


@pytest.fixture
def sample_caracteristiques() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Num_Acc": [202100000001, 202100000002, 202100000003],
            "an": [2021, 2021, 2021],
            "mois": [3, 7, 12],
            "jour": [15, 20, 5],
            "hrmn": ["0830", "1845", "2300"],
            "lat": ["48,8566", "43,2965", "0"],
            "long": ["2,3522", "5,3698", "0"],
            "dep": ["75", "13", "69"],
            "com": ["75056", "13055", "69123"],
            "lum": [1, 5, 3],
            "atm": [1, 2, 7],
        }
    )


@pytest.fixture
def sample_usagers() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Num_Acc": [
                202100000001, 202100000001,
                202100000002,
                202100000003, 202100000003, 202100000003,
            ],
            "grav": [1, 4, 2, 3, 4, 4],
            "an_nais": [1990, 1985, 1970, 2000, 1995, 1980],
            "source_year": [2021] * 6,
        }
    )
