"""KPI cards and a small per-cause chart shown beneath the map."""
from __future__ import annotations

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import dcc, html


def _kpi(label: str, value: str, sub: str = "") -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            html.Div(label, className="kpi-label"),
            html.Div(value, className="kpi-value"),
            html.Div(sub, className="kpi-sub") if sub else None,
        ]),
        className="kpi-card",
    )


def build_kpis(filtered: pd.DataFrame) -> dbc.Row:
    if filtered.empty:
        return dbc.Row([_kpi("No data", "—")])

    total = len(filtered)
    acres = filtered["fire_size_acres"].sum()
    structures = int(filtered["structures_destroyed"].sum())
    biggest = filtered.nlargest(1, "fire_size_acres").iloc[0]

    return dbc.Row(
        [
            dbc.Col(_kpi("Incidents", f"{total:,}"), width=3),
            dbc.Col(_kpi("Acres burned", f"{acres:,.0f}"), width=3),
            dbc.Col(_kpi("Structures destroyed", f"{structures:,}"), width=3),
            dbc.Col(_kpi(
                "Largest fire",
                f"{biggest['fire_size_acres']:,.0f} ac",
                sub=f"{biggest['incident_name']} ({biggest['state']})",
            ), width=3),
        ],
        className="g-2",
    )


def build_cause_chart(filtered: pd.DataFrame) -> dcc.Graph:
    if filtered.empty:
        return dcc.Graph(figure={})
    by_cause = (
        filtered.groupby("cause")
        .agg(incidents=("incident_id", "count"), acres=("fire_size_acres", "sum"))
        .reset_index()
        .sort_values("acres", ascending=True)
    )
    fig = px.bar(
        by_cause, x="acres", y="cause",
        orientation="h", labels={"acres": "Acres burned", "cause": ""},
        color="acres", color_continuous_scale="Inferno",
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="#1f2937", plot_bgcolor="#1f2937",
        font=dict(color="#e5e7eb"),
        height=240, coloraxis_showscale=False,
    )
    return dcc.Graph(figure=fig, config={"displayModeBar": False})


def build_yearly_chart(filtered: pd.DataFrame) -> dcc.Graph:
    if filtered.empty:
        return dcc.Graph(figure={})
    by_year = (
        filtered.groupby("fire_year")
        .agg(incidents=("incident_id", "count"), acres=("fire_size_acres", "sum"))
        .reset_index()
    )
    fig = px.line(
        by_year, x="fire_year", y="acres",
        markers=True, labels={"fire_year": "Year", "acres": "Acres burned"},
    )
    fig.update_traces(line_color="#f59e0b", marker_color="#f59e0b")
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="#1f2937", plot_bgcolor="#1f2937",
        font=dict(color="#e5e7eb"),
        xaxis=dict(gridcolor="#374151"), yaxis=dict(gridcolor="#374151"),
        height=240,
    )
    return dcc.Graph(figure=fig, config={"displayModeBar": False})
