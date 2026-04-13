#!/usr/bin/env python3
from __future__ import annotations

"""
Run an operator-oriented qdisc smoke on a node.

The smoke keeps the logic simple:
- capture tc snapshots
- start one heavy HTTPS flow
- run several small HTTPS probes in the background window
- report p95 and TTFB numbers for the probes
"""

import argparse
import json
import math
import os
import shlex
import socket
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any

import paramiko

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from node_access import connect_node

DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
DEFAULT_PROFILES = REPO_ROOT / "infra" / "node-qdisc-profiles.json"


def _run_local(cmd: str) -> tuple[int, str, str]:
    proc = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def _run_remote(ssh: paramiko.SSHClient, cmd: str) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(f"bash -lc {shlex.quote(cmd)}", timeout=900)
    code = stdout.channel.recv_exit_status()
    return code, stdout.read().decode("utf-8", errors="replace"), stderr.read().decode("utf-8", errors="replace")


def _load_profiles(path: Path) -> dict[str, dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        if "profiles" in raw:
            raw = raw["profiles"]
        else:
            raw = list(raw.values())
    out: dict[str, dict[str, Any]] = {}
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        node_code = str(item.get("node_code") or "").strip().lower()
        if node_code:
            out[node_code] = item
    return out


def _select_profile(profiles: dict[str, dict[str, Any]], node_code: str | None) -> dict[str, Any]:
    code = (node_code or os.getenv("NODE_CODE", "") or socket.gethostname()).strip().lower().split(".", 1)[0]
    if code in profiles:
        return profiles[code]
    if len(profiles) == 1:
        return next(iter(profiles.values()))
    available = ", ".join(sorted(profiles))
    raise SystemExit(f"No profile for node_code={code!r}. Available: {available}")


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    try:
        return float(statistics.quantiles(values, n=20, method="inclusive")[18])
    except Exception:
        return max(values)


def _build_probe_command(url: str, attempts: int, pause_seconds: float) -> str:
    return (
        "python3 - <<'PY'\n"
        "import subprocess, sys, time\n"
        f"url = {url!r}\n"
        f"attempts = {int(attempts)}\n"
        f"pause = {float(pause_seconds)!r}\n"
        "rows = []\n"
        "for i in range(attempts):\n"
        "    proc = subprocess.run(\n"
        "        ['curl', '-sS', '-o', '/dev/null', '-w', '%{time_connect} %{time_starttransfer} %{time_total}\\n', '--max-time', '20', url],\n"
        "        capture_output=True,\n"
        "        text=True,\n"
        "        check=False,\n"
        "    )\n"
        "    if proc.returncode != 0:\n"
        "        sys.stdout.write(f'probe_error={proc.stderr.strip() or proc.stdout.strip()}\\n')\n"
        "        continue\n"
        "    rows.append(proc.stdout.strip())\n"
        "    if pause:\n"
        "        time.sleep(pause)\n"
        "for row in rows:\n"
        "    print(row)\n"
        "PY"
    )


def _parse_probe_rows(text: str) -> tuple[list[float], list[float], list[float]]:
    connect: list[float] = []
    ttfb: list[float] = []
    total: list[float] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("probe_error="):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            connect.append(float(parts[0]))
            ttfb.append(float(parts[1]))
            total.append(float(parts[2]))
        except ValueError:
            continue
    return connect, ttfb, total


def _format_snapshot(title: str, snapshot: str) -> str:
    lines = [title.rstrip(":")]
    text = snapshot.strip()
    if text:
        lines.append(text)
    else:
        lines.append("(empty)")
    return "\n".join(lines)


def run_smoke(
    profile: dict[str, Any],
    *,
    probe_url: str,
    heavy_url: str,
    probe_attempts: int = 8,
    probe_pause_seconds: float = 1.0,
    heavy_timeout_seconds: int = 120,
    executor=_run_local,
) -> dict[str, Any]:
    iface = str(profile.get("iface") or "").strip()
    snapshots: list[str] = []

    code, out, err = executor(f"tc -s qdisc show dev {shlex.quote(iface)} || true")
    snapshots.append(_format_snapshot("tc_before", out or err))
    if code != 0 and not (out or err).strip():
        snapshots.append("tc_before\n(unavailable)")

    heavy_cmd = (
        "set -euo pipefail; "
        f"curl -sS --output /dev/null --max-time {int(heavy_timeout_seconds)} {shlex.quote(heavy_url)}"
    )
    if executor is _run_local:
        heavy_proc = subprocess.Popen(["bash", "-lc", heavy_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        heavy_handle = str(heavy_proc.pid)
        heavy_running = lambda: heavy_proc.poll() is None
        heavy_stop = lambda: heavy_proc.terminate()
        heavy_wait = lambda: heavy_proc.wait(timeout=10)
    else:
        _, heavy_stdout, heavy_stderr = executor(f"nohup bash -lc {shlex.quote(heavy_cmd)} >/tmp/portal-qdisc-heavy.log 2>&1 & echo $!")
        heavy_handle = (heavy_stdout.strip() or heavy_stderr.strip() or "").splitlines()[-1].strip()
        heavy_running = lambda: True

        def heavy_stop() -> None:
            if heavy_handle.isdigit():
                executor(f"kill {heavy_handle} >/dev/null 2>&1 || true")

        def heavy_wait() -> None:
            return None

    probe_cmd = _build_probe_command(probe_url, probe_attempts, probe_pause_seconds)
    probe_code, probe_out, probe_err = executor(probe_cmd)

    if executor is _run_local:
        if heavy_running():
            heavy_stop()
        try:
            heavy_wait()
        except Exception:
            pass
    else:
        heavy_stop()

    code, out, err = executor(f"tc -s qdisc show dev {shlex.quote(iface)} || true")
    snapshots.append(_format_snapshot("tc_after", out or err))

    connect, ttfb, total = _parse_probe_rows(probe_out)
    report = {
        "node_code": profile.get("node_code"),
        "iface": iface,
        "probe_url": probe_url,
        "heavy_url": heavy_url,
        "probe_attempts": probe_attempts,
        "heavy_handle": heavy_handle,
        "probe_connect_p95": _p95(connect),
        "probe_ttfb_p95": _p95(ttfb),
        "probe_total_p95": _p95(total),
        "probe_connect_samples": connect,
        "probe_ttfb_samples": ttfb,
        "probe_total_samples": total,
        "tc_snapshots": snapshots,
        "probe_return_code": probe_code,
        "probe_stderr": probe_err.strip(),
    }
    return report


def _print_report(report: dict[str, Any]) -> None:
    print(f"node={report.get('node_code') or '-'} iface={report.get('iface') or '-'}")
    print(
        "p95 connect="
        f"{report.get('probe_connect_p95', 0.0):.3f}s ttfb={report.get('probe_ttfb_p95', 0.0):.3f}s "
        f"total={report.get('probe_total_p95', 0.0):.3f}s"
    )
    for snapshot in report.get("tc_snapshots", []):
        print(snapshot)
        print("")
    stderr = str(report.get("probe_stderr") or "").strip()
    if stderr:
        print(stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a qdisc smoke with heavy flow and HTTPS probes.")
    ap.add_argument("--profiles", default=str(DEFAULT_PROFILES))
    ap.add_argument("--node-code", default="", help="node code from repo-truth profile catalog")
    ap.add_argument("--host", default="", help="remote host to connect to; omit for local execution")
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--probe-url", default="https://1.1.1.1/cdn-cgi/trace")
    ap.add_argument("--heavy-url", default="https://speed.cloudflare.com/__down?bytes=50000000")
    ap.add_argument("--probe-attempts", type=int, default=8)
    ap.add_argument("--probe-pause-seconds", type=float, default=1.0)
    ap.add_argument("--heavy-timeout-seconds", type=int, default=120)
    args = ap.parse_args()

    profiles = _load_profiles(Path(args.profiles))
    profile = _select_profile(profiles, args.node_code or None)

    if args.host.strip():
        ssh, _auth_method = connect_node(
            code=profile["node_code"],
            host=args.host.strip(),
            user=args.ssh_user,
            port=args.ssh_port,
            passwords_path=Path(args.passwords),
        )
        try:
            executor = lambda cmd: _run_remote(ssh, cmd)
            report = run_smoke(
                profile,
                probe_url=args.probe_url,
                heavy_url=args.heavy_url,
                probe_attempts=args.probe_attempts,
                probe_pause_seconds=args.probe_pause_seconds,
                heavy_timeout_seconds=args.heavy_timeout_seconds,
                executor=executor,
            )
        finally:
            ssh.close()
    else:
        report = run_smoke(
            profile,
            probe_url=args.probe_url,
            heavy_url=args.heavy_url,
            probe_attempts=args.probe_attempts,
            probe_pause_seconds=args.probe_pause_seconds,
            heavy_timeout_seconds=args.heavy_timeout_seconds,
            executor=_run_local,
        )

    _print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
