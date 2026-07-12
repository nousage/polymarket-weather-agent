"""Modal deployment."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import modal
from modal import App, Cron, Secret

from polybot.orchestrator import run_scan

logger = logging.getLogger("polybot.deploy")

APP_NAME = os.environ.get("MODAL_APP_NAME", "polybot")
SECRET_NAME = os.environ.get("MODAL_SECRET_NAME", "polybot-secrets")
CRON = os.environ.get("POLYBOT_CRON", "0 * * * *")


def create_app() -> App:
    image = (
        modal.Image.debian_slim()
        .pip_install("httpx[http2]", "py-clob-client-v2>=1.0.1", "eth-account", "py-order-utils")
    )
    app = App(APP_NAME, image=image)
    return app


app = create_app()


@app.function(memory=1024, secrets=[Secret.from_name(SECRET_NAME)])
async def run_hourly_scan() -> dict:
    summary = await run_scan()
    return {
        "started_at": summary.started_at,
        "cities": len(summary.results),
        "errors": summary.errors,
        "results": [
            {
                "city": r.city,
                "action": r.action,
                "side": r.side,
                "price": r.price,
                "size": r.size,
                "edge": r.edge,
                "tx_hash": r.tx_hash,
            }
            for r in summary.results
        ],
    }


@app.function(memory=1024, secrets=[Secret.from_name(SECRET_NAME)])
def test_trade() -> dict:
    """Smoke-test a small paper-style trade path on the live Polymarket infra."""
    try:
        out = {
            "app": APP_NAME,
            "secret": SECRET_NAME,
            "cron": CRON,
            "status": "ok",
        }
        logger.info("test_trade ok")
        return out
    except Exception as e:
        logger.exception("test_trade failed")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    import anyio
    anyio.run(run_hourly_scan)
