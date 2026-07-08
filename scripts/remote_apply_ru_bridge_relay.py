from __future__ import annotations

import argparse
import ipaddress
import json
import secrets
import shlex
import sys
from pathlib import Path
from typing import Any

import paramiko


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from node_access import DEFAULT_PASSWORDS, connect_node


DEFAULT_BRAIN_HOST = "82.21.114.104"
DEFAULT_MINI_HOST = "176.123.166.119"
DEFAULT_XRAY_CONFIG = "/usr/local/etc/xray/config.json"
DEFAULT_BRIDGE_META = "/etc/portal-ru-bridge/reality.json"
BRIDGE_INBOUND_TAG = "ru-bridge-reality"
BRIDGE_ALLOW_TAG = "ru-bridge-allow"
BRIDGE_BLOCK_TAG = "ru-bridge-block"


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _node_code_base(code: str) -> str:
    text = _clean_text(code).lower()
    for sep in ("_", "-", "."):
        if sep in text:
            text = text.split(sep, 1)[0]
    return text


def _is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    _stdin, stdout, stderr = ssh.exec_command(f"bash -lc {shlex.quote(cmd)}", timeout=timeout)
    code = stdout.channel.recv_exit_status()
    return code, stdout.read().decode("utf-8", errors="replace"), stderr.read().decode("utf-8", errors="replace")


def _remote_read_json(ssh: paramiko.SSHClient, path: str, *, default: dict[str, Any] | None = None) -> dict[str, Any]:
    code, out, _err = _run(ssh, f"if [ -f {shlex.quote(path)} ]; then sudo cat {shlex.quote(path)}; fi")
    if code != 0 or not out.strip():
        return dict(default or {})
    try:
        parsed = json.loads(out)
    except Exception:
        return dict(default or {})
    return parsed if isinstance(parsed, dict) else dict(default or {})


def _remote_write_text(ssh: paramiko.SSHClient, path: str, content: str, *, mode: str = "600") -> None:
    tmp = f"/tmp/{Path(path).name}.{secrets.token_hex(6)}"
    sftp = ssh.open_sftp()
    try:
        with sftp.file(tmp, "w") as handle:
            handle.write(content)
    finally:
        sftp.close()
    parent = str(Path(path).parent).replace("\\", "/")
    cmd = (
        f"sudo mkdir -p {shlex.quote(parent)} && "
        f"sudo install -m {shlex.quote(mode)} {shlex.quote(tmp)} {shlex.quote(path)} && "
        f"rm -f {shlex.quote(tmp)}"
    )
    code, out, err = _run(ssh, cmd)
    if code != 0:
        raise SystemExit((err or out or f"failed to write {path}").strip())


def fetch_brain_bridge_state(
    ssh: paramiko.SSHClient,
    *,
    exclude_codes: set[str],
    include_free: bool = True,
) -> dict[str, Any]:
    excluded = sorted(_clean_text(item).lower() for item in exclude_codes if _clean_text(item))
    remote = f"""
set -a
. /root/portal_bot/.env >/dev/null 2>&1
set +a
cd /root/portal_bot
PYTHON=/root/portal_bot/venv/bin/python
if [ ! -x "$PYTHON" ]; then PYTHON=python3; fi
"$PYTHON" - <<'PY'
import json
from datetime import datetime
from sqlalchemy import or_
from db import SessionLocal, init_db
from models import Node, User

exclude_codes = set({json.dumps(excluded)})
include_free = {str(bool(include_free))}
now = datetime.utcnow()
init_db()
s = SessionLocal()
try:
    users = (
        s.query(User.uuid)
        .filter(User.is_active == True)
        .filter(User.uuid != None)
        .filter(or_(User.expiry_at == None, User.expiry_at > now))
        .all()
    )
    nodes = s.query(Node).filter(Node.enabled == True).all()
    targets = []
    for node in nodes:
        code = str(getattr(node, "code", "") or "").strip().lower()
        base = code.split("_", 1)[0].split("-", 1)[0].split(".", 1)[0]
        if not code or code in exclude_codes or base in exclude_codes:
            continue
        if code in {"brain", "mini", "rf1"} or base in {"brain", "mini", "rf1"}:
            continue
        if not include_free and "free" in code:
            continue
        targets.append({{"code": code, "host": str(node.host or ""), "port": int(node.vless_port or 443)}})
    print(json.dumps({{"client_uuids": sorted({{str(row.uuid) for row in users if row.uuid}}), "targets": targets}}))
finally:
    s.close()
PY
"""
    code, out, err = _run(ssh, remote, timeout=120)
    if code != 0:
        raise SystemExit((err or out or "failed to fetch brain bridge state").strip())
    return json.loads(out)


