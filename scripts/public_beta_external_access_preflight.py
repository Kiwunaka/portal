from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping


PASS = "PASS"
PASS_WITH_ACCEPTED_SKIPS = "PASS_WITH_ACCEPTED_SKIPS"
FAIL = "FAIL"
BLOCKED_BY_ACCESS = "BLOCKED_BY_ACCESS"
BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"
EXTERNAL_DEPENDENCY = "EXTERNAL_DEPENDENCY"
SKIPPED_BY_OPERATOR = "SKIPPED_BY_OPERATOR"
OPERATOR_ATTESTED = "OPERATOR_ATTESTED"

DEFAULT_HANDOFF = Path("docs/audit-artifacts/public-beta-handoff-2026-05-08.md")
DEFAULT_CLIENT_RELEASE_HANDOFF = Path("../POKROV-app/artifacts/releases/release-handoff.json")
DEFAULT_STAGED_APPS_JSON = DEFAULT_CLIENT_RELEASE_HANDOFF
DEFAULT_RU_ORIGIN_JSON = Path("docs/audit-artifacts/ru-origin-mini-2026-05-07.json")
DEFAULT_RU_ORIGIN_SKIP_EVIDENCE = Path("docs/audit-artifacts/ru-origin-skip-accepted-2026-05-08.md")
DEFAULT_CLIENT_BUILD_EVIDENCE = Path("docs/audit-artifacts/client-build-evidence-2026-05-07.md")
DEFAULT_ANDROID_AUDIT_VALIDATION = Path("docs/audit-artifacts/android-physical-audit-evidence-validation-2026-05-08.json")
DEFAULT_ANDROID_OPERATOR_ATTESTATION = Path("docs/audit-artifacts/android-physical-audit-operator-note-2026-05-08.md")
DEFAULT_RUNTIME_APP_DOWNLOAD_SMOKE = Path("docs/audit-artifacts/runtime-app-download-smoke-brain-2026-05-09-docs-default.json")
DEFAULT_ARTIFACT_STAGING_AUTHORIZATION = Path(
    "docs/audit-artifacts/public-beta-artifact-staging-authorization-2026-05-08.md"
)

RELEASE_READY_CLASSIFICATIONS = {PASS, PASS_WITH_ACCEPTED_SKIPS}
RELEASE_READY_CHECK_STATUSES = {PASS, SKIPPED_BY_OPERATOR, OPERATOR_ATTESTED}
RUNTIME_APP_DOWNLOAD_SMOKE_CHECKS = {
    "android_physical_audit",
    "runtime_app_download_smoke_env",
    "github_release_auth",
    "ru_origin_probe_evidence",
    "windows_signing_or_unsigned_risk",
    "staged_client_apps_payload",
}
RUNTIME_SYNC_MISSING_LABELS = {
    "android release URL is missing": "runtime APP_ANDROID_APK_URL is not synced",
    "windows release URL is missing": "runtime APP_WINDOWS_EXE_URL is not synced",
    "docs_url is missing": "runtime APP_DOCS_URL is not synced",
}


def _env_present(env: Mapping[str, str], name: str) -> bool:
    return bool(str(env.get(name) or "").strip())


def _env_truthy(env: Mapping[str, str], name: str) -> bool:
    return str(env.get(name) or "").strip().lower() in {"1", "true", "yes", "y", "accepted"}


def _check(name: str, status: str, *, missing: list[str] | None = None, note: str = "", source: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "missing": list(missing or []),
        "note": note,
        "source": source,
    }


def _env_check(env: Mapping[str, str], name: str, *, check_name: str, note: str) -> dict[str, Any]:
    return _check(
        check_name,
        PASS if _env_present(env, name) else BLOCKED_BY_ACCESS,
        missing=[] if _env_present(env, name) else [name],
        note=note,
        source="environment",
    )


def _runtime_sync_missing_label(value: object) -> str:
    text = str(value or "").strip()
    return RUNTIME_SYNC_MISSING_LABELS.get(text, text)


