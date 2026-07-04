"""Tax Updates & Insights API — serves processed tax content to the frontend."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from src.db.tax_queries import (
    get_tax_updates,
    get_tax_deadlines,
    get_tax_tips,
    get_tax_facts,
    get_last_sync_time,
    seed_tax_deadlines,
    seed_tax_tips,
    seed_tax_facts,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tax", tags=["Tax Updates"])


def _ensure_seeded():
    """Seed default tips/facts/deadlines if the tables are empty."""
    try:
        seed_tax_tips()
        seed_tax_facts()
        seed_tax_deadlines()
    except Exception as e:
        logger.warning("Seed check failed (DB may not be ready): %s", e)


@router.get("/insights")
async def get_tax_insights():
    """Get aggregated tax insights: updates, deadlines, tips, and facts."""
    _ensure_seeded()

    try:
        updates = get_tax_updates(limit=8)
    except Exception as e:
        logger.warning("Failed to fetch updates: %s", e)
        updates = []

    try:
        deadlines = get_tax_deadlines()
    except Exception as e:
        logger.warning("Failed to fetch deadlines: %s", e)
        deadlines = []

    try:
        tips = get_tax_tips()
    except Exception as e:
        logger.warning("Failed to fetch tips: %s", e)
        tips = []

    try:
        facts = get_tax_facts()
    except Exception as e:
        logger.warning("Failed to fetch facts: %s", e)
        facts = []

    last_synced = get_last_sync_time()

    return {
        "updates": updates,
        "deadlines": deadlines,
        "tips": tips,
        "facts": facts,
        "last_synced": last_synced,
    }


@router.get("/updates")
async def list_tax_updates(category: str | None = None, limit: int = 20):
    """Get latest tax updates, optionally filtered by category."""
    _ensure_seeded()
    return get_tax_updates(limit=limit, category=category)


@router.get("/deadlines")
async def list_tax_deadlines():
    """Get all active tax deadlines."""
    _ensure_seeded()
    return get_tax_deadlines()


@router.get("/tips")
async def list_tax_tips():
    """Get tax-saving tips."""
    _ensure_seeded()
    return get_tax_tips()


@router.get("/facts")
async def list_tax_facts():
    """Get educational tax facts."""
    _ensure_seeded()
    return get_tax_facts()
