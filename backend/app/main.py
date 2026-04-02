"""FastAPI application factory – CORS, security middleware, router registration, OpenAPI."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter

from app.api.endpoints import stocks, watchlist, portfolio, news, authendpoints
from app.api.endpoints.market import router as market_router
from app.database import models, database

# ── Security middleware ────────────────────────────────────────────────────
from app.api.security.middleware import RateLimitMiddleware, SecurityHeadersMiddleware

# ── OpenAPI / Swagger docs ─────────────────────────────────────────────────
from app.api.docs.openapi_config import configure_openapi

# Create all DB tables on startup
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="StockIntel API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware stack (applied in reverse order – last added = outermost) ───
# 1. Security headers on every response
app.add_middleware(SecurityHeadersMiddleware)

# 2. Per-IP sliding-window rate limiter (60 req/min; exempt: /docs /redoc /)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# 3. CORS for local frontend dev (Vite :5173, CRA :3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# ── Routers ────────────────────────────────────────────────────────────────
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(stocks.router,        tags=["stocks"])
api_v1.include_router(market_router,        tags=["market"])
api_v1.include_router(watchlist.router,     tags=["watchlist"])
api_v1.include_router(portfolio.router,     tags=["portfolio"])
api_v1.include_router(news.router,          tags=["news"])
api_v1.include_router(authendpoints.router, prefix="/auth", tags=["auth"])

app.include_router(api_v1)

# ── Enrich OpenAPI / Swagger schema ───────────────────────────────────────
configure_openapi(app)


@app.get("/", tags=["health"])
async def root():
    return {
        "message": "StockIntel API",
        "docs": "/docs",
        "redoc": "/redoc",
        "api": "/api/v1",
    }
