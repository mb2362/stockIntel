"""OpenAPI / Swagger documentation configuration for StockIntel API.

Import `configure_openapi` and call it with your FastAPI *app* instance
**after** all routers have been included but **before** the first request.

Usage (in main.py)::

    from app.api.docs.openapi_config import configure_openapi
    configure_openapi(app)
"""
from __future__ import annotations

from typing import Any, Dict

# FastAPI imports are deferred inside configure_openapi() so the pure-data
# constants remain importable in environments without fastapi installed.


# ---------------------------------------------------------------------------
# Reusable schema components
# ---------------------------------------------------------------------------

_COMPONENTS: Dict[str, Any] = {
    "schemas": {
        # ── Auth ──────────────────────────────────────────────────────────
        "Token": {
            "type": "object",
            "required": ["access_token", "token_type"],
            "properties": {
                "access_token": {
                    "type": "string",
                    "description": "JWT Bearer token. Include as `Authorization: Bearer <token>` on secured endpoints.",
                    "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                },
                "token_type": {
                    "type": "string",
                    "description": "Always `bearer`.",
                    "example": "bearer",
                },
            },
        },
        "UserCreate": {
            "type": "object",
            "required": ["username", "email", "password"],
            "properties": {
                "username": {"type": "string", "minLength": 3, "maxLength": 64, "example": "alice"},
                "email": {"type": "string", "format": "email", "example": "alice@example.com"},
                "password": {"type": "string", "minLength": 8, "format": "password", "example": "s3cr3t!"},
            },
        },
        "User": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "username": {"type": "string", "example": "alice"},
                "email": {"type": "string", "format": "email", "example": "alice@example.com"},
            },
        },
        # ── Stocks ────────────────────────────────────────────────────────
        "MACD": {
            "type": "object",
            "description": "Moving Average Convergence Divergence components.",
            "properties": {
                "value":     {"type": "number", "format": "double", "description": "MACD line (EMA12 − EMA26).", "example": 1.23},
                "signal":    {"type": "number", "format": "double", "description": "Signal line (9-period EMA of MACD).", "example": 0.98},
                "histogram": {"type": "number", "format": "double", "description": "MACD − Signal (momentum bar height).", "example": 0.25},
            },
        },
        "TechnicalIndicators": {
            "type": "object",
            "description": "Computed technical indicators for the most recent trading session.",
            "required": ["symbol", "ma50", "ma200", "rsi", "macd"],
            "properties": {
                "symbol": {"type": "string", "example": "AAPL"},
                "ma50":   {"type": "number", "format": "double", "description": "50-period simple moving average of close prices.", "example": 182.45},
                "ma200":  {"type": "number", "format": "double", "description": "200-period simple moving average of close prices.", "example": 175.32},
                "rsi":    {"type": "number", "format": "double", "minimum": 0, "maximum": 100, "description": "14-period Relative Strength Index.", "example": 58.7},
                "macd":   {"$ref": "#/components/schemas/MACD"},
            },
        },
        "HistoricalDataPoint": {
            "type": "object",
            "description": "A single OHLCV bar. `date` is an ISO-8601 date string for daily bars and an ISO-8601 datetime for intraday bars.",
            "required": ["date", "open", "high", "low", "close", "volume"],
            "properties": {
                "date":   {"type": "string", "example": "2024-01-15"},
                "open":   {"type": "number", "format": "double", "minimum": 0, "example": 183.92},
                "high":   {"type": "number", "format": "double", "minimum": 0, "example": 185.10},
                "low":    {"type": "number", "format": "double", "minimum": 0, "example": 182.30},
                "close":  {"type": "number", "format": "double", "minimum": 0, "example": 184.25},
                "volume": {"type": "integer", "minimum": 0, "example": 54_321_000},
            },
        },
        "StockQuote": {
            "type": "object",
            "description": "Real-time or near-real-time price snapshot for a single equity.",
            "required": ["symbol", "name", "price", "change", "changePercent"],
            "properties": {
                "symbol":          {"type": "string", "example": "AAPL"},
                "name":            {"type": "string", "example": "Apple Inc."},
                "price":           {"type": "number", "format": "double", "minimum": 0, "example": 184.25},
                "change":          {"type": "number", "format": "double", "description": "Absolute price change vs previous close.", "example": 1.35},
                "changePercent":   {"type": "number", "format": "double", "description": "Percentage price change vs previous close.", "example": 0.74},
                "volume":          {"type": "integer", "minimum": 0, "example": 54_321_000},
                "marketCap":       {"type": "number", "format": "double", "minimum": 0, "example": 2_850_000_000_000},
                "sector":          {"type": "string", "nullable": True, "example": "Technology"},
                "industry":        {"type": "string", "nullable": True, "example": "Consumer Electronics"},
                "open":            {"type": "number", "format": "double", "minimum": 0, "example": 183.92},
                "high":            {"type": "number", "format": "double", "minimum": 0, "example": 185.10},
                "low":             {"type": "number", "format": "double", "minimum": 0, "example": 182.30},
                "previousClose":   {"type": "number", "format": "double", "minimum": 0, "example": 182.90},
                "fiftyTwoWeekHigh":{"type": "number", "format": "double", "minimum": 0, "example": 199.62},
                "fiftyTwoWeekLow": {"type": "number", "format": "double", "minimum": 0, "example": 124.17},
                "peRatio":         {"type": "number", "format": "double", "nullable": True, "example": 29.5},
                "dividendYield":   {"type": "number", "format": "double", "nullable": True, "example": 0.0055},
                "beta":            {"type": "number", "format": "double", "nullable": True, "example": 1.24},
            },
        },
        "StockDetail": {
            "allOf": [{"$ref": "#/components/schemas/StockQuote"}],
            "description": "Extended stock info including company fundamentals.",
            "properties": {
                "description":   {"type": "string", "nullable": True, "example": "Apple Inc. designs, manufactures, and markets smartphones…"},
                "ceo":           {"type": "string", "nullable": True, "example": "Tim Cook"},
                "employees":     {"type": "integer", "nullable": True, "example": 164_000},
                "headquarters":  {"type": "string", "nullable": True, "example": "Cupertino"},
                "founded":       {"type": "string", "nullable": True, "example": "1976"},
                "website":       {"type": "string", "nullable": True, "example": "https://www.apple.com"},
            },
        },
        "SearchResult": {
            "type": "object",
            "description": "Lightweight ticker search result (no price data).",
            "required": ["symbol", "name"],
            "properties": {
                "symbol":   {"type": "string", "example": "AAPL"},
                "name":     {"type": "string", "example": "Apple Inc."},
                "type":     {"type": "string", "example": "EQUITY"},
                "region":   {"type": "string", "example": "US"},
                "currency": {"type": "string", "example": "USD"},
            },
        },
        "NewsArticle": {
            "type": "object",
            "required": ["id", "title", "source", "url", "publishedAt"],
            "properties": {
                "id":          {"type": "string", "example": "abc-123"},
                "title":       {"type": "string", "example": "Apple Beats Q1 Earnings Estimates"},
                "source":      {"type": "string", "example": "Yahoo Finance"},
                "url":         {"type": "string", "format": "uri", "example": "https://finance.yahoo.com/news/apple-beats-q1"},
                "publishedAt": {"type": "string", "format": "date-time", "example": "2024-02-01T14:30:00Z"},
                "summary":     {"type": "string", "nullable": True},
                "imageUrl":    {"type": "string", "format": "uri", "nullable": True},
                "sentiment":   {"type": "string", "enum": ["positive", "neutral", "negative"], "example": "neutral"},
            },
        },
        "PredictionResult": {
            "type": "object",
            "properties": {
                "symbol":         {"type": "string", "example": "AAPL"},
                "horizonDays":    {"type": "integer", "example": 7},
                "asOf":           {"type": "string", "format": "date-time"},
                "predictedPrice": {"type": "number", "format": "double"},
                "model":          {"type": "string", "example": "stub_baseline"},
            },
        },
        "PaginatedStocks": {
            "type": "object",
            "properties": {
                "data":  {"type": "array", "items": {"$ref": "#/components/schemas/StockQuote"}},
                "total": {"type": "integer", "example": 100},
                "page":  {"type": "integer", "example": 1},
                "pages": {"type": "integer", "example": 10},
            },
        },
        # ── Market ───────────────────────────────────────────────────────
        "MarketIndex": {
            "type": "object",
            "properties": {
                "symbol":        {"type": "string", "example": "^GSPC"},
                "name":          {"type": "string", "example": "S&P 500"},
                "value":         {"type": "number", "format": "double", "example": 5_123.45},
                "change":        {"type": "number", "format": "double", "example": 12.34},
                "changePercent": {"type": "number", "format": "double", "example": 0.24},
            },
        },
        "MarketOverview": {
            "type": "object",
            "properties": {
                "indices":      {"type": "array", "items": {"$ref": "#/components/schemas/MarketIndex"}},
                "marketStatus": {"type": "string", "enum": ["open", "closed", "pre-market", "after-hours"], "example": "open"},
                "lastUpdated":  {"type": "string", "format": "date-time"},
            },
        },
        "TrendingStock": {
            "type": "object",
            "properties": {
                "symbol":        {"type": "string", "example": "TSLA"},
                "name":          {"type": "string", "example": "Tesla, Inc."},
                "price":         {"type": "number", "format": "double"},
                "change":        {"type": "number", "format": "double"},
                "changePercent": {"type": "number", "format": "double"},
                "volume":        {"type": "integer"},
            },
        },
        # ── Watchlist ─────────────────────────────────────────────────────
        "WatchlistItem": {
            "type": "object",
            "properties": {
                "symbol":        {"type": "string", "example": "NVDA"},
                "name":          {"type": "string", "example": "NVIDIA Corporation"},
                "price":         {"type": "number", "format": "double"},
                "change":        {"type": "number", "format": "double"},
                "changePercent": {"type": "number", "format": "double"},
                "volume":        {"type": "integer"},
                "marketCap":     {"type": "number", "format": "double"},
                "addedAt":       {"type": "string", "format": "date-time"},
            },
        },
        # ── Errors ───────────────────────────────────────────────────────
        "HTTPError": {
            "type": "object",
            "properties": {
                "detail": {"type": "string", "example": "Not found"},
            },
        },
        "ValidationError": {
            "type": "object",
            "properties": {
                "detail": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "loc":  {"type": "array", "items": {"type": "string"}},
                            "msg":  {"type": "string"},
                            "type": {"type": "string"},
                        },
                    },
                },
            },
        },
    },
    "securitySchemes": {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": (
                "JWT token obtained from `POST /api/v1/auth/token`. "
                "Pass as `Authorization: Bearer <token>`."
            ),
        },
        "ApiKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "Static API key for server-to-server access (optional alternative to JWT).",
        },
    },
}

