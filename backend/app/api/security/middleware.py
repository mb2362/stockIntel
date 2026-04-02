"""API security layer for StockIntel.

Provides:
  1. RateLimitMiddleware    – sliding-window per-IP rate limiter (in-memory)
  2. SecurityHeadersMiddleware – adds OWASP-recommended response headers
  3. sanitise_symbol_param  – FastAPI dependency that validates symbol path params
  4. get_optional_user      – FastAPI dependency: resolves user from JWT if present
  5. require_auth           – FastAPI dependency: hard-requires a valid JWT

Import and register in main.py::

    from app.api.security.middleware import (
        RateLimitMiddleware,
        SecurityHeadersMiddleware,
        sanitise_symbol_param,
        require_auth,
        get_optional_user,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
"""
from __future__ import annotations

import re
import time
from collections import defaultdict, deque
from typing import Optional

from fastapi import Depends, HTTPException
from starlette.requests import Request
from starlette import status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.api.auth.authhelper import SECRET_KEY, ALGORITHM
from app.database import crud, database, models

import jwt


# ---------------------------------------------------------------------------
# 1. Rate-limit middleware
# ---------------------------------------------------------------------------

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window, per-IP rate limiter.

    Defaults: 60 requests / 60 s.  Health/docs paths are exempt.

    Args:
        app: The ASGI application to wrap.
        requests_per_minute: Maximum requests allowed per IP per 60-second window.
    """

    EXEMPT_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/")

    def __init__(self, app: ASGIApp, requests_per_minute: int = 60) -> None:
        super().__init__(app)
        self.limit = requests_per_minute
        self.window = 60  # seconds
        # ip -> deque of timestamps
        self._windows: dict[str, deque[float]] = defaultdict(deque)

    def _client_ip(self, request: Request) -> str:
        """Prefer X-Forwarded-For (set by reverse proxies) over the raw client host."""
        xff = request.headers.get("X-Forwarded-For")
        if xff:
            return xff.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_exempt(self, path: str) -> bool:
        return any(path == p or path.startswith(p) for p in self.EXEMPT_PREFIXES if p != "/") \
               or path == "/"

    async def dispatch(self, request: Request, call_next):
        if self._is_exempt(request.url.path):
            return await call_next(request)

        ip = self._client_ip(request)
        now = time.monotonic()
        window_start = now - self.window
        q = self._windows[ip]

        # Evict timestamps older than the sliding window
        while q and q[0] < window_start:
            q.popleft()

        if len(q) >= self.limit:
            retry_after = int(self.window - (now - q[0])) + 1
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": (
                        f"Rate limit exceeded: {self.limit} requests per "
                        f"{self.window}s. Retry after {retry_after}s."
                    )
                },
                headers={"Retry-After": str(retry_after)},
            )

        q.append(now)
        response = await call_next(request)
        # Surface remaining quota in response headers
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.limit - len(q)))
        return response


# ---------------------------------------------------------------------------
# 2. Security headers middleware
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attaches OWASP-recommended security headers to every response.

    Headers applied:
    - ``X-Content-Type-Options: nosniff``
    - ``X-Frame-Options: DENY``
    - ``X-XSS-Protection: 1; mode=block``
    - ``Strict-Transport-Security`` (HSTS, 1 year + preload)
    - ``Referrer-Policy: strict-origin-when-cross-origin``
    - ``Content-Security-Policy`` (restrictive API policy; no HTML pages served)
    - ``Permissions-Policy`` (disable unused browser APIs)
    - ``Cache-Control`` for API responses
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        h = response.headers

        h["X-Content-Type-Options"] = "nosniff"
        h["X-Frame-Options"] = "DENY"
        h["X-XSS-Protection"] = "1; mode=block"
        h["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        h["Referrer-Policy"] = "strict-origin-when-cross-origin"
        h["Content-Security-Policy"] = (
            "default-src 'none'; "
            "frame-ancestors 'none';"
        )
        h["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=()"
        )

        # Prevent caching of API responses (data changes frequently)
        if request.url.path.startswith("/api/"):
            h["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            h["Pragma"] = "no-cache"

        return response


# ---------------------------------------------------------------------------
# 3. Symbol sanitiser (FastAPI path-param dependency)
# ---------------------------------------------------------------------------

_SYMBOL_RE = re.compile(r"^[A-Z0-9\^\.\-]{1,20}$")


def sanitise_symbol_param(symbol: str) -> str:
    """FastAPI dependency that validates and normalises a `{symbol}` path parameter.

    Usage::

        @router.get("/{symbol}/quote")
        async def get_quote(symbol: str = Depends(sanitise_symbol_param)):
            ...

    Raises:
        HTTPException 400 if the symbol contains unexpected characters.
    """
    cleaned = symbol.strip().upper()
    # Strip any URL-encoded noise
    cleaned = re.sub(r"[^A-Z0-9\^\.\-]", "", cleaned)
    if not cleaned or not _SYMBOL_RE.match(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid symbol '{symbol}'. Symbols must be 1-20 alphanumeric characters (optionally prefixed with ^ for indices).",
        )
    return cleaned


# ---------------------------------------------------------------------------
# 4. Auth dependencies
# ---------------------------------------------------------------------------

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)
_oauth2_scheme_required = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=True)


def _decode_token(token: str) -> Optional[str]:
    """Decode a JWT and return the username, or None on failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


async def get_optional_user(
    token: Optional[str] = Depends(_oauth2_scheme),
    db: Session = Depends(database.get_db),
) -> Optional[models.User]:
    """FastAPI dependency: resolves the current user from a JWT if present.

    Returns ``None`` (rather than raising) if the token is absent or invalid.
    Use this for endpoints that work both authenticated and anonymously.
    """
    if not token:
        return None
    username = _decode_token(token)
    if not username:
        return None
    return crud.get_user_by_username(db, username)


async def require_auth(
    token: str = Depends(_oauth2_scheme_required),
    db: Session = Depends(database.get_db),
) -> models.User:
    """FastAPI dependency: hard-requires a valid JWT Bearer token.

    Raises ``HTTP 401`` if the token is missing, expired, or invalid.
    Use this for endpoints that must be authenticated.

    Usage::

        @router.get("/protected")
        async def protected_endpoint(user: models.User = Depends(require_auth)):
            return {"hello": user.username}
    """
    _unauth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = _decode_token(token)
    if not username:
        raise _unauth
    user = crud.get_user_by_username(db, username)
    if user is None:
        raise _unauth
    return user
