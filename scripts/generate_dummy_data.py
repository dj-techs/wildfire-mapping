"""Generate realistic dummy datasets for the wildfire infrastructure demo.

Produces:
  data/wildfires.csv         - ~5,000 incidents, NIFC-shaped columns
  data/counties.geojson      - ~40 western US county polygons (simplified)
  data/facilities.csv        - ~200 logistics/response facilities
  data/highways.geojson      - sample interstate corridor lines
  data/rail.geojson          - sample rail corridor lines

Run: python scripts/generate_dummy_data.py
"""
from __future__ import annotations

import csv
import json
import math
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# County polygons — a stylized grid covering ~6 western states.
# Real GeoJSON would come from US Census TIGER; this keeps the demo offline.
# ---------------------------------------------------------------------------

STATES = [
    ("CA", "California", 32.5, 42.0, -124.5, -114.0),
    ("OR", "Oregon",     42.0, 46.3, -124.5, -116.5),
    ("WA", "Washington", 45.5, 49.0, -124.8, -117.0),
    ("NV", "Nevada",     35.0, 42.0, -120.0, -114.0),
    ("ID", "Idaho",      42.0, 49.0, -117.2, -111.0),
    ("MT", "Montana",    44.4, 49.0, -116.0, -104.0),
]

COUNTIES: list[dict] = []
fips_counter = 1000

def _square(lon, lat, w, h):
    return [[
        [lon,     lat],
        [lon + w, lat],
        [lon + w, lat + h],
        [lon,     lat + h],
        [lon,     lat],
    ]]

for state_abbr, state_name, lat0, lat1, lon0, lon1 in STATES:
    cols = 4
    rows = 3
    cell_w = (lon1 - lon0) / cols
    cell_h = (lat1 - lat0) / rows
    for r in range(rows):
        for c in range(cols):
            fips_counter += 1
            cx = lon0 + c * cell_w + cell_w / 2
            cy = lat0 + r * cell_h + cell_h / 2
            COUNTIES.append({
                "type": "Feature",
                "properties": {
                    "fips": str(fips_counter),
                    "name": f"{state_name} County {r}{c}",
                    "state": state_abbr,
                    "state_name": state_name,
                    "centroid_lat": cy,
                    "centroid_lon": cx,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": _square(
                        lon0 + c * cell_w,
                        lat0 + r * cell_h,
                        cell_w,
                        cell_h,
                    ),
                },
            })

(OUT / "counties.geojson").write_text(
    json.dumps({"type": "FeatureCollection", "features": COUNTIES}, indent=1)
)
print(f"counties.geojson: {len(COUNTIES)} features")


# ---------------------------------------------------------------------------
# Wildfire incidents — NIFC-shaped, weighted by season + state risk.
# ---------------------------------------------------------------------------

CAUSES = [
    ("Lightning", 0.35),
    ("Human - Equipment", 0.18),
    ("Human - Debris Burning", 0.12),
    ("Human - Campfire", 0.08),
    ("Human - Arson", 0.05),
    ("Powerline", 0.10),
    ("Undetermined", 0.12),
]

STATE_RISK = {"CA": 1.5, "OR": 1.2, "WA": 1.0, "NV": 0.8, "ID": 1.1, "MT": 1.3}

def weighted_choice(pairs):
    r = random.random()
    cum = 0.0
    for value, w in pairs:
        cum += w
        if r <= cum:
            return value
    return pairs[-1][0]

def fire_size_acres():
    # Pareto-ish: most fires small, occasional megafire.
    base = random.expovariate(1 / 50)
    if random.random() < 0.02:
        base *= random.uniform(50, 500)
    return round(base, 1)

def _size_class(acres: float) -> str:
    # NWCG fire size classes A-G.
    if acres < 0.25:   return "A"
    if acres < 10:     return "B"
    if acres < 100:    return "C"
    if acres < 300:    return "D"
    if acres < 1000:   return "E"
    if acres < 5000:   return "F"
    return "G"

