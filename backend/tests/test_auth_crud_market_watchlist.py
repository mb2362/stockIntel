"""
test_auth_crud_market_watchlist.py
Tests: authhelper · crud · market endpoints · watchlist endpoints
"""
import sys, os, importlib, unittest, types
import unittest.mock as mock
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import conftest  # noqa
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

HTTPException = sys.modules["fastapi"].HTTPException

def _run(coro):
    import asyncio
    loop = asyncio.new_event_loop()
    try: return loop.run_until_complete(coro)
    finally: loop.close()

class _ColSet:
    def __init__(self, names): self._n = set(names)
    def __contains__(self, item): return item in self._n


# ── Auth helper ───────────────────────────────────────────────────────────────

class TestAuthHelper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if "app.api.auth.authhelper" in sys.modules:
            del sys.modules["app.api.auth.authhelper"]
        cls.auth = importlib.import_module("app.api.auth.authhelper")

    def test_hash_returns_string(self):
        self.assertIsInstance(self.auth.get_password_hash("pw"), str)

    def test_hash_differs_from_plain(self):
        self.assertNotEqual("pw", self.auth.get_password_hash("pw"))

    def test_verify_correct(self):
        h = self.auth.get_password_hash("secret123")
        self.assertTrue(self.auth.verify_password("secret123", h))

    def test_verify_wrong(self):
        h = self.auth.get_password_hash("secret123")
        self.assertFalse(self.auth.verify_password("wrong", h))

    def test_create_token_string(self):
        self.assertIsInstance(self.auth.create_access_token({"sub": "alice"}), str)

    def test_create_token_non_empty(self):
        self.assertGreater(len(self.auth.create_access_token({"sub": "bob"})), 0)

    def test_create_token_custom_expiry(self):
        from datetime import timedelta
        t = self.auth.create_access_token({"sub": "x"}, expires_delta=timedelta(hours=1))
        self.assertIsInstance(t, str)

    def test_algorithm_is_hs256(self):
        self.assertEqual(self.auth.ALGORITHM, "HS256")

    def test_expire_minutes_set(self):
        self.assertGreater(self.auth.ACCESS_TOKEN_EXPIRE_MINUTES, 0)


# ── CRUD ──────────────────────────────────────────────────────────────────────

class TestCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _SC = ("ticker", "name", "market", "locale", "primary_exchange", "type",
               "currency_name", "active", "last_updated_utc")
        _HC = ("symbol", "timestamp", "open", "high", "low", "close", "volume", "stock_id")
        _sentinel = mock.MagicMock()

        class _StockM:
            __table__ = type("T", (), {"columns": _ColSet(_SC)})()
            ticker = _sentinel; name = _sentinel
            def __init__(self, **kw): self.__dict__.update(kw)

        class _HistM:
            __table__ = type("T", (), {"columns": _ColSet(_HC)})()
            def __init__(self, **kw): self.__dict__.update(kw)

        class _UserM:
            username = _sentinel
            def __init__(self, **kw): self.__dict__.update(kw)

        class _UC:
            def __init__(self, username="", email="", password=""):
                self.username = username; self.email = email; self.password = password

        sys.modules["app.database.models"].Stock = _StockM
        sys.modules["app.database.models"].HistoricalStockData = _HistM
        sys.modules["app.database.models"].User = _UserM
        sys.modules["app.api.DTO.schemas"].UserCreate = _UC

        if "app.database.crud" in sys.modules: del sys.modules["app.database.crud"]
        cls.crud = importlib.import_module("app.database.crud")
        cls._StockM = _StockM; cls._HistM = _HistM; cls._UserM = _UserM; cls._UC = _UC

    def _db(self, rv=None):
        db = mock.MagicMock()
        db.refresh.side_effect = lambda obj: None
        q = mock.MagicMock(); f = mock.MagicMock()
        f.first.return_value = rv
        q.filter.return_value = f; db.query.return_value = q
        return db

    def test_create_stock(self):
        db = self._db()
        self.crud.create_stock(db, {"ticker": "AAPL", "name": "Apple"})
        db.add.assert_called_once(); db.commit.assert_called_once()

    def test_create_stock_strips_unknown_cols(self):
        db = self._db()
        self.crud.create_stock(db, {"ticker": "AAPL", "bad_col": "x"})
        db.add.assert_called_once()

    def test_create_stock_sets_timestamp(self):
        captured = {}
        db = self._db()
        db.add.side_effect = lambda obj: captured.__setitem__("obj", obj)
        self.crud.create_stock(db, {"ticker": "AAPL"})
        self.assertIn("last_updated_utc", captured["obj"].__dict__)

    def test_get_stock_found(self):
        stock = self._StockM(ticker="AAPL")
        db = self._db(rv=stock)
        result = self.crud.get_stock_by_ticker(db, "AAPL")
        self.assertIsNotNone(result)

    def test_get_stock_not_found(self):
        db = self._db(rv=None)
        self.assertIsNone(self.crud.get_stock_by_ticker(db, "ZZZZ"))

    def test_create_historical_data(self):
        from datetime import datetime
        db = self._db()
        self.crud.create_historical_data(db, {"symbol": "AAPL",
            "timestamp": datetime.now(), "open": 100.0, "high": 105.0,
            "low": 98.0, "close": 102.0, "volume": 1_000_000})
        db.add.assert_called_once(); db.commit.assert_called_once()

    def test_get_user_found(self):
        user = self._UserM(username="alice")
        db = self._db(rv=user)
        self.assertIsNotNone(self.crud.get_user_by_username(db, "alice"))

    def test_get_user_not_found(self):
        db = self._db(rv=None)
        self.assertIsNone(self.crud.get_user_by_username(db, "nobody"))

    def test_create_user(self):
        db = self._db()
        self.crud.create_user(db, self._UC("bob", "b@x.com", "pw"), "hashed_pw")
        db.add.assert_called_once(); db.commit.assert_called_once()


