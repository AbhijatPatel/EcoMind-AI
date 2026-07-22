"""
Centralized error handling.

Route modules (Phase 3+) should raise these instead of generic HTTPException
subclasses directly, so error shape stays consistent across every endpoint
and internal details never leak into a client-facing message.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


class EcoMindError(Exception):
    """Base class for all application-raised errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(EcoMindError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class AuthError(EcoMindError):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class AIProviderError(EcoMindError):
    """Raised when the upstream LLM call fails or times out."""

    def __init__(self, message: str = "AI service is temporarily unavailable"):
        super().__init__(message, status_code=status.HTTP_502_BAD_GATEWAY)


def _error_body(message: str) -> dict:
    return {"error": {"message": message}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(EcoMindError)
    async def handle_ecomind_error(request: Request, exc: EcoMindError) -> JSONResponse:
        logger.warning("Handled error on %s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(status_code=exc.status_code, content=_error_body(exc.message))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.info("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body("Invalid request data. Please check the submitted fields."),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_error_body(str(exc.detail)))

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Never leak stack traces or exception internals to the client.
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("An unexpected error occurred. Please try again."),
        )
