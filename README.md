## Run with:
`docker compose -f docker/docker-compose.yml up --build`

# Stock Market API

This is a backend API for a stock market
application, built using Python and FastAPI. It
provides endpoints for accessing stock data,
managing user accounts, and handling watchlists
and portfolios.

## Features

* **Stock Data:** Retrieve real-time-ish and
  historical stock information using `yfinance`
  (best-effort, based on Yahoo Finance data).
* **User Authentication:** Secure user
  registration and login using JWT (JSON Web
  Tokens).
* **Watchlists:** (To be implemented) Manage user
  watchlists for tracking favorite stocks.
* **Portfolios:** (To be implemented) Track user
  stock portfolios and performance.
* **News:** (To be implemented) Fetch relevant
  financial news.

## Technologies Used

* **Python:** Programming language.
* **FastAPI:** Web framework for building the API.
* **Uvicorn:** ASGI server for running the API.
* **SQLAlchemy:** ORM for database interactions.
* **PostgreSQL:** Database system.
* **Pydantic:** Data validation and serialization.
* **python-jose:** JWT encoding and decoding.
* **passlib:** Password hashing.
* **yfinance:** Market data client.
* **pandas:** Data handling for historical bars.
* **python-dotenv:** For managing environment
  variables.

## Prerequisites

* Python 3.8+
* PostgreSQL database
* No paid market data API key required.

## Setup

1. **Clone the Repository:**

   ```bash
   git clone <repository_url>
   cd stock-market-api
   ```

2. **Create a Virtual Environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   venv\Scripts\activate      # On Windows
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment Variables:**

    * Create a `.env` file in the root directory.
    * Add your database credentials, API key, and
      secret key:

   ```
   DATABASE_URL=postgresql://user:password@host/database
   SECRET_KEY=your_secret_key
   ```

5. **Run the API:**

   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints

### Stock Data

* `GET /stocks/{symbol}`: Retrieve data for a
  specific stock.
*
`GET /stocks/{symbol}/historical?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&multiplier=1&timespan=day`:
Retrieve historical *daily* OHLCV bars for a stock.
* `GET /stocks/search/{query}`: Search for stocks.

### User Authentication

* `POST /auth/token`: User login (get access
  token).
* `POST /auth/users/`: Create a new user (
  register).
* `GET /auth/users/me/`: Get the current user's
  information (protected route).

### Watchlists (To be implemented)

* `GET /watchlists/`: Get user's watchlists.
* `POST /watchlists/`: Create a new watchlist.
* `POST /watchlists/{watchlist_id}/stocks/`: Add
  stock to watchlist.
*
`DELETE /watchlists/{watchlist_id}/stocks/{symbol} `:
Remove stock from watchlist.

### Portfolios (To be implemented)

* `GET /portfolios/`: Get user's portfolios.
* `POST /portfolios/`: Create a new portfolio.
* `POST /portfolios/{portfolio_id}/holdings/`: Add
  stock holding to portfolio.
*
`PUT /portfolios/{portfolio_id}/holdings/{symbol}`:
Update stock holding in portfolio.
*
`DELETE /portfolios/{portfolio_id}/holdings/{symbol}`:
Remove stock holding from portfolio.

### News (To be implemented)

* `GET /news/`: Get recent financial news.
* `GET /news/{symbol}`: Get news related to a
  specific stock.

## Database Schema

* **users:** Stores user information (id,
  username, email, hashed\_password).
* **stocks:** Stores stock information (id,
  ticker, name, market, etc.).
* **historical\_stock\_data:** Stores historical
  stock data (symbol, timestamp, open, high, low,
  close, volume).
* **watchlists:** (To be implemented) Stores user
  watchlists.
* **portfolios:** (To be implemented) Stores user
  portfolios.
* **news:** (To be implemented) Stores financial
  news.

## Authentication

* The API uses JWT (JSON Web Tokens) for
  authentication.
* Users can register and log in to obtain an
  access token.
* The access token must be included in the
  `Authorization` header of protected requests.

## Error Handling

* The API returns appropriate HTTP status codes
  and error messages in JSON format.

## Notes about yfinance

* yfinance does not expose an official, guaranteed ticker-search API.
  This project uses `yfinance.Search` when available; otherwise the
  `/stocks/search/{query}` endpoint returns HTTP 501.
* Many Polygon-specific metadata fields (CIK, FIGI, etc.) may be missing;
  the API returns them as `null`.

## Contributing

Contributions are welcome from group members.