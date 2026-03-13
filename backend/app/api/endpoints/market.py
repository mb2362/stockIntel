from __future__ import annotations

from datetime import datetime, timezone

import yfinance as yf
from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/market")


MAJOR_INDICES = [
    {"symbol": "^GSPC", "name": "S&P 500"},
    {"symbol": "^IXIC", "name": "NASDAQ"},
    {"symbol": "^DJI", "name": "DOW JONES"},
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


def _quote_basic(symbol: str) -> dict:
    """Return price + change for a symbol using yfinance in a lightweight way."""
    t = yf.Ticker(symbol)
    fi = getattr(t, "fast_info", None) or {}

    # Prefer fast_info for price; fall back to last close from history.
    price = fi.get("last_price")
    prev_close = fi.get("previous_close")
    if price is None or prev_close is None:
        h = t.history(period="2d", interval="1d", auto_adjust=True)
        if h is None or h.empty:
            raise HTTPException(status_code=503, detail=f"Market data unavailable for {symbol}")
        # last row is latest close
        close = float(h["Close"].iloc[-1])
        prev = float(h["Close"].iloc[-2]) if len(h) >= 2 else close
        price = close
        prev_close = prev

    change = float(price) - float(prev_close)
    change_pct = (change / float(prev_close) * 100.0) if float(prev_close) else 0.0

    return {
        "price": float(price),
        "prev_close": float(prev_close),
        "change": float(change),
        "changePercent": float(change_pct),
        "volume": int(fi.get("last_volume") or 0),
        "marketCap": float(fi.get("market_cap") or 0),
        "name": fi.get("short_name") or fi.get("long_name") or symbol,
    }


@router.get("/overview")
async def get_market_overview():
    """Matches frontend MarketOverview type."""
    indices = []
    for idx in MAJOR_INDICES:
        q = _quote_basic(idx["symbol"])
        indices.append(
            {
                "symbol": idx["symbol"],
                "name": idx["name"],
                "value": q["price"],
                "change": q["change"],
                "changePercent": q["changePercent"],
            }
        )

    # Simple market status heuristic (good enough for MVP)
    market_status = "open"  # frontend expects one of open/closed/pre-market/after-hours

    return {
        "indices": indices,
        "marketStatus": market_status,
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/trending")
async def get_trending_stocks():
    """Matches frontend TrendingStock type.

    Yahoo does not provide a stable free 'trending' endpoint via yfinance, so we
    approximate using a fixed list of popular tickers.
    """
    out = []
    for symbol in POPULAR_STOCKS:
        try:
            q = _quote_basic(symbol)
            out.append(
                {
                    "symbol": symbol,
                    "name": q["name"],
                    "price": q["price"],
                    "changePercent": q["changePercent"],
                    "volume": q["volume"],
                }
            )
        except Exception:
            continue
    return out


GAINER_LOSER_SYMBOLS = [
    "NVDA", "TSLA", "AMD", "META", "AAPL",
    "AMZN", "MSFT", "GOOGL", "NFLX", "INTC",
    "JPM", "V", "WMT", "BABA", "PLTR",
]


@router.get("/gainers")
async def get_top_gainers():
    """Returns top gaining stocks. Matches frontend TrendingStock type."""
    results = []
    for sym in GAINER_LOSER_SYMBOLS:
        try:
            q = _quote_basic(sym)
            if q["changePercent"] > 0:
                results.append({
                    "symbol": sym,
                    "name": q["name"],
                    "price": q["price"],
                    "change": q["change"],
                    "changePercent": q["changePercent"],
                    "volume": q["volume"],
                })
        except Exception:
            continue

    results.sort(key=lambda x: x["changePercent"], reverse=True)
    return results[:5]


@router.get("/losers")
async def get_top_losers():
    """Returns top losing stocks. Matches frontend TrendingStock type."""
    results = []
    for sym in GAINER_LOSER_SYMBOLS:
        try:
            q = _quote_basic(sym)
            if q["changePercent"] < 0:
                results.append({
                    "symbol": sym,
                    "name": q["name"],
                    "price": q["price"],
                    "change": q["change"],
                    "changePercent": q["changePercent"],
                    "volume": q["volume"],
                })
        except Exception:
            continue

    results.sort(key=lambda x: x["changePercent"])
    return results[:5]
