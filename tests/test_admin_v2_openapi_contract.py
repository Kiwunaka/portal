from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "shared" / "contracts" / "admin" / "admin-v2.openapi.json"
GENERATOR_PATH = ROOT / "scripts" / "generate_admin_v2_openapi.py"
SDK_PATH = ROOT / "adminapp" / "src" / "lib" / "admin-api" / "generated" / "admin-v2.ts"


def _load_generator():
    spec = importlib.util.spec_from_file_location("admin_v2_openapi_generator", GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _contract() -> dict[str, Any]:
    value = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _operations(contract: dict[str, Any]) -> Iterator[tuple[str, str, dict[str, Any]]]:
    for path, item in contract["paths"].items():
        for method, operation in item.items():
            if method in {"get", "post", "put", "patch", "delete"}:
                yield path, method, operation


def _numbers(value: Any, key: str) -> list[float]:
    found: list[float] = []
    if isinstance(value, dict):
        candidate = value.get(key)
        if isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
            found.append(float(candidate))
        for nested in value.values():
            found.extend(_numbers(nested, key))
    elif isinstance(value, list):
        for nested in value:
            found.extend(_numbers(nested, key))
    return found


def test_checked_in_admin_v2_openapi_is_exact_generated_contract() -> None:
    generator = _load_generator()
    contract = _contract()

    assert contract == generator.build_contract()
    assert CONTRACT_PATH.read_text(encoding="utf-8") == generator.render_contract(contract)
    assert contract["x-pokrov-contract"] == "pokrov.admin-v2.openapi.v1"
    assert re.fullmatch(r"[0-9a-f]{64}", contract["x-pokrov-contract-sha256"])


def test_all_v2_operations_are_unique_permissioned_bounded_and_typed() -> None:
    contract = _contract()
    operations = list(_operations(contract))
    ids = [operation["operationId"] for _path, _method, operation in operations]

    assert len(operations) == contract["x-pokrov-operation-count"] == 75
    assert len(set(ids)) == len(ids)
    assert all(re.fullmatch(r"admin_v2_(get|post|put|patch|delete)_[a-z0-9_]+", value) for value in ids)

    binary = 0
    json_envelopes = 0
    for path, method, operation in operations:
        assert path.startswith("/api/admin/v2/")
        assert re.fullmatch(r"[a-z][a-z0-9_.-]+", operation["x-pokrov-permission"])
        expected_security = [{"adminSessionCookie": []}]
        if path == "/api/admin/v2/auth/bootstrap":
            expected_security = [{"adminBootstrapIdentity": []}]
        elif path == "/api/admin/v2/auth/oidc/start":
            expected_security = []
        elif path == "/api/admin/v2/auth/oidc/finish":
            expected_security = [{"adminOidcTransaction": []}]
        assert operation["security"] == expected_security
        parameters = operation.get("parameters", [])
        csrf = [
            item
            for item in parameters
            if item.get("in") == "header" and item.get("name") == "X-Pokrov-Admin-CSRF"
        ]
        csrf_exempt = path in {
            "/api/admin/v2/auth/bootstrap",
            "/api/admin/v2/auth/oidc/finish",
        }
        assert bool(csrf) is (method in {"post", "put", "patch", "delete"} and not csrf_exempt)

        content = operation["responses"]["200"]["content"]
        if "application/json" in content:
            json_envelopes += 1
            assert content["application/json"]["schema"] == {
                "$ref": "#/components/schemas/AdminV2SuccessEnvelopeContract"
            }
        else:
            binary += 1
            assert set(content) in ({"application/octet-stream"}, {"text/csv"})

        for parameter in parameters:
            if parameter.get("in") != "query":
                continue
            name = str(parameter.get("name") or "")
            schema = parameter.get("schema", {})
            if name == "limit":
                assert _numbers(schema, "minimum") and min(_numbers(schema, "minimum")) >= 1
                assert _numbers(schema, "maximum") and max(_numbers(schema, "maximum")) <= 1000
            if name == "offset":
                assert _numbers(schema, "minimum") == [0.0]
                assert _numbers(schema, "maximum") == [100_000.0]

    assert json_envelopes == 73
    assert binary == 2


def test_generated_typescript_sdk_is_bound_at_the_runtime_boundary() -> None:
    contract = _contract()
    sdk = SDK_PATH.read_text(encoding="utf-8")
    client = (ROOT / "adminapp/src/lib/admin-api/client.ts").read_text(encoding="utf-8")

    assert f'ADMIN_V2_OPENAPI_SHA256 = "{contract["x-pokrov-contract-sha256"]}"' in sdk
    assert "ADMIN_V2_OPERATION_COUNT = 75" in sdk
    assert sdk.count("csrfRequired:") == 75
    assert "buildAdminV2Request" in sdk
    assert "matchAdminV2Operation" in sdk
    assert 'import { matchAdminV2Operation } from "./generated/admin-v2";' in client
    assert "assertGeneratedAdminV2Route(path, method);" in client
    assert "assertAdminV2Envelope(path, payload);" in client
    assert "admin_v2_contract_mismatch" in client
    assert "admin_v2_envelope_invalid" in client