rows: list[dict] = []
fire_id = 0
for year in range(2018, 2025):
    for county in COUNTIES:
        state = county["properties"]["state"]
        risk = STATE_RISK[state]
        n_incidents = max(0, int(random.gauss(8 * risk, 4)))
        for _ in range(n_incidents):
            fire_id += 1
            # Cluster in fire season Jun-Oct.
            day_of_year = int(random.gauss(220, 50)) % 365 + 1
            d = date(year, 1, 1) + timedelta(days=day_of_year - 1)
            geom = county["geometry"]["coordinates"][0]
            lon = random.uniform(geom[0][0], geom[2][0])
            lat = random.uniform(geom[0][1], geom[2][1])
            acres = fire_size_acres()
            rows.append({
                "incident_id": f"FIRE-{year}-{fire_id:06d}",
                "incident_name": f"{county['properties']['name'].split()[0]} Fire {fire_id}",
                "discovery_date": d.isoformat(),
                "contain_date": (d + timedelta(days=random.randint(1, 45))).isoformat(),
                "fire_year": year,
                "state": state,
                "county_fips": county["properties"]["fips"],
                "county_name": county["properties"]["name"],
                "latitude": round(lat, 5),
                "longitude": round(lon, 5),
                "fire_size_acres": acres,
                "fire_size_class": _size_class(acres),
                "cause": weighted_choice(CAUSES),
                "structures_destroyed": int(max(0, random.gauss(acres / 200, 5))) if acres > 100 else 0,
                "personnel_assigned": int(max(1, acres / 20 + random.gauss(0, 10))),
            })

with (OUT / "wildfires.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"wildfires.csv: {len(rows)} incidents")


# ---------------------------------------------------------------------------
# Infrastructure — fire stations, air tanker bases, supply depots.
# ---------------------------------------------------------------------------

FAC_TYPES = ["Fire Station", "Air Tanker Base", "Supply Depot", "Helibase", "Incident Command Post"]

facilities = []
for i in range(220):
    county = random.choice(COUNTIES)
    geom = county["geometry"]["coordinates"][0]
    lon = random.uniform(geom[0][0], geom[2][0])
    lat = random.uniform(geom[0][1], geom[2][1])
    facilities.append({
        "facility_id": f"FAC-{i:04d}",
        "name": f"{county['properties']['state']} {random.choice(FAC_TYPES)} {i}",
        "type": random.choice(FAC_TYPES),
        "state": county["properties"]["state"],
        "county_fips": county["properties"]["fips"],
        "latitude": round(lat, 5),
        "longitude": round(lon, 5),
        "capacity_personnel": random.randint(10, 250),
        "active": random.random() > 0.05,
    })

with (OUT / "facilities.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(facilities[0].keys()))
    w.writeheader()
    w.writerows(facilities)
print(f"facilities.csv: {len(facilities)} facilities")


# ---------------------------------------------------------------------------
# Highway + rail overlays — synthetic linestrings.
# ---------------------------------------------------------------------------

def _line(points):
    return {"type": "LineString", "coordinates": points}

highways = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "properties": {"route": "I-5",  "class": "Interstate"},
         "geometry": _line([[-122.4, 32.7], [-122.3, 36.0], [-122.7, 38.6], [-122.8, 45.5], [-122.3, 47.6], [-122.3, 48.9]])},
        {"type": "Feature", "properties": {"route": "I-80", "class": "Interstate"},
         "geometry": _line([[-122.4, 37.8], [-119.8, 39.5], [-115.1, 36.2], [-111.9, 40.8]])},
        {"type": "Feature", "properties": {"route": "I-15", "class": "Interstate"},
         "geometry": _line([[-117.2, 32.7], [-115.1, 36.2], [-112.0, 41.0], [-111.9, 47.0]])},
        {"type": "Feature", "properties": {"route": "I-90", "class": "Interstate"},
         "geometry": _line([[-122.3, 47.6], [-117.4, 47.7], [-112.5, 46.0], [-105.5, 46.8]])},
    ],
}
(OUT / "highways.geojson").write_text(json.dumps(highways))
print(f"highways.geojson: {len(highways['features'])} routes")

rail = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "properties": {"name": "BNSF Northern Transcon", "operator": "BNSF"},
         "geometry": _line([[-122.3, 47.6], [-118.0, 47.7], [-114.0, 47.5], [-108.5, 47.0], [-104.0, 46.9]])},
        {"type": "Feature", "properties": {"name": "UP Overland Route", "operator": "Union Pacific"},
         "geometry": _line([[-122.4, 37.8], [-120.0, 38.6], [-116.0, 40.7], [-111.8, 41.2]])},
        {"type": "Feature", "properties": {"name": "UP Coast Line", "operator": "Union Pacific"},
         "geometry": _line([[-122.4, 37.8], [-121.5, 36.5], [-120.7, 35.4], [-118.2, 33.8]])},
    ],
}
(OUT / "rail.geojson").write_text(json.dumps(rail))
print(f"rail.geojson: {len(rail['features'])} corridors")


print("\nDone. All files in data/")
