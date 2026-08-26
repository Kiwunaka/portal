from __future__ import annotations

import argparse
import json
import os
import re
import shlex
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy

from node_inventory import DEFAULT_INVENTORY, inventory_ipv4_map


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
LIVE_TCP_ERROR_KINDS = frozenset({"dns_failure", "timeout", "refused", "os_error", "remote_exec_error"})


@dataclass(frozen=True)
class LiveNodeTarget:
    """Enabled delivery-node endpoint loaded from the live control plane."""

    code: str
    host: str
    port: int


def _parse_inventory(path: Path) -> dict[str, str]:
    out = inventory_ipv4_map(path)
    if not out:
        raise SystemExit(f"Failed to parse inventory: {path}")
    return out


def _parse_brain_password(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    for i, ln in enumerate(lines):
        if "BRAINnode" not in ln:
            continue
        for j in range(i + 1, min(i + 30, len(lines))):
            v = lines[j].strip()
            if v and not v.startswith("ssh-ed25519 "):
                return v
    return ""


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def _parse_live_node_rows(raw: str) -> list[LiveNodeTarget]:
    """Parse live enabled-node rows while rejecting unsafe endpoint values."""
    targets: list[LiveNodeTarget] = []
    seen_codes: set[str] = set()
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) != 3:
            raise ValueError("live node query returned an invalid row")
        code = parts[0].strip().lower()
        host = parts[1].strip()
        port_text = parts[2].strip()
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,31}", code):
            raise ValueError("live node query returned an invalid node code")
        if code in seen_codes:
            raise ValueError("live node query returned a duplicate node code")
        if not host or len(host) > 253 or any(char.isspace() for char in host):
            raise ValueError("live node query returned an invalid host")
        try:
            port = int(port_text)
        except ValueError as exc:
            raise ValueError("live node query returned an invalid port") from exc
        if not 1 <= port <= 65535:
            raise ValueError("live node query returned an invalid port")
        seen_codes.add(code)
        targets.append(LiveNodeTarget(code=code, host=host, port=port))
    if not targets:
        raise ValueError("live node query returned no enabled nodes")
    return targets


def _load_live_node_targets(ssh: paramiko.SSHClient) -> list[LiveNodeTarget]:
    """Load the current enabled node endpoints without selecting credentials."""
    query = (
        "runuser -u postgres -- psql -d portal -AtF '|' -c "
        '"select code,host,coalesce(vless_port,443) '
        'from nodes where enabled=true order by code;"'
    )
    code, out, _err = _run(ssh, query, timeout=60)
    if code != 0:
        raise RuntimeError("unable to load live enabled nodes")
    return _parse_live_node_rows(out)


def _remote_tcp_probe_command(target: LiveNodeTarget) -> str:
    """Build a bounded remote TCP probe that emits no endpoint material."""
    config = json.dumps({"host": target.host, "port": target.port})
    script = f"""import json
import socket

target = json.loads({config!r})
try:
    with socket.create_connection((target["host"], int(target["port"])), timeout=5):
        print("open")
except socket.gaierror:
    print("closed:dns_failure")
except (TimeoutError, socket.timeout):
    print("closed:timeout")
except ConnectionRefusedError:
    print("closed:refused")
except OSError:
    print("closed:os_error")
"""
    return "python3 -c " + shlex.quote(script)


def _probe_live_node_targets(
    ssh: paramiko.SSHClient,
    targets: list[LiveNodeTarget],
) -> dict[str, Any]:
    """Probe configured live ports from Brain and return a redacted report."""
    rows: list[dict[str, Any]] = []
    for target in targets:
        code, out, _err = _run(ssh, _remote_tcp_probe_command(target), timeout=15)
        result = out.strip().splitlines()[-1] if code == 0 and out.strip() else "closed:remote_exec_error"
        if result == "open":
            tcp_status = "open"
            error_kind = ""
        elif result.startswith("closed:"):
            tcp_status = "closed"
            candidate_error = result.split(":", 1)[1]
            error_kind = candidate_error if candidate_error in LIVE_TCP_ERROR_KINDS else "invalid_probe_result"
        else:
            tcp_status = "closed"
            error_kind = "invalid_probe_result"
        rows.append(
            {
                "node_code": target.code,
                "configured_port": target.port,
                "tcp_status": tcp_status,
                "error_kind": error_kind,
            }
        )
    return {
        "schema_version": "pokrov-brain-network-probe-v2",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "origin": "brain",
        "target_source": "live_enabled_nodes",
        "node_count": len(rows),
        "nodes": rows,
        "ok": bool(rows) and all(row["tcp_status"] == "open" for row in rows),
    }


