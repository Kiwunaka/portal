from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "remote_bind_owned_awg_lab_device.py"


def _remote_helper() -> str:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_REMOTE_HELPER":
                    value = ast.literal_eval(node.value)
                    assert isinstance(value, str)
                    return value
    raise AssertionError("remote helper not found")


def test_default_profile_is_supported_without_reprovisioning_material() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    helper = _remote_helper()

    assert 'choices=("default", "awg2_lab", "awg31_lab")' in source
    assert 'if selected_profile != "default":\n        awg2_endpoint' in helper
    assert 'if selected_profile != "default" and not source_material_available:' in helper
    assert '"awg2_material_provisioned": selected_profile != "default"' in helper


def test_default_profile_removes_only_the_resolved_device_from_lab_scope() -> None:
    helper = _remote_helper()

    assert 'if selected_profile == "default":' in helper
    assert 'cohorts.pop("candidate4-awg-lab", None)' in helper
    assert 'if value != install_id' in helper
    assert 'if int(value) != tg_id' in helper
    assert 'not cohort_identity_present' in helper
    assert 'not lab_allowlist_identity_present' in helper
    assert 'resolved_profile not in {"awg2_lab", "awg31_lab"}' in helper


def test_plan_exposes_only_sanitized_device_recency() -> None:
    helper = _remote_helper()

    assert '"last_seen_age_seconds"' in helper
    assert "now - device.last_seen_at" in helper
    assert '"device_os_version_sha256"' in helper
    assert '"device_locale_sha256"' in helper
    assert '"device_time_zone_sha256"' in helper
    assert '"raw_identifiers_returned": False' in helper


def test_apply_readback_uses_explicit_carrier_context() -> None:
    helper = _remote_helper()

    assert 'carrier_context = str(payload.get("carrier_context") or "none")' in helper
    assert 'carrier=None if carrier_context == "none" else carrier_context' in helper
    assert 'carrier="beeline"' not in helper
    assert '"carrier_context": carrier_context' in helper
