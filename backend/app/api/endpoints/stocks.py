"""Stocks API endpoints – quote, historical, indicators, news, compare, predict."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import concurrent.futures
import requests

import pandas as pd
import yfinance as yf
import logging
from fastapi import APIRouter, Body, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
import time
from app.database import crud, database, models
<<<<<<< Updated upstream
from app.api.utils.data_cleaner import (
    normalise_quote, normalise_stock_detail, normalise_historical,
    normalise_indicators, normalise_news_article, normalise_search_result,
    normalise_watchlist_item, normalise_trending_stock,
    clean_symbol, clean_str, clean_market_cap, clean_volume,
)
from app.api.security.middleware import sanitise_symbol_param
=======
from app.cache import (
    cache_get, cache_set, make_key,
    TTL_QUOTE, TTL_HISTORICAL, TTL_INFO, TTL_NEWS, TTL_OVERVIEW,
)
>>>>>>> Stashed changes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stocks")

# Shared session with a browser-like User-Agent to avoid Yahoo Finance bot-detection rate limits
_session = requests.Session()
_session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})


TIME_RANGE_TO_PERIOD = {
    "1D": ("1d", "5m"),
    "1W": ("7d", "30m"),
    "1M": ("1mo", "1d"),
    "3M": ("3mo", "1d"),
    "1Y": ("1y", "1d"),
    "5Y": ("5y", "1wk"),
}

# v8 chart API params: (interval, range)
TIME_RANGE_TO_V8 = {
    "1D": ("5m",  "1d"),
    "1W": ("30m", "5d"),
    "1M": ("1d",  "1mo"),
    "3M": ("1d",  "3mo"),
    "1Y": ("1d",  "1y"),
    "5Y": ("1wk", "5y"),
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
    # Use the shared browser-spoofed session to avoid rate-limiting
    return yf.Ticker(symbol, session=_session)


_YAHOO_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://finance.yahoo.com",
    "Referer": "https://finance.yahoo.com/",
}

_YAHOO_HTML_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

_crumb: Optional[str] = None


def _bootstrap_yahoo_session() -> Optional[str]:
    """Visit Yahoo Finance homepage to get session cookies, then fetch a valid crumb."""
    global _crumb
    if _crumb:
        return _crumb
    try:
        # Visit the homepage to set session cookies (A3, etc.)
        _session.get("https://finance.yahoo.com", headers=_YAHOO_HTML_HEADERS, timeout=10, allow_redirects=True)
        # Fetch the crumb with the session cookies now set
        resp = _session.get(
            "https://query1.finance.yahoo.com/v1/test/getcrumb",
            headers=_YAHOO_HEADERS,
            timeout=10,
        )
        if resp.status_code == 200 and resp.text:
            _crumb = resp.text.strip()
            logger.info(f"Yahoo Finance crumb obtained: {_crumb[:10]}...")
            return _crumb
    except Exception as e:
        logger.warning(f"Failed to get Yahoo Finance crumb: {e}")
    return None


# Bootstrap the Yahoo session at module load time (best-effort)
try:
    _bootstrap_yahoo_session()
except Exception:
    pass


def _yahoo_chart(symbol: str) -> Dict[str, Any]:
    """Directly call Yahoo Finance v8 chart API — no crumb/cookie required."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"interval": "1d", "range": "2d"}
    resp = _session.get(url, headers=_YAHOO_HEADERS, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _yahoo_quote(symbol: str) -> Dict[str, Any]:
    """Call Yahoo Finance v8 chart API — returns price/OHLV from chart meta. No auth required."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"interval": "1d", "range": "2d", "includePrePost": "false"}
    resp = _session.get(url, headers=_YAHOO_HEADERS, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    result = data.get("chart", {}).get("result", [])
    if not result:
        return {}
    meta = result[0].get("meta", {})
    return meta


def _yahoo_historical(symbol: str, range_key: str) -> List[Dict[str, Any]]:
    """Fetch OHLCV historical data via v8 chart API."""
    interval, v8_range = TIME_RANGE_TO_V8.get(range_key, ("1d", "1mo"))
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"interval": interval, "range": v8_range, "includePrePost": "false"}
    resp = _session.get(url, headers=_YAHOO_HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    result = data.get("chart", {}).get("result", [])
    if not result:
        return []

    chart = result[0]
    timestamps = chart.get("timestamp", [])
    indicators = chart.get("indicators", {})
    quotes = (indicators.get("quote") or [{}])[0]
    opens  = quotes.get("open",   [])
    highs  = quotes.get("high",   [])
    lows   = quotes.get("low",    [])
    closes = quotes.get("close",  [])
    volumes = quotes.get("volume", [])

    is_intraday = interval in ("1m", "5m", "15m", "30m", "60m", "90m")
    out: List[Dict[str, Any]] = []
    for i, ts in enumerate(timestamps):
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        c = _safe_float(closes[i] if i < len(closes) else None)
        if c == 0.0:
            continue
        out.append({
            "date": dt.isoformat() if is_intraday else dt.date().isoformat(),
            "open":   _safe_float(opens[i]   if i < len(opens)   else None),
            "high":   _safe_float(highs[i]   if i < len(highs)   else None),
            "low":    _safe_float(lows[i]    if i < len(lows)    else None),
            "close":  c,
            "volume": _safe_int(volumes[i]   if i < len(volumes) else None),
        })
    return out


def _yahoo_summary(symbol: str) -> Dict[str, Any]:
    """Fetch rich company info via Yahoo Finance v10 quoteSummary (needs crumb)."""
    crumb = _bootstrap_yahoo_session()
    if not crumb:
        return {}
    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
    params = {
        "modules": "assetProfile,summaryDetail,defaultKeyStatistics",
        "crumb": crumb,
    }
    resp = _session.get(url, headers=_YAHOO_HEADERS, params=params, timeout=10)
    if resp.status_code != 200:
        # Crumb may have expired — refresh and retry once
        global _crumb
        _crumb = None
        crumb = _bootstrap_yahoo_session()
        if not crumb:
            return {}
        params["crumb"] = crumb
        resp = _session.get(url, headers=_YAHOO_HEADERS, params=params, timeout=10)
        if resp.status_code != 200:
            return {}
    data = resp.json()
    result = data.get("quoteSummary", {}).get("result") or []
    if not result:
        return {}
    combined = {}
    for module in result[0].values():
        if isinstance(module, dict):
            combined.update(module)
    return combined


def _history_for_quote(t: yf.Ticker) -> pd.DataFrame:
    # Use 2 days to compute prevClose reliably.
    h = t.history(period="2d", interval="1d", auto_adjust=False)
    return h if h is not None else pd.DataFrame()


def _get_info_best_effort(t: yf.Ticker) -> Dict[str, Any]:
    """Try to get company info, first from direct Yahoo API, fall back to yfinance."""
    try:
        # Try direct API first (not affected by crumb rate-limit)
        symbol = t.ticker
        meta = _yahoo_quote(symbol)
        if meta:
            return {
                "shortName": meta.get("shortName") or meta.get("symbol"),
                "longName": meta.get("longName") or meta.get("shortName"),
                "marketCap": meta.get("marketCap"),
                "sector": None,   # v8 chart meta doesn't include sector
                "industry": None, # v8 chart meta doesn't include industry
            }
    except Exception:
        pass
    try:
        info = t.get_info()
        return info or {}
    except Exception:
        return {}


@dataclass
class QuoteParts:
    price: float
    prev_close: float
    open: float
    high: float
    low: float
    volume: int


_quote_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 15  # seconds — updated to match frontend auto-refresh pacing

def _build_quote_parts(symbol: str) -> QuoteParts:
    now = time.time()
    cached = _quote_cache.get(symbol)
    if cached and (now - cached["time"] < CACHE_TTL):
        return cached["data"]

    # Try Redis cache before hitting Yahoo Finance
    redis_key = make_key("quote_parts", symbol)
    redis_cached = cache_get(redis_key)
    if redis_cached:
        result = QuoteParts(**redis_cached)
        _quote_cache[symbol] = {"time": now, "data": result}
        return result

    try:
        # Direct Yahoo Finance API call — bypasses yfinance crumb authentication
        q = _yahoo_quote(symbol)
        price = _safe_float(q.get("regularMarketPrice"))
        prev_close = _safe_float(q.get("chartPreviousClose") or q.get("previousClose"))
        open_ = _safe_float(q.get("regularMarketDayOpen") or q.get("open"))
        high = _safe_float(q.get("regularMarketDayHigh") or q.get("dayHigh"))
        low = _safe_float(q.get("regularMarketDayLow") or q.get("dayLow"))
        vol = _safe_int(q.get("regularMarketVolume") or q.get("volume"))

        if price == 0.0:
            raise ValueError(f"Zero price returned for {symbol}")

        result = QuoteParts(
            price=price,
            prev_close=prev_close or price,
            open=open_,
            high=high,
            low=low,
            volume=vol,
        )
        _quote_cache[symbol] = {"time": time.time(), "data": result}
        # Persist in Redis for cross-process sharing
        cache_set(redis_key, {
            "price": result.price, "prev_close": result.prev_close,
            "open": result.open, "high": result.high,
            "low": result.low, "volume": result.volume,
        }, ttl=TTL_QUOTE)
        return result

    except Exception as e:
        # Return stale cache if available rather than failing hard
        if cached and cached.get("data"):
            logger.warning(f"Yahoo API failed for {symbol}, returning stale cache. Error: {e}")
            return cached["data"]
        raise HTTPException(
            status_code=503,
            detail=f"Yahoo Finance unavailable for {symbol}. Try again later.",
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
            raw = {
                "symbol": item.get("symbol"),
                "name": item.get("shortname") or item.get("longname") or item.get("name"),
                "type": item.get("quoteType") or item.get("typeDisp") or "EQUITY",
                "region": item.get("region") or item.get("exchange") or "US",
                "currency": item.get("currency") or "USD",
            }
            cleaned = normalise_search_result(raw)
            if cleaned:
                out.append(cleaned)
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
                raw = {
                    "symbol": sym, "name": sym, "price": qp.price,
                    "change": change, "changePercent": change_pct, "volume": qp.volume
                }
                results.append(normalise_quote(raw, sym))
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
                raw = {
                    "symbol": sym, "name": sym, "price": qp.price,
                    "change": change, "changePercent": change_pct, "volume": qp.volume
                }
                results.append(normalise_quote(raw, sym))
        except Exception:
            continue

    results.sort(key=lambda x: x["changePercent"])
    return results[:5]


@router.get("/{symbol}/quote")
async def get_stock_quote(symbol: str = Depends(sanitise_symbol_param)):
    """Frontend expects StockQuote."""

    cache_key = make_key("quote", symbol)
    cached_result = cache_get(cache_key)
    if cached_result is not None:
        return cached_result

    # Use v8 chart meta for company info (no yfinance crumb session required)
    try:
        meta = _yahoo_quote(symbol)
    except Exception:
        meta = {}

    qp = _build_quote_parts(symbol)
    change = qp.price - qp.prev_close
    change_pct = (change / qp.prev_close * 100.0) if qp.prev_close else 0.0

<<<<<<< Updated upstream
    raw = {
        "symbol": symbol.upper(),
=======
    result = {
        "symbol": symbol,
>>>>>>> Stashed changes
        "name": meta.get("shortName") or meta.get("symbol") or symbol,
        "price": qp.price,
        "change": change,
        "changePercent": change_pct,
        "volume": qp.volume,
        "marketCap": _safe_float(meta.get("marketCap"), 0.0),
        "sector": meta.get("sector"),
        "industry": meta.get("industry"),
        "open": qp.open,
        "high": qp.high,
        "low": qp.low,
        "previousClose": qp.prev_close,
        "fiftyTwoWeekHigh": _safe_float(meta.get("fiftyTwoWeekHigh") or meta.get("52WeekHigh"), 0.0),
        "fiftyTwoWeekLow": _safe_float(meta.get("fiftyTwoWeekLow") or meta.get("52WeekLow"), 0.0),
        "peRatio": meta.get("trailingPE"),
        "dividendYield": meta.get("dividendYield"),
        "beta": meta.get("beta"),
    }
<<<<<<< Updated upstream
    return normalise_quote(raw, symbol)
=======
    cache_set(cache_key, result, ttl=TTL_QUOTE)
    return result
>>>>>>> Stashed changes


@router.get("/{symbol}/info")
async def get_stock_info(symbol: str = Depends(sanitise_symbol_param)):
    """Frontend expects StockDetails."""

    # Use v8 chart meta for price + basic info
    try:
        meta = _yahoo_quote(symbol)
    except Exception:
        meta = {}

    # Use v10 quoteSummary for rich company info (description, sector, website etc.)
    try:
        summary = _yahoo_summary(symbol)
    except Exception:
        summary = {}

    qp = _build_quote_parts(symbol)
    change = qp.price - qp.prev_close
    change_pct = (change / qp.prev_close * 100.0) if qp.prev_close else 0.0

    name = meta.get("shortName") or summary.get("name") or symbol

    # Persist basic metadata in DB (best-effort)
    try:
        db = next(database.get_db())
        if not crud.get_stock_by_ticker(db, symbol):
            crud.create_stock(
                db,
                {
                    "ticker": symbol,
                    "name": name,
                    "market": "stocks",
                    "active": True,
                },
            )
    except Exception:
        pass

    def _raw(d, key):
        """Safely extract raw value from quoteSummary nested {raw, fmt} dicts."""
        v = d.get(key)
        if isinstance(v, dict):
            return v.get("raw") or v.get("fmt")
        return v

    raw = {
        "symbol": symbol,
        "name": name,
        "price": qp.price,
        "change": change,
        "changePercent": change_pct,
        "volume": qp.volume,
        "marketCap": _safe_float(_raw(summary, "marketCap") or meta.get("marketCap"), 0.0),
        "sector": summary.get("sector"),
        "industry": summary.get("industry"),
        "open": qp.open,
        "high": qp.high,
        "low": qp.low,
        "previousClose": qp.prev_close,
        "fiftyTwoWeekHigh": _safe_float(meta.get("fiftyTwoWeekHigh") or meta.get("52WeekHigh"), 0.0),
        "fiftyTwoWeekLow": _safe_float(meta.get("fiftyTwoWeekLow") or meta.get("52WeekLow"), 0.0),
        "peRatio": _raw(summary, "trailingPE"),
        "dividendYield": _raw(summary, "dividendYield"),
        "beta": _raw(summary, "beta"),
        "description": summary.get("longBusinessSummary"),
        "ceo": None,
        "employees": _raw(summary, "fullTimeEmployees"),
        "headquarters": summary.get("city"),
        "founded": None,
        "website": summary.get("website"),
    }
    return normalise_stock_detail(raw, symbol)


@router.get("")
async def get_all_stocks(page: int = 1, limit: int = 10):
    """
    Return paginated quotes for popular US stocks.
    """
    symbols = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "WMT", "JNJ", "PG", "MA",
        "HD", "CVX", "MRK", "ABBV", "PEP", "AVGO", "KO", "PFE", "TMO", "COST", "CSCO", "MCD", "DIS",
        "CRM", "DHR", "NFLX", "AMD", "ADBE", "ABT", "TXN", "PM", "VZ", "NEE", "INTC", "LIN", "AMGN",
        "HON", "IBM", "UNP", "QCOM", "BA", "SBUX", "GS", "INTU", "LOW", "CAT", "SPGI", "BLK", "DE",
        "MDT", "AXP", "GE", "ISRG", "NOW", "PLD", "SYK", "T", "CB", "MDLZ", "TJX", "ZTS", "C", "BKNG",
        "AMT", "PGR", "LMT", "BSX", "MMC", "GILD", "ADP", "SCHW", "CI", "MU", "ELV", "REGN", "ADI",
        "SO", "KLAC", "DUK", "VRTX", "SNPS", "BDX", "AON", "CME", "CDNS", "ETN", "WM", "NOC", "CSX",
        "MO", "ITW", "SHW", "ATVI", "EOG", "APD", "MCO", "EW", "MCK"
    ]

    total = len(symbols)
    pages = (total + limit - 1) // limit
    start = (page - 1) * limit
    end = start + limit
    paginated_symbols = symbols[start:end]

    results = []

    def fetch_quote(sym):
        try:
            qp = _build_quote_parts(sym)
            change = qp.price - qp.prev_close
            change_pct = (change / qp.prev_close * 100) if qp.prev_close else 0
            raw = {
                "symbol": sym, "name": sym,
                "price": qp.price, "change": change, "changePercent": change_pct,
                "volume": qp.volume, "marketCap": 0, "sector": None, "industry": None,
            }
            return normalise_quote(raw, sym)
        except Exception as e:
            logger.warning(f"Failed to load stock {sym}: {e}")
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_quote, sym) for sym in paginated_symbols]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
                
    # Restore original order
    results_map = {r["symbol"]: r for r in results}
    ordered_results = [results_map[sym] for sym in paginated_symbols if sym in results_map]

    return {
        "data": ordered_results,
        "total": total,
        "page": page,
        "pages": pages
    }


@router.get("/search/detailed")
async def search_stocks_detailed(q: str):
    """Frontend expects StockQuote[]."""
    q = (q or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if not hasattr(yf, "Search"):
        return []

    try:
        s = yf.Search(q)
        quotes = getattr(s, "quotes", None) or []
        symbols = []
        for item in quotes:
            sym = (item.get("symbol") or "").upper()
            quote_type = item.get("quoteType", "")
            if sym and quote_type in ["EQUITY", "ETF"]:
                symbols.append(sym)
                if len(symbols) >= 10:  # Limit concurrent fetches
                    break
        
        results = []
        def fetch_quote_detailed(sym):
            try:
                t = _ticker(sym)
                info = _get_info_best_effort(t)
                qp = _build_quote_parts(sym)
                change = qp.price - qp.prev_close
                change_pct = (change / qp.prev_close * 100) if qp.prev_close else 0
                raw = {
                    "symbol": sym,
                    "name": info.get("shortName") or info.get("longName") or sym,
                    "price": qp.price, "change": change, "changePercent": change_pct,
                    "volume": qp.volume, "marketCap": _safe_float(info.get("marketCap"), 0.0),
                    "sector": info.get("sector"), "industry": info.get("industry"),
                }
                return normalise_quote(raw, sym)
            except Exception as e:
                logger.warning(f"Failed to load stock {sym} for search: {e}")
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_quote_detailed, sym) for sym in symbols]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    results.append(res)

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


@router.get("/{symbol}/historical")
async def get_historical(symbol: str = Depends(sanitise_symbol_param), time_range: str = "1M"):
    """Frontend expects: GET /stocks/{symbol}/historical?range=1M returning HistoricalDataPoint[]."""
    time_range = (time_range or "1M").upper().strip()
    if time_range not in TIME_RANGE_TO_V8:
        raise HTTPException(status_code=400, detail=f"Invalid range: {time_range}")

    hist_key = make_key("historical", symbol, time_range)
    cached_hist = cache_get(hist_key)
    if cached_hist is not None:
        return cached_hist

    try:
        out = _yahoo_historical(symbol, time_range)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Historical data unavailable for {symbol}. Try again later.",
        )

    if not out:
        raise HTTPException(
            status_code=503,
            detail="Yahoo Finance returned empty historical data. Try again later.",
        )

<<<<<<< Updated upstream
    return normalise_historical(out)
=======
    cache_set(hist_key, out, ttl=TTL_HISTORICAL)
    return out
>>>>>>> Stashed changes


@router.get("/{symbol}/indicators")
async def get_indicators(symbol: str = Depends(sanitise_symbol_param)):
    """Frontend expects TechnicalIndicators."""

    ind_key = make_key("indicators", symbol)
    cached_ind = cache_get(ind_key)
    if cached_ind is not None:
        return cached_ind

    try:
        bars = _yahoo_historical(symbol, "1Y")
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Indicators data unavailable for {symbol}. Try again later.",
        )

    if not bars:
        raise HTTPException(
            status_code=503,
            detail="Yahoo Finance returned empty data for indicators. Try again later.",
        )

    close = pd.Series([b["close"] for b in bars], dtype=float)
    ma50  = close.rolling(window=50).mean().iloc[-1]  if len(close) >= 50  else close.mean()
    ma200 = close.rolling(window=200).mean().iloc[-1] if len(close) >= 200 else close.mean()
    rsi   = _compute_rsi(close)
    macd  = _compute_macd(close)

<<<<<<< Updated upstream
    raw_indicators = {
=======
    indicators_result = {
>>>>>>> Stashed changes
        "symbol": symbol,
        "ma50":  _safe_float(ma50,  0.0),
        "ma200": _safe_float(ma200, 0.0),
        "rsi":   rsi,
        "macd":  macd,
    }
<<<<<<< Updated upstream
    return normalise_indicators(raw_indicators, symbol)
=======
    cache_set(ind_key, indicators_result, ttl=TTL_HISTORICAL)
    return indicators_result
>>>>>>> Stashed changes


@router.get("/{symbol}/news")
async def get_stock_news(symbol: str = Depends(sanitise_symbol_param)):
    """Frontend expects NewsArticle[].

    For MVP, we use yfinance's Ticker.news when available. Later you can swap this
    to Twitter/X, NewsAPI, AlphaVantage news, etc.
    """
<<<<<<< Updated upstream
=======
    symbol = symbol.upper().strip()

    news_key = make_key("news", symbol)
    cached_news = cache_get(news_key)
    if cached_news is not None:
        return cached_news

>>>>>>> Stashed changes
    t = _ticker(symbol)
    items = getattr(t, "news", None) or []

    out: List[Dict[str, Any]] = []
    for item in items[:20]:
        ts = item.get("providerPublishTime")
        published = (
            datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat() if ts else datetime.now(timezone.utc).isoformat()
        )
<<<<<<< Updated upstream
        raw_article = {
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
        out.append(normalise_news_article(raw_article, len(out)))
=======
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
    cache_set(news_key, out, ttl=TTL_NEWS)
>>>>>>> Stashed changes
    return out


@router.post("/compare")
async def compare_stocks(payload: dict = Body(...)):
    """Frontend expects ComparisonData.

    POST /stocks/compare { symbols: string[] }
    """
    from app.api.utils.data_cleaner import clean_symbol as _clean_sym, clean_float as _cf, clean_price as _cp, clean_volume as _cv
    symbols = payload.get("symbols")
    if not isinstance(symbols, list) or not symbols:
        raise HTTPException(status_code=400, detail="symbols must be a non-empty array")

    # Sanitise and deduplicate symbols; reject obviously invalid ones
    cleaned_symbols: List[str] = []
    for s in symbols[:10]:  # hard cap at 10
        sym = _clean_sym(str(s))
        if sym and sym not in cleaned_symbols:
            cleaned_symbols.append(sym)

    if not cleaned_symbols:
        raise HTTPException(status_code=400, detail="No valid symbols provided")

    data: Dict[str, Any] = {}

    for sym in cleaned_symbols:
        t = _ticker(sym)
        info = _get_info_best_effort(t)
        qp = _build_quote_parts(sym)
        change = _cf(qp.price - qp.prev_close)
        change_pct = _cf((change / qp.prev_close * 100.0) if qp.prev_close else 0.0)

        hist = t.history(period="1mo", interval="1d", auto_adjust=True)
        historical = []
        if hist is not None and not hist.empty:
            hist = hist.reset_index()
            for _, row in hist.iterrows():
                dt = pd.to_datetime(row["Date"]).date().isoformat() if "Date" in hist.columns else ""
                close_val = _cp(row.get("Close"))
                if dt and close_val > 0:
                    historical.append({"date": dt, "close": close_val})

        data[sym] = {
            "name": clean_str(info.get("shortName") or info.get("longName") or sym, sym, 256),
            "price": _cp(qp.price),
            "change": change,
            "changePercent": change_pct,
            "marketCap": clean_market_cap(info.get("marketCap")),
            "peRatio": _cf(info.get("trailingPE") or info.get("forwardPE"), None) if (info.get("trailingPE") or info.get("forwardPE")) else None,
            "volume": _cv(qp.volume),
            "historical": historical,
        }

    return {"symbols": cleaned_symbols, "data": data}


# -----------------------------
# ML integration hook (stub)
# -----------------------------


@router.get("/{symbol}/predict")
async def predict_future_price(symbol: str = Depends(sanitise_symbol_param), horizon_days: int = 7):
    """Optional endpoint for later ML integration.

    You can replace the dummy logic with:
    - a local model call
    - a separate ML microservice
    - or a queue job (Celery) that stores predictions.
    """
    from app.api.utils.data_cleaner import clean_price as _cp, clean_int as _ci
    qp = _build_quote_parts(symbol)
    return {
        "symbol": symbol.upper(),
        "horizonDays": _ci(horizon_days, default=7, min_val=1, max_val=365),
        "asOf": datetime.now(timezone.utc).isoformat(),
        "predictedPrice": _cp(qp.price),
        "model": "stub_baseline",
    }