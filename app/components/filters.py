"""Sidebar filter controls."""
from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from app.data.loader import load_wildfires


def build_sidebar() -> html.Div:
    df = load_wildfires()
    states = sorted(df["state"].unique())
    causes = sorted(df["cause"].unique())
    yr_min, yr_max = int(df["fire_year"].min()), int(df["fire_year"].max())

    return html.Div(
        className="sidebar",
        children=[
            html.H4("Filters", className="sidebar-title"),

            html.Label("Year range"),
            dcc.RangeSlider(
                id="year-range",
                min=yr_min, max=yr_max, step=1,
                value=[yr_min, yr_max],
                marks={y: str(y) for y in range(yr_min, yr_max + 1)},
                tooltip={"placement": "bottom"},
            ),

            html.Label("States", className="mt-3"),
            dcc.Dropdown(
                id="state-filter",
                options=[{"label": s, "value": s} for s in states],
                value=states,
                multi=True,
            ),

            html.Label("Causes", className="mt-3"),
            dcc.Dropdown(
                id="cause-filter",
                options=[{"label": c, "value": c} for c in causes],
                value=causes,
                multi=True,
            ),

            html.Label("Minimum fire size (acres)", className="mt-3"),
            dcc.Input(
                id="min-acres",
                type="number",
                min=0, value=0, step=10,
                className="form-control",
            ),

            html.H5("Layers", className="mt-4"),
            dcc.Checklist(
                id="layer-toggle",
                options=[
                    {"label": "  County heatmap",  "value": "choropleth"},
                    {"label": "  Fire incidents",  "value": "incidents"},
                    {"label": "  Facilities",      "value": "facilities"},
                    {"label": "  Highways",        "value": "highways"},
                    {"label": "  Rail corridors",  "value": "rail"},
                ],
                value=["choropleth", "incidents", "facilities"],
                labelStyle={"display": "block"},
            ),

            html.H5("Heatmap metric", className="mt-4"),
            dcc.RadioItems(
                id="metric",
                options=[
                    {"label": "  Incident count",       "value": "incident_count"},
                    {"label": "  Total acres burned",   "value": "total_acres"},
                    {"label": "  Structures destroyed", "value": "structures_destroyed"},
                ],
                value="incident_count",
                labelStyle={"display": "block"},
            ),

            html.Div(id="filter-summary", className="text-muted mt-3"),
        ],
    )
