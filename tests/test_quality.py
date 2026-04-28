"""Tests des expectations Great Expectations-style."""

import pandas as pd
import pytest

from src.quality.expectations import (
    expect_columns_exist,
    expect_in_range,
    expect_no_nulls,
    expect_unique,
    expect_values_in_set,
    summarize,
)


@pytest.mark.unit
def test_columns_exist_passes():
    df = pd.DataFrame({"a": [1], "b": [2]})
    r = expect_columns_exist(df, ["a", "b"])
    assert r.passed


@pytest.mark.unit
def test_columns_exist_fails():
    df = pd.DataFrame({"a": [1]})
    r = expect_columns_exist(df, ["a", "b"])
    assert not r.passed


@pytest.mark.unit
def test_no_nulls_with_threshold():
    df = pd.DataFrame({"x": [1, 2, None, None, 5]})  # 40% nuls
    assert expect_no_nulls(df, "x", threshold=0.5).passed
    assert not expect_no_nulls(df, "x", threshold=0.1).passed


@pytest.mark.unit
def test_in_range():
    df = pd.DataFrame({"v": [10, 20, 30]})
    assert expect_in_range(df, "v", 0, 100).passed
    assert not expect_in_range(df, "v", 0, 25).passed


@pytest.mark.unit
def test_unique():
    df = pd.DataFrame({"id": [1, 2, 3]})
    assert expect_unique(df, "id").passed
    df2 = pd.DataFrame({"id": [1, 1, 2]})
    assert not expect_unique(df2, "id").passed


@pytest.mark.unit
def test_values_in_set():
    df = pd.DataFrame({"s": ["a", "b", "a"]})
    assert expect_values_in_set(df, "s", {"a", "b"}).passed
    assert not expect_values_in_set(df, "s", {"a"}).passed


@pytest.mark.unit
def test_summarize():
    df = pd.DataFrame({"v": [1, 2]})
    checks = [expect_in_range(df, "v", 0, 5), expect_in_range(df, "v", 10, 20)]
    s = summarize(checks)
    assert s["total"] == 2
    assert s["passed"] == 1
    assert s["pass_rate"] == 0.5
