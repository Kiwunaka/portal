import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_module():
    path = SCRIPTS_DIR / "remote_ru_origin_environment_probe.py"
    spec = importlib.util.spec_from_file_location("remote_ru_origin_environment_probe", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _response(module, *, installed: bool) -> dict:
    file_rows = []
    payload = []
    for index, (source_path, _remote_path) in enumerate(module.SOURCE_MAPPINGS):
        value = f"source-{index}\n".encode()
        payload.append((source_path, value))
        file_rows.append(
            {
                "index": index,
                "exists": installed,
                "readable": installed,
                "raw_sha256": module._sha256(value) if installed else "",
                "normalized_sha256": module._sha256(value) if installed else "",
                "mode": "644" if installed else "",
            }
        )
    unit_state = {
        unit: {
            "load": "loaded" if installed else "not-found",
            "active": "active" if installed and unit.endswith(".timer") else "inactive" if installed else "unknown",
            "enabled": "enabled" if installed and unit.endswith(".timer") else "static" if installed else "unknown",
            "result": "success" if installed else "unknown",
        }
        for unit in module.REQUIRED_UNITS
    }
    private = {"exists": installed, "metadata_available": installed, "private": installed, "mode": "600"}
    return (
        {
            "schema": module.REMOTE_SCHEMA,
            "files": file_rows,
            "units": unit_state,
            "config": {name: dict(private) for name in ("probe_env", "uploader_env", "hmac_key", "profiles")},
            "spool": {
                **private,
                "counts": {"pending": 0, "blocked": 0, "quarantine": 0, "archive": 0},
            },
            "latest_archive": {"available": False},
            "clock": {"ntp_synchronized": "yes"},
        },
        payload,
    )


def test_not_installed_environment_is_manual_not_failure_or_pass() -> None:
    module = _load_module()
    response, payload = _response(module, installed=False)

    report = module._build_report(
        source_revision="a" * 40,
        auth_method="key",
        source_payload=payload,
        response=response,
        checked_at="2026-08-29T10:00:00+00:00",
    )

    assert report["ok"] is False
    assert report["probe_completed"] is True
    assert report["ru_origin_passed"] is False
    assert report["ru_origin_status"] == "MANUAL_OWNER_TEST"
    assert report["classification"] == "MANUAL_OWNER_TEST_ENVIRONMENT_NOT_INSTALLED"
    assert report["ready_for_manual_owner_run"] is False
    assert report["source_summary"]["not_installed_count"] == len(module.SOURCE_MAPPINGS)
    assert report["runtime_mutated"] is False


def test_installed_exact_environment_still_requires_fresh_manual_run() -> None:
    module = _load_module()
    response, payload = _response(module, installed=True)

    report = module._build_report(
        source_revision="b" * 40,
        auth_method="password#2",
        source_payload=payload,
        response=response,
        checked_at="2026-08-29T10:00:00+00:00",
    )

    assert report["ready_for_manual_owner_run"] is True
    assert report["ok"] is True
    assert report["ru_origin_passed"] is False
    assert report["classification"] == "MANUAL_OWNER_TEST_FRESH_RUN_REQUIRED"
    assert report["ru_origin_status"] == "MANUAL_OWNER_TEST"
    assert report["auth_method"] == "password"
    assert report["server_readback_performed"] is False


def test_report_omits_remote_paths_addresses_aliases_and_content() -> None:
    module = _load_module()
    response, payload = _response(module, installed=False)
    report = module._build_report(
        source_revision="c" * 40,
        auth_method="ssh_config",
        source_payload=payload,
        response=response,
    )
    encoded = json.dumps(report)

    assert "/opt/pokrov" not in encoded
    assert "/etc/pokrov" not in encoded
    assert "node_host" not in encoded
    assert "ssh_config_alias" not in encoded
    assert "source-0" not in encoded
    assert report["auth_method"] == "ssh_config"


def test_incomplete_or_duplicate_remote_file_rows_fail_closed() -> None:
    module = _load_module()
    response, payload = _response(module, installed=False)
    response["files"] = response["files"][:-1]
    with pytest.raises(ValueError, match="incomplete"):
        module._build_report(
            source_revision="d" * 40,
            auth_method="key",
            source_payload=payload,
            response=response,
        )

    response, payload = _response(module, installed=False)
    response["files"][-1]["index"] = 0
    with pytest.raises(ValueError, match="index"):
        module._build_report(
            source_revision="d" * 40,
            auth_method="key",
            source_payload=payload,
            response=response,
        )


def test_blocked_report_never_claims_runtime_failure() -> None:
    module = _load_module()
    report = module._blocked_report("e" * 40, checked_at="2026-08-29T10:00:00+00:00")

    assert report["ok"] is False
    assert report["classification"] == "BLOCKED_BY_ACCESS"
    assert report["ru_origin_status"] == "BLOCKED_BY_ACCESS"
    assert report["runtime_mutated"] is False


def test_untrusted_remote_summary_fields_are_sanitized() -> None:
    module = _load_module()
    response, payload = _response(module, installed=True)
    response["latest_archive"] = {
        "available": True,
        "run_id_sha256": "raw-run-id",
        "manifest_revision": "not-a-hash",
        "finished_at": "raw payload text",
        "age_seconds": -1,
        "execution_status": "secret-state",
        "evidence_code": "raw-exception",
        "target_count": -2,
        "stage_status_counts": {"pass": -1, "fail": "raw", "not_run": 2},
    }

    report = module._build_report(
        source_revision="f" * 40,
        auth_method="key",
        source_payload=payload,
        response=response,
    )

    latest = report["latest_archive"]
    assert latest["run_id_sha256"] == ""
    assert latest["manifest_revision"] == ""
    assert latest["finished_at"] == ""
    assert latest["age_seconds"] is None
    assert latest["execution_status"] == "unknown"
    assert latest["evidence_code"] == "unknown"
    assert latest["target_count"] == 0
    assert latest["stage_status_counts"] == {"pass": 0, "fail": 0, "not_run": 2}


def test_harness_error_is_not_mislabeled_as_access_failure() -> None:
    module = _load_module()
    report = module._harness_error_report("1" * 40, checked_at="2026-08-29T10:00:00+00:00")

    assert report["classification"] == "MANUAL_OWNER_TEST_HARNESS_ERROR"
    assert report["ru_origin_status"] == "MANUAL_OWNER_TEST"
    assert report["ok"] is False
