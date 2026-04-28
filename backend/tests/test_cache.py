"""
test_cache.py  –  Full coverage for app/cache.py and cache integration in endpoints.

Runs without a real Redis server: uses fakeredis when available, falls back to the
in-memory store otherwise.  All tests are hermetic (no network, no DB).
"""
import importlib
import json
import os
import sys
import time
import types
import unittest
import unittest.mock as mock

# ── bootstrap ──────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
import conftest  # noqa – registers all third-party stubs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── helpers ────────────────────────────────────────────────────────────────────

def _run(coro):
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ==============================================================================
# 1.  _InMemoryStore
# ==============================================================================

class TestInMemoryStore(unittest.TestCase):
    def setUp(self):
        from app.cache import _InMemoryStore
        self.store = _InMemoryStore()

    # basic set/get
    def test_set_and_get(self):
        self.store.set("k", "v")
        self.assertEqual(self.store.get("k"), "v")

    def test_get_missing_returns_none(self):
        self.assertIsNone(self.store.get("no_such_key"))

    # TTL expiry
    def test_expired_key_returns_none(self):
        self.store.set("exp", "val", ex=1)
        # Force expiry by manipulating internal store
        key, (val, _) = list(self.store._store.items())[0]
        self.store._store[key] = (val, time.time() - 1)
        self.assertIsNone(self.store.get("exp"))

    def test_non_expired_key_returns_value(self):
        self.store.set("live", "alive", ex=60)
        self.assertEqual(self.store.get("live"), "alive")

    def test_zero_ex_means_no_expiry(self):
        self.store.set("forever", "here", ex=0)
        self.assertEqual(self.store.get("forever"), "here")

    # delete
    def test_delete_removes_key(self):
        self.store.set("del_me", "x")
        self.store.delete("del_me")
        self.assertIsNone(self.store.get("del_me"))

    def test_delete_nonexistent_is_safe(self):
        self.store.delete("ghost")  # must not raise

    # flushdb
    def test_flushdb_clears_all(self):
        self.store.set("a", "1")
        self.store.set("b", "2")
        self.store.flushdb()
        self.assertIsNone(self.store.get("a"))
        self.assertIsNone(self.store.get("b"))

    # keys
    def test_keys_returns_live_keys(self):
        self.store.set("x1", "a")
        self.store.set("x2", "b")
        ks = self.store.keys()
        self.assertIn("x1", ks)
        self.assertIn("x2", ks)

    def test_keys_with_pattern(self):
        self.store.set("stock:AAPL", "1")
        self.store.set("stock:MSFT", "2")
        self.store.set("market:OV", "3")
        ks = self.store.keys("stock:*")
        self.assertIn("stock:AAPL", ks)
        self.assertIn("stock:MSFT", ks)
        self.assertNotIn("market:OV", ks)

    def test_keys_excludes_expired(self):
        self.store.set("old", "v", ex=1)
        self.store._store["old"] = ("v", time.time() - 5)
        ks = self.store.keys()
        self.assertNotIn("old", ks)


# ==============================================================================
# 2.  Public API (cache_get / cache_set / cache_delete / cache_flush / make_key)
# ==============================================================================

