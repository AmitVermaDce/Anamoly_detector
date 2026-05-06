from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.config_service import ConfigService
from app.core.exceptions import ApplicationException
from app.core.logger import get_application_logger
from app.db.credential_manager import CredentialManager
from app.db.snowflake_client import SnowflakeClient
from app.services.data_service import DataService

config_service: ConfigService | None = None
credential_manager: CredentialManager | None = None
snowflake_client: SnowflakeClient | None = None


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    get_application_logger()

    global config_service, credential_manager, snowflake_client

    config_service = ConfigService()
    levels = config_service.detection_levels()
    if levels:
        get_application_logger().info("Loaded {count} detection levels", count=len(levels))

    try:
        credential_manager = CredentialManager()
        _ = credential_manager.config
        snowflake_client = SnowflakeClient(credential_manager=credential_manager)
    except Exception as exc:
        import logging as std_logging
        std_logging.warning("Azure Key Vault not available (%s). Falling back to .env.", exc)
        snowflake_client = SnowflakeClient(settings=settings)

    yield

    if snowflake_client is not None:
        snowflake_client.disconnect()


def create_application() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Anomaly Detection API with Snowflake integration.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    @app.exception_handler(ApplicationException)
    async def app_exc_handler(request: Request, exc: ApplicationException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(Exception)
    async def generic_exc_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Internal server error: {exc}"},
        )

    app.include_router(v1_router)
    _mount_frontend(app)
    return app


def _resolve_frontend_dist() -> Path | None:
    import os

    env_path = os.environ.get("FRONTEND_DIST_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    current_file = Path(__file__).resolve()
    candidates = [
        current_file.parent.parent.parent / "frontend" / "dist",
        Path.cwd().parent / "frontend" / "dist",
        Path.cwd() / "frontend" / "dist",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _mount_frontend(app: FastAPI) -> None:
    frontend_dist = _resolve_frontend_dist()
    if not frontend_dist:
        return

    index_file = frontend_dist / "index.html"
    assets_dir = frontend_dist / "assets"

    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    app.mount("/static", StaticFiles(directory=str(frontend_dist)), name="static")

    @app.get("/{catchall:path}")
    async def serve_spa(catchall: str) -> FileResponse:
        if catchall.startswith(("api/", "docs", "redoc", "openapi")):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        return FileResponse(str(index_file))


def get_snowflake_client() -> SnowflakeClient:
    if snowflake_client is None:
        raise RuntimeError("SnowflakeClient has not been initialized.")
    return snowflake_client


def get_config_service() -> ConfigService:
    if config_service is None:
        return ConfigService()
    return config_service


def get_data_service() -> DataService:
    return DataService(snowflake_client=get_snowflake_client(), config_service=get_config_service())


app = create_application()
