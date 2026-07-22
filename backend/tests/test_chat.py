"""
Tests for the chat module.

The real Anthropic API is never called in tests — `stream_chat_response`
is monkeypatched with a fake async generator. This tests our own routing,
error-handling, and persistence logic, not Anthropic's service.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("ENVIRONMENT", "development")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.errors import AIProviderError
from app.db.session import AsyncSessionLocal, Base, engine
from app.main import create_app
from app.models import chat_log, user  # noqa: F401
from app.models.chat_log import ChatLog

import app.api.routes.chat as chat_route


@pytest.fixture(autouse=True)
async def _reset_settings_cache():
    yield
    from app.config import get_settings

    get_settings.cache_clear()


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
    await client.post("/auth/register", json={"email": "chatter@example.com", "password": "correcthorse123"})
    login = await client.post("/auth/login", json={"email": "chatter@example.com", "password": "correcthorse123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _fake_stream_ok(messages):
    for chunk in ["Your ", "transportation ", "impact is moderate."]:
        yield chunk


async def _fake_stream_failure(messages):
    yield "Analyzing your lifestyle..."
    raise AIProviderError("The AI service failed to respond. Please try again.")


@pytest.mark.asyncio
async def test_chat_without_api_key_returns_clean_502_not_a_broken_stream(client, auth_headers):
    # No ANTHROPIC_API_KEY is set in the test environment — this must be
    # caught before streaming starts, giving a normal JSON error response.
    response = await client.post("/chat", json={"message": "I use my car 20km daily."}, headers=auth_headers)
    assert response.status_code == 502
    assert "error" in response.json()


@pytest.mark.asyncio
async def test_chat_streams_and_persists_full_exchange(client, auth_headers, monkeypatch):
    monkeypatch.setattr(chat_route, "stream_chat_response", _fake_stream_ok)
    # Bypass the pre-flight key check since we're not hitting the real API.
    from app.config import get_settings

    get_settings().anthropic_api_key = "fake-key-for-test"

    response = await client.post("/chat", json={"message": "I use my car 20km daily."}, headers=auth_headers)
    assert response.status_code == 200
    assert response.text == "Your transportation impact is moderate."

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ChatLog))
        logs = result.scalars().all()
    assert len(logs) == 1
    assert logs[0].user_message == "I use my car 20km daily."
    assert logs[0].ai_response == "Your transportation impact is moderate."


@pytest.mark.asyncio
async def test_chat_mid_stream_failure_is_surfaced_and_still_persisted(client, auth_headers, monkeypatch):
    monkeypatch.setattr(chat_route, "stream_chat_response", _fake_stream_failure)
    from app.config import get_settings

    get_settings().anthropic_api_key = "fake-key-for-test"

    response = await client.post("/chat", json={"message": "Tell me about my footprint"}, headers=auth_headers)
    assert response.status_code == 200  # already committed to 200 once streaming began
    assert "Analyzing your lifestyle..." in response.text
    assert "[Error:" in response.text

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ChatLog))
        logs = result.scalars().all()
    assert len(logs) == 1  # partial response + error text still persisted, not lost


@pytest.mark.asyncio
async def test_chat_requires_auth(client):
    response = await client.post("/chat", json={"message": "hello"})
    assert response.status_code == 401
