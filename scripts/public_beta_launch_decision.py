from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PASS = "PASS"
PASS_WITH_ACCEPTED_SKIPS = "PASS_WITH_ACCEPTED_SKIPS"
FAIL = "FAIL"
BLOCKED_BY_ACCESS = "BLOCKED_BY_ACCESS"
BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"
EXTERNAL_DEPENDENCY = "EXTERNAL_DEPENDENCY"
SKIPPED_BY_OPERATOR = "SKIPPED_BY_OPERATOR"
OPERATOR_ATTESTED = "OPERATOR_ATTESTED"
NO_GO = "NO_GO"
GO = "GO"

DEFAULT_HANDOFF = Path("docs/audit-artifacts/public-beta-handoff-2026-05-08.md")
DEFAULT_COMPLETION_AUDIT = Path("docs/audit-artifacts/public-beta-completion-audit-2026-05-08.md")
DEFAULT_EXTERNAL_PREFLIGHT_JSON = Path("docs/audit-artifacts/public-beta-external-access-preflight-2026-05-09.json")
DEFAULT_FULL_GATE = Path("docs/audit-artifacts/release-gate-full-local-2026-05-08.md")
DEFAULT_QUICK_GATE = Path("docs/audit-artifacts/release-gate-local-2026-05-08.md")
DEFAULT_BRAIN_GATE = Path("docs/audit-artifacts/release-gate-brain-2026-05-08.md")
DEFAULT_PAID_CHECKOUT_EVIDENCE = Path("docs/audit-artifacts/paid-checkout-launch-evidence-brain-2026-05-08.json")
DEFAULT_LIVE_EMAIL_STATUS = Path("docs/audit-artifacts/live-email-auth-status-brain-2026-05-08.json")
DEFAULT_LIVE_PAYMENT_STATUS = Path("docs/audit-artifacts/live-payment-provider-status-brain-2026-05-08.json")
DEFAULT_POST_DEPLOY_PROBE = Path("docs/audit-artifacts/public-beta-post-deploy-probe-2026-05-08.json")
DEFAULT_STAGED_REACHABILITY = Path("docs/audit-artifacts/staged-client-apps-reachability-2026-05-08.md")
DEFAULT_RUNTIME_SYNC_GUARD = Path("docs/audit-artifacts/runtime-link-sync-guard-2026-05-08.md")

KNOWN_STATUSES = {
    PASS,
    PASS_WITH_ACCEPTED_SKIPS,
    FAIL,
    BLOCKED_BY_ACCESS,
    BLOCKED_BY_POLICY,
    EXTERNAL_DEPENDENCY,
    SKIPPED_BY_OPERATOR,
    OPERATOR_ATTESTED,
}
STATUS_PRECEDENCE = {
    FAIL: 50,
    BLOCKED_BY_POLICY: 40,
    BLOCKED_BY_ACCESS: 30,
    EXTERNAL_DEPENDENCY: 20,
    SKIPPED_BY_OPERATOR: 10,
    OPERATOR_ATTESTED: 10,
    PASS_WITH_ACCEPTED_SKIPS: 10,
    PASS: 0,
}
RELEASE_READY_STATUSES = {PASS, PASS_WITH_ACCEPTED_SKIPS}


def _load_text(path: Path) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = Path(path).read_bytes()
    except FileNotFoundError:
        return {}
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _normalized_status(value: object, *, default: str = BLOCKED_BY_ACCESS) -> str:
    status = str(value or "").strip().upper()
    return status if status in KNOWN_STATUSES else default


