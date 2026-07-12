"""Smart money / flow signals."""
from __future__ import annotations

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger("polybot.smart_money")
GAMMA_BASE = os.environ.get("POLYGAMMA_URL", "https://poly-proxy.elvischemoiywo.workers.dev/gamma")


def smart_money_signal(condition_id: str) -> Optional[float]:
    try:
        with httpx.Client(timeout=httpx.Timeout(10)) as c:
            r = c.get(f"{GAMMA_BASE}/markets", params={"condition_id": condition_id, "limit": 1})
            r.raise_for_status()
            data = r.json()
            if data:
                m = data[0]
                return float(m.get("lastTradePrice") or 0.0)
    except Exception:
        logger.exception("smart money lookup failed")
    return None
