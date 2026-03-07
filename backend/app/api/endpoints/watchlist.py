from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Body, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.database import crud, database, models


router = APIRouter(prefix="/watchlist")


def _demo_user(db: Session) -> models.User:
    username = "demo"
    user = db.query(models.User).filter(models.User.username == username).first()
    if user:
        return user
    user = models.User(username=username, email="demo@example.com", hashed_password="")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("")
async def get_watchlist(db: Session = Depends(database.get_db)):
    """Frontend expects WatchlistItem[]."""
    user = _demo_user(db)
    rows = db.query(models.Watchlist).filter(models.Watchlist.user_id == user.id).all()

    out = []
    for r in rows:
        stock = db.query(models.Stock).filter(models.Stock.id == r.stock_id).first()
        if not stock:
            continue
        out.append(
            {
                "symbol": stock.ticker,
                "name": stock.name or stock.ticker,
                "price": 0,
                "change": 0,
                "changePercent": 0,
                "volume": 0,
                "marketCap": 0,
                "addedAt": datetime.now(timezone.utc).isoformat(),
            }
        )
    return out


@router.post("")
async def add_to_watchlist(
    payload: dict = Body(...), db: Session = Depends(database.get_db)
):
    """POST /watchlist { symbol }"""
    symbol = (payload.get("symbol") or "").upper().strip()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")

    user = _demo_user(db)

    # ensure stock exists (create minimal row if missing)
    stock = crud.get_stock_by_ticker(db, symbol)
    if not stock:
        stock = crud.create_stock(db, {"ticker": symbol, "name": symbol, "market": "stocks", "active": True})

    existing = (
        db.query(models.Watchlist)
        .filter(models.Watchlist.user_id == user.id, models.Watchlist.stock_id == stock.id)
        .first()
    )
    if not existing:
        db.add(models.Watchlist(user_id=user.id, stock_id=stock.id))
        db.commit()

    return {
        "symbol": symbol,
        "name": stock.name or symbol,
        "price": 0,
        "change": 0,
        "changePercent": 0,
        "volume": 0,
        "marketCap": 0,
        "addedAt": datetime.now(timezone.utc).isoformat(),
    }


@router.delete("/{symbol}")
async def remove_from_watchlist(symbol: str, db: Session = Depends(database.get_db)):
    symbol = symbol.upper().strip()
    user = _demo_user(db)
    stock = crud.get_stock_by_ticker(db, symbol)
    if not stock:
        return {"status": "OK"}

    row = (
        db.query(models.Watchlist)
        .filter(models.Watchlist.user_id == user.id, models.Watchlist.stock_id == stock.id)
        .first()
    )
    if row:
        db.delete(row)
        db.commit()
    return {"status": "OK"}
