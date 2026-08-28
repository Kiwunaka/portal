from __future__ import annotations

import argparse
import json
import os
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from node_access import DEFAULT_PASSWORDS, connect_node
from remote_activate_owned_awg_labs import (
    AWG31_ENDPOINT_REVISION,
    AWG31_GENERATION,
    AWG31_SERVER_RECORD,
    AWG31_VARIANT,
    AWG31_VARIANT_DROPIN,
    AWG_TARGET,
    CONFIG_ROOT,
    NODE_CODE,
    _activate_control_plane,
    _awg31_variant_dropin_content,
    _node_host,
    _run_remote,
    _sftp_write,
)
from remote_rebind_owned_awg_lab_ports import (
    _active_identity,
    _read_config,
)
from remote_run_owned_awg_core_interop import _load_material


PROFILE = "awg31_lab"
INTERFACE = "pokrovawg31"
PORT = 3478
CONTENT_PADDING = "64-512"
_FIELD_RE = re.compile(r"(?mi)^(?P<name>[A-Za-z][A-Za-z0-9]*)\s*=\s*(?P<value>[^\r\n]*)$")


class VariantError(RuntimeError):
    pass


def _safe_error_code(exc: Exception) -> str:
    message = str(exc)
    match = re.search(
        r"admin api [A-Z]+ [^ ]+ failed HTTP (\d{3}) detail=([A-Za-z0-9_.@,-]+)",
        message,
    )
    if match:
        return f"admin_api_http_{match.group(1)}_{match.group(2)}"[:240]
    known = {
        "guarded rollout did not select AWG 3.1": "rollout_selection_mismatch",
        "guarded control-plane activation failed": "control_plane_activation_failed",
    }
    for marker, code in known.items():
        if marker in message:
            return code
    return type(exc).__name__.lower()


def _fields(raw: bytes | bytearray) -> dict[str, list[str]]:
    try:
        text = bytes(raw).decode("ascii")
    except UnicodeDecodeError as exc:
        raise VariantError("AWG server configuration is not ASCII") from exc
    result: dict[str, list[str]] = {}
    for match in _FIELD_RE.finditer(text):
        result.setdefault(match.group("name").lower(), []).append(
            match.group("value").strip()
        )
    return result


def _single_field(values: dict[str, list[str]], name: str) -> str | None:
    matches = values.get(name.lower(), [])
    if len(matches) > 1:
        raise VariantError(f"duplicate AWG field: {name}")
    return matches[0] if matches else None


def _server_is_randomized(raw: bytes | bytearray) -> bool:
    values = _fields(raw)
    return (
        all(_single_field(values, f"s{index}") == "16" for index in range(1, 5))
        and _single_field(values, "headerprotectionkey") not in (None, "")
        and _single_field(values, "contentpaddingaddition") == CONTENT_PADDING
        and (_single_field(values, "randomtrailers") or "").lower() in {"true", "on"}
    )


def _server_is_minimal(raw: bytes | bytearray) -> bool:
    values = _fields(raw)
    content = _single_field(values, "contentpaddingaddition")
    trailers = (_single_field(values, "randomtrailers") or "false").lower()
    return (
        all(_single_field(values, f"s{index}") == "16" for index in range(1, 5))
        and _single_field(values, "headerprotectionkey") not in (None, "")
        and content in (None, "0")
        and trailers in {"false", "off"}
    )


def _replace_server_variant(raw: bytes | bytearray) -> bytes:
    if _server_is_randomized(raw):
        return bytes(raw)
    if not _server_is_minimal(raw):
        raise VariantError("AWG 3.1 server variant precondition failed")
    text = bytes(raw).decode("ascii")
    header = re.search(r"(?mi)^HeaderProtectionKey\s*=\s*[^\r\n]+$", text)
    if header is None:
        raise VariantError("AWG 3.1 header protection key is missing")
    insertion = (
        header.group(0)
        + f"\nContentPaddingAddition = {CONTENT_PADDING}"
        + "\nRandomTrailers = true"
    )
    text = text[: header.start()] + insertion + text[header.end() :]
    encoded = text.encode("ascii")
    if not _server_is_randomized(encoded):
        raise VariantError("AWG 3.1 server variant transform failed")
    return encoded


def _material_is_randomized(endpoint: dict[str, Any]) -> bool:
    return (
        endpoint.get("contract_id") == "pokrov.awg31.endpoint.v1"
        and all(int(endpoint.get(f"s{index}", 0)) >= 12 for index in range(1, 5))
        and bool(endpoint.get("header_protection_key"))
        and endpoint.get("content_padding_addition") == CONTENT_PADDING
        and endpoint.get("random_trailers") is True
    )


