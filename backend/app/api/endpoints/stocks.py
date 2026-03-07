from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
import yfinance as yf
import logging
from fastapi import APIRouter, Body, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.database import crud, database, models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stocks")


TIME_RANGE_TO_PERIOD = {
    "1D": ("1d", "5m"),
    "1W": ("7d", "30m"),
    "1M": ("1mo", "1d"),
    "3M": ("3mo", "1d"),
    "1Y": ("1y", "1d"),
    "5Y": ("5y", "1wk"),
}


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return default
        return float(x)
    except Exception:
        return default


def _safe_int(x: Any, default: int = 0) -> int:
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return default
        return int(x)
    except Exception:
        return default


def _ticker(symbol: str) -> yf.Ticker:
    # A single place to customize yfinance behavior later (e.g. sessions, proxies, etc.)
    return yf.Ticker(symbol)


def _history_for_quote(t: yf.Ticker) -> pd.DataFrame:
    # Use 2 days to compute prevClose reliably.
    h = t.history(period="2d", interval="1d", auto_adjust=False)
    return h if h is not None else pd.DataFrame()


def _get_info_best_effort(t: yf.Ticker) -> Dict[str, Any]:
    try:
        info = t.get_info()  # newer API
        return info or {}
    except Exception:
        # Yahoo sometimes rate limits or returns empty; treat as optional.
        return {}


def _get_fast_info(t: yf.Ticker) -> Dict[str, Any]:
    return getattr(t, "fast_info", None) or {}


@dataclass
class QuoteParts:
    price: float
    prev_close: float
    open: float
    high: float
    low: float
    volume: int


def _build_quote_parts(symbol: str) -> QuoteParts:
    t = _ticker(symbol)
    fi = _get_fast_info(t)
    info = _get_info_best_effort(t)

    # Current price
    price = fi.get("last_price")
    prev_close = fi.get("previous_close")

    h = _history_for_quote(t)
    if (price is None or prev_close is None) and not h.empty:
        close = _safe_float(h["Close"].iloc[-1])
        prev = _safe_float(h["Close"].iloc[-2] if len(h) >= 2 else close)
        price = close if price is None else price
        prev_close = prev if prev_close is None else prev_close

    if price is None or prev_close is None:
        # Distinguish invalid ticker from upstream failure.
        # If even a 1d history is empty, treat as upstream unavailable.
        h1 = t.history(period="1d", interval="1d")
        if h1 is None or h1.empty:
            raise HTTPException(
                status_code=503,
                detail="Yahoo Finance unavailable or rate-limited (empty data). Try again later.",
            )
        raise HTTPException(status_code=404, detail="Stock not found")

    # OHLCV for today (or last trading day)
    if not h.empty:
        row = h.iloc[-1]
        open_ = _safe_float(row.get("Open"))
        high = _safe_float(row.get("High"))
        low = _safe_float(row.get("Low"))
        vol = _safe_int(row.get("Volume"))
    else:
        # Fallbacks
        open_ = _safe_float(info.get("open"))
        high = _safe_float(info.get("dayHigh"))
        low = _safe_float(info.get("dayLow"))
        vol = _safe_int(info.get("volume"))

    return QuoteParts(
        price=_safe_float(price),
        prev_close=_safe_float(prev_close),
        open=open_,
        high=high,
        low=low,
        volume=vol,
    )


def _compute_rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    last = rsi.dropna().iloc[-1] if not rsi.dropna().empty else pd.NA
    return _safe_float(last, default=0.0)


def _compute_macd(close: pd.Series) -> Dict[str, float]:
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return {
        "value": _safe_float(macd.iloc[-1], 0.0),
        "signal": _safe_float(signal.iloc[-1], 0.0),
        "histogram": _safe_float(hist.iloc[-1], 0.0),
    }


def _demo_user(db: Session) -> models.User:
    # Single-user mode for MVP (no auth required by current frontend)
    username = "demo"
    user = db.query(models.User).filter(models.User.username == username).first()
    if user:
        return user
    user = models.User(username=username, email="demo@example.com", hashed_password="")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/")
async def ping():
    return {"message": "Stocks endpoint works"}


