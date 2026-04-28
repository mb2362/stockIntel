"""Market overview, trending, gainers/losers endpoints."""
from __future__ import annotations

import concurrent.futures
from datetime import datetime, timezone

import yfinance as yf
from fastapi import APIRouter, HTTPException
import time

from app.api.endpoints.stocks import _build_quote_parts, _get_info_best_effort, _ticker, _yahoo_quote
<<<<<<< Updated upstream
from app.api.utils.data_cleaner import (
    normalise_market_index, normalise_trending_stock, normalise_quote,
    clean_float, clean_volume, clean_market_cap, clean_symbol, clean_str,
)
=======
from app.cache import cache_get, cache_set, make_key, TTL_OVERVIEW, TTL_QUOTE
>>>>>>> Stashed changes

router = APIRouter(prefix="/market")


MAJOR_INDICES = [
    {"symbol": "^GSPC", "name": "S&P 500"},
    {"symbol": "^IXIC", "name": "NASDAQ"},
    {"symbol": "^DJI", "name": "Dow Jones"},
    {"symbol": "^RUT", "name": "Russell 2000"},
    {"symbol": "^VIX", "name": "Volatility Index"},
    {"symbol": "^FTSE", "name": "FTSE 100"},
    {"symbol": "^N225", "name": "Nikkei 225"},
    {"symbol": "^HSI", "name": "Hang Seng"},
    {"symbol": "^GDAXI", "name": "DAX"},
]

POPULAR_STOCKS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "TSLA",
    "META",
    "NVDA",
    "JPM",
    "V",
    "WMT",
]

_quote_cache = {}


def _quote_basic(symbol: str) -> dict:
    """Return price + change for a symbol using the v8 chart API directly."""
    now = time.time()
    cached = _quote_cache.get(symbol)
    if cached and (now - cached["time"] < 15):
        return cached["data"]
        
    try:
        qp = _build_quote_parts(symbol)
        # Use the v8 chart meta for name (avoids yfinance crumb/rate-limit)
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
    except Exception as e:
        # Return stale cache if available rather than failing hard
        if cached and cached.get("data"):
            return cached["data"]
        raise HTTPException(status_code=503, detail=f"Market data unavailable for {symbol}")


@router.get("/overview")
async def get_market_overview():
    """Matches frontend MarketOverview type."""
    ov_key = make_key("market_overview")
    cached_ov = cache_get(ov_key)
    if cached_ov is not None:
        return cached_ov

    def fetch_index(idx):
        try:
            q = _quote_basic(idx["symbol"])
            raw = {
                "symbol": idx["symbol"],
                "name": idx["name"],
                "value": q["price"],
                "change": q["change"],
                "changePercent": q["changePercent"],
            }
            return normalise_market_index(raw)
        except Exception:
            return None

    indices = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_index, MAJOR_INDICES)
        for r in results:
            if r is not None:
                indices.append(r)

    # Simple market status heuristic (good enough for MVP)
    market_status = "open"  # frontend expects one of open/closed/pre-market/after-hours

    result = {
        "indices": indices,
        "marketStatus": market_status,
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
    }
    cache_set(ov_key, result, ttl=TTL_OVERVIEW)
    return result


@router.get("/trending")
async def get_trending_stocks():
    """Matches frontend TrendingStock type.

    Yahoo does not provide a stable free 'trending' endpoint via yfinance, so we
    approximate using a fixed list of popular tickers.
    """
    def fetch_trending(symbol):
        try:
            q = _quote_basic(symbol)
            raw = {
                "symbol": symbol,
                "name": q["name"],
                "price": q["price"],
                "changePercent": q["changePercent"],
                "volume": q["volume"],
            }
            return normalise_trending_stock(raw)
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
    "NVDA", "TSLA", "AMD", "META", "AAPL",
    "AMZN", "MSFT", "GOOGL", "NFLX", "INTC",
    "JPM", "V", "WMT", "BABA", "PLTR",
]


def _fetch_gainer_loser(sym):
    try:
        q = _quote_basic(sym)
        raw = {
            "symbol": sym,
            "name": q["name"],
            "price": q["price"],
            "change": q["change"],
            "changePercent": q["changePercent"],
            "volume": q["volume"],
        }
        return normalise_trending_stock({**raw, "changePercent": raw["changePercent"]}) | {
            "change": clean_float(raw["change"]),
        }
    except Exception:
        return None


@router.get("/gainers")
async def get_top_gainers():
    """Returns top gaining stocks. Matches frontend TrendingStock type."""
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
    """Returns top losing stocks. Matches frontend TrendingStock type."""
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        r_list = executor.map(_fetch_gainer_loser, GAINER_LOSER_SYMBOLS)
        for r in r_list:
            if r is not None and r["changePercent"] < 0:
                results.append(r)

    results.sort(key=lambda x: x["changePercent"])
    return results[:5]
