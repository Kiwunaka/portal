#!/usr/bin/env python3
"""
Install or render the node-local :443 transport front mux.

The mux is intentionally limited to loopback backends so we do not accidentally
turn it into a general-purpose proxy hop. It only forwards SNI-matched traffic
to local listeners that already exist on the node.
"""

from __future__ import annotations

import argparse
import ipaddress
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

from node_access import DEFAULT_PASSWORDS, connect_node  # noqa: E402


DEFAULT_UNIT_NAME = "portal-transport-front"
DEFAULT_REMOTE_CONFIG_PATH = "/etc/portal-transport-front.cfg"
DEFAULT_REMOTE_SERVICE_PATH = f"/etc/systemd/system/{DEFAULT_UNIT_NAME}.service"
DEFAULT_BIND_ADDRESS = ":443"
DEFAULT_ROUTE_NAME = "legacy_reality_fallback"
ROUTE_NAME_RE = re.compile(r"[a-z][a-z0-9_]{0,63}")
DOMAIN_LABEL_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")
DEFAULT_ROUTES = [
    {
        "name": "legacy_reality_fallback",
        "server_names": ["connect.pokrov.space"],
        "backend_host": "127.0.0.1",
        "backend_port": 10443,
    },
    {
        "name": "grpc_443_primary",
        "server_names": ["grpc.connect.pokrov.space", "mux.connect.pokrov.space"],
        "backend_host": "127.0.0.1",
        "backend_port": 11443,
    },
    {
        "name": "reserve_xhttp_cdn",
        "server_names": ["cdn.connect.pokrov.space"],
        "backend_host": "127.0.0.1",
        "backend_port": 12443,
    },
]

SERVICE_TEMPLATE = (REPO_ROOT / "infra" / "portal-transport-front.service").read_text(encoding="utf-8")


def _clean_text(value: Any, *, lower: bool = False) -> str:
    text = str(value or "").strip()
    return text.lower() if lower else text