def _runtime_app_download_smoke_check(env: Mapping[str, str], path: Path) -> dict[str, Any]:
    if _env_present(env, "TELEGRAM_INIT_DATA"):
        return _check(
            "runtime_app_download_smoke_env",
            PASS,
            note="TELEGRAM_INIT_DATA is present for live /api/client/apps smoke; raw initData must stay env-only.",
            source="environment",
        )

    payload = _load_json(path)
    if str(payload.get("mode") or "") != "brain_runtime_app_download_smoke":
        return _check(
            "runtime_app_download_smoke_env",
            BLOCKED_BY_ACCESS,
            missing=["TELEGRAM_INIT_DATA", str(path)],
            note="Needed for live /api/client/apps smoke. Use env-only Telegram initData or the brain-local signed smoke artifact.",
            source=str(path),
        )

    checks = {str(check.get("name") or ""): check for check in payload.get("checks", []) if isinstance(check, Mapping)}
    signed_auth = checks.get("api_client_apps_signed_init_data", {})
    release_handoff = checks.get("runtime_client_apps_release_handoff", {})
    if payload.get("runtime_app_download_smoke_passed") is True:
        return _check(
            "runtime_app_download_smoke_env",
            PASS,
            note="Brain-local signed initData smoke passed without returning BOT_TOKEN or raw initData.",
            source=str(path),
        )

    missing: list[str] = []
    if str(signed_auth.get("status") or "") != PASS:
        missing.append("brain signed initData /api/client/apps smoke PASS")
    release_missing = release_handoff.get("missing")
    if isinstance(release_missing, list):
        missing.extend(_runtime_sync_missing_label(item) for item in release_missing if str(item).strip())
    if (
        str(signed_auth.get("status") or "") == PASS
        and any(
            item.startswith("runtime APP_") and item.endswith("is not synced")
            for item in missing
        )
    ):
        missing.insert(0, "runtime APP_* sync approval")
    if not missing:
        missing.append("runtime_app_download_smoke_passed=true")
    return _check(
        "runtime_app_download_smoke_env",
        BLOCKED_BY_ACCESS,
        missing=missing,
        note="Brain-local signed initData reached /api/client/apps, but live runtime APP_* links are not synced yet.",
        source=str(path),
    )


def _android_operator_attestation_check(env: Mapping[str, str], path: Path) -> tuple[bool, list[str], str, str]:
    if _env_truthy(env, "ANDROID_PHYSICAL_AUDIT_OPERATOR_OK"):
        return (
            True,
            [],
            "environment",
            "Operator attests that the physical Android release-build localhost/control-surface audit passed. Public claims must state operator-attested evidence, not repo-validated raw JSON.",
        )

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return False, [str(path)], str(path), "No Android physical audit operator attestation is attached."

    missing: list[str] = []
    if "ANDROID_PHYSICAL_AUDIT_OPERATOR_OK=true" not in text:
        missing.append("ANDROID_PHYSICAL_AUDIT_OPERATOR_OK=true")
    if "ANDROID_PHYSICAL_AUDIT_SCOPE=physical_release_build_localhost_control_surface" not in text:
        missing.append("ANDROID_PHYSICAL_AUDIT_SCOPE=physical_release_build_localhost_control_surface")
    if "ANDROID_PHYSICAL_AUDIT_PUBLIC_CLAIMS_MUST_STATE_OPERATOR_ATTESTED=true" not in text:
        missing.append("ANDROID_PHYSICAL_AUDIT_PUBLIC_CLAIMS_MUST_STATE_OPERATOR_ATTESTED=true")
    if missing:
        return False, missing, str(path), "Android physical audit operator attestation is incomplete."
    return (
        True,
        [],
        str(path),
        "Operator attestation is attached. State Android physical audit evidence as operator-attested unless raw repo validation is also PASS.",
    )


