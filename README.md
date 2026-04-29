# StockIntel – Full-Stack Stock Market Intelligence Platform

> A production-grade stock market application featuring real-time data, LSTM-powered price predictions, watchlist management, and a React/TypeScript frontend — all containerised with Docker Compose.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start (Docker — Recommended)](#quick-start-docker--recommended)
- [Local Development Setup](#local-development-setup)
  - [Backend](#backend)
  - [Frontend](#frontend)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
  - [Stocks](#stocks)
  - [Market](#market)
  - [Watchlist](#watchlist)
  - [News](#news)
  - [ML Predictions](#ml-predictions)
- [Database Schema](#database-schema)
- [Machine Learning — Dual LSTM Model](#machine-learning--dual-lstm-model)
- [Caching Layer](#caching-layer)
- [Security](#security)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Supported Tickers (ML Predictions)](#supported-tickers-ml-predictions)
- [Contributing](#contributing)

---

## Overview

StockIntel is a full-stack stock market intelligence platform that provides:

- **Real-time market data** sourced from Yahoo Finance (no paid API key required)
- **AI-powered next-day price predictions** using a per-ticker Dual LSTM model (PyTorch)
- **BUY / SELL signals** with confidence scores
- **Technical indicators** — RSI, MACD, MA50, MA200
- **Personal watchlists** to track stocks with live prices
- **Stock news**, **gainers/losers**, and **market overview**

The backend is a FastAPI REST API with PostgreSQL persistence and optional Redis caching. The frontend is a React 19 + TypeScript SPA styled with Tailwind CSS.

---

## Architecture

- The **frontend** talks to the API at `http://localhost:8001/api/v1`
- The **API** connects to PostgreSQL for persistence and to Yahoo Finance for live data
- The **ML layer** loads pre-trained per-ticker LSTM models from `./models/<TICKER>/`
- **Redis** is optional — the API falls back to an in-memory TTL store automatically

---

## Features

| Category | Feature |
|---|---|
| **Stock Data** | Real-time quotes, OHLCV history, company info |
| **Technical Analysis** | RSI, MACD, 50-day MA, 200-day MA |
| **AI Predictions** | Next-day closing price & BUY/SELL signal (50 tickers) |
| **Market Overview** | Global indices, trending stocks, top gainers/losers |
| **Search** | Ticker/name search with `yfinance.Search` |
| **Comparison** | Side-by-side multi-symbol comparison |
| **Pagination** | Browsable stock list (100+ symbols) |
| **Watchlist** | Add, view, and remove tracked stocks with live prices |
| **News** | Fetch relevant news articles per stock |
| **Caching** | Redis-backed (in-memory fallback) with per-resource TTLs |
| **Rate Limiting** | 60 requests/minute per IP (sliding window) |
| **Security Headers** | HSTS, X-Frame-Options, CSP, X-Content-Type-Options |

---

## Technology Stack

### Backend

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | FastAPI 0.136 + Uvicorn |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Market Data | yfinance + Yahoo Finance v8/v10 direct API |
| Data Processing | pandas 2.2, numpy 2.4 |
| Machine Learning | PyTorch 2.11, scikit-learn 1.8 |
| Caching | Redis 7.4 (with in-memory fallback) |
| Containerisation | Docker + Docker Compose |
| Testing | pytest 9.0, pytest-cov 7.1 |

### Frontend

| Component | Technology |
|---|---|
| Language | TypeScript 5.9 |
| Framework | React 19 + React DOM |
| Build Tool | Vite 6.4 |
| Routing | React Router DOM 6.22 |
| Styling | Tailwind CSS 3.4 |
| Charts | Recharts 2.12 |
| HTTP Client | Axios 1.6 |
| Animations | Framer Motion 12 |
| Icons | Lucide React |
| Testing | Vitest 4, Testing Library |

---

## Project Structure

```
stockIntel-main/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── docs/          # Custom OpenAPI config
│   │   │   ├── endpoints/     # Route handlers
│   │   │   │   ├── market.py
│   │   │   │   ├── news.py
│   │   │   │   ├── predict.py
│   │   │   │   ├── stocks.py
│   │   │   │   └── watchlist.py
│   │   │   ├── security/
│   │   │   │   └── middleware.py  # Rate limiter + security headers
│   │   │   └── utils/
│   │   │       └── data_cleaner.py
│   │   ├── database/
│   │   │   ├── crud.py
│   │   │   ├── database.py
│   │   │   └── models.py      # SQLAlchemy ORM models
│   │   ├── ml/
│   │   │   └── predictor.py   # Dual LSTM inference engine
│   │   ├── ml_assets/         # Default model (NVDA)
│   │   │   ├── dual_lstm_model.pth
│   │   │   ├── scaler_features.pkl
│   │   │   └── scaler_price.pkl
│   │   ├── cache.py           # Redis + in-memory caching layer
│   │   └── main.py            # FastAPI app factory
│   ├── docker/
│   │   ├── Dockerfile
│   │   ├── Dockerfile.test
│   │   └── .env.docker
│   ├── tests/                 # 188 pytest tests
│   ├── requirements.txt
│   └── requirements-test.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   │   └── Landing.tsx
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── models/                    # Pre-trained per-ticker models
│   ├── AAPL/
│   │   ├── dual_lstm_model.pth
│   │   ├── scaler_features.pkl
│   │   └── scaler_price.pkl
│   └── <TICKER>/              # 50 tickers total
├── .github/
│   └── workflows/
│       └── ci-cd.yml          # GitHub Actions CI/CD
├── docker-compose.yml
├── LSTM_signal_v3_pytorch_dynamic_FINAL.ipynb
└── README.md
```

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (recommended) **or**
- Python 3.11+ and Node.js 18+ (for local dev)
- PostgreSQL (if running locally without Docker)
- No paid API keys required — all market data comes from Yahoo Finance

---

## Quick Start (Docker — Recommended)

This single command builds and starts the **API**, **frontend**, and **PostgreSQL** database together:

```bash
git clone <repository_url>
cd stockIntel-main
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend (React) | http://localhost:5173 |
| Backend API | http://localhost:8001 |
| Swagger / OpenAPI | http://localhost:8001/docs |
| ReDoc | http://localhost:8001/redoc |
| PostgreSQL | localhost:5432 |

To stop all services:

```bash
docker compose down
```

To also remove the persistent database volume:

```bash
docker compose down -v
```

---

## Local Development Setup

### Backend

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd stockIntel-main
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate        # macOS/Linux
   venv\Scripts\activate           # Windows
   ```

3. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Create environment file** — `backend/.env`:
   ```env
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/stockmarket
   SECRET_KEY=your-super-secret-key-change-me
   REDIS_URL=redis://localhost:6379/0   # optional — falls back to in-memory
   MODELS_DIR=../models                 # path to the per-ticker model directory
   ```

5. **Run the API:**
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```
   
   The API will be available at `http://localhost:8001` with interactive docs at `/docs`.

### Frontend

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure the API URL** — create `frontend/.env.local`:
   ```env
   VITE_API_BASE_URL=http://localhost:8001/api/v1
   VITE_USE_MOCK_API=false
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   
   The frontend will be available at `http://localhost:5173`.

---

## Environment Variables

### Backend (`backend/.env` or `backend/docker/.env.docker`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string |
| `SECRET_KEY` | ✅ | — | JWT signing secret (use a long random string) |
| `REDIS_URL` | ❌ | `redis://localhost:6379/0` | Redis connection URL; falls back to in-memory if unavailable |
| `MODELS_DIR` | ❌ | `app/ml_assets` | Path to directory containing per-ticker model folders |
| `CACHE_TTL_QUOTE` | ❌ | `15` | Quote cache TTL in seconds |
| `CACHE_TTL_HISTORICAL` | ❌ | `300` | OHLCV bar cache TTL in seconds |
| `CACHE_TTL_INFO` | ❌ | `3600` | Company info cache TTL in seconds |
| `CACHE_TTL_OVERVIEW` | ❌ | `60` | Market overview cache TTL in seconds |
| `CACHE_TTL_NEWS` | ❌ | `600` | News cache TTL in seconds |
| `CACHE_TTL_PREDICT` | ❌ | `300` | ML prediction cache TTL in seconds |

### Frontend

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Base URL of the FastAPI backend (e.g. `http://localhost:8001/api/v1`) |
| `VITE_USE_MOCK_API` | Set to `"true"` to use mock data instead of the real API |

---

## API Reference

All endpoints are prefixed with `/api/v1`. For interactive documentation, visit `/docs` (Swagger UI) or `/redoc`.

### Stocks

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/stocks` | Paginated list of stocks (`?page=1&size=20`) |
| `GET` | `/stocks/search?q=AAPL` | Search by symbol or name |
| `GET` | `/stocks/gainers` | Top daily gainers |
| `GET` | `/stocks/losers` | Top daily losers |
| `GET` | `/stocks/{symbol}/quote` | Live quote (price, change, volume) |
| `GET` | `/stocks/{symbol}/info` | Full company details |
| `GET` | `/stocks/{symbol}/historical?range=1M` | OHLCV history |
| `GET` | `/stocks/{symbol}/indicators` | RSI, MACD, MA50, MA200 |
| `GET` | `/stocks/{symbol}/news` | Stock-specific news articles |
| `POST` | `/stocks/compare` | Side-by-side comparison of multiple symbols |

**Historical range options:** `1D`, `5D`, `1M`, `3M`, `6M`, `1Y`, `2Y`, `5Y`

**Compare request body:**
```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL"]
}
```

---

### Market

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/market/overview` | Major global indices (S&P 500, NASDAQ, Dow, etc.) |
| `GET` | `/market/trending` | Currently trending stocks |
| `GET` | `/market/gainers` | Market-wide top gainers |
| `GET` | `/market/losers` | Market-wide top losers |

---

### Watchlist

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/watchlist` | Get user's watchlist with live prices |
| `POST` | `/watchlist` | Add a stock to watchlist |
| `DELETE` | `/watchlist/{symbol}` | Remove a stock from watchlist |

**Add to watchlist body:**
```json
{
  "symbol": "NVDA"
}
```

---

### News

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/news/{symbol}` | Latest news articles for a ticker |

---

### ML Predictions

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/predict/{symbol}` | LSTM next-day prediction for a supported ticker |

**Example response:**
```json
{
  "symbol": "AAPL",
  "signal": "BUY",
  "confidence": 0.82,
  "current_price": 213.45,
  "predicted_price": 218.90,
  "model": "dual_lstm_v3"
}
```

Returns `400` if the ticker is not in the [supported list](#supported-tickers-ml-predictions).

---

## Database Schema

### `stocks`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `ticker` | String | Unique, indexed |
| `name` | String | Company name |
| `market` | String | e.g. `stocks`, `crypto` |
| `primary_exchange` | String | e.g. `XNAS` |
| `type` | String | e.g. `CS` (common stock) |
| `currency_name` | String | e.g. `usd` |
| `active` | Boolean | Whether the stock is active |

### `historical_stock_data`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `symbol` | String | Ticker symbol |
| `timestamp` | DateTime | Bar timestamp |
| `open`, `high`, `low`, `close` | Float | OHLC prices |
| `volume` | Integer | Trade volume |
| `stock_id` | FK → `stocks.id` | |

### `watchlists`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `user_id` | FK → `users.id` | |
| `stock_id` | FK → `stocks.id` | |

### `news`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `stock_id` | FK → `stocks.id` | |
| `title` | String | Article headline |
| `url` | String | Link to article |
| `published_at` | DateTime | Publication timestamp |

---

## Machine Learning — Dual LSTM Model

StockIntel uses a **Dual LSTM architecture** trained separately for each supported ticker. Models are stored under `models/<TICKER>/` and loaded at runtime.

### Model Files per Ticker

| File | Description |
|---|---|
| `dual_lstm_model.pth` | PyTorch model weights |
| `scaler_features.pkl` | `sklearn` scaler for input features |
| `scaler_price.pkl` | `sklearn` scaler for price output |

### Input Features

The model uses a multi-feature time-series window including:
- OHLCV price data
- Technical indicators (RSI, MACD, moving averages)
- Volume-derived features

### Output

- **`predicted_price`** — Predicted next-day closing price
- **`signal`** — `BUY` or `SELL` based on predicted vs current price
- **`confidence`** — Model confidence score (0.0 – 1.0)

### Training Notebook

The full training pipeline (data preparation, architecture, training loop, evaluation) is documented in:

```
LSTM_signal_v3_pytorch_dynamic_FINAL.ipynb
```

Also included for reference:
- `LogisticRegression` — baseline logistic regression model
- `Random forest` — baseline random forest model

---

## Caching Layer

The API uses a tiered caching strategy to reduce load on Yahoo Finance and improve response times.

| Resource | TTL | Variable |
|---|---|---|
| Live quote | 15 seconds | `CACHE_TTL_QUOTE` |
| OHLCV history | 5 minutes | `CACHE_TTL_HISTORICAL` |
| Company info | 1 hour | `CACHE_TTL_INFO` |
| Market overview | 60 seconds | `CACHE_TTL_OVERVIEW` |
| News articles | 10 minutes | `CACHE_TTL_NEWS` |
| ML predictions | 5 minutes | `CACHE_TTL_PREDICT` |

**Redis** is used when available. If Redis is not reachable at startup, the API automatically falls back to a thread-safe **in-memory TTL store** with zero configuration required.

---

## Security

### Middleware Stack

The following middleware is applied to every request (outermost first):

1. **CORS** — Allows `localhost:5173` and `localhost:3001` (frontend dev servers)
2. **Rate Limiter** — Sliding-window, 60 requests/minute per IP; exempt paths: `/`, `/docs`, `/redoc`
3. **Security Headers** — Adds to every response:
   - `Strict-Transport-Security`
   - `X-Frame-Options: DENY`
   - `X-Content-Type-Options: nosniff`
   - `Content-Security-Policy`

---

## Testing

The backend has a comprehensive test suite using `pytest`.

### Run Tests Locally

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-test.txt
pytest
```

### Run Tests with Coverage Report

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Run Tests via Docker (fully isolated)

```bash
docker compose run --rm test
```

### Test Configuration

Tests run **fully offline** — no database or internet connection required. The test environment uses:
- `DATABASE_URL=sqlite:///:memory:` (in-memory SQLite)
- `SECRET_KEY=test-secret-key-for-ci`
- Mocked external HTTP calls to Yahoo Finance

| Metric | Value |
|---|---|
| Total tests | 188 |
| Coverage target | ≥ 80% |
| Test runner | pytest 9.0 |

For full details on the test suite, Docker-based testing, and troubleshooting, see [`backend/README-TESTS.md`](backend/README-TESTS.md).

---

## CI/CD Pipeline

GitHub Actions runs automatically on every push and pull request to `main` and all `feature/*` branches.

### Jobs

```
push / PR to main
       │
       ├─── test-backend  (pytest, coverage ≥ 80%)
       │         └── uploads coverage.xml artifact
       │
       ├─── build-frontend  (npm install + npm run build)
       │
       └─── ci-passed  (gate — requires both above to succeed)
```

### Backend Job

- Sets up Python 3.11 with pip caching
- Installs `requirements.txt` + `requirements-test.txt`
- Runs `pytest` with `--cov-fail-under=80` — **build fails if coverage drops below 80%**
- Uploads `coverage.xml` as a build artifact

### Frontend Job

- Sets up Node 18 with npm caching
- Runs `npm install --legacy-peer-deps`
- Runs `npm run build` (TypeScript compile + Vite production bundle)

See [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) for the full pipeline definition.

---

## Supported Tickers (ML Predictions)

The `/predict/{symbol}` endpoint supports the following 50 ticker symbols:

| Tech / AI | Finance | Healthcare | Consumer | EV / Other |
|---|---|---|---|---|
| AAPL | GS | LLY | COST | RIVN |
| AMZN | JPM | JNJ | WMT | NIO |
| AMD | MS | PFE | TGT | LCID |
| ADBE | BAC | UNH | HD | COIN |
| ARM | V | | LOW | SOFI |
| AVGO | MA | | DIS | PYPL |
| AXON | BRK-B | | | XYZ |
| CRM | | | | |
| GOOGL / GOOG | | | | |
| INTC | | | | |
| META | | | | |
| MSFT | | | | |
| MU | | | | |
| NFLX | | | | |
| NVDA | | | | |
| ORCL | | | | |
| PANW | | | | |
| PLTR | | | | |
| QCOM | | | | |
| SMCI | | | | |
| SNOW | | | | |
| TSLA | | | | |
| UBER | | | | |
| XOM | | | | |
| CVX | | | | |

---

## Notes on Market Data

- Uses both `yfinance` and direct Yahoo Finance **v8/v10 APIs** for better rate-limit resilience
- `yfinance.Search` is used for ticker search; falls back to an empty list if unavailable
- Fields from Polygon's reference API (CIK, FIGI, composite FIGI) are not available via Yahoo Finance and will return `null`
- Quote results are cached for **15 seconds** by default to reduce upstream API pressure

---