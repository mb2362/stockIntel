"""
Inference wrapper that exactly replicates the get_stock_prediction() function
from LSTM_signal_v3_pytorch_dynamic_FINAL.ipynb.

Uses per-ticker model checkpoints from /models/{TICKER}/:
  - dual_lstm_model.pth  → checkpoint dict with ensemble_configs, weights, state_dicts
  - scaler_features.pkl  → list of StandardScalers (one per ensemble member)
  - scaler_price.pkl     → list of StandardScalers (one per ensemble member)

Architecture matches notebook Cell 7 (18 features + LayerNorm).
Inference logic matches notebook get_stock_prediction() exactly.
Target-date logic accounts for NYSE market hours, weekends, and holidays.
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
from functools import lru_cache
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# ── Model assets root (mounted from host ./models/ to /models) ──────────────
MODELS_DIR = os.environ.get("MODELS_DIR", "/models")

# ── NYSE Market Calendar ──────────────────────────────────────────────────────
_ET = ZoneInfo("America/New_York")

def _easter(year: int) -> date:
    """Compute Easter Sunday — Anonymous Gregorian algorithm."""
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
    """Shift holiday to nearest weekday if it falls on a weekend."""
    if d.weekday() == 5:   # Saturday → Friday
        return d - timedelta(days=1)
    if d.weekday() == 6:   # Sunday  → Monday
        return d + timedelta(days=1)
    return d


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Return the nth occurrence of weekday (0=Mon) in the given month."""
    first = date(year, month, 1)
    delta = (weekday - first.weekday()) % 7
    return first + timedelta(days=delta + (n - 1) * 7)


def _last_weekday(year: int, month: int, weekday: int) -> date:
    """Return the last occurrence of weekday in the given month."""
    # last day of month
    last = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
    delta = (last.weekday() - weekday) % 7
    return last - timedelta(days=delta)


def _nyse_holidays(year: int) -> set:
    """All NYSE observed holidays for the given year."""
    good_friday = _easter(year) - timedelta(days=2)
    return {
        _observed(date(year, 1, 1)),      # New Year's Day
        _nth_weekday(year, 1, 0, 3),      # MLK Day        (3rd Mon Jan)
        _nth_weekday(year, 2, 0, 3),      # Presidents Day (3rd Mon Feb)
        good_friday,                       # Good Friday
        _last_weekday(year, 5, 0),        # Memorial Day   (last Mon May)
        _observed(date(year, 6, 19)),     # Juneteenth
        _observed(date(year, 7, 4)),      # Independence Day
        _nth_weekday(year, 9, 0, 1),      # Labor Day      (1st Mon Sep)
        _nth_weekday(year, 11, 3, 4),     # Thanksgiving   (4th Thu Nov)
        _observed(date(year, 12, 25)),    # Christmas
    }


def _is_trading_day(d: date) -> bool:
    return d.weekday() < 5 and d not in _nyse_holidays(d.year)


def _next_trading_day(d: date) -> date:
    candidate = d + timedelta(days=1)
    while not _is_trading_day(candidate):
        candidate += timedelta(days=1)
    return candidate


def get_prediction_target_date() -> tuple:
    """
    Returns (target_date: date, market_is_open: bool).
    - If the NYSE is currently open  → target = today   (predicting today's close)
    - If the NYSE is currently closed → target = next trading day
    """
    now_et  = datetime.now(_ET)
    today   = now_et.date()

    open_time  = now_et.replace(hour=9,  minute=30, second=0, microsecond=0)
    close_time = now_et.replace(hour=16, minute=0,  second=0, microsecond=0)

    market_is_open = (
        _is_trading_day(today)
        and open_time <= now_et <= close_time
    )

    target_date = today if market_is_open else _next_trading_day(today)
    return target_date, market_is_open

# ── 18 feature columns — exactly matches notebook Cell 5 ─────────────────────
FEATURE_COLS = [
    "rsi_14", "macd", "macd_signal", "bb_width",
    "return_3d", "return_5d", "volatility_5d", "volatility_10d",
    "volatility_20d",
    "dist_sma_10", "dist_sma_20", "dist_sma_50", "dist_sma_200",
    "dist_52w_high", "dist_52w_low",
    "volume_ratio",
    "spy_return", "vix_level",
]


