"""
Vercel Serverless Entry Point

This file is the ONLY serverless function needed for Vercel.
It exports the FastAPI app as an ASGI handler.

Vercel's @vercel/python runtime auto-detects the `app` variable
and serves it as a serverless function.

All routes (benchmark, pricing, sync, health) are handled by FastAPI's
internal router — no need for separate files per endpoint.

The built-in APScheduler is disabled because Vercel Cron handles scheduling
by hitting the GET endpoints directly.
"""

import sys
import os

# Disable the in-process scheduler — Vercel Cron handles scheduling
os.environ["DISABLE_SCHEDULER"] = "1"

# Add project root to path so the `app` package is importable
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, PROJECT_ROOT)

# Add backend/src to path so business logic modules (database, providers, etc.) are importable
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend", "src"))

# Import the FastAPI app (Vercel detects the `app` variable automatically)
from app.main import app  # noqa: F401, E402
