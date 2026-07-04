"""Background scheduler — periodically fetches official sources and stores results.

Uses APScheduler to run the fetch→summarize→store pipeline on a configurable
interval (default: every 8 hours).
"""

from __future__ import annotations

import asyncio
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.providers import get_providers, RawUpdate
from src.summarizer import summarize_update, ProcessedUpdate
from src.db.tax_queries import (
    upsert_tax_update,
    start_sync_log,
    complete_sync_log,
    seed_tax_deadlines,
    seed_tax_tips,
    seed_tax_facts,
)

logger = logging.getLogger(__name__)

# Sync interval in hours — configurable via env var
SYNC_INTERVAL_HOURS = int(os.environ.get("TAX_SYNC_INTERVAL_HOURS", "8"))

scheduler = AsyncIOScheduler()


async def run_sync() -> None:
    """Run a full fetch→summarize→store cycle across all providers."""
    logger.info("Tax sync: starting scheduled run...")
    sync_id = start_sync_log()
    sources_checked = 0
    updates_found = 0
    updates_new = 0

    try:
        # Ensure seed data exists
        seed_tax_tips()
        seed_tax_facts()
        seed_tax_deadlines()

        # Fetch from all registered providers
        providers = get_providers()
        sources_checked = len(providers)

        for provider in providers:
            logger.info("Tax sync: fetching from %s...", provider.label)
            try:
                raw_updates: list[RawUpdate] = await provider.fetch()
                updates_found += len(raw_updates)
                logger.info("Tax sync: %s returned %d items", provider.label, len(raw_updates))

                # Summarize and store each update
                for raw in raw_updates:
                    try:
                        processed: ProcessedUpdate = summarize_update(raw)
                        upsert_tax_update(
                            title=processed.title,
                            summary_short=processed.summary_short,
                            what_changed=processed.what_changed,
                            who_affected=processed.who_affected,
                            action_required=processed.action_required,
                            category=processed.category,
                            effective_date=processed.effective_date,
                            published_date=processed.published_date,
                            source=processed.source,
                            source_url=processed.source_url,
                            raw_content=processed.raw_content,
                        )
                        updates_new += 1
                    except Exception as e:
                        logger.warning("Tax sync: failed to process item '%s': %s",
                                       raw.title[:60] if raw.title else "unknown", e)

            except Exception as e:
                logger.warning("Tax sync: provider %s failed: %s", provider.label, e)

        complete_sync_log(sync_id, sources_checked, updates_found, updates_new)
        logger.info("Tax sync: complete — %d sources, %d found, %d new/updated",
                    sources_checked, updates_found, updates_new)

    except Exception as e:
        logger.error("Tax sync: fatal error: %s", e)
        complete_sync_log(sync_id, sources_checked, updates_found, updates_new, error=str(e))


def start_scheduler():
    """Start the APScheduler for periodic tax data syncing."""
    scheduler.add_job(
        run_sync,
        trigger=IntervalTrigger(hours=SYNC_INTERVAL_HOURS),
        id="tax_sync_job",
        name="Tax Updates Sync",
        replace_existing=True,
        # Jitter to avoid thundering herd
        misfire_grace_time=900,  # 15 min
    )
    scheduler.start()
    logger.info("Tax sync scheduler started (every %d hours)", SYNC_INTERVAL_HOURS)

    # Also run an initial sync after a short delay (let the app finish starting)
    scheduler.add_job(
        run_sync,
        trigger=None,  # Run once after delay
        id="tax_sync_initial",
        name="Tax Updates Initial Sync",
        run_date=None,  # Will be set below
    )
    # Schedule initial sync 60 seconds after startup
    import asyncio as _asyncio
    try:
        loop = _asyncio.get_running_loop()
        loop.call_later(60, lambda: _asyncio.ensure_future(run_sync()))
    except RuntimeError:
        pass  # No running loop yet, skip initial sync


def stop_scheduler():
    """Shut down the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Tax sync scheduler stopped.")