class TestPublicAPI(unittest.TestCase):
    def setUp(self):
        # Reload module and force in-memory fallback (no real Redis)
        if "app.cache" in sys.modules:
            del sys.modules["app.cache"]
        import app.cache as c
        c._redis_client = None  # ensure no Redis
        # Patch _get_redis to always return None
        self._patcher = mock.patch.object(c, "_get_redis", return_value=None)
        self._patcher.start()
        c._fallback_store.flushdb()
        self.c = c

    def tearDown(self):
        self._patcher.stop()

    def test_make_key_single(self):
        self.assertEqual(self.c.make_key("quote", "AAPL"), "stockintel:quote:AAPL")

    def test_make_key_multiple(self):
        self.assertEqual(self.c.make_key("hist", "AAPL", "1M"), "stockintel:hist:AAPL:1M")

    def test_cache_set_and_get_dict(self):
        self.c.cache_set("stockintel:test:1", {"price": 150.0})
        result = self.c.cache_get("stockintel:test:1")
        self.assertEqual(result, {"price": 150.0})

    def test_cache_set_and_get_list(self):
        self.c.cache_set("stockintel:test:2", [1, 2, 3])
        self.assertEqual(self.c.cache_get("stockintel:test:2"), [1, 2, 3])

    def test_cache_miss_returns_none(self):
        self.assertIsNone(self.c.cache_get("stockintel:miss"))

    def test_cache_delete(self):
        self.c.cache_set("stockintel:del", "x")
        self.c.cache_delete("stockintel:del")
        self.assertIsNone(self.c.cache_get("stockintel:del"))

    def test_cache_flush(self):
        self.c.cache_set("stockintel:a", 1)
        self.c.cache_set("stockintel:b", 2)
        self.c.cache_flush()
        self.assertIsNone(self.c.cache_get("stockintel:a"))

    def test_cache_set_returns_true_on_success(self):
        ok = self.c.cache_set("stockintel:ok", {"v": 1})
        self.assertTrue(ok)

    def test_cache_set_handles_exception_gracefully(self):
        # Patch _store() to raise
        with mock.patch.object(self.c, "_store", side_effect=Exception("boom")):
            result = self.c.cache_set("k", "v")
            self.assertFalse(result)

    def test_cache_get_handles_exception_gracefully(self):
        with mock.patch.object(self.c, "_store", side_effect=Exception("boom")):
            self.assertIsNone(self.c.cache_get("k"))

    def test_cache_delete_handles_exception_gracefully(self):
        with mock.patch.object(self.c, "_store", side_effect=Exception("boom")):
            self.c.cache_delete("k")  # must not raise

    def test_cache_flush_handles_exception_gracefully(self):
        with mock.patch.object(self.c, "_store", side_effect=Exception("boom")):
            self.c.cache_flush()  # must not raise

    def test_ttl_constants_positive(self):
        self.assertGreater(self.c.TTL_QUOTE, 0)
        self.assertGreater(self.c.TTL_HISTORICAL, 0)
        self.assertGreater(self.c.TTL_INFO, 0)
        self.assertGreater(self.c.TTL_OVERVIEW, 0)
        self.assertGreater(self.c.TTL_NEWS, 0)
        self.assertGreater(self.c.TTL_PREDICT, 0)


# ==============================================================================
# 3.  invalidate_quote
# ==============================================================================

class TestInvalidateQuote(unittest.TestCase):
    def setUp(self):
        if "app.cache" in sys.modules:
            del sys.modules["app.cache"]
        import app.cache as c
        c._redis_client = None
        self._patcher = mock.patch.object(c, "_get_redis", return_value=None)
        self._patcher.start()
        c._fallback_store.flushdb()
        self.c = c

    def tearDown(self):
        self._patcher.stop()

    def test_invalidate_removes_all_symbol_keys(self):
        suffixes = ("quote", "historical", "info", "indicators", "news")
        for s in suffixes:
            self.c.cache_set(self.c.make_key(s, "AAPL"), {"data": s})
        self.c.invalidate_quote("AAPL")
        for s in suffixes:
            self.assertIsNone(self.c.cache_get(self.c.make_key(s, "AAPL")))

    def test_invalidate_is_case_insensitive(self):
        key = self.c.make_key("quote", "AAPL")
        self.c.cache_set(key, {"v": 1})
        self.c.invalidate_quote("aapl")  # lowercase input
        self.assertIsNone(self.c.cache_get(key))

    def test_invalidate_does_not_remove_other_symbols(self):
        self.c.cache_set(self.c.make_key("quote", "AAPL"), {"v": 1})
        self.c.cache_set(self.c.make_key("quote", "MSFT"), {"v": 2})
        self.c.invalidate_quote("AAPL")
        self.assertIsNotNone(self.c.cache_get(self.c.make_key("quote", "MSFT")))


# ==============================================================================
# 4.  @cached decorator
# ==============================================================================

