# StockIntel 📈

A full-stack stock market intelligence platform with real-time data, technical analysis, and ML-powered price predictions. Built with FastAPI, React, and a dual-LSTM ensemble model.

---

## Features

- **Real-Time Stock Data** — Live quotes, OHLCV history, and company info via Yahoo Finance
- **Technical Indicators** — RSI, MACD, MA50, and MA200 calculated server-side
- **ML Price Predictions** — Per-ticker dual-LSTM ensemble models trained on 18 features with NYSE calendar-aware inference
- **Market Overview** — Global indices, trending stocks, top gainers and losers
- **Stock Comparison** — Side-by-side multi-symbol comparison
- **User Authentication** — JWT-based registration and login with bcrypt password hashing
- **Watchlists** — Manage and track stocks with live prices
- **Portfolios** — Track holdings and performance
- **News Feed** — Stock-related news articles per symbol
- **Rate Limiting** — Per-IP sliding-window rate limiter (60 req/min)
- **Security Headers** — Applied globally via middleware

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, Recharts, Framer Motion |
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **Database** | PostgreSQL + SQLAlchemy |
| **Validation** | Pydantic v2 |
| **Auth** | JWT (PyJWT) + passlib bcrypt |
| **Market Data** | yfinance + Yahoo Finance v8/v10 API |
| **ML** | PyTorch, dual-LSTM ensemble, scikit-learn scalers |
| **Data** | pandas, numpy |
| **Testing** | pytest, pytest-cov, Vitest, Testing Library |
| **Containers** | Docker + Docker Compose |
| **CI/CD** | GitHub Actions |

---

## Project Structure

```
stockIntel/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/       # stocks, market, watchlist, portfolio, news, auth, predict
│   │   │   ├── security/        # rate limiting, security headers middleware
│   │   │   ├── auth/            # JWT helpers
│   │   │   ├── utils/           # data cleaning
│   │   │   └── docs/            # OpenAPI config
│   │   ├── database/            # SQLAlchemy models, CRUD, engine
│   │   ├── ml/                  # LSTM inference wrapper
│   │   └── ml_assets/           # default model checkpoint + scalers
│   ├── tests/                   # 188 pytest tests (offline, no DB required)
│   ├── docker/                  # Dockerfile, Dockerfile.test
│   ├── requirements.txt
│   └── requirements-test.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # UI components
│   │   ├── pages/               # route-level pages
│   │   ├── hooks/               # custom React hooks
│   │   ├── services/            # Axios API clients
│   │   ├── types/               # TypeScript interfaces
│   │   └── utils/               # formatters, validators, constants
│   └── vite.config.ts
├── models/                      # Per-ticker LSTM checkpoints
│   ├── AAPL/
│   ├── AMD/
│   ├── AMZN/
│   ├── AXON/
│   ├── JPM/
│   ├── META/
│   ├── MSFT/
│   ├── NVDA/
│   ├── ORCL/
│   └── TSLA/
├── LSTM_signal_v3_pytorch_dynamic_FINAL.ipynb  # Model training notebook
└── docker-compose.yml
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (or Docker)
- No paid API keys required

### Run with Docker (recommended)

```bash
git clone <repository_url>
cd stockIntel
docker compose up --build
```

This starts three services together:

| Service | Port |
|---|---|
| Backend API | 8001 |
| Frontend | 5173 |
| PostgreSQL | 5432 |

### Manual Setup

**Backend**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql://user:password@host/database
SECRET_KEY=your_secret_key
```

```bash
uvicorn app.main:app --reload --port 8001
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Interactive API docs are available at [http://localhost:8001/docs](http://localhost:8001/docs).

---

## API Reference

### Stocks

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/stocks` | Paginated stock list |
| GET | `/api/v1/stocks/search?q=` | Search stocks |
| GET | `/api/v1/stocks/gainers` | Top gainers |
| GET | `/api/v1/stocks/losers` | Top losers |
| GET | `/api/v1/stocks/{symbol}/quote` | Live quote |
| GET | `/api/v1/stocks/{symbol}/info` | Company details |
| GET | `/api/v1/stocks/{symbol}/historical?range=1M` | OHLCV history |
| GET | `/api/v1/stocks/{symbol}/indicators` | RSI, MACD, MA50, MA200 |
| GET | `/api/v1/stocks/{symbol}/news` | News articles |
| POST | `/api/v1/stocks/compare` | Compare multiple symbols |

### Market

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/market/overview` | Global indices |
| GET | `/api/v1/market/trending` | Trending stocks |
| GET | `/api/v1/market/gainers` | Market gainers |
| GET | `/api/v1/market/losers` | Market losers |

### Watchlist

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/watchlist` | Get user's watchlist |
| POST | `/api/v1/watchlist` | Add a symbol |
| DELETE | `/api/v1/watchlist/{symbol}` | Remove a symbol |

### Predictions

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/predict/{symbol}` | LSTM price prediction for supported tickers |

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/token` | Login — returns JWT |
| POST | `/api/v1/auth/users/` | Register new user |
| GET | `/api/v1/auth/users/me/` | Current authenticated user |

**Protected routes** require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

---

## ML Model

StockIntel includes a **dual-LSTM ensemble** for next-day price signal prediction on 10 tickers (AAPL, AMD, AMZN, AXON, JPM, META, MSFT, NVDA, ORCL, TSLA).

- Architecture: dual-LSTM with LayerNorm, 18 input features
- Inference: per-ticker checkpoints (`dual_lstm_model.pth`, `scaler_features.pkl`, `scaler_price.pkl`)
- Market calendar: NYSE holidays and market hours are accounted for in target-date logic
- Training notebook: `LSTM_signal_v3_pytorch_dynamic_FINAL.ipynb`

---

## Database Schema

| Table | Key Columns |
|---|---|
| `users` | id, username, email, hashed_password |
| `stocks` | id, ticker, name, market, active |
| `historical_stock_data` | symbol, timestamp, open, high, low, close, volume |
| `watchlists` | id, user_id, stock_id |
| `portfolios` | id, user_id, stock_id, quantity, purchase_price |
| `news` | id, stock_id, title, url, published_at |

---

## Testing

The backend has **188 tests** with **>70% coverage**. Tests run fully offline — no database or live API connection required.

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-test.txt
pytest
```

Run with coverage report:

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

See [`backend/README-TESTS.md`](backend/README-TESTS.md) for Docker-based testing, coverage configuration, and troubleshooting.

---

## CI/CD

GitHub Actions runs on every push and pull request to `main`:

- **Backend:** pytest suite with coverage gate (fails if coverage drops below 80%)
- **Frontend:** TypeScript compile + Vite production build
- Both jobs must pass before the pipeline is marked green

See [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) for the full configuration.

---

## Notes on Market Data

- Yahoo Finance v8/v10 APIs are used directly alongside `yfinance` for better rate-limit resilience
- Quote results are cached for 15 seconds to reduce upstream API pressure
- Symbol search uses `yfinance.Search` with a fallback to an empty list
- Fields from Polygon's reference API (CIK, FIGI, etc.) are not available via yfinance and return `null`

---

## Contributing

Pull requests are welcome from group members. Please ensure all backend tests pass and coverage remains above 80% before submitting.