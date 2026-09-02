from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "release_1_2_gate_f.py"
SPEC = importlib.util.spec_from_file_location("release_1_2_gate_f", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _candidate() -> dict[str, object]:
    return {
        "id": "pokrov-1.2.0-candidate.test",
        "operational_id": "1" * 64,
        "manifest_sha256": "2" * 64,
        "signature_sha256": "3" * 64,
        "receipt_sha256": "4" * 64,
        "sources": {
            "platform": "a" * 40,
            "client": "b" * 40,
            "core": "c" * 40,
            "release_index": "d" * 40,
        },
    }


def _args(tmp_path: Path, input_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        input=input_path,
        manifest=tmp_path / "manifest.json",
        signature=tmp_path / "manifest.json.sig",
        receipt=tmp_path / "receipt.json",
        signed_evidence=tmp_path / "signed-evidence.json",
        release_index_root=tmp_path,
        repo_root=tmp_path,
        output=None,
        expect_blocked=False,
    )


def _write_case(
    tmp_path: Path,
    *,
    statuses: dict[str, str] | None = None,
) -> tuple[argparse.Namespace, Path, dict[str, object]]:
    candidate = _candidate()
    resolved_statuses = {
        identifier: "PASS" for identifier in MODULE.REQUIRED_CHECK_IDS
    }
    resolved_statuses.update(statuses or {})
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(
        json.dumps(
            {
                "candidate": {"id": candidate["id"]},
                "checks": resolved_statuses,
            }
        ),
        encoding="utf-8",
    )
    evidence_hash = _sha256(evidence_path)
    payload = {
        "schema": MODULE.INPUT_SCHEMA,
        "candidate": candidate,
        "checks": [
            {
                "id": identifier,
                "evidence": {
                    "path": evidence_path.name,
                    "sha256": evidence_hash,
                    "status_pointer": f"/checks/{identifier}",
                    "candidate_pointer": "/candidate/id",
                },
            }
            for identifier in MODULE.REQUIRED_CHECK_IDS
        ],
    }
    input_path = tmp_path / "gate-f-input.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")
    return _args(tmp_path, input_path), evidence_path, payload


def _signed_candidate_stub(
    *, args: argparse.Namespace, expected: dict[str, object]
) -> dict[str, object]:
    return {
        "status": "PASS",
        "candidate_label": expected["id"],
        "operational_id": expected["operational_id"],
        "manifest_sha256": expected["manifest_sha256"],
        "signature_sha256": expected["signature_sha256"],
        "receipt_sha256": expected["receipt_sha256"],
        "signing": {"status": "PASS"},
        "sources": expected["sources"],
    }


def test_all_required_exact_candidate_checks_produce_go(
    tmp_path: Path, monkeypatch
) -> None:
    args, _evidence, _payload = _write_case(tmp_path)
    monkeypatch.setattr(MODULE, "_validate_signed_candidate", _signed_candidate_stub)

    report = MODULE.build_report(args)

    assert report["decision"] == "GO"
    assert report["summary"] == {
        "required": len(MODULE.REQUIRED_CHECK_IDS),
        "pass": len(MODULE.REQUIRED_CHECK_IDS),
        "fail": 0,
        "non_pass": 0,
        "validation_errors": [],
    }
    assert report["promotion"]["gate_g_authorized"] is False


