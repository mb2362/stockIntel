"""
Inference wrapper — sentiment-aware update.

Changes vs. previous version:
  - feature_cols read from checkpoint (no longer hardcoded to 18)
  - has_sentiment flag read from checkpoint
  - _engineer_features now passes through news_sentiment + computes news_sentiment_delta
  - Finnhub sentiment fetched inline when has_sentiment=True (TTL-cached 1 h)
  - predict() return dict gains sentiment_score + sentiment_used fields
  - Everything else unchanged: NYSE calendar, _get_macro_series cache,
    _safe_download retries, MODELS_DIR env var, get_prediction_target_date
"""

import os
import time
import logging
import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import yfinance as yf
from datetime import date, datetime, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# ── Model assets root ─────────────────────────────────────────────────────────
MODELS_DIR = os.environ.get(
    "MODELS_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "models")
)

# ── Finnhub ───────────────────────────────────────────────────────────────────
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "d72qd9hr01qlfd9o6s80d72qd9hr01qlfd9o6s8g")

# ── NYSE Market Calendar ──────────────────────────────────────────────────────
_ET = ZoneInfo("America/New_York")


def _easter(year: int) -> date:
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day   = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _observed(d: date) -> date:
    if d.weekday() == 5: return d - timedelta(days=1)
    if d.weekday() == 6: return d + timedelta(days=1)
    return d


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    delta = (weekday - first.weekday()) % 7
    return first + timedelta(days=delta + (n - 1) * 7)


def _last_weekday(year: int, month: int, weekday: int) -> date:
    last = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
    delta = (last.weekday() - weekday) % 7
    return last - timedelta(days=delta)


def _nyse_holidays(year: int) -> set:
    good_friday = _easter(year) - timedelta(days=2)
    return {
        _observed(date(year, 1, 1)),
        _nth_weekday(year, 1, 0, 3),
        _nth_weekday(year, 2, 0, 3),
        good_friday,
        _last_weekday(year, 5, 0),
        _observed(date(year, 6, 19)),
        _observed(date(year, 7, 4)),
        _nth_weekday(year, 9, 0, 1),
        _nth_weekday(year, 11, 3, 4),
        _observed(date(year, 12, 25)),
    }


def _is_trading_day(d: date) -> bool:
    return d.weekday() < 5 and d not in _nyse_holidays(d.year)


def _next_trading_day(d: date) -> date:
    candidate = d + timedelta(days=1)
    while not _is_trading_day(candidate):
        candidate += timedelta(days=1)
    return candidate


def get_prediction_target_date() -> tuple:
    now_et     = datetime.now(_ET)
    today      = now_et.date()
    open_time  = now_et.replace(hour=9,  minute=30, second=0, microsecond=0)
    close_time = now_et.replace(hour=16, minute=0,  second=0, microsecond=0)
    market_is_open = (
        _is_trading_day(today) and open_time <= now_et <= close_time
    )
    target_date = today if market_is_open else _next_trading_day(today)
    return target_date, market_is_open