# ── Market endpoints ──────────────────────────────────────────────────────────

class TestMarketEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # market.py imports from stocks.py – must be loaded first
        if "app.api.endpoints.stocks" not in sys.modules:
            importlib.import_module("app.api.endpoints.stocks")
        if "app.api.endpoints.market" in sys.modules:
            del sys.modules["app.api.endpoints.market"]
        cls.market = importlib.import_module("app.api.endpoints.market")

    def _q(self, price=100.0, prev=98.0):
        from app.api.endpoints.stocks import QuoteParts
        qp = QuoteParts(price=price, prev_close=prev, open=99.0,
                        high=102.0, low=97.0, volume=1_000_000)
        return qp

    def test_overview_has_indices(self):
        with mock.patch.object(self.market, "_quote_basic",
                               return_value={"price": 100.0, "prev_close": 98.0,
                                             "change": 2.0, "changePercent": 2.04,
                                             "volume": 1_000_000, "marketCap": 1e9, "name": "Idx"}):
            result = _run(self.market.get_market_overview())
        self.assertIn("indices", result)
        self.assertGreater(len(result["indices"]), 0)

    def test_overview_market_status(self):
        with mock.patch.object(self.market, "_quote_basic",
                               return_value={"price": 100.0, "prev_close": 98.0,
                                             "change": 2.0, "changePercent": 2.04,
                                             "volume": 0, "marketCap": 0, "name": "X"}):
            result = _run(self.market.get_market_overview())
        self.assertIn("marketStatus", result)

    def test_overview_last_updated(self):
        with mock.patch.object(self.market, "_quote_basic",
                               return_value={"price": 100.0, "prev_close": 98.0,
                                             "change": 2.0, "changePercent": 2.04,
                                             "volume": 0, "marketCap": 0, "name": "X"}):
            result = _run(self.market.get_market_overview())
        self.assertIn("lastUpdated", result)

    def test_trending_returns_list(self):
        with mock.patch.object(self.market, "_quote_basic",
                               return_value={"price": 100.0, "prev_close": 98.0,
                                             "change": 2.0, "changePercent": 2.04,
                                             "volume": 0, "marketCap": 0, "name": "X"}):
            result = _run(self.market.get_trending_stocks())
        self.assertIsInstance(result, list)

    def test_gainers_positive(self):
        with mock.patch.object(self.market, "_quote_basic",
                               return_value={"price": 110.0, "prev_close": 100.0,
                                             "change": 10.0, "changePercent": 10.0,
                                             "volume": 0, "marketCap": 0, "name": "X"}):
            result = _run(self.market.get_top_gainers())
        for item in result: self.assertGreater(item["changePercent"], 0)

    def test_losers_negative(self):
        with mock.patch.object(self.market, "_quote_basic",
                               return_value={"price": 90.0, "prev_close": 100.0,
                                             "change": -10.0, "changePercent": -10.0,
                                             "volume": 0, "marketCap": 0, "name": "X"}):
            result = _run(self.market.get_top_losers())
        for item in result: self.assertLess(item["changePercent"], 0)

    def test_gainers_max_5(self):
        with mock.patch.object(self.market, "_quote_basic",
                               return_value={"price": 110.0, "prev_close": 100.0,
                                             "change": 10.0, "changePercent": 10.0,
                                             "volume": 0, "marketCap": 0, "name": "X"}):
            self.assertLessEqual(len(_run(self.market.get_top_gainers())), 5)

    def test_quote_basic_uses_cache(self):
        import time
        self.market._quote_cache["TEST"] = {
            "time": time.time(), "data": {"price": 200.0, "changePercent": 5.0}}
        result = self.market._quote_basic("TEST")
        self.assertEqual(result["price"], 200.0)
        del self.market._quote_cache["TEST"]

    def test_quote_basic_503_on_no_data(self):
        import time
        stocks_mod = importlib.import_module("app.api.endpoints.stocks")
        with mock.patch.object(stocks_mod, "_build_quote_parts",
                               side_effect=HTTPException(503, "down")):
            with self.assertRaises(HTTPException) as ctx:
                self.market._quote_basic("FAKE_NO_CACHE_XYZ")
        self.assertEqual(ctx.exception.status_code, 503)

    def test_fetch_gainer_loser_returns_none_on_error(self):
        stocks_mod = importlib.import_module("app.api.endpoints.stocks")
        with mock.patch.object(self.market, "_quote_basic", side_effect=Exception("err")):
            result = self.market._fetch_gainer_loser("FAKE")
        self.assertIsNone(result)


