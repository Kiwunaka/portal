from __future__ import annotations

"""
One-shot setup for Free tier:
- On PL node:
  - create (or reuse) VLESS Reality inbound on port 8443, cloning Reality settings from port 443
  - open UFW 8443/tcp (best-effort)
  - install a systemd `tc` shaper to limit egress on port 8443 to 50mbit (aggregate)
- On brain node:
  - add/update nodes row `pl_free` (same host/Reality params as `pl`, but port=8443 and inbound_id=new)

This script reads secrets from local ignored files (node_facts/PASSWORDS) and does not print them.
"""

import argparse
import base64
import json
import os
import posixpath
import re
from dataclasses import dataclass
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = REPO_ROOT / "docs" / "08-node-inventory.md"
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
DEFAULT_LEGACY_INV_DIR = REPO_ROOT / "legacy" / "inventory" / "2026-02-07"


REMOTE_ENSURE_8443 = r"""
from __future__ import annotations

import base64
import json
import sys
import urllib.parse
import urllib.request
import http.cookiejar


def _req(opener, method: str, url: str, *, data: bytes | None = None, headers: dict | None = None, timeout: int = 20):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with opener.open(req, timeout=timeout) as resp:
        body = resp.read()
        return resp.status, body, resp.headers.get("Content-Type", "")


def _json_loads(b: bytes):
    try:
        return json.loads(b.decode("utf-8", errors="replace"))
    except Exception:
        return None


def _sanitize_inb(inb: dict) -> dict:
    out = {}
    for k in ("id", "remark", "port", "protocol", "enable", "tag"):
        if k in inb:
            out[k] = inb.get(k)
    # Do not return streamSettings/settings (may include private keys).
    return out


def main() -> int:
    payload_b64 = sys.argv[1].strip()
    pad = "=" * ((4 - (len(payload_b64) % 4)) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + pad).decode("utf-8"))

    panel_port = int(payload["panel_port"])
    panel_path = str(payload["panel_path"]).strip("/").strip()
    panel_user = payload["panel_user"]
    panel_pass = payload["panel_pass"]
    src_port = int(payload.get("src_port", 443))
    dst_port = int(payload.get("dst_port", 8443))

    base = f"http://127.0.0.1:{panel_port}/{panel_path}"
    login_url = f"{base}/login"
    list_url = f"{base}/panel/api/inbounds/list"
    add_url = f"{base}/panel/api/inbounds/add"

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    data = urllib.parse.urlencode({"username": panel_user, "password": panel_pass}).encode("utf-8")
    st, body, _ = _req(opener, "POST", login_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if st != 200:
        print(json.dumps({"ok": False, "error": f"login_http_{st}"}))
        return 2

    st, body, _ = _req(opener, "GET", list_url)
    obj = _json_loads(body) or {}
    if not obj.get("success"):
        print(json.dumps({"ok": False, "error": "list_failed"}))
        return 3

    inbounds = obj.get("obj", []) or []
    for inb in inbounds:
        if int(inb.get("port", -1)) == dst_port and str(inb.get("protocol", "")).lower() == "vless":
            print(json.dumps({"ok": True, "action": "exists", "inbound": _sanitize_inb(inb)}))
            return 0

    src = None
    for inb in inbounds:
        if int(inb.get("port", -1)) == src_port and str(inb.get("protocol", "")).lower() == "vless":
            src = inb
            break
    if not src:
        print(json.dumps({"ok": False, "error": "src_inbound_not_found"}))
        return 4

    sniffing = src.get("sniffing") or json.dumps({"enabled": True, "destOverride": ["http", "tls", "quic"], "metadataOnly": False}, ensure_ascii=True)
    stream = src.get("streamSettings") or src.get("stream_settings") or ""
    if not stream:
        print(json.dumps({"ok": False, "error": "src_missing_stream"}))
        return 5

    desired = {
        "up": 0,
        "down": 0,
        "total": 0,
        "remark": "PL Free Reality",
        "enable": True,
        "expiryTime": 0,
        "listen": "",
        "port": dst_port,
        "protocol": "vless",
        # New inbound should start empty (clients are created per-user).
        "settings": json.dumps({"clients": [], "decryption": "none", "fallbacks": []}, ensure_ascii=True),
        # Clone Reality settings from the main 443 inbound (same serverNames/dest/shortIds/privateKey).
        "streamSettings": stream,
        "sniffing": sniffing,
        "tag": "vless-pl-free",
    }

    st, body, _ = _req(opener, "POST", add_url, data=json.dumps(desired).encode("utf-8"), headers={"Content-Type": "application/json"})
    if st != 200:
        print(json.dumps({"ok": False, "error": f"add_http_{st}"}))
        return 6
    obj = _json_loads(body) or {}
    if not obj.get("success"):
        print(json.dumps({"ok": False, "error": "add_failed"}))
        return 7

    st, body, _ = _req(opener, "GET", list_url)
    obj = _json_loads(body) or {}
    if not obj.get("success"):
        print(json.dumps({"ok": False, "error": "list_failed_after_add"}))
        return 8
    inbounds = obj.get("obj", []) or []
    for inb in inbounds:
        if int(inb.get("port", -1)) == dst_port and str(inb.get("protocol", "")).lower() == "vless":
            print(json.dumps({"ok": True, "action": "created", "inbound": _sanitize_inb(inb)}))
            return 0

    print(json.dumps({"ok": False, "error": "created_but_not_found"}))
    return 9


if __name__ == "__main__":
    raise SystemExit(main())
"""


