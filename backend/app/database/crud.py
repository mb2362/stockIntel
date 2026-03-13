from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.api.DTO.schemas import UserCreate
from app.database import models

def create_stock(db: Session, stock_data: dict) -> models.Stock:
    stock_data_filtered = {
        key: value
        for key, value in stock_data.items()
        if key in models.Stock.__table__.columns
    } # create a new object stock_data_filtered that parses through stock_data input and stores all the columns that are there in DB
    stock_data_filtered["last_updated_utc"] = datetime.now(timezone.utc) # update last updated date time
    db_stock = models.Stock(**stock_data_filtered) #create an object that can be saved in db
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock

#get stocks from db based on symbol name
def get_stock_by_ticker(db: Session, ticker: str) -> models.Stock:
    return db.query(models.Stock).filter(models.Stock.ticker == ticker).first()

def create_historical_data(
    db: Session, historical_data: dict
) -> models.HistoricalStockData:
    historical_data_filtered = {
        key: value
        for key, value in historical_data.items()
        if key in models.HistoricalStockData.__table__.columns
    }
    db_historical_data = models.HistoricalStockData(**historical_data_filtered)
    db.add(db_historical_data)
    db.commit()
    db.refresh(db_historical_data)
    return db_historical_data

def get_historical_data_by_stock_and_date(
    db: Session, stock_id: int, timestamp: datetime
) -> models.HistoricalStockData:
    return (
        db.query(models.HistoricalStockData)
        .filter(
            models.HistoricalStockData.stock_id == stock_id,
            models.HistoricalStockData.timestamp == timestamp,
        )
        .first()
    )


# -----------------------------
# User CRUD (needed by auth router)
# -----------------------------


def get_user_by_username(db: Session, username: str) -> models.User | None:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: UserCreate, hashed_password: str) -> models.User:
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user