# Common error responses reused across operations
_ERROR_RESPONSES: Dict[str, Any] = {
    "400": {
        "description": "Bad Request – invalid query parameters or request body.",
        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/HTTPError"}}},
    },
    "401": {
        "description": "Unauthorised – missing or invalid Bearer token.",
        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/HTTPError"}}},
    },
    "422": {
        "description": "Unprocessable Entity – request validation failed.",
        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ValidationError"}}},
    },
    "503": {
        "description": "Service Unavailable – upstream Yahoo Finance API is down or rate-limited.",
        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/HTTPError"}}},
    },
}

# Tags with rich descriptions shown in the Swagger sidebar
_TAGS: list[Dict[str, str]] = [
    {
        "name": "stocks",
        "description": (
            "Real-time quotes, historical OHLCV, technical indicators, news, "
            "stock comparison, and ML price-prediction endpoints. "
            "Data sourced from Yahoo Finance via the v8 chart API."
        ),
    },
    {
        "name": "market",
        "description": (
            "Market-wide data: major index overview (S&P 500, NASDAQ, Dow Jones …), "
            "trending stocks, daily top gainers, and top losers."
        ),
    },
    {
        "name": "watchlist",
        "description": (
            "Manage the authenticated user's watchlist. "
            "All watchlist items are enriched with live price data on retrieval."
        ),
    },
    {
        "name": "auth",
        "description": (
            "User registration, JWT token issuance (`/auth/token`), "
            "and current-user profile (`/auth/users/me/`). "
            "Tokens expire after 30 minutes."
        ),
    },
    {
        "name": "portfolio",
        "description": "Portfolio management (stub – coming soon).",
    },
    {
        "name": "news",
        "description": "Global market news feed (stub – coming soon).",
    },
]


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------