def _redact_inventory_report(report: dict[str, dict[str, str]]) -> dict[str, Any]:
    """Remove inventory addresses and derive an explicit diagnostic verdict."""
    rows: list[dict[str, Any]] = []
    for node_code in sorted(report):
        raw = report[node_code]
        ports = {
            key.removeprefix("port_"): value
            for key, value in sorted(raw.items())
            if key.startswith("port_")
        }
        rows.append({"node_code": node_code, "ports": ports})
    statuses = [status for row in rows for status in row["ports"].values()]
    return {
        "schema_version": "pokrov-brain-network-probe-v2",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "origin": "brain",
        "target_source": "retained_inventory_diagnostic",
        "node_count": len(rows),
        "nodes": rows,
        "ok": bool(statuses) and all(status == "open" for status in statuses),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe worker-node ports from brain node.")
    ap.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--brain-ip", default="", help="Override brain IP (optional)")
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--ports", default="443,8443,29374")
    ap.add_argument(
        "--node-code",
        action="append",
        default=[],
        help="Limit retained-inventory diagnostics to a named node code; repeatable.",
    )
    ap.add_argument(
        "--redact",
        action="store_true",
        help="Omit retained inventory addresses and emit an explicit diagnostic verdict.",
    )
    ap.add_argument(
        "--live-enabled-nodes",
        action="store_true",
        help="Probe each live enabled node on its configured vless_port and emit a redacted report.",
    )
    ap.add_argument("--json-out", default="", help="Optional JSON output path for the redacted live-node report.")
    args = ap.parse_args()

    if args.json_out and not (args.live_enabled_nodes or args.redact):
        raise SystemExit("--json-out requires --live-enabled-nodes or --redact")

    inv = _parse_inventory(Path(args.inventory))
    brain_ip = (args.brain_ip or "").strip() or inv.get("brain", "")
    if not brain_ip:
        raise SystemExit("Brain IP is missing.")

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_brain_password(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    ports = [int(p.strip()) for p in str(args.ports).split(",") if p.strip()]
    selected_codes = {str(code or "").strip().lower() for code in args.node_code if str(code or "").strip()}
    unknown_codes = selected_codes.difference(inv)
    if unknown_codes:
        raise SystemExit("Unknown inventory node code: " + ", ".join(sorted(unknown_codes)))
    targets = {
        key: value
        for key, value in inv.items()
        if key != "brain" and (not selected_codes or key in selected_codes)
    }

    ssh = paramiko.SSHClient()
    configure_ssh_host_key_policy(ssh)
    ssh.connect(
        brain_ip,
        port=args.ssh_port,
        username=args.ssh_user,
        password=pw,
        timeout=30,
        banner_timeout=30,
        auth_timeout=30,
    )
    try:
        if args.live_enabled_nodes:
            try:
                targets = _load_live_node_targets(ssh)
                live_report = _probe_live_node_targets(ssh, targets)
            except (RuntimeError, ValueError) as exc:
                live_report = {
                    "schema_version": "pokrov-brain-network-probe-v2",
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                    "origin": "brain",
                    "target_source": "live_enabled_nodes",
                    "node_count": 0,
                    "nodes": [],
                    "ok": False,
                    "error_kind": type(exc).__name__,
                }
            encoded = json.dumps(live_report, ensure_ascii=False, indent=2)
            if args.json_out:
                output_path = Path(args.json_out)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(encoded + "\n", encoding="utf-8")
                print(output_path)
            else:
                print(encoded)
            return 0 if live_report["ok"] else 2

        report: dict[str, dict[str, str]] = {}
        for code, ip in targets.items():
            host_report: dict[str, str] = {"ip": ip}
            for port in ports:
                cmd = (
                    f"timeout 5 bash -lc 'cat < /dev/null > /dev/tcp/{ip}/{port}' "
                    f"&& echo open || echo closed"
                )
                _, out, _ = _run(ssh, cmd, timeout=15)
                raw_status = out.strip().splitlines()[-1] if out.strip() else "closed"
                host_report[f"port_{port}"] = "open" if raw_status == "open" else "closed"
            report[code] = host_report

        payload: dict[str, Any] = _redact_inventory_report(report) if args.redact else report
        encoded = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.json_out:
            output_path = Path(args.json_out)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(encoded + "\n", encoding="utf-8")
            print(output_path)
        else:
            print(encoded)
        if args.redact:
            return 0 if payload["ok"] else 2
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
