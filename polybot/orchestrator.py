from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import httpx

from polybot.ensemble import ensemble_forecast
from polybot.atmospheric import atmospheric_correction
from polybot.polymarket import (
    Probabilities,
    calibrate_probabilities,
    find_temperature_markets,
    resolve_market_token,
)
from polybot.clob import submit_trade, build_cofire_trade_args, OrderRoundConfig
from polybot.liquidity_sniffer import pick_best_token_for_liquidity
from polybot.cities import CITY_COORDS, CITY_ALIASES
from polybot.dashboard import record_city_scan, record_bucket_scan, record_ensemble_bucket
from polybot.trade_summary import summarize_trade

logger = logging.getLogger("polybot.orchestrator")

OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"


async def _fetch_open_meteo(city: str, lat: float, lon: float) -> dict[str, Any]:
    params = {
        "latitude": f"{lat:.4f}",
        "longitude": f"{lon:.4f}",
        "current": "wind_direction_10m,wind_speed_10m",
        "hourly": "temperature_2m,dew_point_2m,cloud_cover",
        "timezone": "auto",
        "forecast_days": 1,
        "temperature_unit": "fahrenheit",
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(20)) as client:
        r = await client.get(OPEN_METEO_BASE, params=params, headers={"User-Agent": "polybot/1.0"})
        r.raise_for_status()
        return r.json()


def _compute_features(payload: dict[str, Any]) -> dict[str, float]:
    hourly = payload.get("hourly", {})
    temps = hourly.get("temperature_2m", [])
    dew = hourly.get("dew_point_2m", [])
    cloud = hourly.get("cloud_cover", [])
    forecast_high = float(max(temps)) if temps else 0.0
    wind_speed = 0.0
    wind_dir = 0.0
    current = payload.get("current", {})
    try:
        wind_speed = float(current.get("wind_speed_10m", 0) or 0)
        wind_dir = float(current.get("wind_direction_10m", 0) or 0)
    except (TypeError, ValueError):
        pass
    cloud_avg = float(sum(cloud) / max(len(cloud), 1))
    dew_avg = float(sum(dew) / max(len(dew), 1))
    return {
        "forecast_high": forecast_high,
        "cloud_avg": cloud_avg,
        "dew_avg": dew_avg,
        "wind_speed": wind_speed,
        "wind_dir": wind_dir,
    }


def _scan_city(city: str) -> CityScanResult:
    if city not in CITY_COORDS:
        return CityScanResult(city=city, forecast_high_f=0.0, ecmwf_f=0.0, icon_f=0.0, ukmo_f=0.0, gfs_prob=0.0, calibrated_prob=0.0, edge=None, action="NO_EDGE", market_slug=None, condition_id=None, token_id=None, side=None, price=None, size=None, tx_hash=None, error="unknown city")
    lat, lon = CITY_COORDS[city]
    model_name = "openmeteo"
    payload = {}
    try:
        import anyio
        payload = anyio.run(_fetch_open_meteo, city, lat, lon)
    except Exception as e:
        logger.warning("weather fetch failed for %s: %s", city, e)
        return CityScanResult(city=city, forecast_high_f=0.0, ecmwf_f=0.0, icon_f=0.0, ukmo_f=0.0, gfs_prob=0.0, calibrated_prob=0.0, edge=None, action="NO_EDGE", market_slug=None, condition_id=None, token_id=None, side=None, price=None, size=None, tx_hash=None, error=f"weather fetch failed: {e}")
    feats = _compute_features(payload)
    forecast_high = feats["forecast_high"]
    ens = ensemble_forecast(forecast_high)
    corr = atmospheric_correction(city, forecast_high, ens.ecmwf, feats["cloud_avg"], feats["wind_speed"], feats["dew_avg"])
    ecmwf = corr.corrected_temperature
    series = [ecmwf, corr.icon, corr.ukmo, corr.gfs]
    markets = find_temperature_markets(city)
    if not markets:
        record_city_scan(city, forecast_high, ecmwf, corr.icon, corr.ukmo, corr.gfs, {model_name: forecast_high}, "high", "high agree")
        return CityScanResult(city=city, forecast_high_f=forecast_high, ecmwf_f=ecmwf, icon_f=corr.icon, ukmo_f=corr.ukmo, gfs_prob=0.0, calibrated_prob=0.0, edge=None, action="NO_EDGE", market_slug=None, condition_id=None, token_id=None, side=None, price=None, size=None, tx_hash=None, error="no markets")
    best_threshold, best_market = sorted(markets, key=lambda m: abs(m.threshold_f - ecmwf))[0], sorted(markets, key=lambda m: abs(m.threshold_f - ecmwf))[0]
    raw_prob = prob_from_series(series, best_threshold.threshold_f)
    probs = calibrate_probabilities(city, raw_prob, best_threshold.threshold_f, series)
    edge = probs.yes_probability - (1.0 - float(best_market.best_yes or 0.0))
    action = "NO_EDGE"
    side = None
    size = 0.1
    if edge >= 0.5:
        action = "TRADE"
        side = "BUY"
    elif edge <= -0.5:
        action = "TRADE"
        side = "SELL"
    token_id, liq_error = pick_best_token_for_liquidity(best_market.condition_id, best_market.clob_token_ids)
    if token_id is None:
        action = "NO_EDGE"
        side = None
    price = float(best_market.best_bid or best_market.best_ask or 0.0)
    record_city_scan(city, forecast_high, ecmwf, corr.icon, corr.ukmo, corr.gfs, {model_name: forecast_high}, "high", "high agree")
    record_ensemble_bucket(best_market.condition_id, best_market.question, best_threshold.threshold_label, best_market.clob_token_ids, series, probs.yes_probability)
    record_bucket_scan(best_market.condition_id, best_threshold.threshold_label, probs.yes_probability, best_market.clob_token_ids)
    return CityScanResult(
        city=city,
        forecast_high_f=forecast_high,
        ecmwf_f=ecmwf,
        icon_f=corr.icon,
        ukmo_f=corr.ukmo,
        gfs_prob=probs.yes_probability,
        calibrated_prob=probs.yes_probability,
        edge=edge,
        action=action,
        market_slug=best_market.slug,
        condition_id=best_market.condition_id,
        token_id=token_id,
        side=side,
        price=price,
        size=size,
        tx_hash=None,
        error=liq_error,
    )


async def run_scan() -> ScanSummary:
    summary = ScanSummary()
    for city in CITIES:
        try:
            result = _scan_city(city)
            summary.results.append(result)
        except Exception as exc:
            logger.exception("scan failed for %s", city)
            summary.errors.append(f"{city}:{exc}")
    do_rebalance(summary)
    return summary


def do_rebalance(summary: ScanSummary) -> None:
    from polybot.rebalance import rebalance_portfolio
    rebalance_portfolio(summary)
