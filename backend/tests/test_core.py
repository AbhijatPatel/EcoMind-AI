"""
Smoke tests for the backend core module (config, db session, app bootstrap).

Uses SQLite via aiosqlite as a stand-in for Postgres so this test suite has
no external dependency — it is only verifying that the core wiring (settings
-> engine -> session -> FastAPI app -> route) works end to end, not that
Postgres-specific SQL behaves correctly.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("ENVIRONMENT", "development")

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.asyncio
async def test_health_check_returns_ok():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["app"] == "EcoMind AI"
    assert body["database"] == "ok"
    assert body["status"] == "ok"


@pytest.mark.asyncio
async def test_settings_are_cached_singleton():
    from app.config import get_settings

    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2  # lru_cache should return the same instance


@pytest.mark.asyncio
async def test_unknown_route_returns_structured_404():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/nonexistent")

    assert response.status_code == 404
    assert "error" in response.json()
