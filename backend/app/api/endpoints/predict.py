"""
FastAPI router for LSTM stock price prediction.
Endpoint: GET /api/v1/predict/{symbol}
"""

from fastapi import APIRouter, HTTPException
from app.ml.predictor import predict

router = APIRouter()

ALLOWED_SYMBOLS = {
    # ── Original 10 ────────────────────────────────────────
    "NVDA", "AMZN", "AXON", "AAPL", "ORCL",
    "MSFT", "JPM",  "META", "TSLA", "AMD",
    # ── Additional 40 ──────────────────────────────────────
    "GOOGL", "GOOG",  "NFLX", "UBER",  "CRM",
    "ADBE",  "INTC",  "QCOM", "MU",    "AVGO",
    "ARM",   "PANW",  "SNOW", "PLTR",  "SMCI",
    "GS",    "MS",    "BAC",  "V",     "MA",
    "BRK-B", "UNH",   "LLY",  "JNJ",   "PFE",
    "XOM",   "CVX",   "COST", "WMT",   "TGT",
    "HD",    "LOW",   "DIS",  "PYPL",  "XYZ",
    "COIN",  "RIVN",  "NIO",  "LCID",  "SOFI",
}


@router.get("/predict/{symbol}", summary="LSTM next-day price prediction")
def get_prediction(symbol: str):
    """
    Returns the model's BUY/SELL signal, confidence score,
    current price, and predicted next-day closing price for a stock.
    Only the 10 supported tickers are accepted.
    """
    sym = symbol.upper()
    if sym not in ALLOWED_SYMBOLS:
        raise HTTPException(
            status_code=400,
            detail=f"'{sym}' is not supported. Allowed: {sorted(ALLOWED_SYMBOLS)}",
        )
    try:
        return predict(sym)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")
