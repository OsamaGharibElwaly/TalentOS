from fastapi import FastAPI

from app.api.routes_applications import router as applications_router
from app.api.routes_interviews import router as interviews_router
from app.api.routes_frontend import router as frontend_router
from app.api.routes_jobs import router as jobs_router
from app.api.routes_search import router as search_router
from app.api.routes_telemetry import router as telemetry_router
from app.middleware.rate_limiter import install_rate_limiter
from app.middleware.security_headers import install_security_headers


def create_app() -> FastAPI:
    app = FastAPI(title="TalentOS", version="0.1.0")
    app.include_router(jobs_router)
    app.include_router(frontend_router)
    app.include_router(applications_router)
    app.include_router(interviews_router)
    app.include_router(search_router)
    app.include_router(telemetry_router)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    install_rate_limiter(app)
    install_security_headers(app)
    return app


app = create_app()
