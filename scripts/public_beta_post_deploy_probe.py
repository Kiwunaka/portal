from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from paid_checkout_launch_evidence_check import build_report as build_paid_evidence_report


PASS = "PASS"
FAIL = "FAIL"
BLOCKED_BY_ACCESS = "BLOCKED_BY_ACCESS"
BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"
EXTERNAL_DEPENDENCY = "EXTERNAL_DEPENDENCY"

DEFAULT_API_BASE_URL = "https://api.pokrov.space"
DEFAULT_READINESS_JSON = Path("docs/audit-artifacts/payment-email-readiness-brain-2026-05-08.json")

RuntimeFetcher = Callable[[str], dict[str, Any]]
CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]

_BRAIN_LIVE_CHECK_NAMES = {
    "email_delivery_verify",
    "email_delivery_reset",
    "email_delivery_payment_access_key",
    "lavatop_live_invoice_creation",
}
_BRAIN_LIVE_CHECK_KEYS = {"name", "status", "missing", "note", "source", "http_status"}


def _offer_env_name(plan_code: str) -> str:
    suffix = "".join(ch if ch.isalnum() else "_" for ch in str(plan_code or "").upper()).strip("_")
    return f"LAVATOP_OFFER_ID_{suffix}" if suffix else "LAVATOP_OFFER_ID"


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "enabled", "available"}


def _env_present(env: Mapping[str, str], name: str) -> bool:
    return bool(str(env.get(name) or "").strip())


def _check(
    name: str,
    status: str,
    *,
    missing: list[str] | None = None,
    note: str = "",
    source: str = "",
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "missing": list(missing or []),
        "note": note,
        "source": source,
    }


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


def _normalized_probe_status(value: object) -> str:
    status = str(value or "").strip().upper()
    return status if status in {PASS, FAIL, BLOCKED_BY_ACCESS, BLOCKED_BY_POLICY, EXTERNAL_DEPENDENCY} else BLOCKED_BY_ACCESS


def _sanitize_brain_live_check(raw_check: Mapping[str, Any]) -> dict[str, Any] | None:
    name = str(raw_check.get("name") or "").strip()
    if name not in _BRAIN_LIVE_CHECK_NAMES:
        return None
    sanitized: dict[str, Any] = {}
    for key in _BRAIN_LIVE_CHECK_KEYS:
        if key not in raw_check:
            continue
        if key == "status":
            sanitized[key] = _normalized_probe_status(raw_check.get(key))
        elif key == "missing":
            values = raw_check.get(key)
            sanitized[key] = [str(value) for value in values] if isinstance(values, list) else []
        elif key == "http_status":
            try:
                sanitized[key] = int(raw_check.get(key) or 0)
            except (TypeError, ValueError):
                continue
        else:
            sanitized[key] = str(raw_check.get(key) or "")
    sanitized.setdefault("name", name)
    sanitized.setdefault("status", BLOCKED_BY_ACCESS)
    sanitized.setdefault("missing", [])
    sanitized.setdefault("note", "Redacted brain-local live probe result.")
    sanitized.setdefault("source", "brain:portal-api")
    return sanitized


