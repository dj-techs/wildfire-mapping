---
name: add-map-layer
description: Use when the user wants to add a new visual layer to the map — a new overlay (polygons, points, lines), a new heatmap variant, or a new toggleable trace. Triggers: "add a layer for X", "show evacuation zones", "overlay air quality", "add a points layer for hospitals".
---

# Adding a new map layer

This codebase has a single figure builder (`app/components/map.py`). Layers
are added as Plotly traces conditioned on a `layers` set. The toggle UI
already exists in the sidebar — you just plug in.

## Steps

### 1. Add a loader (if the layer needs new data)

Edit `app/data/loader.py`. Follow the pattern of `load_facilities()`:
- One function per dataset.
- `@lru_cache(maxsize=1)`.
- Return a DataFrame for tabular, a dict for GeoJSON.
- Cast any `*_fips` columns to string explicitly.

### 2. Wire the toggle

Edit `app/components/filters.py`, in the `layer-toggle` Checklist:
```python
{"label": "  My new layer", "value": "my-layer-id"},
```
Append (don't insert) so the default-on layers stay first.

### 3. Add the trace block

Edit `app/components/map.py`, inside `build_figure`. Add a block in the
correct visual order (bottom→top: choropleth, highways, rail, facilities,
incidents). Example for a new points layer:

```python
if "my-layer-id" in layers:
    df = load_my_layer()
    fig.add_trace(go.Scattermapbox(
        lon=df["longitude"], lat=df["latitude"],
        mode="markers",
        marker=dict(size=8, color="#ec4899"),
        name="My layer",
        hovertemplate="<b>%{customdata[0]}</b><extra></extra>",
        customdata=df[["name"]].values,
    ))
```

For polygons, use `go.Choroplethmapbox` with `geojson=` and
`featureidkey="properties.<your_join_key>"`.

For lines, follow the `highways` block — one trace per feature with
`mode="lines"`.

### 4. Update the legend if the layer is on by default

If the layer is added to the default `value=[...]` of `layer-toggle`,
verify it appears correctly in the legend and doesn't crowd existing ones.

### 5. Smoke check

```bash
source .venv/bin/activate
python -m app.server
# Open http://localhost:8050, toggle the new layer on/off,
# verify it renders, check hover tooltip, check it stacks correctly.
```

## Done when

- [ ] Layer toggles on/off without a page reload
- [ ] No console errors in the browser
- [ ] Hover tooltip shows useful info (not raw column names)
- [ ] Layer stacks visually correct against existing ones
- [ ] If the layer queries new data, `load_*` is cached and returns the right shape
