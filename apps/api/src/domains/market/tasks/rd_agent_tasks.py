"""
Scheduled autonomous factor mining.

Runs the RD-Agent research loop out of band from the API: propose a factor, backtest
it, and persist it only if it clears the deployment gate in `config/config.yaml`.

This lives in a Celery worker rather than inside the async overnight pipeline on
purpose: `ValidationUnit.evaluate_factor()` drives its own event loops
(`asyncio.run` plus the loop `BacktestEngine.simulate_trades` creates), which raises
"cannot be called from a running event loop" if invoked from async code.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from tasks.celery_app import celery_app
from storage.database import get_db_session
from research.validation_unit import ValidationUnit, FactorSandboxError

logger = logging.getLogger(__name__)


def _validation_config() -> Dict[str, Any]:
    """Pull the `research.rd_agent.validation` block out of the shared YAML config."""
    from api.dependencies import load_config

    config = load_config() or {}
    research = config.get("research", {}) or {}
    rd_agent = research.get("rd_agent", {}) or {}
    if not rd_agent.get("enabled", True):
        return {}
    return rd_agent.get("validation", {}) or {}


@celery_app.task(bind=True, name="tasks.rd_agent_tasks.run_autonomous_mining_cycle")
def run_autonomous_mining_cycle(self, cycles: int = 3) -> Dict[str, Any]:
    """
    Run `cycles` independent propose -> validate -> deploy iterations.

    Each cycle is independent: a factor that fails the gate is discarded and the next
    proposal is attempted. Returns a summary of what was proposed and what deployed;
    never raises for a factor that merely fails validation, since that is the normal
    outcome and must not fail the scheduled job.
    """
    config = _validation_config()
    if not config:
        logger.warning("RD-Agent mining is disabled in config; skipping this cycle.")
        return {"enabled": False, "cycles": 0, "proposed": [], "deployed": []}

    unit = ValidationUnit(config)
    proposed: List[Dict[str, Any]] = []
    deployed: List[Dict[str, Any]] = []

    logger.info(
        f"Starting autonomous mining cycle: {cycles} proposal(s), "
        f"gate IC>{unit.ic_gate} win_rate>{unit.win_rate_gate} "
        f"on >= {unit.min_trades} trades."
    )

    for i in range(1, cycles + 1):
        logger.info(f"--- mining iteration {i}/{cycles} ---")
        try:
            with get_db_session() as session:
                result = unit.run_research_iteration(session)
        except Exception as exc:  # API outage, data outage, unexpected bug
            logger.exception(f"Mining iteration {i} failed: {exc}")
            proposed.append({"cycle": i, "error": str(exc)})
            continue

        entry = {
            "cycle": i,
            "name": result.get("name"),
            "source": result.get("source"),
            "deployed": result.get("deployed", False),
            "error": result.get("error"),
        }
        metrics = result.get("metrics") or {}
        if metrics:
            entry["information_coefficient"] = metrics.get("information_coefficient")
            entry["win_rate"] = metrics.get("win_rate")
            entry["total_trades"] = metrics.get("total_trades")

        proposed.append(entry)
        if result.get("deployed"):
            deployed.append({"name": result.get("name"), "id": result.get("factor_id")})
            logger.info(f"Deployed factor '{result.get('name')}' (id={result.get('factor_id')}).")
        else:
            logger.info(f"Factor '{result.get('name')}' did not clear the gate.")

    summary = {
        "enabled": True,
        "cycles": cycles,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "proposed": proposed,
        "deployed": deployed,
        "deployed_count": len(deployed),
    }
    logger.info(
        f"Mining cycle complete: {len(proposed)} proposed, {len(deployed)} deployed."
    )
    return summary


__all__ = ["run_autonomous_mining_cycle", "FactorSandboxError"]
