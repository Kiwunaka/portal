"""OpenAPI-visible response contracts for the canonical Operator Center API."""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field


class AdminV2MetaContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: str = Field(min_length=20, max_length=40)
    trace_id: str | None = Field(default=None, max_length=128)
    schema_version: str = Field(pattern=r"^admin-v2\.[0-9]+$")
    query_ms: int = Field(ge=0)


class AdminV2SuccessEnvelopeContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: Any
    meta: AdminV2MetaContract
    sources: list[dict[str, Any]]
    warnings: list[dict[str, Any]]


class AdminV2ErrorContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=96)
    message: str = Field(min_length=1, max_length=240)


class AdminV2ErrorEnvelopeContract(AdminV2SuccessEnvelopeContract):
    data: None = None
    error: AdminV2ErrorContract


def admin_v2_operation_id(route: APIRoute) -> str:
    methods = sorted(str(method).lower() for method in route.methods if method != "HEAD")
    if len(methods) != 1:
        raise RuntimeError(f"Admin API v2 route must have exactly one method: {route.path}")
    relative = str(route.path_format).removeprefix("/api/admin/v2").strip("/")
    parts: list[str] = []
    for segment in relative.split("/") if relative else ["root"]:
        parameter = re.fullmatch(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", segment)
        if parameter is not None:
            parts.extend(("by", parameter.group(1).lower()))
            continue
        normalized = re.sub(r"[^a-z0-9]+", "_", segment.lower()).strip("_")
        if not normalized:
            raise RuntimeError(f"Admin API v2 route has invalid path: {route.path}")
        parts.append(normalized)
    return "admin_v2_" + methods[0] + "_" + "_".join(parts)


class AdminV2ContractRouter(APIRouter):
    """Apply one validated success envelope to every JSON v2 endpoint."""

    def get(self, path: str, **kwargs):
        kwargs.setdefault("response_model", AdminV2SuccessEnvelopeContract)
        return super().get(path, **kwargs)

    def post(self, path: str, **kwargs):
        kwargs.setdefault("response_model", AdminV2SuccessEnvelopeContract)
        return super().post(path, **kwargs)


COMMON_ERROR_RESPONSES = {
    status: {"model": AdminV2ErrorEnvelopeContract}
    for status in (400, 401, 403, 404, 409, 410, 422, 428, 503)
}


__all__ = [
    "AdminV2ContractRouter",
    "AdminV2ErrorEnvelopeContract",
    "AdminV2SuccessEnvelopeContract",
    "COMMON_ERROR_RESPONSES",
    "admin_v2_operation_id",
]
