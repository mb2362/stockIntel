from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from app.api.DTO.marketenums import MarketEnum


class StockData(BaseModel):
    """Stock metadata.

    The original tutorial models Polygon's reference ticker payload.
    With yfinance, many of those fields are not available, so most are optional.
    """

    model_config = ConfigDict(from_attributes=True)

    ticker: str
    name: Optional[str] = None
    market: Optional[MarketEnum] = MarketEnum.STOCKS
    locale: Optional[str] = None
    primary_exchange: Optional[str] = None
    type: Optional[str] = None
    active: Optional[bool] = True
    currency_name: Optional[str] = None
    cik: Optional[str] = None
    composite_figi: Optional[str] = None
    share_class_figi: Optional[str] = None
    last_updated_utc: Optional[datetime] = None


class HistoricalData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: str
    queryCount: int
    resultsCount: int
    adjusted: bool
    results: List[dict]
    status: str
    request_id: str
    count: int


class StockSearch(BaseModel):
    """Search response.

    yfinance does not provide an official, stable ticker-search endpoint.
    We return best-effort matches using yfinance.Search (if available).
    """

    model_config = ConfigDict(from_attributes=True)

    results: List[StockData]
    count: int
    status: str
    request_id: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)