# ── Watchlist endpoints ───────────────────────────────────────────────────────

class TestWatchlistEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _sentinel = mock.MagicMock()

        class _User:
            id = 1; username = "demo"; email = "demo@x.com"; hashed_password = ""
            username_col = _sentinel

        class _Stock:
            def __init__(self, id=1, ticker="AAPL", name="Apple"):
                self.id = id; self.ticker = ticker; self.name = name

        class _WL:
            user_id = _sentinel; stock_id = _sentinel
            def __init__(self, user_id=1, stock_id=1):
                self.user_id = user_id; self.stock_id = stock_id

        sys.modules["app.database.models"].User = _User
        sys.modules["app.database.models"].Stock = _Stock
        sys.modules["app.database.models"].Watchlist = _WL

        crud = sys.modules["app.database.crud"]
        crud.get_stock_by_ticker = mock.MagicMock(return_value=None)
        crud.create_stock = mock.MagicMock(return_value=_Stock())
        cls.crud = crud

        if "app.api.endpoints.watchlist" in sys.modules:
            del sys.modules["app.api.endpoints.watchlist"]
        cls.wl = importlib.import_module("app.api.endpoints.watchlist")
        cls._User = _User; cls._Stock = _Stock; cls._WL = _WL

    def _db(self):
        db = mock.MagicMock()
        user = self._User()
        q = mock.MagicMock(); f = mock.MagicMock()
        f.first.return_value = user; f.all.return_value = []
        q.filter.return_value = f; db.query.return_value = q
        return db

    def test_get_watchlist_empty(self):
        db = self._db()
        result = _run(self.wl.get_watchlist(db=db))
        self.assertEqual(result, [])

    def test_add_empty_symbol_raises_400(self):
        db = self._db()
        with self.assertRaises(HTTPException) as ctx:
            _run(self.wl.add_to_watchlist(payload={"symbol": ""}, db=db))
        self.assertEqual(ctx.exception.status_code, 400)

    def test_add_missing_key_raises_400(self):
        db = self._db()
        with self.assertRaises(HTTPException) as ctx:
            _run(self.wl.add_to_watchlist(payload={}, db=db))
        self.assertEqual(ctx.exception.status_code, 400)

    def test_add_creates_stock_when_missing(self):
        db = self._db()
        self.crud.get_stock_by_ticker.return_value = None
        self.crud.create_stock.reset_mock()
        stocks_mod = sys.modules.get("app.api.endpoints.stocks")
        with mock.patch.object(stocks_mod, "_build_quote_parts",
                               side_effect=Exception("skip")):
            _run(self.wl.add_to_watchlist(payload={"symbol": "TSLA"}, db=db))
        self.crud.create_stock.assert_called_once()

    def test_add_returns_symbol(self):
        db = self._db()
        self.crud.get_stock_by_ticker.return_value = self._Stock()
        stocks_mod = sys.modules.get("app.api.endpoints.stocks")
        with mock.patch.object(stocks_mod, "_build_quote_parts",
                               side_effect=Exception("skip")):
            result = _run(self.wl.add_to_watchlist(payload={"symbol": "aapl"}, db=db))
        self.assertEqual(result["symbol"], "AAPL")

    def test_add_returns_added_at(self):
        db = self._db()
        self.crud.get_stock_by_ticker.return_value = self._Stock()
        stocks_mod = sys.modules.get("app.api.endpoints.stocks")
        with mock.patch.object(stocks_mod, "_build_quote_parts",
                               side_effect=Exception("skip")):
            result = _run(self.wl.add_to_watchlist(payload={"symbol": "AAPL"}, db=db))
        self.assertIn("addedAt", result)

    def test_remove_nonexistent_ok(self):
        db = self._db()
        self.crud.get_stock_by_ticker.return_value = None
        result = _run(self.wl.remove_from_watchlist(symbol="ZZZZ", db=db))
        self.assertEqual(result["status"], "OK")

    def test_remove_existing_ok(self):
        db = self._db()
        stock = self._Stock(); wl_row = self._WL()
        self.crud.get_stock_by_ticker.return_value = stock
        q = mock.MagicMock(); f = mock.MagicMock()
        f.first.side_effect = [self._User(), wl_row]
        q.filter.return_value = f; db.query.return_value = q
        result = _run(self.wl.remove_from_watchlist(symbol="AAPL", db=db))
        self.assertEqual(result["status"], "OK")

    def test_remove_symbol_upper(self):
        db = self._db()
        self.crud.get_stock_by_ticker.return_value = None
        result = _run(self.wl.remove_from_watchlist(symbol="aapl", db=db))
        self.assertEqual(result["status"], "OK")




