from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


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
    with pytest.raises(module.RuntimeProfileBoundaryError, match="outside the app runtime"):
        module._runtime_config_path(escaped, "space.pokrov.pokrov_android_shell")


@pytest.mark.parametrize(
    "path",
    (
        "/data/user/0/space.pokrov.pokrov_android_shell/files/pokrov-runtime/../escape.json",
        "/data/user/0/space.pokrov.pokrov_android_shell/files/pokrov-runtime//escape.json",
        "/data/user/0/space.pokrov.pokrov_android_shell/files/pokrov-runtime/dir\\escape.json",
        "/data/user/0/space.pokrov.pokrov_android_shell/files/pokrov-runtime/a.json;id",
    ),
)
def test_runtime_path_rejects_dot_segments_and_shell_metacharacters(path: str) -> None:
    module = _load_module()
    xml = f'<map><string name="config_path">{path}</string></map>'

    with pytest.raises(module.RuntimeProfileBoundaryError):
        module._runtime_config_path(xml, "space.pokrov.pokrov_android_shell")


def test_runtime_path_keeps_valid_nested_profile() -> None:
    module = _load_module()
    nested = (
        '<map><string name="config_path">'
        "/data/user/0/space.pokrov.pokrov_android_shell/files/"
        "pokrov-runtime/working/configs/profile-123.json"
        "</string></map>"
    )

    assert module._runtime_config_path(
        nested, "space.pokrov.pokrov_android_shell"
    ).endswith("/working/configs/profile-123.json")


@pytest.mark.parametrize(
    "package",
    (
        "space/pokrov/app",
        "space..pokrov",
        ".space.pokrov",
        "space.pokrov.",
        "space.pokrov;id",
        "1space.pokrov",
    ),
)
def test_android_package_requires_application_id_syntax(package: str) -> None:
    module = _load_module()
    assert module._valid_package(package) is False


def test_remote_read_uses_one_open_file_descriptor_for_validation_and_read() -> None:
    module = _load_module()
    package = "space.pokrov.pokrov_android_shell"
    runtime = f"/data/user/0/{package}/files/pokrov-runtime"
    target = f"{runtime}/working/configs/profile.json"
    with patch.object(module, "_run_adb", return_value=b"{}") as run_adb:
        assert module._read_remote_file(
            Path(sys.executable),
            "emulator-5554",
            target,
            runtime,
            64,
            exact_target=False,
        ) == "{}"

    command = run_adb.call_args.args[-1]
    assert "exec 3<" in command
    assert "/proc/$$/fd/3" in command
    assert "toybox realpath" in command
    assert "toybox head -c 65 <&3" in command
    assert run_adb.call_args.kwargs["boundary_returncodes"] == frozenset(
        {61, 126, 127}
    )


def test_preferences_read_requires_the_exact_opened_target() -> None:
    module = _load_module()
    package = "space.pokrov.pokrov_android_shell"
    root = f"/data/user/0/{package}/shared_prefs"
    target = f"{root}/{module.PREFERENCES_FILE}"
    with patch.object(module, "_run_adb", return_value=b"<map />") as run_adb:
        module._read_remote_file(
            Path(sys.executable),
            "emulator-5554",
            target,
            root,
            64,
            exact_target=True,
        )

    command = run_adb.call_args.args[-1]
    assert (
        '[ "$target_real" = "$root_real/pokrov_runtime_profile.xml" ] || exit 61'
        in command
    )


def test_remote_file_rejects_the_extra_byte_after_bounded_read() -> None:
    module = _load_module()
    package = "space.pokrov.pokrov_android_shell"
    runtime = f"/data/user/0/{package}/files/pokrov-runtime"
    with patch.object(module, "_run_adb", return_value=b"x" * 65):
        with pytest.raises(module.RuntimeProfileBoundaryError, match="exceeded"):
            module._read_remote_file(
                Path(sys.executable),
                "emulator-5554",
                f"{runtime}/profile.json",
                runtime,
                64,
                exact_target=False,
            )


def test_adb_boundary_exit_code_is_permanent() -> None:
    module = _load_module()
    with patch.object(
        module,
        "_run_bounded_process",
        return_value=(61, b"", b""),
    ):
        with pytest.raises(module.RuntimeProfileBoundaryError, match="boundary"):
            module._run_adb(
                Path(sys.executable),
                "emulator-5554",
                "shell",
                "false",
                stdout_limit=1,
                boundary_returncodes=frozenset({61}),
            )


def test_missing_android_root_exit_code_remains_retryable() -> None:
    module = _load_module()
    with patch.object(
        module,
        "_run_bounded_process",
        return_value=(10, b"", b""),
    ):
        with pytest.raises(RuntimeError, match="readback failed"):
            module._run_adb(
                Path(sys.executable),
                "emulator-5554",
                "shell",
                "false",
                stdout_limit=1,
                boundary_returncodes=frozenset({61}),
            )


def test_bounded_process_accepts_exact_limit_and_rejects_stdout_or_stderr_overflow() -> None:
    module = _load_module()
    exact = [
        sys.executable,
        "-c",
        "import sys;sys.stdout.buffer.write(b'x'*8)",
    ]
    returncode, stdout, stderr = module._run_bounded_process(
        exact,
        stdout_limit=8,
        stderr_limit=8,
        timeout=5,
    )
    assert (returncode, stdout, stderr) == (0, b"x" * 8, b"")

    for stream_name in ("stdout", "stderr"):
        command = [
            sys.executable,
            "-c",
            f"import sys;sys.{stream_name}.buffer.write(b'x'*9)",
        ]
        with pytest.raises(module.RuntimeProfileBoundaryError, match="exceeded"):
            module._run_bounded_process(
                command,
                stdout_limit=8,
                stderr_limit=8,
                timeout=5,
            )


def test_permanent_containment_failure_is_not_retried() -> None:
    module = _load_module()
    with patch.object(
        module,
        "_read_remote_file",
        side_effect=module.RuntimeProfileBoundaryError("blocked"),
    ) as read_remote:
        with pytest.raises(SystemExit, match="containment or size"):
            module._load_runtime_config(
                Path(sys.executable),
                "emulator-5554",
                "space.pokrov.pokrov_android_shell",
                30,
            )

    assert read_remote.call_count == 1


def test_transient_staging_failure_retries_then_succeeds() -> None:
    module = _load_module()
    package = "space.pokrov.pokrov_android_shell"
    preferences = (
        '<map><string name="config_path">'
        f"/data/user/0/{package}/files/pokrov-runtime/profile.json"
        "</string></map>"
    )
    config = '{"route":{"final":"countries"},"endpoints":[],"outbounds":[]}'
    with patch.object(
        module,
        "_read_remote_file",
        side_effect=[RuntimeError("not staged"), preferences, config],
    ) as read_remote, patch.object(module.time, "sleep") as sleep:
        loaded = module._load_runtime_config(
            Path(sys.executable),
            "emulator-5554",
            package,
            5,
        )

    assert loaded["route"]["final"] == "countries"
    assert read_remote.call_count == 3
    sleep.assert_called_once_with(0.5)