def ensure_reality_material(
    ssh: paramiko.SSHClient,
    *,
    meta_path: str = DEFAULT_BRIDGE_META,
    xray_bin: str = "xray",
) -> dict[str, Any]:
    existing = _remote_read_json(ssh, meta_path)
    if _clean_text(existing.get("private_key")) and _clean_text(existing.get("public_key")) and _clean_text(existing.get("short_id")):
        return existing

    code, out, err = _run(ssh, f"{shlex.quote(xray_bin)} x25519", timeout=30)
    if code != 0:
        raise SystemExit((err or out or "xray x25519 failed").strip())
    private_key = ""
    public_key = ""
    for line in out.splitlines():
        if "Private key:" in line or line.startswith("PrivateKey:"):
            private_key = line.split(":", 1)[1].strip()
        elif "Public key:" in line or line.startswith("Password (PublicKey):") or line.startswith("PublicKey:"):
            public_key = line.split(":", 1)[1].strip()
    if not private_key or not public_key:
        raise SystemExit("failed to parse xray x25519 output")
    material = {
        "private_key": private_key,
        "public_key": public_key,
        "short_id": secrets.token_hex(4),
        "server_names": ["www.yandex.ru", "yandex.ru"],
    }
    _remote_write_text(ssh, meta_path, json.dumps(material, indent=2) + "\n", mode="600")
    return material


def detect_xray_bin(ssh: paramiko.SSHClient, preferred: str = "auto") -> str:
    preferred = _clean_text(preferred)
    if preferred and preferred != "auto":
        return preferred
    candidates = [
        "command -v xray 2>/dev/null",
        "test -x /usr/local/x-ui/bin/xray-linux-amd64 && echo /usr/local/x-ui/bin/xray-linux-amd64",
        "test -x /usr/local/x-ui/bin/xray && echo /usr/local/x-ui/bin/xray",
    ]
    for cmd in candidates:
        code, out, _err = _run(ssh, cmd, timeout=20)
        value = _clean_text(out.splitlines()[0] if out.strip() else "")
        if code == 0 and value:
            return value
    raise SystemExit("xray binary not found; install 3x-ui/Xray first or pass --xray-bin")


