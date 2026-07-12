"""Liquidity sniffer / best-token selector."""
from __future__ import annotations

import logging
import os
from typing import List, Optional

import httpx

logger = logging.getLogger("polybot.liquidity_sniffer")
CLOB_BASE = os.environ.get("CLOB_URL", "https://poly-proxy.elvischemoiywo.workers.dev/clob")


def pick_best_token_for_liquidity(condition_id: str, token_ids: List[str]) -> (Optional[str], Optional[str]):
    if not token_ids:
        return None, "no token ids"
    best = None
    best_score = -1
    err = None
    for tok in token_ids:
        score = 0.0
        try:
            with httpx.Client(timeout=httpx.Timeout(10)) as c:
                r = c.get(f"{CLOB_BASE}/book", params={"token_id": tok})
                r.raise_for_status()
                data = r.json()
                bids = data.get("bids", [])
                asks = data.get("asks", [])
                if bids:
                    score += float(bids[0][0]) * float(bids[0][1])
                if asks:
                    score += float(asks[0][0]) * float(asks[0][1])
        except Exception as e:
            err = str(e)
            continue
        if score > best_score:
            best_score = score
            best = tok
    return best, err