def _int_value(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _provider_codes_from_payment_payload(payload: dict[str, Any]) -> list[str]:
    explicit_codes = payload.get("provider_codes")
    if isinstance(explicit_codes, list):
        return [str(value).strip().lower() for value in explicit_codes if str(value).strip()]

    raw_providers = payload.get("providers")
    if not isinstance(raw_providers, list):
        return []

    codes: list[str] = []
    for item in raw_providers:
        if isinstance(item, dict):
            code = str(item.get("code") or item.get("provider") or "").strip().lower()
        else:
            code = str(item or "").strip().lower()
        if code:
            codes.append(code)
    return codes


def _provider_count_from_payment_payload(payload: dict[str, Any], provider_codes: list[str]) -> int:
    if "provider_count" in payload:
        return _int_value(payload.get("provider_count"))
    return len(provider_codes)


def _check(
    name: str,
    status: str,
    *,
    source: Path | str = "",
    missing: list[str] | None = None,
    note: str = "",
) -> dict[str, Any]:
    return {
        "name": name,
        "status": _normalized_status(status),
        "missing": list(missing or []),
        "source": str(source),
        "note": note,
    }


def _extract_markdown_status(text: str) -> str:
    match = re.search(r"(?m)^-\s+Status:\s+`([^`]+)`", text)
    return str(match.group(1)).strip().upper() if match else ""


def _markdown_gate_check(
    *,
    name: str,
    path: Path,
    required_phrases: list[str],
    note: str,
) -> dict[str, Any]:
    text = _load_text(path)
    if not text:
        return _check(name, BLOCKED_BY_ACCESS, source=path, missing=[str(path)], note="Gate report is missing.")

    status = _extract_markdown_status(text)
    missing = [phrase for phrase in required_phrases if phrase not in text]
    if status != PASS:
        missing.append("- Status: `PASS`")
    if missing:
        return _check(name, FAIL, source=path, missing=missing, note=note)
    return _check(name, PASS, source=path, note=note)


def _handoff_policy_check(path: Path) -> dict[str, Any]:
    text = _load_text(path)
    if not text:
        return _check(
            "public_beta_handoff_policy",
            BLOCKED_BY_POLICY,
            source=path,
            missing=[str(path)],
            note="A final handoff must exist before publication.",
        )
    if "GO for public beta publication" in text and "NO-GO" not in text:
        return _check(
            "public_beta_handoff_policy",
            PASS,
            source=path,
            note="Handoff explicitly authorizes public beta publication.",
        )
    return _check(
        "public_beta_handoff_policy",
        BLOCKED_BY_POLICY,
        source=path,
        missing=["GO for public beta publication without any NO-GO marker"],
        note="Current handoff does not authorize public publication.",
    )


def _completion_audit_check(path: Path) -> dict[str, Any]:
    text = _load_text(path)
    if not text:
        return _check(
            "completion_audit_verdict",
            BLOCKED_BY_POLICY,
            source=path,
            missing=[str(path)],
            note="Completion audit must map the prompt to real evidence.",
        )
    if "GOAL COMPLETE" in text and "GOAL NOT COMPLETE" not in text and "Public beta publication remains NO-GO" not in text:
        return _check(
            "completion_audit_verdict",
            PASS,
            source=path,
            note="Completion audit says the objective is complete.",
        )
    return _check(
        "completion_audit_verdict",
        BLOCKED_BY_POLICY,
        source=path,
        missing=["GOAL COMPLETE without NO-GO conclusion"],
        note="Completion audit still says the goal is not complete.",
    )


def _external_preflight_check(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    if not payload:
        return _check(
            "external_access_preflight",
            BLOCKED_BY_ACCESS,
            source=path,
            missing=[str(path)],
            note="Run public_beta_external_access_preflight.py before final decision.",
        )
    status = _normalized_status(payload.get("classification"))
    if payload.get("ok") is True and payload.get("safe_to_publish_public_beta") is True and status in RELEASE_READY_STATUSES:
        accepted_skips = [
            str(value)
            for value in payload.get("accepted_skips", [])
            if str(value or "").strip()
        ]
        note = "External access preflight is green."
        if accepted_skips:
            note = (
                "External access preflight is green with accepted operator skips: "
                + ", ".join(accepted_skips)
                + ". Do not claim skipped evidence as verified."
            )
        return _check("external_access_preflight", status, source=path, note=note)

    missing: list[str] = []
    for item in payload.get("checks", []):
        if not isinstance(item, dict) or str(item.get("status") or "") == PASS:
            continue
        for value in item.get("missing", []) or []:
            text = str(value or "").strip()
            if text:
                missing.append(text)
    if status == PASS:
        status = FAIL
        missing.append("ok=true and safe_to_publish_public_beta=true")
    return _check(
        "external_access_preflight",
        status,
        source=path,
        missing=missing,
        note="External access preflight is not safe for public publication.",
    )


def _staged_reachability_check(path: Path) -> dict[str, Any]:
    text = _load_text(path)
    if not text:
        return _check(
            "staged_client_apps_reachability",
            BLOCKED_BY_ACCESS,
            source=path,
            missing=[str(path)],
            note="Run smoke_client_apps.py against staged GitHub Release URLs before publication.",
        )

    required = ["[OK] android.apk_url:", "[OK] windows.exe_url:", "[OK] docs_url:"]
    fail_lines = [line.strip() for line in text.splitlines() if "[FAIL]" in line]
    missing: list[str] = []
    for value in required:
        field_name = value.removeprefix("[OK] ").removesuffix(":")
        if value not in text and not any(field_name in line for line in fail_lines):
            missing.append(value)
    if "[FAIL]" not in text and not missing:
        return _check(
            "staged_client_apps_reachability",
            PASS,
            source=path,
            note="Staged APK/EXE/docs URLs are reachable.",
        )

    missing.extend(fail_lines)
    status = BLOCKED_BY_ACCESS if "NOT_PUBLISHED" in text or "404" in text else FAIL
    return _check(
        "staged_client_apps_reachability",
        status,
        source=path,
        missing=missing,
        note="Staged APK/EXE/docs URLs are not all reachable.",
    )


def _runtime_sync_guard_check(path: Path) -> dict[str, Any]:
    text = _load_text(path)
    if not text:
        return _check(
            "runtime_link_sync_guard",
            BLOCKED_BY_ACCESS,
            source=path,
            missing=[str(path)],
            note="Runtime APP_* sync guard evidence is missing.",
        )

    required = [
        "NO RUNTIME SYNC",
        "No SSH connection, env write, or service restart was performed.",
        "GO evidence file is required for runtime APP_* sync",
        "OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true",
    ]
    missing = [value for value in required if value not in text]
    if missing:
        return _check(
            "runtime_link_sync_guard",
            BLOCKED_BY_ACCESS,
            source=path,
            missing=missing,
            note="Runtime APP_* sync guard evidence is incomplete.",
        )
    return _check(
        "runtime_link_sync_guard",
        PASS,
        source=path,
        note=(
            "Runtime APP_* sync is guarded: dry-run validates values and mutation is blocked without "
            "explicit operator evidence. This check does not authorize runtime APP_* sync."
        ),
    )


def _paid_checkout_evidence_check(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    if not payload:
        return _check(
            "paid_checkout_launch_evidence",
            BLOCKED_BY_ACCESS,
            source=path,
            missing=[str(path)],
            note="Paid checkout launch evidence is missing.",
        )
    status = _normalized_status(payload.get("classification"))
    if payload.get("ok") is True and payload.get("safe_to_enable_paid_checkout") is True and status == PASS:
        return _check("paid_checkout_launch_evidence", PASS, source=path, note="Paid checkout evidence is green.")

    missing: list[str] = []
    for item in payload.get("checks", []):
        if not isinstance(item, dict) or str(item.get("status") or "") == PASS:
            continue
        for value in item.get("missing", []) or []:
            text = str(value or "").strip()
            if text:
                missing.append(text)
    if status == PASS:
        status = FAIL
        missing.append("ok=true and safe_to_enable_paid_checkout=true")
    return _check(
        "paid_checkout_launch_evidence",
        status,
        source=path,
        missing=missing,
        note="Paid checkout must remain unavailable until this evidence is green.",
    )


def _live_email_status_check(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    if not payload:
        return _check(
            "live_email_auth_status",
            BLOCKED_BY_ACCESS,
            source=path,
            missing=[str(path)],
            note="Live email auth status is missing.",
        )
    if (
        payload.get("enabled") is True
        and payload.get("public_enabled") is True
        and payload.get("delivery_configured") is True
        and payload.get("delivery_secret_configured") is True
        and payload.get("debug_echo") is False
    ):
        return _check("live_email_auth_status", PASS, source=path, note="Live email auth is public and delivery-ready.")
    missing = [str(value) for value in payload.get("blocked_reasons", []) if str(value or "").strip()]
    if payload.get("public_enabled") is not True and "public_email_disabled" not in missing:
        missing.append("public_email_disabled")
    if payload.get("delivery_secret_configured") is not True and "delivery_webhook_secret_missing" not in missing:
        missing.append("delivery_webhook_secret_missing")
    return _check(
        "live_email_auth_status",
        BLOCKED_BY_ACCESS,
        source=path,
        missing=missing,
        note="Email auth is not live-public yet.",
    )


def _live_payment_status_check(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    if not payload:
        return _check(
            "live_payment_provider_status",
            BLOCKED_BY_ACCESS,
            source=path,
            missing=[str(path)],
            note="Live payment provider status is missing.",
        )
    provider_codes = _provider_codes_from_payment_payload(payload)
    provider_count = _provider_count_from_payment_payload(payload, provider_codes)
    if (
        payload.get("ok") is True
        and payload.get("blocked") is False
        and provider_codes == ["lavatop"]
        and provider_count == 1
    ):
        return _check("live_payment_provider_status", PASS, source=path, note="Live provider catalog exposes Lava.top only.")

    missing = [str(value) for value in payload.get("blocked_reasons", []) if str(value or "").strip()]
    if provider_codes and provider_codes != ["lavatop"]:
        missing.append(f"expected only lavatop, got {', '.join(provider_codes)}")
    if payload.get("blocked") is not True and provider_count != 1:
        missing.append("provider_count must be 1")
    status = (
        FAIL
        if payload.get("ok") is True and payload.get("blocked") is False
        else BLOCKED_BY_ACCESS if payload.get("blocked") is True or missing else FAIL
    )
    return _check(
        "live_payment_provider_status",
        status,
        source=path,
        missing=missing,
        note="Live paid checkout is not green.",
    )


def _post_deploy_probe_check(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    if not payload:
        return _check(
            "post_deploy_payment_email_probe",
            BLOCKED_BY_ACCESS,
            source=path,
            missing=[str(path)],
            note="Run public_beta_post_deploy_probe.py after deploy before final publication.",
        )

    missing: list[str] = []
    if payload.get("mode") != "public_beta_post_deploy_probe":
        missing.append("mode=public_beta_post_deploy_probe")
    if payload.get("email_public_runtime_config_passed") is not True:
        missing.append("email_public_runtime_config_passed=true")
    if payload.get("email_live_delivery_probe_passed") is not True:
        missing.append("email live delivery proof")
    if payload.get("safe_to_keep_email_public") is not True:
        missing.append("safe_to_keep_email_public=true")
    if payload.get("lavatop_live_invoice_probe_passed") is not True:
        missing.append("Lava.top live invoice proof")

    if not missing:
        return _check(
            "post_deploy_payment_email_probe",
            PASS,
            source=path,
            note="Post-deploy email delivery and Lava.top invoice probes are green.",
        )

    status = _normalized_status(payload.get("classification"), default=BLOCKED_BY_ACCESS)
    if status == PASS:
        status = FAIL
    return _check(
        "post_deploy_payment_email_probe",
        status,
        source=path,
        missing=missing,
        note="Post-deploy payment/email probe is not fully green.",
    )


def _classification(checks: list[dict[str, Any]]) -> str:
    statuses = [_normalized_status(check.get("status")) for check in checks]
    if statuses and all(status == PASS for status in statuses):
        return PASS
    if statuses and all(status in RELEASE_READY_STATUSES for status in statuses):
        return PASS_WITH_ACCEPTED_SKIPS
    return max(statuses, key=lambda status: STATUS_PRECEDENCE.get(status, 0))


def build_report(
    *,
    handoff: Path = DEFAULT_HANDOFF,
    completion_audit: Path = DEFAULT_COMPLETION_AUDIT,
    external_preflight_json: Path = DEFAULT_EXTERNAL_PREFLIGHT_JSON,
    full_gate: Path = DEFAULT_FULL_GATE,
    quick_gate: Path = DEFAULT_QUICK_GATE,
    brain_gate: Path = DEFAULT_BRAIN_GATE,
    paid_checkout_evidence: Path = DEFAULT_PAID_CHECKOUT_EVIDENCE,
    live_email_status: Path = DEFAULT_LIVE_EMAIL_STATUS,
    live_payment_status: Path = DEFAULT_LIVE_PAYMENT_STATUS,
    post_deploy_probe: Path = DEFAULT_POST_DEPLOY_PROBE,
    staged_reachability: Path = DEFAULT_STAGED_REACHABILITY,
    runtime_sync_guard: Path = DEFAULT_RUNTIME_SYNC_GUARD,
) -> dict[str, Any]:
    checks = [
        _markdown_gate_check(
            name="current_origin_full_gate",
            path=Path(full_gate),
            required_phrases=["- Gate set: `default`", "| current-origin check | local default gate set | PASS |"],
            note="Full/default current-origin gate must be green.",
        ),
        _markdown_gate_check(
            name="current_origin_quick_gate",
            path=Path(quick_gate),
            required_phrases=["- Gate set: `quick`", "| current-origin check | local quick gate set | PASS |"],
            note="Latest quick current-origin gate must be green.",
        ),
        _markdown_gate_check(
            name="brain_origin_quick_gate",
            path=Path(brain_gate),
            required_phrases=[
                "- Brain IP supplied: `yes`",
                "| brain-origin check | `scripts/verify_brain_ready.py` plus node predeploy readiness | PASS |",
            ],
            note="Brain-origin runtime/static and node readiness gates must be green.",
        ),
        _handoff_policy_check(Path(handoff)),
        _completion_audit_check(Path(completion_audit)),
        _external_preflight_check(Path(external_preflight_json)),
        _staged_reachability_check(Path(staged_reachability)),
        _runtime_sync_guard_check(Path(runtime_sync_guard)),
        _paid_checkout_evidence_check(Path(paid_checkout_evidence)),
        _live_email_status_check(Path(live_email_status)),
        _live_payment_status_check(Path(live_payment_status)),
        _post_deploy_probe_check(Path(post_deploy_probe)),
    ]
    classification = _classification(checks)
    ok = classification in RELEASE_READY_STATUSES
    return {
        "ok": ok,
        "verdict": GO if ok else NO_GO,
        "classification": classification,
        "mode": "public_beta_launch_decision",
        "safe_to_publish_public_beta": ok,
        "inputs": {
            "handoff": str(handoff),
            "completion_audit": str(completion_audit),
            "external_preflight_json": str(external_preflight_json),
            "full_gate": str(full_gate),
            "quick_gate": str(quick_gate),
            "brain_gate": str(brain_gate),
            "paid_checkout_evidence": str(paid_checkout_evidence),
            "live_email_status": str(live_email_status),
            "live_payment_status": str(live_payment_status),
            "post_deploy_probe": str(post_deploy_probe),
            "staged_reachability": str(staged_reachability),
            "runtime_sync_guard": str(runtime_sync_guard),
        },
        "checks": checks,
        "safe_public_claims": [
            "POKROV готовит ограниченную бета-проверку для Android и Windows вне магазинов.",
            "Статусы current-origin и brain-origin можно цитировать только вместе с точными датированными артефактами проверки.",
            "Email-вход включен по конфигурации; живая доставка писем все еще требует проверки с EMAIL_PROBE_TO.",
            "Android-аудит можно описывать только как операторски подтвержденный, пока нет полного подтверждения из репозитория.",
            "GitHub Releases можно описывать только как предварительные артефакты для проверки, пока ссылки загрузки не авторизованы, не синхронизированы и не прошли живую контрольную проверку.",
            "Оплата и ссылки загрузки остаются закрытыми, пока соответствующие проверки не станут зелеными.",
            "Если внешняя проверка показывает SKIPPED_BY_OPERATOR по RU-origin, публично говорим, что RU-origin не проверялся для этой бета-волны.",
        ],
        "unsafe_public_claims": [
            "Публичная бета уже запущена.",
            "GitHub Releases уже являются рабочим путем загрузки до синхронизации ссылок и живой контрольной проверки.",
            "Оплата Lava.top уже работает публично.",
            "Email-доставка уже доказана живой проверкой почтового ящика до появления подтверждения EMAIL_PROBE_TO.",
            "Публичные загрузки Android/Windows уже доступны через ссылки загрузки.",
            "Полный Android-аудит из репозитория зеленый, когда есть только OPERATOR_ATTESTED.",
            "RU-origin доступность Telegram проверена, когда внешняя проверка говорит SKIPPED_BY_OPERATOR.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate current public-beta evidence into a machine-readable GO/NO-GO launch decision.",
    )
    parser.add_argument("--handoff", default=str(DEFAULT_HANDOFF))
    parser.add_argument("--completion-audit", default=str(DEFAULT_COMPLETION_AUDIT))
    parser.add_argument("--external-preflight-json", default=str(DEFAULT_EXTERNAL_PREFLIGHT_JSON))
    parser.add_argument("--full-gate", default=str(DEFAULT_FULL_GATE))
    parser.add_argument("--quick-gate", default=str(DEFAULT_QUICK_GATE))
    parser.add_argument("--brain-gate", default=str(DEFAULT_BRAIN_GATE))
    parser.add_argument("--paid-checkout-evidence", default=str(DEFAULT_PAID_CHECKOUT_EVIDENCE))
    parser.add_argument("--live-email-status", default=str(DEFAULT_LIVE_EMAIL_STATUS))
    parser.add_argument("--live-payment-status", default=str(DEFAULT_LIVE_PAYMENT_STATUS))
    parser.add_argument("--post-deploy-probe", default=str(DEFAULT_POST_DEPLOY_PROBE))
    parser.add_argument("--staged-reachability", default=str(DEFAULT_STAGED_REACHABILITY))
    parser.add_argument("--runtime-sync-guard", default=str(DEFAULT_RUNTIME_SYNC_GUARD))
    parser.add_argument("--output", default="", help="Optional JSON output path.")
    args = parser.parse_args(argv)

    report = build_report(
        handoff=Path(args.handoff),
        completion_audit=Path(args.completion_audit),
        external_preflight_json=Path(args.external_preflight_json),
        full_gate=Path(args.full_gate),
        quick_gate=Path(args.quick_gate),
        brain_gate=Path(args.brain_gate),
        paid_checkout_evidence=Path(args.paid_checkout_evidence),
        live_email_status=Path(args.live_email_status),
        live_payment_status=Path(args.live_payment_status),
        post_deploy_probe=Path(args.post_deploy_probe),
        staged_reachability=Path(args.staged_reachability),
        runtime_sync_guard=Path(args.runtime_sync_guard),
    )
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
