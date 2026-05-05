# Wildfire Mapping Platform — Claude Code Guide

This is a Flask + Dash interactive geospatial dashboard for mapping wildfire
incidents and response infrastructure across the western US. It mirrors the
shape of the production project (county heatmaps, facility overlays, layered
maps, filtered drill-down) on a self-contained dummy dataset so the dev loop
runs fully offline.

---

## Repo map

```
app/
  server.py          Flask + Dash entry point. Exports `server` for gunicorn.
  config.py          Env-driven config. Mapbox token optional (falls back to OSM).
  auth.py            Login glue — demo users locally, swap in Cognito for prod.
  data/
    loader.py        CSV / GeoJSON loaders. lru_cache'd at process start.
  components/
    layout.py        Page shell.
    filters.py       Sidebar controls.
    map.py           Plotly figure builder. One trace per layer.
    stats_panel.py   KPIs + supporting charts.
  callbacks/
    map_callbacks.py Single fan-out callback: filters -> map + KPIs + charts.
  assets/styles.css  Custom CSS layered on dash-bootstrap DARKLY.
data/                Dummy CSV + GeoJSON. Regenerate via scripts/.
scripts/             Dev utilities (data gen, future ETL).
infra/               AWS deployment notes + IaC stubs.
tests/               pytest. Currently smoke-level.
```

---

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_dummy_data.py    # only if data/ is empty
python -m app.server                     # http://localhost:8050
```

`MAPBOX_TOKEN` in `.env` enables the Mapbox dark style. Without it, the map
falls back to OpenStreetMap so the app still runs.

---

## Conventions and gotchas

**Data layer is the seam, not the implementation.** `app/data/loader.py`
returns DataFrames and GeoJSON dicts. Callers MUST NOT reach into CSV paths
or assume in-memory storage. When the dataset moves to S3/Parquet or a
database, only `loader.py` changes.

**One callback per output set, not per output.** The single fan-out in
`callbacks/map_callbacks.py` is intentional — filters are cheap and keeping
KPIs/map/charts in one update prevents flicker between mutually consistent
states. Don't split it without measuring first.

**Map figure layering is ordered.** In `components/map.py` the layer add
order is choropleth → highways → rail → facilities → incidents (bottom to
top). New overlays should slot in by visual priority, not by add-time.

**Incident points are capped at 2000.** The `nlargest(2000, ...)` in
`build_figure` keeps the browser responsive. If the underlying data grows
past ~50K filtered rows, consider `Densitymapbox` for the heat layer instead
of scattered points.

**Caches are per-process.** `@lru_cache` on loaders is fine for single-node
dev. Under gunicorn with multiple workers each worker gets its own cache —
that's acceptable today but should move to a shared store (Redis, or a
DataFrame on S3 reloaded on a TTL) before horizontal scaling.

**Auth is a stub.** `app/auth.py` is structured so Cognito drops in via
`_verify_demo_credentials` only. Don't sprinkle Cognito calls elsewhere.

---

## Working with this codebase

- **Adding a new map layer:** use the `add-map-layer` skill.
- **Ingesting a new dataset:** use the `ingest-dataset` skill.
- **Deploying to AWS:** use the `deploy-aws` skill.
- **Domain-specific work:** delegate to the matching agent in `.claude/agents/` —
  `geospatial-specialist`, `dash-frontend`, `data-pipeline`.

When changing a Plotly figure, eyeball the result in the browser — the type
checker won't catch a swapped axis or an off-by-one colorbar tick.

When touching `loader.py`, run `pytest tests/` — the smoke test asserts row
counts and column shapes that the rest of the app depends on.

---

## What this demo deliberately doesn't have

These are out of scope on purpose; the prod project handles them and the demo
references the shape only:
- Real Cognito integration (stubbed)
- DynamoDB session storage (stubbed)
- S3-backed data with TTL refresh (loaders read flat files)
- CI/CD (a starter `.github/workflows/ci.yml` runs lint + tests only)
- CloudFront / EC2 IaC (sketched in `infra/README.md`)
