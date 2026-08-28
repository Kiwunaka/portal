from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any

from node_access import DEFAULT_PASSWORDS, connect_node
from remote_activate_owned_awg_labs import (
    AWG2_INTERFACE,
    AWG2_PORT,
    AWG31_INTERFACE,
    AWG31_PORT,
    _node_host,
    _run_remote,
)


PAYLOAD_SIZE = 37
SEND_COUNT = 3
REMOTE_PROBE = "/data/local/tmp/pokrov-udp-roundtrip-probe"
PROFILES = {
    "awg2_lab": (AWG2_INTERFACE, AWG2_PORT),
    "awg31_lab": (AWG31_INTERFACE, AWG31_PORT),
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Guarded plain-UDP round-trip probe on one owned AWG port."
    )
    parser.add_argument("--profile", choices=tuple(PROFILES), default="awg31_lab")
    parser.add_argument("--adb", required=True)
    parser.add_argument("--phone-probe", required=True)
    parser.add_argument("--brain-ip", default="82.21.114.104")
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--known-hosts", required=True)
    parser.add_argument("--confirm-profile", default="")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def _phone_serial(adb: Path) -> str:
    completed = subprocess.run(
        [str(adb), "devices"],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    devices = []
    for line in completed.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == "device" and parts[0] not in {
            "emulator-5554",
            "127.0.0.1:5555",
        }:
            devices.append(parts[0])
    if len(devices) != 1:
        raise RuntimeError("exactly one physical phone must be connected")
    return devices[0]


def _service_ready(node: Any, interface: str, port: int) -> bool:
    service = f"pokrov-awg-lab@{interface}.service"
    return (
        _run_remote(node, f"systemctl is-active {service}") == "active"
        and _run_remote(node, f"/usr/local/bin/awg show {interface} listen-port")
        == str(port)
    )


def _echo_command(port: int) -> str:
    code = f"""import socket,time
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('0.0.0.0',{port}))
s.settimeout(.5)
deadline=time.monotonic()+12
count=0
while time.monotonic()<deadline:
 try:
  payload,source=s.recvfrom(512)
  if payload == b'P'*{PAYLOAD_SIZE}:
   count += 1
   s.sendto(payload,source)
 except TimeoutError:
  pass
print(count)
"""
    return "python3 -c " + shlex.quote(code)


def _finalize_report(report: dict[str, Any]) -> bool:
    report["roundtrip_pass"] = bool(report.get("server_received_all")) and bool(
        report.get("phone_received_valid_echo")
    )
    report["execution_safe"] = bool(report.get("service_restored"))
    report["ok"] = report["execution_safe"] and report["roundtrip_pass"]
    return bool(report["ok"])


def main() -> int:
    args = _parse_args()
    known_hosts = Path(args.known_hosts).resolve()
    passwords = Path(args.passwords).resolve()
    adb = Path(args.adb).resolve()
    phone_probe = Path(args.phone_probe).resolve()
    profile = str(args.profile)
    interface, port = PROFILES[profile]
    service = f"pokrov-awg-lab@{interface}.service"
    if not all(path.is_file() for path in (known_hosts, passwords, adb, phone_probe)):
        raise SystemExit("required trust, authentication, ADB, or phone probe input is missing")
    report: dict[str, Any] = {
        "schema_version": "pokrov-owned-awg-udp-roundtrip-v1",
        "mode": "APPLY" if args.apply else "PLAN",
        "profile": profile,
        "port": port,
        "service_interruption_required": True,
        "raw_addresses_returned": False,
        "raw_identifiers_returned": False,
    }
    if not args.apply:
        report["ok"] = True
        print(json.dumps(report, sort_keys=True))
        return 0
    if args.confirm_profile != profile:
        raise SystemExit("--confirm-profile mismatch")

    os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)
    brain, _brain_auth = connect_node(
        code="brain", host=str(args.brain_ip), passwords_path=passwords
    )
    node = None
    serial = ""
    service_stopped = False
    probe_pushed = False
    try:
        node_host = _node_host(brain)
        node, _node_auth = connect_node(
            code="de", host=node_host, passwords_path=passwords
        )
        if not _service_ready(node, interface, port):
            raise RuntimeError("AWG service precondition failed")
        serial = _phone_serial(adb)
        subprocess.run(
            [str(adb), "-s", serial, "push", str(phone_probe), REMOTE_PROBE],
            capture_output=True,
            timeout=30,
            check=True,
        )
        probe_pushed = True
        subprocess.run(
            [str(adb), "-s", serial, "shell", "chmod", "0700", REMOTE_PROBE],
            capture_output=True,
            timeout=10,
            check=True,
        )
        _run_remote(node, f"systemctl stop {service}", timeout=120)
        service_stopped = True
        free = _run_remote(
            node,
            f"if ss -H -lun 'sport = :{port}' | grep -q .; then printf busy; else printf free; fi",
        )
        if free != "free":
            raise RuntimeError("AWG port did not become free")
        _stdin, stdout, stderr = node.exec_command(_echo_command(port), timeout=30)
        time.sleep(2)
        completed = subprocess.run(
            [
                str(adb),
                "-s",
                serial,
                "shell",
                REMOTE_PROBE,
                node_host,
                str(port),
                str(PAYLOAD_SIZE),
                str(SEND_COUNT),
                "roundtrip",
            ],
            capture_output=True,
            timeout=15,
            check=False,
        )
        code = stdout.channel.recv_exit_status()
        observed_text = stdout.read().decode("ascii", "strict").strip()
        error = stderr.read().decode("utf-8", "replace").strip()
        if code != 0:
            raise RuntimeError((error or "remote UDP echo failed")[:240])
        observed = int(observed_text)
        report.update(
            {
                "sent_packets": SEND_COUNT,
                "server_observed_packets": observed,
                "server_received_all": observed == SEND_COUNT,
                "phone_received_valid_echo": completed.returncode == 0,
            }
        )
    finally:
        if probe_pushed and serial:
            subprocess.run(
                [str(adb), "-s", serial, "shell", "rm", "-f", REMOTE_PROBE],
                capture_output=True,
                timeout=10,
                check=False,
            )
        if node is not None and service_stopped:
            _run_remote(node, f"systemctl start {service}", timeout=120)
            report["service_restored"] = _service_ready(node, interface, port)
        if node is not None:
            node.close()
        brain.close()
    _finalize_report(report)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
