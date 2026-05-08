from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PASS = "PASS"
BLOCKED_BY_ACCESS = "BLOCKED_BY_ACCESS"
EXTERNAL_DEPENDENCY = "EXTERNAL_DEPENDENCY"

DEFAULT_READINESS_JSON = Path("docs/audit-artifacts/payment-email-readiness-2026-05-07.json")

READINESS_REQUIRED = [
    "lavatop_invoice_credentials",
    "lavatop_webhook_auth",
    "lavatop_provider_acceptance",
    "email_public_mode",
    "email_delivery_webhook",
]

LIVE_EVIDENCE_REQUIRED = [
    "lavatop_live_invoice_creation",
    "lavatop_authenticated_success_webhook",
    "lavatop_webhook_replay_idempotency",
    "lavatop_failed_payment_no_fulfillment",
    "lavatop_manual_review_mismatch",
    "lavatop_reconciliation_procedure",
    "paid_access_key_email_delivery",
]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _status(value: object) -> str:
    normalized = str(value or "").strip().upper()
    if normalized in {PASS, BLOCKED_BY_ACCESS, EXTERNAL_DEPENDENCY}:
        return normalized
    return BLOCKED_BY_ACCESS


def _classification(statuses: list[str]) -> str:
    if statuses and all(status == PASS for status in statuses):
        return PASS
    if BLOCKED_BY_ACCESS in statuses:
        return BLOCKED_BY_ACCESS
    return EXTERNAL_DEPENDENCY


def _checks_by_name(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    raw_checks = payload.get("checks")
    if not isinstance(raw_checks, list):
        return result
    for item in raw_checks:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        result[name] = item
    return result


def _safe_check(name: str, status: str, *, missing: list[str] | None = None, source: str = "", note: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "status": _status(status),
        "missing": list(missing or []),
        "source": source,
        "note": note,
    }


def _readiness_checks(readiness_payload: dict[str, Any], *, readiness_json: Path) -> list[dict[str, Any]]:
    if not readiness_payload:
        return [
            _safe_check(
                "payment_email_readiness",
                BLOCKED_BY_ACCESS,
                missing=[str(readiness_json)],
                source="payment_email_readiness_smoke.py",
                note="Run the redacted Lava.top/email readiness smoke first.",
            )
        ]

    checks = _checks_by_name(readiness_payload)
    results: list[dict[str, Any]] = [
        _safe_check(
            "payment_email_readiness",
            _status(readiness_payload.get("classification")),
            source=str(readiness_json),
            note="Aggregate classification from payment_email_readiness_smoke.py.",
        )
    ]
    for name in READINESS_REQUIRED:
        check = checks.get(name)
        if not check:
            results.append(
                _safe_check(
                    name,
                    BLOCKED_BY_ACCESS,
                    missing=[f"{name} readiness"],
                    source=str(readiness_json),
                )
            )
            continue
        missing = [str(item) for item in check.get("missing", []) if str(item or "").strip()]
        results.append(
            _safe_check(
                name,
                _status(check.get("status")),
                missing=missing,
                source=str(readiness_json),
            )
        )
    return results


def _live_evidence_checks(evidence_payload: dict[str, Any], *, evidence_json: Path | None) -> list[dict[str, Any]]:
    checks = _checks_by_name(evidence_payload)
    source = str(evidence_json) if evidence_json else ""
    results: list[dict[str, Any]] = []
    for name in LIVE_EVIDENCE_REQUIRED:
        check = checks.get(name)
        if not check:
            results.append(
                _safe_check(
                    name,
                    BLOCKED_BY_ACCESS,
                    missing=[f"{name} evidence"],
                    source=source,
                    note="Attach redacted live/sandbox evidence before enabling paid checkout.",
                )
            )
            continue
        missing = [str(item) for item in check.get("missing", []) if str(item or "").strip()]
        results.append(
            _safe_check(
                name,
                _status(check.get("status")),
                missing=missing,
                source=source,
            )
        )
    return results


def build_report(*, readiness_json: Path, evidence_json: Path | None) -> dict[str, Any]:
    readiness_path = Path(readiness_json)
    evidence_path = Path(evidence_json) if evidence_json else None
    readiness_payload = _load_json(readiness_path)
    evidence_payload = _load_json(evidence_path) if evidence_path else {}
    checks = [
        *_readiness_checks(readiness_payload, readiness_json=readiness_path),
        *_live_evidence_checks(evidence_payload, evidence_json=evidence_path),
    ]
    statuses = [str(check["status"]) for check in checks]
    classification = _classification(statuses)
    ok = classification == PASS
    return {
        "ok": ok,
        "classification": classification,
        "safe_to_enable_paid_checkout": ok,
        "mode": "paid_checkout_launch_evidence",
        "inputs": {
            "readiness_json": str(readiness_path),
            "evidence_json": str(evidence_path) if evidence_path else "",
        },
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate redacted Lava.top/email launch evidence before paid checkout can be enabled.",
    )
    parser.add_argument("--readiness-json", default=str(DEFAULT_READINESS_JSON))
    parser.add_argument("--evidence-json", default="", help="Optional redacted live/sandbox paid-checkout evidence JSON.")
    parser.add_argument("--output", default="", help="Optional JSON output path.")
    args = parser.parse_args(argv)

    report = build_report(
        readiness_json=Path(args.readiness_json),
        evidence_json=Path(args.evidence_json) if str(args.evidence_json or "").strip() else None,
    )
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