def _android_physical_audit_check(env: Mapping[str, str], validation_path: Path, operator_attestation: Path) -> dict[str, Any]:
    if _env_present(env, "ANDROID_AUDIT_SERIAL"):
        return _check(
            "android_physical_audit",
            PASS,
            note="ANDROID_AUDIT_SERIAL is present for a fresh physical release-build localhost/control-surface audit run.",
            source="environment",
        )

    payload = _load_json(validation_path)
    if payload.get("ok") is True and str(payload.get("classification") or "") == PASS:
        return _check(
            "android_physical_audit",
            PASS,
            note="Retained Android physical audit validation is PASS.",
            source=str(validation_path),
        )

    attested, attestation_missing, attestation_source, attestation_note = _android_operator_attestation_check(
        env,
        operator_attestation,
    )
    if attested:
        return _check(
            "android_physical_audit",
            OPERATOR_ATTESTED,
            note=attestation_note,
            source=attestation_source,
        )

    missing = payload.get("missing") if isinstance(payload.get("missing"), list) else []
    if missing:
        missing = list(missing) + attestation_missing
    return _check(
        "android_physical_audit",
        BLOCKED_BY_ACCESS,
        missing=missing or ["ANDROID_AUDIT_SERIAL, PASS android physical audit validation, or complete operator attestation"],
        note="Needed to prove the physical release-build localhost/control-surface audit.",
        source=str(validation_path) if payload else "environment",
    )


