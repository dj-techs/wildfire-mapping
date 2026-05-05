"""Runtime configuration. Reads .env if present, otherwise sensible defaults."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

load_dotenv(ROOT / ".env")


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
    DEBUG = os.getenv("DASH_DEBUG", "true").lower() == "true"

    # Mapbox: if absent, we fall back to the open-source `open-street-map`
    # tile style so the app still renders without an account.
    MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")
    MAP_STYLE = "mapbox://styles/mapbox/dark-v11" if os.getenv("MAPBOX_TOKEN") else "open-street-map"

    # AWS — only consulted by infra/auth code paths.
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    S3_DATA_BUCKET = os.getenv("S3_DATA_BUCKET", "")
    COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")
    COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID", "")
    DDB_SESSIONS_TABLE = os.getenv("DDB_SESSIONS_TABLE", "")

    # Auth bypass for local dev (set false to exercise the login flow).
    AUTH_DISABLED = os.getenv("AUTH_DISABLED", "true").lower() == "true"