def _material_with_randomized_variant(raw: bytes | bytearray) -> dict[str, Any]:
    try:
        endpoint = json.loads(raw)
    except Exception as exc:
        raise VariantError("AWG 3.1 endpoint material is invalid") from exc
    if not isinstance(endpoint, dict):
        raise VariantError("AWG 3.1 endpoint material shape is invalid")
    if _material_is_randomized(endpoint):
        return endpoint
    if (
        endpoint.get("contract_id") != "pokrov.awg31.endpoint.v1"
        or endpoint.get("content_padding_addition") not in (None, "0")
        or endpoint.get("random_trailers") not in (None, False)
        or not bool(endpoint.get("header_protection_key"))
        or not all(int(endpoint.get(f"s{index}", 0)) >= 12 for index in range(1, 5))
    ):
        raise VariantError("AWG 3.1 endpoint variant precondition failed")
    endpoint["content_padding_addition"] = CONTENT_PADDING
    endpoint["random_trailers"] = True
    if not _material_is_randomized(endpoint):
        raise VariantError("AWG 3.1 endpoint variant transform failed")
    return endpoint


def _read_optional_dropin(node: Any) -> bytearray | None:
    sftp = node.open_sftp()
    try:
        try:
            with sftp.open(AWG31_VARIANT_DROPIN, "rb") as handle:
                raw = bytearray(handle.read(16 * 1024 + 1))
        except OSError:
            return None
    finally:
        sftp.close()
    if not 1 <= len(raw) <= 16 * 1024:
        raise VariantError("AWG 3.1 variant drop-in size is invalid")
    return raw


def _dropin_is_randomized(raw: bytes | bytearray | None) -> bool:
    if raw is None:
        return False
    return bytes(raw).replace(b"\r\n", b"\n") == _awg31_variant_dropin_content()


def _write_dropin(node: Any, raw: bytes | bytearray) -> None:
    _run_remote(
        node,
        "install -d -m 0755 "
        + shlex.quote(AWG31_VARIANT_DROPIN.rsplit("/", 1)[0]),
    )
    sftp = node.open_sftp()
    try:
        _sftp_write(sftp, AWG31_VARIANT_DROPIN, bytes(raw), 0o644)
    finally:
        sftp.close()


def _apply_server_variant(node: Any) -> None:
    _write_dropin(node, _awg31_variant_dropin_content())
    _run_remote(node, "systemctl daemon-reload")
    _run_remote(node, f"systemctl restart pokrov-awg-lab@{INTERFACE}.service", timeout=120)


def _restore_server_variant(node: Any, old_dropin: bytes | bytearray | None) -> None:
    if old_dropin is None:
        _run_remote(node, "rm -f " + shlex.quote(AWG31_VARIANT_DROPIN))
    else:
        _write_dropin(node, old_dropin)
    _run_remote(node, "systemctl daemon-reload")
    _run_remote(node, f"systemctl restart pokrov-awg-lab@{INTERFACE}.service", timeout=120)


def _live_server_checks(node: Any) -> dict[str, bool]:
    persisted = _read_config(node, INTERFACE)
    dropin = _read_optional_dropin(node)
    try:
        showconf = _run_remote(node, f"{AWG_TARGET} showconf {INTERFACE}")
        active = _run_remote(
            node, f"systemctl is-active pokrov-awg-lab@{INTERFACE}.service"
        )
        port = _run_remote(node, f"{AWG_TARGET} show {INTERFACE} listen-port")
        socket_ready = _run_remote(
            node,
            f"if ss -H -lun 'sport = :{PORT}' | grep -q .; then printf yes; else printf no; fi",
        )
        return {
            "base_config_minimal": _server_is_minimal(persisted),
            "persistent_dropin": _dropin_is_randomized(dropin),
            "live_variant": _server_is_randomized(showconf.encode("ascii")),
            "service_active": active == "active",
            "listen_port": port == str(PORT),
            "udp_socket": socket_ready == "yes",
        }
    finally:
        for index in range(len(persisted)):
            persisted[index] = 0
        if dropin is not None:
            for index in range(len(dropin)):
                dropin[index] = 0


def _material_check(brain: Any) -> bool:
    raw = bytearray(_load_material(brain, PROFILE))
    try:
        endpoint = json.loads(raw)
        return isinstance(endpoint, dict) and _material_is_randomized(endpoint)
    finally:
        for index in range(len(raw)):
            raw[index] = 0


