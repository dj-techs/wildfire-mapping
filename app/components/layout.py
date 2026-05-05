"""Top-level page layout."""
from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from app.components.filters import build_sidebar


def build_layout() -> html.Div:
    return html.Div(
        className="app-shell",
        children=[
            dcc.Location(id="url"),
            html.Header(
                className="app-header",
                children=[
                    html.Div("🔥 Western US Wildfire & Response Infrastructure", className="brand"),
                    html.Div(id="user-tag", className="user-tag"),
                ],
            ),
            html.Div(
                className="app-body",
                children=[
                    build_sidebar(),
                    html.Main(
                        className="main",
                        children=[
                            html.Div(id="kpi-row", className="kpi-row"),
                            dcc.Loading(
                                dcc.Graph(
                                    id="map",
                                    style={"height": "62vh"},
                                    config={"scrollZoom": True, "displaylogo": False},
                                ),
                                type="default",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col([html.H6("Acres burned by year"), html.Div(id="yearly-chart")], width=6),
                                    dbc.Col([html.H6("Acres burned by cause"), html.Div(id="cause-chart")], width=6),
                                ],
                                className="g-3 mt-2",
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
