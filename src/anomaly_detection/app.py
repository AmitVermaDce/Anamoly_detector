from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from loguru import logger

from anomaly_detection.api.router import router as v1_router
from anomaly_detection.config import get_settings, Config
from anomaly_detection.database.credentials import CredentialManager
from anomaly_detection.database.queries import SQLQueryLoader
from anomaly_detection.database.snowflake import SnowflakeClient
from anomaly_detection.exceptions import ApplicationException
from anomaly_detection.logger import configure_logging
from anomaly_detection import state


_templates_dir = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    configure_logging()

    state.config = Config()
    levels = state.config.detection_levels()
    if levels:
        logger.info("Loaded {count} detection levels", count=len(levels))

    package_root = Path(__file__).resolve().parent.parent
    queries_dir = state.config.queries_dir() or "queries"
    query_file = state.config.query_file() or "filename.sql"
    state.query_loader = SQLQueryLoader(package_root / queries_dir / query_file)

    try:
        state.credential_manager = CredentialManager()
        _ = state.credential_manager.config
        state.snowflake_client = SnowflakeClient(credential_manager=state.credential_manager)
        # Eagerly test the connection so Key Vault credential failures surface here
        state.snowflake_client.get_active_connection()
    except Exception as exc:
        logger.warning("Azure Key Vault not available ({error}). Falling back to .env.", error=exc)
        state.snowflake_client = SnowflakeClient(settings=settings)

    yield

    if state.snowflake_client is not None:
        state.snowflake_client.disconnect()


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

    @app.get("/")
    async def serve_dashboard(request: Request):
        return templates.TemplateResponse(request, "index.html", {})

    return app


app = create_application()
