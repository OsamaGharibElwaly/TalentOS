from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

CONTENT_SECURITY_POLICY = "; ".join(
    (
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: https:",
        "font-src 'self' data:",
        "connect-src 'self'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "object-src 'none'",
    )
)
SENSITIVE_PREFIXES = (
    "/auth",
    "/frontend",
    "/applications",
    "/interviews",
    "/search",
    "/telemetry",
    "/api/v1/telemetry",
)


def install_security_headers(app: FastAPI) -> None:
    @app.middleware("http")
    async def add_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        if request.url.path.startswith(SENSITIVE_PREFIXES):
            response.headers["Cache-Control"] = "no-store"
        return response
