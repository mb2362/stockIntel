"""Tests for data cleaning/normalisation, OpenAPI docs, and security middleware."""
from __future__ import annotations

import math
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import Response

# ============================================================
# 1.  DATA CLEANER TESTS
# ============================================================
from app.api.utils.data_cleaner import (
    clean_float,
    clean_int,
    clean_str,
    clean_symbol,
    clean_percent,
    clean_price,
    clean_volume,
    clean_market_cap,
    normalise_quote,
    normalise_stock_detail,
    normalise_historical,
    normalise_historical_point,
    normalise_indicators,
    normalise_news_article,
    normalise_search_result,
    normalise_market_index,
    normalise_trending_stock,
    normalise_watchlist_item,
)


class TestCleanFloat:
    def test_normal_value(self):
        assert clean_float(3.14) == pytest.approx(3.14)

    def test_none_returns_default(self):
        assert clean_float(None) == 0.0

    def test_nan_returns_default(self):
        assert clean_float(float("nan")) == 0.0

    def test_inf_returns_default(self):
        assert clean_float(float("inf")) == 0.0
        assert clean_float(float("-inf")) == 0.0

    def test_string_number(self):
        assert clean_float("2.5") == pytest.approx(2.5)

    def test_invalid_string(self):
        assert clean_float("abc") == 0.0

    def test_clamp_min(self):
        assert clean_float(-5.0, min_val=0.0) == 0.0

    def test_clamp_max(self):
        assert clean_float(200.0, max_val=100.0) == 100.0

    def test_custom_default(self):
        assert clean_float(None, default=99.9) == pytest.approx(99.9)


class TestCleanInt:
    def test_normal_int(self):
        assert clean_int(42) == 42

    def test_float_input(self):
        assert clean_int(3.9) == 3

    def test_none_returns_default(self):
        assert clean_int(None) == 0

    def test_nan_float(self):
        assert clean_int(float("nan")) == 0

    def test_clamp_min(self):
        assert clean_int(-10, min_val=0) == 0

    def test_clamp_max(self):
        assert clean_int(1000, max_val=500) == 500


class TestCleanStr:
    def test_normal_string(self):
        assert clean_str("  hello  ") == "hello"

    def test_none_returns_default(self):
        assert clean_str(None) == ""

    def test_truncation(self):
        assert clean_str("abcdef", max_length=3) == "abc"

    def test_numeric_coercion(self):
        assert clean_str(42) == "42"

    def test_empty_string_returns_default(self):
        assert clean_str("   ", default="N/A") == "N/A"


class TestCleanSymbol:
    def test_uppercase_normalisation(self):
        assert clean_symbol("aapl") == "AAPL"

    def test_strips_invalid_chars(self):
        assert clean_symbol("AA PL!") == "AAPL"

    def test_index_prefix_kept(self):
        assert clean_symbol("^GSPC") == "^GSPC"

    def test_class_suffix_kept(self):
        assert clean_symbol("BRK.B") == "BRK.B"

    def test_truncation(self):
        long = "A" * 30
        assert len(clean_symbol(long)) <= 20


class TestCleanPercent:
    def test_normal(self):
        assert clean_percent(2.5) == pytest.approx(2.5)

    def test_clamps_at_minus_100(self):
        assert clean_percent(-200.0) == pytest.approx(-100.0)

    def test_clamps_at_10000(self):
        assert clean_percent(99999.0) == pytest.approx(10_000.0)


class TestCleanPrice:
    def test_positive_price(self):
        assert clean_price(184.25) == pytest.approx(184.25)

    def test_negative_clamped_to_zero(self):
        assert clean_price(-5.0) == 0.0

    def test_none(self):
        assert clean_price(None) == 0.0


class TestNormaliseQuote:
    def _raw(self):
        return {
            "symbol": "aapl",
            "name": "Apple Inc.",
            "price": 184.25,
            "change": 1.35,
            "changePercent": 0.74,
            "volume": 54_321_000,
            "marketCap": 2_850_000_000_000,
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "open": 183.92,
            "high": 185.10,
            "low": 182.30,
            "previousClose": 182.90,
            "fiftyTwoWeekHigh": 199.62,
            "fiftyTwoWeekLow": 124.17,
            "peRatio": 29.5,
            "dividendYield": 0.0055,
            "beta": 1.24,
        }

    def test_symbol_uppercased(self):
        result = normalise_quote(self._raw())
        assert result["symbol"] == "AAPL"

    def test_price_is_float(self):
        result = normalise_quote(self._raw())
        assert isinstance(result["price"], float)

    def test_volume_is_int(self):
        result = normalise_quote(self._raw())
        assert isinstance(result["volume"], int)

    def test_nan_price_becomes_zero(self):
        raw = self._raw()
        raw["price"] = float("nan")
        result = normalise_quote(raw)
        assert result["price"] == 0.0

    def test_negative_price_clamped(self):
        raw = self._raw()
        raw["price"] = -10.0
        result = normalise_quote(raw)
        assert result["price"] == 0.0

    def test_change_percent_clamped(self):
        raw = self._raw()
        raw["changePercent"] = -999.0
        result = normalise_quote(raw)
        assert result["changePercent"] == pytest.approx(-100.0)

    def test_all_required_keys_present(self):
        result = normalise_quote(self._raw())
        for key in ("symbol", "name", "price", "change", "changePercent", "volume"):
            assert key in result


