"""
test_stocks_logic.py – Tests for app/api/endpoints/stocks.py.
Covers: Yahoo API helpers, cache, quote building, all endpoints.
All network I/O and DB access is fully mocked.
"""
import sys, os, importlib, unittest, types, time
import unittest.mock as mock
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import conftest  # noqa
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

stocks = importlib.import_module("app.api.endpoints.stocks")
HTTPException = sys.modules["fastapi"].HTTPException


def _run(coro):
    import asyncio
    loop = asyncio.new_event_loop()
    try: return loop.run_until_complete(coro)
    finally: loop.close()


def _qp(price=155.0, prev=150.0):
    return stocks.QuoteParts(price=price, prev_close=prev,
        open=149.0, high=157.0, low=148.0, volume=1_000_000)


def _hist_df(rows=5, named=True):
    prices = [150.0 + i for i in range(rows)]
    idx = pd.date_range("2024-01-01", periods=rows, freq="D",
                        name="Date" if named else None)
    return pd.DataFrame({"Open": [p-1 for p in prices], "High": [p+2 for p in prices],
        "Low": [p-2 for p in prices], "Close": prices, "Volume": [1_000_000]*rows}, index=idx)


# ── Yahoo API helpers ─────────────────────────────────────────────────────────

class TestYahooQuote(unittest.TestCase):
    """_yahoo_quote returns dict from v8 chart meta."""

    def _mock_resp(self, meta):
        r = mock.MagicMock()
        r.raise_for_status = mock.MagicMock()
        r.json.return_value = {"chart": {"result": [{"meta": meta}]}}
        return r

    def test_returns_meta_dict(self):
        resp = self._mock_resp({"regularMarketPrice": 150.0, "chartPreviousClose": 148.0})
        stocks._session.get = mock.MagicMock(return_value=resp)
        result = stocks._yahoo_quote("AAPL")
        self.assertEqual(result.get("regularMarketPrice"), 150.0)

    def test_empty_result_returns_empty_dict(self):
        r = mock.MagicMock()
        r.raise_for_status = mock.MagicMock()
        r.json.return_value = {"chart": {"result": []}}
        stocks._session.get = mock.MagicMock(return_value=r)
        result = stocks._yahoo_quote("FAKE")
        self.assertEqual(result, {})

    def test_http_error_propagates(self):
        r = mock.MagicMock()
        r.raise_for_status.side_effect = Exception("404")
        stocks._session.get = mock.MagicMock(return_value=r)
        with self.assertRaises(Exception):
            stocks._yahoo_quote("BAD")


class TestYahooHistorical(unittest.TestCase):
    """_yahoo_historical returns list of OHLCV dicts."""

    def _mock_resp(self, timestamps, closes, opens=None, highs=None, lows=None, vols=None):
        n = len(timestamps)
        quote = {
            "close": closes, "open": opens or closes,
            "high": highs or closes, "low": lows or closes,
            "volume": vols or [1_000_000] * n
        }
        r = mock.MagicMock()
        r.raise_for_status = mock.MagicMock()
        r.json.return_value = {"chart": {"result": [{
            "timestamp": timestamps,
            "indicators": {"quote": [quote]}
        }]}}
        return r

    def test_returns_list_of_dicts(self):
        ts = [1_700_000_000 + i * 86400 for i in range(3)]
        r = self._mock_resp(ts, [100.0, 101.0, 102.0])
        stocks._session.get = mock.MagicMock(return_value=r)
        result = stocks._yahoo_historical("AAPL", "1M")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_each_point_has_ohlcv(self):
        ts = [1_700_000_000 + i * 86400 for i in range(3)]
        r = self._mock_resp(ts, [100.0, 101.0, 102.0])
        stocks._session.get = mock.MagicMock(return_value=r)
        result = stocks._yahoo_historical("AAPL", "1M")
        for pt in result:
            for f in ("date", "open", "high", "low", "close", "volume"):
                self.assertIn(f, pt)

    def test_zero_close_skipped(self):
        ts = [1_700_000_000, 1_700_086_400]
        r = self._mock_resp(ts, [0.0, 102.0])
        stocks._session.get = mock.MagicMock(return_value=r)
        result = stocks._yahoo_historical("AAPL", "1M")
        for pt in result:
            self.assertGreater(pt["close"], 0)

    def test_empty_result_returns_empty(self):
        r = mock.MagicMock()
        r.raise_for_status = mock.MagicMock()
        r.json.return_value = {"chart": {"result": []}}
        stocks._session.get = mock.MagicMock(return_value=r)
        self.assertEqual(stocks._yahoo_historical("FAKE", "1M"), [])

    def test_intraday_uses_iso_format(self):
        ts = [1_700_000_000]
        r = self._mock_resp(ts, [100.0])
        stocks._session.get = mock.MagicMock(return_value=r)
        result = stocks._yahoo_historical("AAPL", "1D")  # 5m interval → intraday
        if result:
            self.assertIn("T", result[0]["date"])  # ISO datetime contains T


