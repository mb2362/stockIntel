"""
conftest.py  –  stub bootstrap for stockIntel backend tests
Registers all third-party stubs in sys.modules before any app code is loaded.
Idempotent: safe to import multiple times.
"""
import importlib, os, sys, types, unittest.mock as mock
from enum import Enum

if getattr(sys.modules.get(__name__), "_LOADED", False):
    pass
else:
    _BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if _BACKEND not in sys.path:
        sys.path.insert(0, _BACKEND)
    os.environ.setdefault("SECRET_KEY", "test-secret-key")

    def _stub(name, **attrs):
        m = sys.modules.get(name) or types.ModuleType(name)
        [setattr(m, k, v) for k, v in attrs.items()]
        sys.modules[name] = m; return m

    def _pkg(name, real_dir):
        m = sys.modules.get(name) or types.ModuleType(name)
        m.__path__ = [real_dir]; m.__package__ = name
        sys.modules[name] = m; return m

    def _app(*parts): return os.path.join(_BACKEND, "app", *parts)

    # ── pydantic + fastapi + starlette: use real packages ─────────────────────
    # These are all installed in requirements.txt; stubbing them causes import
    # conflicts because fastapi imports pydantic internals at load time.
    import pydantic as _pydantic
    import fastapi as _fastapi
    HTTPException = _fastapi.HTTPException
    # Keep a simple BaseModel stand-in for test helpers that use _BM directly
    class _BM(_pydantic.BaseModel):
        model_config = _pydantic.ConfigDict(arbitrary_types_allowed=True)

    # starlette is installed as a fastapi dependency – use the real package
    # Re-register fastapi submodule stubs that test files patch directly via sys.modules
    import fastapi.middleware.cors as _fmc
    sys.modules.setdefault("fastapi.middleware.cors", _fmc)

    # ── sqlalchemy ─────────────────────────────────────────────────────────────
    _N = lambda *a, **kw: None
    _stub("sqlalchemy", Column=_N, Integer=type("I", (), {}), String=type("S", (), {}),
          Float=type("F", (), {}), ForeignKey=_N, DateTime=type("D", (), {}),
          Boolean=type("B", (), {}), create_engine=mock.MagicMock())
    _stub("sqlalchemy.orm", relationship=_N, Session=mock.MagicMock,
          sessionmaker=mock.MagicMock(),
          declarative_base=lambda: type("Base", (), {"metadata": mock.MagicMock()}))
    _stub("sqlalchemy.exc"); _stub("sqlalchemy.pool")

    # ── passlib ────────────────────────────────────────────────────────────────
    class _CC:
        _PFX = "hashed_"
        def __init__(self, schemes=None, deprecated="auto"): pass
        def hash(self, pw): return f"{self._PFX}{pw}"
        def verify(self, plain, hashed): return hashed == f"{self._PFX}{plain}"
    _stub("passlib"); _stub("passlib.context", CryptContext=_CC)

    # ── PyJWT ──────────────────────────────────────────────────────────────────
    _FAKE_TOK = "mocked.jwt.token"
    class _JWTErr(Exception): pass
    _stub("jwt",
          encode=lambda payload, key, algorithm="HS256": _FAKE_TOK,
          decode=lambda tok, key, algorithms=None: (
              {"sub": "testuser"} if tok == _FAKE_TOK else (_ for _ in ()).throw(_JWTErr())),
          PyJWTError=_JWTErr)

    # ── dotenv ─────────────────────────────────────────────────────────────────
    _stub("dotenv", load_dotenv=lambda *a, **kw: None)

    # ── requests ───────────────────────────────────────────────────────────────
    class _Response:
        status_code = 200
        text = ""
        def raise_for_status(self): pass
        def json(self): return {}

    class _Session:
        headers = mock.MagicMock()
        def get(self, url, **kw): return _Response()
        def update(self, *a, **kw): pass

    _stub("requests", Session=_Session, Response=_Response)

    # ── yfinance ───────────────────────────────────────────────────────────────
    import pandas as pd

    def _hist(rows=5, name="Date"):
        prices = [148.0 + i for i in range(rows)]
        idx = pd.date_range("2024-01-01", periods=rows, freq="D", name=name)
        return pd.DataFrame({"Open": [p - 1 for p in prices], "High": [p + 2 for p in prices],
            "Low": [p - 2 for p in prices], "Close": prices, "Volume": [1_000_000] * rows}, index=idx)

    class _Ticker:
        def __init__(self, sym, session=None):
            self.ticker = sym; self.symbol = sym
            self.fast_info = {"last_price": 150.0, "previous_close": 148.0,
                              "last_volume": 1_000_000, "market_cap": 1e9}
            self.news = []
            self._info = {"shortName": f"{sym} Corp", "sector": "Technology",
                "marketCap": 1_000_000_000, "trailingPE": 25.0,
                "fiftyTwoWeekHigh": 200.0, "fiftyTwoWeekLow": 100.0}
        def get_info(self): return self._info
        def history(self, **kw): return _hist()

    class _Search:
        def __init__(self, q):
            self.quotes = [{"symbol": "AAPL", "shortname": "Apple Inc.",
                            "quoteType": "EQUITY", "region": "US", "currency": "USD"}]

    _stub("yfinance", Ticker=_Ticker, Search=_Search)

    # ── app package stubs (real dirs) ──────────────────────────────────────────
    _pkg("app",               _app())
    _pkg("app.api",           _app("api"))
    _pkg("app.api.auth",      _app("api", "auth"))
    _pkg("app.api.DTO",       _app("api", "DTO"))
    _pkg("app.api.endpoints", _app("api", "endpoints"))
    _pkg("app.api.security",  _app("api", "security"))
    _pkg("app.api.utils",     _app("api", "utils"))
    _pkg("app.database",      _app("database"))

    # ── db sub-module stubs ────────────────────────────────────────────────────
    class _ColSet:
        def __init__(self, names): self._n = set(names)
        def __contains__(self, item): return item in self._n

    _SC = ("ticker", "name", "market", "locale", "primary_exchange", "type",
           "currency_name", "active", "last_updated_utc", "cik", "composite_figi", "share_class_figi")
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
        __table__ = type("T", (), {"columns": _ColSet(("id", "username", "email", "hashed_password"))})()
        username = _sentinel
        def __init__(self, **kw): self.__dict__.update(kw)

    class _WLM:
        user_id = _sentinel; stock_id = _sentinel
        def __init__(self, **kw): self.__dict__.update(kw)

    _stub("app.database.database",
          Base=type("Base", (), {"metadata": mock.MagicMock()}),
          get_db=mock.MagicMock(), engine=mock.MagicMock())
    _stub("app.database.models", Stock=_StockM, HistoricalStockData=_HistM,
          User=_UserM, Watchlist=_WLM, Portfolio=_WLM, News=_WLM)
    _stub("app.database.crud")

    # ── DTO stubs: use real schemas (pydantic is real now) ────────────────────
    # Import the real DTO modules so response_model= annotations satisfy FastAPI
    import app.api.DTO.marketenums as _me_mod
    import app.api.DTO.schemas as _sc_mod
    sys.modules["app.api.DTO.marketenums"] = _me_mod
    sys.modules["app.api.DTO.schemas"] = _sc_mod

    _this = sys.modules[__name__]
    _this._LOADED = True
    _this.HTTPException = HTTPException
    _this._CryptContext = _CC
    _this._FAKE_TOK = _FAKE_TOK


# ---------------------------------------------------------------------------
# Restore real fastapi classes after any test that replaces them in sys.modules
# (TestMain.setUpClass replaces FastAPI/APIRouter and never restores them)
# ---------------------------------------------------------------------------
import fastapi as _real_fastapi
import fastapi.routing as _real_fastapi_routing

_REAL_FASTAPI_CLASS = _real_fastapi.FastAPI
_REAL_APIROUTER_CLASS = _real_fastapi.APIRouter
_REAL_ROUTING_APIROUTER = _real_fastapi_routing.APIRouter


def pytest_runtest_teardown(item, nextitem):
    """After every test, restore real FastAPI/APIRouter if a test replaced them."""
    import sys
    fa = sys.modules.get("fastapi")
    if fa and getattr(fa, "FastAPI", None) is not _REAL_FASTAPI_CLASS:
        fa.FastAPI = _REAL_FASTAPI_CLASS
        fa.APIRouter = _REAL_APIROUTER_CLASS
    fr = sys.modules.get("fastapi.routing")
    if fr and getattr(fr, "APIRouter", None) is not _REAL_ROUTING_APIROUTER:
        fr.APIRouter = _REAL_ROUTING_APIROUTER