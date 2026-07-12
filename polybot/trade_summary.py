"""Trade summary helper."""
from __future__ import annotations

from typing import Any


def summarize_trade(result, market) -> dict:  # type: ignore[no-untyped-def]
    return {
        "city": getattr(result, "city", None),
        "action": getattr(result, "action", None),
        "side": getattr(result, "side", None),
        "price": getattr(result, "price", None),
        "size": getattr(result, "size", None),
        "token_id": getattr(result, "token_id", None),
        "condition_id": getattr(result, "condition_id", None),
        "tx_hash": getattr(result, "tx_hash", None),
        "error": getattr(result, "error", None),
        "question": getattr(market, "question", None),
    }
