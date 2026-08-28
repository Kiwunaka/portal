from __future__ import annotations

import argparse
import base64
import json
import os
import socket
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from node_access import DEFAULT_PASSWORDS, connect_node
from remote_activate_owned_awg_labs import _node_host
from remote_run_owned_awg_core_interop import _load_material


PROFILE_SERVER = {
    "awg2_lab": ("pokrovawg2", 4500),
    "awg31_lab": ("pokrovawg31", 3478),
}
CONFIG_ROOT = "/etc/amnezia/amneziawg"
AWG = "/usr/local/bin/awg"


def _public_key(private_key: str) -> str:
    private_raw = base64.b64decode(private_key, validate=True)
    if len(private_raw) != 32:
        raise RuntimeError("private key length invalid")
    public_raw = (
        X25519PrivateKey.from_private_bytes(private_raw)
        .public_key()
        .public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    )
    return base64.b64encode(public_raw).decode("ascii")


def _parse_config(raw: bytes) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    current = ""
    for raw_line in raw.decode("utf-8", "strict").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            sections.setdefault(current, {})
            continue
        if "=" in line and current:
            key, value = line.split("=", 1)
            sections[current][key.strip()] = value.strip()
    return sections


def _normalize_padding(value: object) -> str:
    normalized = str(value or "").strip()
    return normalized or "0"


def _normalize_enabled(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "on", "true", "yes"}


def _run(client, command: str) -> str:
    _stdin, stdout, stderr = client.exec_command(command, timeout=30)
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode("utf-8", "replace").strip()
    error = stderr.read().decode("utf-8", "replace").strip()
    if code != 0:
        raise RuntimeError((error or "remote AWG readback failed")[:240])
    return output


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare owned AWG control-plane material with the live server without returning keys."
    )
    parser.add_argument("profile", choices=tuple(PROFILE_SERVER))
    parser.add_argument("--brain-ip", default="82.21.114.104")
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--known-hosts", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    known_hosts = Path(args.known_hosts).resolve()
    passwords = Path(args.passwords).resolve()
    if not known_hosts.is_file() or not passwords.is_file():
        raise SystemExit("SSH trust or authentication input is missing")
    os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)

    brain, _brain_auth = connect_node(
        code="brain",
        host=str(args.brain_ip),
        passwords_path=passwords,
    )
    node = None
    material = bytearray()
    server_config = bytearray()
    try:
        material = bytearray(_load_material(brain, str(args.profile)))
        endpoint = json.loads(material)
        node_host = _node_host(brain)
        node, _node_auth = connect_node(
            code="de",
            host=node_host,
            passwords_path=passwords,
        )
        interface, expected_port = PROFILE_SERVER[str(args.profile)]
        sftp = node.open_sftp()
        try:
            with sftp.open(f"{CONFIG_ROOT}/{interface}.conf", "rb") as handle:
                server_config = bytearray(handle.read(64 * 1024 + 1))
        finally:
            sftp.close()
        if not 1 <= len(server_config) <= 64 * 1024:
            raise RuntimeError("server AWG configuration size invalid")
        parsed = _parse_config(server_config)
        server_interface = parsed.get("Interface", {})
        server_peer = parsed.get("Peer", {})
        endpoint_peer = endpoint["peers"][0]

        live_private = _run(node, f"{AWG} show {interface} private-key")
        live_peers = _run(node, f"{AWG} show {interface} peers").splitlines()
        live_port = _run(node, f"{AWG} show {interface} listen-port")
        live_config = _parse_config(
            _run(node, f"{AWG} showconf {interface}").encode("utf-8")
        )
        live_interface = live_config.get("Interface", {})

        field_pairs = {
            "S1": "s1",
            "S2": "s2",
            "S3": "s3",
            "S4": "s4",
            "H1": "h1",
            "H2": "h2",
            "H3": "h3",
            "H4": "h4",
        }
        protocol_fields_match = all(
            str(live_interface.get(server_key, "0"))
            == str(endpoint.get(endpoint_key, "0"))
            for server_key, endpoint_key in field_pairs.items()
        )
        expected_header_key = str(endpoint.get("header_protection_key") or "")
        server_header_key = str(live_interface.get("HeaderProtectionKey") or "")
        checks = {
            "server_private_matches_live": live_private
            == str(server_interface.get("PrivateKey") or ""),
            "server_public_matches_endpoint": _public_key(live_private)
            == str(endpoint_peer.get("public_key") or ""),
            "client_public_matches_server_peer": _public_key(
                str(endpoint.get("private_key") or "")
            )
            == str(server_peer.get("PublicKey") or ""),
            "client_public_matches_live_peer": len(live_peers) == 1
            and _public_key(str(endpoint.get("private_key") or "")) == live_peers[0],
            "listen_port_matches": live_port == str(expected_port)
            and str(server_interface.get("ListenPort") or "") == str(expected_port)
            and int(endpoint_peer.get("port") or 0) == expected_port,
            "node_address_matches": socket.gethostbyname(str(endpoint_peer["address"]))
            == socket.gethostbyname(node_host),
            "tunnel_address_matches": str(server_peer.get("AllowedIPs") or "")
            in {str(value) for value in endpoint.get("address") or []},
            "protocol_fields_match": protocol_fields_match,
            "header_protection_key_matches": expected_header_key == server_header_key,
            "content_padding_addition_matches": _normalize_padding(
                endpoint.get("content_padding_addition")
            )
            == _normalize_padding(live_interface.get("ContentPaddingAddition")),
            "random_trailers_matches": bool(endpoint.get("random_trailers"))
            == _normalize_enabled(live_interface.get("RandomTrailers")),
        }
        ok = all(checks.values())
        print(
            json.dumps(
                {
                    "schema_version": "pokrov-owned-awg-alignment-v2",
                    "profile": str(args.profile),
                    "ok": ok,
                    "checks": checks,
                    "raw_material_returned": False,
                },
                sort_keys=True,
            )
        )
        return 0 if ok else 1
    finally:
        if node is not None:
            node.close()
        brain.close()
        for buffer in (material, server_config):
            for index in range(len(buffer)):
                buffer[index] = 0


if __name__ == "__main__":
    raise SystemExit(main())
