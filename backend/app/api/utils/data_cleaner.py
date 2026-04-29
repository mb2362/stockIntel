"""Data cleaning and normalization utilities for StockIntel API.

All raw data from Yahoo Finance / yfinance passes through these helpers
before being returned to clients, guaranteeing consistent types, bounded
values, and no NaN / None leaking into JSON responses.
"""
from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Primitive sanitisers
# ---------------------------------------------------------------------------

def clean_float(value: Any, default: float = 0.0, min_val: float | None = None,
                max_val: float | None = None) -> float:
    """Convert *value* to a finite float, clamping to optional bounds."""
    try:
        if value is None:
            return default
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return default
        if min_val is not None:
            f = max(min_val, f)
        if max_val is not None:
            f = min(max_val, f)
        return round(f, 6)
    except (TypeError, ValueError):
        return default


def clean_int(value: Any, default: int = 0, min_val: int | None = None,
              max_val: int | None = None) -> int:
    """Convert *value* to an int, clamping to optional bounds."""
    try:
        if value is None:
            return default
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return default
        i = int(value)
        if min_val is not None:
            i = max(min_val, i)
        if max_val is not None:
            i = min(max_val, i)
        return i
    except (TypeError, ValueError):
        return default


def clean_str(value: Any, default: str = "", max_length: int = 512) -> str:
    """Coerce to string, strip whitespace, truncate to *max_length*."""
    if value is None:
        return default
    s = str(value).strip()
    if not s:
        return default
    return s[:max_length]


def clean_symbol(value: Any) -> str:
    """Normalise a stock ticker: upper-case, strip non-alphanumeric (except ^/.)."""
    raw = clean_str(value, "").upper()
    # Keep letters, digits, ^ (index prefix), . (class suffix), -
    normalised = re.sub(r"[^A-Z0-9\^\.\-]", "", raw)
    return normalised[:20]


def clean_percent(value: Any, default: float = 0.0) -> float:
    """Return a percentage clamped to [-100, 10 000] to avoid absurd outliers."""
    return clean_float(value, default, min_val=-100.0, max_val=10_000.0)


def clean_price(value: Any, default: float = 0.0) -> float:
    """Return a non-negative price rounded to 4 dp."""
    return clean_float(value, default, min_val=0.0)


def clean_volume(value: Any) -> int:
    """Return a non-negative integer volume."""
    return clean_int(value, 0, min_val=0)


def clean_market_cap(value: Any) -> float:
    """Return a non-negative market-cap float."""
    return clean_float(value, 0.0, min_val=0.0)


def clean_iso_date(value: Any) -> Optional[str]:
    """Return an ISO-8601 date string or None."""
    if not value:
        return None
    s = clean_str(value)
    # Already looks like an ISO string?
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return s
    try:
        dt = datetime.fromtimestamp(float(s), tz=timezone.utc)
        return dt.isoformat()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Domain-level normalisers
# ---------------------------------------------------------------------------

def normalise_quote(raw: Dict[str, Any], symbol: str | None = None) -> Dict[str, Any]:
    """Normalise a stock-quote dict returned by the stocks endpoints."""
    sym = clean_symbol(symbol or raw.get("symbol", ""))
    price = clean_price(raw.get("price"))
    prev_close = clean_price(raw.get("previousClose") or raw.get("prevClose"))

    # Re-derive change/changePercent from cleaned values so they stay consistent
    change = clean_float(raw.get("change"))
    if price and prev_close and not raw.get("change"):
        change = round(price - prev_close, 6)

    change_pct = clean_percent(raw.get("changePercent"))
    if prev_close and not raw.get("changePercent"):
        change_pct = round((change / prev_close) * 100, 4)

    return {
        "symbol": sym,
        "name": clean_str(raw.get("name"), sym, max_length=256),
        "price": price,
        "change": change,
        "changePercent": change_pct,
        "volume": clean_volume(raw.get("volume")),
        "marketCap": clean_market_cap(raw.get("marketCap")),
        "sector": clean_str(raw.get("sector"), None, 128) or None,
        "industry": clean_str(raw.get("industry"), None, 128) or None,
        "open": clean_price(raw.get("open")),
        "high": clean_price(raw.get("high")),
        "low": clean_price(raw.get("low")),
        "previousClose": prev_close,
        "fiftyTwoWeekHigh": clean_price(raw.get("fiftyTwoWeekHigh")),
        "fiftyTwoWeekLow": clean_price(raw.get("fiftyTwoWeekLow")),
        "peRatio": clean_float(raw.get("peRatio"), None) if raw.get("peRatio") is not None else None,
        "dividendYield": clean_float(raw.get("dividendYield"), None) if raw.get("dividendYield") is not None else None,
        "beta": clean_float(raw.get("beta"), None) if raw.get("beta") is not None else None,
    }


