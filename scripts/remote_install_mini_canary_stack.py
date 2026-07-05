from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import sys
import textwrap
import uuid
from pathlib import Path
from urllib.parse import quote

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from node_access import connect_node

DEFAULT_INVENTORY = REPO_ROOT / "docs" / "08-node-inventory.md"
DEFAULT_XRAY_CONFIG = "/usr/local/etc/xray/config.json"
DEFAULT_HYSTERIA_CONFIG = "/etc/hysteria/config.yaml"
DEFAULT_HYSTERIA_SERVICE = "/etc/systemd/system/hysteria-server.service"
DEFAULT_NGINX_SITE = "/etc/nginx/sites-available/pokrovvpn.duckdns.org"
DEFAULT_HYSTERIA_CERT = "/etc/hysteria/server.crt"
DEFAULT_HYSTERIA_KEY = "/etc/hysteria/server.key"
DEFAULT_LE_CERT = "/etc/letsencrypt/live/pokrovvpn.duckdns.org/fullchain.pem"
DEFAULT_LE_KEY = "/etc/letsencrypt/live/pokrovvpn.duckdns.org/privkey.pem"

XRAY_SERVICE_TEXT = """[Unit]
Description=Xray Service
After=network-online.target nss-lookup.target
Wants=network-online.target

[Service]
User=root
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
NoNewPrivileges=true
ExecStart=/usr/local/bin/xray run -config /usr/local/etc/xray/config.json
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

HYSTERIA_SERVICE_TEXT = """[Unit]
Description=Hysteria 2 Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/hysteria server -c /etc/hysteria/config.yaml
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
NoNewPrivileges=true
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""


def _random_path() -> str:
    return "/pokrov-" + secrets.token_hex(8)


def _random_password() -> str:
    return secrets.token_urlsafe(18)


def _read_inventory_ip(code: str, inventory_path: Path) -> str:
    text = inventory_path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if f"`{code}`" not in line:
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 7:
            continue
        ip = parts[6].strip("` ").strip()
        if ip and ip != "TBD":
            return ip
    raise SystemExit(f"Unable to resolve node IP for {code} from {inventory_path}")


def build_xray_config(
    *,
    client_id: str,
    xhttp_path: str,
    listen: str = "127.0.0.1",
    port: int = 10080,
) -> dict[str, object]:
    return {
        "log": {"loglevel": "warning"},
        "inbounds": [
            {
                "listen": listen,
                "port": port,
                "protocol": "vless",
                "settings": {
                    "clients": [{"id": client_id}],
                    "decryption": "none",
                },
                "streamSettings": {
                    "network": "xhttp",
                    "security": "none",
                    "xhttpSettings": {
                        "path": xhttp_path,
                        "mode": "packet-up",
                    },
                },
            }
        ],
        "outbounds": [{"protocol": "freedom", "tag": "direct"}],
    }


def build_hysteria_config(
    *,
    auth_password: str,
    cert_path: str,
    key_path: str,
    listen: str = ":443",
) -> str:
    return textwrap.dedent(
        f"""
        listen: {listen}
        tls:
          cert: {cert_path}
          key: {key_path}
        auth:
          type: password
          password: {auth_password}
        disableUDP: false
        udpIdleTimeout: 60s
        """
    ).strip() + "\n"


def build_nginx_site_config(
    *,
    xhttp_path: str,
    server_names: list[str],
    cert_path: str,
    key_path: str,
    upstream_port: int = 10080,
    root: str = "/var/www/html",
    index: str = "index.html index.htm",
) -> str:
    server_name_line = " ".join(server_names)
    return textwrap.dedent(
        f"""
        server {{
            listen 80;
            listen 443 ssl;
            server_name {server_name_line};

            ssl_certificate {cert_path};
            ssl_certificate_key {key_path};

            ssl_protocols TLSv1.2 TLSv1.3;
            ssl_ciphers HIGH:!aNULL:!MD5;

            client_max_body_size 300M;

            location ^~ {xhttp_path} {{
                proxy_http_version 1.1;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_buffering off;
                proxy_request_buffering off;
                proxy_read_timeout 86400;
                proxy_send_timeout 86400;
                proxy_pass http://127.0.0.1:{upstream_port};
            }}

            location / {{
                root {root};
                index {index};
            }}
        }}
        """
    ).strip() + "\n"