# ── DualLSTM — exactly matches notebook Cell 7 ───────────────────────────────
class DualLSTM(nn.Module):
    def __init__(self, input_size, hidden_size=128, second_hidden=64,
                 dense_size=32, dropout=0.2):
        super().__init__()

        # Layer 1
        self.lstm1 = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.norm1 = nn.LayerNorm(hidden_size)
        self.drop1 = nn.Dropout(dropout)

        # Layer 2
        self.lstm2 = nn.LSTM(hidden_size, second_hidden, batch_first=True)
        self.norm2 = nn.LayerNorm(second_hidden)
        self.drop2 = nn.Dropout(dropout)

        # Dense shared trunk
        self.fc1     = nn.Linear(second_hidden, dense_size)
        self.relu    = nn.ReLU()
        self.fc_drop = nn.Dropout(dropout / 2)
        self.fc2     = nn.Linear(dense_size, dense_size)

        # Head 1: Signal (BUY/SELL)
        self.signal_fc   = nn.Linear(dense_size, dense_size // 2)
        self.signal_head = nn.Linear(dense_size // 2, 1)

        # Head 2: Price (next-day % return)
        self.price_fc   = nn.Linear(dense_size, dense_size // 2)
        self.price_head = nn.Linear(dense_size // 2, 1)

    def forward(self, x):
        x, _ = self.lstm1(x)
        x     = self.norm1(x)
        x     = self.drop1(x)

        x, _ = self.lstm2(x)
        x     = self.norm2(x)
        x     = self.drop2(x[:, -1, :])   # last timestep only

        x = self.relu(self.fc1(x))
        x = self.fc_drop(x)
        x = self.relu(self.fc2(x))

        sig_out = self.relu(self.signal_fc(x))
        sig_out = self.signal_head(sig_out).squeeze(-1)

        prc_out = self.relu(self.price_fc(x))
        prc_out = self.price_head(prc_out).squeeze(-1)

        return sig_out, prc_out


# ── Feature engineering — exactly matches notebook Cell 4 ────────────────────
def _engineer_features(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Replicates the engineer_features() function from the notebook.
    Expects raw_df to already have spy_return and vix_level columns.
    """
    flat = {}
    src = raw_df.copy()

    # Flatten MultiIndex if present
    if isinstance(src.columns, pd.MultiIndex):
        src.columns = [str(c[0]) if isinstance(c, tuple) else str(c)
                       for c in src.columns]

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in src.columns:
            extracted = src[col]
            if isinstance(extracted, pd.DataFrame):
                flat[col] = extracted.iloc[:, 0].to_numpy(dtype=float, na_value=np.nan)
            else:
                flat[col] = extracted.to_numpy(dtype=float, na_value=np.nan)

    if "Date" in src.columns:
        flat["Date"] = src["Date"].values

    for extra_col in ["spy_return", "vix_level"]:
        if extra_col in src.columns:
            extracted = src[extra_col]
            if isinstance(extracted, pd.DataFrame):
                flat[extra_col] = extracted.iloc[:, 0].to_numpy(dtype=float, na_value=np.nan)
            else:
                flat[extra_col] = extracted.to_numpy(dtype=float, na_value=np.nan)

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
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs       = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi_14"] = 100 - (100 / (1 + rs))

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["macd"]        = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    rolling_mean  = close.rolling(20).mean()
    rolling_std   = close.rolling(20).std()
    df["bb_upper"] = rolling_mean + (2 * rolling_std)
    df["bb_lower"] = rolling_mean - (2 * rolling_std)
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

    rolling_52w_high    = close.rolling(252).max()
    rolling_52w_low     = close.rolling(252).min()
    df["dist_52w_high"] = (close - rolling_52w_high) / rolling_52w_high
    df["dist_52w_low"]  = (close - rolling_52w_low)  / rolling_52w_low

    df["volume_sma_20"] = volume.rolling(20).mean()
    df["volume_ratio"]  = volume / df["volume_sma_20"].replace(0, np.nan)

    return df.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)


def _safe_download(ticker: str, period: str = "5y") -> pd.DataFrame:
    """Thin wrapper around yf.download with retries."""
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


@lru_cache(maxsize=2)
def _get_macro_series():
    """Download SPY and VIX once and cache for the session."""
    spy_series = _safe_download("SPY", "5y")["Close"].pct_change()
    vix_series = _safe_download("^VIX", "5y")["Close"]

    if isinstance(spy_series, pd.DataFrame): spy_series = spy_series.iloc[:, 0]
    if isinstance(vix_series, pd.DataFrame): vix_series = vix_series.iloc[:, 0]

    spy_series.index = pd.to_datetime(spy_series.index)
    vix_series.index = pd.to_datetime(vix_series.index)
    spy_series.name  = "spy_return"
    vix_series.name  = "vix_level"
    return spy_series, vix_series


# ── Public API ─────────────────────────────────────────────────────────────────
def predict(symbol: str) -> dict:
    """
    Exactly replicates get_stock_prediction(ticker_symbol) from the notebook.
    Loads the per-ticker ensemble from models/{symbol}/.
    """
    symbol = symbol.upper()
    model_dir = os.path.join(MODELS_DIR, symbol)
    ckpt_path = os.path.join(model_dir, "dual_lstm_model.pth")
    sx_path   = os.path.join(model_dir, "scaler_features.pkl")
    sy_path   = os.path.join(model_dir, "scaler_price.pkl")

    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(
            f"No trained model found for {symbol} at {ckpt_path}"
        )

    # Load checkpoint
    checkpoint       = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    ensemble_configs = checkpoint["ensemble_configs"]
    ensemble_weights = np.array(checkpoint["ensemble_weights"], dtype=np.float64)
    threshold        = float(checkpoint.get("threshold", 0.5))
    scalers_X        = joblib.load(sx_path)
    scalers_y        = joblib.load(sy_path)

    # Download macro data (cached)
    spy_series, vix_series = _get_macro_series()

    probs       = []
    prices_raw  = []
    ran_indices = []
    last_close  = None

    for model_idx, cfg in enumerate(ensemble_configs):
        # Build model with this config's exact dimensions
        model = DualLSTM(
            input_size    = len(FEATURE_COLS),
            hidden_size   = cfg["hidden_size"],
            second_hidden = cfg["second_hidden"],
            dense_size    = cfg["dense_size"],
            dropout       = cfg["dropout"]
        )
        model.load_state_dict(
            checkpoint["ensemble_model_state_dicts"][model_idx], strict=True
        )
        model.eval()

        # Download ticker data for this config's period
        df = _safe_download(symbol, cfg["period"])
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
        df = df.loc[:, ~df.columns.duplicated()]
        df = df.reset_index().sort_values("Date").reset_index(drop=True)

        # Merge macro data
        df = df.set_index("Date")
        df = df.join(spy_series, how="left").join(vix_series, how="left")
        df[["spy_return", "vix_level"]] = df[["spy_return", "vix_level"]].ffill()
        df = df.reset_index()

        # Feature engineering
        df = _engineer_features(df)

        lookback = cfg["lookback"]
        if len(df) < lookback + 5:
            logger.warning(f"Skipping config {model_idx}: not enough rows for {symbol}")
            continue

        last_close = float(df["Close"].iloc[-1])

        X_scaled = scalers_X[model_idx].transform(df[FEATURE_COLS].values)
        X_input  = torch.tensor(
            X_scaled[-lookback:], dtype=torch.float32
        ).unsqueeze(0)

        with torch.no_grad():
            sig_logit, price_out = model(X_input)

        prob             = float(torch.sigmoid(sig_logit).item())
        predicted_return = float(
            scalers_y[model_idx].inverse_transform([[price_out.item()]])[0][0]
        )

        probs.append(prob)
        prices_raw.append(predicted_return)
        ran_indices.append(model_idx)

    if not probs:
        raise ValueError(f"Not enough processed rows for inference on {symbol}.")

    # Weighted ensemble average — mirrors notebook exactly
    active_weights       = ensemble_weights[ran_indices]
    active_weights       = active_weights / active_weights.sum()
    ensemble_prob        = float(np.average(probs,      weights=active_weights))
    ensemble_return_pred = float(np.average(prices_raw, weights=active_weights))

    predicted_next_close = round(last_close * (1 + ensemble_return_pred), 2)
    predicted_pct_change = round(ensemble_return_pred * 100, 4)

    # BUY / SELL / HOLD thresholds — mirrors notebook exactly
    upper_hold = min(0.60, max(0.55, threshold + 0.08))
    lower_hold = max(0.40, min(0.45, threshold - 0.08))

    if ensemble_prob >= upper_hold:
        signal = "BUY"
    elif ensemble_prob <= lower_hold:
        signal = "SELL"
    else:
        signal = "HOLD"

    sig_std = float(np.std(probs)) if len(probs) > 1 else 0.0
    if sig_std > 0.10:
        note = f"High model disagreement (std={sig_std:.3f})"
    elif abs(ensemble_prob - threshold) < 0.05:
        note = f"Near threshold (diff={abs(ensemble_prob - threshold):.3f})"
    else:
        note = "Models agree"

    target_date, market_is_open = get_prediction_target_date()

    return {
        "symbol":          symbol,
        "signal":          signal,
        "confidence":      round(ensemble_prob, 4),
        "current_price":   round(last_close, 2),
        "predicted_price": predicted_next_close,
        "pct_change":      predicted_pct_change,
        "confidence_note": note,
        "target_date":     target_date.isoformat(),
        "market_is_open":  market_is_open,
        "CANARY":          "DETECTED",
    }
