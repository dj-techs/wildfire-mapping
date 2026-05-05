"""Map figure builder.

Composes a single Plotly figure with optional layers stacked in this order
(bottom -> top): choropleth, highways, rail, facilities, incident points.
The caller passes a `layers` set so a layer can be turned off without
re-fetching data.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from app.config import Config
from app.data.loader import (
    county_aggregates,
    load_counties,
    load_facilities,
    load_highways,
    load_rail,
)

METRIC_LABELS = {
    "incident_count": "Incidents",
    "total_acres": "Acres burned",
    "structures_destroyed": "Structures destroyed",
}

FAC_COLORS = {
    "Fire Station": "#3b82f6",
    "Air Tanker Base": "#f59e0b",
    "Supply Depot": "#10b981",
    "Helibase": "#a855f7",
    "Incident Command Post": "#ef4444",
}


def build_figure(
    filtered_fires: pd.DataFrame,
    layers: set[str],
    metric: str = "incident_count",
) -> go.Figure:
    fig = go.Figure()

    if "choropleth" in layers:
        agg = county_aggregates(filtered_fires)
        counties = load_counties()
        fig.add_trace(go.Choroplethmapbox(
            geojson=counties,
            locations=agg["county_fips"],
            z=agg[metric],
            featureidkey="properties.fips",
            colorscale="Inferno",
            marker_opacity=0.55,
            marker_line_width=0.3,
            marker_line_color="#222",
            colorbar=dict(title=METRIC_LABELS.get(metric, metric), thickness=12, len=0.5),
            hovertemplate="<b>%{location}</b><br>" + METRIC_LABELS.get(metric, metric) + ": %{z:,.0f}<extra></extra>",
            name="Counties",
        ))

    if "highways" in layers:
        for feat in load_highways()["features"]:
            lons, lats = zip(*feat["geometry"]["coordinates"])
            fig.add_trace(go.Scattermapbox(
                lon=lons, lat=lats, mode="lines",
                line=dict(width=2, color="#9ca3af"),
                name=feat["properties"]["route"],
                hoverinfo="name",
                showlegend=False,
            ))

    if "rail" in layers:
        for feat in load_rail()["features"]:
            lons, lats = zip(*feat["geometry"]["coordinates"])
            fig.add_trace(go.Scattermapbox(
                lon=lons, lat=lats, mode="lines",
                line=dict(width=2, color="#fbbf24"),
                name=feat["properties"]["name"],
                hoverinfo="name",
                showlegend=False,
            ))

    if "facilities" in layers:
        fac = load_facilities()
        fac = fac[fac["state"].isin(filtered_fires["state"].unique())] if not filtered_fires.empty else fac
        for ftype, color in FAC_COLORS.items():
            sub = fac[fac["type"] == ftype]
            if sub.empty:
                continue
            fig.add_trace(go.Scattermapbox(
                lon=sub["longitude"], lat=sub["latitude"],
                mode="markers",
                marker=dict(size=9, color=color, opacity=0.85),
                name=ftype,
                customdata=sub[["name", "capacity_personnel"]].values,
                hovertemplate="<b>%{customdata[0]}</b><br>Capacity: %{customdata[1]}<extra></extra>",
            ))

    if "incidents" in layers and not filtered_fires.empty:
        # Cap at 2K points for browser performance; sort so largest fires win.
        sample = filtered_fires.nlargest(2000, "fire_size_acres")
        fig.add_trace(go.Scattermapbox(
            lon=sample["longitude"], lat=sample["latitude"],
            mode="markers",
            marker=dict(
                size=(sample["fire_size_acres"].clip(1, 50000) ** 0.35) + 3,
                color=sample["fire_size_acres"],
                colorscale="YlOrRd",
                opacity=0.7,
                showscale=False,
            ),
            customdata=sample[["incident_name", "fire_size_acres", "cause", "discovery_date"]].astype(str).values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Acres: %{customdata[1]}<br>"
                "Cause: %{customdata[2]}<br>"
                "Discovered: %{customdata[3]}<extra></extra>"
            ),
            name="Fire incidents",
        ))

    fig.update_layout(
        mapbox=dict(
            accesstoken=Config.MAPBOX_TOKEN or None,
            style=Config.MAP_STYLE,
            center=dict(lat=42.5, lon=-118.0),
            zoom=4.2,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#1f2937",
        font=dict(color="#e5e7eb"),
        legend=dict(bgcolor="rgba(31,41,55,0.7)", bordercolor="#374151", borderwidth=1, x=0, y=1),
        uirevision="keep-pan",
    )
    return fig
