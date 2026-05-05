"""Smoke tests — guard the data shape that the rest of the app depends on."""
from __future__ import annotations

import pandas as pd

from app.data.loader import (
    county_aggregates,
    filter_wildfires,
    load_counties,
    load_facilities,
    load_highways,
    load_rail,
    load_wildfires,
)


REQUIRED_FIRE_COLS = {
    "incident_id", "fire_year", "state", "county_fips",
    "latitude", "longitude", "fire_size_acres", "cause",
    "structures_destroyed", "discovery_date", "contain_date",
}


def test_wildfires_load():
    df = load_wildfires()
    assert len(df) > 1000
    assert REQUIRED_FIRE_COLS.issubset(df.columns)
    # county_fips MUST be string — choropleth join breaks otherwise.
    # (Don't assert dtype: pandas 2.x uses object, 3.x uses StringDtype.)
    assert isinstance(df["county_fips"].iloc[0], str)


def test_facilities_load():
    df = load_facilities()
    assert len(df) > 0
    assert {"facility_id", "type", "latitude", "longitude"}.issubset(df.columns)


def test_geojson_loads():
    for loader in (load_counties, load_highways, load_rail):
        gj = loader()
        assert gj["type"] == "FeatureCollection"
        assert len(gj["features"]) > 0


def test_filter_combinations():
    full = load_wildfires()
    sub = filter_wildfires(years=(2020, 2022), states=["CA"], min_acres=100)
    assert len(sub) < len(full)
    assert sub["fire_year"].between(2020, 2022).all()
    assert (sub["state"] == "CA").all()
    assert (sub["fire_size_acres"] >= 100).all()


def test_county_aggregates_shape():
    agg = county_aggregates(load_wildfires())
    assert {"county_fips", "incident_count", "total_acres"}.issubset(agg.columns)
    assert agg["incident_count"].sum() > 0
