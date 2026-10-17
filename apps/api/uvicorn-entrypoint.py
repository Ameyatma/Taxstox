#!/usr/bin/env python3
"""Uvicorn entrypoint for local development.

Loads environment variables from the repo's `.env` file (gitignored), validates
that the required secrets are present, and starts the FastAPI app. Production
deployments use `deploy_gcp.sh` and set environment variables directly, so this
script is dev-only.

Usage:
    export $(cat .env | xargs)
    python3 uvicorn-entrypoint.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

REQUIRED_VARS = ("DATABASE_URL", "TAXSTOX_JWT_SECRET", "TAXSTOX_ENCRYPTION_KEY")

missing = [v for v in REQUIRED_VARS if not os.environ.get(v)]
if missing:
    print(
        f"ERROR: Missing required environment variables: {', '.join(missing)}\n"
        "Create a .env file (see .env.example) with these values.",
        file=sys.stderr,
    )
    sys.exit(1)

import uvicorn

from src.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        access_log=True,
        log_level="info",
    )