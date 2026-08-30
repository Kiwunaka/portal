from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "inspect_android_runtime_profile.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("inspect_android_runtime_profile", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_awg31_profile_requires_matching_route_and_typed_endpoint() -> None:
    module = _load_module()
    report = module.inspect_runtime_profile(
        {
            "route": {"final": "pokrov-awg31-lab"},
            "endpoints": [
                {
                    "type": "awg",
                    "tag": "pokrov-awg31-lab",
                    "private_key": "must-not-leak",
                    "server": "must-not-leak",
                }
            ],
            "outbounds": [
                {"type": "direct", "tag": "direct"},
                {"type": "block", "tag": "block"},
            ],
        },
        "awg31_lab",
    )

    assert report == {
        "schema_version": "pokrov-android-runtime-profile-readback-v1",
        "expected_profile": "awg31_lab",
        "observed_profile": "awg31_lab",
        "matches_expected_profile": True,
        "profile_internally_consistent": True,
        "endpoint_type_counts": {"awg": 1},
        "outbound_type_counts": {"block": 1, "direct": 1},
        "private_key_material_present": True,
        "raw_config_returned": False,
        "raw_endpoints_returned": False,
        "raw_identifiers_returned": False,
    }
    assert "must-not-leak" not in repr(report)


def test_lab_route_with_wrong_endpoint_fails_closed() -> None:
    module = _load_module()
    report = module.inspect_runtime_profile(
        {
            "route": {"final": "pokrov-awg31-lab"},
            "endpoints": [{"type": "awg", "tag": "pokrov-awg2-lab"}],
            "outbounds": [],
        },
        "awg31_lab",
    )

    assert report["observed_profile"] == "invalid_lab_profile"
    assert report["profile_internally_consistent"] is False
    assert report["matches_expected_profile"] is False


def test_cached_default_profile_cannot_pass_an_awg_expectation() -> None:
    module = _load_module()
    report = module.inspect_runtime_profile(
        {
            "route": {"final": "countries"},
            "endpoints": [],
            "outbounds": [
                {"type": "vless", "tag": "node"},
                {"type": "selector", "tag": "countries"},
            ],
        },
        "awg31_lab",
    )

    assert report["observed_profile"] == "default"
    assert report["matches_expected_profile"] is False
    assert report["outbound_type_counts"] == {"selector": 1, "vless": 1}


def test_default_profile_passes_only_without_an_awg_endpoint() -> None:
    module = _load_module()
    report = module.inspect_runtime_profile(
        {
            "route": {"final": "countries"},
            "endpoints": [{}],
            "outbounds": [{"type": "vless"}],
        },
        "default",
    )

    assert report["observed_profile"] == "default"
    assert report["matches_expected_profile"] is True
    assert report["endpoint_type_counts"] == {"unknown": 1}


def test_runtime_path_must_stay_inside_the_selected_app() -> None:
    module = _load_module()
    valid = (
        '<map><string name="config_path">'
        "/data/user/0/space.pokrov.pokrov_android_shell/files/pokrov-runtime/a.json"
        "</string></map>"
    )
    escaped = (
        '<map><string name="config_path">'
        "/data/user/0/other.package/files/pokrov-runtime/a.json"
        "</string></map>"
    )

    assert module._runtime_config_path(
        valid, "space.pokrov.pokrov_android_shell"
    ).endswith("/a.json")
    try:
        module._runtime_config_path(escaped, "space.pokrov.pokrov_android_shell")
    except ValueError as exc:
        assert "outside the app runtime" in str(exc)
    else:
        raise AssertionError("escaped runtime profile path was accepted")
