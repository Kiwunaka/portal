from __future__ import annotations

import argparse
import json
import os
import shlex
import socket
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
    parser.add_argument("--source", choices=("local", "phone"), default="phone")
    parser.add_argument(
        "--reply-source",
        choices=("route", "ingress", "snat", "policy"),
        default="route",
        help="Use the route-selected source or preserve the received destination address.",
    )
    parser.add_argument("--adb", default="")
    parser.add_argument("--phone-probe", default="")
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
        if (
            len(parts) == 2
            and parts[1] == "device"
            and parts[0]
            not in {
                "emulator-5554",
                "127.0.0.1:5555",
            }
        ):
            devices.append(parts[0])
    if len(devices) != 1:
        raise RuntimeError("exactly one physical phone must be connected")
    return devices[0]


def _service_ready(node: Any, interface: str, port: int) -> bool:
    service = f"pokrov-awg-lab@{interface}.service"
    return _run_remote(
        node, f"systemctl is-active {service}"
    ) == "active" and _run_remote(
        node, f"/usr/local/bin/awg show {interface} listen-port"
    ) == str(port)


def _echo_command(port: int, reply_source: str = "route") -> str:
    if reply_source == "ingress":
        code = f"""import socket,struct,time
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
pktinfo=getattr(socket,'IP_PKTINFO',8)
s.setsockopt(socket.SOL_IP,pktinfo,1)
s.bind(('0.0.0.0',{port}))
s.settimeout(.5)
deadline=time.monotonic()+12
count=0
matches=0
while time.monotonic()<deadline:
 try:
  payload,ancillary,_flags,source=s.recvmsg(512,128)
  if payload == b'P'*{PAYLOAD_SIZE}:
   info=next((data for level,kind,data in ancillary if level == socket.SOL_IP and kind == pktinfo),None)
   if info is None or len(info) < 12:
    continue
   ifindex,spec_dst,dst=struct.unpack('I4s4s',info[:12])
   selected=spec_dst if spec_dst != b'\\0'*4 else dst
   route=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
   route.connect(source)
   route_src=socket.inet_aton(route.getsockname()[0])
   route.close()
   matches += int(route_src == selected)
   control=struct.pack('I4s4s',ifindex,selected,b'\\0'*4)
   count += 1
   s.sendmsg([payload],[(socket.SOL_IP,pktinfo,control)],0,source)
 except TimeoutError:
  pass
print(count,matches)
"""
    else:
        code = f"""import socket,struct,time
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_IP,getattr(socket,'IP_PKTINFO',8),1)
s.bind(('0.0.0.0',{port}))
s.settimeout(.5)
deadline=time.monotonic()+12
count=0
matches=0
while time.monotonic()<deadline:
 try:
  payload,ancillary,_flags,source=s.recvmsg(512,128)
  if payload == b'P'*{PAYLOAD_SIZE}:
   info=next((data for level,kind,data in ancillary if level == socket.SOL_IP and kind == getattr(socket,'IP_PKTINFO',8)),None)
   if info is None or len(info) < 12:
    continue
   _ifindex,spec_dst,dst=struct.unpack('I4s4s',info[:12])
   selected=spec_dst if spec_dst != b'\\0'*4 else dst
   route=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
   route.connect(source)
   route_src=socket.inet_aton(route.getsockname()[0])
   route.close()
   matches += int(route_src == selected)
   count += 1
   s.sendto(payload,source)
 except TimeoutError:
  pass
print(count,matches)
"""
    return "python3 -c " + shlex.quote(code)


def _probe_local(host: str, port: int) -> bool:
    payload = b"P" * PAYLOAD_SIZE
    received = 0
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(0.5)
        for _ in range(SEND_COUNT):
            sock.sendto(payload, (host, port))
            time.sleep(0.1)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and received < SEND_COUNT:
            try:
                echoed, _source = sock.recvfrom(512)
            except TimeoutError:
                continue
            received += int(echoed == payload)
    return received == SEND_COUNT


def _temporary_snat_rule(
    interface: str, port: int, address: str, operation: str
) -> str:
    position = " 1" if operation == "-I" else ""
    comment = f"POKROV owned {interface} roundtrip temporary reply source"
    return (
        f"iptables -t nat {operation} POSTROUTING{position} -o eth0 -p udp "
        f"-m udp --sport {port} -m comment --comment {shlex.quote(comment)} "
        f"-j SNAT --to-source {address}"
    )


def _temporary_policy_commands(port: int, address: str) -> tuple[str, str, str]:
    priority = 10_000 + port
    table = 20_000 + port
    preflight = (
        f"if ip -4 rule show | grep -q '^{priority}:'; then printf occupied; "
        f"elif ip -4 route show table {table} | grep -q .; then printf occupied; "
        "else printf free; fi"
    )
    apply = (
        "set -eu; gateway=$(ip -4 route show table main default | "
        "awk 'NR==1 { for(i=1;i<=NF;i++) if($i==\"via\") { print $(i+1); exit } }'); "
        'test -n "$gateway"; '
        f'ip -4 route replace table {table} default via "$gateway" dev eth0 src {address}; '
        f"ip -4 rule add priority {priority} ipproto udp sport {port} lookup {table}; "
        "ip -4 route flush cache"
    )
    cleanup = (
        f"ip -4 rule del priority {priority} 2>/dev/null || true; "
        f"ip -4 route flush table {table}; ip -4 route flush cache"
    )
    return preflight, apply, cleanup