def _gh_cli_authenticated() -> bool:
    if not shutil.which("gh"):
        return False
    try:
        proc = subprocess.run(
            ["gh", "auth", "status"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def _github_release_auth_check(env: Mapping[str, str], *, gh_authenticated: bool) -> dict[str, Any]:
    has_env_token = _env_present(env, "GITHUB_TOKEN") or _env_present(env, "GH_TOKEN")
    if has_env_token or gh_authenticated:
        source = "environment" if has_env_token else "gh_cli_keyring"
        note = "Needed only for guarded GitHub Release upload execution."
        if gh_authenticated and not has_env_token:
            note = "Authenticated GitHub CLI is available for the guarded gh release workflow."
        return _check(
            "github_release_auth",
            PASS,
            note=note,
            source=source,
        )
    return _check(
        "github_release_auth",
        BLOCKED_BY_ACCESS,
        missing=["GITHUB_TOKEN, GH_TOKEN, or authenticated gh CLI"],
        note="Needed only for guarded GitHub Release upload execution.",
        source="environment_or_gh_cli",
    )


def _github_release_url(value: object, *, suffix: str) -> bool:
    text = str(value or "").strip()
    return (
        text.startswith("https://github.com/")
        and "/releases/download/" in text
        and text.lower().endswith(suffix.lower())
    )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _normalize_staged_apps_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if "downloads" not in payload and "runtime_env" not in payload:
        return dict(payload)

    downloads = payload.get("downloads", {}) if isinstance(payload.get("downloads"), Mapping) else {}
    android = downloads.get("android", {}) if isinstance(downloads.get("android"), Mapping) else {}
    windows = downloads.get("windows", {}) if isinstance(downloads.get("windows"), Mapping) else {}
    runtime_env = payload.get("runtime_env", {}) if isinstance(payload.get("runtime_env"), Mapping) else {}

    def _first(*values: object) -> str:
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
        return ""

    return {
        "android": {
            "play_url": _first(android.get("play_url"), runtime_env.get("APP_ANDROID_PLAY_URL")),
            "apk_url": _first(android.get("apk_url"), runtime_env.get("APP_ANDROID_APK_URL")),
            "mirror_url": _first(android.get("mirror_url"), runtime_env.get("APP_ANDROID_MIRROR_URL")),
        },
        "windows": {
            "exe_url": _first(windows.get("exe_url"), runtime_env.get("APP_WINDOWS_EXE_URL")),
            "mirror_url": _first(windows.get("mirror_url"), runtime_env.get("APP_WINDOWS_MIRROR_URL")),
        },
        "docs_url": _first(downloads.get("docs_url"), payload.get("docs_url"), runtime_env.get("APP_DOCS_URL")),
    }


def _staged_apps_check(path: Path) -> dict[str, Any]:
    payload = _normalize_staged_apps_payload(_load_json(path))
    if not payload:
        return _check(
            "staged_client_apps_payload",
            BLOCKED_BY_ACCESS,
            missing=[str(path)],
            note="Required before artifact-staging URL policy and reachability smokes.",
            source=str(path),
        )

    android = payload.get("android") if isinstance(payload.get("android"), dict) else {}
    windows = payload.get("windows") if isinstance(payload.get("windows"), dict) else {}
    docs_url = str(payload.get("docs_url") or "").strip()
    missing: list[str] = []
    if str(android.get("play_url") or "").strip():
        missing.append("android.play_url must stay empty for outside-store beta")
    if not _github_release_url(android.get("apk_url"), suffix=".apk"):
        missing.append("android.apk_url GitHub Releases .apk")
    if not _github_release_url(windows.get("exe_url"), suffix=".exe"):
        missing.append("windows.exe_url GitHub Releases .exe")
    if not docs_url.startswith("https://pokrov.space/install/"):
        missing.append("docs_url under https://pokrov.space/install/")
    return _check(
        "staged_client_apps_payload",
        BLOCKED_BY_ACCESS if missing else PASS,
        missing=missing,
        note="Validates candidate /api/client/apps shape without probing URL reachability.",
        source=str(path),
    )


def _has_artifact_staging_authorization(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return False
    required_markers = (
        "ARTIFACT STAGING GO FOR RUNTIME SMOKE",
        "NON-URL P0 GATES GREEN FOR ARTIFACT STAGING",
        "ONLY REMAINING P0 GATE: RUNTIME APP-DOWNLOAD URL SMOKE",
        "NO RUNTIME SYNC OR ANNOUNCEMENT",
    )
    return all(marker in text for marker in required_markers)


def _handoff_policy_check(path: Path, *, artifact_staging_authorization: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return _check(
            "public_beta_handoff_policy",
            BLOCKED_BY_POLICY,
            missing=[str(path)],
            note="A dated release handoff is required before any public publication.",
            source=str(path),
        )
    has_public_go = "GO for public beta publication" in text and "NO-GO" not in text
    has_staging_go = (
        "ARTIFACT STAGING GO FOR RUNTIME SMOKE" in text
        and "NO RUNTIME SYNC OR ANNOUNCEMENT" in text
    )
    staging_auth_exists = _has_artifact_staging_authorization(artifact_staging_authorization)
    if has_public_go:
        note = "Handoff allows public beta publication if all other gates are still green."
        status = PASS
        missing: list[str] = []
    elif has_staging_go:
        note = "Handoff itself allows artifact staging only; runtime sync and announcement remain blocked."
        status = BLOCKED_BY_POLICY
        missing = ["GO handoff for public publication"]
    elif staging_auth_exists:
        note = "Separate artifact-staging authorization is attached; public publication, runtime sync, and announcement remain blocked."
        status = BLOCKED_BY_POLICY
        missing = ["GO handoff for public publication"]
    else:
        note = "Current handoff does not authorize public publication or artifact staging."
        status = BLOCKED_BY_POLICY
        missing = ["GO handoff or artifact-staging authorization markers"]
    return _check("public_beta_handoff_policy", status, missing=missing, note=note, source=str(path))


def _ru_origin_skip_check(env: Mapping[str, str], path: Path) -> tuple[bool, list[str], str, str]:
    if _env_truthy(env, "RU_ORIGIN_SKIP_ACCEPTED"):
        return (
            True,
            [],
            "environment",
            "Operator accepted skipping RU-origin readiness for this beta pass. Do not claim RU-origin readiness.",
        )

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return False, [str(path)], str(path), "No operator skip evidence is attached."

    missing: list[str] = []
    if "RU_ORIGIN_SKIP_ACCEPTED=true" not in text:
        missing.append("RU_ORIGIN_SKIP_ACCEPTED=true")
    if "RU_ORIGIN_PUBLIC_CLAIMS_MUST_STATE_UNVERIFIED=true" not in text:
        missing.append("RU_ORIGIN_PUBLIC_CLAIMS_MUST_STATE_UNVERIFIED=true")
    if missing:
        return False, missing, str(path), "RU-origin skip evidence is incomplete."
    return (
        True,
        [],
        str(path),
        "Operator skip evidence is attached. Do not claim RU-origin readiness; state that RU-origin was not verified.",
    )


def _ru_origin_check(path: Path, *, env: Mapping[str, str], skip_evidence: Path) -> dict[str, Any]:
    payload = _load_json(path)
    skip_accepted, skip_missing, skip_source, skip_note = _ru_origin_skip_check(env, skip_evidence)

    if not payload:
        if skip_accepted:
            return _check(
                "ru_origin_probe_evidence",
                SKIPPED_BY_OPERATOR,
                note=skip_note,
                source=skip_source,
            )
        return _check(
            "ru_origin_probe_evidence",
            BLOCKED_BY_ACCESS,
            missing=skip_missing if skip_missing != [str(skip_evidence)] else [str(path), str(skip_evidence)],
            note="A fresh redacted RU-origin probe report is required before publication.",
            source=str(path),
        )

    raw_status = str(payload.get("status") or "").strip().upper()
    raw_classification = str(payload.get("classification") or "").strip()
    ok = bool(payload.get("ok")) or raw_status in {"PASS", "OK"}
    if ok:
        status = PASS
        missing: list[str] = []
        note = "RU-origin report says POKROV and Telegram reachability passed."
    elif skip_accepted:
        status = SKIPPED_BY_OPERATOR
        missing = []
        note = skip_note
    else:
        status = FAIL
        missing = skip_missing or ["RU-origin Telegram reachability PASS"]
        note = raw_classification or "RU-origin report is not PASS."
    return _check(
        "ru_origin_probe_evidence",
        status,
        missing=missing,
        note=note,
        source=skip_source if status == SKIPPED_BY_OPERATOR else str(path),
    )


def _windows_signing_check(env: Mapping[str, str], path: Path) -> dict[str, Any]:
    if _env_present(env, "WINDOWS_TRUSTED_SIGNING_CONFIRMED"):
        return _check(
            "windows_signing_or_unsigned_risk",
            PASS,
            note="Trusted Windows signing is explicitly confirmed in the current shell.",
            source="environment",
        )
    if _env_present(env, "WINDOWS_UNSIGNED_BETA_RISK_ACCEPTED"):
        return _check(
            "windows_signing_or_unsigned_risk",
            PASS,
            note="Unsigned Windows beta risk posture is explicitly accepted for this release attempt.",
            source="environment",
        )
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return _check(
            "windows_signing_or_unsigned_risk",
            BLOCKED_BY_ACCESS,
            missing=[str(path)],
            note="Windows signing or unsigned-risk evidence file is required.",
            source=str(path),
        )

    if "Authenticode: `Valid`" in text or "Authenticode: Valid" in text or "Status: Valid" in text:
        return _check(
            "windows_signing_or_unsigned_risk",
            PASS,
            note="Client build evidence reports a valid Windows signature.",
            source=str(path),
        )
    if (
        "Unsigned beta risk accepted: `Accepted`" in text
        or "Unsigned beta risk: `Accepted`" in text
        or "WINDOWS_UNSIGNED_BETA_RISK_ACCEPTED=true" in text
    ):
        return _check(
            "windows_signing_or_unsigned_risk",
            PASS,
            note="Unsigned Windows beta risk posture is explicitly accepted in retained client-build evidence.",
            source=str(path),
        )
    return _check(
        "windows_signing_or_unsigned_risk",
        EXTERNAL_DEPENDENCY,
        missing=["trusted Windows signing evidence or WINDOWS_UNSIGNED_BETA_RISK_ACCEPTED"],
        note="Current Windows EXE evidence is unsigned or does not prove a trusted signature.",
        source=str(path),
    )


def _classification(checks: list[dict[str, Any]]) -> str:
    statuses = [str(check.get("status") or "") for check in checks]
    if statuses and all(status == PASS for status in statuses):
        return PASS
    if statuses and all(status in RELEASE_READY_CHECK_STATUSES for status in statuses):
        return PASS_WITH_ACCEPTED_SKIPS
    if BLOCKED_BY_ACCESS in statuses:
        return BLOCKED_BY_ACCESS
    if FAIL in statuses:
        return FAIL
    if EXTERNAL_DEPENDENCY in statuses:
        return EXTERNAL_DEPENDENCY
    return BLOCKED_BY_POLICY


def _check_ready(checks_by_name: Mapping[str, dict[str, Any]], name: str) -> bool:
    return str(checks_by_name.get(name, {}).get("status") or "") in RELEASE_READY_CHECK_STATUSES


def build_report(
    *,
    env: Mapping[str, str] | None = None,
    handoff_path: Path = DEFAULT_HANDOFF,
    staged_apps_json: Path = DEFAULT_STAGED_APPS_JSON,
    ru_origin_json: Path = DEFAULT_RU_ORIGIN_JSON,
    ru_origin_skip_evidence: Path = DEFAULT_RU_ORIGIN_SKIP_EVIDENCE,
    client_build_evidence: Path = DEFAULT_CLIENT_BUILD_EVIDENCE,
    android_audit_validation: Path = DEFAULT_ANDROID_AUDIT_VALIDATION,
    android_operator_attestation: Path = DEFAULT_ANDROID_OPERATOR_ATTESTATION,
    runtime_app_download_smoke: Path = DEFAULT_RUNTIME_APP_DOWNLOAD_SMOKE,
    artifact_staging_authorization: Path = DEFAULT_ARTIFACT_STAGING_AUTHORIZATION,
    gh_authenticated: bool = False,
) -> dict[str, Any]:
    source = env if env is not None else os.environ
    checks = [
        _android_physical_audit_check(
            source,
            Path(android_audit_validation),
            Path(android_operator_attestation),
        ),
        _runtime_app_download_smoke_check(source, Path(runtime_app_download_smoke)),
        _github_release_auth_check(source, gh_authenticated=gh_authenticated),
        _env_check(
            source,
            "EMAIL_PROBE_TO",
            check_name="email_live_probe_env",
            note="Needed for live verify/reset/paid-access-key delivery probes.",
        ),
        _env_check(
            source,
            "LAVATOP_PROBE_EMAIL",
            check_name="lavatop_live_probe_env",
            note="Needed for live Lava.top invoice probe evidence.",
        ),
        _ru_origin_check(Path(ru_origin_json), env=source, skip_evidence=Path(ru_origin_skip_evidence)),
        _windows_signing_check(source, Path(client_build_evidence)),
        _staged_apps_check(Path(staged_apps_json)),
        _handoff_policy_check(
            Path(handoff_path),
            artifact_staging_authorization=Path(artifact_staging_authorization),
        ),
    ]
    classification = _classification(checks)
    checks_by_name = {str(check.get("name") or ""): check for check in checks}
    handoff_ok = next(check for check in checks if check["name"] == "public_beta_handoff_policy")["status"] == PASS
    env_and_payload_ok = all(
        check["status"] in RELEASE_READY_CHECK_STATUSES
        for check in checks
        if check["name"] != "public_beta_handoff_policy"
    )
    ready_to_run_runtime_app_download_smoke = all(
        _check_ready(checks_by_name, name) for name in RUNTIME_APP_DOWNLOAD_SMOKE_CHECKS
    )
    ready_to_run_email_post_deploy_probe = _check_ready(checks_by_name, "email_live_probe_env")
    ready_to_run_lavatop_post_deploy_probe = _check_ready(checks_by_name, "lavatop_live_probe_env")
    accepted_skips = [check["name"] for check in checks if check["status"] == SKIPPED_BY_OPERATOR]
    accepted_operator_attestations = [check["name"] for check in checks if check["status"] == OPERATOR_ATTESTED]
    return {
        "ok": classification in RELEASE_READY_CLASSIFICATIONS,
        "classification": classification,
        "mode": "public_beta_external_access_preflight",
        "safe_to_publish_public_beta": classification in RELEASE_READY_CLASSIFICATIONS and handoff_ok,
        "ready_to_run_access_gated_smokes": env_and_payload_ok,
        "ready_to_run_runtime_app_download_smoke": ready_to_run_runtime_app_download_smoke,
        "ready_to_run_email_post_deploy_probe": ready_to_run_email_post_deploy_probe,
        "ready_to_run_lavatop_post_deploy_probe": ready_to_run_lavatop_post_deploy_probe,
        "post_deploy_probe_modes": {
            "email_public_probe": "READY" if ready_to_run_email_post_deploy_probe else BLOCKED_BY_ACCESS,
            "lavatop_invoice_probe": "READY" if ready_to_run_lavatop_post_deploy_probe else BLOCKED_BY_ACCESS,
            "combined_payment_email_probe": "READY"
            if ready_to_run_email_post_deploy_probe and ready_to_run_lavatop_post_deploy_probe
            else BLOCKED_BY_ACCESS,
        },
        "accepted_skips": accepted_skips,
        "accepted_operator_attestations": accepted_operator_attestations,
        "public_claim_guardrails": [
            "Не заявлять готовность RU-origin, если ru_origin_probe_evidence имеет статус SKIPPED_BY_OPERATOR.",
            "Если RU-origin пропущен, публично можно говорить только, что RU-origin не проверялся в этой бета-волне.",
            "Если Android physical audit имеет статус OPERATOR_ATTESTED, в публичных и релизных текстах можно говорить только об операторском подтверждении; не заявлять raw repo validation.",
            "Email-доставку можно проверять после деплоя независимо от подтверждения Lava.top invoice.",
            "Проверка Lava.top invoice не считается запуском платной оплаты без подтверждения webhook, replay/idempotency, failure и reconciliation.",
        ],
        "inputs": {
            "handoff_path": str(handoff_path),
            "staged_apps_json": str(staged_apps_json),
            "ru_origin_json": str(ru_origin_json),
            "ru_origin_skip_evidence": str(ru_origin_skip_evidence),
            "client_build_evidence": str(client_build_evidence),
            "android_audit_validation": str(android_audit_validation),
            "android_operator_attestation": str(android_operator_attestation),
            "runtime_app_download_smoke": str(runtime_app_download_smoke),
            "artifact_staging_authorization": str(artifact_staging_authorization),
        },
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Redacted preflight for public-beta external access inputs; does not publish, deploy, send email, or call payment APIs.",
    )
    parser.add_argument("--handoff", default=str(DEFAULT_HANDOFF))
    parser.add_argument("--staged-apps-json", default=str(DEFAULT_STAGED_APPS_JSON))
    parser.add_argument("--ru-origin-json", default=str(DEFAULT_RU_ORIGIN_JSON))
    parser.add_argument("--ru-origin-skip-evidence", default=str(DEFAULT_RU_ORIGIN_SKIP_EVIDENCE))
    parser.add_argument("--client-build-evidence", default=str(DEFAULT_CLIENT_BUILD_EVIDENCE))
    parser.add_argument("--android-audit-validation", default=str(DEFAULT_ANDROID_AUDIT_VALIDATION))
    parser.add_argument("--android-operator-attestation", default=str(DEFAULT_ANDROID_OPERATOR_ATTESTATION))
    parser.add_argument("--runtime-app-download-smoke", default=str(DEFAULT_RUNTIME_APP_DOWNLOAD_SMOKE))
    parser.add_argument("--artifact-staging-authorization", default=str(DEFAULT_ARTIFACT_STAGING_AUTHORIZATION))
    parser.add_argument("--output", default="", help="Optional JSON output path.")
    args = parser.parse_args(argv)

    report = build_report(
        env=os.environ,
        handoff_path=Path(args.handoff),
        staged_apps_json=Path(args.staged_apps_json),
        ru_origin_json=Path(args.ru_origin_json),
        ru_origin_skip_evidence=Path(args.ru_origin_skip_evidence),
        client_build_evidence=Path(args.client_build_evidence),
        android_audit_validation=Path(args.android_audit_validation),
        android_operator_attestation=Path(args.android_operator_attestation),
        runtime_app_download_smoke=Path(args.runtime_app_download_smoke),
        artifact_staging_authorization=Path(args.artifact_staging_authorization),
        gh_authenticated=_gh_cli_authenticated(),
    )
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
