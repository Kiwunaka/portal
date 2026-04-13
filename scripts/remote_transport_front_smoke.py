#!/usr/bin/env python3
from __future__ import annotations

"""
Run a small TLS smoke against the node-local transport-front listener.

This only checks whether the :443 mux accepts the TLS hello for the provided
SNI and returns a normal certificate chain. It does not assert higher-level
gRPC or Reality behavior.
"""

import argparse
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from node_access import DEFAULT_PASSWORDS, connect_node


def build_tls_probe_command(*, address: str, server_name: str, port: int = 443) -> str:
    return (
        "printf '' | openssl s_client -brief "
        f"-connect {shlex.quote(str(address).strip())}:{int(port)} "
        f"-servername {shlex.quote(str(server_name).strip())}"
    )


def parse_tls_probe_output(stdout: str, stderr: str) -> dict[str, Any]:
    output = str(stdout or "").strip()
    error_text = str(stderr or "").strip()

    protocol_match = re.search(r"Protocol version:\s*([^\s]+)", output, flags=re.IGNORECASE)
    cert_match = re.search(r"Peer certificate:\s*CN\s*=\s*([^\n]+)", output, flags=re.IGNORECASE)
    if cert_match is None:
        cert_match = re.search(r"subject=.*?CN\s*=\s*([^,\n/]+)", output, flags=re.IGNORECASE)

    protocol = protocol_match.group(1).strip() if protocol_match else ""
    server_name = cert_match.group(1).strip() if cert_match else ""
    ok = bool(output and "CONNECTION ESTABLISHED" in output.upper() and protocol and server_name and not error_text)

    return {
        "ok": ok,
        "protocol": protocol,
        "server_name": server_name,
        "error": "" if ok else error_text,
    }


def _run_local(cmd: str) -> tuple[int, str, str]:
    proc = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def _run_remote(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    _stdin, stdout, stderr = ssh.exec_command(f"bash -lc {shlex.quote(cmd)}", timeout=timeout)
    code = stdout.channel.recv_exit_status()
    return code, stdout.read().decode("utf-8", errors="replace"), stderr.read().decode("utf-8", errors="replace")


def run_probe(*, address: str, server_name: str, executor=_run_local) -> dict[str, Any]:
    command = build_tls_probe_command(address=address, server_name=server_name)
    code, stdout, stderr = executor(command)
    parsed = parse_tls_probe_output(stdout, stderr)
    parsed.update(
        {
            "address": str(address).strip(),
            "requested_server_name": str(server_name).strip(),
            "command": command,
            "exit_code": int(code),
        }
    )
    if code != 0 and parsed["ok"]:
        parsed["ok"] = False
        parsed["error"] = parsed["error"] or f"probe exited with code {code}"
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="TLS smoke for the node-local transport front listener.")
    parser.add_argument("--address", required=True, help="Front listener address or hostname")
    parser.add_argument("--server-name", action="append", dest="server_names", required=True, help="SNI name to probe; repeatable")
    parser.add_argument("--host", default="", help="Optional remote SSH host; omit for local execution")
    parser.add_argument("--node-code", default="", help="Node code for SSH auth material lookup")
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    args = parser.parse_args()

    executor = _run_local
    ssh = None
    if str(args.host or "").strip():
        ssh, _auth_method = connect_node(
            code=str(args.node_code or "brain").strip().lower() or "brain",
            host=str(args.host).strip(),
            user=args.ssh_user,
            port=int(args.ssh_port),
            passwords_path=Path(args.passwords),
        )
        executor = lambda cmd: _run_remote(ssh, cmd)

    try:
        results = [run_probe(address=args.address, server_name=server_name, executor=executor) for server_name in args.server_names]
    finally:
        if ssh is not None:
            ssh.close()

    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    return 0 if all(item["ok"] for item in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