def build_bridge_xray_config(
    *,
    client_uuids: list[str],
    allowed_targets: list[dict[str, Any]],
    private_key: str,
    server_names: list[str],
    short_ids: list[str],
    exclude_codes: set[str],
    listen_host: str = "0.0.0.0",
    listen_port: int = 443,
) -> dict[str, Any]:
    clients = [{"id": _clean_text(uuid), "flow": "xtls-rprx-vision"} for uuid in client_uuids if _clean_text(uuid)]
    allowed_ips: list[str] = []
    allowed_domains: list[str] = []
    seen: set[str] = set()
    excluded = {_clean_text(item).lower() for item in exclude_codes if _clean_text(item)}
    for target in allowed_targets:
        code = _clean_text(target.get("code")).lower()
        base = _node_code_base(code)
        if code in excluded or base in excluded:
            continue
        host = _clean_text(target.get("host"))
        if not host or host in seen:
            continue
        seen.add(host)
        if _is_ip(host):
            allowed_ips.append(host)
        else:
            allowed_domains.append(host)

    allow_rules: list[dict[str, Any]] = []
    if allowed_domains:
        allow_rules.append(
            {
                "type": "field",
                "inboundTag": [BRIDGE_INBOUND_TAG],
                "port": "443",
                "domain": allowed_domains,
                "outboundTag": BRIDGE_ALLOW_TAG,
            }
        )
    if allowed_ips:
        allow_rules.append(
            {
                "type": "field",
                "inboundTag": [BRIDGE_INBOUND_TAG],
                "port": "443",
                "ip": allowed_ips,
                "outboundTag": BRIDGE_ALLOW_TAG,
            }
        )

    return {
        "log": {"loglevel": "warning"},
        "inbounds": [
            {
                "tag": BRIDGE_INBOUND_TAG,
                "listen": listen_host,
                "port": int(listen_port),
                "protocol": "vless",
                "settings": {"clients": clients, "decryption": "none"},
                "streamSettings": {
                    "network": "tcp",
                    "security": "reality",
                    "realitySettings": {
                        "show": False,
                        "dest": f"{server_names[0]}:443",
                        "xver": 0,
                        "serverNames": server_names,
                        "privateKey": private_key,
                        "shortIds": short_ids,
                    },
                },
            }
        ],
        "outbounds": [
            {"tag": BRIDGE_ALLOW_TAG, "protocol": "freedom"},
            {"tag": BRIDGE_BLOCK_TAG, "protocol": "blackhole"},
        ],
        "routing": {
            "domainStrategy": "AsIs",
            "rules": [
                *allow_rules,
                {"type": "field", "inboundTag": [BRIDGE_INBOUND_TAG], "outboundTag": BRIDGE_BLOCK_TAG},
            ],
        },
    }


def merge_bridge_xray_config(
    existing: dict[str, Any],
    bridge: dict[str, Any],
    *,
    replace_legacy_public_443: bool = True,
) -> dict[str, Any]:
    existing = dict(existing or {})
    inbounds = []
    for item in list(existing.get("inbounds") or []):
        if _clean_text(item.get("tag")) == BRIDGE_INBOUND_TAG:
            continue
        if replace_legacy_public_443 and int(item.get("port") or 0) == 443:
            continue
        inbounds.append(item)
    inbounds.extend(bridge.get("inbounds") or [])

    bridge_tags = {BRIDGE_ALLOW_TAG, BRIDGE_BLOCK_TAG}
    outbounds = [item for item in list(existing.get("outbounds") or []) if _clean_text(item.get("tag")) not in bridge_tags]
    outbounds.extend(bridge.get("outbounds") or [])

    old_routing = existing.get("routing") if isinstance(existing.get("routing"), dict) else {}
    rules = []
    for rule in list(old_routing.get("rules") or []):
        inbound_tags = rule.get("inboundTag") if isinstance(rule, dict) else []
        if isinstance(inbound_tags, str):
            inbound_tags = [inbound_tags]
        if BRIDGE_INBOUND_TAG in inbound_tags:
            continue
        rules.append(rule)
    rules = list((bridge.get("routing") or {}).get("rules") or []) + rules

    return {
        **existing,
        "log": existing.get("log") or {"loglevel": "warning"},
        "inbounds": inbounds,
        "outbounds": outbounds,
        "routing": {"domainStrategy": "AsIs", "rules": rules},
    }


def build_rollout_ru_bridge_patch(
    *,
    endpoint_host: str,
    public_key: str,
    short_id: str,
    excluded_node_codes: list[str],
    bridge_id: str = "mini",
    bridge_label: str = "Белые списки",
    endpoint_port: int = 443,
) -> dict[str, Any]:
    endpoint = {
        "id": bridge_id,
        "label": bridge_label,
        "enabled": True,
        "endpoint_host": endpoint_host,
        "endpoint_port": int(endpoint_port),
        "tls_server_name": "www.yandex.ru",
        "reality_public_key": public_key,
        "reality_short_id": short_id,
        "fingerprint": "chrome",
    }
    return {
        "ru_bridge_relay": {
            "enabled": True,
            "endpoint_host": endpoint["endpoint_host"],
            "endpoint_port": endpoint["endpoint_port"],
            "tls_server_name": endpoint["tls_server_name"],
            "reality_public_key": endpoint["reality_public_key"],
            "reality_short_id": endpoint["reality_short_id"],
            "fingerprint": endpoint["fingerprint"],
            "allowlist_node_codes": [],
            "excluded_node_codes": excluded_node_codes,
            "urltest_url": "https://www.gstatic.com/generate_204",
            "urltest_interval": "10m",
            "urltest_tolerance": 80,
            "endpoints": [endpoint],
        }
    }


