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

    # ── pydantic ───────────────────────────────────────────────────────────────
    class _BM:
        model_config = {}
        def __init__(self, **d): self.__dict__.update(d)
    _stub("pydantic", BaseModel=_BM, ConfigDict=dict); _stub("pydantic.v1")

    # ── fastapi ────────────────────────────────────────────────────────────────
    class HTTPException(Exception):
        def __init__(self, status_code=500, detail="", **kw):
            self.status_code = status_code; self.detail = detail; super().__init__(detail)

    class _Router:
        def __init__(self, **kw): self.prefix = kw.get("prefix", "")
        def get(self, p, **kw): return lambda fn: fn
        def post(self, p, **kw): return lambda fn: fn
        def delete(self, p, **kw): return lambda fn: fn
        def include_router(self, r, **kw): pass

    _stub("fastapi", APIRouter=_Router, HTTPException=HTTPException,
        Depends=lambda d=None: None, Body=lambda *a, **kw: None,
        Query=lambda default=None, **kw: default)
    _stub("fastapi.params", Depends=lambda d=None: None)
    _stub("fastapi.security", OAuth2PasswordBearer=lambda *a, **kw: None,
          OAuth2PasswordRequestForm=type('OAuth2PasswordRequestForm', (), {}))
    _stub("fastapi.responses"); _stub("fastapi.middleware"); _stub("fastapi.middleware.cors",
          CORSMiddleware=mock.MagicMock())
    _stub("fastapi.routing", APIRouter=_Router)

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

    # ── DTO stubs ──────────────────────────────────────────────────────────────
    class _UC2:
        def __init__(self, username="", email="", password=""):
            self.username = username; self.email = email; self.password = password

    class _ME(str, Enum): STOCKS = "stocks"; FX = "fx"; OTC = "otc"; INDICIES = "indices"

    _stub("app.api.DTO.schemas", UserCreate=_UC2, StockData=_BM, Token=_BM, UserBase=_BM, User=_BM)
    _stub("app.api.DTO.marketenums", MarketEnum=_ME)

    _this = sys.modules[__name__]
    _this._LOADED = True
    _this.HTTPException = HTTPException
    _this._CryptContext = _CC
    _this._FAKE_TOK = _FAKE_TOK
