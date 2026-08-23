"""Bounded build and schema identity for the Operator Center BFF."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any


ADMIN_V2_SCHEMA = "admin-v2.1"
ADMIN_V2_APP = "pokrov-operator-api"


def _optional_env(name: str) -> str | None:
    value = str(os.getenv(name) or "").strip()
    return value or None


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_admin_v2_meta_response(*, trace_id: str | None = None) -> dict[str, Any]:
    """Return only bounded deployment identity; missing evidence stays missing."""

    generated_at = _iso_now()
    portal_commit = _optional_env("PORTAL_BUILD_COMMIT") or _optional_env("GIT_COMMIT")
    deployed_at = _optional_env("PORTAL_DEPLOYED_AT")
    db_schema = _optional_env("PORTAL_DB_SCHEMA")
    active_client_release = _optional_env("ACTIVE_CLIENT_RELEASE")
    core_release = _optional_env("ACTIVE_CORE_RELEASE")
    warnings: list[dict[str, str]] = []
    for field_name, value in (
        ("portal_commit", portal_commit),
        ("deployed_at", deployed_at),
        ("db_schema", db_schema),
        ("active_client_release", active_client_release),
        ("core_release", core_release),
    ):
        if value is None:
            warnings.append({"code": "deployment_identity_missing", "field": field_name})

    return {
        "data": {
            "app": ADMIN_V2_APP,
            "api_schema": ADMIN_V2_SCHEMA,
            "portal_commit": portal_commit,
            "deployed_at": deployed_at,
            "db_schema": db_schema,
            "active_client_release": active_client_release,
            "core_release": core_release,
            "expected_frontend_app": "pokrov-operator-center",
        },
        "meta": {
            "generated_at": generated_at,
            "trace_id": str(trace_id or "").strip() or None,
            "schema_version": ADMIN_V2_SCHEMA,
            "query_ms": 0,
        },
        "sources": [],
        "warnings": warnings,
    }
