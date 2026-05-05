"""Wires sidebar inputs -> map figure + KPIs + supporting charts.

The single fan-out callback is intentional: filters are cheap, and one
callback keeps map / KPIs / charts mutually consistent. If a partial
refresh becomes a perf bottleneck (>250ms), split out the chart updates
into a clientside callback driven by a shared dcc.Store.
"""
from __future__ import annotations

from dash import Input, Output

from app.components.map import build_figure
from app.components.stats_panel import build_cause_chart, build_kpis, build_yearly_chart
from app.data.loader import filter_wildfires


def register_callbacks(app):
    @app.callback(
        Output("map", "figure"),
        Output("kpi-row", "children"),
        Output("yearly-chart", "children"),
        Output("cause-chart", "children"),
        Output("filter-summary", "children"),
        Input("year-range", "value"),
        Input("state-filter", "value"),
        Input("cause-filter", "value"),
        Input("min-acres", "value"),
        Input("layer-toggle", "value"),
        Input("metric", "value"),
    )
    def update_dashboard(years, states, causes, min_acres, layers, metric):
        df = filter_wildfires(
            years=tuple(years) if years else None,
            states=states or None,
            causes=causes or None,
            min_acres=float(min_acres or 0),
        )
        layer_set = set(layers or [])
        fig = build_figure(df, layer_set, metric=metric)
        kpis = build_kpis(df)
        yearly = build_yearly_chart(df)
        cause = build_cause_chart(df)
        summary = f"Showing {len(df):,} of {len(filter_wildfires()):,} incidents"
        return fig, kpis, yearly, cause, summary