@dataclass(frozen=True)
class Node:
    code: str
    ip: str


def _parse_inventory(path: Path) -> dict[str, Node]:
    txt = path.read_text(encoding="utf-8", errors="replace")
    out: dict[str, Node] = {}
    for line in txt.splitlines():
        line = line.strip()
        if not line.startswith("|") or "`" not in line:
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 4:
            continue
        code = parts[0].strip("`").strip()
        ip = parts[3].strip("`").strip()
        if not code or code.lower() == "code":
            continue
        if not re.fullmatch(r"[a-z0-9_-]+", code):
            continue
        if not re.fullmatch(r"(\d{1,3}\.){3}\d{1,3}", ip):
            continue
        out[code] = Node(code=code, ip=ip)
    if not out:
        raise SystemExit(f"Failed to parse inventory: {path}")
    return out


def _parse_passwords(path: Path) -> dict[str, str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    out: dict[str, str] = {}
    markers = {"brain": "BRAINnode", "us": "USnode", "pl": "PLnode", "it": "ITnode", "free": "Free Node"}
    for code, marker in markers.items():
        try:
            idx = next(i for i, ln in enumerate(lines) if marker in ln)
        except StopIteration:
            continue
        pw = ""
        for j in range(idx + 1, min(idx + 12, len(lines))):
            ln = lines[j]
            if not ln or ln.startswith("ssh-ed25519 "):
                continue
            pw = ln
            break
        if pw:
            out[code] = pw
    return out


def _pick_node_facts_with_pl(path_hint: str) -> Path:
    if path_hint:
        p = Path(path_hint)
        if not p.exists():
            raise SystemExit(f"node_facts not found: {p}")
        return p

    cands: list[Path] = []
    for base in (REPO_ROOT, DEFAULT_LEGACY_INV_DIR):
        cands.extend(sorted(base.glob("node_facts-*.json")))
    # prefer latest file that has pl with panel_port/path/user/pass
    for p in reversed(sorted(cands)):
        try:
            data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            m = {r.get("code"): r for r in (data.get("results", []) or [])}
            pl = m.get("pl") or {}
            if pl.get("panel_port") and pl.get("panel_path") and pl.get("panel_user") and pl.get("panel_pass"):
                return p
        except Exception:
            continue
    raise SystemExit("Could not find a usable node_facts-*.json containing PL panel credentials.")


def _load_pl_panel_facts(node_facts_path: Path) -> dict:
    data = json.loads(node_facts_path.read_text(encoding="utf-8", errors="replace"))
    m = {r.get("code"): r for r in (data.get("results", []) or [])}
    pl = m.get("pl") or {}
    need = ("panel_port", "panel_path", "panel_user", "panel_pass")
    for k in need:
        if not pl.get(k):
            raise SystemExit(f"node_facts missing {k} for pl (file={node_facts_path})")
    return pl


def _ssh_connect(ip: str, *, user: str, port: int, password: str) -> paramiko.SSHClient:
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(ip, port=port, username=user, password=password, timeout=30, banner_timeout=30, auth_timeout=30)
    t = cli.get_transport()
    if t:
        t.set_keepalive(30)
    return cli


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 600) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def _b64url_nopad(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def _upload_text(sftp: paramiko.SFTPClient, remote_path: str, content: str) -> None:
    d = posixpath.dirname(remote_path)
    try:
        sftp.stat(d)
    except IOError:
        try:
            sftp.mkdir(d)
        except IOError:
            pass
    with sftp.file(remote_path, "w") as f:
        f.write(content)


def _ensure_pl_inbound_8443(*, pl_ip: str, ssh_user: str, ssh_port: int, ssh_pass: str, panel_facts: dict) -> int:
    ssh = _ssh_connect(pl_ip, user=ssh_user, port=ssh_port, password=ssh_pass)
    try:
        payload = {
            "panel_port": int(panel_facts["panel_port"]),
            "panel_path": str(panel_facts["panel_path"]),
            "panel_user": str(panel_facts["panel_user"]),
            "panel_pass": str(panel_facts["panel_pass"]),
            "src_port": 443,
            "dst_port": 8443,
        }
        payload_b64 = _b64url_nopad(json.dumps(payload, ensure_ascii=True).encode("utf-8"))
        sftp = ssh.open_sftp()
        try:
            remote_py = "/tmp/ensure_pl_free_8443.py"
            _upload_text(sftp, remote_py, REMOTE_ENSURE_8443)
        finally:
            sftp.close()

        code, out, err = _run(ssh, f"python3 {remote_py} {payload_b64}", timeout=120)
        if code != 0:
            raise RuntimeError(f"ensure inbound failed: {out.strip() or err.strip()}")
        resp = json.loads((out or "").strip() or "{}")
        if not resp.get("ok"):
            raise RuntimeError(f"ensure inbound failed: {resp}")
        inb = resp.get("inbound") or {}
        inbound_id = int(inb.get("id"))
        return inbound_id
    finally:
        ssh.close()


def _install_pl_shaper(*, pl_ip: str, ssh_user: str, ssh_port: int, ssh_pass: str, port: int, rate: str) -> None:
    ssh = _ssh_connect(pl_ip, user=ssh_user, port=ssh_port, password=ssh_pass)
    try:
        _run(ssh, "DEBIAN_FRONTEND=noninteractive apt-get update -y", timeout=900)
        _run(ssh, "DEBIAN_FRONTEND=noninteractive apt-get install -y iproute2", timeout=900)
        _run(ssh, f"(command -v ufw >/dev/null 2>&1 && ufw allow {int(port)}/tcp >/dev/null 2>&1 || true)", timeout=60)

        sftp = ssh.open_sftp()
        try:
            sftp.put(str(REPO_ROOT / "infra" / "setup_free_egress_shaper.sh"), "/root/setup_free_egress_shaper.sh")
            sftp.put(str(REPO_ROOT / "infra" / "install_free_egress_shaper.sh"), "/root/install_free_egress_shaper.sh")
        finally:
            sftp.close()

        _run(ssh, "chmod +x /root/setup_free_egress_shaper.sh /root/install_free_egress_shaper.sh", timeout=30)
        cmd = f"PORT={int(port)} RATE={rate} /root/install_free_egress_shaper.sh"
        code, out, err = _run(ssh, cmd, timeout=300)
        if code != 0:
            raise RuntimeError(f"install shaper failed: {out.strip() or err.strip()}")
    finally:
        ssh.close()


def _upsert_brain_pl_free(*, brain_ip: str, ssh_user: str, ssh_port: int, ssh_pass: str, inbound_id: int) -> None:
    remote_py = r"""
import sqlite3
import sys
from datetime import datetime

db = "/root/portal_bot/portal.db"
inb = int(sys.argv[1])

con = sqlite3.connect(db)
try:
    cur = con.cursor()
    row = cur.execute(
        "select name,host,vless_port,reality_sni,reality_pbk,reality_sid,fingerprint,flow,panel_base_url,panel_path,panel_user,panel_pass,inbound_id,enabled,weight from nodes where code='pl'"
    ).fetchone()
    if not row:
        raise SystemExit("missing pl node in brain portal.db")

    (name, host, vless_port, sni, pbk, sid, fp, flow, pbase, ppath, puser, ppass, inb_old, enabled, weight) = row
    code = "pl_free"
    new_name = "Poland"

    # upsert (two-step for compatibility)
    cur.execute(
        "update nodes set name=?, host=?, vless_port=?, reality_sni=?, reality_pbk=?, reality_sid=?, fingerprint=?, flow=?, panel_base_url=?, panel_path=?, panel_user=?, panel_pass=?, inbound_id=?, enabled=1, weight=? where code=?",
        (new_name, host, 8443, sni, pbk, sid, fp, flow, pbase, ppath, puser, ppass, inb, int(weight or 90), code),
    )
    if cur.rowcount == 0:
        cur.execute(
            "insert into nodes (code,name,host,vless_port,reality_sni,reality_pbk,reality_sid,fingerprint,flow,panel_base_url,panel_path,panel_user,panel_pass,inbound_id,enabled,weight) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (code, new_name, host, 8443, sni, pbk, sid, fp, flow, pbase, ppath, puser, ppass, inb, 1, int(weight or 90)),
        )
    con.commit()
finally:
    con.close()
print("OK")
"""
    ssh = _ssh_connect(brain_ip, user=ssh_user, port=ssh_port, password=ssh_pass)
    try:
        sftp = ssh.open_sftp()
        try:
            _upload_text(sftp, "/tmp/upsert_pl_free.py", remote_py)
        finally:
            sftp.close()
        code, out, err = _run(ssh, f"python3 /tmp/upsert_pl_free.py {int(inbound_id)}", timeout=60)
        if code != 0:
            raise RuntimeError(out.strip() or err.strip())
    finally:
        ssh.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--node-facts", default="", help="path to node_facts-*.json that contains PL panel creds")
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--rate", default="50mbit")
    args = ap.parse_args()

    inv = _parse_inventory(Path(args.inventory))
    if "pl" not in inv or "brain" not in inv:
        raise SystemExit("inventory must contain pl and brain")

    pw_map = _parse_passwords(Path(args.passwords))
    pl_pw = os.getenv("NODE_PASS_PL", "").strip() or pw_map.get("pl", "")
    brain_pw = os.getenv("NODE_PASS_BRAIN", "").strip() or pw_map.get("brain", "")
    if not pl_pw:
        raise SystemExit("Missing password for pl")
    if not brain_pw:
        raise SystemExit("Missing password for brain")

    nf = _pick_node_facts_with_pl(args.node_facts)
    pl_facts = _load_pl_panel_facts(nf)

    inbound_id = _ensure_pl_inbound_8443(
        pl_ip=inv["pl"].ip,
        ssh_user=args.ssh_user,
        ssh_port=args.ssh_port,
        ssh_pass=pl_pw,
        panel_facts=pl_facts,
    )
    print(f"PL inbound 8443: inbound_id={inbound_id}")

    _install_pl_shaper(
        pl_ip=inv["pl"].ip,
        ssh_user=args.ssh_user,
        ssh_port=args.ssh_port,
        ssh_pass=pl_pw,
        port=8443,
        rate=str(args.rate),
    )
    print("PL shaper: OK")

    _upsert_brain_pl_free(
        brain_ip=inv["brain"].ip,
        ssh_user=args.ssh_user,
        ssh_port=args.ssh_port,
        ssh_pass=brain_pw,
        inbound_id=inbound_id,
    )
    print("brain portal.db: pl_free OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