def _normalize_server_names(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [item for item in values.split(",")]
    if not isinstance(values, list):
        raise ValueError("transport front route requires server_names")

    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        server_name = _normalize_server_name(item)
        if not server_name:
            continue
        if server_name in seen:
            continue
        seen.add(server_name)
        out.append(server_name)
    return out


def _normalize_server_name(value: Any) -> str:
    server_name = _clean_text(value, lower=True).rstrip(".")
    if not server_name or len(server_name) > 253:
        raise ValueError("transport front server name is empty or too long")
    try:
        ipaddress.ip_address(server_name)
    except ValueError:
        pass
    else:
        raise ValueError("transport front server name must be a DNS name")
    labels = server_name.split(".")
    if len(labels) < 2 or any(not DOMAIN_LABEL_RE.fullmatch(label) for label in labels):
        raise ValueError(f"transport front server name is invalid: {server_name}")
    return server_name


def _normalize_backend_host(value: Any) -> str:
    host = _clean_text(value)
    if not host:
        raise ValueError("transport front route requires backend_host")
    if host == "localhost":
        return host
    try:
        addr = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError(f"transport front backend_host must be a loopback address: {host}") from exc
    if not addr.is_loopback:
        raise ValueError(f"transport front backend_host must stay loopback-only: {host}")
    return host


def _normalize_backend_port(value: Any) -> int:
    try:
        port = int(value)
    except Exception as exc:
        raise ValueError(f"invalid backend_port: {value!r}") from exc
    if port <= 0 or port > 65535:
        raise ValueError(f"backend_port out of range: {port}")
    return port


def normalize_transport_front_route(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("transport front route must be an object")

    name = _clean_text(raw.get("name"))
    if not ROUTE_NAME_RE.fullmatch(name):
        raise ValueError("transport front route requires a safe lowercase name")

    server_names = _normalize_server_names(raw.get("server_names"))
    server_name_suffixes = _normalize_server_names(raw.get("server_name_suffixes"))
    if not server_names and not server_name_suffixes:
        raise ValueError("transport front route requires a server name or suffix")
    send_proxy_v2 = raw.get("send_proxy_v2", False)
    if not isinstance(send_proxy_v2, bool):
        raise ValueError("transport front send_proxy_v2 must be a boolean")

    return {
        "name": name,
        "server_names": server_names,
        "server_name_suffixes": server_name_suffixes,
        "backend_host": _normalize_backend_host(raw.get("backend_host")),
        "backend_port": _normalize_backend_port(raw.get("backend_port")),
        "send_proxy_v2": send_proxy_v2,
    }


def default_transport_front_routes() -> list[dict[str, Any]]:
    return [normalize_transport_front_route(route) for route in DEFAULT_ROUTES]


def load_transport_front_routes(path: Path | str) -> tuple[list[dict[str, Any]], str, str]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        routes_raw = payload.get("routes")
        bind_address = _clean_text(payload.get("bind_address"), lower=False) or DEFAULT_BIND_ADDRESS
        default_route_name = _clean_text(payload.get("default_route_name")) or DEFAULT_ROUTE_NAME
    else:
        routes_raw = payload
        bind_address = DEFAULT_BIND_ADDRESS
        default_route_name = DEFAULT_ROUTE_NAME

    if not isinstance(routes_raw, list):
        raise ValueError("transport front route payload must be a list or {routes: [...]}")
    routes = [normalize_transport_front_route(item) for item in routes_raw]
    return routes, bind_address, default_route_name


def render_transport_front_config(
    routes: list[dict[str, Any]],
    *,
    bind_address: str = DEFAULT_BIND_ADDRESS,
    default_route_name: str = DEFAULT_ROUTE_NAME,
) -> str:
    normalized_routes = [normalize_transport_front_route(route) for route in routes]
    if not normalized_routes:
        raise ValueError("transport front requires at least one route")

    names = [str(route["name"]) for route in normalized_routes]
    if len(names) != len(set(names)):
        raise ValueError("transport front route names must be unique")
    if default_route_name not in names:
        raise ValueError(f"default route {default_route_name!r} is not defined")

    owned_matches: dict[tuple[str, str], str] = {}
    for route in normalized_routes:
        for match_type, values in (
            ("exact", route["server_names"]),
            ("suffix", route["server_name_suffixes"]),
        ):
            for value in values:
                key = (match_type, value)
                previous = owned_matches.get(key)
                if previous is not None and previous != route["name"]:
                    raise ValueError(f"transport front SNI match {value!r} is assigned to multiple routes")
                owned_matches[key] = route["name"]

    lines = [
        "global",
        "    log stdout format raw local0",
        "    maxconn 4096",
        "",
        "defaults",
        "    log global",
        "    mode tcp",
        "    timeout connect 5s",
        "    timeout client 60s",
        "    timeout server 60s",
        "",
        "frontend fe_transport_front",
        f"    bind {bind_address}",
        "    mode tcp",
        "    tcp-request inspect-delay 5s",
        "    tcp-request content accept if { req.ssl_hello_type 1 }",
    ]

    for route in normalized_routes:
        backend_name = f"be_{route['name']}"
        for server_name in route["server_names"]:
            lines.append(f"    use_backend {backend_name} if {{ req.ssl_sni -i {server_name} }}")
        for suffix in route["server_name_suffixes"]:
            lines.append(f"    use_backend {backend_name} if {{ req.ssl_sni -i {suffix} }}")
            lines.append(f"    use_backend {backend_name} if {{ req.ssl_sni -m end -i .{suffix} }}")
    lines.append(f"    default_backend be_{default_route_name}")

    for route in normalized_routes:
        proxy_protocol = " send-proxy-v2" if route["send_proxy_v2"] else ""
        lines.extend(
            [
                "",
                f"backend be_{route['name']}",
                "    mode tcp",
                "    option tcp-check",
                f"    server {route['name']} {route['backend_host']}:{route['backend_port']} check{proxy_protocol}",
            ]
        )

    return "\n".join(lines) + "\n"


def render_transport_front_service(
    *,
    unit_name: str = DEFAULT_UNIT_NAME,
    config_path: str = DEFAULT_REMOTE_CONFIG_PATH,
) -> str:
    return (
        SERVICE_TEMPLATE.replace("/etc/portal-transport-front.cfg", str(config_path).strip())
        .replace("portal-transport-front", str(unit_name).strip())
    )


def build_apply_commands(
    *,
    unit_name: str = DEFAULT_UNIT_NAME,
    config_path: str = DEFAULT_REMOTE_CONFIG_PATH,
) -> list[str]:
    quoted_config = shlex.quote(str(config_path).strip())
    unit = shlex.quote(str(unit_name).strip())
    return [
        f"haproxy -c -f {quoted_config}",
        "systemctl daemon-reload",
        f"systemctl enable {unit}",
        f"systemctl restart {unit}",
        f"systemctl status --no-pager {unit}",
        "ss -tlnp | grep -E '(^|[[:space:]])LISTEN.*:443([[:space:]]|$)' || true",
    ]


def _run_remote(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    _stdin, stdout, stderr = ssh.exec_command(f"bash -lc {shlex.quote(cmd)}", timeout=timeout)
    code = stdout.channel.recv_exit_status()
    return code, stdout.read().decode("utf-8", errors="replace"), stderr.read().decode("utf-8", errors="replace")


def _run_local(cmd: str) -> tuple[int, str, str]:
    proc = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def _write_remote_file(ssh: paramiko.SSHClient, remote_path: str, content: str) -> None:
    sftp = ssh.open_sftp()
    try:
        with sftp.file(remote_path, "w") as handle:
            handle.write(content)
    finally:
        sftp.close()


def _apply_remote_assets(
    ssh: paramiko.SSHClient,
    *,
    config_text: str,
    service_text: str,
    remote_config_path: str,
    remote_service_path: str,
    unit_name: str,
) -> None:
    config_dir = str(Path(remote_config_path).parent).replace("\\", "/")
    service_dir = str(Path(remote_service_path).parent).replace("\\", "/")
    code, out, err = _run_remote(ssh, f"mkdir -p {shlex.quote(config_dir)} {shlex.quote(service_dir)}")
    if code != 0:
        raise SystemExit((err or out or "failed to create transport-front directories").strip())

    _write_remote_file(ssh, remote_config_path, config_text)
    _write_remote_file(ssh, remote_service_path, service_text)

    for command in build_apply_commands(unit_name=unit_name, config_path=remote_config_path):
        code, out, err = _run_remote(ssh, command)
        if code != 0:
            raise SystemExit((err or out or f"transport-front apply failed: {command}").strip())
        text = (out or err).strip()
        if text:
            print(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render and apply the node-local transport-front :443 mux.")
    parser.add_argument("--host", default="", help="Remote node host; omit with --dry-run to print assets only")
    parser.add_argument("--node-code", default="", help="Node code for SSH auth material lookup")
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--routes-json", default="", help="Optional JSON file with {routes, bind_address, default_route_name}")
    parser.add_argument("--bind-address", default=DEFAULT_BIND_ADDRESS)
    parser.add_argument("--default-route-name", default=DEFAULT_ROUTE_NAME)
    parser.add_argument("--config-path", default=DEFAULT_REMOTE_CONFIG_PATH)
    parser.add_argument("--service-path", default=DEFAULT_REMOTE_SERVICE_PATH)
    parser.add_argument("--unit-name", default=DEFAULT_UNIT_NAME)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.routes_json:
        routes, bind_address, default_route_name = load_transport_front_routes(args.routes_json)
    else:
        routes = default_transport_front_routes()
        bind_address = str(args.bind_address or DEFAULT_BIND_ADDRESS).strip() or DEFAULT_BIND_ADDRESS
        default_route_name = str(args.default_route_name or DEFAULT_ROUTE_NAME).strip() or DEFAULT_ROUTE_NAME

    config_text = render_transport_front_config(
        routes,
        bind_address=bind_address,
        default_route_name=default_route_name,
    )
    service_text = render_transport_front_service(
        unit_name=args.unit_name,
        config_path=args.config_path,
    )

    if args.dry_run or not str(args.host or "").strip():
        print("### portal-transport-front.service")
        print(service_text.rstrip())
        print("")
        print("### portal-transport-front.cfg")
        print(config_text.rstrip())
        print("")
        print("### apply-commands")
        for command in build_apply_commands(unit_name=args.unit_name, config_path=args.config_path):
            print(command)
        if args.dry_run:
            return 0
        raise SystemExit("--host is required unless --dry-run is used")

    node_code = _clean_text(args.node_code, lower=True) or "brain"
    ssh, auth_method = connect_node(
        code=node_code,
        host=str(args.host).strip(),
        user=args.ssh_user,
        port=int(args.ssh_port),
        passwords_path=Path(args.passwords),
    )
    try:
        print(f"transport_front_auth={auth_method}")
        _apply_remote_assets(
            ssh,
            config_text=config_text,
            service_text=service_text,
            remote_config_path=str(args.config_path).strip(),
            remote_service_path=str(args.service_path).strip(),
            unit_name=str(args.unit_name).strip(),
        )
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