class TestCachedDecorator(unittest.TestCase):
    def setUp(self):
        if "app.cache" in sys.modules:
            del sys.modules["app.cache"]
        import app.cache as c
        c._redis_client = None
        self._patcher = mock.patch.object(c, "_get_redis", return_value=None)
        self._patcher.start()
        c._fallback_store.flushdb()
        self.c = c

    def tearDown(self):
        self._patcher.stop()

    def test_cached_decorator_caches_result(self):
        call_count = {"n": 0}

        @self.c.cached(ttl=60)
        def expensive(x):
            call_count["n"] += 1
            return {"value": x * 2}

        r1 = expensive(5)
        r2 = expensive(5)
        self.assertEqual(r1, {"value": 10})
        self.assertEqual(r2, {"value": 10})
        self.assertEqual(call_count["n"], 1)  # only called once

    def test_cached_decorator_different_args_call_separately(self):
        call_count = {"n": 0}

        @self.c.cached(ttl=60)
        def expensive(x):
            call_count["n"] += 1
            return x

        expensive(1)
        expensive(2)
        self.assertEqual(call_count["n"], 2)

    def test_cached_exposes_ttl(self):
        @self.c.cached(ttl=42)
        def fn():
            return 1

        self.assertEqual(fn._cache_ttl, 42)

    def test_cached_with_custom_key_fn(self):
        call_count = {"n": 0}

        @self.c.cached(ttl=60, key_fn=lambda sym: f"stockintel:custom:{sym}")
        def fetch(sym):
            call_count["n"] += 1
            return {"sym": sym}

        fetch("AAPL")
        fetch("AAPL")
        self.assertEqual(call_count["n"], 1)

    def test_cached_with_kwargs(self):
        call_count = {"n": 0}

        @self.c.cached(ttl=60)
        def fetch(sym, period="1M"):
            call_count["n"] += 1
            return {"sym": sym, "period": period}

        fetch("AAPL", period="3M")
        fetch("AAPL", period="3M")
        self.assertEqual(call_count["n"], 1)

    def test_cached_preserves_function_name(self):
        @self.c.cached(ttl=60)
        def my_function():
            return 1

        self.assertEqual(my_function.__name__, "my_function")


# ==============================================================================
# 5.  _get_redis  (connection logic)
# ==============================================================================

class TestGetRedis(unittest.TestCase):
    def setUp(self):
        if "app.cache" in sys.modules:
            del sys.modules["app.cache"]

    def test_returns_none_when_redis_unavailable(self):
        import app.cache as c
        c._redis_client = None
        with mock.patch.dict("sys.modules", {"redis": None}):
            # redis import will fail
            result = c._get_redis()
        self.assertIsNone(result)

    def test_returns_cached_client_if_already_connected(self):
        import app.cache as c
        fake_client = mock.MagicMock()
        c._redis_client = fake_client
        result = c._get_redis()
        self.assertIs(result, fake_client)
        c._redis_client = None  # cleanup

    def test_returns_none_on_ping_failure(self):
        import app.cache as c
        c._redis_client = None
        fake_redis_mod = types.ModuleType("redis")
        fake_client = mock.MagicMock()
        fake_client.ping.side_effect = Exception("connection refused")
        fake_redis_mod.Redis = mock.MagicMock()
        fake_redis_mod.Redis.from_url = mock.MagicMock(return_value=fake_client)
        with mock.patch.dict("sys.modules", {"redis": fake_redis_mod}):
            result = c._get_redis()
        self.assertIsNone(result)

    def test_returns_client_on_successful_connect(self):
        import app.cache as c
        c._redis_client = None
        fake_redis_mod = types.ModuleType("redis")
        fake_client = mock.MagicMock()
        fake_client.ping.return_value = True
        fake_redis_mod.Redis = mock.MagicMock()
        fake_redis_mod.Redis.from_url = mock.MagicMock(return_value=fake_client)
        with mock.patch.dict("sys.modules", {"redis": fake_redis_mod}):
            result = c._get_redis()
        self.assertIs(result, fake_client)
        c._redis_client = None  # cleanup


# ==============================================================================
# 6.  Cache integration: stocks endpoint handlers
# ==============================================================================

