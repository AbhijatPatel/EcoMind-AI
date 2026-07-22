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
    await client.post("/auth/register", json={"email": "planner@example.com", "password": "correcthorse123"})
    login = await client.post("/auth/login", json={"email": "planner@example.com", "password": "correcthorse123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


CARBON_PAYLOAD = {
    "vehicle_type": "petrol_car",
    "distance_km_per_day": 30,
    "diet_type": "non_vegetarian",
    "meat_meals_per_week": 10,
    "electricity_kwh_per_month": 200,
    "ac_hours_per_day": 1,
    "shopping_trips_per_month": 2,
    "recycles": True,
}


@pytest.mark.asyncio
async def test_generate_plan_requires_auth(client):
    response = await client.post("/generate-plan")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_generate_plan_without_prior_assessment_returns_404(client, auth_headers):
    response = await client.post("/generate-plan", headers=auth_headers)
    assert response.status_code == 404
    assert "calculate-carbon" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_generate_plan_after_assessment_targets_weakest_areas(client, auth_headers):
    await client.post("/calculate-carbon", json=CARBON_PAYLOAD, headers=auth_headers)

    response = await client.post("/generate-plan", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()

    # This payload has a heavy petrol commute -> transport should be a weak
    # area and therefore show up in focus_areas.
    assert "Transportation" in body["focus_areas"]
    assert len(body["daily"]) == 2
    assert len(body["weekly"]) == 2
    assert len(body["monthly"]) == 2
    assert body["based_on_category"] in {"Eco Champion", "Green Lifestyle", "Needs Improvement", "High Impact"}


@pytest.mark.asyncio
async def test_generate_plan_uses_most_recent_assessment(client, auth_headers):
    # First assessment: weak transport.
    await client.post("/calculate-carbon", json=CARBON_PAYLOAD, headers=auth_headers)
    # Second, more recent assessment: everything strong except food.
    strong_except_food = {
        "vehicle_type": "bike",
        "distance_km_per_day": 2,
        "diet_type": "non_vegetarian",
        "meat_meals_per_week": 20,
        "electricity_kwh_per_month": 50,
        "ac_hours_per_day": 0,
        "shopping_trips_per_month": 0,
        "recycles": True,
    }
    await client.post("/calculate-carbon", json=strong_except_food, headers=auth_headers)

    response = await client.post("/generate-plan", headers=auth_headers)
    assert response.status_code == 200
    assert "Food" in response.json()["focus_areas"]
