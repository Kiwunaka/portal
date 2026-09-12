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


@pytest.fixture()
def material_selector(monkeypatch):
    import base64
    import importlib
    from datetime import datetime, timezone
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    monkeypatch.syspath_prepend(str(ROOT / "portal_bot"))
    from models import Awg2LabMaterial, Awg31LabMaterial, Base
    from awg_lab_key_binding import require_awg_device_key_binding

    services = [importlib.import_module(name + "_lab_service") for name in ("awg2", "awg31")]
    models = [Awg2LabMaterial, Awg31LabMaterial]
    policy = {}
    namespace = {"require_awg_device_key_binding": require_awg_device_key_binding,
                 "load_network_rollout_config": lambda **_: policy}
    for name, service, model in zip(("awg2", "awg31"), services, models):
        monkeypatch.setenv(name.upper() + "_LAB_MATERIAL_SECRET", "binder-fixture-encryption-only")
        policy[name + "_lab"] = getattr(service, "default_" + name + "_lab_config")()
        policy[name + "_lab"].update(generation="fixture-v1", server_record_id="fixture-server",
                                     allowlist_node_codes=["de"])
        namespace[model.__name__] = model
        namespace["ready_" + name] = service._ready_material
        namespace["decrypt_" + name] = service._decrypt_endpoint
    function = next(node for node in ast.parse(_remote_helper()).body
                    if isinstance(node, ast.FunctionDef) and node.name == "load_target_materials")
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(SCRIPT), "exec"), namespace)
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)

    def seed(install, key_bytes, *, state="ready", age_days=0):
        from datetime import timedelta
        rows = []
        for name, service, model in zip(("awg2", "awg31"), services, models):
            config = policy[name + "_lab"]
            row = model(
                tg_id=1001, install_id=install, contract_id=config["contract_id"],
                contract_sha256=config["contract_sha256"], generation=config["generation"],
                endpoint_revision=config["endpoint_revision"], server_record_id=config["server_record_id"],
                node_code="de", material_hash="a" * 64,
                endpoint_ciphertext=service._encrypt_endpoint({"private_key": base64.b64encode(key_bytes).decode()}),
                state=state, is_active=state == "ready",
                provisioned_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=age_days),
            )
            session.add(row)
            rows.append(row)
        session.commit()
        return rows

    try:
        yield session, namespace["load_target_materials"], seed, models
    finally:
        session.close()
        engine.dispose()


def test_binder_does_not_copy_another_devices_material(material_selector) -> None:
    session, select, seed, models = material_selector
    seed("foreign", bytes(32))
    assert select(session, 1001, "target", "awg31_lab") == (None, None)
    assert all(session.query(model).count() == 1 for model in models)


def test_repeated_bind_reuses_exact_target_without_refreshing_age(material_selector) -> None:
    session, select, seed, models = material_selector
    own = seed("target", bytes(32), age_days=1)
    seed("foreign", bytes(range(32)))
    before = [(row.id, row.provisioned_at, row.endpoint_ciphertext) for row in own[1:]]
    for _ in range(2):
        result = select(session, 1001, "target", "awg31_lab")
        assert [(row.id, row.provisioned_at, row.endpoint_ciphertext) for row in result if row is not None] == before
    assert all(session.query(model).count() == 2 for model in models)
    assert not session.new and not session.dirty and not session.deleted


def test_binder_rejects_key_shared_with_foreign_history(material_selector) -> None:
    from awg_lab_key_binding import AwgDeviceKeyError
    session, select, seed, _ = material_selector
    seed("target", bytes(32))
    seed("foreign", bytes([1]) + bytes(31), state="rotated")
    with pytest.raises(AwgDeviceKeyError, match="material_key_already_bound"):
        select(session, 1001, "target", "awg31_lab")
    assert not session.new and not session.dirty and not session.deleted


def test_binder_does_not_refresh_expired_material(material_selector) -> None:
    session, select, seed, _ = material_selector
    own = seed("target", bytes(32), age_days=8)
    before = [row.provisioned_at for row in own]
    assert select(session, 1001, "target", "awg31_lab") == (None, None)
    assert [row.provisioned_at for row in own] == before


def test_awg31_binding_needs_only_its_own_material_and_allowlist(material_selector) -> None:
    session, select, seed, _ = material_selector
    awg2, awg31 = seed("target", bytes(32))
    session.delete(awg2)
    session.commit()
    rows = select(session, 1001, "target", "awg31_lab")
    assert rows == (None, awg31)
    tree = ast.parse(_remote_helper())
    available = next(node.value for node in ast.walk(tree) if isinstance(node, ast.Assign)
                     and any(isinstance(target, ast.Name) and target.id == "source_material_available"
                             for target in node.targets))
    assert eval(compile(ast.Expression(available), str(SCRIPT), "eval"),
                {"awg2_row": rows[0], "awg31_row": rows[1]}) is True
    gate_loop = next(node for node in tree.body if isinstance(node, ast.For)
                     and isinstance(node.target, ast.Name) and node.target.id == "name")
    config = {"awg2_lab": {"allowlist_install_ids": ["target"], "expires_at": "unchanged"},
              "awg31_lab": {"allowlist_install_ids": []}}
    scope = {"current": config, "selected_profile": "awg31_lab", "install_id": "target",
             "tg_id": 1001, "target_user": type("User", (), {"tg_id": 1001})(),
             "cleanup_tg_ids": {1001}, "expires_at": "new-awg31-expiry"}
    exec(compile(ast.Module(body=[gate_loop], type_ignores=[]), str(SCRIPT), "exec"), scope)
    assert config["awg2_lab"] == {"allowlist_install_ids": [], "allowlist_tg_ids": [],
                                   "expires_at": "unchanged"}
    assert config["awg31_lab"]["allowlist_install_ids"] == ["target"]


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
    assert 'if selected_profile != "default" and not source_material_available:' in helper
    assert '"awg2_material_provisioned": False' in helper
    assert 'awg2_lab_material.replace' not in helper
    assert 'awg31_lab_material.replace' not in helper


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

    assert "from remote_activate_owned_awg_labs import _load_emulator_identity" in source
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
