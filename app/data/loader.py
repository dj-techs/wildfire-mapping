"""Dataset loaders.

All loaders are cached at import time so the working set lives in memory for
the life of the process. This is the right call at the current data scale
(~5K incidents, ~70 county polygons). When the platform grows past ~1M rows
or needs cross-process freshness, swap the bodies for a Parquet-on-S3 read or
a thin DB layer — the call sites in `callbacks/` only depend on the returned
DataFrame / GeoJSON shape.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.config import DATA_DIR


@lru_cache(maxsize=1)
def load_wildfires() -> pd.DataFrame:
    df = pd.read_csv(
        DATA_DIR / "wildfires.csv",
        parse_dates=["discovery_date", "contain_date"],
        dtype={"county_fips": str},
    )
    df["duration_days"] = (df["contain_date"] - df["discovery_date"]).dt.days
    df["month"] = df["discovery_date"].dt.month
    return df


@lru_cache(maxsize=1)
def load_facilities() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "facilities.csv", dtype={"county_fips": str})


@lru_cache(maxsize=1)
def load_counties() -> dict:
    return json.loads((DATA_DIR / "counties.geojson").read_text())


@lru_cache(maxsize=1)
def load_highways() -> dict:
    return json.loads((DATA_DIR / "highways.geojson").read_text())


@lru_cache(maxsize=1)
def load_rail() -> dict:
    return json.loads((DATA_DIR / "rail.geojson").read_text())


def filter_wildfires(
    years: tuple[int, int] | None = None,
    states: list[str] | None = None,
    causes: list[str] | None = None,
    min_acres: float = 0.0,
) -> pd.DataFrame:
    df = load_wildfires()
    if years:
        df = df[(df["fire_year"] >= years[0]) & (df["fire_year"] <= years[1])]
    if states:
        df = df[df["state"].isin(states)]
    if causes:
        df = df[df["cause"].isin(causes)]
    if min_acres > 0:
        df = df[df["fire_size_acres"] >= min_acres]
    return df


def county_aggregates(filtered: pd.DataFrame) -> pd.DataFrame:
    """Rollup used by the choropleth: incidents and total acres per county."""
    agg = (
        filtered.groupby("county_fips")
        .agg(
            incident_count=("incident_id", "count"),
            total_acres=("fire_size_acres", "sum"),
            avg_acres=("fire_size_acres", "mean"),
            structures_destroyed=("structures_destroyed", "sum"),
        )
        .reset_index()
    )
    return agg