# -----------------------------
# Frontend-aligned endpoints
# -----------------------------


@router.get("/search")
async def search_stocks(q: str):
    """Frontend expects: GET /stocks/search?q=... returning SearchResult[]."""
    q = (q or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if not hasattr(yf, "Search"):
        return []

    try:
        s = yf.Search(q)
        quotes = getattr(s, "quotes", None) or []
        out = []
        for item in quotes:
            sym = (item.get("symbol") or "").upper()
            if not sym:
                continue
            out.append(
                {
                    "symbol": sym,
                    "name": item.get("shortname") or item.get("longname") or item.get("name") or sym,
                    "type": item.get("quoteType") or item.get("typeDisp") or "EQUITY",
                    "region": item.get("region") or item.get("exchange") or "US",
                    "currency": item.get("currency") or "USD",
                }
            )
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


@router.get("/gainers")
async def get_top_gainers():
    symbols = [
        "NVDA","TSLA","AMD","META","AAPL",
        "AMZN","MSFT","GOOGL","NFLX","INTC"
    ]

    results = []

    for sym in symbols:
        try:
            qp = _build_quote_parts(sym)

            change = qp.price - qp.prev_close
            change_pct = (change / qp.prev_close * 100) if qp.prev_close else 0

            if change_pct > 0:
                results.append({
                    "symbol": sym,
                    "name": sym,
                    "price": qp.price,
                    "change": change,
                    "changePercent": change_pct,
                    "volume": qp.volume
                })

        except Exception:
            continue

    results.sort(key=lambda x: x["changePercent"], reverse=True)

    return results[:5]


@router.get("/losers")
async def get_top_losers():
    symbols = [
        "NVDA","TSLA","AMD","META","AAPL",
        "AMZN","MSFT","GOOGL","NFLX","INTC"
    ]

    results = []

    for sym in symbols:
        try:
            qp = _build_quote_parts(sym)

            change = qp.price - qp.prev_close
            change_pct = (change / qp.prev_close * 100) if qp.prev_close else 0

            if change_pct < 0:
                results.append({
                    "symbol": sym,
                    "name": sym,
                    "price": qp.price,
                    "change": change,
                    "changePercent": change_pct,
                    "volume": qp.volume
                })

        except Exception:
            continue

    results.sort(key=lambda x: x["changePercent"])

    return results[:5]


@router.get("/{symbol}/quote")
async def get_stock_quote(symbol: str):
    """Frontend expects StockQuote."""
    symbol = symbol.upper().strip()
    t = _ticker(symbol)
    info = _get_info_best_effort(t)

    qp = _build_quote_parts(symbol)
    change = qp.price - qp.prev_close
    change_pct = (change / qp.prev_close * 100.0) if qp.prev_close else 0.0

    return {
        "symbol": symbol,
        "name": info.get("shortName") or info.get("longName") or symbol,
        "price": qp.price,
        "change": change,
        "changePercent": change_pct,
        "volume": qp.volume,
        "marketCap": _safe_float(info.get("marketCap"), 0.0),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "open": qp.open,
        "high": qp.high,
        "low": qp.low,
        "previousClose": qp.prev_close,
        "fiftyTwoWeekHigh": _safe_float(info.get("fiftyTwoWeekHigh"), 0.0),
        "fiftyTwoWeekLow": _safe_float(info.get("fiftyTwoWeekLow"), 0.0),
        "peRatio": info.get("trailingPE") or info.get("forwardPE"),
        "dividendYield": info.get("dividendYield"),
        "beta": info.get("beta"),
    }


@router.get("/{symbol}/info")
async def get_stock_info(symbol: str):
    """Frontend expects StockDetails."""
    symbol = symbol.upper().strip()
    t = _ticker(symbol)
    info = _get_info_best_effort(t)
    qp = _build_quote_parts(symbol)
    change = qp.price - qp.prev_close
    change_pct = (change / qp.prev_close * 100.0) if qp.prev_close else 0.0

    # Attempt to cache basic metadata in DB (optional for frontend, useful for your pipeline)
    # This keeps your existing DB model relevant without forcing the frontend schema.
    try:
        db = next(database.get_db())
        if not crud.get_stock_by_ticker(db, symbol):
            crud.create_stock(
                db,
                {
                    "ticker": symbol,
                    "name": info.get("shortName") or info.get("longName") or symbol,
                    "market": "stocks",
                    "locale": info.get("country") or info.get("region"),
                    "primary_exchange": info.get("exchange") or info.get("fullExchangeName"),
                    "type": info.get("quoteType"),
                    "currency_name": info.get("currency"),
                    "active": True,
                },
            )
    except Exception:
        pass

    return {
        "symbol": symbol,
        "name": info.get("shortName") or info.get("longName") or symbol,
        "price": qp.price,
        "change": change,
        "changePercent": change_pct,
        "volume": qp.volume,
        "marketCap": _safe_float(info.get("marketCap"), 0.0),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "open": qp.open,
        "high": qp.high,
        "low": qp.low,
        "previousClose": qp.prev_close,
        "fiftyTwoWeekHigh": _safe_float(info.get("fiftyTwoWeekHigh"), 0.0),
        "fiftyTwoWeekLow": _safe_float(info.get("fiftyTwoWeekLow"), 0.0),
        "peRatio": info.get("trailingPE") or info.get("forwardPE"),
        "dividendYield": info.get("dividendYield"),
        "beta": info.get("beta"),
        "description": info.get("longBusinessSummary"),
        "ceo": None,
        "employees": info.get("fullTimeEmployees"),
        "headquarters": None,
        "founded": None,
        "website": info.get("website"),
    }


@router.get("")
async def get_all_stocks():
    """
    Return quotes for popular stocks so the homepage can load.
    """
    symbols = [
        "AAPL","MSFT","GOOGL","AMZN","TSLA",
        "META","NVDA","JPM","V","WMT"
    ]

    results = []
    for sym in symbols:
        try:
            qp = _build_quote_parts(sym)
            change = qp.price - qp.prev_close
            change_pct = (change / qp.prev_close * 100) if qp.prev_close else 0

            results.append({
                "symbol": sym,
                "name": sym,
                "price": qp.price,
                "change": change,
                "changePercent": change_pct,
                "volume": qp.volume,
                "marketCap": 0,
                "sector": None,
                "industry": None,
            })

        except Exception as e:
            logger.warning(f"Failed to load stock {sym}: {e}")
            continue

    return results


@router.get("/{symbol}/historical")
async def get_historical(symbol: str, range: str = "1M"):
    """Frontend expects: GET /stocks/{symbol}/historical?range=1M returning HistoricalDataPoint[]."""
    symbol = symbol.upper().strip()
    range = (range or "1M").upper().strip()
    if range not in TIME_RANGE_TO_PERIOD:
        raise HTTPException(status_code=400, detail=f"Invalid range: {range}")

    period, interval = TIME_RANGE_TO_PERIOD[range]
    t = _ticker(symbol)
    hist = t.history(period=period, interval=interval, auto_adjust=False)
    if hist is None or hist.empty:
        raise HTTPException(
            status_code=503,
            detail="Yahoo Finance unavailable or rate-limited (empty data). Try again later.",
        )

    hist = hist.reset_index()
    # yfinance can return either Date or Datetime index based on interval
    date_col = "Datetime" if "Datetime" in hist.columns else "Date"

    out: List[Dict[str, Any]] = []
    for _, row in hist.iterrows():
        dt = pd.to_datetime(row[date_col])
        out.append(
            {
                "date": dt.date().isoformat() if interval.endswith("d") or interval.endswith("wk") else dt.isoformat(),
                "open": _safe_float(row.get("Open")),
                "high": _safe_float(row.get("High")),
                "low": _safe_float(row.get("Low")),
                "close": _safe_float(row.get("Close")),
                "volume": _safe_int(row.get("Volume")),
            }
        )
    return out


@router.get("/{symbol}/indicators")
async def get_indicators(symbol: str):
    """Frontend expects TechnicalIndicators."""
    symbol = symbol.upper().strip()
    t = _ticker(symbol)
    hist = t.history(period="2y", interval="1d", auto_adjust=True)
    if hist is None or hist.empty or "Close" not in hist.columns:
        raise HTTPException(
            status_code=503,
            detail="Yahoo Finance unavailable or rate-limited (empty data). Try again later.",
        )

    close = hist["Close"].astype(float)
    ma50 = close.rolling(window=50).mean().iloc[-1] if len(close) >= 50 else close.mean()
    ma200 = close.rolling(window=200).mean().iloc[-1] if len(close) >= 200 else close.mean()
    rsi = _compute_rsi(close)
    macd = _compute_macd(close)

    return {
        "symbol": symbol,
        "ma50": _safe_float(ma50, 0.0),
        "ma200": _safe_float(ma200, 0.0),
        "rsi": rsi,
        "macd": macd,
    }


@router.get("/{symbol}/news")
async def get_stock_news(symbol: str):
    """Frontend expects NewsArticle[].

    For MVP, we use yfinance's Ticker.news when available. Later you can swap this
    to Twitter/X, NewsAPI, AlphaVantage news, etc.
    """
    symbol = symbol.upper().strip()
    t = _ticker(symbol)
    items = getattr(t, "news", None) or []

    out: List[Dict[str, Any]] = []
    for item in items[:20]:
        # yfinance news items are dicts with keys like: title, publisher, link, providerPublishTime
        ts = item.get("providerPublishTime")
        published = (
            datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat() if ts else datetime.now(timezone.utc).isoformat()
        )
        out.append(
            {
                "id": str(item.get("uuid") or item.get("id") or item.get("link") or len(out)),
                "title": item.get("title") or "",
                "source": item.get("publisher") or "Yahoo Finance",
                "url": item.get("link") or "",
                "publishedAt": published,
                "summary": item.get("summary"),
                "imageUrl": (item.get("thumbnail", {}) or {}).get("resolutions", [{}])[-1].get("url")
                if isinstance(item.get("thumbnail"), dict)
                else None,
                "sentiment": "neutral",
            }
        )
    return out


@router.post("/compare")
async def compare_stocks(payload: dict = Body(...)):
    """Frontend expects ComparisonData.

    POST /stocks/compare { symbols: string[] }
    """
    symbols = payload.get("symbols")
    if not isinstance(symbols, list) or not symbols:
        raise HTTPException(status_code=400, detail="symbols must be a non-empty array")

    symbols = [str(s).upper().strip() for s in symbols if str(s).strip()]
    data: Dict[str, Any] = {}

    for sym in symbols:
        t = _ticker(sym)
        info = _get_info_best_effort(t)
        qp = _build_quote_parts(sym)
        change = qp.price - qp.prev_close
        change_pct = (change / qp.prev_close * 100.0) if qp.prev_close else 0.0

        hist = t.history(period="1mo", interval="1d", auto_adjust=True)
        historical = []
        if hist is not None and not hist.empty:
            hist = hist.reset_index()
            for _, row in hist.iterrows():
                dt = pd.to_datetime(row["Date"]).date().isoformat() if "Date" in hist.columns else ""
                historical.append({"date": dt, "close": _safe_float(row.get("Close"))})

        data[sym] = {
            "name": info.get("shortName") or info.get("longName") or sym,
            "price": qp.price,
            "change": change,
            "changePercent": change_pct,
            "marketCap": _safe_float(info.get("marketCap"), 0.0),
            "peRatio": info.get("trailingPE") or info.get("forwardPE"),
            "volume": qp.volume,
            "historical": historical,
        }

    return {"symbols": symbols, "data": data}


# -----------------------------
# ML integration hook (stub)
# -----------------------------


@router.get("/{symbol}/predict")
async def predict_future_price(symbol: str, horizon_days: int = 7):
    """Optional endpoint for later ML integration.

    You can replace the dummy logic with:
    - a local model call
    - a separate ML microservice
    - or a queue job (Celery) that stores predictions.
    """
    symbol = symbol.upper().strip()
    qp = _build_quote_parts(symbol)
    # Dummy baseline: predict flat price.
    return {
        "symbol": symbol,
        "horizonDays": horizon_days,
        "asOf": datetime.now(timezone.utc).isoformat(),
        "predictedPrice": qp.price,
        "model": "stub_baseline",
    }
