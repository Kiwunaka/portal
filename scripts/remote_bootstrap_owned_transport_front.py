#!/usr/bin/env python3
"""Guarded PLAN/APPLY/ROLLBACK for a first owned TCP/443 transport front.

The bootstrap preserves the existing public Xray/Reality route: one exact x-ui
inbound is moved from wildcard ``:443`` to ``127.0.0.1:10443`` and HAProxy
becomes the public ``:443`` owner with that loopback listener as its default
backend.  Smart DNS is deliberately not installed by this operation.

PLAN is read-only. APPLY and ROLLBACK require digest-bound confirmations and a
root-only receipt. APPLY arms automatic rollback before the first mutation.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

try:
    from node_access import DEFAULT_PASSWORDS, connect_node
except ImportError:  # pragma: no cover - package import for tests
    from .node_access import DEFAULT_PASSWORDS, connect_node


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_SOURCE = REPO_ROOT / "infra" / "portal-transport-front.legacy-one-backend.cfg"
SERVICE_SOURCE = REPO_ROOT / "infra" / "portal-transport-front.service"
REPORT_SCHEMA = "pokrov-owned-transport-front-bootstrap-v1"
CONFIG_PATH = "/etc/portal-transport-front.cfg"
SERVICE_PATH = "/etc/systemd/system/portal-transport-front.service"
SERVICE_NAME = "portal-transport-front.service"
DEFAULT_HAPROXY_SERVICE = "haproxy.service"
XUI_SERVICE = "x-ui.service"
XUI_DB = "/etc/x-ui/x-ui.db"
PUBLIC_PORT = 443
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 10443
SMART_DNS_PORT = 18443
RECEIPT_ROOT = "/root/pokrov-transport-front-bootstrap"
SAFE_SHA256_RE = re.compile(r"[0-9a-f]{64}")
SAFE_COMPONENT_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,31}")
SAFE_RECEIPT_RE = re.compile(r"[0-9]{8}T[0-9]{6}Z-[0-9]+-[0-9a-f]{12}")


class TransportFrontBootstrapError(RuntimeError):
    """Raised when a guard cannot be proved."""


def _q(value: object) -> str:
    return shlex.quote(str(value))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_text(path: Path) -> bytes:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise TransportFrontBootstrapError("text_utf8_bom_forbidden")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TransportFrontBootstrapError("text_utf8_invalid") from exc
    normalized = text.replace("\r\n", "\n")
    if "\r" in normalized:
        raise TransportFrontBootstrapError("text_lone_carriage_return_forbidden")
    if not normalized.endswith("\n"):
        normalized += "\n"
    return normalized.encode("utf-8")


def _safe_component(value: str, *, label: str) -> str:
    normalized = str(value or "").strip().lower()
    if not SAFE_COMPONENT_RE.fullmatch(normalized):
        raise TransportFrontBootstrapError(f"{label}_invalid")
    return normalized


def _safe_positive_int(value: object, *, label: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise TransportFrontBootstrapError(f"{label}_invalid") from exc
    if result <= 0 or result > 2_147_483_647:
        raise TransportFrontBootstrapError(f"{label}_invalid")
    return result


def _release_id(config_sha256: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{now}-{os.getpid()}-{config_sha256[:12]}"


def _validate_sources(config: bytes, service: bytes) -> None:
    text = config.decode("utf-8")
    lines = text.splitlines()
    required = {
        "frontend fe_transport_front",
        "bind :443",
        "default_backend be_legacy_reality_fallback",
        "backend be_legacy_reality_fallback",
        "server legacy_reality_fallback 127.0.0.1:10443 check",
    }
    if not required.issubset({line.strip() for line in lines}):
        raise TransportFrontBootstrapError("config_contract_invalid")
    if sum(line.strip() == "bind :443" for line in lines) != 1:
        raise TransportFrontBootstrapError("config_public_bind_count_invalid")
    if sum(line.strip().startswith("server ") for line in lines) != 1:
        raise TransportFrontBootstrapError("config_backend_count_invalid")
    lowered = text.lower()
    if "smart_dns" in lowered or f":{SMART_DNS_PORT}" in text:
        raise TransportFrontBootstrapError("config_smart_dns_forbidden")
    service_text = service.decode("utf-8")
    for marker in (
        "ExecStartPre=/usr/sbin/haproxy -c -f /etc/portal-transport-front.cfg",
        "ExecStart=/usr/sbin/haproxy -W -db -f /etc/portal-transport-front.cfg",
        "ExecReload=/bin/kill -USR2 $MAINPID",
        "KillMode=mixed",
    ):
        if marker not in service_text:
            raise TransportFrontBootstrapError("service_contract_invalid")


def _run(ssh: Any, command: str, *, label: str, timeout: int = 180) -> str:
    _stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode("utf-8", errors="replace").strip()
    stderr.read()
    if code != 0:
        raise TransportFrontBootstrapError(f"{label}_failed_exit_{code}")
    return output


def _run_allow_failure(ssh: Any, command: str, *, timeout: int = 180) -> None:
    try:
        _run(ssh, command, label="best_effort", timeout=timeout)
    except Exception:
        return


def _psql(ssh: Any, sql: str, *, label: str) -> str:
    stdin, stdout, stderr = ssh.exec_command(
        "runuser -u postgres -- psql -d portal -At", timeout=60
    )
    stdin.write(sql + "\n")
    stdin.channel.shutdown_write()
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode("utf-8", errors="replace").strip()
    stderr.read()
    if code != 0:
        raise TransportFrontBootstrapError(f"{label}_failed_exit_{code}")
    return output


def _resolve_node_host(brain: Any, node_code: str) -> str:
    node = _safe_component(node_code, label="node_code")
    raw = _psql(
        brain,
        "select host from nodes "
        f"where code='{node}' and enabled=true order by id limit 2;",
        label="node_resolution",
    )
    hosts = [line.strip() for line in raw.splitlines() if line.strip()]
    if len(hosts) != 1:
        raise TransportFrontBootstrapError("owned_node_resolution_not_unique")
    return hosts[0]


def _connect_owned(*, code: str, host: str, passwords: Path) -> tuple[Any, str]:
    try:
        return connect_node(code=code, host=host, passwords_path=passwords)
    except Exception as exc:
        raise TransportFrontBootstrapError(f"{code}_ssh_connect_failed") from exc


def _auth_family(value: str) -> str:
    return "key" if str(value or "").startswith("key") else "password"


_REMOTE_PROBE = r'''
import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess

p = argparse.ArgumentParser()
p.add_argument("--inbound-id", type=int, required=True)
p.add_argument("--expected-state", choices=("direct", "fronted"), required=True)
a = p.parse_args()

def run(command):
    return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False)

def state(unit, kind):
    value = run(["systemctl", f"is-{kind}", unit]).stdout.strip()
    allowed = {"active", "inactive", "failed", "unknown", "enabled", "disabled", "static", "indirect", "masked", "not-found"}
    return value if value in allowed else "other"

def exists(path):
    return os.path.isfile(path) and not os.path.islink(path)

def digest(path):
    if not exists(path):
        return "missing"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

result = {
    "effective_uid_root": os.geteuid() == 0,
    "systemd_present": run(["sh", "-c", "command -v systemctl"]).returncode == 0,
    "python3_present": run(["sh", "-c", "command -v python3"]).returncode == 0,
    "sqlite3_module_present": True,
    "apt_present": run(["sh", "-c", "command -v apt-get"]).returncode == 0,
    "haproxy_present": run(["sh", "-c", "command -v haproxy"]).returncode == 0,
    "haproxy_package_candidate": False,
    "xui_state": state("x-ui.service", "active"),
    "xui_enabled": state("x-ui.service", "enabled"),
    "frontend_state": state("portal-transport-front.service", "active"),
    "frontend_enabled": state("portal-transport-front.service", "enabled"),
    "default_haproxy_state": state("haproxy.service", "active"),
    "default_haproxy_enabled": state("haproxy.service", "enabled"),
    "config_present": exists("/etc/portal-transport-front.cfg"),
    "config_sha256": digest("/etc/portal-transport-front.cfg"),
    "service_present": exists("/etc/systemd/system/portal-transport-front.service"),
    "service_sha256": digest("/etc/systemd/system/portal-transport-front.service"),
    "xui_db_present": exists("/etc/x-ui/x-ui.db"),
    "inbound_found": False,
    "inbound_unique": False,
    "inbound_protocol_vless": False,
    "inbound_enabled": False,
    "inbound_listen_state": "missing",
    "inbound_port": 0,
    "inbound_reality": False,
    "inbound_invariant_sha256": "missing",
    "enabled_public_443_inbound_count": 0,
    "public_443_listening": False,
    "backend_10443_listening": False,
    "smart_dns_18443_listening": False,
    "public_443_owned_by_xray": False,
    "backend_10443_owned_by_xray": False,
    "frontend_config_valid": False,
}

if result["apt_present"]:
    policy = run(["apt-cache", "policy", "haproxy"])
    result["haproxy_package_candidate"] = policy.returncode == 0 and bool(re.search(r"Candidate:\s*(?!\(none\))\S+", policy.stdout))

try:
    if result["xui_db_present"]:
        db = sqlite3.connect("file:/etc/x-ui/x-ui.db?mode=ro", uri=True, timeout=5)
        cols = {row[1] for row in db.execute("pragma table_info(inbounds)")}
        required = {"id", "listen", "port", "protocol", "enable", "stream_settings"}
        if required.issubset(cols):
            rows = list(db.execute("select id,listen,port,protocol,enable,stream_settings from inbounds where id=?", (a.inbound_id,)))
            result["inbound_unique"] = len(rows) == 1
            if len(rows) == 1:
                row = rows[0]
                result["inbound_found"] = True
                result["inbound_protocol_vless"] = row[3] == "vless"
                result["inbound_enabled"] = bool(row[4])
                listen = str(row[1] or "")
                if listen == "": result["inbound_listen_state"] = "wildcard_empty"
                elif listen == "127.0.0.1": result["inbound_listen_state"] = "loopback_v4"
                else: result["inbound_listen_state"] = "other"
                result["inbound_port"] = int(row[2] or 0)
                invariant = json.dumps(
                    [int(row[0]), str(row[3] or ""), int(bool(row[4])), str(row[5] or "")],
                    ensure_ascii=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                result["inbound_invariant_sha256"] = hashlib.sha256(invariant).hexdigest()
                try:
                    stream = json.loads(row[5] or "{}")
                    result["inbound_reality"] = str(stream.get("security", "")).lower() == "reality"
                except Exception:
                    pass
            result["enabled_public_443_inbound_count"] = int(db.execute("select count(*) from inbounds where enable=1 and port=443").fetchone()[0])
        db.close()
except Exception:
    result["sqlite3_module_present"] = False

ss = run(["ss", "-H", "-ltnp"]).stdout.splitlines()
for line in ss:
    fields = line.split()
    if len(fields) < 4: continue
    endpoint = fields[3]
    owner_xray = "xray" in line.lower()
    if endpoint.endswith(":443"):
        result["public_443_listening"] = True
        result["public_443_owned_by_xray"] = result["public_443_owned_by_xray"] or owner_xray
    if endpoint.endswith(":10443"):
        result["backend_10443_listening"] = True
        result["backend_10443_owned_by_xray"] = result["backend_10443_owned_by_xray"] or owner_xray
    if endpoint.endswith(":18443"):
        result["smart_dns_18443_listening"] = True

if result["haproxy_present"] and result["config_present"]:
    result["frontend_config_valid"] = run(["haproxy", "-c", "-f", "/etc/portal-transport-front.cfg"]).returncode == 0

result["expected_state"] = a.expected_state
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
'''.strip()


def _remote_probe(ssh: Any, *, inbound_id: int, expected_state: str) -> dict[str, Any]:
    encoded = base64.b64encode(_REMOTE_PROBE.encode("utf-8")).decode("ascii")
    command = (
        f"python3 -c \"$(printf %s {_q(encoded)} | base64 -d)\""
        f" --inbound-id {_q(inbound_id)} --expected-state {_q(expected_state)}"
    )
    raw = _run(ssh, command, label="remote_probe", timeout=90)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TransportFrontBootstrapError("remote_probe_json_invalid") from exc
    required = {
        "effective_uid_root", "systemd_present", "python3_present", "sqlite3_module_present",
        "apt_present", "haproxy_present", "haproxy_package_candidate", "xui_state",
        "xui_enabled", "frontend_state", "frontend_enabled", "default_haproxy_state",
        "default_haproxy_enabled", "config_present", "config_sha256", "service_present",
        "service_sha256", "xui_db_present", "inbound_found", "inbound_unique",
        "inbound_protocol_vless", "inbound_enabled", "inbound_listen_state", "inbound_port",
        "inbound_reality", "inbound_invariant_sha256", "enabled_public_443_inbound_count", "public_443_listening",
        "backend_10443_listening", "smart_dns_18443_listening", "public_443_owned_by_xray",
        "backend_10443_owned_by_xray", "frontend_config_valid", "expected_state",
    }
    if not isinstance(result, dict) or set(result) != required:
        raise TransportFrontBootstrapError("remote_probe_contract_invalid")
    if result["expected_state"] != expected_state:
        raise TransportFrontBootstrapError("remote_probe_state_mismatch")
    for key in ("config_sha256", "service_sha256"):
        if result[key] != "missing" and not SAFE_SHA256_RE.fullmatch(str(result[key])):
            raise TransportFrontBootstrapError("remote_probe_digest_invalid")
    if not SAFE_SHA256_RE.fullmatch(str(result["inbound_invariant_sha256"])):
        raise TransportFrontBootstrapError("remote_probe_inbound_invariant_invalid")
    return result


def _assert_direct_preflight(probe: Mapping[str, Any]) -> None:
    required_true = (
        "effective_uid_root", "systemd_present", "python3_present", "sqlite3_module_present",
        "apt_present", "haproxy_package_candidate", "xui_db_present", "inbound_found",
        "inbound_unique", "inbound_protocol_vless", "inbound_enabled", "inbound_reality",
        "public_443_listening", "public_443_owned_by_xray",
    )
    for key in required_true:
        if probe.get(key) is not True:
            raise TransportFrontBootstrapError(f"direct_preflight_{key}_required")
    expected = {
        "xui_state": "active",
        "xui_enabled": "enabled",
        "frontend_state": "inactive",
        "config_present": False,
        "service_present": False,
        "inbound_listen_state": "wildcard_empty",
        "inbound_port": PUBLIC_PORT,
        "enabled_public_443_inbound_count": 1,
        "backend_10443_listening": False,
        "smart_dns_18443_listening": False,
    }
    for key, value in expected.items():
        if probe.get(key) != value:
            raise TransportFrontBootstrapError(f"direct_preflight_{key}_mismatch")
    if probe.get("default_haproxy_state") == "active":
        raise TransportFrontBootstrapError("direct_preflight_default_haproxy_active")


def _assert_fronted_preflight(
    probe: Mapping[str, Any], *, config_sha256: str, service_sha256: str
) -> None:
    required_true = (
        "effective_uid_root", "systemd_present", "python3_present", "sqlite3_module_present",
        "haproxy_present", "xui_db_present", "inbound_found", "inbound_unique",
        "inbound_protocol_vless", "inbound_enabled", "inbound_reality", "config_present",
        "service_present", "public_443_listening", "backend_10443_listening",
        "backend_10443_owned_by_xray", "frontend_config_valid",
    )
    for key in required_true:
        if probe.get(key) is not True:
            raise TransportFrontBootstrapError(f"fronted_preflight_{key}_required")
    expected = {
        "xui_state": "active",
        "frontend_state": "active",
        "inbound_listen_state": "loopback_v4",
        "inbound_port": BACKEND_PORT,
        "config_sha256": config_sha256,
        "service_sha256": service_sha256,
        "smart_dns_18443_listening": False,
    }
    for key, value in expected.items():
        if probe.get(key) != value:
            raise TransportFrontBootstrapError(f"fronted_preflight_{key}_mismatch")


def _remote_write(ssh: Any, path: str, content: bytes, mode: int) -> None:
    sftp = ssh.open_sftp()
    try:
        with sftp.file(path, "xb") as remote:
            remote.set_pipelined(True)
            remote.write(content)
            remote.flush()
        sftp.chmod(path, mode)
    except OSError as exc:
        raise TransportFrontBootstrapError("remote_stage_write_failed") from exc
    finally:
        sftp.close()


_SQL_CAS_HELPER = r'''
import argparse
import hashlib
import json
import sqlite3

p = argparse.ArgumentParser()
p.add_argument("--mode", choices=("apply", "rollback"), required=True)
p.add_argument("--inbound-id", type=int, required=True)
p.add_argument("--expected-invariant", required=True)
a = p.parse_args()

db = sqlite3.connect("/etc/x-ui/x-ui.db", timeout=10)
db.execute("pragma busy_timeout=10000")
db.execute("begin immediate")
row = db.execute(
    "select id,protocol,enable,stream_settings from inbounds where id=?", (a.inbound_id,)
).fetchone()
if row is None:
    db.rollback()
    raise SystemExit(41)
payload = json.dumps(
    [int(row[0]), str(row[1] or ""), int(bool(row[2])), str(row[3] or "")],
    ensure_ascii=True,
    separators=(",", ":"),
).encode("utf-8")
if hashlib.sha256(payload).hexdigest() != a.expected_invariant:
    db.rollback()
    raise SystemExit(43)
if a.mode == "apply":
    cur = db.execute(
        "update inbounds set listen=?,port=? where id=? and coalesce(listen,'')='' and port=? and protocol='vless' and enable=1",
        ("127.0.0.1", 10443, a.inbound_id, 443),
    )
else:
    cur = db.execute(
        "update inbounds set listen=?,port=? where id=? and listen=? and port=? and protocol='vless' and enable=1",
        ("", 443, a.inbound_id, "127.0.0.1", 10443),
    )
if cur.rowcount != 1:
    db.rollback()
    raise SystemExit(42)
db.commit()
db.close()
'''.strip()


def _embedded_python_command(source: str, *arguments: str) -> str:
    encoded = base64.b64encode(source.encode("utf-8")).decode("ascii")
    suffix = " ".join(_q(value) for value in arguments)
    return f"python3 -c \"$(printf %s {_q(encoded)} | base64 -d)\" {suffix}".rstrip()


def _receipt_payload(
    *, receipt_id: str, node_code: str, inbound_id: int, config_sha256: str,
    service_sha256: str, inbound_invariant_sha256: str, haproxy_was_present: bool
) -> bytes:
    payload = {
        "schema_version": REPORT_SCHEMA,
        "receipt_id": receipt_id,
        "node_code": node_code,
        "inbound_id": inbound_id,
        "from_listen": "wildcard_empty",
        "from_port": PUBLIC_PORT,
        "to_listen": BACKEND_HOST,
        "to_port": BACKEND_PORT,
        "config_sha256": config_sha256,
        "service_sha256": service_sha256,
        "inbound_invariant_sha256": inbound_invariant_sha256,
        "haproxy_was_present": haproxy_was_present,
        "state": "armed",
    }
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _apply_command(
    *, inbound_id: int, stage_config: str, stage_service: str, receipt_path: str,
    config_sha256: str, service_sha256: str, inbound_invariant_sha256: str,
    haproxy_was_present: bool
) -> str:
    cas_apply = _embedded_python_command(
        _SQL_CAS_HELPER, "--mode", "apply", "--inbound-id", str(inbound_id),
        "--expected-invariant", inbound_invariant_sha256
    )
    cas_rollback = _embedded_python_command(
        _SQL_CAS_HELPER, "--mode", "rollback", "--inbound-id", str(inbound_id),
        "--expected-invariant", inbound_invariant_sha256
    )
    installed = "no" if haproxy_was_present else "yes"
    return "\n".join(
        [
            "set -eu",
            f"stage_config={_q(stage_config)}",
            f"stage_service={_q(stage_service)}",
            f"receipt={_q(receipt_path)}",
            "moved=no",
            f"installed={installed}",
            "front_files=no",
            "rollback() {",
            "  rc=$?",
            "  trap - EXIT INT TERM HUP",
            "  rollback_ok=yes",
            f"  systemctl disable --now {_q(SERVICE_NAME)} >/dev/null 2>&1 || rollback_ok=no",
            f"  if test \"$moved\" = yes; then {cas_rollback} >/dev/null 2>&1 || rollback_ok=no; systemctl restart {_q(XUI_SERVICE)} >/dev/null 2>&1 || rollback_ok=no; fi",
            f"  if test \"$front_files\" = yes; then rm -f -- {_q(CONFIG_PATH)} {_q(SERVICE_PATH)} || rollback_ok=no; systemctl daemon-reload >/dev/null 2>&1 || rollback_ok=no; fi",
            f"  if test \"$installed\" = yes; then DEBIAN_FRONTEND=noninteractive apt-get remove -y haproxy >/dev/null 2>&1 || rollback_ok=no; systemctl unmask {_q(DEFAULT_HAPROXY_SERVICE)} >/dev/null 2>&1 || rollback_ok=no; fi",
            f"  systemctl is-active --quiet {_q(XUI_SERVICE)} || rollback_ok=no",
            f"  ss -H -ltnp 'sport = :{PUBLIC_PORT}' | grep -qi xray || rollback_ok=no",
            "  rollback_state=automatic_rollback_pass",
            "  if test \"$rollback_ok\" != yes; then rollback_state=automatic_rollback_fail; fi",
            "  ROLLBACK_STATE=\"$rollback_state\" python3 - \"$receipt\" <<'PY' || rollback_ok=no",
            "import json,os,sys,tempfile",
            "p=sys.argv[1]; d=json.load(open(p,encoding='utf-8')); d['state']=os.environ['ROLLBACK_STATE']",
            "fd,t=tempfile.mkstemp(prefix='.receipt-',dir=os.path.dirname(p)); os.fchmod(fd,0o600)",
            "with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(d,f,sort_keys=True,separators=(',',':')); f.write('\\n'); f.flush(); os.fsync(f.fileno())",
            "os.replace(t,p)",
            "PY",
            "  if test \"$rollback_ok\" != yes; then exit 97; fi",
            "  exit \"$rc\"",
            "}",
            "trap rollback EXIT INT TERM HUP",
            f"test \"$(sha256sum \"$stage_config\" | cut -d' ' -f1)\" = {_q(config_sha256)}",
            f"test \"$(sha256sum \"$stage_service\" | cut -d' ' -f1)\" = {_q(service_sha256)}",
            "if test \"$installed\" = yes; then",
            f"  systemctl mask {_q(DEFAULT_HAPROXY_SERVICE)} >/dev/null",
            "  DEBIAN_FRONTEND=noninteractive apt-get update >/dev/null",
            "  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends haproxy >/dev/null",
            "fi",
            "haproxy -c -f \"$stage_config\" >/dev/null",
            f"{cas_apply}",
            "moved=yes",
            f"systemctl restart {_q(XUI_SERVICE)}",
            f"systemctl is-active --quiet {_q(XUI_SERVICE)}",
            f"ss -H -ltnp | grep -E '127\\.0\\.0\\.1:{BACKEND_PORT}([[:space:]]|$)' | grep -qi xray",
            f"if ss -H -ltn 'sport = :{PUBLIC_PORT}' | grep -q .; then exit 45; fi",
            "front_files=yes",
            f"install -o root -g root -m 0644 \"$stage_config\" {_q(CONFIG_PATH)}",
            f"install -o root -g root -m 0644 \"$stage_service\" {_q(SERVICE_PATH)}",
            "systemctl daemon-reload",
            f"systemctl enable --now {_q(SERVICE_NAME)}",
            f"systemctl is-active --quiet {_q(SERVICE_NAME)}",
            f"haproxy -c -f {_q(CONFIG_PATH)} >/dev/null",
            f"ss -H -ltnp 'sport = :{PUBLIC_PORT}' | grep -qi haproxy",
            f"ss -H -ltnp 'sport = :{BACKEND_PORT}' | grep -qi xray",
            "python3 - \"$receipt\" <<'PY'",
            "import json,os,sys,tempfile",
            "p=sys.argv[1]; d=json.load(open(p,encoding='utf-8')); d['state']='applied'",
            "fd,t=tempfile.mkstemp(prefix='.receipt-',dir=os.path.dirname(p)); os.fchmod(fd,0o600)",
            "with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(d,f,sort_keys=True,separators=(',',':')); f.write('\\n'); f.flush(); os.fsync(f.fileno())",
            "os.replace(t,p)",
            "PY",
            "trap - EXIT INT TERM HUP",
            "printf 'apply_status=pass\\n'",
        ]
    )


def _receipt_probe_command(receipt_path: str) -> str:
    source = r'''
import json,os,re,stat,sys
p=sys.argv[1]
st=os.lstat(p)
if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode) or stat.S_IMODE(st.st_mode) != 0o600 or st.st_uid != 0:
    raise SystemExit(40)
d=json.load(open(p,encoding="utf-8"))
allowed={"schema_version","receipt_id","node_code","inbound_id","from_listen","from_port","to_listen","to_port","config_sha256","service_sha256","inbound_invariant_sha256","haproxy_was_present","state"}
if set(d)!=allowed: raise SystemExit(41)
safe={k:d[k] for k in ("schema_version","receipt_id","node_code","inbound_id","config_sha256","service_sha256","inbound_invariant_sha256","haproxy_was_present","state")}
print(json.dumps(safe,sort_keys=True,separators=(",",":")))
'''.strip()
    return _embedded_python_command(source, receipt_path)


def _load_receipt_probe(ssh: Any, *, receipt_id: str) -> dict[str, Any]:
    path = f"{RECEIPT_ROOT}/{receipt_id}/receipt.json"
    raw = _run(ssh, _receipt_probe_command(path), label="receipt_probe")
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TransportFrontBootstrapError("receipt_probe_json_invalid") from exc
    required = {
        "schema_version", "receipt_id", "node_code", "inbound_id", "config_sha256",
        "service_sha256", "inbound_invariant_sha256", "haproxy_was_present", "state",
    }
    if not isinstance(result, dict) or set(result) != required:
        raise TransportFrontBootstrapError("receipt_probe_contract_invalid")
    if result["schema_version"] != REPORT_SCHEMA or result["receipt_id"] != receipt_id:
        raise TransportFrontBootstrapError("receipt_probe_identity_invalid")
    if result["state"] not in {
        "armed", "applied", "rolled_back", "rolled_back_cleanup_pending",
        "automatic_rollback_pass", "automatic_rollback_fail",
        "rollback_failed_front_restored", "rollback_failed_unknown",
    }:
        raise TransportFrontBootstrapError("receipt_probe_state_invalid")
    if not SAFE_SHA256_RE.fullmatch(str(result["config_sha256"])) or not SAFE_SHA256_RE.fullmatch(str(result["service_sha256"])):
        raise TransportFrontBootstrapError("receipt_probe_digest_invalid")
    if not SAFE_SHA256_RE.fullmatch(str(result["inbound_invariant_sha256"])):
        raise TransportFrontBootstrapError("receipt_probe_inbound_invariant_invalid")
    return result


def _rollback_command(
    *, inbound_id: int, receipt_path: str, inbound_invariant_sha256: str,
    remove_haproxy: bool
) -> str:
    cas_direct = _embedded_python_command(
        _SQL_CAS_HELPER, "--mode", "rollback", "--inbound-id", str(inbound_id),
        "--expected-invariant", inbound_invariant_sha256
    )
    cas_fronted = _embedded_python_command(
        _SQL_CAS_HELPER, "--mode", "apply", "--inbound-id", str(inbound_id),
        "--expected-invariant", inbound_invariant_sha256
    )
    lines = [
        "set -eu",
        "direct_db=no",
        "recover_fronted() {",
        "  rc=$?",
        "  trap - EXIT INT TERM HUP",
        "  recovery_ok=yes",
        f"  if test \"$direct_db\" = yes; then {cas_fronted} >/dev/null 2>&1 || recovery_ok=no; systemctl restart {_q(XUI_SERVICE)} >/dev/null 2>&1 || recovery_ok=no; fi",
        f"  systemctl enable --now {_q(SERVICE_NAME)} >/dev/null 2>&1 || recovery_ok=no",
        f"  systemctl is-active --quiet {_q(SERVICE_NAME)} || recovery_ok=no",
        f"  ss -H -ltnp 'sport = :{PUBLIC_PORT}' | grep -qi haproxy || recovery_ok=no",
        "  recovery_state=rollback_failed_front_restored",
        "  if test \"$recovery_ok\" != yes; then recovery_state=rollback_failed_unknown; fi",
        f"  RECOVERY_STATE=\"$recovery_state\" python3 - {_q(receipt_path)} <<'PY' || true",
        "import json,os,sys,tempfile",
        "p=sys.argv[1]; d=json.load(open(p,encoding='utf-8')); d['state']=os.environ['RECOVERY_STATE']",
        "fd,t=tempfile.mkstemp(prefix='.receipt-',dir=os.path.dirname(p)); os.fchmod(fd,0o600)",
        "with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(d,f,sort_keys=True,separators=(',',':')); f.write('\\n'); f.flush(); os.fsync(f.fileno())",
        "os.replace(t,p)",
        "PY",
        "  if test \"$recovery_ok\" != yes; then exit 98; fi",
        "  exit \"$rc\"",
        "}",
        "trap recover_fronted EXIT INT TERM HUP",
        f"{cas_direct}",
        "direct_db=yes",
        f"systemctl disable --now {_q(SERVICE_NAME)}",
        f"systemctl restart {_q(XUI_SERVICE)}",
        f"systemctl is-active --quiet {_q(XUI_SERVICE)}",
        f"ss -H -ltnp 'sport = :{PUBLIC_PORT}' | grep -qi xray",
        "trap - EXIT INT TERM HUP",
        "cleanup_ok=yes",
        f"rm -f -- {_q(CONFIG_PATH)} {_q(SERVICE_PATH)} || cleanup_ok=no",
        "systemctl daemon-reload || cleanup_ok=no",
    ]
    if remove_haproxy:
        lines.extend(
            [
                "DEBIAN_FRONTEND=noninteractive apt-get remove -y haproxy >/dev/null || cleanup_ok=no",
                f"systemctl unmask {_q(DEFAULT_HAPROXY_SERVICE)} >/dev/null 2>&1 || true",
            ]
        )
    lines.extend(
        [
            "receipt_state=rolled_back",
            "if test \"$cleanup_ok\" != yes; then receipt_state=rolled_back_cleanup_pending; fi",
            f"RECEIPT_STATE=\"$receipt_state\" python3 - {_q(receipt_path)} <<'PY'",
            "import json,os,sys,tempfile",
            "p=sys.argv[1]; d=json.load(open(p,encoding='utf-8')); d['state']=os.environ['RECEIPT_STATE']",
            "fd,t=tempfile.mkstemp(prefix='.receipt-',dir=os.path.dirname(p)); os.fchmod(fd,0o600)",
            "with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(d,f,sort_keys=True,separators=(',',':')); f.write('\\n'); f.flush(); os.fsync(f.fileno())",
            "os.replace(t,p)",
            "PY",
            "if test \"$cleanup_ok\" != yes; then exit 96; fi",
            "printf 'rollback_status=pass\\n'",
        ]
    )
    return "\n".join(lines)


def _write_report(report: Mapping[str, Any], output: str) -> None:
    if not str(output or "").strip():
        return
    path = Path(output).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(report), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Guarded first HAProxy transport-front bootstrap for one owned x-ui Reality inbound."
    )
    parser.add_argument("--brain-host", default="")
    parser.add_argument("--node-code", required=True)
    parser.add_argument("--inbound-id", type=int, required=True)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--operation", choices=("install", "rollback"), default="install")
    parser.add_argument("--receipt-id", default="")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-node-code", default="")
    parser.add_argument("--confirm-inbound-id", default="")
    parser.add_argument("--confirm-config-sha256", default="")
    parser.add_argument("--confirm-service-sha256", default="")
    parser.add_argument("--confirm-inbound-invariant-sha256", default="")
    parser.add_argument("--confirm-external-mutation", default="")
    parser.add_argument("--json-out", default="")
    return parser


def main() -> int:
    args = _parser().parse_args()
    failure: dict[str, Any] = {
        "receipt_id": None,
        "receipt_created": False,
        "mutation_attempted": False,
        "automatic_rollback_status": "NOT_ARMED",
    }
    brain = None
    node = None
    try:
        node_code = _safe_component(args.node_code, label="node_code")
        inbound_id = _safe_positive_int(args.inbound_id, label="inbound_id")
        passwords = Path(args.passwords).expanduser().resolve(strict=True)
        config = _canonical_text(CONFIG_SOURCE)
        service = _canonical_text(SERVICE_SOURCE)
        _validate_sources(config, service)
        config_sha256 = _sha256_bytes(config)
        service_sha256 = _sha256_bytes(service)
        brain_host = str(args.brain_host or os.getenv("BRAIN_HOST", "")).strip()
        if not brain_host:
            raise TransportFrontBootstrapError("brain_host_missing")
        brain, brain_auth = _connect_owned(code="brain", host=brain_host, passwords=passwords)
        node_host = _resolve_node_host(brain, node_code)
        node, node_auth = _connect_owned(code=node_code, host=node_host, passwords=passwords)

        receipt = None
        receipt_id = ""
        if args.operation == "rollback":
            receipt_id = str(args.receipt_id or "").strip()
            if not SAFE_RECEIPT_RE.fullmatch(receipt_id):
                raise TransportFrontBootstrapError("receipt_id_invalid")
            failure["receipt_id"] = receipt_id
            receipt = _load_receipt_probe(node, receipt_id=receipt_id)
            if receipt["node_code"] != node_code or int(receipt["inbound_id"]) != inbound_id:
                raise TransportFrontBootstrapError("receipt_target_mismatch")
            config_sha256 = str(receipt["config_sha256"])
            service_sha256 = str(receipt["service_sha256"])
            probe = _remote_probe(node, inbound_id=inbound_id, expected_state="fronted")
            _assert_fronted_preflight(
                probe, config_sha256=config_sha256, service_sha256=service_sha256
            )
        else:
            probe = _remote_probe(node, inbound_id=inbound_id, expected_state="direct")
            _assert_direct_preflight(probe)

        report: dict[str, Any] = {
            "schema_version": REPORT_SCHEMA,
            "mode": "APPLY" if args.apply else "PLAN",
            "operation": args.operation,
            "node_code": node_code,
            "inbound_id": inbound_id,
            "config_sha256": config_sha256,
            "service_sha256": service_sha256,
            "brain_auth_method": _auth_family(brain_auth),
            "node_auth_method": _auth_family(node_auth),
            "preflight": probe,
            "bootstrap_applicable": True,
            "smart_dns_included": False,
            "mutation_performed": False,
            "raw_host_returned": False,
            "raw_config_returned": False,
            "raw_runtime_material_returned": False,
        }
        if receipt is not None:
            report["receipt_id"] = receipt_id
            report["receipt_state"] = receipt["state"]
        if not args.apply:
            report["plan"] = (
                [
                    "create_root_only_digest_bound_receipt",
                    "mask_default_haproxy_unit_and_install_package_if_absent",
                    "validate_staged_frontend",
                    "cas_move_exact_xui_inbound_to_loopback_10443",
                    "restart_xui_and_verify_loopback_listener",
                    "install_enable_and_verify_portal_transport_front_on_443",
                    "automatic_rollback_on_any_failed_guard",
                ]
                if args.operation == "install"
                else [
                    "verify_exact_applied_receipt_and_current_fronted_state",
                    "stop_portal_transport_front",
                    "cas_restore_exact_xui_inbound_to_wildcard_443",
                    "restart_xui_and_verify_direct_listener",
                    "remove_only_files_and_package_owned_by_receipt",
                    "retain_receipt_as_rolled_back",
                ]
            )
            _write_report(report, args.json_out)
            print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
            return 0

        if str(args.confirm_node_code).strip().lower() != node_code:
            raise TransportFrontBootstrapError("confirm_node_code_mismatch")
        if _safe_positive_int(args.confirm_inbound_id, label="confirm_inbound_id") != inbound_id:
            raise TransportFrontBootstrapError("confirm_inbound_id_mismatch")
        if str(args.confirm_config_sha256).strip().lower() != config_sha256:
            raise TransportFrontBootstrapError("confirm_config_sha256_mismatch")
        if str(args.confirm_service_sha256).strip().lower() != service_sha256:
            raise TransportFrontBootstrapError("confirm_service_sha256_mismatch")
        expected_invariant = (
            str(receipt["inbound_invariant_sha256"])
            if receipt is not None
            else str(probe["inbound_invariant_sha256"])
        )
        if str(args.confirm_inbound_invariant_sha256).strip().lower() != expected_invariant:
            raise TransportFrontBootstrapError("confirm_inbound_invariant_sha256_mismatch")

        if args.operation == "install":
            if str(args.confirm_external_mutation).strip() != "OWNED_TRANSPORT_FRONT_BOOTSTRAP_AUTHORIZED":
                raise TransportFrontBootstrapError("bootstrap_mutation_confirmation_missing")
            receipt_id = _release_id(config_sha256)
            failure["receipt_id"] = receipt_id
            receipt_dir = f"{RECEIPT_ROOT}/{receipt_id}"
            receipt_path = f"{receipt_dir}/receipt.json"
            stage_config = f"{receipt_dir}/candidate.cfg"
            stage_service = f"{receipt_dir}/candidate.service"
            _run(
                node,
                f"install -d -o root -g root -m 0700 {_q(RECEIPT_ROOT)}; test ! -e {_q(receipt_dir)}; install -d -o root -g root -m 0700 {_q(receipt_dir)}",
                label="receipt_directory_prepare",
            )
            try:
                _remote_write(node, stage_config, config, 0o600)
                _remote_write(node, stage_service, service, 0o600)
                receipt_payload = _receipt_payload(
                    receipt_id=receipt_id,
                    node_code=node_code,
                    inbound_id=inbound_id,
                    config_sha256=config_sha256,
                    service_sha256=service_sha256,
                    inbound_invariant_sha256=expected_invariant,
                    haproxy_was_present=bool(probe["haproxy_present"]),
                )
                _remote_write(node, receipt_path, receipt_payload, 0o600)
                failure["receipt_created"] = True
                failure["mutation_attempted"] = True
                failure["automatic_rollback_status"] = "ARMED"
                _run(
                    node,
                    _apply_command(
                        inbound_id=inbound_id,
                        stage_config=stage_config,
                        stage_service=stage_service,
                        receipt_path=receipt_path,
                        config_sha256=config_sha256,
                        service_sha256=service_sha256,
                        inbound_invariant_sha256=expected_invariant,
                        haproxy_was_present=bool(probe["haproxy_present"]),
                    ),
                    label="bootstrap_apply",
                    timeout=600,
                )
                post = _remote_probe(node, inbound_id=inbound_id, expected_state="fronted")
                _assert_fronted_preflight(
                    post, config_sha256=config_sha256, service_sha256=service_sha256
                )
            except Exception:
                try:
                    failed_receipt = _load_receipt_probe(node, receipt_id=receipt_id)
                    if failed_receipt["state"] == "automatic_rollback_pass":
                        failure["automatic_rollback_status"] = "PASS"
                    elif failed_receipt["state"] == "automatic_rollback_fail":
                        failure["automatic_rollback_status"] = "FAIL"
                    elif failed_receipt["state"] == "applied":
                        _run(
                            node,
                            _rollback_command(
                                inbound_id=inbound_id,
                                receipt_path=receipt_path,
                                inbound_invariant_sha256=expected_invariant,
                                remove_haproxy=not bool(probe["haproxy_present"]),
                            ),
                            label="postflight_automatic_rollback",
                            timeout=600,
                        )
                        restored = _remote_probe(
                            node, inbound_id=inbound_id, expected_state="direct"
                        )
                        _assert_direct_preflight(restored)
                        failure["automatic_rollback_status"] = "PASS"
                    else:
                        failure["automatic_rollback_status"] = "UNKNOWN"
                except Exception:
                    failure["automatic_rollback_status"] = "UNKNOWN"
                raise
            finally:
                _run_allow_failure(node, f"rm -f -- {_q(stage_config)} {_q(stage_service)}")
            report.update(
                {
                    "mutation_performed": True,
                    "receipt_id": receipt_id,
                    "automatic_rollback_armed": True,
                    "postflight": post,
                }
            )
        else:
            if str(args.confirm_external_mutation).strip() != "OWNED_TRANSPORT_FRONT_ROLLBACK_AUTHORIZED":
                raise TransportFrontBootstrapError("rollback_mutation_confirmation_missing")
            if receipt is None or receipt["state"] != "applied":
                raise TransportFrontBootstrapError("rollback_receipt_not_applied")
            failure["mutation_attempted"] = True
            receipt_path = f"{RECEIPT_ROOT}/{receipt_id}/receipt.json"
            _run(
                node,
                _rollback_command(
                    inbound_id=inbound_id,
                    receipt_path=receipt_path,
                    inbound_invariant_sha256=expected_invariant,
                    remove_haproxy=not bool(receipt["haproxy_was_present"]),
                ),
                label="explicit_rollback",
                timeout=600,
            )
            post = _remote_probe(node, inbound_id=inbound_id, expected_state="direct")
            _assert_direct_preflight(post)
            report.update(
                {"mutation_performed": True, "receipt_id": receipt_id, "postflight": post}
            )
        _write_report(report, args.json_out)
        print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        code = str(exc).split(":", 1)[0][:160]
        report = {
            "schema_version": REPORT_SCHEMA,
            "mode": "ERROR",
            "operation": str(getattr(args, "operation", "unknown")),
            "error_code": code,
            **failure,
            "raw_host_returned": False,
            "raw_config_returned": False,
            "raw_runtime_material_returned": False,
        }
        try:
            _write_report(report, str(getattr(args, "json_out", "") or ""))
        except Exception:
            pass
        print(
            f"owned transport front bootstrap failed: {type(exc).__name__}: {code}",
            file=sys.stderr,
        )
        return 1
    finally:
        if node is not None:
            node.close()
        if brain is not None:
            brain.close()


if __name__ == "__main__":
    raise SystemExit(main())
