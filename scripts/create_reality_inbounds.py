from __future__ import annotations

"""
Create or discover a standard VLESS Reality inbound on fresh 3x-ui nodes.

Why this exists:
- New nodes are "empty" and have no inbounds.
- Control-plane needs an inbound_id + Reality params (SNI/PBK/SID) per node.

How it works:
- Connect to each node via SSH (password auth).
- Call the local 3x-ui panel API on 127.0.0.1:<panel_port>/<panel_path>/...
- Ensure there is a VLESS Reality inbound on port 443.

Security:
- This script avoids printing panel credentials.
- It writes output with only public Reality parameters (PBK/SID/SNI) and inbound_id.
"""

import argparse
import base64
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import paramiko
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = REPO_ROOT / "docs" / "08-node-inventory.md"
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


REMOTE_SCRIPT = r"""
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
        ctype = resp.headers.get("Content-Type", "")
        return resp.status, body, ctype


def _json_loads(b: bytes):
    try:
        return json.loads(b.decode("utf-8", errors="replace"))
    except Exception:
        return None


def main() -> int:
    payload_b64 = sys.argv[1].strip()
    pad = "=" * ((4 - (len(payload_b64) % 4)) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + pad).decode("utf-8"))

    panel_port = int(payload["panel_port"])
    panel_path = str(payload["panel_path"]).strip("/").strip()
    panel_user = payload["panel_user"]
    panel_pass = payload["panel_pass"]

    desired = payload["desired"]
    desired_port = int(desired["port"])
    desired_protocol = desired["protocol"]

    base = f"http://127.0.0.1:{panel_port}/{panel_path}"
    login_url = f"{base}/login"
    list_url = f"{base}/panel/api/inbounds/list"
    add_url = f"{base}/panel/api/inbounds/add"

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # login
    data = urllib.parse.urlencode({"username": panel_user, "password": panel_pass}).encode("utf-8")
    st, body, _ = _req(opener, "POST", login_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if st != 200:
        print(json.dumps({"ok": False, "error": f"login_http_{st}"}))
        return 2

    st, body, _ = _req(opener, "GET", list_url)
    obj = _json_loads(body) or {}
    if not obj.get("success"):
        print(json.dumps({"ok": False, "error": "list_failed", "details": obj}))
        return 3

    inbounds = obj.get("obj", []) or []
    for inb in inbounds:
        if int(inb.get("port", -1)) == desired_port and str(inb.get("protocol", "")).lower() == desired_protocol:
            print(json.dumps({"ok": True, "action": "exists", "inbound": inb}))
            return 0

    # create
    st, body, _ = _req(
        opener,
        "POST",
        add_url,
        data=json.dumps(desired).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    if st != 200:
        print(json.dumps({"ok": False, "error": f"add_http_{st}", "body": body.decode('utf-8', errors='replace')[:400]}))
        return 4
    obj = _json_loads(body) or {}
    if not obj.get("success"):
        print(json.dumps({"ok": False, "error": "add_failed", "details": obj}))
        return 5

    st, body, _ = _req(opener, "GET", list_url)
    obj = _json_loads(body) or {}
    if not obj.get("success"):
        print(json.dumps({"ok": False, "error": "list_failed_after_add", "details": obj}))
        return 6

    inbounds = obj.get("obj", []) or []
    for inb in inbounds:
        if int(inb.get("port", -1)) == desired_port and str(inb.get("protocol", "")).lower() == desired_protocol:
            print(json.dumps({"ok": True, "action": "created", "inbound": inb}))
            return 0

    print(json.dumps({"ok": False, "error": "created_but_not_found"}))
    return 7


if __name__ == "__main__":
    raise SystemExit(main())
"""


@dataclass(frozen=True)
class Node:
    code: str
    ip: str
    role: str