class TestStocksCacheIntegration(unittest.TestCase):
    """Verify that endpoint handlers read from and write to the cache."""

    @classmethod
    def setUpClass(cls):
        # Ensure cache module is loaded with in-memory fallback
        if "app.cache" in sys.modules:
            del sys.modules["app.cache"]
        import app.cache as c
        c._redis_client = None
        cls._patcher = mock.patch.object(c, "_get_redis", return_value=None)
        cls._patcher.start()
        c._fallback_store.flushdb()
        cls.cache = c

        # Import stocks module (stubs registered by conftest)
        if "app.api.endpoints.stocks" in sys.modules:
            del sys.modules["app.api.endpoints.stocks"]
        cls.stocks = importlib.import_module("app.api.endpoints.stocks")

    @classmethod
    def tearDownClass(cls):
        cls._patcher.stop()

    def setUp(self):
        # Clear cache between tests
        self.cache._fallback_store.flushdb()
        # Also reset in-process _quote_cache
        self.stocks._quote_cache.clear()

    # ── _build_quote_parts ─────────────────────────────────────────────────────

    def _mock_yahoo_quote(self, symbol):
        return {"regularMarketPrice": 150.0, "chartPreviousClose": 148.0,
                "regularMarketDayOpen": 149.0, "regularMarketDayHigh": 151.0,
                "regularMarketDayLow": 147.0, "regularMarketVolume": 1000000}

    def test_build_quote_parts_writes_to_cache(self):
        with mock.patch.object(self.stocks, "_yahoo_quote", self._mock_yahoo_quote):
            qp = self.stocks._build_quote_parts("AAPL_WRITE")
        key = self.cache.make_key("quote_parts", "AAPL_WRITE")
        cached = self.cache.cache_get(key)
        self.assertIsNotNone(cached)
        self.assertIn("price", cached)

    def test_build_quote_parts_reads_from_cache(self):
        key = self.cache.make_key("quote_parts", "MSFT")
        self.cache.cache_set(key, {
            "price": 999.0, "prev_close": 998.0,
            "open": 997.0, "high": 1000.0, "low": 996.0, "volume": 500,
        }, ttl=60)
        qp = self.stocks._build_quote_parts("MSFT")
        self.assertEqual(qp.price, 999.0)

    def test_build_quote_parts_in_memory_cache_takes_priority(self):
        # Put stale data in in-memory cache
        from dataclasses import asdict
        qp_stale = self.stocks.QuoteParts(
            price=111.0, prev_close=110.0, open=109.0,
            high=112.0, low=108.0, volume=100,
        )
        self.stocks._quote_cache["CACHED"] = {"time": time.time(), "data": qp_stale}
        result = self.stocks._build_quote_parts("CACHED")
        self.assertEqual(result.price, 111.0)

    # ── get_stock_quote ────────────────────────────────────────────────────────

    def test_get_stock_quote_caches_result(self):
        with mock.patch.object(self.stocks, "_yahoo_quote", self._mock_yahoo_quote):
            result = _run(self.stocks.get_stock_quote("AAPL_QUOTE"))
        key = self.cache.make_key("quote", "AAPL_QUOTE")
        self.assertIsNotNone(self.cache.cache_get(key))

    def test_get_stock_quote_reads_from_cache(self):
        key = self.cache.make_key("quote", "TSLA")
        self.cache.cache_set(key, {"symbol": "TSLA", "price": 777.0, "cached": True}, ttl=60)
        result = _run(self.stocks.get_stock_quote("TSLA"))
        self.assertTrue(result.get("cached"))
        self.assertEqual(result["price"], 777.0)

    # ── get_historical ─────────────────────────────────────────────────────────

    def _make_bars(self):
        return [{"date": "2024-01-01", "open": 148.0, "high": 152.0,
                 "low": 147.0, "close": 150.0, "volume": 1000000}]

    def test_get_historical_caches_result(self):
        bars = self._make_bars()
        with mock.patch.object(self.stocks, "_yahoo_historical", return_value=bars):
            result = _run(self.stocks.get_historical("AAPL", "1M"))
        key = self.cache.make_key("historical", "AAPL", "1M")
        self.assertIsNotNone(self.cache.cache_get(key))

    def test_get_historical_reads_from_cache(self):
        bars = self._make_bars()
        key = self.cache.make_key("historical", "AAPL", "3M")
        self.cache.cache_set(key, bars, ttl=300)
        with mock.patch.object(self.stocks, "_yahoo_historical", side_effect=Exception("should not be called")):
            result = _run(self.stocks.get_historical("AAPL", "3M"))
        self.assertEqual(result, bars)

    def test_get_historical_invalid_range_raises(self):
        HTTPException = sys.modules["fastapi"].HTTPException
        with self.assertRaises(HTTPException) as ctx:
            _run(self.stocks.get_historical("AAPL", "99Y"))
        self.assertEqual(ctx.exception.status_code, 400)

    def test_get_historical_empty_data_raises_503(self):
        HTTPException = sys.modules["fastapi"].HTTPException
        with mock.patch.object(self.stocks, "_yahoo_historical", return_value=[]):
            with self.assertRaises(HTTPException) as ctx:
                _run(self.stocks.get_historical("AAPL", "1M"))
        self.assertEqual(ctx.exception.status_code, 503)

    def test_get_historical_exception_raises_503(self):
        HTTPException = sys.modules["fastapi"].HTTPException
        with mock.patch.object(self.stocks, "_yahoo_historical", side_effect=Exception("network error")):
            with self.assertRaises(HTTPException) as ctx:
                _run(self.stocks.get_historical("AAPL", "1M"))
        self.assertEqual(ctx.exception.status_code, 503)

    # ── get_indicators ─────────────────────────────────────────────────────────

    def test_get_indicators_caches_result(self):
        import pandas as pd
        n = 250
        bars = [{"date": f"2024-{i:03d}", "close": 100.0 + i,
                 "open": 100.0, "high": 110.0, "low": 90.0, "volume": 1000} for i in range(1, n+1)]
        with mock.patch.object(self.stocks, "_yahoo_historical", return_value=bars):
            result = _run(self.stocks.get_indicators("NVDA"))
        key = self.cache.make_key("indicators", "NVDA")
        self.assertIsNotNone(self.cache.cache_get(key))
        self.assertIn("ma50", result)
        self.assertIn("ma200", result)

    def test_get_indicators_reads_from_cache(self):
        key = self.cache.make_key("indicators", "AMD")
        cached_data = {"symbol": "AMD", "ma50": 100.0, "ma200": 90.0, "rsi": 55.0, "macd": {}}
        self.cache.cache_set(key, cached_data, ttl=300)
        with mock.patch.object(self.stocks, "_yahoo_historical", side_effect=Exception("no call")):
            result = _run(self.stocks.get_indicators("AMD"))
        self.assertEqual(result["ma50"], 100.0)

    def test_get_indicators_empty_data_raises_503(self):
        HTTPException = sys.modules["fastapi"].HTTPException
        with mock.patch.object(self.stocks, "_yahoo_historical", return_value=[]):
            with self.assertRaises(HTTPException) as ctx:
                _run(self.stocks.get_indicators("AAPL"))
        self.assertEqual(ctx.exception.status_code, 503)

    def test_get_indicators_exception_raises_503(self):
        HTTPException = sys.modules["fastapi"].HTTPException
        with mock.patch.object(self.stocks, "_yahoo_historical", side_effect=Exception("network")):
            with self.assertRaises(HTTPException) as ctx:
                _run(self.stocks.get_indicators("AAPL"))
        self.assertEqual(ctx.exception.status_code, 503)

    # ── get_stock_news ─────────────────────────────────────────────────────────

    def test_get_stock_news_caches_result(self):
        result = _run(self.stocks.get_stock_news("AAPL"))
        key = self.cache.make_key("news", "AAPL")
        # news list may be empty (stub ticker has no news), but cache key is set
        self.assertIsNotNone(self.cache.cache_get(key))

    def test_get_stock_news_reads_from_cache(self):
        key = self.cache.make_key("news", "MSFT")
        cached_news = [{"id": "1", "title": "Cached", "source": "Test", "url": "",
                        "publishedAt": "2024-01-01T00:00:00Z", "sentiment": "neutral"}]
        self.cache.cache_set(key, cached_news, ttl=600)
        result = _run(self.stocks.get_stock_news("MSFT"))
        self.assertEqual(result[0]["title"], "Cached")

    def test_get_stock_news_with_timestamp(self):
        """News items with providerPublishTime should parse correctly."""
        import time as t
        news_item = {
            "uuid": "abc123",
            "title": "Test News",
            "publisher": "Reuters",
            "link": "http://example.com",
            "providerPublishTime": int(t.time()),
            "summary": "A summary",
        }
        # Patch ticker to return news
        original_ticker = self.stocks._ticker

        class _FakeTicker:
            def __init__(self, sym, session=None):
                self.ticker = sym
                self.news = [news_item]

        with mock.patch.object(self.stocks, "_ticker", _FakeTicker):
            self.cache._fallback_store.flushdb()  # ensure cache miss
            result = _run(self.stocks.get_stock_news("AAPL"))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Test News")

    def test_get_stock_news_with_thumbnail(self):
        """News item with thumbnail dict should extract imageUrl."""
        import time as t
        news_item = {
            "uuid": "img123",
            "title": "Image News",
            "publisher": "Bloomberg",
            "link": "http://example.com",
            "providerPublishTime": int(t.time()),
            "thumbnail": {"resolutions": [{"url": "http://img.example.com/small.jpg"},
                                           {"url": "http://img.example.com/large.jpg"}]},
        }

        class _FakeTicker:
            def __init__(self, sym, session=None):
                self.ticker = sym
                self.news = [news_item]

        with mock.patch.object(self.stocks, "_ticker", _FakeTicker):
            self.cache._fallback_store.flushdb()
            result = _run(self.stocks.get_stock_news("AAPL"))
        self.assertIsNotNone(result[0]["imageUrl"])

    # ── misc stocks helpers ────────────────────────────────────────────────────

    def test_safe_float_none(self):
        self.assertEqual(self.stocks._safe_float(None), 0.0)

    def test_safe_float_nan(self):
        import math
        self.assertEqual(self.stocks._safe_float(float("nan")), 0.0)

    def test_safe_float_value(self):
        self.assertAlmostEqual(self.stocks._safe_float(3.14), 3.14)

    def test_safe_float_string(self):
        self.assertAlmostEqual(self.stocks._safe_float("2.5"), 2.5)

    def test_safe_float_bad_string(self):
        self.assertEqual(self.stocks._safe_float("abc"), 0.0)

    def test_safe_int_none(self):
        self.assertEqual(self.stocks._safe_int(None), 0)

    def test_safe_int_float(self):
        self.assertEqual(self.stocks._safe_int(3.7), 3)

    def test_compute_rsi_sufficient_data(self):
        import pandas as pd
        close = pd.Series([100.0 + i for i in range(30)])
        rsi = self.stocks._compute_rsi(close)
        self.assertIsInstance(rsi, float)

    def test_compute_rsi_insufficient_data(self):
        import pandas as pd
        close = pd.Series([100.0, 101.0])  # less than 14 periods
        rsi = self.stocks._compute_rsi(close)
        self.assertEqual(rsi, 0.0)

    def test_compute_macd_returns_dict(self):
        import pandas as pd
        close = pd.Series([100.0 + i * 0.5 for i in range(50)])
        macd = self.stocks._compute_macd(close)
        self.assertIn("value", macd)
        self.assertIn("signal", macd)
        self.assertIn("histogram", macd)

    def test_get_all_stocks_returns_paginated(self):
        with mock.patch.object(self.stocks, "_build_quote_parts") as mock_qp:
            from dataclasses import dataclass
            @dataclass
            class FakeQP:
                price: float = 100.0
                prev_close: float = 99.0
                open: float = 98.0
                high: float = 101.0
                low: float = 97.0
                volume: int = 1000000
            mock_qp.return_value = FakeQP()
            result = _run(self.stocks.get_all_stocks(page=1, limit=5))
        self.assertIn("data", result)
        self.assertIn("total", result)
        self.assertIn("page", result)
        self.assertIn("pages", result)

    def test_ping_endpoint(self):
        result = _run(self.stocks.ping())
        self.assertEqual(result["message"], "Stocks endpoint works")

    def test_search_stocks_empty_query(self):
        HTTPException = sys.modules["fastapi"].HTTPException
        with self.assertRaises(HTTPException) as ctx:
            _run(self.stocks.search_stocks(""))
        self.assertEqual(ctx.exception.status_code, 400)

    def test_search_stocks_no_yf_search(self):
        yf_stub = sys.modules["yfinance"]
        if hasattr(yf_stub, "Search"):
            delattr(yf_stub, "Search")
        result = _run(self.stocks.search_stocks("AAPL"))
        self.assertEqual(result, [])
        # Restore
        class _Search:
            def __init__(self, q):
                self.quotes = []
        yf_stub.Search = _Search

    def test_compare_stocks_empty_symbols(self):
        HTTPException = sys.modules["fastapi"].HTTPException
        with self.assertRaises(HTTPException):
            _run(self.stocks.compare_stocks({"symbols": []}))

    def test_compare_stocks_non_list(self):
        HTTPException = sys.modules["fastapi"].HTTPException
        with self.assertRaises(HTTPException):
            _run(self.stocks.compare_stocks({"symbols": "AAPL"}))

    def test_predict_future_price(self):
        with mock.patch.object(self.stocks, "_yahoo_quote", self._mock_yahoo_quote):
            result = _run(self.stocks.predict_future_price("AAPL_PRED", 7))
        self.assertIn("predictedPrice", result)
        self.assertEqual(result["symbol"], "AAPL_PRED")
        self.assertEqual(result["horizonDays"], 7)

    def test_get_top_gainers(self):
        with mock.patch.object(self.stocks, "_yahoo_quote", self._mock_yahoo_quote),              mock.patch.object(self.stocks, "_build_quote_parts") as mock_qp:
            from dataclasses import dataclass
            @dataclass
            class FakeQP:
                price: float = 110.0
                prev_close: float = 100.0
                open: float = 100.0
                high: float = 111.0
                low: float = 99.0
                volume: int = 1000000
            mock_qp.return_value = FakeQP()
            result = _run(self.stocks.get_top_gainers())
        self.assertIsInstance(result, list)

    def test_get_top_losers(self):
        with mock.patch.object(self.stocks, "_yahoo_quote", self._mock_yahoo_quote),              mock.patch.object(self.stocks, "_build_quote_parts") as mock_qp:
            from dataclasses import dataclass
            @dataclass
            class FakeQP:
                price: float = 90.0
                prev_close: float = 100.0
                open: float = 100.0
                high: float = 101.0
                low: float = 89.0
                volume: int = 1000000
            mock_qp.return_value = FakeQP()
            result = _run(self.stocks.get_top_losers())
        self.assertIsInstance(result, list)

    def test_build_quote_parts_raises_when_yahoo_fails(self):
        HTTPException = sys.modules["fastapi"].HTTPException
        with mock.patch.object(self.stocks, "_yahoo_quote", side_effect=Exception("fail")):
            with self.assertRaises(HTTPException) as ctx:
                self.stocks._build_quote_parts("BADTICKER_UNIQUE_12345")
        self.assertEqual(ctx.exception.status_code, 503)

    def test_build_quote_parts_returns_stale_cache_on_failure(self):
        """When Yahoo fails, stale in-process cache should be returned."""
        from dataclasses import dataclass
        @dataclass
        class FakeQP:
            price: float = 123.0
            prev_close: float = 122.0
            open: float = 121.0
            high: float = 124.0
            low: float = 120.0
            volume: int = 999

        sym = "STALE_TEST"
        # Put stale data in _quote_cache
        self.stocks._quote_cache[sym] = {"time": time.time() - 9999, "data": FakeQP()}
        with mock.patch.object(self.stocks, "_yahoo_quote", side_effect=Exception("network down")):
            result = self.stocks._build_quote_parts(sym)
        self.assertEqual(result.price, 123.0)


