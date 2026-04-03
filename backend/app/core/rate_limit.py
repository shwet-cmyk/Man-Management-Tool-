from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window = timedelta(seconds=window_seconds)
        self.hits: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        key = request.client.host if request.client else "unknown"
        now = datetime.utcnow()
        queue = self.hits[key]

        while queue and now - queue[0] > self.window:
            queue.popleft()

        if len(queue) >= self.limit:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

        queue.append(now)
        return await call_next(request)
