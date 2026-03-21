# Running the Test Suite

## Quick Start

```bash
# 1. Go into the backend directory (REQUIRED)
cd stockIntel-main/backend

# 2. Install test dependencies
pip install pytest pytest-cov pytest-asyncio httpx

# 3. Run all tests
pytest

# OR explicitly:
pytest tests/
```

## ⚠️ Common Mistake

The error `file or directory not found: tests/` means you are running pytest
from the **wrong directory**. You must be inside `backend/` when running pytest.

```bash
# ❌ Wrong – run from project root
cd stockIntel-main
pytest tests/                    # ERROR: file or directory not found: tests/

# ✅ Correct – run from backend/
cd stockIntel-main/backend
pytest                           # uses pytest.ini → finds tests/ automatically
pytest tests/                    # also works
pytest tests/test_utils.py       # run a single file
```

If you must run from outside `backend/`, pass the full path:
```bash
# From stockIntel-main/:
pytest backend/tests/

# From repo root:
pytest stockIntel-main/backend/tests/
```

## Run with Coverage

```bash
cd stockIntel-main/backend
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=70
```

Expected output:
```
---------- coverage: ... ----------
app/api/endpoints/stocks.py       74%
app/api/endpoints/watchlist.py    86%
...
TOTAL                             71%
188 passed in X.XXs
```

## Install All Dependencies (App + Tests)

```bash
cd stockIntel-main/backend
pip install -r requirements.txt
pip install -r requirements-test.txt
```

## Test Structure

```
tests/
├── conftest.py                        # Stubs for fastapi, sqlalchemy, yfinance, etc.
├── test_utils.py                      # _safe_float, _safe_int, RSI, MACD helpers
├── test_stocks_logic.py               # Yahoo API helpers, cache, all stock endpoints
├── test_auth_crud_market_watchlist.py # Auth, CRUD, market, watchlist endpoints
└── test_remaining_modules.py          # auth endpoints, schemas, enums, main, database
```

## No Database or Network Required

All tests run completely offline — every external dependency (yfinance, FastAPI,
SQLAlchemy, requests, passlib, PyJWT) is replaced by a lightweight in-memory stub
registered in `tests/conftest.py`. No `.env` file, database, or internet connection
is needed to run the tests.