class TestYahooSummary(unittest.TestCase):
    """_yahoo_summary returns combined quoteSummary dict."""

    def test_returns_empty_when_no_crumb(self):
        with mock.patch.object(stocks, "_bootstrap_yahoo_session", return_value=None):
            result = stocks._yahoo_summary("AAPL")
        self.assertEqual(result, {})

    def test_returns_dict_with_crumb(self):
        r = mock.MagicMock()
        r.status_code = 200
        r.json.return_value = {"quoteSummary": {"result": [
            {"assetProfile": {"sector": "Technology", "industry": "Software"}}
        ]}}
        stocks._session.get = mock.MagicMock(return_value=r)
        with mock.patch.object(stocks, "_bootstrap_yahoo_session", return_value="crumb123"):
            result = stocks._yahoo_summary("AAPL")
        self.assertIsInstance(result, dict)


# ── Quote cache ───────────────────────────────────────────────────────────────

class TestQuoteCache(unittest.TestCase):
    def setUp(self):
        stocks._quote_cache.clear()

    def test_cache_hit_avoids_second_call(self):
        qp = _qp()
        stocks._quote_cache["AAPL"] = {"time": time.time(), "data": qp}
        with mock.patch.object(stocks, "_yahoo_quote") as mock_yq:
            result = stocks._build_quote_parts("AAPL")
        mock_yq.assert_not_called()
        self.assertIs(result, qp)

    def test_expired_cache_refetches(self):
        old_qp = _qp(100.0, 98.0)
        stocks._quote_cache["AAPL"] = {"time": time.time() - 100, "data": old_qp}
        new_meta = {"regularMarketPrice": 155.0, "chartPreviousClose": 150.0}
        with mock.patch.object(stocks, "_yahoo_quote", return_value=new_meta):
            result = stocks._build_quote_parts("AAPL")
        self.assertAlmostEqual(result.price, 155.0)

    def test_stale_cache_returned_on_error(self):
        stale = _qp(120.0, 118.0)
        stocks._quote_cache["AAPL"] = {"time": time.time() - 100, "data": stale}
        with mock.patch.object(stocks, "_yahoo_quote", side_effect=Exception("yf down")):
            result = stocks._build_quote_parts("AAPL")
        self.assertIs(result, stale)

    def test_no_cache_no_data_raises_503(self):
        stocks._quote_cache.clear()
        with mock.patch.object(stocks, "_yahoo_quote", side_effect=Exception("down")):
            with self.assertRaises(HTTPException) as ctx:
                stocks._build_quote_parts("FAKE")
        self.assertEqual(ctx.exception.status_code, 503)

    def test_zero_price_raises_and_falls_back_to_cache(self):
        stale = _qp(110.0, 108.0)
        stocks._quote_cache["AAPL"] = {"time": time.time() - 100, "data": stale}
        with mock.patch.object(stocks, "_yahoo_quote", return_value={"regularMarketPrice": 0.0}):
            result = stocks._build_quote_parts("AAPL")
        self.assertIs(result, stale)


# ── Build quote parts ─────────────────────────────────────────────────────────

