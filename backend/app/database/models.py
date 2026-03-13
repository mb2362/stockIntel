from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    watchlists = relationship("Watchlist", back_populates="user")
    portfolios = relationship("Portfolio", back_populates="user")


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True)
    name = Column(String)
    market = Column(String)
    locale = Column(String)
    primary_exchange = Column(String)
    type = Column(String)
    currency_name = Column(String)
    cik = Column(String)
    composite_figi = Column(String)
    share_class_figi = Column(String)
    last_updated_utc = Column(DateTime)
    active = Column(Boolean)
    news = relationship("News", back_populates="stock")
    historical_data = relationship("HistoricalStockData", back_populates="stock")


class HistoricalStockData(Base):
    __tablename__ = "historical_stock_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String)
    timestamp = Column(DateTime)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    stock = relationship("Stock", back_populates="historical_data")


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stock_id = Column(Integer, ForeignKey("stocks.id"))

    user = relationship("User", back_populates="watchlists")
    stock = relationship("Stock")


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    quantity = Column(Integer)
    purchase_price = Column(Float)
    purchase_date = Column(DateTime)

    user = relationship("User", back_populates="portfolios")
    stock = relationship("Stock")


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    title = Column(String)
    url = Column(String)
    published_at = Column(DateTime)

    stock = relationship("Stock")
