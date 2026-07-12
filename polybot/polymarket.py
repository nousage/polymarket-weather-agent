"""Polymarket Gamma/CLOB helpers."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List, Optional

import httpx

GAMMA_BASE = os.environ.get("POLYGAMMA_URL", "https://poly-proxy.elvischemoiywo.workers.dev/gamma")
CLOB_BASE = os.environ.get("CLOB_URL", "https://poly-proxy.elvischemoiywo.workers.dev/clob")


@dataclass
class TemperatureMarket:
    question: str
    condition_id: str
    slug: str
    token_id_yes: str
    token_id_no: str
    threshold_label: str
    threshold_f: float
    best_bid: Optional[float]
    best_ask: Optional[float]
    best_yes: Optional[float]
    clob_token_ids: List[str]


@dataclass
class Probabilities:
    yes_probability: float
    no_probability: float


def _get(path: str, params=None) -> dict:
    with httpx.Client(timeout=httpx.Timeout(20)) as c:
        r = c.get(f"{GAMMA_BASE}{path}", params=params)
        r.raise_for_status()
        return r.json()


def find_temperature_markets(city: str, date_str: Optional[str] = None) -> List[TemperatureMarket]:
    import datetime
    if date_str is None:
        date_str = datetime.date.today().strftime("%B %-d")
    events = _get("/events", params={"active": "true", "closed": "false", "limit": 100, "offset": 0})
    out: List[TemperatureMarket] = []
    for ev in events:
        title = (ev.get("title") or "").lower()
        if city.lower() not in title:
            continue
        for m in ev.get("markets", []):
            q = m.get("question", "")
            if not q.startswith("Will the highest temperature in"):
                continue
            if date_str.lower() not in q.lower():
                continue
            tokens = m.get("clobTokenIds") or "[]"
            try:
                tok = json.loads(tokens)
            except Exception:
                tok = []
            out.append(TemperatureMarket(
                question=q,
                condition_id=m.get("condition_id") or m.get("conditionId") or "",
                slug=m.get("slug", ""),
                token_id_yes=tok[0] if len(tok) > 0 else "",
                token_id_no=tok[1] if len(tok) > 1 else "",
                threshold_label=q,
                threshold_f=0.0,
                best_bid=float(m.get("bestBid") or 0),
                best_ask=float(m.get("bestAsk") or 0),
                best_yes=float(m.get("lastTradePrice") or 0),
                clob_token_ids=tok,
            ))
    return out


def resolve_market_token(condition_id: str, clob_token_ids: List[str], side: str) -> Optional[str]:
    if not clob_token_ids:
        return None
    return clob_token_ids[0] if side.upper() == "BUY" else clob_token_ids[-1]


def calibrate_probabilities(city: str, raw_prob: float, threshold: float, series: list[float]) -> Probabilities:
    return Probabilities(yes_probability=raw_prob, no_probability=max(0.0, 1.0 - raw_prob))
