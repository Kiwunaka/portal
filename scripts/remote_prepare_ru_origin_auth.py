#!/usr/bin/env python3
"""Guarded PLAN/APPLY/ROLLBACK for the RU-origin internal HMAC registry."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

try:
    import remote_apply_ru_bridge_relay as relay
    import remote_install_owned_smart_dns_lab as remote_support
    import internal_hmac_client
    from node_access import DEFAULT_PASSWORDS, connect_node
except ImportError:  # pragma: no cover - package import for tests
    from . import internal_hmac_client
    from . import remote_apply_ru_bridge_relay as relay
    from . import remote_install_owned_smart_dns_lab as remote_support
    from .node_access import DEFAULT_PASSWORDS, connect_node

# internal_hmac_client exposes the Portal package for its own dependency import.
# Keep this script directory first so later standalone ops-script imports cannot
# accidentally resolve portal_bot/ssh_host_keys.py as scripts/ssh_host_keys.py.
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR in sys.path:
    sys.path.remove(_SCRIPT_DIR)
sys.path.insert(0, _SCRIPT_DIR)


REPORT_SCHEMA = "pokrov-ru-origin-auth-remote-operation-v1"
RECEIPT_SCHEMA = "pokrov-ru-origin-auth-receipt-v1"
KEY_ID = "ru-mini-v1"
SUBJECT = "mini"
SCOPES = ("ru_probe:heartbeat", "ru_probe:ingest", "ru_probe:manifest")
ORIGINS = ("ru",)
REGISTRY_PATH = "/etc/pokrov/internal-hmac-keys.json"
DROPIN_PATH = "/etc/systemd/system/portal-api.service.d/40-pokrov-internal-hmac.conf"
RECEIPT_ROOT = "/root/pokrov-ru-origin-auth-receipts"
STAGE_ROOT = "/root/pokrov-ru-origin-auth-staging"
API_BASE_URL = "https://api.pokrov.space"
MANIFEST_PATH = "/api/internal/probes/ru-origin/manifest"
MANIFEST_ATTEMPTS = 10
MANIFEST_TIMEOUT_SECONDS = 5
MANIFEST_RETRY_SECONDS = 1.5
SAFE_RECEIPT_RE = re.compile(r"[0-9]{8}T[0-9]{6}Z-[0-9]+\Z")


class RuOriginAuthError(RuntimeError):
    """Raised when the guarded auth operation cannot prove its contract."""


def _q(value: str) -> str:
    return shlex.quote(str(value))


def _release_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{os.getpid()}"


def _receipt_id(value: str) -> str:
    normalized = str(value or "").strip()
    if SAFE_RECEIPT_RE.fullmatch(normalized) is None:
        raise RuOriginAuthError("receipt_id_invalid")
    return normalized


def _secret(path_value: str | Path) -> bytes:
    try:
        value = internal_hmac_client.read_secret_file(path_value)
    except Exception as exc:
        raise RuOriginAuthError("secret_file_invalid") from exc
    if any(byte < 0x21 or byte > 0x7E for byte in value):
        raise RuOriginAuthError("secret_file_not_visible_ascii")
    return value


def _registry(secret: bytes) -> bytes:
    try:
        secret_text = secret.decode("ascii")
    except UnicodeDecodeError as exc:
        raise RuOriginAuthError("secret_file_not_ascii") from exc
    payload = {
        "keys": [
            {
                "enabled": True,
                "key_id": KEY_ID,
                "origins": list(ORIGINS),
                "scopes": list(SCOPES),
                "secret": secret_text,
                "subject": SUBJECT,
            }
        ]
    }
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def _dropin() -> bytes:
    return (
        "# Managed by scripts/remote_prepare_ru_origin_auth.py\n"
        "[Service]\n"
        f'Environment="INTERNAL_HMAC_KEYS_FILE={REGISTRY_PATH}"\n'
    ).encode("utf-8")


def _run(ssh: Any, command: str, *, label: str, timeout: int = 180) -> str:
    try:
        return remote_support._run(ssh, command, label=label, timeout=timeout)
    except Exception as exc:
        code = str(exc).split(":", 1)[0]
        raise RuOriginAuthError(code) from exc


def _parse_probe(raw: str) -> dict[str, bool]:
    values: dict[str, bool] = {}
    for line in raw.splitlines():
        key, separator, value = line.partition("=")
        if (
            separator != "="
            or re.fullmatch(r"[a-z0-9_]{1,64}", key) is None
            or value not in {"yes", "no"}
            or key in values
        ):
            raise RuOriginAuthError("remote_preflight_shape_invalid")
        values[key] = value == "yes"
    required = {
        "effective_uid_root",
        "python3_present",
        "install_present",
        "systemctl_present",
        "portal_api_active",
        "registry_present",
        "dropin_present",
        "registry_env_configured",
    }
    if set(values) != required:
        raise RuOriginAuthError("remote_preflight_keys_invalid")
    return values


def _preflight_command() -> str:
    registry_marker = "INTERNAL_HMAC_KEYS_FILE=" + REGISTRY_PATH
    return "\n".join(
        [
            "set -u",
            "emit_bool() { if sh -c \"$2\" >/dev/null 2>&1; then printf '%s=yes\\n' \"$1\"; else printf '%s=no\\n' \"$1\"; fi; }",
            "emit_bool effective_uid_root 'test \"$(id -u)\" = 0'",
            "emit_bool python3_present 'command -v python3'",
            "emit_bool install_present 'command -v install'",
            "emit_bool systemctl_present 'command -v systemctl'",
            "emit_bool portal_api_active 'systemctl is-active --quiet portal-api'",
            f"emit_bool registry_present 'test -e {_q(REGISTRY_PATH)}'",
            f"emit_bool dropin_present 'test -e {_q(DROPIN_PATH)}'",
            "emit_bool registry_env_configured 'pid=$(systemctl show portal-api --property MainPID --value); "
            "test -n \"$pid\"; test \"$pid\" != 0; tr \"\\000\" \"\\n\" < /proc/$pid/environ | "
            + "grep -Fxq "
            + _q(registry_marker)
            + "'",
        ]
    )


def _assert_install_preflight(values: Mapping[str, bool]) -> None:
    for name in (
        "effective_uid_root",
        "python3_present",
        "install_present",
        "systemctl_present",
        "portal_api_active",
    ):
        if not values.get(name):
            raise RuOriginAuthError(f"preflight_{name}_failed")
    if values.get("registry_present") or values.get("dropin_present"):
        raise RuOriginAuthError("preflight_target_already_present")
    if values.get("registry_env_configured"):
        raise RuOriginAuthError("preflight_registry_env_already_configured")


def _receipt() -> bytes:
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dropin_path": DROPIN_PATH,
        "key_id": KEY_ID,
        "previous_dropin_present": False,
        "previous_registry_present": False,
        "registry_path": REGISTRY_PATH,
        "schema_version": RECEIPT_SCHEMA,
        "subject": SUBJECT,
    }
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def _apply_command(*, stage_dir: str, receipt_dir: str) -> str:
    return "\n".join(
        [
            "set -e",
            f"test ! -e {_q(REGISTRY_PATH)}",
            f"test ! -e {_q(DROPIN_PATH)}",
            f"install -D -o root -g root -m 0600 {_q(stage_dir + '/registry.json')} {_q(REGISTRY_PATH)}",
            f"install -D -o root -g root -m 0644 {_q(stage_dir + '/dropin.conf')} {_q(DROPIN_PATH)}",
            f"test \"$(stat -c %a {_q(REGISTRY_PATH)})\" = 600",
            f"test \"$(stat -c %u {_q(REGISTRY_PATH)})\" = 0",
            f"test \"$(stat -c %g {_q(REGISTRY_PATH)})\" = 0",
            f"test \"$(stat -c %a {_q(DROPIN_PATH)})\" = 644",
            f"test \"$(stat -c %u {_q(DROPIN_PATH)})\" = 0",
            f"test \"$(stat -c %g {_q(DROPIN_PATH)})\" = 0",
            "systemctl daemon-reload",
            "systemctl restart portal-api",
            "systemctl is-active --quiet portal-api",
            "pid=$(systemctl show portal-api --property MainPID --value)",
            "test -n \"$pid\"",
            "test \"$pid\" != 0",
            "tr '\\000' '\\n' < /proc/$pid/environ | grep -Fxq "
            + _q("INTERNAL_HMAC_KEYS_FILE=" + REGISTRY_PATH),
            f"printf '%s\\n' applied > {_q(receipt_dir + '/state')}",
            f"rm -rf -- {_q(stage_dir)}",
        ]
    )


def _cleanup_command(*, stage_dir: str, receipt_dir: str) -> str:
    return "\n".join(
        [
            "set -e",
            f"rm -f -- {_q(DROPIN_PATH)} {_q(REGISTRY_PATH)}",
            f"rm -rf -- {_q(stage_dir)}",
            "systemctl daemon-reload",
            "systemctl restart portal-api",
            "systemctl is-active --quiet portal-api",
            f"if test -d {_q(receipt_dir)}; then printf '%s\\n' automatic_cleanup > {_q(receipt_dir + '/state')}; fi",
        ]
    )


def _rollback_command(*, receipt_dir: str) -> str:
    validator = r'''import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
value = json.loads(p.read_text(encoding="utf-8"))
expected = {
    "schema_version": "pokrov-ru-origin-auth-receipt-v1",
    "key_id": "ru-mini-v1",
    "subject": "mini",
    "registry_path": "/etc/pokrov/internal-hmac-keys.json",
    "dropin_path": "/etc/systemd/system/portal-api.service.d/40-pokrov-internal-hmac.conf",
    "previous_registry_present": False,
    "previous_dropin_present": False,
}
if not isinstance(value, dict) or any(value.get(k) != v for k, v in expected.items()):
    raise SystemExit(2)
registry = json.loads(pathlib.Path(expected["registry_path"]).read_text(encoding="utf-8"))
keys = registry.get("keys") if isinstance(registry, dict) else None
if not isinstance(keys, list) or len(keys) != 1:
    raise SystemExit(3)
entry = keys[0]
if not isinstance(entry, dict) or set(entry) != {"enabled", "key_id", "origins", "scopes", "secret", "subject"}:
    raise SystemExit(4)
if entry.get("key_id") != expected["key_id"] or entry.get("subject") != expected["subject"]:
    raise SystemExit(5)
if entry.get("enabled") is not True or entry.get("origins") != ["ru"]:
    raise SystemExit(6)
if entry.get("scopes") != ["ru_probe:heartbeat", "ru_probe:ingest", "ru_probe:manifest"]:
    raise SystemExit(7)
if not isinstance(entry.get("secret"), str) or not 16 <= len(entry["secret"].encode("utf-8")) <= 512:
    raise SystemExit(8)
dropin = pathlib.Path(expected["dropin_path"]).read_text(encoding="utf-8")
if dropin != '# Managed by scripts/remote_prepare_ru_origin_auth.py\n[Service]\nEnvironment="INTERNAL_HMAC_KEYS_FILE=/etc/pokrov/internal-hmac-keys.json"\n':
    raise SystemExit(9)
'''
    import base64

    encoded = base64.b64encode(validator.encode("utf-8")).decode("ascii")
    return "\n".join(
        [
            "set -e",
            f"test -f {_q(receipt_dir + '/receipt.json')}",
            f"test -f {_q(REGISTRY_PATH)}",
            f"test -f {_q(DROPIN_PATH)}",
            f"printf %s {_q(encoded)} | base64 -d | python3 - {_q(receipt_dir + '/receipt.json')}",
            f"rm -f -- {_q(DROPIN_PATH)} {_q(REGISTRY_PATH)}",
            "systemctl daemon-reload",
            "systemctl restart portal-api",
            "systemctl is-active --quiet portal-api",
            f"printf '%s\\n' rolled_back > {_q(receipt_dir + '/state')}",
        ]
    )


def _signed_manifest(
    secret_file: Path,
    *,
    attempts: int = MANIFEST_ATTEMPTS,
    retry_seconds: float = MANIFEST_RETRY_SECONDS,
    sleep_fn: Any = time.sleep,
) -> dict[str, Any]:
    if not 1 <= attempts <= MANIFEST_ATTEMPTS or not 0 <= retry_seconds <= 5:
        raise RuOriginAuthError("signed_manifest_retry_contract_invalid")
    response = None
    payload: object = None
    for attempt in range(1, attempts + 1):
        try:
            response = internal_hmac_client.signed_request(
                api_base_url=API_BASE_URL,
                method="GET",
                path=MANIFEST_PATH,
                key_id=KEY_ID,
                secret_file=secret_file,
                raw_body=b"",
                timeout_sec=MANIFEST_TIMEOUT_SECONDS,
            )
        except Exception as exc:
            if attempt == attempts:
                raise RuOriginAuthError("signed_manifest_transport_failed") from exc
            sleep_fn(retry_seconds)
            continue
        try:
            payload = json.loads(response.body.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            if response.status >= 500 and attempt < attempts:
                sleep_fn(retry_seconds)
                continue
            raise RuOriginAuthError(
                f"signed_manifest_http_{response.status}_non_json"
            ) from exc
        if response.status == 200:
            break
        error_code = payload.get("code") if isinstance(payload, dict) else None
        safe_code = (
            error_code
            if isinstance(error_code, str)
            and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", error_code)
            else "unknown"
        )
        if response.status >= 500 and attempt < attempts:
            sleep_fn(retry_seconds)
            continue
        raise RuOriginAuthError(f"signed_manifest_http_{response.status}_{safe_code}")
    if response is None or response.status != 200 or not isinstance(payload, dict):
        raise RuOriginAuthError("signed_manifest_response_invalid")
    targets = payload.get("targets")
    if not isinstance(targets, list) or not targets:
        raise RuOriginAuthError("signed_manifest_targets_missing")
    profile_ids = sorted(
        {
            endpoint.get("local_probe_profile_id")
            for target in targets
            if isinstance(target, dict)
            and isinstance((endpoint := target.get("endpoint")), dict)
            and isinstance(endpoint.get("local_probe_profile_id"), str)
            and endpoint.get("local_probe_profile_id")
        }
    )
    return {
        "http_status": response.status,
        "readiness_attempts": attempt,
        "target_count": len(targets),
        "release_required_count": sum(
            1
            for target in targets
            if isinstance(target, dict) and target.get("scope") == "release_required"
        ),
        "local_profile_ids": profile_ids,
    }


def _write_report(report: Mapping[str, Any], raw_path: str) -> None:
    value = str(raw_path or "").strip()
    if not value:
        return
    path = Path(value).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(report), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brain-host", default=relay.DEFAULT_BRAIN_HOST)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--operation", choices=("install", "rollback"), default="install")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--secret-file", default="")
    parser.add_argument("--receipt-id", default="")
    parser.add_argument("--confirm-key-id", default="")
    parser.add_argument("--confirm-subject", default="")
    parser.add_argument("--confirm-external-mutation", default="")
    parser.add_argument("--confirm-portal-api-restart", default="")
    parser.add_argument("--json-out", default="")
    return parser


def main() -> int:
    args = _parser().parse_args()
    brain = None
    stage_dir = ""
    receipt_dir = ""
    cleanup_armed = False
    mutation_attempted = False
    receipt_created = False
    try:
        passwords = Path(args.passwords).resolve()
        brain, auth_method = connect_node(
            code="brain", host=str(args.brain_host), passwords_path=passwords
        )
        preflight = _parse_probe(
            _run(brain, _preflight_command(), label="ru_origin_auth_preflight", timeout=60)
        )
        report: dict[str, Any] = {
            "schema_version": REPORT_SCHEMA,
            "mode": "APPLY" if args.apply else "PLAN",
            "operation": args.operation,
            "key_id": KEY_ID,
            "subject": SUBJECT,
            "scopes": list(SCOPES),
            "origins": list(ORIGINS),
            "brain_auth_method": remote_support._auth_family(auth_method),
            "preflight": preflight,
            "mutation_performed": False,
            "secret_supplied": bool(args.secret_file),
            "secret_returned": False,
            "secret_hash_returned": False,
            "raw_host_returned": False,
        }
        if not args.apply:
            report["ordered_actions"] = (
                [
                    "validate_exact_local_secret_without_returning_it_or_its_hash",
                    "retain_root_only_absent-state_receipt",
                    "install_single-key_root-only_registry",
                    "install_owned_systemd_environment_dropin",
                    "restart_portal_api",
                    "prove_signed_manifest_read",
                ]
                if args.operation == "install"
                else [
                    "validate_exact_owned_receipt_and_managed_targets",
                    "remove_only_operation_owned_registry_and_dropin",
                    "restart_portal_api",
                ]
            )
            _write_report(report, args.json_out)
            print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
            return 0

        if args.confirm_key_id != KEY_ID:
            raise RuOriginAuthError("confirm_key_id_mismatch")
        if args.confirm_subject != SUBJECT:
            raise RuOriginAuthError("confirm_subject_mismatch")
        if args.confirm_external_mutation != "RU_ORIGIN_AUTH_MUTATION_AUTHORIZED":
            raise RuOriginAuthError("external_mutation_confirmation_missing")
        if args.confirm_portal_api_restart != "PORTAL_API_RESTART_AUTHORIZED":
            raise RuOriginAuthError("portal_api_restart_confirmation_missing")

        if args.operation == "rollback":
            receipt_id = _receipt_id(args.receipt_id)
            receipt_dir = f"{RECEIPT_ROOT}/{receipt_id}"
            _run(
                brain,
                _rollback_command(receipt_dir=receipt_dir),
                label="ru_origin_auth_rollback",
                timeout=120,
            )
            report.update(
                {
                    "mutation_performed": True,
                    "receipt_id": receipt_id,
                    "rollback_status": "PASS",
                }
            )
        else:
            _assert_install_preflight(preflight)
            if not args.secret_file:
                raise RuOriginAuthError("secret_file_required")
            secret_file = Path(args.secret_file).resolve(strict=True)
            registry = _registry(_secret(secret_file))
            receipt_id = _release_id()
            receipt_dir = f"{RECEIPT_ROOT}/{receipt_id}"
            stage_dir = f"{STAGE_ROOT}/{receipt_id}"
            _run(
                brain,
                "set -e; install -d -o root -g root -m 0700 "
                + _q(receipt_dir)
                + " "
                + _q(stage_dir),
                label="ru_origin_auth_stage",
            )
            cleanup_armed = True
            mutation_attempted = True
            sftp = brain.open_sftp()
            try:
                remote_support._remote_write(
                    sftp, receipt_dir + "/receipt.json", _receipt(), 0o600
                )
                remote_support._remote_write(
                    sftp, stage_dir + "/registry.json", registry, 0o600
                )
                remote_support._remote_write(
                    sftp, stage_dir + "/dropin.conf", _dropin(), 0o600
                )
            finally:
                sftp.close()
            receipt_created = True
            _run(
                brain,
                _apply_command(stage_dir=stage_dir, receipt_dir=receipt_dir),
                label="ru_origin_auth_apply",
                timeout=120,
            )
            manifest = _signed_manifest(secret_file)
            cleanup_armed = False
            report.update(
                {
                    "mutation_performed": True,
                    "receipt_id": receipt_id,
                    "signed_manifest": manifest,
                    "runtime_ready_for_pi_install": not manifest["local_profile_ids"],
                    "automatic_cleanup_status": "NOT_NEEDED",
                }
            )
        _write_report(report, args.json_out)
        print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        cleanup_status = "NOT_ARMED"
        if brain is not None and cleanup_armed:
            try:
                _run(
                    brain,
                    _cleanup_command(stage_dir=stage_dir, receipt_dir=receipt_dir),
                    label="ru_origin_auth_automatic_cleanup",
                    timeout=120,
                )
                cleanup_status = "PASS"
            except Exception:
                cleanup_status = "FAIL"
        code = str(exc).split(":", 1)[0][:160]
        failure_report = {
            "schema_version": REPORT_SCHEMA,
            "mode": "ERROR",
            "operation": str(getattr(args, "operation", "")),
            "error_code": code,
            "receipt_created": receipt_created,
            "mutation_attempted": mutation_attempted,
            "automatic_cleanup_status": cleanup_status,
            "secret_returned": False,
            "secret_hash_returned": False,
            "raw_host_returned": False,
        }
        try:
            _write_report(failure_report, str(getattr(args, "json_out", "") or ""))
        except Exception:
            pass
        print(
            f"RU-origin auth operation failed: {type(exc).__name__}: {code} "
            f"automatic_cleanup_status={cleanup_status}",
            file=sys.stderr,
        )
        return 1
    finally:
        if brain is not None:
            brain.close()


if __name__ == "__main__":
    raise SystemExit(main())