def configure_openapi(app) -> None:  # app: FastAPI
    """Attach enriched OpenAPI schema to *app*.

    Call this once after all routers are registered::

        configure_openapi(app)
    """

    def _custom_openapi() -> Dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        from fastapi.openapi.utils import get_openapi
        schema = get_openapi(
            title="StockIntel API",
            version="1.0.0",
            summary="Real-time stock intelligence platform",
            description=(
                "## Overview\n\n"
                "**StockIntel** provides real-time equity data, technical indicators, "
                "portfolio & watchlist management, and ML-based price predictions.\n\n"
                "### Data freshness\n"
                "Quote endpoints cache results for **15 seconds** to respect Yahoo Finance "
                "rate limits while still providing near-real-time data.\n\n"
                "### Authentication\n"
                "Most read endpoints are public. Watchlist write operations require a "
                "**JWT Bearer token** obtained from `POST /api/v1/auth/token`.\n\n"
                "### Rate limits\n"
                "No hard rate limit is enforced by this API, but Yahoo Finance upstream "
                "throttling applies. Burst requests may receive `503` responses.\n\n"
                "### Time ranges\n"
                "Historical data supports: `1D`, `1W`, `1M`, `3M`, `1Y`, `5Y`."
            ),
            routes=app.routes,
            tags=_TAGS,
        )

        # Merge our rich component definitions
        schema.setdefault("components", {})
        schema["components"].setdefault("schemas", {}).update(_COMPONENTS["schemas"])
        schema["components"].setdefault("securitySchemes", {}).update(
            _COMPONENTS["securitySchemes"]
        )

        # Enrich individual operations
        _enrich_operations(schema)

        app.openapi_schema = schema
        return schema

    app.openapi = _custom_openapi  # type: ignore[method-assign]


