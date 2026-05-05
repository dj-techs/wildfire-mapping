# Wildfire Mapping Platform

Interactive Flask + Dash dashboard mapping ~5,000 western US wildfire
incidents and ~220 response facilities across ~70 counties, with toggleable
overlays for highways, rail corridors, and a county-level heatmap.

Demoable proxy for an existing regional infrastructure mapping platform —
same shape (Flask + Dash + Plotly + Mapbox, county heatmaps, geospatial
overlays, CSV/GeoJSON ingestion, AWS deploy target), self-contained dummy
dataset.

## Screenshot of features

- **County choropleth** — incidents, total acres, or structures destroyed
- **Fire incident scatter** — sized + colored by acres burned, with hover detail
- **Facility overlay** — fire stations, air tanker bases, supply depots, helibases, ICPs
- **Linear overlays** — interstates and major rail corridors
- **Filters** — year range, state, cause, minimum size
- **KPIs + supporting charts** — yearly trend, cause breakdown
- **Auth shell** — login page, demo users, Cognito drop-in seam

## Quick start

```bash
git clone <this-repo> wildfire-mapping
cd wildfire-mapping

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python scripts/generate_dummy_data.py   # ~5K fires, 70 counties, 220 facilities
python -m app.server                    # http://localhost:8050
```

The app runs without a Mapbox token (falls back to OpenStreetMap tiles).
For the Mapbox dark style, copy `.env.example` → `.env` and set
`MAPBOX_TOKEN`.

## Running tests

```bash
pytest -q
```

## Trying the auth flow

```bash
AUTH_DISABLED=false python -m app.server
# Visit http://localhost:8050 → /login
# Demo: demo@example.com / demo  (or admin@example.com / demo)
```

## Project layout

```
app/
  server.py          Flask + Dash entry point. Exports `server` for gunicorn.
  config.py          Env-driven config.
  auth.py            Demo login. Cognito-ready seam.
  data/loader.py     CSV + GeoJSON loaders (lru_cache'd).
  components/        Layout, sidebar filters, map figure, stats panel.
  callbacks/         Filter → map + KPIs + charts wiring.
  assets/styles.css  Dark theme polish.
data/                Generated CSV + GeoJSON.
scripts/             Data generation + future ETL.
tests/               pytest smoke tests.
infra/               AWS deployment notes (EC2 unit, CloudFront, Cognito).
.github/workflows/   CI (install + tests + smoke import).
.claude/             Claude Code agents, skills, slash commands, settings.
CLAUDE.md            Repo guide for Claude Code.
```

## AI-driven workflow

This repo is set up for the [Claude Code](https://docs.claude.com/claude-code)
agent-driven workflow. See [`CLAUDE.md`](CLAUDE.md) for the repo guide and:

- **Agents** (`.claude/agents/`) — domain specialists Claude delegates to:
  - `geospatial-specialist` — Plotly mapbox traces, GeoJSON, spatial joins
  - `dash-frontend` — Dash components, callbacks, layout, CSS
  - `data-pipeline` — loaders, ETL, schema, performance, S3/DB migration
- **Skills** (`.claude/skills/`) — repeatable procedures:
  - `add-map-layer` — add a new visual layer end-to-end
  - `ingest-dataset` — bring in a new CSV / GeoJSON / API source
  - `deploy-aws` — production deploy + rollback runbook
- **Slash commands** (`.claude/commands/`):
  - `/dev` — boot the dev server
  - `/regen-data` — regenerate dummy datasets
- **Settings** (`.claude/settings.json`) — sensible permissions allowlist
  (read-only commands auto-approved; `aws`, `git push`, `rm` require ask).

## Production / AWS deployment

See [`infra/README.md`](infra/README.md) for the EC2 systemd unit, CloudFront
configuration, Cognito wiring steps, and DynamoDB table shapes. The data
loaders read flat files today; the migration path to S3 + Parquet (and
later DuckDB or PostGIS) is documented in `.claude/agents/data-pipeline.md`.

## Dataset notes

The dummy data is structured to mirror the
[NIFC Wildland Fire Incident Locations](https://data-nifc.opendata.arcgis.com/)
schema closely enough that swapping in the real public dataset should mean
only a column-rename pass in `loader.py`. The county polygons are a
stylized grid covering CA / OR / WA / NV / ID / MT — replace with US Census
TIGER county shapefiles for production.
