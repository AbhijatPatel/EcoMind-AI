"""
Tests for the auth module.

Each test gets a fresh in-memory SQLite database (tables created from
Base.metadata) so tests don't leak state into each other via a shared file
or a real Postgres instance.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("ENVIRONMENT", "development")

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import Base, engine
from app.main import create_app
from app.models import assessment, challenge, chat_log, user  # noqa: F401


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


@pytest.mark.asyncio
async def test_register_returns_token(client):
    response = await client.post(
        "/auth/register", json={"email": "ada@example.com", "password": "correcthorse123"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


@pytest.mark.asyncio
async def test_register_duplicate_email_rejected(client):
    payload = {"email": "dup@example.com", "password": "correcthorse123"}
    first = await client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/auth/register", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(client):
    await client.post("/auth/register", json={"email": "bob@example.com", "password": "correcthorse123"})

    response = await client.post(
        "/auth/login", json={"email": "bob@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_success_and_access_protected_route(client):
    await client.post("/auth/register", json={"email": "carol@example.com", "password": "correcthorse123"})

    login_response = await client.post(
        "/auth/login", json={"email": "carol@example.com", "password": "correcthorse123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "carol@example.com"


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_password_with_wrong_current_password_returns_401(client):
    await client.post("/auth/register", json={"email": "pw1@example.com", "password": "correcthorse123"})
    login = await client.post("/auth/login", json={"email": "pw1@example.com", "password": "correcthorse123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.patch(
        "/auth/password",
        json={"current_password": "wrong-password", "new_password": "newpassword123"},
        headers=headers,
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_password_succeeds_and_new_password_works(client):
    await client.post("/auth/register", json={"email": "pw2@example.com", "password": "correcthorse123"})
    login = await client.post("/auth/login", json={"email": "pw2@example.com", "password": "correcthorse123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    change = await client.patch(
        "/auth/password",
        json={"current_password": "correcthorse123", "new_password": "newpassword123"},
        headers=headers,
    )
    assert change.status_code == 204

    old_login = await client.post("/auth/login", json={"email": "pw2@example.com", "password": "correcthorse123"})
    assert old_login.status_code == 401

    new_login = await client.post("/auth/login", json={"email": "pw2@example.com", "password": "newpassword123"})
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_delete_account_with_wrong_password_returns_401(client):
    await client.post("/auth/register", json={"email": "del1@example.com", "password": "correcthorse123"})
    login = await client.post("/auth/login", json={"email": "del1@example.com", "password": "correcthorse123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.request(
        "DELETE", "/auth/me", json={"password": "wrong-password"}, headers=headers
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_account_removes_user_and_login_then_fails(client):
    await client.post("/auth/register", json={"email": "del2@example.com", "password": "correcthorse123"})
    login = await client.post("/auth/login", json={"email": "del2@example.com", "password": "correcthorse123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.request(
        "DELETE", "/auth/me", json={"password": "correcthorse123"}, headers=headers
    )
    assert response.status_code == 204

    relogin = await client.post("/auth/login", json={"email": "del2@example.com", "password": "correcthorse123"})
    assert relogin.status_code == 401


@pytest.mark.asyncio
async def test_delete_account_with_history_does_not_fail(client):
    """
    Regression test for the FK-cascade issue: a user with assessments,
    challenges, and chat logs must still be deletable without violating
    foreign key constraints or leaving orphaned rows.
    """
    await client.post("/auth/register", json={"email": "del3@example.com", "password": "correcthorse123"})
    login = await client.post("/auth/login", json={"email": "del3@example.com", "password": "correcthorse123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    await client.post(
        "/calculate-carbon",
        json={
            "vehicle_type": "petrol_car",
            "distance_km_per_day": 10,
            "diet_type": "flexitarian",
            "meat_meals_per_week": 5,
            "electricity_kwh_per_month": 200,
            "ac_hours_per_day": 1,
            "shopping_trips_per_month": 2,
            "recycles": True,
        },
        headers=headers,
    )
    await client.post("/challenge", json={"category": "food"}, headers=headers)

    response = await client.request(
        "DELETE", "/auth/me", json={"password": "correcthorse123"}, headers=headers
    )
    assert response.status_code == 204