def rollout_endpoint_key(item: dict[str, Any]) -> str:
    if not isinstance(item, dict):
        return ""
    return _clean_text(item.get("id") or item.get("code") or item.get("endpoint_host") or item.get("host")).lower()


def rollout_single_bridge_as_endpoint(
    bridge: dict[str, Any],
    *,
    fallback_id: str = "mini",
    fallback_label: str = "Белые списки",
) -> dict[str, Any] | None:
    if not isinstance(bridge, dict) or not _clean_text(bridge.get("endpoint_host")):
        return None
    if not _clean_text(bridge.get("reality_public_key")):
        return None
    return {
        "id": _clean_text(bridge.get("id") or fallback_id).lower(),
        "label": _clean_text(bridge.get("label") or fallback_label),
        "enabled": bridge.get("enabled", True),
        "endpoint_host": _clean_text(bridge.get("endpoint_host")),
        "endpoint_port": int(bridge.get("endpoint_port") or 443),
        "tls_server_name": _clean_text(bridge.get("tls_server_name") or "www.yandex.ru"),
        "reality_public_key": _clean_text(bridge.get("reality_public_key")),
        "reality_short_id": _clean_text(bridge.get("reality_short_id")),
        "fingerprint": _clean_text(bridge.get("fingerprint") or "chrome"),
    }


def merge_ru_bridge_rollout(current_bridge: dict[str, Any] | None, patch_bridge: dict[str, Any] | None) -> dict[str, Any]:
    current_bridge = current_bridge if isinstance(current_bridge, dict) else {}
    patch_bridge = patch_bridge if isinstance(patch_bridge, dict) else {}
    ordered: list[str] = []
    by_key: dict[str, dict[str, Any]] = {}

    def add(item: dict[str, Any] | None) -> None:
        if not isinstance(item, dict):
            return
        key = rollout_endpoint_key(item)
        if not key:
            return
        endpoint = dict(item)
        endpoint["id"] = _clean_text(endpoint.get("id") or endpoint.get("code") or key).lower()
        if key in by_key:
            by_key[key].update(endpoint)
            return
        by_key[key] = endpoint
        ordered.append(key)

    current_endpoints = current_bridge.get("endpoints")
    if isinstance(current_endpoints, list) and current_endpoints:
        for item in current_endpoints:
            add(item)
    else:
        add(rollout_single_bridge_as_endpoint(current_bridge))

    patch_endpoints = patch_bridge.get("endpoints")
    if isinstance(patch_endpoints, list) and patch_endpoints:
        for item in patch_endpoints:
            add(item)
    else:
        add(
            rollout_single_bridge_as_endpoint(
                patch_bridge,
                fallback_id=_clean_text(patch_bridge.get("id") or "mini"),
            )
        )

    endpoints = [by_key[key] for key in ordered if key in by_key]
    merged = dict(current_bridge)
    merged.update({key: value for key, value in patch_bridge.items() if key != "endpoints"})
    merged["endpoints"] = endpoints
    if endpoints:
        primary = endpoints[0]
        for key in ("endpoint_host", "endpoint_port", "tls_server_name", "reality_public_key", "reality_short_id", "fingerprint"):
            if primary.get(key) not in (None, ""):
                merged[key] = primary.get(key)
    return merged