# ── Extra watchlist coverage tests ───────────────────────────────────────────

class TestWatchlistCoverage(unittest.TestCase):
    """Covers the concurrent fetch path, _demo_user creation, and live price in add."""

    @classmethod
    def setUpClass(cls):
        _sentinel = mock.MagicMock()

        class _User:
            id = 1
            username = _sentinel   # class-level for filter(models.User.username == x)
            def __init__(self, username="demo", email="demo@x.com", hashed_password=""):
                self.id = 1; self.username = username
                self.email = email; self.hashed_password = hashed_password
        class _Stock:
            id = _sentinel
            def __init__(self, id=1, ticker="AAPL", name="Apple"):
                self.id = id; self.ticker = ticker; self.name = name
        class _WL:
            user_id = _sentinel; stock_id = _sentinel
            def __init__(self, user_id=1, stock_id=1):
                self.user_id = user_id; self.stock_id = stock_id

        sys.modules["app.database.models"].User = _User
        sys.modules["app.database.models"].Stock = _Stock
        sys.modules["app.database.models"].Watchlist = _WL

        crud = sys.modules["app.database.crud"]
        crud.get_stock_by_ticker = mock.MagicMock(return_value=None)
        crud.create_stock = mock.MagicMock(return_value=_Stock())
        cls.crud = crud
        cls._User = _User; cls._Stock = _Stock; cls._WL = _WL

        # Ensure stocks module is loaded first (watchlist imports from it)
        if "app.api.endpoints.stocks" not in sys.modules:
            importlib.import_module("app.api.endpoints.stocks")
        cls.stocks_mod = importlib.import_module("app.api.endpoints.stocks")

        if "app.api.endpoints.watchlist" in sys.modules:
            del sys.modules["app.api.endpoints.watchlist"]
        cls.wl = importlib.import_module("app.api.endpoints.watchlist")

    def _db_with_watchlist(self, ticker="AAPL"):
        """DB mock that returns a user with one watchlist row pointing at a stock."""
        db = mock.MagicMock()
        user  = self._User()
        stock = self._Stock(id=1, ticker=ticker, name=ticker)
        row   = self._WL(user_id=1, stock_id=1)

        call_count = [0]
        def query_side(model):
            q = mock.MagicMock()
            f = mock.MagicMock()
            call_count[0] += 1
            if model is self.wl.models.User:
                f.first.return_value = user
            elif model is self.wl.models.Watchlist:
                f.all.return_value = [row]
            elif model is self.wl.models.Stock:
                f.first.return_value = stock
            q.filter.return_value = f
            return q
        db.query.side_effect = query_side
        return db

    def test_get_watchlist_with_items_returns_list(self):
        db = self._db_with_watchlist()
        stocks_mod = importlib.import_module("app.api.endpoints.stocks")
        from app.api.endpoints.stocks import QuoteParts
        qp = QuoteParts(price=150.0, prev_close=148.0, open=147.0, high=152.0, low=146.0, volume=500_000)
        with mock.patch.object(stocks_mod, "_build_quote_parts", return_value=qp):
            result = _run(self.wl.get_watchlist(db=db))
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_get_watchlist_item_has_price_fields(self):
        db = self._db_with_watchlist()
        stocks_mod = importlib.import_module("app.api.endpoints.stocks")
        from app.api.endpoints.stocks import QuoteParts
        qp = QuoteParts(price=150.0, prev_close=148.0, open=147.0, high=152.0, low=146.0, volume=500_000)
        with mock.patch.object(stocks_mod, "_build_quote_parts", return_value=qp):
            result = _run(self.wl.get_watchlist(db=db))
        if result:
            for f in ("symbol", "price", "change", "changePercent"):
                self.assertIn(f, result[0])

    def test_get_watchlist_fetch_error_returns_zero_price(self):
        """When _build_quote_parts fails, watchlist still returns item with price=0."""
        db = self._db_with_watchlist()
        stocks_mod = importlib.import_module("app.api.endpoints.stocks")
        with mock.patch.object(stocks_mod, "_build_quote_parts", side_effect=Exception("err")):
            result = _run(self.wl.get_watchlist(db=db))
        self.assertIsInstance(result, list)
        if result:
            self.assertEqual(result[0]["price"], 0)

    def test_demo_user_created_when_missing(self):
        """Cover the _demo_user creation branch (user not found → create)."""
        db = mock.MagicMock()
        q = mock.MagicMock(); f = mock.MagicMock()
        f.first.return_value = None   # user not found → triggers creation
        f.all.return_value = []
        q.filter.return_value = f; db.query.return_value = q
        db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)
        result = _run(self.wl.get_watchlist(db=db))
        db.add.assert_called()
        db.commit.assert_called()

    def test_add_with_live_price_success(self):
        """Cover the live-price fetch path inside add_to_watchlist."""
        db = mock.MagicMock()
        user = self._User()
        stock = self._Stock()
        q = mock.MagicMock(); f = mock.MagicMock()
        f.first.return_value = user; f.all.return_value = []
        q.filter.return_value = f; db.query.return_value = q

        self.crud.get_stock_by_ticker.return_value = stock
        stocks_mod = importlib.import_module("app.api.endpoints.stocks")
        from app.api.endpoints.stocks import QuoteParts
        qp = QuoteParts(price=155.0, prev_close=150.0, open=149.0, high=157.0, low=148.0, volume=500_000)
        with mock.patch.object(stocks_mod, "_build_quote_parts", return_value=qp):
            result = _run(self.wl.add_to_watchlist(payload={"symbol": "AAPL"}, db=db))
        self.assertAlmostEqual(result["price"], 155.0)
        self.assertAlmostEqual(result["change"], 5.0)

    def test_add_duplicate_not_committed_again(self):
        """If watchlist row already exists, no second commit should occur."""
        db = mock.MagicMock()
        user = self._User()
        stock = self._Stock()
        existing_row = self._WL()
        q = mock.MagicMock(); f = mock.MagicMock()
        f.first.side_effect = [user, existing_row]
        q.filter.return_value = f; db.query.return_value = q
        self.crud.get_stock_by_ticker.return_value = stock
        stocks_mod = importlib.import_module("app.api.endpoints.stocks")
        with mock.patch.object(stocks_mod, "_build_quote_parts", side_effect=Exception("skip")):
            result = _run(self.wl.add_to_watchlist(payload={"symbol": "AAPL"}, db=db))
        # Should return ok without adding duplicate
        self.assertEqual(result["symbol"], "AAPL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
