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
    await client.post("/auth/register", json={"email": "challenger@example.com", "password": "correcthorse123"})
    login = await client.post("/auth/login", json={"email": "challenger@example.com", "password": "correcthorse123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_challenge_requires_auth(client):
    response = await client.post("/challenge", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_challenge_without_assessment_uses_default_category(client, auth_headers):
    response = await client.post("/challenge", json={}, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "lifestyle"
    assert body["title"]
    assert body["duration_days"] == 7


@pytest.mark.asyncio
async def test_challenge_targets_weakest_category_after_assessment(client, auth_headers):
    heavy_transport_impact = {
        "vehicle_type": "diesel_car",
        "distance_km_per_day": 60,
        "diet_type": "vegan",
        "meat_meals_per_week": 0,
        "electricity_kwh_per_month": 50,
        "ac_hours_per_day": 0,
        "shopping_trips_per_month": 0,
        "recycles": True,
    }
    await client.post("/calculate-carbon", json=heavy_transport_impact, headers=auth_headers)

    response = await client.post("/challenge", json={}, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["category"] == "transport"


@pytest.mark.asyncio
async def test_explicit_category_overrides_inference(client, auth_headers):
    response = await client.post("/challenge", json={"category": "energy"}, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["category"] == "energy"


@pytest.mark.asyncio
async def test_invalid_category_returns_422(client, auth_headers):
    response = await client.post("/challenge", json={"category": "spaceship"}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_repeated_challenges_in_same_category_rotate(client, auth_headers):
    first = await client.post("/challenge", json={"category": "food"}, headers=auth_headers)
    second = await client.post("/challenge", json={"category": "food"}, headers=auth_headers)
    third = await client.post("/challenge", json={"category": "food"}, headers=auth_headers)

    titles = [first.json()["title"], second.json()["title"], third.json()["title"]]
    assert titles[0] != titles[1]
    assert titles[0] == titles[2]  # pool of 2 wraps back around


@pytest.mark.asyncio
async def test_list_challenges_requires_auth(client):
    response = await client.get("/challenges")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_challenges_returns_own_challenges_newest_first(client, auth_headers):
    await client.post("/challenge", json={"category": "transport"}, headers=auth_headers)
    await client.post("/challenge", json={"category": "food"}, headers=auth_headers)

    response = await client.get("/challenges", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["category"] == "food"  # most recently created first
    assert body[1]["category"] == "transport"


@pytest.mark.asyncio
async def test_list_challenges_excludes_other_users(client, auth_headers):
    await client.post("/challenge", json={"category": "energy"}, headers=auth_headers)

    await client.post("/auth/register", json={"email": "other2@example.com", "password": "correcthorse123"})
    other_login = await client.post("/auth/login", json={"email": "other2@example.com", "password": "correcthorse123"})
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    response = await client.get("/challenges", headers=other_headers)
    assert response.json() == []


@pytest.mark.asyncio
async def test_complete_challenge_marks_it_done(client, auth_headers):
    created = await client.post("/challenge", json={"category": "lifestyle"}, headers=auth_headers)
    challenge_id = created.json()["id"]
    assert created.json()["completed"] is False

    response = await client.patch(f"/challenges/{challenge_id}/complete", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["completed"] is True

    listed = await client.get("/challenges", headers=auth_headers)
    assert listed.json()[0]["completed"] is True


@pytest.mark.asyncio
async def test_complete_nonexistent_challenge_returns_404(client, auth_headers):
    response = await client.patch("/challenges/does-not-exist/complete", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_complete_another_users_challenge(client, auth_headers):
    created = await client.post("/challenge", json={"category": "food"}, headers=auth_headers)
    challenge_id = created.json()["id"]

    await client.post("/auth/register", json={"email": "attacker@example.com", "password": "correcthorse123"})
    attacker_login = await client.post("/auth/login", json={"email": "attacker@example.com", "password": "correcthorse123"})
    attacker_headers = {"Authorization": f"Bearer {attacker_login.json()['access_token']}"}

    response = await client.patch(f"/challenges/{challenge_id}/complete", headers=attacker_headers)
    assert response.status_code == 404  # not 403 — doesn't reveal the challenge exists