# ---------------------------------------------------------------------------
# Per-operation enrichment
# ---------------------------------------------------------------------------

def _enrich_operations(schema: Dict[str, Any]) -> None:
    """Walk all paths and attach richer responses / examples / summaries."""
    paths: Dict[str, Any] = schema.get("paths", {})

    _patch = {
        # ── Stocks ───────────────────────────────────────────────────────
        "/api/v1/stocks/search": {
            "get": {
                "summary": "Search tickers",
                "description": "Full-text ticker/company search. Returns up to 10 matching equities and ETFs.",
                "responses": {
                    "200": {
                        "description": "Array of matching search results.",
                        "content": {
                            "application/json": {
                                "schema": {"type": "array", "items": {"$ref": "#/components/schemas/SearchResult"}},
                                "example": [
                                    {"symbol": "AAPL", "name": "Apple Inc.", "type": "EQUITY", "region": "US", "currency": "USD"},
                                ],
                            }
                        },
                    },
                    **_ERROR_RESPONSES,
                },
            }
        },
        "/api/v1/stocks": {
            "get": {
                "summary": "List popular stocks (paginated)",
                "description": "Returns a paginated list of up to 100 popular US equities with live quote data.",
                "responses": {
                    "200": {
                        "description": "Paginated stock list.",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/PaginatedStocks"},
                            }
                        },
                    },
                    **_ERROR_RESPONSES,
                },
            }
        },
        "/api/v1/stocks/{symbol}/quote": {
            "get": {
                "summary": "Real-time stock quote",
                "description": "Fetch a real-time price snapshot for any equity. Cached for 15 s.",
                "responses": {
                    "200": {
                        "description": "Stock quote.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/StockQuote"}},
                        },
                    },
                    **_ERROR_RESPONSES,
                },
            }
        },
        "/api/v1/stocks/{symbol}/info": {
            "get": {
                "summary": "Detailed stock information",
                "description": "Returns price data **plus** company fundamentals (sector, description, employees …).",
                "responses": {
                    "200": {
                        "description": "Extended stock detail.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/StockDetail"}},
                        },
                    },
                    **_ERROR_RESPONSES,
                },
            }
        },
        "/api/v1/stocks/{symbol}/historical": {
            "get": {
                "summary": "Historical OHLCV bars",
                "description": (
                    "Fetch historical open/high/low/close/volume bars. "
                    "The `time_range` query parameter controls the lookback window and bar interval:\n\n"
                    "| time_range | Interval | Lookback |\n"
                    "|-----------|----------|----------|\n"
                    "| `1D` | 5 min | 1 day |\n"
                    "| `1W` | 30 min | 5 days |\n"
                    "| `1M` | 1 day | 1 month |\n"
                    "| `3M` | 1 day | 3 months |\n"
                    "| `1Y` | 1 day | 1 year |\n"
                    "| `5Y` | 1 week | 5 years |"
                ),
                "responses": {
                    "200": {
                        "description": "Array of OHLCV bars sorted ascending by date.",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/HistoricalDataPoint"},
                                },
                            }
                        },
                    },
                    **_ERROR_RESPONSES,
                },
            }
        },
        "/api/v1/stocks/{symbol}/indicators": {
            "get": {
                "summary": "Technical indicators",
                "description": "Compute MA50, MA200, RSI (14-period), and MACD from 1-year daily history.",
                "responses": {
                    "200": {
                        "description": "Technical indicator values.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/TechnicalIndicators"}},
                        },
                    },
                    **_ERROR_RESPONSES,
                },
            }
        },
        "/api/v1/stocks/{symbol}/news": {
            "get": {
                "summary": "Stock-specific news",
                "description": "Latest news articles for the given ticker from Yahoo Finance (up to 20 items).",
                "responses": {
                    "200": {
                        "description": "Array of news articles.",
                        "content": {
                            "application/json": {
                                "schema": {"type": "array", "items": {"$ref": "#/components/schemas/NewsArticle"}},
                            }
                        },
                    },
                    **_ERROR_RESPONSES,
                },
            }
        },
        "/api/v1/stocks/compare": {
            "post": {
                "summary": "Compare multiple stocks",
                "description": "Side-by-side comparison of up to 10 equities including 1-month historical close prices.",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["symbols"],
                                "properties": {
                                    "symbols": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 1,
                                        "maxItems": 10,
                                        "example": ["AAPL", "MSFT", "GOOGL"],
                                    }
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "200": {"description": "Comparison data keyed by symbol."},
                    **_ERROR_RESPONSES,
                },
            }
        },
        "/api/v1/stocks/{symbol}/predict": {
            "get": {
                "summary": "Price prediction (stub)",
                "description": (
                    "⚠️ **Stub endpoint** – currently returns a flat-price baseline. "
                    "Replace the body with a real ML model call when ready."
                ),
                "responses": {
                    "200": {
                        "description": "Predicted price for the given horizon.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/PredictionResult"}},
                        },
                    },
                    **_ERROR_RESPONSES,
                },
            }
        },
        # ── Market ───────────────────────────────────────────────────────
        "/api/v1/market/overview": {
            "get": {
                "summary": "Market overview",
                "description": "Returns major global index values (S&P 500, NASDAQ, Dow Jones, FTSE, Nikkei …) plus market status.",
                "responses": {
                    "200": {
                        "description": "Market overview with indices.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/MarketOverview"}},
                        },
                    },
                    **_ERROR_RESPONSES,
                },
            }
        },
        "/api/v1/market/trending": {
            "get": {
                "summary": "Trending stocks",
                "description": "Live quotes for the 10 most-watched US equities.",
                "responses": {
                    "200": {
                        "description": "Array of trending stock quotes.",
                        "content": {
                            "application/json": {
                                "schema": {"type": "array", "items": {"$ref": "#/components/schemas/TrendingStock"}},
                            }
                        },
                    },
                    **_ERROR_RESPONSES,
                },
            }
        },
        "/api/v1/market/gainers": {
            "get": {
                "summary": "Top gainers",
                "description": "Top 5 stocks with the highest positive `changePercent` in the current session.",
                "responses": {
                    "200": {
                        "description": "Array of top gainers.",
                        "content": {
                            "application/json": {
                                "schema": {"type": "array", "items": {"$ref": "#/components/schemas/TrendingStock"}},
                            }
                        },
                    },
                    **_ERROR_RESPONSES,
                },
            }
        },
        "/api/v1/market/losers": {
            "get": {
                "summary": "Top losers",
                "description": "Top 5 stocks with the most negative `changePercent` in the current session.",
                "responses": {
                    "200": {
                        "description": "Array of top losers.",
                        "content": {
                            "application/json": {
                                "schema": {"type": "array", "items": {"$ref": "#/components/schemas/TrendingStock"}},
                            }
                        },
                    },
                    **_ERROR_RESPONSES,
                },
            }
        },
        # ── Watchlist ─────────────────────────────────────────────────────
        "/api/v1/watchlist": {
            "get": {
                "summary": "Get watchlist",
                "description": "Returns all tickers on the current user's watchlist, enriched with live price data.",
                "security": [{"BearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "Array of watchlist items with live prices.",
                        "content": {
                            "application/json": {
                                "schema": {"type": "array", "items": {"$ref": "#/components/schemas/WatchlistItem"}},
                            }
                        },
                    },
                    **_ERROR_RESPONSES,
                },
            },
            "post": {
                "summary": "Add ticker to watchlist",
                "description": "Adds the given symbol to the current user's watchlist and returns its live quote.",
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["symbol"],
                                "properties": {"symbol": {"type": "string", "example": "NVDA"}},
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Newly added watchlist item.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/WatchlistItem"}},
                        },
                    },
                    **_ERROR_RESPONSES,
                },
            },
        },
        "/api/v1/watchlist/{symbol}": {
            "delete": {
                "summary": "Remove ticker from watchlist",
                "security": [{"BearerAuth": []}],
                "responses": {
                    "200": {"description": "Symbol removed (idempotent)."},
                    **_ERROR_RESPONSES,
                },
            }
        },
        # ── Auth ─────────────────────────────────────────────────────────
        "/api/v1/auth/token": {
            "post": {
                "summary": "Login – obtain JWT",
                "description": (
                    "Authenticate with `username` + `password` (form data). "
                    "Returns a JWT Bearer token valid for 30 minutes."
                ),
                "responses": {
                    "200": {
                        "description": "Access token.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Token"}},
                        },
                    },
                    "401": _ERROR_RESPONSES["401"],
                },
            }
        },
        "/api/v1/auth/users/": {
            "post": {
                "summary": "Register new user",
                "responses": {
                    "200": {
                        "description": "Created user.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/User"}},
                        },
                    },
                    "400": _ERROR_RESPONSES["400"],
                },
            }
        },
        "/api/v1/auth/users/me/": {
            "get": {
                "summary": "Current user profile",
                "security": [{"BearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "Authenticated user.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/User"}},
                        },
                    },
                    "401": _ERROR_RESPONSES["401"],
                },
            }
        },
    }

    for path, methods in _patch.items():
        if path not in paths:
            continue
        for method, overrides in methods.items():
            if method not in paths[path]:
                continue
            op = paths[path][method]
            # Merge top-level keys (summary, description, security, responses, requestBody)
            for key, val in overrides.items():
                if key == "responses":
                    op.setdefault("responses", {}).update(val)
                else:
                    op[key] = val
