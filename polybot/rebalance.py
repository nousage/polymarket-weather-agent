"""Rebalance / portfolio management."""
from __future__ import annotations

import logging

logger = logging.getLogger("polybot.rebalance")


def rebalance_portfolio(summary) -> None:  # type: ignore[no-untyped-def]
    try:
        trades = [r for r in summary.results if getattr(r, "action", None) == "TRADE"]
        logger.info("rebalance: evaluating %d candidate trades", len(trades))
    except Exception:
        logger.exception("rebalance failed")
