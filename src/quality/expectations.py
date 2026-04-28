"""Validation des données via Great Expectations (API ergonomique sans GE complet).

Pour rester léger et reproductible, on utilise une suite d'assertions
inspirée de GE — qui peuvent être migrées vers GE-natif au besoin.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""

    def __str__(self) -> str:
        flag = "✓" if self.passed else "✗"
        return f"{flag} {self.name} — {self.detail}"


def expect_columns_exist(df: pd.DataFrame, cols: list[str]) -> CheckResult:
    missing = [c for c in cols if c not in df.columns]
    return CheckResult(
        name="columns_exist",
        passed=not missing,
        detail=f"missing={missing}" if missing else f"all {len(cols)} columns present",
    )


def expect_no_nulls(df: pd.DataFrame, col: str, threshold: float = 0.05) -> CheckResult:
    if col not in df.columns:
        return CheckResult("no_nulls", False, f"column '{col}' missing")
    null_ratio = df[col].isna().mean()
    return CheckResult(
        name=f"no_nulls[{col}]",
        passed=null_ratio <= threshold,
        detail=f"null_ratio={null_ratio:.2%} (max={threshold:.0%})",
    )


def expect_values_in_set(df: pd.DataFrame, col: str, allowed: set) -> CheckResult:
    if col not in df.columns:
        return CheckResult("values_in_set", False, f"column '{col}' missing")
    extra = set(df[col].dropna().unique()) - allowed
    return CheckResult(
        name=f"values_in_set[{col}]",
        passed=not extra,
        detail=f"unexpected={list(extra)[:5]}" if extra else "ok",
    )


def expect_in_range(df: pd.DataFrame, col: str, lo: float, hi: float) -> CheckResult:
    if col not in df.columns:
        return CheckResult("in_range", False, f"column '{col}' missing")
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    out_of = ((s < lo) | (s > hi)).sum()
    return CheckResult(
        name=f"in_range[{col}]",
        passed=out_of == 0,
        detail=f"out_of_range={out_of} (range=[{lo},{hi}])",
    )


def expect_unique(df: pd.DataFrame, col: str) -> CheckResult:
    if col not in df.columns:
        return CheckResult("unique", False, f"column '{col}' missing")
    dup = df[col].duplicated().sum()
    return CheckResult(
        name=f"unique[{col}]",
        passed=dup == 0,
        detail=f"duplicates={dup}",
    )


def run_suite_accidents(df: pd.DataFrame) -> list[CheckResult]:
    """Suite de validation pour la table fct_accidents."""
    checks = [
        expect_columns_exist(df, ["accident_id", "date", "lat", "lon", "dep"]),
        expect_unique(df, "accident_id"),
        expect_no_nulls(df, "accident_id", threshold=0.0),
        expect_no_nulls(df, "date", threshold=0.01),
        expect_in_range(df, "lat", 41.0, 51.5),
        expect_in_range(df, "lon", -5.5, 10.0),
        expect_in_range(df, "hour", 0, 23),
    ]
    for c in checks:
        (log.info if c.passed else log.error)(str(c))
    return checks


def summarize(checks: list[CheckResult]) -> dict:
    passed = sum(c.passed for c in checks)
    return {
        "total": len(checks),
        "passed": passed,
        "failed": len(checks) - passed,
        "pass_rate": passed / len(checks) if checks else 1.0,
    }
