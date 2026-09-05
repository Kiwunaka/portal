from __future__ import annotations

import ast
import copy
from pathlib import Path

import pytest


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


def _scope_guard():
    helper = ast.parse(_remote_helper())
    function = next(node for node in helper.body if isinstance(node, ast.FunctionDef) and node.name == "require_isolated_lab_scope")
    namespace = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(SCRIPT), "exec"), namespace)
    return namespace["require_isolated_lab_scope"]


@pytest.mark.parametrize("config", [
    {"awg2_lab": {"allowlist_install_ids": ["other-install"]}},
    {"awg31_lab": {"allowlist_tg_ids": [42]}},
    {"cohort_overrides": {"candidate4-awg-lab": {"install_ids": ["other-install"]}}},
    {"cohort_overrides": {"candidate4-awg-lab": {"install_ids": ["target"], "tg_ids": [42]}}},
    {"cohort_overrides": {"other": {"transport_profile": "awg31_lab", "platforms": ["windows"]}}},
    {"defaults": {"transport_profile": "awg2_lab"}},
    {"carrier_overrides": {"beeline": {"transport_profile": "awg31_lab"}}},
])
def test_shared_lab_scope_is_rejected_without_mutating_input(config) -> None:
    before = copy.deepcopy(config)
    with pytest.raises(ValueError, match="shared AWG scope"):
        _scope_guard()(config, "target")
    assert config == before


def test_isolated_install_scope_preserves_unrelated_configuration() -> None:
    config = {"defaults": {"transport_profile": "legacy_reality_fallback"},
              "cohort_overrides": {"other": {"install_ids": ["other"], "transport_profile": "legacy_reality_fallback"},
                                   "candidate4-awg-lab": {"install_ids": ["target"], "transport_profile": "awg31_lab"}},
              "awg2_lab": {"allowlist_install_ids": ["target"]},
              "awg31_lab": {"allowlist_install_ids": []}}
    before = copy.deepcopy(config)
    _scope_guard()(config, "target")
    assert config == before


def test_scope_guard_precedes_any_guarded_mutation_and_new_scope_is_install_only() -> None:
    helper = _remote_helper()
    first_mutation = helper.index('    guarded(\n        "user.extend"')
    assert helper.index("require_isolated_lab_scope(current, install_id)") < first_mutation
    assignment = helper[helper.index('    cohorts["candidate4-awg-lab"] = {'):helper.index('current["cohort_overrides"] = cohorts')]
    assert '"tg_ids": []' in assignment
    assert '"allowlist_tg_ids": [tg_id]' not in helper
    assert helper.index("if latest != current:") < helper.index('    "network_rollout_config.update",')


@pytest.mark.parametrize("account_selector,expected", [(False, True), (True, False)])
def test_apply_readback_accepts_only_install_scoped_binding(account_selector, expected) -> None:
    tree = ast.parse(_remote_helper())
    branch = next(node for node in tree.body if isinstance(node, ast.If)
                  and any(isinstance(child, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ok" for t in child.targets) for child in node.body))
    scope = {"selected_profile": "awg31_lab", "install_id": "target", "tg_id": 42,
             "selected": {"transport_profile": "awg31_lab", "install_ids": ["target"]},
             "selected_lab": {"allowlist_install_ids": ["target"], "allowlist_tg_ids": [42] if account_selector else []},
             "live_user_entitled": True, "resolved_profile": "awg31_lab"}
    exec(compile(ast.Module(body=branch.orelse, type_ignores=[]), str(SCRIPT), "exec"), scope)
    assert scope["ok"] is expected


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

    assert "from remote_activate_owned_awg_labs import (" in source
    assert "_load_emulator_identity," in source
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


def test_confirmed_install_hash_can_select_without_device_label() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    helper = _remote_helper()

    assert 'parser.add_argument("--device-label-fragment", default="")' in source
    assert '(not label and not target_confirmation)' in source
    assert '(not label_fragment and not confirm_target_install_sha256)' in helper
    assert "AccountDevice.install_id.isnot(None)" in helper
    assert ".limit(1000)" in helper
    assert 'target_selection_mode = "confirmed_install_hash"' in helper
    assert '"confirmed_install_hash_resolution"' in helper
    assert '"device_label_sha256": label_sha256 or None' in source


def test_account_component_resolution_is_unique_and_install_owned() -> None:
    helper = _remote_helper()

    assert 'target_user_resolution = "account_component_entitled"' in helper
    assert '[int(row.tg_id) for row in (target_users or global_install_users)]' in helper
    assert 'AccountDevice.revoked_at.is_(None)' in helper
    assert 'entitled_user_owns_install = bool(' in helper
    assert '"entitled_user_install_ownership"' in helper
    assert '"account_user_resolution_unavailable"' in helper


def test_exact_local_install_can_receive_one_explicit_test_day() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    helper = _remote_helper()

    assert '"--extend-target-entitlement-days"' in source
    assert "choices=(0, 1)" in source
    assert "entitlement extension requires exact root-verified local install" in source
    assert "extend_target_entitlement_days not in {0, 1}" in helper
    assert 'selected_profile == "default"' in helper
    assert 'entitlement_resolution = "exact_install_one_day_extension"' in helper
    assert "device_account_matches_global_install_user" in helper
    assert '"user.extend"' in helper
    assert '{"days": 1, "delta_days": 1, "allow_deactivate": False}' in helper
    assert '"entitlement_extension_applied": entitlement_extension_applied' in helper
    assert '"target_user_is_entitled": target_user_currently_entitled' in helper
    assert '"target_user_is_entitled": live_user_entitled' in helper
    assert '"entitlement_subject_matches_target_user": target_user is entitled_user' in helper
    assert "and live_user_entitled" in helper