def _parse_inventory(path: Path) -> list[Node]:
    txt = path.read_text(encoding="utf-8", errors="replace")
    nodes: list[Node] = []
    for line in txt.splitlines():
        line = line.strip()
        if not line.startswith("|") or "`" not in line:
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        # Expected table: | Code | Role | Plan | IP |
        if len(parts) < 4:
            continue
        code = parts[0].strip("`").strip()
        role = parts[1].strip("`").strip()
        ip = parts[3].strip("`").strip()
        if not code or code.lower() == "code":
            continue
        if not re.fullmatch(r"[a-z0-9_-]+", code):
            continue
        if not re.fullmatch(r"(\d{1,3}\.){3}\d{1,3}", ip):
            continue
        nodes.append(Node(code=code, ip=ip, role=role))
    if not nodes:
        raise SystemExit(f"Failed to parse inventory: {path}")
    return nodes


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


def _load_node_facts(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    results = data.get("results", [])
    out: dict[str, dict] = {}
    for r in results:
        code = str(r.get("code", "")).strip()
        if not code:
            continue
        out[code] = r
    return out


def _ssh_connect(ip: str, *, user: str, port: int, password: str) -> paramiko.SSHClient:
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(ip, port=port, username=user, password=password, timeout=30, banner_timeout=30, auth_timeout=30)
    t = cli.get_transport()
    if t:
        t.set_keepalive(30)
    return cli


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def _b64url_nopad(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def _gen_reality_keypair() -> tuple[str, str]:
    priv = x25519.X25519PrivateKey.generate()
    priv_bytes = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return _b64url_nopad(priv_bytes), _b64url_nopad(pub_bytes)


def _derive_public_from_private(priv_b64: str) -> str:
    pad = "=" * ((4 - (len(priv_b64) % 4)) % 4)
    priv_bytes = base64.urlsafe_b64decode(priv_b64 + pad)
    priv = x25519.X25519PrivateKey.from_private_bytes(priv_bytes)
    pub_bytes = priv.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    return _b64url_nopad(pub_bytes)


def _upload_and_run(ssh: paramiko.SSHClient, *, payload: dict) -> dict:
    payload_b64 = _b64url_nopad(json.dumps(payload, ensure_ascii=True).encode("utf-8"))
    sftp = ssh.open_sftp()
    try:
        remote_py = "/tmp/ensure_inbound.py"
        with sftp.file(remote_py, "w") as f:
            f.write(REMOTE_SCRIPT)
        sftp.chmod(remote_py, 0o700)
    finally:
        sftp.close()

    code, out, err = _run(ssh, f"python3 /tmp/ensure_inbound.py {payload_b64}", timeout=180)
    # best-effort cleanup
    _run(ssh, "rm -f /tmp/ensure_inbound.py", timeout=30)
    if code != 0:
        raise RuntimeError(f"remote script failed (code={code}): {err.strip() or out.strip()}")
    try:
        return json.loads(out.strip() or "{}")
    except Exception as e:
        raise RuntimeError(f"failed to parse remote JSON: {e}; out={out[:400]!r}; err={err[:200]!r}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--node-facts", default="", help="node_facts-*.json from bootstrap step")
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--only", default="", help="comma-separated node codes (default: all except brain)")
    ap.add_argument("--include-brain", action="store_true")
    ap.add_argument("--sni", default="www.cloudflare.com")
    ap.add_argument("--dest", default="www.cloudflare.com:443")
    ap.add_argument("--flow", default="xtls-rprx-vision")
    ap.add_argument("--fingerprint", default="firefox")
    ap.add_argument("--out", default="", help="write JSON result to path")
    args = ap.parse_args()

    nodes = _parse_inventory(Path(args.inventory))
    only = {c.strip() for c in args.only.split(",") if c.strip()}
    if only:
        nodes = [n for n in nodes if n.code in only]
    else:
        # default: only workers
        if not args.include_brain:
            nodes = [n for n in nodes if n.code != "brain"]

    pw_map = _parse_passwords(Path(args.passwords))

    # node facts are required because panel port/path/user/pass are randomized
    nf_path = Path(args.node_facts) if args.node_facts else None
    if nf_path is None:
        # auto-pick the latest node_facts-*.json in repo root
        cands = sorted(REPO_ROOT.glob("node_facts-*.json"))
        if not cands:
            raise SystemExit("Missing --node-facts and no node_facts-*.json found in repo root.")
        nf_path = cands[-1]
    facts_map = _load_node_facts(nf_path)

    results: list[dict] = []
    for n in nodes:
        pw = os.getenv(f"NODE_PASS_{n.code.upper()}", "").strip() or pw_map.get(n.code, "")
        if not pw:
            raise SystemExit(f"Missing password for node {n.code}")
        facts = facts_map.get(n.code)
        if not facts:
            raise SystemExit(f"node_facts missing entry for {n.code} (file={nf_path})")

        panel_port = int(facts["panel_port"])
        panel_path = str(facts["panel_path"])
        panel_user = str(facts["panel_user"])
        panel_pass = str(facts["panel_pass"])

        print(f"[{n.code}] ensure inbound on {n.ip} ...")
        ssh = _ssh_connect(n.ip, user=args.ssh_user, port=args.ssh_port, password=pw)
        try:
            # Generate keys for the "create" path. If inbound already exists, we will ignore these.
            priv_b64, pub_b64 = _gen_reality_keypair()
            short_id = os.urandom(8).hex()

            desired = {
                "up": 0,
                "down": 0,
                "total": 0,
                "remark": f"{n.code.upper()} Reality",
                "enable": True,
                "expiryTime": 0,
                "listen": "",
                "port": 443,
                "protocol": "vless",
                "settings": json.dumps({"clients": [], "decryption": "none", "fallbacks": []}, ensure_ascii=True),
                "streamSettings": json.dumps(
                    {
                        "network": "tcp",
                        "security": "reality",
                        "realitySettings": {
                            "show": False,
                            "dest": args.dest,
                            "xver": 0,
                            "serverNames": [args.sni],
                            "privateKey": priv_b64,
                            "minClientVer": "",
                            "maxClientVer": "",
                            "maxTimeDiff": 0,
                            "shortIds": [short_id],
                        },
                        "tcpSettings": {"header": {"type": "none"}},
                    },
                    ensure_ascii=True,
                ),
                "sniffing": json.dumps({"enabled": True, "destOverride": ["http", "tls", "quic"], "metadataOnly": False}, ensure_ascii=True),
                "tag": f"vless-{n.code}",
            }

            payload = {
                "panel_port": panel_port,
                "panel_path": panel_path,
                "panel_user": panel_user,
                "panel_pass": panel_pass,
                "desired": desired,
            }

            resp = _upload_and_run(ssh, payload=payload)
            if not resp.get("ok"):
                raise RuntimeError(f"panel operation failed: {resp}")

            inb = resp.get("inbound") or {}
            inbound_id = int(inb.get("id"))

            # If it already existed, derive PBK/SID from the existing streamSettings.
            if resp.get("action") == "exists":
                try:
                    ss = json.loads(inb.get("streamSettings") or inb.get("stream_settings") or "{}")
                except Exception:
                    ss = {}
                rs = ss.get("realitySettings") or {}
                sni = (rs.get("serverNames") or [args.sni])[0]
                sid = (rs.get("shortIds") or [""])[0]
                pvk = str(rs.get("privateKey") or "")
                if not pvk or not sid:
                    raise RuntimeError("existing inbound found, but realitySettings missing privateKey/shortIds")
                pbk = _derive_public_from_private(pvk)
            else:
                sni = args.sni
                sid = short_id
                pbk = pub_b64

            results.append(
                {
                    "code": n.code,
                    "ip": n.ip,
                    "role": n.role,
                    "inbound_id": inbound_id,
                    "vless_port": 443,
                    "reality_sni": sni,
                    "reality_sid": sid,
                    "reality_pbk": pbk,
                    "fingerprint": args.fingerprint,
                    "flow": args.flow,
                }
            )
        finally:
            ssh.close()
        time.sleep(0.2)

    payload = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "results": results}
    if args.out:
        out_path = Path(args.out)
    else:
        out_path = REPO_ROOT / f"node_reality-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
