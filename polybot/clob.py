"""CLOB trade execution via CLOB v2 / Relayer."""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

import httpx
from eth_account import Account
from eth_account.messages import encode_defunct

logger = logging.getLogger("polybot.clob")

CLOB_API_KEY = os.environ["CLOB_API_KEY"]
CLOB_SECRET = os.environ["CLOB_SECRET"]
CLOB_PASS_PHRASE = os.environ["CLOB_PASS_PHRASE"]
CLOB_BASE = os.environ.get("CLOB_URL", "https://poly-proxy.elvischemoiywo.workers.dev/clob")
RELAYER_BASE = os.environ.get("RELAYER_URL", "https://relayer-v2.polymarket.com")
PROXY_WALLET = os.environ.get("PROXY_WALLET", "0xAB2ddbd4BF2c8a256584Ca6c4eCa7D51810263CA")
SIGNATURE_TYPE = int(os.environ.get("SIGNATURE_TYPE", "3"))
RELAYER_API_KEY = os.environ["RELAYER_API_KEY"]
RELAYER_API_KEY_ADDRESS = os.environ["RELAYER_API_KEY_ADDRESS"]
PK = os.environ["PK"]
FUNDER = os.environ["FUNDER"]


@dataclass(frozen=True)
class OrderRoundConfig:
    price: int = 3
    size: int = 2
    amount: int = 5


def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "CLOB-API-KEY": CLOB_API_KEY,
    }


def _auth_headers() -> dict:
    ts = str(int(time.time() * 1000))
    return {
        "CLOB-API-KEY": CLOB_API_KEY,
        "CLOB-TIMESTAMP": ts,
        "CLOB-PASSPHRASE": CLOB_PASS_PHRASE,
        "CLOB-SIGNATURE": "",
    }


def _sign(payload: str) -> str:
    secret = CLOB_SECRET
    acct = Account.from_key(secret)
    signed = acct.sign_message(encode_defunct(text=payload))
    return signed.signature.to_0x_hex()


def build_cofire_trade_args(token_id: str, side: str, price: float, size: float, round_config: OrderRoundConfig | None = None) -> dict:
    rc = round_config or OrderRoundConfig()
    price_scaled = int(round(float(price), rc.price) * 10**rc.price)
    size_scaled = int(round(float(size), rc.size) * 10**rc.size)
    amount_scaled = int(round(float(price) * float(size), rc.amount) * 10**rc.amount)
    return {
        "token_id": str(token_id),
        "side": side.upper(),
        "price": str(price),
        "size": str(size),
        "price_scaled": str(price_scaled),
        "size_scaled": str(size_scaled),
        "amount_scaled": str(amount_scaled),
    }


def _relayer_order(side: str, token_id: str, price: float, size: float, rc: OrderRoundConfig) -> dict:
    tick = 10 ** (-rc.price)
    price_scaled = int(round(price / tick)) if rc.price > 0 else int(round(price))
    size_scaled = int(round(size, rc.size) * 10**rc.size)
    amount_scaled = int(round(price * size, rc.amount) * 10**rc.amount)
    maker_amount = amount_scaled
    taker_amount = size_scaled
    salt = int(time.time() * 1000)
    order = {
        "side": side.upper(),
        "token_id": str(token_id),
        "maker_amount": str(maker_amount),
        "taker_amount": str(taker_amount),
        "salt": str(salt),
        "fee_rate_bps": "0",
        "nonce": "0",
        "expiration": "0",
        "taker": "0x0000000000000000000000000000000000000000",
        "signature_type": str(SIGNATURE_TYPE),
    }
    return order


def submit_trade(token_id: str, side: str, price: float, size: float) -> dict:
    rc = OrderRoundConfig()
    tx_hash = None
    try:
        with httpx.Client(timeout=httpx.Timeout(30)) as c:
            r = c.post(f"{CLOB_BASE}/v2/order", json={
                "token_id": token_id,
                "side": side.upper(),
                "type": "GTC",
                "price": str(price),
                "size": str(size),
            }, headers=_auth_headers())
            r.raise_for_status()
            data = r.json()
            tx_hash = data.get("transaction_hash") or data.get("orderID") or data.get("id")
            return {"ok": True, "data": data, "tx_hash": tx_hash}
    except Exception as e:
        logger.exception("clob order failed")
        return {"ok": False, "error": str(e), "tx_hash": tx_hash}
