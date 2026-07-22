"""
Integration tests for /calculate-carbon — exercised through the real
FastAPI app (auth -> route -> engine -> DB persistence), not by calling
the engine function directly.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("ENVIRONMENT", "development")

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import Base, engine
from app.main import create_app
from app.models import assessment, user  # noqa: F401


@pytest.fixture(autouse=True)
async def _setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def auth_headers(client):
    await client.post("/auth/register", json={"email": "green@example.com", "password": "correcthorse123"})
    login = await client.post("/auth/login", json={"email": "green@example.com", "password": "correcthorse123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


GOOD_PAYLOAD = {
    "vehicle_type": "bike",
    "distance_km_per_day": 5,
    "diet_type": "vegetarian",
    "meat_meals_per_week": 0,
    "electricity_kwh_per_month": 150,
    "ac_hours_per_day": 1,
    "shopping_trips_per_month": 2,
    "recycles": True,
}


@pytest.mark.asyncio
async def test_calculate_carbon_works_for_guests_but_is_not_saved(client):
    response = await client.post("/calculate-carbon", json=GOOD_PAYLOAD)
    assert response.status_code == 201
    body = response.json()

    assert body["saved"] is False
    assert body["id"] is None
    assert 0 <= body["overall_score"] <= 100


@pytest.mark.asyncio
async def test_calculate_carbon_rejects_invalid_distance_for_guests_too(client):
    bad_payload = {**GOOD_PAYLOAD, "distance_km_per_day": -5}
    response = await client.post("/calculate-carbon", json=bad_payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_calculate_carbon_returns_persisted_result(client, auth_headers):
    response = await client.post("/calculate-carbon", json=GOOD_PAYLOAD, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()

    assert body["saved"] is True
    assert 0 <= body["overall_score"] <= 100
    assert body["category"] in {"Eco Champion", "Green Lifestyle", "Needs Improvement", "High Impact"}
    assert body["id"] is not None and body["created_at"] is not None


@pytest.mark.asyncio
async def test_calculate_carbon_rejects_invalid_distance(client, auth_headers):
    bad_payload = {**GOOD_PAYLOAD, "distance_km_per_day": -5}
    response = await client.post("/calculate-carbon", json=bad_payload, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_calculate_carbon_rejects_invalid_vehicle_type(client, auth_headers):
    bad_payload = {**GOOD_PAYLOAD, "vehicle_type": "spaceship"}
    response = await client.post("/calculate-carbon", json=bad_payload, headers=auth_headers)
    assert response.status_code == 422
