"""Watchlist API endpoints – get, add, remove symbols with live prices."""
from __future__ import annotations

from datetime import datetime, timezone
import concurrent.futures

from fastapi import APIRouter, Body, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.database import crud, database, models
from app.api.utils.data_cleaner import normalise_watchlist_item, clean_symbol
from app.api.security.middleware import sanitise_symbol_param


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
    """Frontend expects WatchlistItem[] with live prices."""
    user = _demo_user(db)
    rows = db.query(models.Watchlist).filter(models.Watchlist.user_id == user.id).all()

    symbols = []
    symbol_to_name = {}
    for r in rows:
        stock = db.query(models.Stock).filter(models.Stock.id == r.stock_id).first()
        if stock:
            symbols.append(stock.ticker)
            symbol_to_name[stock.ticker] = stock.name or stock.ticker

    if not symbols:
        return []

    # Fetch live prices concurrently using same robust logic as other endpoints
    from app.api.endpoints.stocks import _build_quote_parts

    def fetch_quote(sym):
        try:
            qp = _build_quote_parts(sym)
            change = qp.price - qp.prev_close
            change_pct = (change / qp.prev_close * 100.0) if qp.prev_close else 0.0
            raw = {
                "symbol": sym,
                "name": symbol_to_name.get(sym, sym),
                "price": qp.price,
                "change": change,
                "changePercent": change_pct,
                "volume": qp.volume,
                "marketCap": 0,
                "addedAt": datetime.now(timezone.utc).isoformat(),
            }
            return normalise_watchlist_item(raw)
        except Exception:
            return normalise_watchlist_item({
                "symbol": sym,
                "name": symbol_to_name.get(sym, sym),
                "price": 0, "change": 0, "changePercent": 0,
                "volume": 0, "marketCap": 0,
                "addedAt": datetime.now(timezone.utc).isoformat(),
            })

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_quote, symbols))

    return results


@router.post("")
async def add_to_watchlist(
    payload: dict = Body(...), db: Session = Depends(database.get_db)
):
    """POST /watchlist { symbol }"""
    raw_symbol = (payload.get("symbol") or "").strip()
    try:
        symbol = sanitise_symbol_param(raw_symbol)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid symbol: '{raw_symbol}'")

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

    # Fetch live price for immediate response
    try:
        from app.api.endpoints.stocks import _build_quote_parts
        qp = _build_quote_parts(symbol)
        change = qp.price - qp.prev_close
        change_pct = (change / qp.prev_close * 100.0) if qp.prev_close else 0.0
        price, change_val, change_pct_val, volume = qp.price, change, change_pct, qp.volume
    except Exception:
        price = change_val = change_pct_val = volume = 0

    return {
        "symbol": symbol,
        "name": stock.name or symbol,
        "price": price,
        "change": change_val,
        "changePercent": change_pct_val,
        "volume": volume,
        "marketCap": 0,
        "addedAt": datetime.now(timezone.utc).isoformat(),
    }


@router.delete("/{symbol}")
async def remove_from_watchlist(symbol: str = Depends(sanitise_symbol_param), db: Session = Depends(database.get_db)):
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
