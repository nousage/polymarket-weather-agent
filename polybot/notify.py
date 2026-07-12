"""Notification helpers."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("polybot.notify")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


def notify_trade(summary: dict) -> None:
    if not DISCORD_WEBHOOK_URL:
        logger.debug("No DISCORD_WEBHOOK_URL set - skipping embed")
        return
    try:
        with httpx.Client(timeout=httpx.Timeout(15)) as c:
            c.post(DISCORD_WEBHOOK_URL, json={"content": json.dumps(summary)[:1900]})
    except Exception:
        logger.exception("notify failed")


def notify_error(message: str) -> None:
    logger.error("NOTIFY: %s", message)