class TestNormaliseHistorical:
    def test_zero_close_bar_dropped(self):
        bars = [
            {"date": "2024-01-01", "open": 1, "high": 2, "low": 0.5, "close": 0, "volume": 100},
            {"date": "2024-01-02", "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 200},
        ]
        result = normalise_historical(bars)
        assert len(result) == 1
        assert result[0]["date"] == "2024-01-02"

    def test_duplicate_dates_deduplicated(self):
        bar = {"date": "2024-01-01", "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 100}
        result = normalise_historical([bar, bar])
        assert len(result) == 1

    def test_ohlc_consistency_high_corrected(self):
        bar = {"date": "2024-01-01", "open": 10, "high": 5, "low": 4, "close": 9, "volume": 100}
        result = normalise_historical([bar])
        assert result[0]["high"] >= result[0]["open"]
        assert result[0]["high"] >= result[0]["close"]

    def test_empty_input(self):
        assert normalise_historical([]) == []


class TestNormaliseIndicators:
    def test_rsi_clamped(self):
        raw = {"symbol": "AAPL", "ma50": 180, "ma200": 175, "rsi": 150, "macd": {"value": 1, "signal": 0.5, "histogram": 0.5}}
        result = normalise_indicators(raw, "AAPL")
        assert result["rsi"] <= 100.0

    def test_symbol_normalised(self):
        raw = {"symbol": "aapl", "ma50": 180, "ma200": 175, "rsi": 55, "macd": {"value": 1, "signal": 0.5, "histogram": 0.5}}
        result = normalise_indicators(raw)
        assert result["symbol"] == "AAPL"

    def test_macd_structure_preserved(self):
        raw = {"symbol": "AAPL", "ma50": 180, "ma200": 175, "rsi": 55, "macd": {"value": 1.2, "signal": 0.9, "histogram": 0.3}}
        result = normalise_indicators(raw)
        assert "value" in result["macd"]
        assert "signal" in result["macd"]
        assert "histogram" in result["macd"]


class TestNormaliseNewsArticle:
    def test_title_truncated_at_512(self):
        raw = {"title": "X" * 1000, "id": "1", "source": "YF", "url": "https://example.com", "publishedAt": "2024-01-01T00:00:00Z", "sentiment": "neutral"}
        result = normalise_news_article(raw)
        assert len(result["title"]) <= 512

    def test_sentiment_defaults_to_neutral(self):
        raw = {"title": "Test", "id": "1", "source": "YF", "url": "https://example.com", "publishedAt": "2024-01-01T00:00:00Z"}
        result = normalise_news_article(raw)
        assert result["sentiment"] == "neutral"


class TestNormaliseSearchResult:
    def test_returns_none_for_empty_symbol(self):
        assert normalise_search_result({"symbol": ""}) is None

    def test_symbol_uppercased(self):
        result = normalise_search_result({"symbol": "msft", "name": "Microsoft"})
        assert result["symbol"] == "MSFT"


# ============================================================
# 2.  SECURITY MIDDLEWARE TESTS
# ============================================================
from app.api.security.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    sanitise_symbol_param,
)


def _make_test_app_with_middleware():
    """Create a minimal FastAPI app with both security middlewares."""
    _app = FastAPI()
    _app.add_middleware(SecurityHeadersMiddleware)
    _app.add_middleware(RateLimitMiddleware, requests_per_minute=5)

    @_app.get("/api/v1/test")
    async def _test_endpoint():
        return {"ok": True}

    @_app.get("/docs")
    async def _docs():
        return {"ok": "docs"}

    return _app


class TestSecurityHeadersMiddleware:
    @pytest.fixture(autouse=True)
    def client(self):
        self.client = TestClient(_make_test_app_with_middleware(), raise_server_exceptions=False)

    def test_x_content_type_options(self):
        r = self.client.get("/api/v1/test")
        assert r.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self):
        r = self.client.get("/api/v1/test")
        assert r.headers.get("x-frame-options") == "DENY"

    def test_hsts_header_present(self):
        r = self.client.get("/api/v1/test")
        hsts = r.headers.get("strict-transport-security", "")
        assert "max-age=31536000" in hsts

    def test_csp_header_present(self):
        r = self.client.get("/api/v1/test")
        assert "content-security-policy" in r.headers

    def test_cache_control_for_api_paths(self):
        r = self.client.get("/api/v1/test")
        assert "no-store" in r.headers.get("cache-control", "")

    def test_referrer_policy(self):
        r = self.client.get("/api/v1/test")
        assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