def build_client_links(
    *,
    endpoint: str,
    sni: str,
    client_id: str,
    xhttp_path: str,
    hy2_password: str,
    allow_insecure: bool = False,
) -> dict[str, str]:
    insecure_vless = "1" if allow_insecure else "0"
    insecure_hy2 = "1" if allow_insecure else "0"
    xhttp_query = (
        f"encryption=none&security=tls&type=xhttp&mode=packet-up&"
        f"path={quote(xhttp_path, safe='')}&host={quote(sni, safe='')}&"
        f"sni={quote(sni, safe='')}&fp=chrome&allowInsecure={insecure_vless}&core=xray"
    )
    hy2_query = f"sni={quote(sni, safe='')}&insecure={insecure_hy2}"
    return {
        "xhttp": f"xvless://{client_id}@{endpoint}:443?{xhttp_query}#mini-xhttp-canary",
        "hysteria2": f"hysteria2://{quote(hy2_password, safe='')}@{endpoint}:443/?{hy2_query}#mini-hy2-canary",
    }


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 180) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def _put_text(sftp: paramiko.SFTPClient, remote_path: str, content: str) -> None:
    with sftp.file(remote_path, "w") as fh:
        fh.write(content)


def _ensure_success(code: int, out: str, err: str, label: str) -> None:
    if code == 0:
        return
    raise SystemExit(f"{label} failed\nOUT:\n{out}\nERR:\n{err}")


def _remote_install_prereqs(ssh: paramiko.SSHClient) -> None:
    cmd = (
        "if command -v curl >/dev/null 2>&1 && "
        "command -v unzip >/dev/null 2>&1 && "
        "command -v nginx >/dev/null 2>&1; then exit 0; fi; "
        "export DEBIAN_FRONTEND=noninteractive; "
        "apt-get update && apt-get install -y curl unzip nginx"
    )
    code, out, err = _run(ssh, f"bash -lc '{cmd}'", timeout=600)
    _ensure_success(code, out, err, "install prereqs")


def _remote_install_xray(ssh: paramiko.SSHClient) -> None:
    cmd = (
        "if command -v xray >/dev/null 2>&1; then exit 0; fi; "
        "curl -fsSL https://raw.githubusercontent.com/XTLS/Xray-install/main/install-release.sh "
        "-o /tmp/install-xray.sh && bash /tmp/install-xray.sh install"
    )
    code, out, err = _run(ssh, f"bash -lc '{cmd}'", timeout=900)
    _ensure_success(code, out, err, "install xray")


def _remote_install_hysteria(ssh: paramiko.SSHClient) -> None:
    cmd = (
        "if command -v hysteria >/dev/null 2>&1; then exit 0; fi; "
        "curl -fsSL https://get.hy2.sh/ | bash"
    )
    code, out, err = _run(ssh, f"bash -lc '{cmd}'", timeout=900)
    _ensure_success(code, out, err, "install hysteria")


def _deploy(
    ssh: paramiko.SSHClient,
    *,
    xray_config: dict[str, object],
    hysteria_config: str,
    nginx_site: str,
    site_path: str,
    source_cert_path: str,
    source_key_path: str,
) -> dict[str, str]:
    sftp = ssh.open_sftp()
    try:
        _run(ssh, "mkdir -p /usr/local/etc/xray /etc/hysteria", timeout=30)
        _put_text(sftp, DEFAULT_XRAY_CONFIG, json.dumps(xray_config, indent=2) + "\n")
        _put_text(sftp, DEFAULT_HYSTERIA_CONFIG, hysteria_config)
        _put_text(sftp, "/etc/systemd/system/xray.service", XRAY_SERVICE_TEXT)
        _put_text(sftp, DEFAULT_HYSTERIA_SERVICE, HYSTERIA_SERVICE_TEXT)
    finally:
        sftp.close()

    backup_cmd = f"if [ -f {site_path} ] && [ ! -f {site_path}.pre-canary ]; then cp {site_path} {site_path}.pre-canary; fi"
    _run(ssh, f"bash -lc '{backup_cmd}'", timeout=60)
    copy_tls_cmd = (
        f"cp {source_cert_path} {DEFAULT_HYSTERIA_CERT} && "
        f"cp {source_key_path} {DEFAULT_HYSTERIA_KEY} && "
        f"chmod 644 {DEFAULT_HYSTERIA_CERT} && chmod 600 {DEFAULT_HYSTERIA_KEY}"
    )
    code, out, err = _run(ssh, f"bash -lc '{copy_tls_cmd}'", timeout=60)
    _ensure_success(code, out, err, "copy hysteria tls files")
    sftp = ssh.open_sftp()
    try:
        _put_text(sftp, site_path, nginx_site)
    finally:
        sftp.close()
    site_name = Path(site_path).name
    enable_site_cmd = f"ln -sfn {site_path} /etc/nginx/sites-enabled/{site_name}"
    code, out, err = _run(ssh, f"bash -lc '{enable_site_cmd}'", timeout=60)
    _ensure_success(code, out, err, "enable nginx site")

    checks = {
        "xray_test": "xray run -test -config /usr/local/etc/xray/config.json",
        "nginx_test": "nginx -t",
        "daemon_reload": "systemctl daemon-reload",
        "enable_services": "systemctl enable xray hysteria-server nginx",
        "restart_services": "systemctl restart xray hysteria-server nginx",
        "service_state": "systemctl is-active xray hysteria-server nginx",
        "listeners": "ss -lntup | grep -E \":443\\\\b|:10080\\\\b\" || true",
    }
    outputs: dict[str, str] = {}
    for name, cmd in checks.items():
        code, out, err = _run(ssh, f"bash -lc '{cmd}'", timeout=240)
        _ensure_success(code, out, err, name)
        outputs[name] = (out or err).strip()
    return outputs


