from __future__ import annotations

import argparse
import hashlib
import json
import sys
import warnings
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_ROOT = REPO_ROOT / "portal_bot"
OUTPUT_PATH = REPO_ROOT / "shared" / "contracts" / "admin" / "admin-v2.openapi.json"
ADMIN_PREFIX = "/api/admin/v2"
HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete"})
UNSAFE_METHODS = frozenset({"post", "put", "patch", "delete"})
CSRF_EXEMPT_OPERATIONS = frozenset(
    {
        ("post", f"{ADMIN_PREFIX}/auth/bootstrap"),
        ("post", f"{ADMIN_PREFIX}/auth/oidc/finish"),
    }
)
_BINARY_RESPONSES = {
    f"{ADMIN_PREFIX}/support/tickets/{{ticket_id}}/bundles/{{bundle_ref}}/content": "application/octet-stream",
    f"{ADMIN_PREFIX}/governance/audit/export": "text/csv",
}


class AdminV2OpenApiError(RuntimeError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _component_names(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        reference = value.get("$ref")
        prefix = "#/components/schemas/"
        if isinstance(reference, str) and reference.startswith(prefix):
            yield reference.removeprefix(prefix)
        for nested in value.values():
            yield from _component_names(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _component_names(nested)


def _referenced_schemas(
    paths: dict[str, Any],
    available: dict[str, Any],
) -> dict[str, Any]:
    pending = list(dict.fromkeys(_component_names(paths)))
    selected: dict[str, Any] = {}
    while pending:
        name = pending.pop(0)
        if name in selected:
            continue
        schema = available.get(name)
        if not isinstance(schema, dict):
            raise AdminV2OpenApiError(f"missing_component:{name}")
        selected[name] = schema
        pending.extend(
            nested
            for nested in _component_names(schema)
            if nested not in selected and nested not in pending
        )
    return {name: selected[name] for name in sorted(selected)}


def _permission_key(method: str, full_path: str) -> str:
    relative = full_path.removeprefix(ADMIN_PREFIX) or "/"
    return f"{method.upper()} {relative}"


def _csrf_parameter() -> dict[str, Any]:
    return {
        "description": "Session-bound CSRF proof. Never persist it in browser storage.",
        "in": "header",
        "name": "X-Pokrov-Admin-CSRF",
        "required": True,
        "schema": {"maxLength": 128, "minLength": 32, "type": "string"},
    }


def build_contract() -> dict[str, Any]:
    if str(PORTAL_BOT_ROOT) not in sys.path:
        sys.path.insert(0, str(PORTAL_BOT_ROOT))
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=r"Duplicate Operation ID .*", category=UserWarning)
        from api import app
        from admin_v2.meta import ADMIN_V2_SCHEMA
        from admin_v2.router import ROUTE_PERMISSIONS

        raw = app.openapi()

    raw_paths = raw.get("paths")
    if not isinstance(raw_paths, dict):
        raise AdminV2OpenApiError("openapi_paths_missing")
    paths: dict[str, Any] = {
        path: raw_paths[path]
        for path in sorted(raw_paths)
        if str(path).startswith(ADMIN_PREFIX)
    }
    if not paths:
        raise AdminV2OpenApiError("admin_v2_paths_missing")

    operation_ids: set[str] = set()
    permission_keys: set[str] = set()
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            raise AdminV2OpenApiError(f"invalid_path_item:{path}")
        for method, operation in path_item.items():
            if method not in HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                raise AdminV2OpenApiError(f"invalid_operation:{method}:{path}")
            operation_id = str(operation.get("operationId") or "").strip()
            if not operation_id or operation_id in operation_ids:
                raise AdminV2OpenApiError(f"duplicate_or_missing_operation_id:{operation_id}")
            operation_ids.add(operation_id)
            permission_key = _permission_key(method, path)
            permission = str(ROUTE_PERMISSIONS.get(permission_key) or "").strip()
            if not permission:
                raise AdminV2OpenApiError(f"permission_missing:{permission_key}")
            permission_keys.add(permission_key)
            operation["x-pokrov-permission"] = permission
            csrf_required = method in UNSAFE_METHODS and (method, path) not in CSRF_EXEMPT_OPERATIONS
            operation["x-pokrov-csrf-required"] = csrf_required
            binary_media_type = _BINARY_RESPONSES.get(path)
            if binary_media_type is not None:
                success = operation.setdefault("responses", {}).setdefault("200", {})
                success["content"] = {
                    binary_media_type: {
                        "schema": {"format": "binary", "type": "string"}
                    }
                }
            if path == f"{ADMIN_PREFIX}/auth/bootstrap":
                operation["security"] = [{"adminBootstrapIdentity": []}]
            elif path == f"{ADMIN_PREFIX}/auth/oidc/start":
                operation["security"] = []
            elif path == f"{ADMIN_PREFIX}/auth/oidc/finish":
                operation["security"] = [{"adminOidcTransaction": []}]
            else:
                operation["security"] = [{"adminSessionCookie": []}]
            if csrf_required:
                parameters = operation.setdefault("parameters", [])
                if not isinstance(parameters, list):
                    raise AdminV2OpenApiError(f"parameters_invalid:{operation_id}")
                if not any(
                    isinstance(item, dict)
                    and item.get("in") == "header"
                    and str(item.get("name") or "").lower() == "x-pokrov-admin-csrf"
                    for item in parameters
                ):
                    parameters.append(_csrf_parameter())

    expected_permissions = set(ROUTE_PERMISSIONS)
    if permission_keys != expected_permissions:
        missing = sorted(expected_permissions - permission_keys)
        stale = sorted(permission_keys - expected_permissions)
        raise AdminV2OpenApiError(
            f"permission_matrix_drift:missing={missing}:stale={stale}"
        )

    raw_components = raw.get("components")
    available_schemas = (
        raw_components.get("schemas", {}) if isinstance(raw_components, dict) else {}
    )
    if not isinstance(available_schemas, dict):
        raise AdminV2OpenApiError("openapi_components_invalid")
    schemas = _referenced_schemas(paths, available_schemas)
    contract: dict[str, Any] = {
        "openapi": str(raw.get("openapi") or "3.1.0"),
        "info": {
            "description": (
                "Canonical, cookie-authenticated Operator Center v2 contract. "
                "Legacy /api/admin routes are intentionally excluded."
            ),
            "title": "POKROV Operator API v2",
            "version": ADMIN_V2_SCHEMA,
        },
        "servers": [{"url": "https://api.pokrov.space"}],
        "paths": paths,
        "components": {
            "schemas": schemas,
            "securitySchemes": {
                "adminBootstrapIdentity": {
                    "description": (
                        "Compatibility Telegram Mini App identity. Disable it after "
                        "the measured OIDC cutover."
                    ),
                    "in": "header",
                    "name": "X-Telegram-Init-Data",
                    "type": "apiKey",
                },
                "adminSessionCookie": {
                    "description": "Opaque HttpOnly host-only operator session.",
                    "in": "cookie",
                    "name": "__Host-pokrov_admin_session",
                    "type": "apiKey",
                },
                "adminOidcTransaction": {
                    "description": "Short-lived HttpOnly cookie bound to one purpose-specific OIDC state.",
                    "in": "cookie",
                    "name": "__Host-pokrov_admin_oidc",
                    "type": "apiKey",
                },
            },
        },
        "tags": [{"name": "admin-v2"}],
        "x-pokrov-contract": "pokrov.admin-v2.openapi.v1",
        "x-pokrov-operation-count": len(operation_ids),
        "x-pokrov-permission-matrix-sha256": _digest(
            {key: ROUTE_PERMISSIONS[key] for key in sorted(ROUTE_PERMISSIONS)}
        ),
    }
    contract["x-pokrov-contract-sha256"] = _digest(contract)
    return contract


def render_contract(contract: dict[str, Any]) -> str:
    return json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _write_or_check(expected: str, *, check: bool) -> None:
    if check:
        try:
            actual = OUTPUT_PATH.read_text(encoding="utf-8")
        except OSError as exc:
            raise AdminV2OpenApiError("generated_contract_missing") from exc
        if actual != expected:
            raise AdminV2OpenApiError("generated_contract_stale")
        return
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(expected, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the deterministic, v2-only Operator Center OpenAPI contract."
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        contract = build_contract()
        _write_or_check(render_contract(contract), check=bool(args.check))
    except AdminV2OpenApiError as exc:
        print(f"FAIL admin-v2-openapi {exc}")
        return 1
    print(
        "PASS admin-v2-openapi "
        f"operations={contract['x-pokrov-operation-count']} "
        f"sha256={contract['x-pokrov-contract-sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
