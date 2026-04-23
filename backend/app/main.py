"""FastAPI application factory and CORS/router configuration."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter

from app.api.endpoints import stocks, watchlist, portfolio, news, authendpoints
from app.api.endpoints.market import router as market_router
from app.database import models, database


models.Base.metadata.create_all(bind=database.engine)


app = FastAPI(title="Stock Predictor Backend", version="1.0.0")

# CORS for local frontend dev (Vite defaults to :5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Frontend expects API at /api/v1
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(stocks.router, tags=["stocks"])
api_v1.include_router(market_router, tags=["market"])
api_v1.include_router(watchlist.router, tags=["watchlist"])
api_v1.include_router(portfolio.router, tags=["portfolio"])
api_v1.include_router(news.router, tags=["news"])
api_v1.include_router(authendpoints.router, prefix="/auth", tags=["auth"])

app.include_router(api_v1)


@app.get("/")
async def root():
    return {"message": "Stock Market Backend API", "docs": "/docs", "api": "/api/v1"}