class TestBuildQuoteParts(unittest.TestCase):
    def setUp(self): stocks._quote_cache.clear()

    def test_normal_path(self):
        meta = {"regularMarketPrice": 150.0, "chartPreviousClose": 148.0,
                "regularMarketDayOpen": 147.0, "regularMarketDayHigh": 152.0,
                "regularMarketDayLow": 146.0, "regularMarketVolume": 1_000_000}
        with mock.patch.object(stocks, "_yahoo_quote", return_value=meta):
            qp = stocks._build_quote_parts("AAPL")
        self.assertAlmostEqual(qp.price, 150.0)
        self.assertAlmostEqual(qp.prev_close, 148.0)

    def test_prev_close_defaults_to_price_when_zero(self):
        meta = {"regularMarketPrice": 150.0, "chartPreviousClose": 0.0}
        with mock.patch.object(stocks, "_yahoo_quote", return_value=meta):
            qp = stocks._build_quote_parts("AAPL")
        self.assertAlmostEqual(qp.prev_close, 150.0)  # prev defaults to price

    def test_stores_in_cache(self):
        stocks._quote_cache.clear()
        meta = {"regularMarketPrice": 150.0, "chartPreviousClose": 148.0}
        with mock.patch.object(stocks, "_yahoo_quote", return_value=meta):
            stocks._build_quote_parts("AAPL")
        self.assertIn("AAPL", stocks._quote_cache)


# ── Search endpoints ──────────────────────────────────────────────────────────

class TestSearchStocks(unittest.TestCase):
    def test_empty_raises_400(self):
        with self.assertRaises(HTTPException) as ctx: _run(stocks.search_stocks(""))
        self.assertEqual(ctx.exception.status_code, 400)

    def test_whitespace_raises_400(self):
        with self.assertRaises(HTTPException) as ctx: _run(stocks.search_stocks("   "))
        self.assertEqual(ctx.exception.status_code, 400)

    def test_valid_query(self):
        fs = mock.MagicMock()
        fs.quotes = [{"symbol": "AAPL", "shortname": "Apple", "quoteType": "EQUITY"}]
        with mock.patch.object(sys.modules["yfinance"], "Search", return_value=fs):
            result = _run(stocks.search_stocks("Apple"))
        self.assertEqual(result[0]["symbol"], "AAPL")

    def test_empty_symbol_skipped(self):
        fs = mock.MagicMock()
        fs.quotes = [{"symbol": "", "shortname": "Bad"}]
        with mock.patch.object(sys.modules["yfinance"], "Search", return_value=fs):
            result = _run(stocks.search_stocks("Bad"))
        self.assertEqual(result, [])

    def test_yf_exception_raises_500(self):
        with mock.patch.object(sys.modules["yfinance"], "Search", side_effect=RuntimeError("err")):
            with self.assertRaises(HTTPException) as ctx: _run(stocks.search_stocks("AAPL"))
        self.assertEqual(ctx.exception.status_code, 500)

    def test_no_search_attr_returns_empty(self):
        yf = sys.modules["yfinance"]
        orig = yf.Search; del yf.Search
        try:
            result = _run(stocks.search_stocks("AAPL"))
            self.assertEqual(result, [])
        finally:
            yf.Search = orig

    def test_result_fields(self):
        fs = mock.MagicMock()
        fs.quotes = [{"symbol": "MSFT", "shortname": "Microsoft",
                      "quoteType": "EQUITY", "region": "US", "currency": "USD"}]
        with mock.patch.object(sys.modules["yfinance"], "Search", return_value=fs):
            result = _run(stocks.search_stocks("Microsoft"))
        for f in ("symbol", "name", "type", "region", "currency"):
            self.assertIn(f, result[0])


class TestSearchDetailed(unittest.TestCase):
    def test_empty_raises_400(self):
        with self.assertRaises(HTTPException) as ctx: _run(stocks.search_stocks_detailed(""))
        self.assertEqual(ctx.exception.status_code, 400)

    def test_valid_returns_list(self):
        fs = mock.MagicMock()
        fs.quotes = [{"symbol": "AAPL", "quoteType": "EQUITY"}]
        t = mock.MagicMock(); t.ticker = "AAPL"
        t.get_info.return_value = {"shortName": "Apple"}
        with mock.patch.object(sys.modules["yfinance"], "Search", return_value=fs), \
             mock.patch.object(stocks, "_ticker", return_value=t), \
             mock.patch.object(stocks, "_get_info_best_effort", return_value={"shortName": "Apple"}), \
             mock.patch.object(stocks, "_build_quote_parts", return_value=_qp()):
            result = _run(stocks.search_stocks_detailed("Apple"))
        self.assertIsInstance(result, list)

    def test_non_equity_etf_skipped(self):
        fs = mock.MagicMock()
        fs.quotes = [{"symbol": "BTC-USD", "quoteType": "CRYPTOCURRENCY"}]
        with mock.patch.object(sys.modules["yfinance"], "Search", return_value=fs):
            result = _run(stocks.search_stocks_detailed("BTC"))
        self.assertEqual(result, [])


