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
    assert "cleanup_tg_ids = {tg_id, int(target_user.tg_id)}" in helper
    assert "if int(value) not in cleanup_tg_ids" in helper
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


def test_root_adb_mode_selects_the_exact_local_install_without_reporting_it() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    helper = _remote_helper()

    assert (
        "from remote_activate_owned_awg_labs import _load_emulator_identity" in source
    )
    assert 'parser.add_argument("--adb-serial", default="emulator-5554")' in source
    assert '"exact_install_id": exact_install_id' in source
    assert (
        'exact_install_id = str(payload.get("exact_install_id") or "").strip()'
        in helper
    )
    assert "AccountDevice.install_id == exact_install_id" in helper
    assert 'target_selection_mode = "exact_local_install"' in helper
    assert '"device_record_present": device is not None' in helper
    assert '"raw_identifiers_returned": False' in helper
    assert '"exact_install_id": exact_install_id' not in helper


def test_any_supplied_install_confirmation_is_checked_in_plan_and_apply() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    helper = _remote_helper()

    assert "if confirm_target_install_sha256 and not hmac.compare_digest(" in helper
    assert "target_confirmation_invalid = bool(confirm_target_install_sha256)" in helper
    assert "target_confirmation_invalid = bool(target_confirmation)" in source
    assert "local install identity confirmation failed" in source