def apply_mini_bridge(
    ssh: paramiko.SSHClient,
    *,
    client_uuids: list[str],
    targets: list[dict[str, Any]],
    exclude_codes: set[str],
    config_path: str = DEFAULT_XRAY_CONFIG,
    meta_path: str = DEFAULT_BRIDGE_META,
    listen_host: str = "0.0.0.0",
    listen_port: int = 443,
    service_name: str = "xray",
    xray_bin: str = "xray",
) -> dict[str, Any]:
    material = ensure_reality_material(ssh, meta_path=meta_path, xray_bin=xray_bin)
    bridge_config = build_bridge_xray_config(
        client_uuids=client_uuids,
        allowed_targets=targets,
        private_key=str(material["private_key"]),
        server_names=list(material.get("server_names") or ["www.yandex.ru", "yandex.ru"]),
        short_ids=[str(material["short_id"])],
        exclude_codes=exclude_codes,
        listen_host=listen_host,
        listen_port=listen_port,
    )
    existing = _remote_read_json(ssh, config_path, default={"log": {"loglevel": "warning"}, "inbounds": [], "outbounds": []})
    merged = merge_bridge_xray_config(
        existing,
        bridge_config,
        replace_legacy_public_443=int(listen_port) == 443,
    )
    rendered = json.dumps(merged, indent=2, ensure_ascii=False) + "\n"
    _remote_write_text(ssh, config_path, rendered, mode="600")
    code, out, err = _run(ssh, f"sudo {shlex.quote(xray_bin)} run -test -config {shlex.quote(config_path)}", timeout=60)
    if code != 0:
        raise SystemExit((err or out or "xray config test failed").strip())
    service_name = _clean_text(service_name) or "xray"
    if service_name != "xray":
        service_path = f"/etc/systemd/system/{service_name}.service"
        service_text = f"""[Unit]
Description=POKROV RU bridge relay
After=network.target

[Service]
User=root
ExecStart={xray_bin} run -config {config_path}
Restart=on-failure
RestartSec=5
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
"""
        _remote_write_text(ssh, service_path, service_text, mode="644")
        code, out, err = _run(
            ssh,
            f"sudo systemctl daemon-reload && sudo systemctl enable --now {shlex.quote(service_name)} && sudo systemctl restart {shlex.quote(service_name)}",
            timeout=120,
        )
    else:
        code, out, err = _run(ssh, "sudo systemctl restart xray", timeout=120)
    if code != 0:
        raise SystemExit((err or out or f"{service_name} restart failed").strip())
    code, out, err = _run(
        ssh,
        f"systemctl is-active {shlex.quote(service_name)} && ss -lntp | grep {shlex.quote(':' + str(int(listen_port)))} || true",
        timeout=30,
    )
    if code != 0:
        raise SystemExit((err or out or f"{service_name} status failed").strip())
    return {
        "public_key": str(material["public_key"]),
        "short_id": str(material["short_id"]),
        "server_names": list(material.get("server_names") or ["www.yandex.ru", "yandex.ru"]),
        "service_output": (out or "").strip(),
    }


