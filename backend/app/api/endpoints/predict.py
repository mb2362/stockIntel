"""
FastAPI router for LSTM stock price prediction.
Endpoint: GET /api/v1/predict/{symbol}
"""

from fastapi import APIRouter, HTTPException
from app.ml.predictor import predict

router = APIRouter()

ALLOWED_SYMBOLS = {
    "NVDA", "AMZN", "AXON", "AAPL", "ORCL",
    "MSFT", "JPM",  "META", "TSLA", "AMD",
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
