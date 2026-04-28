"""Market overview, trending, gainers/losers endpoints."""
from __future__ import annotations

import concurrent.futures
from datetime import datetime, timezone, time as dtime
import zoneinfo

import yfinance as yf
from fastapi import APIRouter, HTTPException
import time

from app.api.endpoints.stocks import _build_quote_parts, _get_info_best_effort, _ticker, _yahoo_quote

router = APIRouter(prefix="/market")


MAJOR_INDICES = [
    {"symbol": "^GSPC", "name": "S&P 500"},
    {"symbol": "^IXIC", "name": "NASDAQ"},
    {"symbol": "^DJI",  "name": "Dow Jones"},
    {"symbol": "^RUT",  "name": "Russell 2000"},
    {"symbol": "^VIX",  "name": "Volatility Index"},
    {"symbol": "^FTSE", "name": "FTSE 100"},
    {"symbol": "^N225", "name": "Nikkei 225"},
    {"symbol": "^HSI",  "name": "Hang Seng"},
    {"symbol": "^GDAXI","name": "DAX"},
]

POPULAR_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
    "META", "NVDA", "JPM",   "V",    "WMT",
]

_quote_cache = {}


def _get_market_status() -> str:
    """Return real-time US market status based on Eastern Time."""
    try:
        now = datetime.now(zoneinfo.ZoneInfo("America/New_York"))
    except Exception:
        # Fallback if zoneinfo not available
        import datetime as _dt
        now = datetime.utcnow().replace(tzinfo=timezone.utc)

    weekday = now.weekday()  # 0=Mon, 6=Sun
    current_time = now.time()

    # Weekend — always closed
    if weekday >= 5:
        return "closed"

    pre_market_open  = dtime(4,  0)
    market_open      = dtime(9, 30)
    market_close     = dtime(16,  0)
    after_hours_end  = dtime(20,  0)

    if current_time < pre_market_open or current_time >= after_hours_end:
        return "closed"
    if current_time < market_open:
        return "pre-market"
    if current_time >= market_close:
        return "after-hours"
    return "open"


def _quote_basic(symbol: str) -> dict:
    """Return price + change for a symbol using the v8 chart API directly."""
    now = time.time()
    cached = _quote_cache.get(symbol)
    if cached and (now - cached["time"] < 15):
        return cached["data"]

    try:
        qp = _build_quote_parts(symbol)
        try:
            meta = _yahoo_quote(symbol)
            name = meta.get("shortName") or meta.get("symbol") or symbol
            market_cap = float(meta.get("marketCap") or 0)
        except Exception:
            name = symbol
            market_cap = 0.0

        change = qp.price - qp.prev_close
        change_pct = (change / qp.prev_close * 100.0) if qp.prev_close else 0.0

        result = {
            "price": qp.price,
            "prev_close": qp.prev_close,
            "change": change,
            "changePercent": change_pct,
            "volume": qp.volume,
            "marketCap": market_cap,
            "name": name,
        }
        _quote_cache[symbol] = {"time": time.time(), "data": result}
        return result
    except Exception:
        if cached and cached.get("data"):
            return cached["data"]
        raise HTTPException(status_code=503, detail=f"Market data unavailable for {symbol}")


@router.get("/overview")
async def get_market_overview():
    """Matches frontend MarketOverview type."""
    def fetch_index(idx):
        try:
            q = _quote_basic(idx["symbol"])
            return {
                "symbol": idx["symbol"],
                "name": idx["name"],
                "value": q["price"],
                "change": q["change"],
                "changePercent": q["changePercent"],
            }
        except Exception:
            return None

    indices = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_index, MAJOR_INDICES)
        for r in results:
            if r is not None:
                indices.append(r)

    return {
        "indices": indices,
        "marketStatus": _get_market_status(),
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/trending")
async def get_trending_stocks():
    """Matches frontend TrendingStock type."""
    def fetch_trending(symbol):
        try:
            q = _quote_basic(symbol)
            return {
                "symbol": symbol,
                "name": q["name"],
                "price": q["price"],
                "changePercent": q["changePercent"],
                "volume": q["volume"],
            }
        except Exception:
            return None

    out = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_trending, POPULAR_STOCKS)
        for r in results:
            if r is not None:
                out.append(r)
    return out


GAINER_LOSER_SYMBOLS = [
    "NVDA", "TSLA", "AMD",   "META",  "AAPL",
    "AMZN", "MSFT", "GOOGL", "NFLX",  "INTC",
    "JPM",  "V",    "WMT",   "BABA",  "PLTR",
]


def _fetch_gainer_loser(sym):
    try:
        q = _quote_basic(sym)
        return {
            "symbol": sym,
            "name": q["name"],
            "price": q["price"],
            "change": q["change"],
            "changePercent": q["changePercent"],
            "volume": q["volume"],
        }
    except Exception:
        return None


@router.get("/gainers")
async def get_top_gainers():
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        r_list = executor.map(_fetch_gainer_loser, GAINER_LOSER_SYMBOLS)
        for r in r_list:
            if r is not None and r["changePercent"] > 0:
                results.append(r)
    results.sort(key=lambda x: x["changePercent"], reverse=True)
    return results[:5]


@router.get("/losers")
async def get_top_losers():
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        r_list = executor.map(_fetch_gainer_loser, GAINER_LOSER_SYMBOLS)
        for r in r_list:
            if r is not None and r["changePercent"] < 0:
                results.append(r)
    results.sort(key=lambda x: x["changePercent"])
    return results[:5]