# ── DualLSTM — exactly matches notebook Cell 8 ───────────────────────────────
class DualLSTM(nn.Module):
    def __init__(self, input_size, hidden_size=128, second_hidden=64,
                 dense_size=32, dropout=0.2):
        super().__init__()
        self.lstm1       = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.norm1       = nn.LayerNorm(hidden_size)
        self.drop1       = nn.Dropout(dropout)
        self.lstm2       = nn.LSTM(hidden_size, second_hidden, batch_first=True)
        self.norm2       = nn.LayerNorm(second_hidden)
        self.drop2       = nn.Dropout(dropout)
        self.fc1         = nn.Linear(second_hidden, dense_size)
        self.relu        = nn.ReLU()
        self.fc_drop     = nn.Dropout(dropout / 2)
        self.fc2         = nn.Linear(dense_size, dense_size)
        self.signal_fc   = nn.Linear(dense_size, dense_size // 2)
        self.signal_head = nn.Linear(dense_size // 2, 1)
        self.price_fc    = nn.Linear(dense_size, dense_size // 2)
        self.price_head  = nn.Linear(dense_size // 2, 1)

    def forward(self, x):
        x, _ = self.lstm1(x);  x = self.norm1(x);  x = self.drop1(x)
        x, _ = self.lstm2(x);  x = self.norm2(x);  x = self.drop2(x[:, -1, :])
        x = self.relu(self.fc1(x));  x = self.fc_drop(x);  x = self.relu(self.fc2(x))
        sig_out = self.signal_head(self.relu(self.signal_fc(x))).squeeze(-1)
        prc_out = self.price_head(self.relu(self.price_fc(x))).squeeze(-1)
        return sig_out, prc_out


# ── Feature engineering — mirrors notebook Cell 5 exactly ────────────────────
def _engineer_features(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Replicates engineer_features() from the notebook.
    Passes through spy_return, vix_level, AND news_sentiment when present.
    Also computes news_sentiment_delta (3-day momentum) when news_sentiment exists.
    """
    flat = {}
    src  = raw_df.copy()

    if isinstance(src.columns, pd.MultiIndex):
        src.columns = [str(c[0]) if isinstance(c, tuple) else str(c)
                       for c in src.columns]

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in src.columns:
            e = src[col]
            flat[col] = (e.iloc[:, 0] if isinstance(e, pd.DataFrame) else e
                         ).to_numpy(dtype=float, na_value=np.nan)

    if "Date" in src.columns:
        flat["Date"] = src["Date"].values

    # ✅ news_sentiment passed through alongside macro cols
    for extra_col in ["spy_return", "vix_level", "news_sentiment"]:
        if extra_col in src.columns:
            e = src[extra_col]
            flat[extra_col] = (e.iloc[:, 0] if isinstance(e, pd.DataFrame) else e
                               ).to_numpy(dtype=float, na_value=np.nan)

    df     = pd.DataFrame(flat)
    close  = df["Close"]
    volume = df["Volume"]

    df["sma_10"]  = close.rolling(10).mean()
    df["sma_20"]  = close.rolling(20).mean()
    df["sma_50"]  = close.rolling(50).mean()
    df["sma_200"] = close.rolling(200).mean()

    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    rs       = gain.rolling(14).mean() / loss.rolling(14).mean().replace(0, np.nan)
    df["rsi_14"] = 100 - (100 / (1 + rs))

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["macd"]        = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    rm, rs_ = close.rolling(20).mean(), close.rolling(20).std()
    df["bb_upper"] = rm + 2 * rs_
    df["bb_lower"] = rm - 2 * rs_
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / close

    df["return"]         = close.pct_change()
    df["return_3d"]      = close.pct_change(3)
    df["return_5d"]      = close.pct_change(5)
    df["volatility_5d"]  = df["return"].rolling(5).std()
    df["volatility_10d"] = df["return"].rolling(10).std()
    df["volatility_20d"] = df["return"].rolling(20).std()

    df["dist_sma_10"]  = (close - df["sma_10"])  / df["sma_10"]
    df["dist_sma_20"]  = (close - df["sma_20"])  / df["sma_20"]
    df["dist_sma_50"]  = (close - df["sma_50"])  / df["sma_50"]
    df["dist_sma_200"] = (close - df["sma_200"]) / df["sma_200"]

    h52 = close.rolling(252).max()
    l52 = close.rolling(252).min()
    df["dist_52w_high"] = (close - h52) / h52
    df["dist_52w_low"]  = (close - l52) / l52

    df["volume_sma_20"] = volume.rolling(20).mean()
    df["volume_ratio"]  = volume / df["volume_sma_20"].replace(0, np.nan)

    # ✅ 3-day sentiment momentum — only when column exists
    if "news_sentiment" in df.columns:
        df["news_sentiment_delta"] = df["news_sentiment"].diff(3)

    return df.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)


# ── Finnhub sentiment (TTL-cached per ticker) ─────────────────────────────────
_sentiment_cache: dict = {}   # { ticker: (timestamp, score) }
_SENTIMENT_TTL = 3600         # 1 hour

_POS = {"beat","surge","rally","gain","growth","profit","exceed","strong",
        "upgrade","positive","bullish","record","raise","outperform","success",
        "expand","rise","high","buy","boost","accelerat","innovati","partner",
        "award","approv","launch","revenue","dividend","buyback","breakthrough",
        "soar","jump"}
_NEG = {"miss","drop","fall","loss","decline","weak","downgrade","negative",
        "bearish","cut","layoff","recall","lawsuit","investigat","fraud","down",
        "low","sell","warning","risk","disappoint","concern","fear","crash",
        "plunge","probe","regulat","penalt","fine","bankrupt","restructur","slump"}


def _score_headline(text: str) -> float:
    words = text.lower().split()
    p = sum(1 for w in words if any(w.startswith(s) for s in _POS))
    n = sum(1 for w in words if any(w.startswith(s) for s in _NEG))
    return (p - n) / (p + n) if (p + n) else 0.0


def _fetch_sentiment_series(ticker: str, n_days: int = 365) -> pd.DataFrame:
    """
    Returns DataFrame[Date, news_sentiment] with 5-day rolling mean.
    Returns empty DataFrame on any failure.
    """
    if not FINNHUB_API_KEY:
        return pd.DataFrame(columns=["Date", "news_sentiment"])
    try:
        import finnhub
        fh     = finnhub.Client(api_key=FINNHUB_API_KEY)
        to_d   = datetime.today().strftime("%Y-%m-%d")
        from_d = (datetime.today() - timedelta(days=n_days)).strftime("%Y-%m-%d")
        arts   = fh.company_news(ticker, _from=from_d, to=to_d)
        if not arts:
            return pd.DataFrame(columns=["Date", "news_sentiment"])
        recs = [
            {"Date":  pd.to_datetime(a.get("datetime", 0), unit="s").normalize(),
             "score": _score_headline(a.get("headline","") + " " + a.get("summary",""))}
            for a in arts
        ]
        df_n = (pd.DataFrame(recs)
                  .groupby("Date")["score"].mean()
                  .rename("news_sentiment_raw")
                  .reset_index()
                  .sort_values("Date"))
        df_n["news_sentiment"] = df_n["news_sentiment_raw"].rolling(5, min_periods=1).mean()
        return df_n[["Date", "news_sentiment"]]
    except Exception as e:
        logger.warning(f"Finnhub fetch failed for {ticker}: {e}")
        return pd.DataFrame(columns=["Date", "news_sentiment"])


def _get_latest_sentiment_score(ticker: str) -> float:
    """Returns latest rolling-mean sentiment score, with in-process TTL cache."""
    now = time.time()
    if ticker in _sentiment_cache:
        ts, score = _sentiment_cache[ticker]
        if now - ts < _SENTIMENT_TTL:
            return score
    df_n = _fetch_sentiment_series(ticker, n_days=90)
    score = float(df_n["news_sentiment"].iloc[-1]) if not df_n.empty else 0.0
    _sentiment_cache[ticker] = (now, score)
    return score


# ── Macro data (cached for session) ──────────────────────────────────────────
@lru_cache(maxsize=2)
def _get_macro_series():
    """Download SPY and VIX once and cache for the session."""
    spy = _safe_download("SPY", "5y")["Close"].pct_change()
    vix = _safe_download("^VIX", "5y")["Close"]
    if isinstance(spy, pd.DataFrame): spy = spy.iloc[:, 0]
    if isinstance(vix, pd.DataFrame): vix = vix.iloc[:, 0]
    spy.index = pd.to_datetime(spy.index); spy.name = "spy_return"
    vix.index = pd.to_datetime(vix.index); vix.name = "vix_level"
    return spy, vix


def _safe_download(ticker: str, period: str = "5y") -> pd.DataFrame:
    """yf.download with 3 retries."""
    for attempt in range(3):
        try:
            df = yf.download(ticker, period=period, interval="1d",
                             progress=False, auto_adjust=True)
            if not df.empty:
                return df
        except Exception as e:
            logger.warning(f"Download attempt {attempt+1} failed for {ticker}: {e}")
        time.sleep(1)
    raise RuntimeError(f"Failed to download data for {ticker}")


# ── Public API ────────────────────────────────────────────────────────────────
def predict(symbol: str) -> dict:
    """
    Loads the per-ticker ensemble and runs inference.

    Automatically detects whether the model was trained with news sentiment
    (via has_sentiment flag in checkpoint) and fetches live Finnhub data
    when applicable.

    Returns
    -------
    dict: symbol, signal, confidence, confidence_note, current_price,
          predicted_price, pct_change, target_date, market_is_open,
          sentiment_score, sentiment_used
    """
    symbol    = symbol.upper()
    model_dir = os.path.join(MODELS_DIR, symbol)
    ckpt_path = os.path.join(model_dir, "dual_lstm_model.pth")
    sx_path   = os.path.join(model_dir, "scaler_features.pkl")
    sy_path   = os.path.join(model_dir, "scaler_price.pkl")

    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"No trained model found for {symbol} at {ckpt_path}")

    # ── Load checkpoint ───────────────────────────────────────
    checkpoint       = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    ensemble_configs = checkpoint["ensemble_configs"]
    ensemble_weights = np.array(checkpoint["ensemble_weights"], dtype=np.float64)
    threshold        = float(checkpoint.get("threshold", 0.5))
    # ✅ Read feature cols from checkpoint — works for both 18-col and 20-col models
    feature_cols     = checkpoint.get("feature_cols", [
        "rsi_14","macd","macd_signal","bb_width",
        "return_3d","return_5d","volatility_5d","volatility_10d","volatility_20d",
        "dist_sma_10","dist_sma_20","dist_sma_50","dist_sma_200",
        "dist_52w_high","dist_52w_low","volume_ratio","spy_return","vix_level",
    ])
    has_sentiment    = checkpoint.get("has_sentiment", False)
    scalers_X        = joblib.load(sx_path)
    scalers_y        = joblib.load(sy_path)

    # ── Download macro data (session-cached) ──────────────────
    spy_series, vix_series = _get_macro_series()

    # ── Fetch live sentiment when model was trained with it ───
    sentiment_score = 0.0
    sentiment_used  = False
    news_series     = None

    if has_sentiment and "news_sentiment" in feature_cols:
        sentiment_score = _get_latest_sentiment_score(symbol)
        df_n = _fetch_sentiment_series(symbol, n_days=90)
        if not df_n.empty:
            df_n["Date"] = pd.to_datetime(df_n["Date"])
            news_series  = df_n.set_index("Date")["news_sentiment"]
            sentiment_used = True
            logger.info(f"{symbol}: live sentiment score={sentiment_score:.4f}")
        else:
            logger.warning(f"{symbol}: sentiment fallback → 0.0")

    # ── Per-model inference ───────────────────────────────────
    probs       = []
    prices_raw  = []
    ran_indices = []
    last_close  = None

    for model_idx, cfg in enumerate(ensemble_configs):
        model = DualLSTM(
            input_size    = len(feature_cols),   # ✅ dynamic — matches checkpoint
            hidden_size   = cfg["hidden_size"],
            second_hidden = cfg["second_hidden"],
            dense_size    = cfg["dense_size"],
            dropout       = cfg["dropout"],
        )
        model.load_state_dict(
            checkpoint["ensemble_model_state_dicts"][model_idx], strict=True
        )
        model.eval()

        # Download OHLCV for this config's period
        df = _safe_download(symbol, cfg["period"])
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        df = df.loc[:, ~df.columns.duplicated()]
        df = df.reset_index().sort_values("Date").reset_index(drop=True)

        # Merge macro context
        df = df.set_index("Date")
        df = df.join(spy_series, how="left").join(vix_series, how="left")
        df[["spy_return", "vix_level"]] = df[["spy_return", "vix_level"]].ffill()

        # ✅ Merge sentiment when available; fill with 0.0 as fallback
        if "news_sentiment" in feature_cols:
            if news_series is not None:
                df = df.join(news_series, how="left")
                df["news_sentiment"] = df["news_sentiment"].ffill().fillna(0.0)
            else:
                df["news_sentiment"] = 0.0

        df = df.reset_index()
        df = _engineer_features(df)

        lookback = cfg["lookback"]
        if len(df) < lookback + 5:
            logger.warning(f"Skipping config {model_idx} for {symbol}: insufficient rows")
            continue

        last_close = float(df["Close"].iloc[-1])

        # ✅ Only use columns that exist in both df and feature_cols
        available = [f for f in feature_cols if f in df.columns]
        X_scaled  = scalers_X[model_idx].transform(df[available].values)
        X_input   = torch.tensor(X_scaled[-lookback:], dtype=torch.float32).unsqueeze(0)

        with torch.no_grad():
            sig_logit, price_out = model(X_input)

        probs.append(float(torch.sigmoid(sig_logit).item()))
        prices_raw.append(
            float(scalers_y[model_idx].inverse_transform([[price_out.item()]])[0][0])
        )
        ran_indices.append(model_idx)

    if not probs:
        raise ValueError(f"Not enough processed rows for inference on {symbol}.")

    # ── Weighted ensemble average ─────────────────────────────
    active_w             = ensemble_weights[ran_indices]
    active_w             = active_w / active_w.sum()
    ensemble_prob        = float(np.average(probs,      weights=active_w))
    ensemble_return_pred = float(np.average(prices_raw, weights=active_w))

    predicted_next_close = round(last_close * (1 + ensemble_return_pred), 2)
    predicted_pct_change = round(ensemble_return_pred * 100, 4)

    # ── Signal decision ───────────────────────────────────────
    upper_hold = min(0.60, max(0.55, threshold + 0.08))
    lower_hold = max(0.40, min(0.45, threshold - 0.08))

    if   ensemble_prob >= upper_hold: signal = "BUY"
    elif ensemble_prob <= lower_hold: signal = "SELL"
    else:                             signal = "HOLD"

    sig_std = float(np.std(probs)) if len(probs) > 1 else 0.0
    if   sig_std > 0.10:                        note = f"High model disagreement (std={sig_std:.3f})"
    elif abs(ensemble_prob - threshold) < 0.05: note = f"Near threshold (diff={abs(ensemble_prob - threshold):.3f})"
    else:                                        note = "Models agree"

    target_date, market_is_open = get_prediction_target_date()

    return {
        "symbol":          symbol,
        "signal":          signal,
        "confidence":      round(ensemble_prob, 4),
        "confidence_note": note,
        "current_price":   round(last_close, 2),
        "predicted_price": predicted_next_close,
        "pct_change":      predicted_pct_change,
        "target_date":     target_date.isoformat(),
        "market_is_open":  market_is_open,
        # ✅ New fields
        "sentiment_score": round(sentiment_score, 4),
        "sentiment_used":  sentiment_used,
    }