---
name: ingest-dataset
description: Use when the user wants to add a new dataset (CSV, GeoJSON, Parquet, or remote API) to the platform — extending the data layer beyond the existing wildfires/facilities/counties tables. Triggers: "ingest the X dataset", "load NOAA data", "add a new CSV", "pull from this API".
---

# Ingesting a new dataset

The data layer is the seam: every consumer reads through `app/data/loader.py`.
A new dataset means a new loader function — and ideally a script in
`scripts/` if the data needs preprocessing.

## Decision tree

**Static-ish file** (refreshed manually or weekly):
→ Drop the file in `data/`, write a `load_*` function, done.

**Periodically-refreshed file** (refreshed daily or hourly):
→ Write a `scripts/refresh_<name>.py` that downloads + transforms.
→ Loader still reads from `data/`. Cron the script (or use the
  `engineering:schedule` skill).

**Live API**:
→ Loader hits the API behind a TTL cache. Use `requests` + a manual
  TTL wrapper (lru_cache won't expire) — see pattern below.

**>1M rows**:
→ Convert to Parquet. Don't ship CSVs over a few hundred MB.

## Steps

### 1. Add a preprocessing script (if needed)

`scripts/load_<name>.py`:
```python
"""Fetch <name> from <source>, transform, write to data/<name>.{csv,parquet}.

Run: python scripts/load_<name>.py
"""
from pathlib import Path
import pandas as pd, requests

OUT = Path(__file__).resolve().parents[1] / "data" / "<name>.csv"

def main():
    df = pd.read_csv("https://...")  # or requests.get(...).json()
    df = df.rename(columns={...})
    df.to_csv(OUT, index=False)

if __name__ == "__main__":
    main()
```

### 2. Add the loader

In `app/data/loader.py`:
```python
@lru_cache(maxsize=1)
def load_<name>() -> pd.DataFrame:
    return pd.read_csv(
        DATA_DIR / "<name>.csv",
        parse_dates=[...],          # if any
        dtype={"county_fips": str}, # always str for FIPS!
    )
```

For GeoJSON: `return json.loads((DATA_DIR / "<name>.geojson").read_text())`.

### 3. Document invariants

If the rest of the app relies on specific columns existing, add a comment
to the loader spelling them out. The `data-pipeline` agent file lists the
guaranteed columns for `load_wildfires`; do the same here.

### 4. Add a smoke test

`tests/test_<name>.py`:
```python
def test_<name>_loads():
    from app.data.loader import load_<name>
    df = load_<name>()
    assert len(df) > 0
    assert "<expected_column>" in df.columns
```

### 5. Wire into UI

If this dataset drives a new layer, follow the `add-map-layer` skill.
If it drives a new chart, add to `app/components/stats_panel.py`.
If it adds a new filter axis, add to `app/components/filters.py` and a new
input/argument to `filter_<table>` in `loader.py`.

## TTL cache pattern (for live APIs)

```python
import time
_cache = {"ts": 0, "data": None}
TTL = 300  # seconds

def load_live_thing():
    if time.time() - _cache["ts"] < TTL and _cache["data"] is not None:
        return _cache["data"]
    df = pd.read_json("https://...")
    _cache["data"] = df
    _cache["ts"] = time.time()
    return df
```

## Done when

- [ ] Loader function lives in `loader.py` and is cached
- [ ] Column dtypes are explicit (especially FIPS as string)
- [ ] Smoke test asserts shape + key columns
- [ ] If preprocessing is needed, script is in `scripts/` with run instructions in its docstring
- [ ] No call site outside `loader.py` reads files directly from `data/`
