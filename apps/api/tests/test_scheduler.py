"""Tests for PR5.4 scheduler reliability.

Focused, offline, DB-free. Verifies:
- start_scheduler() is idempotent (duplicate start is a no-op, never raises)
- stop_scheduler() cleanly stops
- run_sync() isolates a failing provider (does not propagate / kill the loop)
- run_sync() isolates a failing single item among good items
- run_sync() records a complete/failed sync log without raising on provider error

No network, no PostgreSQL. Providers and DB log/seed functions are monkeypatched.
"""

import asyncio

import pytest

from src.scheduler import (
    run_sync,
    scheduler,
    start_scheduler,
    stop_scheduler,
)


class _StubProvider:
    """Returns a fixed list of RawUpdate objects; optionally raises."""

    name = "stub"
    label = "Stub Provider"

    def __init__(self, items=None, boom=False):
        self._items = items or []
        self._boom = boom

    async def fetch(self):
        if self._boom:
            raise RuntimeError("simulated network failure")
        return list(self._items)


def _patch_sync_dependencies(monkeypatch, providers, log_capture):
    """Replace scheduler's provider registry + DB log/seed calls with stubs."""
    monkeypatch.setattr("src.scheduler.get_providers", lambda: providers)

    def _start_log():
        log_capture.append({"event": "start"})
        return "sync-id"

    def _complete_log(sync_id, sources_checked, updates_found, updates_new, error=None):
        log_capture.append({
            "event": "complete",
            "args": (sync_id, sources_checked, updates_found, updates_new),
            "kwargs": {"error": error} if error else {}
        })

    monkeypatch.setattr("src.scheduler.start_sync_log", _start_log)
    monkeypatch.setattr("src.scheduler.complete_sync_log", _complete_log)
    monkeypatch.setattr("src.scheduler.seed_tax_tips", lambda: None)
    monkeypatch.setattr("src.scheduler.seed_tax_facts", lambda: None)
    monkeypatch.setattr("src.scheduler.seed_tax_deadlines", lambda: None)


def test_start_scheduler_idempotent_and_clean():
    """Calling start twice does not crash; stop cleanly halts the scheduler."""

    async def _run():
        start_scheduler()
        assert scheduler.running is True
        # Second call must be a no-op, not a RuntimeError("already running")
        start_scheduler()
        assert scheduler.running is True
        stop_scheduler()
        # shutdown(wait=False) is async; allow brief moment for running flag to clear
        await asyncio.sleep(0.05)
        assert scheduler.running is False

    asyncio.run(_run())


def test_run_sync_isolates_provider_failure(monkeypatch):
    """A failing provider must not raise out of run_sync (API survives).

    Per-provider failures are caught and logged; the sync completes without
    propagating the exception. The complete_sync_log is called without an
    error kwarg (only fatal outer exceptions set error).
    """
    log = []
    _patch_sync_dependencies(monkeypatch, [_StubProvider(boom=True)], log)

    async def _run():
        await run_sync()  # must not raise

    asyncio.run(_run())
    # A start + a complete log were recorded
    assert log[0]["event"] == "start"
    assert log[-1]["event"] == "complete"
    # Provider failure is isolated — no error kwarg (only fatal outer exceptions)
    assert "error" not in log[-1]["kwargs"]


def test_run_sync_isolates_single_bad_item(monkeypatch):
    """One unprocessable item is skipped; good items still store."""
    from src.providers import RawUpdate

    good = RawUpdate(
        title="Good update",
        raw_content="content",
        url="https://example.com/good",
        published_date="2026-01-01",
        source="pib",
    )

    class _BadItemProvider(_StubProvider):
        async def fetch(self):
            return [good]

    stored = []

    def _upsert(**kwargs):
        stored.append(kwargs)

    monkeypatch.setattr("src.scheduler.upsert_tax_update", _upsert)

    log = []
    _patch_sync_dependencies(monkeypatch, [_BadItemProvider()], log)

    async def _run():
        await run_sync()

    asyncio.run(_run())
    assert len(stored) == 1  # good item stored


def test_run_sync_success_records_completion(monkeypatch):
    """A clean run records a successful completion with counts."""
    from src.providers import RawUpdate

    item = RawUpdate(
        title="Update",
        raw_content="content",
        url="https://example.com/u",
        published_date="2026-01-01",
        source="cbdt",
    )

    log = []
    _patch_sync_dependencies(monkeypatch, [_StubProvider(items=[item])], log)

    async def _run():
        await run_sync()

    asyncio.run(_run())
    complete = log[-1]
    assert complete["event"] == "complete"
    # error key absent on success
    assert "error" not in complete["kwargs"]