# ==============================================================================
# 7.  Market endpoint cache integration
# ==============================================================================

class TestMarketCacheIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if "app.cache" in sys.modules:
            del sys.modules["app.cache"]
        import app.cache as c
        c._redis_client = None
        cls._patcher = mock.patch.object(c, "_get_redis", return_value=None)
        cls._patcher.start()
        c._fallback_store.flushdb()
        cls.cache = c

        for mod in list(sys.modules.keys()):
            if "market" in mod and "app.api" in mod:
                del sys.modules[mod]
        cls.market = importlib.import_module("app.api.endpoints.market")

    @classmethod
    def tearDownClass(cls):
        cls._patcher.stop()

    def setUp(self):
        self.cache._fallback_store.flushdb()

    def test_get_market_overview_caches_result(self):
        with mock.patch.object(self.market, "_quote_basic", return_value={
            "price": 4500.0, "prev_close": 4490.0, "change": 10.0,
            "changePercent": 0.22, "volume": 1000000, "marketCap": 0, "name": "S&P 500",
        }):
            _run(self.market.get_market_overview())
        key = self.cache.make_key("market_overview")
        self.assertIsNotNone(self.cache.cache_get(key))

    def test_get_market_overview_reads_from_cache(self):
        key = self.cache.make_key("market_overview")
        fake_overview = {"indices": [], "marketStatus": "open", "lastUpdated": "now", "cached": True}
        self.cache.cache_set(key, fake_overview, ttl=60)
        result = _run(self.market.get_market_overview())
        self.assertTrue(result.get("cached"))

    def test_get_trending_stocks(self):
        with mock.patch.object(self.market, "_quote_basic", return_value={
            "price": 150.0, "prev_close": 148.0, "change": 2.0,
            "changePercent": 1.35, "volume": 1000000, "marketCap": 0, "name": "AAPL",
        }):
            result = _run(self.market.get_trending_stocks())
        self.assertIsInstance(result, list)

    def test_get_market_gainers(self):
        with mock.patch.object(self.market, "_quote_basic", return_value={
            "price": 200.0, "prev_close": 180.0, "change": 20.0,
            "changePercent": 11.1, "volume": 500000, "marketCap": 0, "name": "GAINER",
        }):
            result = _run(self.market.get_top_gainers())
        self.assertIsInstance(result, list)

    def test_get_market_losers(self):
        with mock.patch.object(self.market, "_quote_basic", return_value={
            "price": 80.0, "prev_close": 100.0, "change": -20.0,
            "changePercent": -20.0, "volume": 300000, "marketCap": 0, "name": "LOSER",
        }):
            result = _run(self.market.get_top_losers())
        self.assertIsInstance(result, list)

    def test_quote_basic_uses_in_memory_cache(self):
        """_quote_basic should serve from its own time-based cache."""
        self.market._quote_cache["^TEST"] = {
            "time": time.time(),
            "data": {"price": 5000.0, "changePercent": 0.1, "change": 5.0,
                     "volume": 1, "marketCap": 0, "name": "Test", "prev_close": 4995.0},
        }
        result = self.market._quote_basic("^TEST")
        self.assertEqual(result["price"], 5000.0)

    def test_quote_basic_raises_when_no_cache_and_fails(self):
        HTTPException = sys.modules["fastapi"].HTTPException
        # Ensure no cache
        self.market._quote_cache.pop("^FAIL", None)
        from app.api.endpoints import stocks as stocks_mod
        with mock.patch.object(stocks_mod, "_build_quote_parts", side_effect=HTTPException(503, "fail")):
            with self.assertRaises(HTTPException):
                self.market._quote_basic("^FAIL")