def _brain_live_checks(report: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(report, Mapping):
        return {}
    if str(report.get("mode") or "") != "brain_post_deploy_live_probe":
        return {}
    by_name: dict[str, dict[str, Any]] = {}
    raw_checks = report.get("checks")
    if not isinstance(raw_checks, list):
        return by_name
    for raw_check in raw_checks:
        if not isinstance(raw_check, Mapping):
            continue
        sanitized = _sanitize_brain_live_check(raw_check)
        if sanitized is not None:
            by_name[str(sanitized["name"])] = sanitized
    return by_name


def _merge_brain_live_check(local_check: dict[str, Any], brain_by_name: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
    name = str(local_check.get("name") or "")
    brain_check = brain_by_name.get(name)
    if not brain_check:
        return local_check
    if str(brain_check.get("status") or "") == PASS or str(local_check.get("status") or "") != PASS:
        return dict(brain_check)
    return local_check


def _classification(checks: list[dict[str, Any]]) -> str:
    statuses = [str(check.get("status") or "") for check in checks]
    if statuses and all(status == PASS for status in statuses):
        return PASS
    if BLOCKED_BY_POLICY in statuses:
        return BLOCKED_BY_POLICY
    if BLOCKED_BY_ACCESS in statuses:
        return BLOCKED_BY_ACCESS
    if FAIL in statuses:
        return FAIL
    return EXTERNAL_DEPENDENCY


def _runtime_fetcher(api_base_url: str) -> RuntimeFetcher:
    base = str(api_base_url or DEFAULT_API_BASE_URL).rstrip("/")

    def fetch(path: str) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{base}{path}",
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8", errors="replace")
        payload = json.loads(raw or "{}")
        return payload if isinstance(payload, dict) else {}

    return fetch


def _fetch_or_error(fetcher: RuntimeFetcher, path: str) -> dict[str, Any]:
    try:
        return fetcher(path)
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
        return {"_probe_error": type(exc).__name__}


def _email_runtime_check(payload: Mapping[str, Any], *, source: str) -> dict[str, Any]:
    if payload.get("_probe_error"):
        return _check(
            "email_public_runtime_config",
            BLOCKED_BY_ACCESS,
            missing=[str(payload["_probe_error"])],
            note="Could not read live email auth status from the deployed API.",
            source=source,
        )

    missing: list[str] = []
    if not _truthy(payload.get("enabled")):
        missing.append("email auth enabled")
    if not _truthy(payload.get("public_enabled")):
        missing.append("public email auth enabled")
    if not _truthy(payload.get("delivery_url_configured")):
        missing.append("delivery webhook URL configured")
    if not _truthy(payload.get("delivery_secret_configured")):
        missing.append("delivery relay secret configured")
    if _truthy(payload.get("debug_echo")):
        missing.append("EMAIL_AUTH_DEBUG_ECHO=false")

    return _check(
        "email_public_runtime_config",
        PASS if not missing else BLOCKED_BY_ACCESS,
        missing=missing,
        note="Live deployed API email status; does not send email.",
        source=source,
    )


def _provider_name(provider: Mapping[str, Any]) -> str:
    for key in ("provider", "code", "id", "name"):
        value = str(provider.get(key) or "").strip().lower()
        if value:
            return value
    return ""


def _provider_enabled(provider: Mapping[str, Any], *, catalog_enabled: bool = False) -> bool:
    if "enabled" in provider:
        return _truthy(provider.get("enabled"))
    if "available" in provider:
        return _truthy(provider.get("available"))
    return bool(catalog_enabled)


def _payment_provider_block_note(payload: Mapping[str, Any]) -> str:
    texts = payload.get("blocked_reason_texts")
    if isinstance(texts, list):
        text_note = "; ".join(str(item).strip() for item in texts if str(item or "").strip())
        if text_note:
            return text_note

    reasons = payload.get("blocked_reasons")
    if isinstance(reasons, list):
        reason_note = ", ".join(str(item).strip() for item in reasons if str(item or "").strip())
        if reason_note:
            return reason_note

    for key in ("blocked_reason", "reason"):
        value = str(payload.get(key) or "").strip()
        if value:
            return value

    return "paid checkout unavailable"


def _payment_provider_check(payload: Mapping[str, Any], *, source: str) -> dict[str, Any]:
    if payload.get("_probe_error"):
        return _check(
            "payment_provider_catalog",
            BLOCKED_BY_ACCESS,
            missing=[str(payload["_probe_error"])],
            note="Could not read deployed payment provider catalog.",
            source=source,
        )

    raw_providers = payload.get("providers")
    providers = [item for item in raw_providers if isinstance(item, dict)] if isinstance(raw_providers, list) else []
    catalog_enabled = payload.get("ok") is True and payload.get("blocked") is not True
    lava_enabled = any("lava" in _provider_name(item) and _provider_enabled(item, catalog_enabled=catalog_enabled) for item in providers)
    freekassa_enabled = any("freekassa" in _provider_name(item) and _provider_enabled(item, catalog_enabled=catalog_enabled) for item in providers)

    if freekassa_enabled:
        return _check(
            "payment_provider_catalog",
            BLOCKED_BY_POLICY,
            missing=["FreeKassa must not be enabled in the public checkout catalog"],
            note="Paid checkout must stay Lava.top-only for this launch lane.",
            source=source,
        )
    if lava_enabled:
        return _check(
            "payment_provider_catalog",
            PASS,
            note="Live deployed provider catalog exposes enabled Lava.top checkout.",
            source=source,
        )

    return _check(
        "payment_provider_catalog",
        BLOCKED_BY_ACCESS,
        missing=["enabled Lava.top provider catalog"],
        note=_payment_provider_block_note(payload),
        source=source,
    )


def _subprocess_runner(cmd: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )


def _merged_env(env: Mapping[str, str]) -> dict[str, str]:
    merged = dict(os.environ)
    merged.update({name: value for name, value in env.items() if value is not None})
    return merged


def _email_delivery_probe_check(
    *,
    name: str,
    kind: str,
    live: bool,
    env: Mapping[str, str],
    command_runner: Callable[..., subprocess.CompletedProcess[str]],
) -> dict[str, Any]:
    missing: list[str] = []
    if not live:
        missing.append("--live")
    if not _env_present(env, "EMAIL_PROBE_TO"):
        missing.append("EMAIL_PROBE_TO")
    if not (_env_present(env, "EMAIL_DELIVERY_WEBHOOK_URL") or _env_present(env, "EMAIL_AUTH_WEBHOOK_URL")):
        missing.append("EMAIL_DELIVERY_WEBHOOK_URL or EMAIL_AUTH_WEBHOOK_URL")
    if not _env_present(env, "EMAIL_DELIVERY_WEBHOOK_SECRET"):
        missing.append("EMAIL_DELIVERY_WEBHOOK_SECRET")
    if missing:
        return _check(
            name,
            BLOCKED_BY_ACCESS,
            missing=missing,
            note="Live delivery proof is required after deploy; dry-run never sends email.",
            source="scripts/email_delivery_probe.py",
        )

    cmd = [
        sys.executable,
        "scripts/email_delivery_probe.py",
        "--kind",
        kind,
        "--email",
        str(env["EMAIL_PROBE_TO"]),
        "--live",
    ]
    try:
        result = command_runner(cmd, env=_merged_env(env))
    except (OSError, subprocess.SubprocessError, TimeoutError) as exc:
        return _check(
            name,
            BLOCKED_BY_ACCESS,
            missing=[type(exc).__name__],
            note="Live email delivery probe could not complete.",
            source=f"scripts/email_delivery_probe.py --kind {kind} --live",
        )
    return _check(
        name,
        PASS if int(result.returncode) == 0 else BLOCKED_BY_ACCESS,
        missing=[] if int(result.returncode) == 0 else [f"email probe returncode {result.returncode}"],
        note="Live email delivery probe completed without exposing relay secrets.",
        source=f"scripts/email_delivery_probe.py --kind {kind} --live",
    )


def _lavatop_invoice_probe_check(
    *,
    plan_code: str,
    live: bool,
    env: Mapping[str, str],
    command_runner: Callable[..., subprocess.CompletedProcess[str]],
) -> dict[str, Any]:
    offer_name = _offer_env_name(plan_code)
    missing: list[str] = []
    if not live:
        missing.append("--live")
    if not _env_present(env, "LAVATOP_PROBE_EMAIL"):
        missing.append("LAVATOP_PROBE_EMAIL")
    if not _env_present(env, "LAVATOP_API_KEY"):
        missing.append("LAVATOP_API_KEY")
    if not (_env_present(env, offer_name) or _env_present(env, "LAVATOP_OFFER_ID")):
        missing.append(f"{offer_name} or LAVATOP_OFFER_ID")
    if missing:
        return _check(
            "lavatop_live_invoice_creation",
            BLOCKED_BY_ACCESS,
            missing=missing,
            note="Live invoice proof is required after deploy; dry-run never calls Lava.top.",
            source="scripts/lavatop_invoice_probe.py",
        )

    cmd = [
        sys.executable,
        "scripts/lavatop_invoice_probe.py",
        "--plan-code",
        plan_code,
        "--email",
        str(env["LAVATOP_PROBE_EMAIL"]),
        "--live",
    ]
    try:
        result = command_runner(cmd, env=_merged_env(env))
    except (OSError, subprocess.SubprocessError, TimeoutError) as exc:
        return _check(
            "lavatop_live_invoice_creation",
            BLOCKED_BY_ACCESS,
            missing=[type(exc).__name__],
            note="Live Lava.top invoice probe could not complete.",
            source="scripts/lavatop_invoice_probe.py --live",
        )
    return _check(
        "lavatop_live_invoice_creation",
        PASS if int(result.returncode) == 0 else BLOCKED_BY_ACCESS,
        missing=[] if int(result.returncode) == 0 else [f"Lava.top invoice probe returncode {result.returncode}"],
        note="Live Lava.top invoice probe completed without exposing API keys.",
        source="scripts/lavatop_invoice_probe.py --live",
    )


def _paid_evidence_check(
    *,
    readiness_json: Path,
    evidence_json: Path | None,
    paid_evidence_report: Mapping[str, Any] | None,
) -> dict[str, Any]:
    report: Mapping[str, Any] | None = paid_evidence_report
    source = "injected paid evidence report"
    if report is None and evidence_json:
        report = build_paid_evidence_report(readiness_json=readiness_json, evidence_json=evidence_json)
        source = str(evidence_json)
    if report is None:
        return _check(
            "paid_checkout_launch_evidence",
            BLOCKED_BY_ACCESS,
            missing=["--evidence-json"],
            note="Attach the redacted live/sandbox Lava.top evidence JSON before enabling checkout.",
            source="scripts/paid_checkout_launch_evidence_check.py",
        )

    status = PASS if report.get("safe_to_enable_paid_checkout") is True and str(report.get("classification")) == PASS else BLOCKED_BY_ACCESS
    return _check(
        "paid_checkout_launch_evidence",
        status,
        missing=[] if status == PASS else ["paid checkout evidence classification PASS"],
        note="Aggregate paid-checkout evidence status.",
        source=source,
    )


def _redacted_env_inputs(env: Mapping[str, str], *, plan_code: str) -> dict[str, str]:
    names = [
        "EMAIL_PROBE_TO",
        "EMAIL_DELIVERY_WEBHOOK_URL",
        "EMAIL_AUTH_WEBHOOK_URL",
        "EMAIL_DELIVERY_WEBHOOK_SECRET",
        "LAVATOP_PROBE_EMAIL",
        "LAVATOP_API_KEY",
        "LAVATOP_OFFER_ID",
        _offer_env_name(plan_code),
    ]
    return {name: ("present" if _env_present(env, name) else "missing") for name in names}


def build_report(
    *,
    api_base_url: str = DEFAULT_API_BASE_URL,
    env: Mapping[str, str] | None = None,
    live: bool = False,
    runtime_fetcher: RuntimeFetcher | None = None,
    command_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    plan_code: str = "start_99",
    readiness_json: Path = DEFAULT_READINESS_JSON,
    evidence_json: Path | None = None,
    paid_evidence_report: Mapping[str, Any] | None = None,
    brain_live_probe_report: Mapping[str, Any] | None = None,
    brain_live_probe_json: Path | None = None,
) -> dict[str, Any]:
    env = dict(env or os.environ)
    fetcher = runtime_fetcher or _runtime_fetcher(api_base_url)
    runner = command_runner or _subprocess_runner
    email_source = f"{api_base_url.rstrip('/')}/api/auth/email/status"
    providers_source = f"{api_base_url.rstrip('/')}/api/payments/providers"
    if brain_live_probe_report is None and brain_live_probe_json:
        brain_live_probe_report = _load_json(Path(brain_live_probe_json))
    brain_by_name = _brain_live_checks(brain_live_probe_report)

    checks = [
        _email_runtime_check(_fetch_or_error(fetcher, "/api/auth/email/status"), source=email_source),
        _payment_provider_check(_fetch_or_error(fetcher, "/api/payments/providers"), source=providers_source),
        _merge_brain_live_check(
            _email_delivery_probe_check(
                name="email_delivery_verify",
                kind="verify",
                live=live,
                env=env,
                command_runner=runner,
            ),
            brain_by_name,
        ),
        _merge_brain_live_check(
            _email_delivery_probe_check(
                name="email_delivery_reset",
                kind="reset",
                live=live,
                env=env,
                command_runner=runner,
            ),
            brain_by_name,
        ),
        _merge_brain_live_check(
            _email_delivery_probe_check(
                name="email_delivery_payment_access_key",
                kind="payment_access_key",
                live=live,
                env=env,
                command_runner=runner,
            ),
            brain_by_name,
        ),
        _merge_brain_live_check(
            _lavatop_invoice_probe_check(
                plan_code=plan_code,
                live=live,
                env=env,
                command_runner=runner,
            ),
            brain_by_name,
        ),
        _paid_evidence_check(
            readiness_json=Path(readiness_json),
            evidence_json=Path(evidence_json) if evidence_json else None,
            paid_evidence_report=paid_evidence_report,
        ),
    ]
    by_name = {check["name"]: check for check in checks}
    classification = _classification(checks)
    email_public_runtime_config_passed = by_name["email_public_runtime_config"]["status"] == PASS
    email_live_delivery_probe_passed = (
        by_name["email_delivery_verify"]["status"] == PASS
        and by_name["email_delivery_reset"]["status"] == PASS
    )
    lavatop_live_invoice_probe_passed = by_name["lavatop_live_invoice_creation"]["status"] == PASS
    safe_to_keep_email_public = email_public_runtime_config_passed
    safe_to_enable_paid_checkout = (
        email_public_runtime_config_passed
        and by_name["payment_provider_catalog"]["status"] == PASS
        and by_name["paid_checkout_launch_evidence"]["status"] == PASS
    )
    return {
        "ok": classification == PASS,
        "classification": classification,
        "mode": "public_beta_post_deploy_probe",
        "live": bool(live),
        "email_public_runtime_config_passed": email_public_runtime_config_passed,
        "email_live_delivery_probe_passed": email_live_delivery_probe_passed,
        "lavatop_live_invoice_probe_passed": lavatop_live_invoice_probe_passed,
        "post_deploy_probe_modes": {
            "email_public_runtime": "PASS" if email_public_runtime_config_passed else BLOCKED_BY_ACCESS,
            "email_live_delivery": "PASS" if email_live_delivery_probe_passed else BLOCKED_BY_ACCESS,
            "lavatop_invoice": "PASS" if lavatop_live_invoice_probe_passed else BLOCKED_BY_ACCESS,
        },
        "safe_to_keep_email_public": safe_to_keep_email_public,
        "safe_to_enable_paid_checkout": safe_to_enable_paid_checkout,
        "inputs": {
            "api_base_url": api_base_url,
            "plan_code": plan_code,
            "readiness_json": str(readiness_json),
            "evidence_json": str(evidence_json) if evidence_json else "",
            "brain_live_probe_json": str(brain_live_probe_json) if brain_live_probe_json else "",
            "env": _redacted_env_inputs(env, plan_code=plan_code),
        },
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the redacted public-beta post-deploy payment/email probe bundle.",
    )
    parser.add_argument("--api-base-url", default=DEFAULT_API_BASE_URL)
    parser.add_argument("--plan-code", default="start_99")
    parser.add_argument("--readiness-json", default=str(DEFAULT_READINESS_JSON))
    parser.add_argument("--evidence-json", default="")
    parser.add_argument(
        "--brain-live-probe-json",
        default="",
        help="Optional redacted output from brain_payment_email_readiness.py --post-deploy-live.",
    )
    parser.add_argument("--output", default="")
    parser.add_argument("--live", action="store_true", help="Send email probes and create a Lava.top probe invoice when env is present.")
    parser.add_argument("--offline", action="store_true", help="Skip deployed API status reads; useful for dry operator shells.")
    args = parser.parse_args(argv)

    report = build_report(
        api_base_url=args.api_base_url,
        env=os.environ,
        live=bool(args.live),
        runtime_fetcher=(lambda _path: {}) if args.offline else None,
        plan_code=args.plan_code,
        readiness_json=Path(args.readiness_json),
        evidence_json=Path(args.evidence_json) if str(args.evidence_json or "").strip() else None,
        brain_live_probe_json=Path(args.brain_live_probe_json) if str(args.brain_live_probe_json or "").strip() else None,
    )
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
