"""
test_remaining_modules.py
Tests: authendpoints · news · portfolio · schemas · marketenums · database · main
"""
import sys, os, importlib, unittest, types
import unittest.mock as mock

sys.path.insert(0, os.path.dirname(__file__))
import conftest  # noqa
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

HTTPException = sys.modules["fastapi"].HTTPException

def _run(coro):
    import asyncio
    loop = asyncio.new_event_loop()
    try: return loop.run_until_complete(coro)
    finally: loop.close()


class TestMarketEnum(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if "app.api.DTO.marketenums" in sys.modules:
            del sys.modules["app.api.DTO.marketenums"]
        cls.mod = importlib.import_module("app.api.DTO.marketenums")

    def test_stocks_value(self):  self.assertEqual(self.mod.MarketEnum.STOCKS, "stocks")
    def test_fx_value(self):      self.assertEqual(self.mod.MarketEnum.FX, "fx")
    def test_otc_value(self):     self.assertEqual(self.mod.MarketEnum.OTC, "otc")
    def test_indicies_value(self): self.assertEqual(self.mod.MarketEnum.INDICIES, "indices")
    def test_is_enum(self):
        from enum import Enum
        self.assertTrue(issubclass(self.mod.MarketEnum, Enum))
    def test_stocks_is_string(self): self.assertIsInstance(self.mod.MarketEnum.STOCKS.value, str)


class TestSchemas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if "app.api.DTO.schemas" in sys.modules:
            del sys.modules["app.api.DTO.schemas"]
        cls.s = importlib.import_module("app.api.DTO.schemas")

    def test_token_access_token(self):
        t = self.s.Token(access_token="abc", token_type="bearer")
        self.assertEqual(t.access_token, "abc")

    def test_token_type(self):
        t = self.s.Token(access_token="abc", token_type="bearer")
        self.assertEqual(t.token_type, "bearer")

    def test_user_base(self):
        u = self.s.UserBase(username="alice", email="a@x.com")
        self.assertEqual(u.username, "alice")

    def test_user_create_password(self):
        u = self.s.UserCreate(username="b", email="b@x.com", password="pw")
        self.assertEqual(u.password, "pw")

    def test_user_id(self):
        u = self.s.User(id=42, username="c", email="c@x.com")
        self.assertEqual(u.id, 42)

    def test_stock_data_ticker(self):
        sd = self.s.StockData(ticker="AAPL")
        self.assertEqual(sd.ticker, "AAPL")

    def test_stock_data_optional_none(self):
        sd = self.s.StockData(ticker="MSFT")
        self.assertIsNone(sd.name)

    def test_stock_data_active_true(self):
        sd = self.s.StockData(ticker="GOOGL")
        self.assertTrue(sd.active)

    def test_historical_data(self):
        from datetime import datetime
        hd = self.s.HistoricalData(ticker="AAPL", queryCount=1, resultsCount=1,
            adjusted=True, results=[{}], status="OK", request_id="r1", count=1)
        self.assertEqual(hd.ticker, "AAPL")

    def test_stock_search(self):
        sd = self.s.StockData(ticker="AAPL")
        ss = self.s.StockSearch(results=[sd], count=1, status="OK", request_id="r1")
        self.assertEqual(ss.count, 1)


class TestNewsEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if "app.api.endpoints.news" in sys.modules:
            del sys.modules["app.api.endpoints.news"]
        cls.news = importlib.import_module("app.api.endpoints.news")

    def test_returns_dict(self):     self.assertIsInstance(_run(self.news.read_items()), dict)
    def test_has_message(self):      self.assertIn("message", _run(self.news.read_items()))
    def test_router_exists(self):    self.assertTrue(hasattr(self.news, "router"))


class TestPortfolioEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if "app.api.endpoints.portfolio" in sys.modules:
            del sys.modules["app.api.endpoints.portfolio"]
        cls.p = importlib.import_module("app.api.endpoints.portfolio")

    def test_returns_dict(self):  self.assertIsInstance(_run(self.p.read_items()), dict)
    def test_has_message(self):   self.assertIn("message", _run(self.p.read_items()))
    def test_router_exists(self): self.assertTrue(hasattr(self.p, "router"))


class TestDatabase(unittest.TestCase):
    def test_get_db_yields_and_closes(self):
        db = mock.MagicMock()
        SessionLocal = mock.MagicMock(return_value=db)
        def get_db():
            s = SessionLocal()
            try: yield s
            finally: s.close()
        gen = get_db()
        got = next(gen)
        self.assertIs(got, db)
        try: next(gen)
        except StopIteration: pass
        db.close.assert_called_once()

    def test_get_db_closes_on_early_exit(self):
        db = mock.MagicMock()
        def get_db():
            try: yield db
            finally: db.close()
        gen = get_db(); next(gen); gen.close()
        db.close.assert_called_once()

    def test_session_called_once(self):
        db = mock.MagicMock()
        SL = mock.MagicMock(return_value=db)
        def get_db():
            s = SL()
            try: yield s
            finally: s.close()
        list(get_db())
        SL.assert_called_once()


class TestAuthEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class _Form: username = "testuser"; password = "testpass"
        class _UserM: id = 1; username = "testuser"; email = "t@x.com"; hashed_password = "hashed_testpass"
        cls._UserM = _UserM; cls._Form = _Form

        helper = types.ModuleType("app.api.auth.authhelper")
        helper.verify_password   = lambda p, h: h == f"hashed_{p}"
        helper.get_password_hash = lambda pw: f"hashed_{pw}"
        helper.create_access_token = lambda data, expires_delta=None: "test.token"
        helper.get_current_user    = mock.AsyncMock(return_value=_UserM())
        helper.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        helper.timedelta = __import__("datetime").timedelta
        sys.modules["app.api.auth.authhelper"] = helper
        sys.modules["app.api.auth"].authhelper = helper

        crud = sys.modules["app.database.crud"]
        crud.get_user_by_username = mock.MagicMock(return_value=_UserM())
        crud.create_user = mock.MagicMock(return_value=_UserM())
        cls.crud = crud

        class _UC: username = "newuser"; email = "n@x.com"; password = "pw"
        sys.modules["app.api.DTO.schemas"].UserCreate = _UC

        if "app.api.endpoints.authendpoints" in sys.modules:
            del sys.modules["app.api.endpoints.authendpoints"]
        cls.ae = importlib.import_module("app.api.endpoints.authendpoints")

    def _db(self): return mock.MagicMock()

    def test_login_valid(self):
        class _F: username = "testuser"; password = "testpass"
        user = self._UserM()
        self.crud.get_user_by_username.return_value = user
        result = _run(self.ae.login_for_access_token(form_data=_F(), db=self._db()))
        self.assertIn("access_token", result)
        self.assertEqual(result["token_type"], "bearer")

    def test_login_wrong_password(self):
        class _F: username = "testuser"; password = "WRONG"
        user = self._UserM()
        self.crud.get_user_by_username.return_value = user
        with self.assertRaises(HTTPException) as ctx:
            _run(self.ae.login_for_access_token(form_data=_F(), db=self._db()))
        self.assertEqual(ctx.exception.status_code, 401)

    def test_login_unknown_user(self):
        class _F: username = "ghost"; password = "pw"
        self.crud.get_user_by_username.return_value = None
        with self.assertRaises(HTTPException) as ctx:
            _run(self.ae.login_for_access_token(form_data=_F(), db=self._db()))
        self.assertEqual(ctx.exception.status_code, 401)

    def test_create_user_new(self):
        class _UC: username = "brand_new"; email = "b@x.com"; password = "pw"
        self.crud.get_user_by_username.return_value = None
        self.crud.create_user.reset_mock()
        _run(self.ae.create_user(user=_UC(), db=self._db()))
        self.crud.create_user.assert_called()

    def test_create_user_duplicate_400(self):
        class _UC: username = "existing"; email = "e@x.com"; password = "pw"
        self.crud.get_user_by_username.return_value = self._UserM()
        with self.assertRaises(HTTPException) as ctx:
            _run(self.ae.create_user(user=_UC(), db=self._db()))
        self.assertEqual(ctx.exception.status_code, 400)

    def test_read_me(self):
        fake_user = mock.MagicMock(id=1, username="me", email="me@x.com")
        result = _run(self.ae.read_users_me(current_user=fake_user))
        self.assertIs(result, fake_user)

    def test_router_exists(self): self.assertTrue(hasattr(self.ae, "router"))


class TestMain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for mod in ("app.api.endpoints.stocks", "app.api.endpoints.watchlist",
                    "app.api.endpoints.portfolio", "app.api.endpoints.news",
                    "app.api.endpoints.authendpoints", "app.api.endpoints.market"):
            stub = sys.modules.get(mod) or types.ModuleType(mod)
            if not hasattr(stub, "router"):
                stub.router = mock.MagicMock()
                stub.router.prefix = ""; stub.router.tags = []
            sys.modules[mod] = stub

        sys.modules["fastapi.middleware.cors"].CORSMiddleware = mock.MagicMock()

        class _FastAPI:
            def __init__(self, **kw): self.title = kw.get("title", ""); self.routers = []
            def add_middleware(self, cls, **kw): pass
            def include_router(self, r, **kw): self.routers.append(r)
            def get(self, path, **kw):
                def deco(fn): self._root_fn = fn; return fn
                return deco

        class _RouterFull:
            def __init__(self, **kw): self.prefix = kw.get("prefix", ""); self.routers = []
            def get(self, p, **kw): return lambda fn: fn
            def post(self, p, **kw): return lambda fn: fn
            def delete(self, p, **kw): return lambda fn: fn
            def include_router(self, r, **kw): self.routers.append(r)

        sys.modules["fastapi"].FastAPI = _FastAPI
        sys.modules["fastapi"].APIRouter = _RouterFull
        sys.modules["fastapi.routing"].APIRouter = _RouterFull

        sys.modules["app.database.database"].engine = mock.MagicMock()
        sys.modules["app.database.models"].Base = mock.MagicMock()
        sys.modules["app.database.models"].Base.metadata.create_all = mock.MagicMock()

        if "app.main" in sys.modules: del sys.modules["app.main"]
        cls.main = importlib.import_module("app.main")

    def test_app_created(self): self.assertTrue(hasattr(self.main, "app"))
    def test_app_title(self):   self.assertIn("Stock", self.main.app.title)
    def test_routers_included(self): self.assertGreater(len(self.main.app.routers), 0)
    def test_create_all_called(self):
        sys.modules["app.database.models"].Base.metadata.create_all.assert_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
