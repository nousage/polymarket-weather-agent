"""Dashboard / state persistence."""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger("polybot.dashboard")
DASH_DIR = os.environ.get("POLYBOT_DATA_DIR", "/polybot-data")


def _ensure_dir() -> None:
    try:
        os.makedirs(DASH_DIR, exist_ok=True)
    except Exception:
        pass


def record_city_scan(city: str, forecast_high: float, ecmwf: float, icon: float, ukmo: float, gfs: float, model_temps: dict, sky: str, trend: str) -> None:
    try:
        _ensure_dir()
        path = os.path.join(DASH_DIR, "city_scan.ndjson")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "city": city,
                "forecast_high": forecast_high,
                "ecmwf": ecmwf,
                "icon": icon,
                "ukmo": ukmo,
                "gfs": gfs,
                "model_temps": model_temps,
                "sky": sky,
                "trend": trend,
            }) + "\n")
    except Exception:
        logger.exception("record_city_scan failed")