def test_gate_f_validates_signed_candidate_before_physical_phone_gate(
    tmp_path: Path, monkeypatch
) -> None:
    expected = _candidate()
    args = _args(tmp_path, tmp_path / "input.json")
    captured: dict[str, object] = {}

    def validate_retained_candidate(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {
            "candidate_label": expected["id"],
            "candidate_id": expected["operational_id"],
            "manifest_sha256": expected["manifest_sha256"],
            "signature_sha256": expected["signature_sha256"],
            "signing": {"status": "PASS"},
        }

    monkeypatch.setattr(
        MODULE.candidate_gate,
        "_validate_retained_candidate",
        validate_retained_candidate,
    )
    monkeypatch.setattr(
        MODULE,
        "_read_json",
        lambda _path: {
            "sources": {
                name: {"commit": revision}
                for name, revision in expected["sources"].items()
            }
        },
    )
    monkeypatch.setattr(MODULE, "_sha256_file", lambda _path: "4" * 64)

    result = MODULE._validate_signed_candidate(args=args, expected=expected)

    assert result["status"] == "PASS"
    assert captured["require_physical_phone_install_binding"] is False


def test_manual_or_access_gate_produces_blocked(
    tmp_path: Path, monkeypatch
) -> None:
    args, _evidence, _payload = _write_case(
        tmp_path,
        statuses={"ru_origin": "BLOCKED_BY_ACCESS"},
    )
    monkeypatch.setattr(MODULE, "_validate_signed_candidate", _signed_candidate_stub)

    report = MODULE.build_report(args)

    assert report["decision"] == "BLOCKED"
    assert report["summary"]["pass"] == len(MODULE.REQUIRED_CHECK_IDS) - 1
    assert report["summary"]["non_pass"] == 1


def test_explicit_failed_gate_produces_no_go(tmp_path: Path, monkeypatch) -> None:
    args, _evidence, _payload = _write_case(
        tmp_path,
        statuses={"mandatory_stop_ship_and_dod": "FAIL"},
    )
    monkeypatch.setattr(MODULE, "_validate_signed_candidate", _signed_candidate_stub)

    report = MODULE.build_report(args)

    assert report["decision"] == "NO_GO"
    assert report["summary"]["fail"] == 1


def test_tampered_evidence_fails_closed(tmp_path: Path, monkeypatch) -> None:
    args, evidence_path, _payload = _write_case(tmp_path)
    monkeypatch.setattr(MODULE, "_validate_signed_candidate", _signed_candidate_stub)
    evidence_path.write_text('{"tampered":true}', encoding="utf-8")

    report = MODULE.build_report(args)

    assert report["decision"] == "NO_GO"
    assert "evidence SHA-256 mismatch" in report["summary"]["validation_errors"][0]


def test_missing_required_check_fails_closed(tmp_path: Path, monkeypatch) -> None:
    args, _evidence, payload = _write_case(tmp_path)
    payload["checks"].pop()
    args.input.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(MODULE, "_validate_signed_candidate", _signed_candidate_stub)

    report = MODULE.build_report(args)

    assert report["decision"] == "NO_GO"
    assert "check set mismatch" in report["summary"]["validation_errors"][0]


def test_unknown_status_fails_closed(tmp_path: Path, monkeypatch) -> None:
    args, _evidence, _payload = _write_case(
        tmp_path,
        statuses={"current_origin": "LOOKS_GOOD"},
    )
    monkeypatch.setattr(MODULE, "_validate_signed_candidate", _signed_candidate_stub)

    report = MODULE.build_report(args)

    assert report["decision"] == "NO_GO"
    assert "status is not allowed" in report["summary"]["validation_errors"][0]


def test_candidate_mismatch_fails_closed(tmp_path: Path, monkeypatch) -> None:
    args, evidence_path, payload = _write_case(tmp_path)
    evidence_path.write_text(
        json.dumps(
            {
                "candidate": {"id": "pokrov-1.2.0-candidate.other"},
                "checks": {
                    identifier: "PASS" for identifier in MODULE.REQUIRED_CHECK_IDS
                },
            }
        ),
        encoding="utf-8",
    )
    new_hash = _sha256(evidence_path)
    for check in payload["checks"]:
        check["evidence"]["sha256"] = new_hash
    args.input.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(MODULE, "_validate_signed_candidate", _signed_candidate_stub)

    report = MODULE.build_report(args)

    assert report["decision"] == "NO_GO"
    assert "candidate binding mismatch" in report["summary"]["validation_errors"][0]


def test_evidence_path_escape_fails_closed(tmp_path: Path, monkeypatch) -> None:
    args, _evidence, payload = _write_case(tmp_path)
    payload["checks"][0]["evidence"]["path"] = "../outside.json"
    args.input.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(MODULE, "_validate_signed_candidate", _signed_candidate_stub)

    report = MODULE.build_report(args)

    assert report["decision"] == "NO_GO"
    assert "escapes the repository" in report["summary"]["validation_errors"][0]


def test_gate_f_aggregate_rehashes_upstream_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    args, evidence_path, payload = _write_case(tmp_path)
    upstream_path = tmp_path / "upstream.json"
    upstream_path.write_text('{"status":"PASS"}', encoding="utf-8")
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence["schema"] = "pokrov.release-1.2.0.gate-f-evidence/v1"
    evidence["upstream_evidence"] = [
        {"path": upstream_path.name, "sha256": _sha256(upstream_path)}
    ]
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    new_hash = _sha256(evidence_path)
    for check in payload["checks"]:
        check["evidence"]["sha256"] = new_hash
    args.input.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(MODULE, "_validate_signed_candidate", _signed_candidate_stub)

    assert MODULE.build_report(args)["decision"] == "GO"

    upstream_path.write_text('{"status":"FAIL"}', encoding="utf-8")
    report = MODULE.build_report(args)
    assert report["decision"] == "NO_GO"
    assert "upstream evidence SHA-256 mismatch" in report["summary"][
        "validation_errors"
    ][0]


def test_expect_blocked_never_masks_no_go() -> None:
    assert MODULE._exit_code("GO", expect_blocked=False) == 0
    assert MODULE._exit_code("BLOCKED", expect_blocked=False) == 2
    assert MODULE._exit_code("BLOCKED", expect_blocked=True) == 0
    assert MODULE._exit_code("NO_GO", expect_blocked=True) == 2