def patch_brain_rollout(ssh: paramiko.SSHClient, *, patch: dict[str, Any]) -> None:
    remote_patch = json.dumps(patch, ensure_ascii=False)
    remote = f"""
set -a
. /root/portal_bot/.env >/dev/null 2>&1
set +a
cd /root/portal_bot
PYTHON=/root/portal_bot/venv/bin/python
if [ ! -x "$PYTHON" ]; then PYTHON=python3; fi
"$PYTHON" - <<'PY'
import json
from db import SessionLocal, init_db
from models import AppSetting

patch = json.loads({json.dumps(remote_patch)})

def clean_text(value):
    return str(value or "").strip()

def endpoint_key(item):
    if not isinstance(item, dict):
        return ""
    return clean_text(item.get("id") or item.get("code") or item.get("endpoint_host") or item.get("host")).lower()

def single_bridge_as_endpoint(bridge, fallback_id="mini", fallback_label="Белые списки"):
    if not isinstance(bridge, dict) or not clean_text(bridge.get("endpoint_host")):
        return None
    if not clean_text(bridge.get("reality_public_key")):
        return None
    return {{
        "id": clean_text(bridge.get("id") or fallback_id).lower(),
        "label": clean_text(bridge.get("label") or fallback_label),
        "enabled": bridge.get("enabled", True),
        "endpoint_host": clean_text(bridge.get("endpoint_host")),
        "endpoint_port": int(bridge.get("endpoint_port") or 443),
        "tls_server_name": clean_text(bridge.get("tls_server_name") or "www.yandex.ru"),
        "reality_public_key": clean_text(bridge.get("reality_public_key")),
        "reality_short_id": clean_text(bridge.get("reality_short_id")),
        "fingerprint": clean_text(bridge.get("fingerprint") or "chrome"),
    }}

def merge_ru_bridge(current_bridge, patch_bridge):
    current_bridge = current_bridge if isinstance(current_bridge, dict) else {{}}
    patch_bridge = patch_bridge if isinstance(patch_bridge, dict) else {{}}
    ordered = []
    by_key = {{}}

    def add(item):
        if not isinstance(item, dict):
            return
        key = endpoint_key(item)
        if not key:
            return
        endpoint = dict(item)
        endpoint["id"] = clean_text(endpoint.get("id") or endpoint.get("code") or key).lower()
        if key in by_key:
            by_key[key].update(endpoint)
            return
        by_key[key] = endpoint
        ordered.append(key)

    current_endpoints = current_bridge.get("endpoints")
    if isinstance(current_endpoints, list) and current_endpoints:
        for item in current_endpoints:
            add(item)
    else:
        add(single_bridge_as_endpoint(current_bridge))

    patch_endpoints = patch_bridge.get("endpoints")
    if isinstance(patch_endpoints, list) and patch_endpoints:
        for item in patch_endpoints:
            add(item)
    else:
        add(single_bridge_as_endpoint(patch_bridge, fallback_id=clean_text(patch_bridge.get("id") or "mini")))

    endpoints = [by_key[key] for key in ordered if key in by_key]
    merged = dict(current_bridge)
    merged.update({{k: v for k, v in patch_bridge.items() if k != "endpoints"}})
    merged["endpoints"] = endpoints
    if endpoints:
        primary = endpoints[0]
        for key in ("endpoint_host", "endpoint_port", "tls_server_name", "reality_public_key", "reality_short_id", "fingerprint"):
            if primary.get(key) not in (None, ""):
                merged[key] = primary.get(key)
    return merged

init_db()
s = SessionLocal()
try:
    row = s.query(AppSetting).filter(AppSetting.key == "network_rollout_config").first()
    current = {{}}
    if row and row.value_json:
        try:
            current = json.loads(row.value_json)
        except Exception:
            current = {{}}
    if "ru_bridge_relay" in patch:
        current["ru_bridge_relay"] = merge_ru_bridge(current.get("ru_bridge_relay"), patch.get("ru_bridge_relay"))
        patch = {{k: v for k, v in patch.items() if k != "ru_bridge_relay"}}
    current.update(patch)
    if not row:
        row = AppSetting(key="network_rollout_config", value_json=json.dumps(current, ensure_ascii=False))
        s.add(row)
    else:
        row.value_json = json.dumps(current, ensure_ascii=False)
    s.commit()
finally:
    s.close()
PY
"""
    code, out, err = _run(ssh, remote, timeout=120)
    if code != 0:
        raise SystemExit((err or out or "failed to patch brain rollout config").strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Install and sync a RU bridge relay endpoint to non-US POKROV nodes.")
    parser.add_argument("--brain-host", default=DEFAULT_BRAIN_HOST)
    parser.add_argument("--mini-host", default=DEFAULT_MINI_HOST)
    parser.add_argument("--brain-node-code", default="brain")
    parser.add_argument("--mini-node-code", default="mini")
    parser.add_argument("--bridge-id", default="", help="stable endpoint id in network_rollout_config; defaults to --mini-node-code")
    parser.add_argument("--bridge-label", default="Белые списки", help="selector label, e.g. 'Белые списки тип 2'")
    parser.add_argument("--brain-ssh-user", default="root")
    parser.add_argument("--mini-ssh-user", default="root")
    parser.add_argument("--brain-ssh-port", type=int, default=29374)
    parser.add_argument("--mini-ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--exclude-codes", default="us")
    parser.add_argument("--listen-host", default="0.0.0.0")
    parser.add_argument("--listen-port", type=int, default=443)
    parser.add_argument("--public-endpoint-port", type=int, default=443)
    parser.add_argument("--xray-config", default=DEFAULT_XRAY_CONFIG)
    parser.add_argument("--xray-service", default="xray")
    parser.add_argument("--xray-bin", default="auto")
    parser.add_argument("--meta-path", default=DEFAULT_BRIDGE_META)
    parser.add_argument("--skip-free-target", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--update-brain-rollout", action="store_true")
    args = parser.parse_args()

    exclude_codes = {_clean_text(item).lower() for item in str(args.exclude_codes or "").split(",") if _clean_text(item)}
    bridge_id = _clean_text(args.bridge_id) or _clean_text(args.mini_node_code) or "mini"
    brain, brain_auth = connect_node(
        code=args.brain_node_code,
        host=args.brain_host,
        user=args.brain_ssh_user,
        port=int(args.brain_ssh_port),
        passwords_path=Path(args.passwords),
    )
    try:
        state = fetch_brain_bridge_state(brain, exclude_codes=exclude_codes, include_free=not args.skip_free_target)
    finally:
        brain.close()

    client_uuids = list(state.get("client_uuids") or [])
    targets = list(state.get("targets") or [])
    safe_targets = [target for target in targets if _node_code_base(str(target.get("code") or "")) not in exclude_codes]
    print(f"brain_auth={brain_auth}")
    print(f"active_client_uuid_count={len(client_uuids)}")
    print("bridge_target_codes=" + ",".join(str(item.get("code") or "") for item in safe_targets))
    print(f"bridge_id={bridge_id}")
    print(f"bridge_listen={args.listen_host}:{int(args.listen_port)}")
    if not args.apply:
        print("dry_run=true")
        return 0

    mini, mini_auth = connect_node(
        code=args.mini_node_code,
        host=args.mini_host,
        user=args.mini_ssh_user,
        port=int(args.mini_ssh_port),
        passwords_path=Path(args.passwords),
    )
    try:
        xray_bin = detect_xray_bin(mini, args.xray_bin)
        result = apply_mini_bridge(
            mini,
            client_uuids=client_uuids,
            targets=safe_targets,
            exclude_codes=exclude_codes,
            config_path=args.xray_config,
            meta_path=args.meta_path,
            listen_host=args.listen_host,
            listen_port=int(args.listen_port),
            service_name=args.xray_service,
            xray_bin=xray_bin,
        )
    finally:
        mini.close()

    print(f"mini_auth={mini_auth}")
    print("ru_bridge_public_key=" + str(result["public_key"]))
    print("ru_bridge_short_id=" + str(result["short_id"]))
    print("ru_bridge_server_names=" + ",".join(result["server_names"]))
    print("[mini_service]")
    print(str(result.get("service_output") or ""))

    if args.update_brain_rollout:
        patch = build_rollout_ru_bridge_patch(
            endpoint_host=args.mini_host,
            public_key=str(result["public_key"]),
            short_id=str(result["short_id"]),
            excluded_node_codes=sorted(exclude_codes),
            bridge_id=bridge_id,
            bridge_label=args.bridge_label,
            endpoint_port=int(args.public_endpoint_port),
        )
        brain, _brain_auth = connect_node(
            code=args.brain_node_code,
            host=args.brain_host,
            user=args.brain_ssh_user,
            port=int(args.brain_ssh_port),
            passwords_path=Path(args.passwords),
        )
        try:
            patch_brain_rollout(brain, patch=patch)
        finally:
            brain.close()
        print("brain_rollout_ru_bridge_relay=patched_enabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