# ── Quote endpoint ────────────────────────────────────────────────────────────

class TestGetStockQuote(unittest.TestCase):
    def _p(self, price=155.0, prev=150.0, meta=None):
        return (mock.patch.object(stocks, "_build_quote_parts", return_value=_qp(price, prev)),
                mock.patch.object(stocks, "_yahoo_quote", return_value=meta or {"shortName": "ACME"}))

    def test_has_fields(self):
        p1, p2 = self._p()
        with p1, p2: result = _run(stocks.get_stock_quote("AAPL"))
        for f in ("symbol", "price", "change", "changePercent", "volume",
                  "open", "high", "low", "previousClose"):
            self.assertIn(f, result)

    def test_symbol_upper(self):
        p1, p2 = self._p()
        with p1, p2: result = _run(stocks.get_stock_quote("aapl"))
        self.assertEqual(result["symbol"], "AAPL")

    def test_change_correct(self):
        p1, p2 = self._p(160.0, 150.0)
        with p1, p2: result = _run(stocks.get_stock_quote("AAPL"))
        self.assertAlmostEqual(result["change"], 10.0)
        self.assertAlmostEqual(result["changePercent"], 10.0/150.0*100, places=4)

    def test_zero_prev_close(self):
        p1, p2 = self._p(100.0, 0.0)
        with p1, p2: result = _run(stocks.get_stock_quote("AAPL"))
        self.assertEqual(result["changePercent"], 0.0)

    def test_yahoo_quote_exception_handled(self):
        with mock.patch.object(stocks, "_build_quote_parts", return_value=_qp()), \
             mock.patch.object(stocks, "_yahoo_quote", side_effect=Exception("err")):
            result = _run(stocks.get_stock_quote("AAPL"))
        self.assertIn("price", result)


# ── Historical endpoint ───────────────────────────────────────────────────────

class TestGetHistorical(unittest.TestCase):
    def test_invalid_range_raises_400(self):
        with self.assertRaises(HTTPException) as ctx:
            _run(stocks.get_historical("AAPL", time_range="INVALID"))
        self.assertEqual(ctx.exception.status_code, 400)

    def test_valid_range_returns_list(self):
        bars = [{"date": "2024-01-01", "open": 100.0, "high": 102.0,
                 "low": 99.0, "close": 101.0, "volume": 1_000_000}]
        with mock.patch.object(stocks, "_yahoo_historical", return_value=bars):
            result = _run(stocks.get_historical("AAPL", time_range="1M"))
        self.assertEqual(result, bars)

    def test_empty_data_raises_503(self):
        with mock.patch.object(stocks, "_yahoo_historical", return_value=[]):
            with self.assertRaises(HTTPException) as ctx:
                _run(stocks.get_historical("FAKE", time_range="1M"))
        self.assertEqual(ctx.exception.status_code, 503)

    def test_api_exception_raises_503(self):
        with mock.patch.object(stocks, "_yahoo_historical", side_effect=Exception("down")):
            with self.assertRaises(HTTPException) as ctx:
                _run(stocks.get_historical("AAPL", time_range="1M"))
        self.assertEqual(ctx.exception.status_code, 503)

    def test_all_valid_ranges(self):
        bars = [{"date": "2024-01-01", "open": 100.0, "high": 102.0,
                 "low": 99.0, "close": 101.0, "volume": 1_000_000}]
        with mock.patch.object(stocks, "_yahoo_historical", return_value=bars):
            for r in ("1D", "1W", "1M", "3M", "1Y", "5Y"):
                result = _run(stocks.get_historical("AAPL", time_range=r))
                self.assertIsInstance(result, list)


# ── Indicators endpoint ───────────────────────────────────────────────────────