def _finalize_report(report: dict[str, Any]) -> bool:
    source_echo = report.get("source_received_valid_echo")
    if source_echo is None:
        source_echo = report.get("phone_received_valid_echo")
    report["roundtrip_pass"] = bool(report.get("server_received_all")) and bool(
        source_echo
    )
    report["execution_safe"] = (
        bool(report.get("service_restored"))
        and bool(report.get("temporary_snat_removed", True))
        and bool(report.get("temporary_policy_removed", True))
    )
    report["ok"] = report["execution_safe"] and report["roundtrip_pass"]
    return bool(report["ok"])


def main() -> int:
    args = _parse_args()
    known_hosts = Path(args.known_hosts).resolve()
    passwords = Path(args.passwords).resolve()
    adb = Path(args.adb).resolve() if args.adb else None
    phone_probe = Path(args.phone_probe).resolve() if args.phone_probe else None
    source = str(args.source)
    reply_source = str(args.reply_source)
    profile = str(args.profile)
    interface, port = PROFILES[profile]
    service = f"pokrov-awg-lab@{interface}.service"
    if not known_hosts.is_file() or not passwords.is_file():
        raise SystemExit("required trust or authentication input is missing")
    if source == "phone" and (
        adb is None
        or not adb.is_file()
        or phone_probe is None
        or not phone_probe.is_file()
    ):
        raise SystemExit("ADB and phone probe inputs are required for phone source")
    report: dict[str, Any] = {
        "schema_version": "pokrov-owned-awg-udp-roundtrip-v1",
        "mode": "APPLY" if args.apply else "PLAN",
        "profile": profile,
        "source": source,
        "reply_source": reply_source,
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
    temporary_snat_added = False
    temporary_snat_removed = True
    temporary_policy_touched = False
    temporary_policy_removed = True
    try:
        node_host = _node_host(brain)
        node, _node_auth = connect_node(
            code="de", host=node_host, passwords_path=passwords
        )
        if not _service_ready(node, interface, port):
            raise RuntimeError("AWG service precondition failed")
        if source == "phone":
            assert adb is not None and phone_probe is not None
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
        if reply_source == "snat":
            target_address = socket.gethostbyname(node_host)
            _run_remote(
                node,
                _temporary_snat_rule(interface, port, target_address, "-I"),
            )
            temporary_snat_added = True
            temporary_snat_removed = False
        if reply_source == "policy":
            target_address = socket.gethostbyname(node_host)
            preflight, apply_policy, _cleanup = _temporary_policy_commands(
                port, target_address
            )
            if _run_remote(node, preflight) != "free":
                raise RuntimeError("temporary AWG reply policy slot is occupied")
            temporary_policy_touched = True
            temporary_policy_removed = False
            _run_remote(node, apply_policy)
        _stdin, stdout, stderr = node.exec_command(
            _echo_command(port, "ingress" if reply_source == "ingress" else "route"),
            timeout=30,
        )
        time.sleep(2)
        if source == "phone":
            assert adb is not None
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
            source_echo = completed.returncode == 0
        else:
            source_echo = _probe_local(node_host, port)
        code = stdout.channel.recv_exit_status()
        observed_text = stdout.read().decode("ascii", "strict").strip()
        error = stderr.read().decode("utf-8", "replace").strip()
        if code != 0:
            raise RuntimeError((error or "remote UDP echo failed")[:240])
        safe_counts = observed_text.split()
        if len(safe_counts) != 2:
            raise RuntimeError("remote UDP source classification failed")
        observed, route_source_matches = map(int, safe_counts)
        report.update(
            {
                "sent_packets": SEND_COUNT,
                "server_observed_packets": observed,
                "server_received_all": observed == SEND_COUNT,
                "source_received_valid_echo": source_echo,
                "route_source_matches_ingress": (
                    route_source_matches == observed and observed > 0
                ),
            }
        )
        if source == "phone":
            report["phone_received_valid_echo"] = source_echo
    finally:
        if probe_pushed and serial and adb is not None:
            subprocess.run(
                [str(adb), "-s", serial, "shell", "rm", "-f", REMOTE_PROBE],
                capture_output=True,
                timeout=10,
                check=False,
            )
        if node is not None and temporary_snat_added:
            try:
                _run_remote(
                    node,
                    _temporary_snat_rule(
                        interface,
                        port,
                        socket.gethostbyname(node_host),
                        "-D",
                    ),
                )
                temporary_snat_removed = True
            except Exception:
                temporary_snat_removed = False
        report["temporary_snat_removed"] = temporary_snat_removed
        if node is not None and temporary_policy_touched:
            try:
                _preflight, _apply, cleanup_policy = _temporary_policy_commands(
                    port, socket.gethostbyname(node_host)
                )
                _run_remote(node, cleanup_policy)
                temporary_policy_removed = True
            except Exception:
                temporary_policy_removed = False
        report["temporary_policy_removed"] = temporary_policy_removed
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
