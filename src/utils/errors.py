from collections.abc import Awaitable, Callable
from typing import Any, NoReturn, TypeVar
from fastapi import HTTPException
from .logging import get_logger

T = TypeVar("T")

logger = get_logger(__name__)


def bad_request(detail: str) -> NoReturn:
    raise HTTPException(status_code=400, detail=detail)


def server_error(detail: str) -> NoReturn:
    raise HTTPException(status_code=500, detail=detail)


async def run_route(operation: str, handler: Callable[[], Awaitable[T]]) -> T:
    try:
        return await handler()
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("%s failed", operation)
        raise HTTPException(
            status_code=500,
            detail=f"{type(exc).__name__}: {exc}",
        ) from exc


def agent_retry_error(
    exc: Exception,
    state: dict[str, Any],
    *,
    error_key: str,
    status_key: str | None = None,
) -> dict[str, Any]:
    logger.exception("Agent node failed: %s", error_key)
    payload: dict[str, Any] = {
        error_key: str(exc),
        "retry_count": state.get("retry_count", 0) + 1,
    }
    if status_key:
        payload[status_key] = False
    return payload