class TestGetIndicators(unittest.TestCase):
    def _bars(self, n=250):
        return [{"date": f"2024-01-{i+1:02d}", "open": 100.0+i*0.1,
                 "high": 102.0+i*0.1, "low": 99.0+i*0.1,
                 "close": 101.0+i*0.1, "volume": 1_000_000} for i in range(n)]

    def test_has_expected_keys(self):
        with mock.patch.object(stocks, "_yahoo_historical", return_value=self._bars()):
            result = _run(stocks.get_indicators("AAPL"))
        for k in ("symbol", "ma50", "ma200", "rsi", "macd"): self.assertIn(k, result)

    def test_symbol_upper(self):
        with mock.patch.object(stocks, "_yahoo_historical", return_value=self._bars()):
            result = _run(stocks.get_indicators("aapl"))
        self.assertEqual(result["symbol"], "AAPL")

    def test_empty_bars_raises_503(self):
        with mock.patch.object(stocks, "_yahoo_historical", return_value=[]):
            with self.assertRaises(HTTPException) as ctx:
                _run(stocks.get_indicators("FAKE"))
        self.assertEqual(ctx.exception.status_code, 503)

    def test_api_error_raises_503(self):
        with mock.patch.object(stocks, "_yahoo_historical", side_effect=Exception("down")):
            with self.assertRaises(HTTPException) as ctx:
                _run(stocks.get_indicators("AAPL"))
        self.assertEqual(ctx.exception.status_code, 503)

    def test_ma50_float(self):
        with mock.patch.object(stocks, "_yahoo_historical", return_value=self._bars()):
            result = _run(stocks.get_indicators("AAPL"))
        self.assertIsInstance(result["ma50"], float)

    def test_macd_dict(self):
        with mock.patch.object(stocks, "_yahoo_historical", return_value=self._bars()):
            result = _run(stocks.get_indicators("AAPL"))
        self.assertIsInstance(result["macd"], dict)


# ── Gainers / losers ──────────────────────────────────────────────────────────

class TestGainersLosers(unittest.TestCase):
    def test_gainers_positive(self):
        with mock.patch.object(stocks, "_build_quote_parts", return_value=_qp(110, 100)):
            result = _run(stocks.get_top_gainers())
        for item in result: self.assertGreater(item["changePercent"], 0)

    def test_losers_negative(self):
        with mock.patch.object(stocks, "_build_quote_parts", return_value=_qp(90, 100)):
            result = _run(stocks.get_top_losers())
        for item in result: self.assertLess(item["changePercent"], 0)

    def test_gainers_sorted_desc(self):
        prices = [120, 115, 110, 108, 105, 100, 100, 100, 100, 100]
        it = iter(prices)
        def side(sym): p = next(it); return _qp(p, 100)
        with mock.patch.object(stocks, "_build_quote_parts", side_effect=side):
            result = _run(stocks.get_top_gainers())
        pcts = [r["changePercent"] for r in result]
        self.assertEqual(pcts, sorted(pcts, reverse=True))

    def test_error_skipped(self):
        def side(sym):
            if sym == "NVDA": raise RuntimeError("err")
            return _qp(110, 100)
        with mock.patch.object(stocks, "_build_quote_parts", side_effect=side):
            result = _run(stocks.get_top_gainers())
        self.assertIsInstance(result, list)

    def test_max_5(self):
        with mock.patch.object(stocks, "_build_quote_parts", return_value=_qp(110, 100)):
            self.assertLessEqual(len(_run(stocks.get_top_gainers())), 5)
            self.assertLessEqual(len(_run(stocks.get_top_losers())), 5)


# ── get_all_stocks (paginated) ────────────────────────────────────────────────

class TestGetAllStocks(unittest.TestCase):
    def test_returns_paginated_structure(self):
        with mock.patch.object(stocks, "_build_quote_parts", return_value=_qp()):
            result = _run(stocks.get_all_stocks(page=1, limit=10))
        self.assertIn("data", result)
        self.assertIn("total", result)
        self.assertIn("page", result)
        self.assertIn("pages", result)

    def test_page_respects_limit(self):
        with mock.patch.object(stocks, "_build_quote_parts", return_value=_qp()):
            result = _run(stocks.get_all_stocks(page=1, limit=5))
        self.assertLessEqual(len(result["data"]), 5)

    def test_page_2_different_from_page_1(self):
        with mock.patch.object(stocks, "_build_quote_parts", return_value=_qp()):
            r1 = _run(stocks.get_all_stocks(page=1, limit=5))
            r2 = _run(stocks.get_all_stocks(page=2, limit=5))
        syms1 = {s["symbol"] for s in r1["data"]}
        syms2 = {s["symbol"] for s in r2["data"]}
        self.assertEqual(syms1 & syms2, set())  # no overlap

    def test_error_skipped(self):
        def side(sym):
            if sym == "AAPL": raise RuntimeError("fail")
            return _qp()
        with mock.patch.object(stocks, "_build_quote_parts", side_effect=side):
            result = _run(stocks.get_all_stocks(page=1, limit=10))
        self.assertIsInstance(result["data"], list)

    def test_total_reflects_all_symbols(self):
        with mock.patch.object(stocks, "_build_quote_parts", return_value=_qp()):
            result = _run(stocks.get_all_stocks(page=1, limit=10))
        self.assertGreater(result["total"], 10)


