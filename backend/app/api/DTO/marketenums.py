"""Market type enumerations used in stock data schemas."""
from enum import Enum

class MarketEnum(str, Enum):
     STOCKS = "stocks"
     FX = "fx"
     OTC = "otc"
     INDICIES = "indices"