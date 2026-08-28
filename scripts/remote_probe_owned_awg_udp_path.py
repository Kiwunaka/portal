from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time
from pathlib import Path

from node_access import DEFAULT_PASSWORDS, connect_node
from remote_activate_owned_awg_labs import _node_host


PROFILE_PORTS = {
    "awg2_lab": 4500,
    "awg31_lab": 3478,
}
PAYLOAD_SIZE = 37
SEND_COUNT = 5


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the owned AWG UDP path with a fixed-size non-secret marker."
    )
    parser.add_argument("profile", choices=tuple(PROFILE_PORTS))
    parser.add_argument("--node", choices=("de", "brain"), default="de")
    parser.add_argument("--source", choices=("local", "phone"), required=True)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--adb", default="")
    parser.add_argument("--phone-sender", default="")
    parser.add_argument("--brain-ip", default="82.21.114.104")
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--known-hosts", required=True)
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
        if len(parts) == 2 and parts[1] == "device":
            serial = parts[0]
            if serial not in {"emulator-5554", "127.0.0.1:5555"}:
                devices.append(serial)
    if len(devices) != 1:
        raise RuntimeError("exactly one physical phone must be connected")
    return devices[0]


def _send_local(host: str, port: int, payload: bytes) -> None:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(2)
        for _ in range(SEND_COUNT):
            sock.sendto(payload, (host, port))
            time.sleep(0.1)


def _send_phone(
    adb: Path,
    serial: str,
    sender: Path,
    host: str,
    port: int,
) -> None:
    remote_sender = "/data/local/tmp/pokrov-udp-probe"
    try:
        pushed = subprocess.run(
            [str(adb), "-s", serial, "push", str(sender), remote_sender],
            capture_output=True,
            timeout=30,
            check=False,
        )
        if pushed.returncode != 0:
            raise RuntimeError("phone UDP sender deployment failed")
        chmod = subprocess.run(
            [str(adb), "-s", serial, "shell", "chmod", "0700", remote_sender],
            capture_output=True,
            timeout=10,
            check=False,
        )
        if chmod.returncode != 0:
            raise RuntimeError("phone UDP sender permission failed")
        completed = subprocess.run(
            [
                str(adb),
                "-s",
                serial,
                "shell",
                remote_sender,
                host,
                str(port),
                str(PAYLOAD_SIZE),
                str(SEND_COUNT),
            ],
            capture_output=True,
            timeout=15,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError("phone UDP sender unavailable")
    finally:
        subprocess.run(
            [str(adb), "-s", serial, "shell", "rm", "-f", remote_sender],
            capture_output=True,
            timeout=10,
            check=False,
        )


def main() -> int:
    args = _parse_args()
    known_hosts = Path(args.known_hosts).resolve()
    passwords = Path(args.passwords).resolve()
    adb = Path(args.adb).resolve() if args.adb else None
    phone_sender = Path(args.phone_sender).resolve() if args.phone_sender else None
    if not known_hosts.is_file() or not passwords.is_file():
        raise SystemExit("SSH trust or authentication input is missing")
    if args.source == "phone" and (
        adb is None
        or not adb.is_file()
        or phone_sender is None
        or not phone_sender.is_file()
    ):
        raise SystemExit("ADB executable and phone sender are required for phone source")
    if int(args.port) < 0 or int(args.port) > 65535:
        raise SystemExit("port override is invalid")

    os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)
    brain, _brain_auth = connect_node(
        code="brain",
        host=str(args.brain_ip),
        passwords_path=passwords,
    )
    node = None
    try:
        if args.node == "brain":
            node_host = str(args.brain_ip)
            node = brain
        else:
            node_host = _node_host(brain)
            node, _node_auth = connect_node(
                code="de",
                host=node_host,
                passwords_path=passwords,
            )
        port = int(args.port) or PROFILE_PORTS[str(args.profile)]
        if args.node == "brain":
            capture_backend = "udp_socket"
            server_capture_self_test = True
            listener_code = (
                "import socket,time\n"
                "sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)\n"
                f"sock.bind(('0.0.0.0',{port}))\n"
                "sock.settimeout(.5)\n"
                "deadline=time.monotonic()+12\n"
                "count=0\n"
                "while time.monotonic()<deadline:\n"
                " try:\n"
                "  payload,_source=sock.recvfrom(512)\n"
                f"  count += int(payload == b'P'*{PAYLOAD_SIZE})\n"
                " except TimeoutError:\n"
                "  pass\n"
                "print(count)\n"
            )
            capture = "python3 -c " + shlex.quote(listener_code)
        else:
            capture_backend = "tcpdump"
            self_test = (
                "(sleep 1; python3 -c \"import socket,time;"
                "s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);"
                f"[(s.sendto(b'P'*{PAYLOAD_SIZE},('127.0.0.1',{port})),time.sleep(.1)) "
                f"for _ in range({SEND_COUNT})]\") & "
                f"timeout -s INT 4s tcpdump -tt -nn -l -i lo 'udp dst port {port}' "
                f"2>/dev/null | awk '$NF == {PAYLOAD_SIZE} "
                "{ count += 1 } END { print count+0 }'"
            )
            _self_stdin, self_stdout, self_stderr = node.exec_command(self_test, timeout=15)
            self_code = self_stdout.channel.recv_exit_status()
            self_output = self_stdout.read().decode("ascii", "strict").strip()
            self_error = self_stderr.read().decode("utf-8", "replace").strip()
            server_capture_self_test = (
                self_code == 0 and int(self_output or "-1") == SEND_COUNT
            )
            if not server_capture_self_test:
                raise RuntimeError(
                    (self_error or "remote UDP capture self-test failed")[:240]
                )
            capture = (
                f"timeout -s INT 12s tcpdump -tt -nn -l -i any "
                f"'udp dst port {port}' 2>/dev/null | "
                f"awk '$NF == {PAYLOAD_SIZE} {{ count += 1 }} END {{ print count+0 }}'"
            )
        _stdin, stdout, stderr = node.exec_command(capture, timeout=30)
        time.sleep(2)
        payload = b"P" * PAYLOAD_SIZE
        if len(payload) != PAYLOAD_SIZE:
            raise RuntimeError("probe payload size invalid")
        if args.source == "phone":
            serial = _phone_serial(adb)
            _send_phone(adb, serial, phone_sender, node_host, port)
        else:
            _send_local(node_host, port, payload)
        code = stdout.channel.recv_exit_status()
        output = stdout.read().decode("ascii", "strict").strip()
        error = stderr.read().decode("utf-8", "replace").strip()
        if code != 0:
            raise RuntimeError((error or "remote UDP capture failed")[:240])
        observed = int(output)
        print(
            json.dumps(
                {
                    "schema_version": "pokrov-owned-awg-udp-path-v1",
                    "profile": str(args.profile),
                    "node": str(args.node),
                    "port_override": bool(args.port),
                    "source": str(args.source),
                    "sent_packets": SEND_COUNT,
                    "observed_packets": observed,
                    "capture_backend": capture_backend,
                    "server_capture_self_test": server_capture_self_test,
                    "path_reachable": observed == SEND_COUNT,
                    "raw_addresses_returned": False,
                },
                sort_keys=True,
            )
        )
        return 0 if observed == SEND_COUNT else 1
    finally:
        if node is not None and node is not brain:
            node.close()
        brain.close()


if __name__ == "__main__":
    raise SystemExit(main())