# ── Compare stocks ────────────────────────────────────────────────────────────

class TestCompareStocks(unittest.TestCase):
    def _p(self, price=150.0, prev=148.0):
        t = mock.MagicMock()
        t.history.return_value = _hist_df()
        return (mock.patch.object(stocks, "_build_quote_parts", return_value=_qp(price, prev)),
                mock.patch.object(stocks, "_ticker", return_value=t),
                mock.patch.object(stocks, "_get_info_best_effort",
                                  return_value={"shortName": "ACME"}))

    def test_empty_symbols_raises_400(self):
        with self.assertRaises(HTTPException) as ctx:
            _run(stocks.compare_stocks({"symbols": []}))
        self.assertEqual(ctx.exception.status_code, 400)

    def test_missing_key_raises_400(self):
        with self.assertRaises(HTTPException) as ctx: _run(stocks.compare_stocks({}))
        self.assertEqual(ctx.exception.status_code, 400)

    def test_non_list_raises_400(self):
        with self.assertRaises(HTTPException) as ctx:
            _run(stocks.compare_stocks({"symbols": "AAPL"}))
        self.assertEqual(ctx.exception.status_code, 400)

    def test_valid_returns_data(self):
        p1, p2, p3 = self._p()
        with p1, p2, p3:
            result = _run(stocks.compare_stocks({"symbols": ["AAPL", "MSFT"]}))
        self.assertIn("symbols", result); self.assertIn("data", result)

    def test_symbols_uppercased(self):
        p1, p2, p3 = self._p()
        with p1, p2, p3:
            result = _run(stocks.compare_stocks({"symbols": ["aapl"]}))
        self.assertIn("AAPL", result["data"])

    def test_entry_has_price_and_historical(self):
        p1, p2, p3 = self._p()
        with p1, p2, p3:
            result = _run(stocks.compare_stocks({"symbols": ["AAPL"]}))
        e = result["data"]["AAPL"]
        self.assertIn("price", e); self.assertIn("historical", e)


# ── Predict / news ────────────────────────────────────────────────────────────

class TestPredictAndNews(unittest.TestCase):
    def test_predict_stub(self):
        with mock.patch.object(stocks, "_build_quote_parts", return_value=_qp(200.0, 198.0)):
            result = _run(stocks.predict_future_price("AAPL", horizon_days=7))
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["model"], "stub_baseline")
        self.assertAlmostEqual(result["predictedPrice"], 200.0)

    def test_predict_symbol_upper(self):
        with mock.patch.object(stocks, "_build_quote_parts", return_value=_qp()):
            result = _run(stocks.predict_future_price("msft"))
        self.assertEqual(result["symbol"], "MSFT")

    def test_news_returns_list(self):
        t = mock.MagicMock(); t.news = []
        with mock.patch.object(stocks, "_ticker", return_value=t):
            result = _run(stocks.get_stock_news("AAPL"))
        self.assertIsInstance(result, list)

    def test_news_item_fields(self):
        t = mock.MagicMock()
        t.news = [{"uuid": "1", "title": "Big news", "publisher": "Reuters",
                   "link": "https://x.com", "providerPublishTime": 1_700_000_000}]
        with mock.patch.object(stocks, "_ticker", return_value=t):
            result = _run(stocks.get_stock_news("AAPL"))
        for f in ("id", "title", "source", "url", "publishedAt"):
            self.assertIn(f, result[0])

    def test_news_max_20(self):
        t = mock.MagicMock()
        t.news = [{"uuid": str(i), "title": f"N{i}", "publisher": "X",
                   "link": "http://x.com", "providerPublishTime": 1_700_000_000}
                  for i in range(30)]
        with mock.patch.object(stocks, "_ticker", return_value=t):
            result = _run(stocks.get_stock_news("AAPL"))
        self.assertLessEqual(len(result), 20)


if __name__ == "__main__":
    unittest.main(verbosity=2)
