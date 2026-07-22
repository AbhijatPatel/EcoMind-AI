"""
Application bootstrap.

This is intentionally the only file that assembles cross-cutting concerns
(logging, CORS, error handlers, routers). Route modules should never
configure middleware themselves — it belongs here so there's exactly one
place to see everything that runs on every request.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, carbon, challenge, chat, dashboard, health, plan
from app.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.db.session import Base, engine

# Importing the model modules registers their tables on Base.metadata —
# required for the auto-create-tables startup step below to know about all
# four tables, not just whichever route happened to import first.
from app.models import assessment, challenge as challenge_model, chat_log, user  # noqa: F401

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # Fail fast rather than serve traffic with an insecure default secret.
    if settings.is_production and settings.jwt_secret == "CHANGE_ME_IN_PRODUCTION":
        raise RuntimeError(
            "Refusing to start: JWT_SECRET is still the default placeholder in a "
            "production environment. Set a real secret via environment variables."
        )

    if settings.auto_create_tables:
        # Dev/Docker Compose convenience so `docker compose up` works against
        # a fresh Postgres instance without a separate migration step. This
        # is NOT a substitute for real schema migrations — create_all only
        # adds missing tables, it never alters existing ones. A production
        # deployment with an evolving schema should use Alembic instead and
        # set AUTO_CREATE_TABLES=false.
        logger.info("Auto-creating database tables (AUTO_CREATE_TABLES=true)")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    logger.info("Starting %s in %s mode", settings.app_name, settings.environment)
    yield
    logger.info("Shutting down %s", settings.app_name)
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(carbon.router)
    app.include_router(chat.router)
    app.include_router(plan.router)
    app.include_router(challenge.router)
    app.include_router(dashboard.router)

    return app


app = create_app()
