from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "pokrov_operator_copilot.py"
    spec = importlib.util.spec_from_file_location("pokrov_operator_copilot", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_tool_schemas_are_strict_and_read_only_named() -> None:
    module = _load_module()

    schemas = module.tool_schemas()
    names = {schema["name"] for schema in schemas}

    assert "pokrov_list_canon" in names
    assert "pokrov_read_canonical_doc_excerpt" in names
    assert "pokrov_run_public_copy_guardrails" in names
    assert all(schema["strict"] is True for schema in schemas)
    assert all(schema["parameters"]["additionalProperties"] is False for schema in schemas)
    forbidden_words = ("deploy", "grant", "revoke", "refund", "ssh", "write")
    assert not any(word in schema["name"] for schema in schemas for word in forbidden_words)


def test_read_canonical_doc_excerpt_rejects_arbitrary_paths() -> None:
    module = _load_module()

    try:
        module.execute_tool(
            "pokrov_read_canonical_doc_excerpt",
            {"path_key": "../portal_bot/.env", "query": None, "max_chars": 1000},
        )
    except module.ToolExecutionError as exc:
        assert "unsupported canonical doc key" in str(exc)
    else:
        raise AssertionError("expected arbitrary path_key to be rejected")


def test_read_canonical_doc_excerpt_returns_matching_lines() -> None:
    module = _load_module()

    result = module.execute_tool(
        "pokrov_read_canonical_doc_excerpt",
        {"path_key": "product", "query": "outside-store stable-direct", "max_chars": 3000},
    )

    assert result["path"] == "docs/product/portal-vpn-product.md"
    assert "outside-store stable-direct" in result["excerpt"]


def test_origin_handoff_keeps_origin_verdicts_separate() -> None:
    module = _load_module()

    result = module.execute_tool(
        "pokrov_build_origin_status_handoff",
        {
            "current_origin": "PASS",
            "brain_origin": "PASS",
            "ru_origin": "BLOCKED_BY_ACCESS",
            "notes": "mini SSH auth missing",
        },
    )

    handoff = result["handoff"]
    assert "current-origin check: PASS" in handoff
    assert "brain-origin check: PASS" in handoff
    assert "RU-origin check: BLOCKED_BY_ACCESS" in handoff
    assert "mini SSH auth missing" in handoff


def test_payment_email_tool_redacts_secret_env(monkeypatch) -> None:
    module = _load_module()
    monkeypatch.setenv("LAVATOP_API_KEY", "super-secret-api-key")
    monkeypatch.setenv("EMAIL_DELIVERY_WEBHOOK_SECRET", "super-secret-email-secret")

    result = module.execute_tool(
        "pokrov_check_payment_email_readiness",
        {"plan_code": "start_99"},
    )

    serialized = module.json.dumps(result, ensure_ascii=False)
    assert "super-secret" not in serialized
    assert result["classification"] in {"BLOCKED_BY_ACCESS", "EXTERNAL_DEPENDENCY", "PASS"}
