"""
POST /chat

Purpose: send user sustainability questions to the AI, streamed in
real time.

Two things this route deliberately gets right, both flagged as risks
before this module was built:

1. Configuration is checked BEFORE the StreamingResponse starts. Once the
   first byte of a streaming response is sent, the HTTP status code is
   locked in — so a missing API key must be caught synchronously up front
   (clean 502 JSON) rather than discovered lazily inside the generator
   (which would silently return 200 with a broken stream).
2. The chat log is persisted using a *fresh* session opened inside the
   generator's `finally` block, not the request-scoped `Depends(get_db)`
   session. FastAPI closes generator-based dependencies right after the
   route function returns — which, for a StreamingResponse, happens
   before the client has actually received any streamed bytes. Writing to
   the original request-scoped session here would use an already-closed
   connection.
"""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.ai.client import stream_chat_response
from app.ai.prompts import build_messages
from app.api.deps import get_current_user
from app.config import get_settings
from app.core.errors import AIProviderError
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.chat_log import ChatLog
from app.models.user import User
from app.schemas.chat import ChatRequest

router = APIRouter(tags=["chat"])
logger = get_logger(__name__)


@router.post("/chat")
async def chat(payload: ChatRequest, current_user: User = Depends(get_current_user)) -> StreamingResponse:
    settings = get_settings()
    if not settings.anthropic_api_key:
        # Raised here (pre-stream) so it becomes a normal 502 JSON error,
        # not a broken 200 stream.
        raise AIProviderError("AI chat is not configured yet — ANTHROPIC_API_KEY is missing on the server.")

    messages = build_messages(payload.message)

    async def event_stream() -> AsyncGenerator[str, None]:
        chunks: list[str] = []
        try:
            async for chunk in stream_chat_response(messages):
                chunks.append(chunk)
                yield chunk
        except AIProviderError as exc:
            # The 200 response has already started streaming by this point,
            # so we can't change the status code — surface the failure as
            # visible text and make sure it's logged server-side too.
            logger.error("AI stream failed mid-response for user %s: %s", current_user.id, exc.message)
            error_text = f"\n\n[Error: {exc.message}]"
            chunks.append(error_text)
            yield error_text
        finally:
            full_response = "".join(chunks)
            if full_response.strip():
                async with AsyncSessionLocal() as session:
                    session.add(
                        ChatLog(
                            user_id=current_user.id,
                            user_message=payload.message,
                            ai_response=full_response,
                        )
                    )
                    await session.commit()

    return StreamingResponse(event_stream(), media_type="text/plain; charset=utf-8")
