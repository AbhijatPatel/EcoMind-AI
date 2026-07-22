"""
GET /health

Purpose: application monitoring. Returns 200 with basic status info if the
app is up. Includes a DB round-trip so a load balancer / CloudWatch alarm
can detect "app is running but can't reach Postgres" as unhealthy, not just
"process is alive".
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.session import get_db

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check DB ping failed")
        db_status = "unavailable"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": db_status,
    }
