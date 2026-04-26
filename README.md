## Run with:
`docker compose up --build`

# StockIntel – Stock Market API

A backend API for a stock market application built with Python and FastAPI.
Provides endpoints for real-time stock data, user authentication, watchlists, and portfolios.

---

## 🧪 Testing

The backend has a full pytest suite with **188 tests** and **71.8% coverage**.
Tests run completely offline — no database or internet connection required.

**Quick start:**
```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-test.txt
pytest
```

For full details — coverage reports, Docker-based testing, CI/CD setup, and troubleshooting — see **[backend/README-TESTS.md](backend/README-TESTS.md)**.

### CI/CD
Tests run automatically on every push and pull request to `main` via GitHub Actions.
The build fails if coverage drops below 70%. See [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml).

---

## Features

* **Stock Data:** Real-time and historical stock data via Yahoo Finance (`yfinance` + direct v8/v10 API).
* **User Authentication:** JWT-based registration and login.
* **Watchlists:** Manage tracked stocks with live prices.
* **Portfolios:** Track stock holdings and performance.
* **News:** Fetch stock-related news articles.
* **Technical Indicators:** RSI, MACD, MA50, MA200.
* **Stock Comparison:** Side-by-side comparison of multiple symbols.
* **Pagination:** Browsable stock list with 100+ symbols.

## Technologies

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL + SQLAlchemy |
| Validation | Pydantic v2 |
| Auth | JWT (PyJWT) + passlib bcrypt |
| Market data | yfinance + Yahoo Finance v8/v10 API |
| Data handling | pandas |
| Testing | pytest + pytest-cov |
| Containerisation | Docker + Docker Compose |

## Prerequisites

* Python 3.11+
* PostgreSQL (or Docker)
* No paid API key required

## Setup

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd stockIntel-main
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS/Linux
   venv\Scripts\activate      # Windows
   ```

3. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Set up environment variables** — create `backend/.env`:
   ```
   DATABASE_URL=postgresql://user:password@host/database
   SECRET_KEY=your_secret_key
   ```

5. **Run the API:**
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```

### Run with Docker (recommended)
```bash
docker compose up --build
```
This starts the API (port 8001), frontend (port 5173), and PostgreSQL together.

## API Endpoints

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
| POST | `/api/v1/stocks/compare` | Compare symbols |

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
| GET | `/api/v1/watchlist` | Get watchlist |
| POST | `/api/v1/watchlist` | Add symbol |
| DELETE | `/api/v1/watchlist/{symbol}` | Remove symbol |

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/token` | Login |
| POST | `/api/v1/auth/users/` | Register |
| GET | `/api/v1/auth/users/me/` | Current user |

## Database Schema

| Table | Key columns |
|---|---|
| `users` | id, username, email, hashed_password |
| `stocks` | id, ticker, name, market, active |
| `historical_stock_data` | symbol, timestamp, open, high, low, close, volume |
| `watchlists` | id, user_id, stock_id |
| `portfolios` | id, user_id, stock_id, quantity, purchase_price |
| `news` | id, stock_id, title, url, published_at |

## Authentication

JWT tokens are used for protected routes. Include the token in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

## Notes on Market Data

* Uses Yahoo Finance v8/v10 APIs directly alongside `yfinance` for better rate-limit resilience.
* Quote results are cached for 15 seconds to reduce upstream API pressure.
* `yfinance.Search` is used for symbol search when available; falls back to empty list if unavailable.
* Fields from Polygon's reference API (CIK, FIGI, etc.) are not available via yfinance and return `null`.

## Contributing

Contributions are welcome from group members.
