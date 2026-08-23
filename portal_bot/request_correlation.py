"""Typed, privacy-safe request correlation for the platform API."""

from __future__ import annotations

import contextvars
import uuid
from dataclasses import dataclass
from typing import Any


CORRELATION_ID_HEADER = "X-Correlation-ID"
REQUEST_ID_HEADER = "X-Request-ID"


@dataclass(frozen=True, slots=True)
class RequestCorrelation:
    correlation_id: str
    request_id: str


_current_request_correlation: contextvars.ContextVar[RequestCorrelation | None] = (
    contextvars.ContextVar("pokrov_request_correlation", default=None)
)


def _new_id() -> str:
    return str(uuid.uuid4())


def normalize_correlation_id(value: str | None) -> str | None:
    """Accept only canonical lowercase UUIDs; never reflect arbitrary input."""

    candidate = str(value or "").strip()
    if not candidate or len(candidate) != 36 or candidate != candidate.lower():
        return None
    try:
        parsed = uuid.UUID(candidate)
    except (ValueError, AttributeError):
        return None
    if parsed.variant != uuid.RFC_4122 or parsed.version != 4:
        return None
    return candidate if str(parsed) == candidate else None


def build_request_correlation(client_correlation_id: str | None) -> RequestCorrelation:
    return RequestCorrelation(
        correlation_id=normalize_correlation_id(client_correlation_id) or _new_id(),
        request_id=_new_id(),
    )


def bind_request_correlation(
    context: RequestCorrelation,
) -> contextvars.Token[RequestCorrelation | None]:
    return _current_request_correlation.set(context)


def reset_request_correlation(
    token: contextvars.Token[RequestCorrelation | None],
) -> None:
    _current_request_correlation.reset(token)


def current_request_correlation() -> RequestCorrelation | None:
    return _current_request_correlation.get()


def request_correlation_from_request(request: Any) -> RequestCorrelation:
    state = getattr(request, "state", None)
    context = getattr(state, "request_correlation", None)
    if isinstance(context, RequestCorrelation):
        return context
    current = current_request_correlation()
    if current is not None:
        return current
    return build_request_correlation(None)


def response_headers(context: RequestCorrelation) -> dict[str, str]:
    return {
        CORRELATION_ID_HEADER: context.correlation_id,
        REQUEST_ID_HEADER: context.request_id,
    }
