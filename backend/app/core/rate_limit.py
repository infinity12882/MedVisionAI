"""
Lightweight rate-limiting middleware: a fixed-window counter per client IP,
backed by an in-memory dict. This is intentionally simple — sufficient to
demonstrate and enforce the requirement, and correct for a single-process
deployment. For multi-worker/multi-instance production deployments, swap
the in-memory counter for a Redis INCR+EXPIRE counter (settings.REDIS_URL
is already configured for exactly this).
"""
from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

_window_seconds = 60
_request_log: dict[str, list[float]] = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        timestamps = _request_log[client_ip]
        # Drop timestamps outside the current window.
        cutoff = now - _window_seconds
        idx = 0
        while idx < len(timestamps) and timestamps[idx] < cutoff:
            idx += 1
        if idx > 0:
            timestamps = timestamps[idx:]
            _request_log[client_ip] = timestamps
            
        if not timestamps:
            del _request_log[client_ip]

        if len(timestamps) >= settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down and try again shortly."},
            )

        if not timestamps:
            _request_log[client_ip] = timestamps
        timestamps.append(now)
        return await call_next(request)