class TestRateLimitMiddleware:
    @pytest.fixture(autouse=True)
    def client(self):
        self.client = TestClient(_make_test_app_with_middleware(), raise_server_exceptions=False)

    def test_ratelimit_headers_present(self):
        r = self.client.get("/api/v1/test")
        assert "x-ratelimit-limit" in r.headers
        assert "x-ratelimit-remaining" in r.headers

    def test_ratelimit_limit_header_value(self):
        r = self.client.get("/api/v1/test")
        assert r.headers["x-ratelimit-limit"] == "5"

    def test_remaining_decrements(self):
        r1 = self.client.get("/api/v1/test")
        r2 = self.client.get("/api/v1/test")
        rem1 = int(r1.headers["x-ratelimit-remaining"])
        rem2 = int(r2.headers["x-ratelimit-remaining"])
        assert rem2 < rem1

    def test_429_after_limit_exceeded(self):
        for _ in range(5):
            self.client.get("/api/v1/test")
        r = self.client.get("/api/v1/test")
        assert r.status_code == 429

    def test_retry_after_header_on_429(self):
        for _ in range(6):
            r = self.client.get("/api/v1/test")
        if r.status_code == 429:
            assert "retry-after" in r.headers

    def test_docs_path_exempt_from_rate_limit(self):
        """Docs paths should never be rate-limited."""
        for _ in range(10):
            r = self.client.get("/docs")
        assert r.status_code != 429


class TestSanitiseSymbolParam:
    def test_valid_symbol_uppercased(self):
        assert sanitise_symbol_param("aapl") == "AAPL"

    def test_index_symbol_allowed(self):
        assert sanitise_symbol_param("^GSPC") == "^GSPC"

    def test_invalid_chars_raise_400(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            sanitise_symbol_param("AAPL; DROP TABLE stocks;")
        assert exc.value.status_code == 400

    def test_too_long_raises_400(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            sanitise_symbol_param("A" * 30)

    def test_empty_string_raises_400(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            sanitise_symbol_param("")

    def test_dot_allowed(self):
        assert sanitise_symbol_param("BRK.B") == "BRK.B"


# ============================================================
# 3.  OPENAPI DOCS TESTS
# ============================================================
from app.api.docs.openapi_config import configure_openapi


def _make_documented_app():
    from fastapi.routing import APIRouter
    _app = FastAPI()

    @_app.get("/api/v1/stocks/{symbol}/quote", tags=["stocks"])
    async def _quote(symbol: str):
        return {}

    @_app.get("/api/v1/market/overview", tags=["market"])
    async def _overview():
        return {}

    configure_openapi(_app)
    return _app


class TestOpenAPIConfig:
    @pytest.fixture(autouse=True)
    def schema(self):
        app = _make_documented_app()
        self.schema = app.openapi()

    def test_title_set(self):
        assert self.schema["info"]["title"] == "StockIntel API"

    def test_version_set(self):
        assert self.schema["info"]["version"] == "1.0.0"

    def test_stockquote_schema_present(self):
        assert "StockQuote" in self.schema["components"]["schemas"]

    def test_technical_indicators_schema_present(self):
        assert "TechnicalIndicators" in self.schema["components"]["schemas"]

    def test_bearer_auth_security_scheme_present(self):
        schemes = self.schema["components"].get("securitySchemes", {})
        assert "BearerAuth" in schemes

    def test_api_key_security_scheme_present(self):
        schemes = self.schema["components"].get("securitySchemes", {})
        assert "ApiKeyHeader" in schemes

    def test_tags_include_stocks(self):
        tag_names = [t["name"] for t in self.schema.get("tags", [])]
        assert "stocks" in tag_names

    def test_tags_include_auth(self):
        tag_names = [t["name"] for t in self.schema.get("tags", [])]
        assert "auth" in tag_names

    def test_historical_data_point_schema_present(self):
        assert "HistoricalDataPoint" in self.schema["components"]["schemas"]

    def test_macd_schema_present(self):
        assert "MACD" in self.schema["components"]["schemas"]

    def test_market_overview_schema_present(self):
        assert "MarketOverview" in self.schema["components"]["schemas"]

    def test_watchlist_item_schema_present(self):
        assert "WatchlistItem" in self.schema["components"]["schemas"]