def _retain_backup(
    node: Any,
    raw: bytes | bytearray,
    dropin: bytes | bytearray | None,
) -> None:
    root = (
        "/root/pokrov-awg-lab-variant-backups/"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    _run_remote(node, f"install -d -m 0700 {shlex.quote(root)}")
    sftp = node.open_sftp()
    try:
        _sftp_write(sftp, f"{root}/{INTERFACE}.conf", bytes(raw), 0o600)
        if dropin is None:
            _sftp_write(sftp, f"{root}/variant-dropin.absent", b"absent\n", 0o600)
        else:
            _sftp_write(sftp, f"{root}/variant.conf", bytes(dropin), 0o600)
    finally:
        sftp.close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Guarded promotion of the owned AWG 3.1 randomized-trailer lab variant."
    )
    parser.add_argument("--brain-ip", default="82.21.114.104")
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--known-hosts", required=True)
    parser.add_argument("--confirm-node", default="")
    parser.add_argument("--confirm-variant", default="")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    known_hosts = Path(args.known_hosts).resolve()
    passwords = Path(args.passwords).resolve()
    if not known_hosts.is_file() or not passwords.is_file():
        raise SystemExit("SSH trust or authentication input is missing")
    os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)

    brain, _brain_auth = connect_node(
        code="brain", host=str(args.brain_ip), passwords_path=passwords
    )
    node = None
    materials: dict[str, bytearray] = {}
    old_config = bytearray()
    old_dropin: bytearray | None = None
    server_changed = False
    control_attempted = False
    tg_id = 0
    install_id = ""
    stage = "connect"
    readback_failures: list[str] = []
    try:
        stage = "active_identity"
        tg_id, install_id = _active_identity(brain)
        stage = "node_connect"
        node = connect_node(
            code=NODE_CODE, host=_node_host(brain), passwords_path=passwords
        )[0]
        stage = "preflight"
        materials["awg2_lab"] = bytearray(_load_material(brain, "awg2_lab"))
        materials[PROFILE] = bytearray(_load_material(brain, PROFILE))
        old_config = _read_config(node, INTERFACE)
        old_dropin = _read_optional_dropin(node)
        new_config = _replace_server_variant(old_config)
        awg31_endpoint = _material_with_randomized_variant(materials[PROFILE])
        already_randomized = _dropin_is_randomized(old_dropin) and _material_is_randomized(
            json.loads(materials[PROFILE])
        )
        report: dict[str, Any] = {
            "schema_version": "pokrov-owned-awg31-variant-v1",
            "mode": "APPLY" if args.apply else "PLAN",
            "node_code": NODE_CODE,
            "profile": PROFILE,
            "target_variant": AWG31_VARIANT,
            "target_generation": AWG31_GENERATION,
            "target_endpoint_revision": AWG31_ENDPOINT_REVISION,
            "target_server_record": AWG31_SERVER_RECORD,
            "preflight": {
                "already_randomized": already_randomized,
                "server_transform_ready": _server_is_randomized(new_config),
                "server_dropin_ready": _dropin_is_randomized(
                    _awg31_variant_dropin_content()
                ),
                "material_transform_ready": _material_is_randomized(awg31_endpoint),
                "active_material_identity_consistent": True,
            },
            "raw_identifiers_returned": False,
            "raw_material_returned": False,
        }
        if not args.apply:
            report["ok"] = True
            print(json.dumps(report, sort_keys=True))
            return 0
        if str(args.confirm_node).strip().lower() != NODE_CODE:
            raise VariantError("--confirm-node mismatch")
        if str(args.confirm_variant).strip() != AWG31_VARIANT:
            raise VariantError("--confirm-variant mismatch")

        if not already_randomized:
            stage = "backup"
            _retain_backup(node, old_config, old_dropin)
            stage = "dataplane"
            server_changed = True
            _apply_server_variant(node)
        stage = "control_plane"
        control_attempted = True
        report["control_plane"] = _activate_control_plane(
            brain,
            tg_id=tg_id,
            install_id=install_id,
            extend_entitlement=False,
            awg2_endpoint=json.loads(materials["awg2_lab"]),
            awg31_endpoint=awg31_endpoint,
        )
        stage = "readback"
        report["readback"] = {
            "server": _live_server_checks(node),
            "material_variant": _material_check(brain),
            "backup_retained": not already_randomized,
        }
        report["ok"] = all(report["readback"]["server"].values()) and bool(
            report["readback"]["material_variant"]
        )
        if not report["ok"]:
            readback_failures = [
                name
                for name, passed in report["readback"]["server"].items()
                if not passed
            ]
            if not report["readback"]["material_variant"]:
                readback_failures.append("material_variant")
            raise VariantError("AWG 3.1 variant readback failed")
        print(json.dumps(report, sort_keys=True))
        return 0
    except Exception as exc:
        if node is not None and server_changed and old_config:
            try:
                _restore_server_variant(node, old_dropin)
            except Exception:
                pass
        if control_attempted and tg_id > 0 and install_id and materials:
            try:
                _activate_control_plane(
                    brain,
                    tg_id=tg_id,
                    install_id=install_id,
                    extend_entitlement=False,
                    awg2_endpoint=json.loads(materials["awg2_lab"]),
                    awg31_endpoint=json.loads(materials[PROFILE]),
                )
            except Exception:
                pass
        print(
            json.dumps(
                {
                    "schema_version": "pokrov-owned-awg31-variant-v1",
                    "mode": "APPLY" if args.apply else "PLAN",
                    "node_code": NODE_CODE,
                    "profile": PROFILE,
                    "target_variant": AWG31_VARIANT,
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "safe_error_code": _safe_error_code(exc),
                    "failure_stage": stage,
                    "readback_failures": readback_failures,
                    "rollback_attempted": bool(server_changed or control_attempted),
                    "raw_identifiers_returned": False,
                    "raw_material_returned": False,
                },
                sort_keys=True,
            )
        )
        return 1
    finally:
        if node is not None:
            node.close()
        brain.close()
        for raw in [*materials.values(), old_config, old_dropin]:
            if raw is None:
                continue
            for index in range(len(raw)):
                raw[index] = 0


if __name__ == "__main__":
    raise SystemExit(main())