def main() -> int:
    ap = argparse.ArgumentParser(description="Install a temporary XHTTP + Hysteria2 canary ingress on mini.")
    ap.add_argument("--node-code", default="mini")
    ap.add_argument("--host", default="")
    ap.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=22)
    ap.add_argument("--domain", default="pokrovvpn.duckdns.org")
    ap.add_argument("--endpoint", default="pokrovvpn.duckdns.org")
    ap.add_argument("--xhttp-path", default="")
    ap.add_argument("--client-id", default="")
    ap.add_argument("--hy2-password", default="")
    ap.add_argument("--site-path", default=DEFAULT_NGINX_SITE)
    ap.add_argument("--print-links", action="store_true", help="Print live client links. Off by default because links are bearer secrets.")
    ap.add_argument("--print-secrets", action="store_true", help="Print generated client id and Hysteria2 password. Off by default.")
    args = ap.parse_args()

    host = args.host.strip() or _read_inventory_ip(args.node_code, Path(args.inventory))
    xhttp_path = args.xhttp_path.strip() or _random_path()
    if not xhttp_path.startswith("/"):
        xhttp_path = "/" + xhttp_path
    client_id = args.client_id.strip() or str(uuid.uuid4())
    hy2_password = args.hy2_password.strip() or _random_password()

    ssh, auth_method = connect_node(
        code=args.node_code,
        host=host,
        user=args.ssh_user,
        port=args.ssh_port,
    )
    try:
        _remote_install_prereqs(ssh)
        _remote_install_xray(ssh)
        _remote_install_hysteria(ssh)
        outputs = _deploy(
            ssh,
            xray_config=build_xray_config(client_id=client_id, xhttp_path=xhttp_path),
            hysteria_config=build_hysteria_config(
                auth_password=hy2_password,
                cert_path=DEFAULT_HYSTERIA_CERT,
                key_path=DEFAULT_HYSTERIA_KEY,
            ),
            nginx_site=build_nginx_site_config(
                xhttp_path=xhttp_path,
                server_names=[args.domain],
                cert_path=DEFAULT_LE_CERT,
                key_path=DEFAULT_LE_KEY,
            ),
            site_path=args.site_path,
            source_cert_path=DEFAULT_LE_CERT,
            source_key_path=DEFAULT_LE_KEY,
        )
    finally:
        ssh.close()

    links = build_client_links(
        endpoint=args.endpoint.strip() or args.domain,
        sni=args.domain,
        client_id=client_id,
        xhttp_path=xhttp_path,
        hy2_password=hy2_password,
    )
    print(f"mini canary deployed via auth={auth_method}")
    print(f"host={host}")
    print(f"domain={args.domain}")
    print(f"xhttp_path={xhttp_path}")
    print("client_id_sha256=" + hashlib.sha256(client_id.encode("utf-8")).hexdigest())
    print("hy2_password_sha256=" + hashlib.sha256(hy2_password.encode("utf-8")).hexdigest())
    if args.print_secrets:
        print(f"client_id={client_id}")
        print(f"hy2_password={hy2_password}")
    else:
        print("client_id=[redacted]")
        print("hy2_password=[redacted]")
    if args.print_links:
        print("xhttp_link=" + links["xhttp"])
        print("hysteria2_link=" + links["hysteria2"])
    else:
        print("xhttp_link=[redacted]")
        print("hysteria2_link=[redacted]")
    for name, output in outputs.items():
        print(f"[{name}]")
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