def normalise_stock_detail(raw: Dict[str, Any], symbol: str | None = None) -> Dict[str, Any]:
    """Normalise a full stock-info/detail dict."""
    base = normalise_quote(raw, symbol)
    base.update({
        "description": clean_str(raw.get("description"), None, 4096) or None,
        "ceo": clean_str(raw.get("ceo"), None, 128) or None,
        "employees": clean_int(raw.get("employees"), None) if raw.get("employees") is not None else None,
        "headquarters": clean_str(raw.get("headquarters"), None, 256) or None,
        "founded": clean_str(raw.get("founded"), None, 32) or None,
        "website": clean_str(raw.get("website"), None, 256) or None,
    })
    return base


def normalise_historical_point(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalise a single OHLCV bar; returns None if the bar is unusable."""
    close = clean_price(raw.get("close"))
    if close == 0.0:
        return None  # Drop zero-close bars (bad data / pre-market artefacts)

    date = clean_str(raw.get("date"), "")
    if not date:
        return None

    open_ = clean_price(raw.get("open"))
    high = clean_price(raw.get("high"))
    low = clean_price(raw.get("low"))

    # Enforce OHLC consistency (high >= open/close, low <= open/close)
    high = max(high, open_, close)
    low = min(low, open_, close) if low > 0 else low

    return {
        "date": date,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": clean_volume(raw.get("volume")),
    }


def normalise_historical(bars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalise and deduplicate a list of OHLCV bars."""
    seen: set[str] = set()
    out: List[Dict[str, Any]] = []
    for bar in bars:
        cleaned = normalise_historical_point(bar)
        if cleaned is None:
            continue
        date_key = cleaned["date"]
        if date_key in seen:
            continue  # deduplicate
        seen.add(date_key)
        out.append(cleaned)
    return out


def normalise_indicators(raw: Dict[str, Any], symbol: str | None = None) -> Dict[str, Any]:
    """Normalise technical-indicator response."""
    macd_raw = raw.get("macd") or {}
    return {
        "symbol": clean_symbol(symbol or raw.get("symbol", "")),
        "ma50": clean_float(raw.get("ma50")),
        "ma200": clean_float(raw.get("ma200")),
        "rsi": clean_float(raw.get("rsi"), min_val=0.0, max_val=100.0),
        "macd": {
            "value": clean_float(macd_raw.get("value") if isinstance(macd_raw, dict) else None),
            "signal": clean_float(macd_raw.get("signal") if isinstance(macd_raw, dict) else None),
            "histogram": clean_float(macd_raw.get("histogram") if isinstance(macd_raw, dict) else None),
        },
    }


def normalise_news_article(raw: Dict[str, Any], index: int = 0) -> Dict[str, Any]:
    """Normalise a single news-article dict."""
    return {
        "id": clean_str(raw.get("id"), str(index), 256),
        "title": clean_str(raw.get("title"), "Untitled", 512),
        "source": clean_str(raw.get("source"), "Unknown", 128),
        "url": clean_str(raw.get("url"), "", 1024),
        "publishedAt": clean_str(raw.get("publishedAt"), datetime.now(timezone.utc).isoformat()),
        "summary": clean_str(raw.get("summary"), None, 2048) or None,
        "imageUrl": clean_str(raw.get("imageUrl"), None, 1024) or None,
        "sentiment": clean_str(raw.get("sentiment"), "neutral", 32),
    }


def normalise_search_result(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalise a search-result item; returns None if symbol is missing."""
    sym = clean_symbol(raw.get("symbol", ""))
    if not sym:
        return None
    return {
        "symbol": sym,
        "name": clean_str(raw.get("name"), sym, 256),
        "type": clean_str(raw.get("type"), "EQUITY", 32),
        "region": clean_str(raw.get("region"), "US", 32),
        "currency": clean_str(raw.get("currency"), "USD", 16),
    }


def normalise_market_index(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise a market-index entry."""
    return {
        "symbol": clean_symbol(raw.get("symbol", "")),
        "name": clean_str(raw.get("name"), "", 128),
        "value": clean_price(raw.get("value")),
        "change": clean_float(raw.get("change")),
        "changePercent": clean_percent(raw.get("changePercent")),
    }


def normalise_trending_stock(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise a trending-stock entry."""
    sym = clean_symbol(raw.get("symbol", ""))
    return {
        "symbol": sym,
        "name": clean_str(raw.get("name"), sym, 256),
        "price": clean_price(raw.get("price")),
        "changePercent": clean_percent(raw.get("changePercent")),
        "volume": clean_volume(raw.get("volume")),
    }


def normalise_watchlist_item(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise a watchlist entry with live price info."""
    sym = clean_symbol(raw.get("symbol", ""))
    return {
        "symbol": sym,
        "name": clean_str(raw.get("name"), sym, 256),
        "price": clean_price(raw.get("price")),
        "change": clean_float(raw.get("change")),
        "changePercent": clean_percent(raw.get("changePercent")),
        "volume": clean_volume(raw.get("volume")),
        "marketCap": clean_market_cap(raw.get("marketCap")),
        "addedAt": clean_str(raw.get("addedAt"), datetime.now(timezone.utc).isoformat()),
    }
