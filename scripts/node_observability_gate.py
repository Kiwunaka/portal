from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))

from db import SessionLocal, init_db  # noqa: E402
from models import Node  # noqa: E402


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_dt(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _node_rows() -> list[dict]:
    init_db()
    session = SessionLocal()
    try:
        rows = session.query(Node).order_by(Node.code.asc()).all()
        payload: list[dict] = []
        for row in rows:
            payload.append(
                {
                    "code": row.code,
                    "enabled": bool(row.enabled),
                    "accepting_new_clients": bool(getattr(row, "accepting_new_clients", True)),
                    "is_draining": bool(getattr(row, "is_draining", False)),
                    "is_healthy": bool(row.is_healthy),
                    "last_probe_at": row.last_probe_at.isoformat() if row.last_probe_at else "",
                    "last_health_at": row.last_health_at.isoformat() if row.last_health_at else "",
                    "last_probe_stage": str(getattr(row, "last_probe_stage", "") or ""),
                    "last_probe_error_kind": str(getattr(row, "last_probe_error_kind", "") or ""),
                }
            )
        return payload
    finally:
        session.close()


def _node_state_failures(rows: list[dict], *, stale_after_minutes: int, now: datetime | None = None) -> list[str]:
    failures: list[str] = []
    current = now or _utcnow()
    stale_before = current - timedelta(minutes=max(1, int(stale_after_minutes)))
    for row in rows:
        if not bool(row.get("enabled")):
            continue
        code = str(row.get("code") or "?")
        if not bool(row.get("is_healthy")):
            failures.append(f"enabled node {code} is unhealthy")
        freshness = _parse_dt(row.get("last_probe_at")) or _parse_dt(row.get("last_health_at"))
        if freshness is None or freshness < stale_before:
            failures.append(f"enabled node {code} has stale health data")
    return failures


def _drift_failures(payload: dict) -> list[str]:
    drift = int(((payload or {}).get("summary") or {}).get("drift") or 0)
    if drift > 0:
        return [f"control-plane drift detected on {drift} node(s)"]
    return []


def _dns_failures(payload: dict) -> list[str]:
    failures: list[str] = []
    for warning in (payload or {}).get("warnings", []) or []:
        if isinstance(warning, dict):
            failures.append(f"dns audit reported {warning.get('type') or 'warning'}")
        else:
            failures.append(f"dns audit reported {warning}")
    for host in (payload or {}).get("hosts", []) or []:
        host_name = str((host or {}).get("host") or "?")
        for warning in (host or {}).get("warnings", []) or []:
            failures.append(f"dns audit host {host_name} warning: {warning}")
    return failures


def _run_json_command(cmd: list[str]) -> tuple[int, dict, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (proc.stdout or "").strip()
    try:
        payload = json.loads(output) if output else {}
    except json.JSONDecodeError:
        payload = {}
    return int(proc.returncode), payload, output


def _build_report(
    *,
    node_rows: list[dict],
    node_failures: list[str],
    drift_payload: dict,
    drift_failures: list[str],
    dns_payload: dict,
    dns_failures: list[str],
) -> dict:
    failures = [*node_failures, *drift_failures, *dns_failures]
    return {
        "generated_at": _utcnow().isoformat(),
        "ok": not failures,
        "failures": failures,
        "node_state": {
            "total": len(node_rows),
            "enabled": sum(1 for row in node_rows if bool(row.get("enabled"))),
            "unhealthy": sum(1 for row in node_rows if bool(row.get("enabled")) and not bool(row.get("is_healthy"))),
            "rows": node_rows,
        },
        "drift": drift_payload,
        "dns": dns_payload,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Required predeploy gate for node freshness, unhealthy nodes, control-plane drift, and DNS audit."
    )
    parser.add_argument("--domain", default="pokrov.space")
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"))
    parser.add_argument("--stale-after-minutes", type=int, default=30)
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    node_rows = _node_rows()
    node_failures = _node_state_failures(node_rows, stale_after_minutes=int(args.stale_after_minutes))

    drift_cmd = [
        sys.executable,
        "scripts/control_plane_drift_report.py",
        "--ssh-user",
        args.ssh_user,
        "--ssh-port",
        str(args.ssh_port),
        "--passwords",
        args.passwords,
    ]
    drift_rc, drift_payload, drift_output = _run_json_command(drift_cmd)
    drift_failures = _drift_failures(drift_payload)
    if drift_rc != 0:
        drift_failures.insert(0, f"control-plane drift audit failed with exit code {drift_rc}")
        if drift_output:
            drift_failures.append(drift_output.splitlines()[-1])

    dns_cmd = [
        sys.executable,
        "scripts/audit_node_dns.py",
        "--domain",
        args.domain,
        "--include-brain",
    ]
    dns_rc, dns_payload, dns_output = _run_json_command(dns_cmd)
    dns_failures = _dns_failures(dns_payload)
    if dns_rc != 0:
        dns_failures.insert(0, f"dns audit failed with exit code {dns_rc}")
        if dns_output:
            dns_failures.append(dns_output.splitlines()[-1])

    report = _build_report(
        node_rows=node_rows,
        node_failures=node_failures,
        drift_payload=drift_payload,
        drift_failures=drift_failures,
        dns_payload=dns_payload,
        dns_failures=dns_failures,
    )
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        print(out_path)
    else:
        print(text)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