# ==============================================================================
# 8.  fakeredis integration (when available)
# ==============================================================================

class TestFakeRedisIntegration(unittest.TestCase):
    """Use fakeredis as a drop-in Redis for end-to-end cache path testing."""

    def setUp(self):
        try:
            import fakeredis
            self._fakeredis = fakeredis
        except ImportError:
            self.skipTest("fakeredis not installed")

        if "app.cache" in sys.modules:
            del sys.modules["app.cache"]
        import app.cache as c
        self.cache = c
        # Wire in fakeredis
        self.fake_server = self._fakeredis.FakeServer()
        fake_client = self._fakeredis.FakeRedis(server=self.fake_server)
        c._redis_client = fake_client

    def tearDown(self):
        if hasattr(self, "cache"):
            self.cache._redis_client = None

    def test_set_and_get_via_fakeredis(self):
        self.cache.cache_set("stockintel:fr:test", {"hello": "world"})
        result = self.cache.cache_get("stockintel:fr:test")
        self.assertEqual(result, {"hello": "world"})

    def test_delete_via_fakeredis(self):
        self.cache.cache_set("stockintel:fr:del", "bye")
        self.cache.cache_delete("stockintel:fr:del")
        self.assertIsNone(self.cache.cache_get("stockintel:fr:del"))

    def test_flush_via_fakeredis(self):
        self.cache.cache_set("stockintel:fr:a", 1)
        self.cache.cache_set("stockintel:fr:b", 2)
        self.cache.cache_flush()
        self.assertIsNone(self.cache.cache_get("stockintel:fr:a"))

    def test_make_key_and_get_via_fakeredis(self):
        key = self.cache.make_key("quote", "AAPL")
        self.cache.cache_set(key, {"price": 188.0}, ttl=30)
        result = self.cache.cache_get(key)
        self.assertEqual(result["price"], 188.0)

    def test_cached_decorator_via_fakeredis(self):
        calls = {"n": 0}

        @self.cache.cached(ttl=30)
        def fetch_price(sym):
            calls["n"] += 1
            return {"price": 150.0, "symbol": sym}

        r1 = fetch_price("AAPL")
        r2 = fetch_price("AAPL")
        self.assertEqual(calls["n"], 1)
        self.assertEqual(r1["price"], 150.0)
        self.assertEqual(r2["price"], 150.0)

    def test_invalidate_quote_via_fakeredis(self):
        for suffix in ("quote", "historical", "info"):
            key = self.cache.make_key(suffix, "TSLA")
            self.cache.cache_set(key, {"data": suffix}, ttl=60)
        self.cache.invalidate_quote("TSLA")
        for suffix in ("quote", "historical", "info"):
            self.assertIsNone(self.cache.cache_get(self.cache.make_key(suffix, "TSLA")))


if __name__ == "__main__":
    unittest.main()
