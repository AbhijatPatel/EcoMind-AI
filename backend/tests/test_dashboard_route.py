import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("ENVIRONMENT", "development")

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import Base, engine
from app.main import create_app
from app.models import assessment, challenge, user  # noqa: F401


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
    await client.post("/auth/register", json={"email": "dash@example.com", "password": "correcthorse123"})
    login = await client.post("/auth/login", json={"email": "dash@example.com", "password": "correcthorse123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


CARBON_PAYLOAD = {
    "vehicle_type": "petrol_car",
    "distance_km_per_day": 20,
    "diet_type": "flexitarian",
    "meat_meals_per_week": 5,
    "electricity_kwh_per_month": 200,
    "ac_hours_per_day": 1,
    "shopping_trips_per_month": 2,
    "recycles": True,
}


@pytest.mark.asyncio
async def test_dashboard_requires_auth(client):
    response = await client.get("/dashboard")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_empty_state_for_new_user(client, auth_headers):
    response = await client.get("/dashboard", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["latest"] is None
    assert body["history"] == []
    assert body["challenges"] == []


@pytest.mark.asyncio
async def test_dashboard_reflects_latest_assessment(client, auth_headers):
    await client.post("/calculate-carbon", json=CARBON_PAYLOAD, headers=auth_headers)

    response = await client.get("/dashboard", headers=auth_headers)
    body = response.json()

    assert body["latest"] is not None
    assert 0 <= body["latest"]["overall_score"] <= 100
    assert len(body["history"]) == 1


@pytest.mark.asyncio
async def test_dashboard_history_is_oldest_first_and_uses_most_recent_as_latest(client, auth_headers):
    weak = {**CARBON_PAYLOAD, "distance_km_per_day": 80, "vehicle_type": "diesel_car"}
    strong = {**CARBON_PAYLOAD, "distance_km_per_day": 0, "vehicle_type": "bike"}

    await client.post("/calculate-carbon", json=weak, headers=auth_headers)
    await client.post("/calculate-carbon", json=strong, headers=auth_headers)

    response = await client.get("/dashboard", headers=auth_headers)
    body = response.json()

    assert len(body["history"]) == 2
    # oldest (weak) first, newest (strong) last
    assert body["history"][0]["score"] < body["history"][1]["score"]
    # "latest" reflects the most recent, i.e. the strong one
    assert body["latest"]["overall_score"] == body["history"][-1]["score"]


@pytest.mark.asyncio
async def test_dashboard_includes_recent_challenges(client, auth_headers):
    await client.post("/challenge", json={"category": "food"}, headers=auth_headers)
    await client.post("/challenge", json={"category": "energy"}, headers=auth_headers)

    response = await client.get("/dashboard", headers=auth_headers)
    body = response.json()

    assert len(body["challenges"]) == 2
    categories = {c["category"] for c in body["challenges"]}
    assert categories == {"food", "energy"}


@pytest.mark.asyncio
async def test_dashboard_only_shows_own_data(client, auth_headers):
    await client.post("/calculate-carbon", json=CARBON_PAYLOAD, headers=auth_headers)

    await client.post("/auth/register", json={"email": "other@example.com", "password": "correcthorse123"})
    other_login = await client.post("/auth/login", json={"email": "other@example.com", "password": "correcthorse123"})
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    response = await client.get("/dashboard", headers=other_headers)
    body = response.json()
    assert body["latest"] is None
    assert body["history"] == []
