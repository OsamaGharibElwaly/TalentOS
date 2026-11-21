from __future__ import annotations

import time
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

BUCKETS = (
    ("/frontend/ingest", "upload", 5),
    ("/frontend/scoring", "scoring", 30),
    ("/search/talent", "search", 60),
    ("/frontend/session", "auth", 120),
    ("/frontend/account", "signup", 10),
)
WINDOW_SECONDS = 60.0


@dataclass(slots=True)
class RateLimiter:
    limit: int
    window_seconds: float = WINDOW_SECONDS
    _hits: dict[str, deque[float]] = field(default_factory=dict)

    def check(self, key: str, *, now: float | None = None) -> bool:
        moment = time.monotonic() if now is None else now
        bucket = self._hits.setdefault(key, deque())
        cutoff = moment - self.window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False
        bucket.append(moment)
        return True

    def pending(self, key: str) -> int:
        return len(self._hits.get(key, ()))


def bucket_for(path: str) -> tuple[str, int] | None:
    for prefix, name, limit in BUCKETS:
        if path.startswith(prefix):
            return name, limit
    return None


def install_rate_limiter(app: FastAPI) -> None:
    limiters = {name: RateLimiter(limit) for _, name, limit in BUCKETS}

    @app.middleware("http")
    async def enforce_limit(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        bucket = bucket_for(request.url.path)
        if bucket is not None:
            name, _ = bucket
            identity = request.headers.get("X-User-Id")
            if not identity:
                identity = request.client.host if request.client else "anonymous"
            if not limiters[name].check(f"{name}:{identity}"):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "rate limit exceeded"},
                    headers={"Retry-After": str(int(WINDOW_SECONDS))},
                )
        return await call_next(request)
