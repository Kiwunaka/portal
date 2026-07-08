from __future__ import annotations

"""
Remote bootstrap for fresh Ubuntu nodes (brain + workers).

What it does (per node):
- Connects via SSH password (paramiko).
- Installs basic packages (curl/ufw/fail2ban/sqlite3).
- Installs 3x-ui (MHSanaei/3x-ui) if missing.
- Configures UFW:
  - allow SSH (22/tcp by default)
  - allow user traffic port 443/tcp
  - allow panel port only from control-plane IP (best-effort autodetect)

Security:
- No passwords are printed.
- Passwords can be provided via env vars, or (fallback) parsed from local
  `VPN NODE SSH KEYS/PASSWORDS.txt` (this folder is gitignored).
"""

import argparse
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy

from node_inventory import DEFAULT_INVENTORY, read_inventory
from node_passwords import parse_password_candidates


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


@dataclass(frozen=True)
class Node:
    code: str
    ip: str
    role: str


def _parse_inventory(path: Path) -> list[Node]:
    """
    Parse retained node inventory table rows.
    Expected row example:
    | `brain` | Brain / control-plane candidate | ... | `82.21.114.104` |
    """
    nodes = [Node(code=row.code, ip=row.ip, role=row.role) for row in read_inventory(path)]
    if not nodes:
        raise SystemExit(f"Failed to parse inventory: {path}")
    return nodes


def _parse_passwords(path: Path) -> dict[str, str]:
    """
    Parse local PASSWORDS.txt.
    We match blocks by marker words like 'BRAINnode', 'USnode', etc and take the next
    non-empty non-pubkey line as password.
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    out: dict[str, str] = {}

    # Map inventory code -> marker substring in PASSWORDS.txt
    markers = {
        "brain": "BRAINnode",
        "us": "USnode",
        "ru": "RUnode",
        "ru_spb": "RUnodeSPB",
        "pl": "PLnode",
        "it": "ITnode",
        "nl": "NLnode",
        "free": "Free Node",
        "mini": "RU SBER",
        "rf1": "RFRESERVE1",
    }

    for code, marker in markers.items():
        try:
            idx = next(i for i, ln in enumerate(lines) if marker in ln)
        except StopIteration:
            continue
        pw = ""
        for j in range(idx + 1, min(idx + 12, len(lines))):
            ln = lines[j]
            if not ln:
                continue
            if re.fullmatch(r"(\d{1,3}\.){3}\d{1,3}", ln):
                continue
            if ln.startswith("ssh-ed25519 "):
                continue
            pw = ln
            break
        if pw:
            out[code] = pw
    return out


def _passwords_for(code: str, *, env_prefix: str, file_candidates: dict[str, list[str]]) -> list[str]:
    # Highest priority: per-node env var
    v = os.getenv(f"{env_prefix}{code.upper()}", "").strip()
    if v:
        return [v]
    # Fallback: file map
    return [v for v in file_candidates.get(code, []) if v.strip()]


def _ssh_connect(ip: str, *, user: str, port: int, password: str) -> paramiko.SSHClient:
    cli = paramiko.SSHClient()
    configure_ssh_host_key_policy(cli)
    cli.connect(ip, port=port, username=user, password=password, timeout=30, banner_timeout=30, auth_timeout=30)
    t = cli.get_transport()
    if t:
        t.set_keepalive(30)
    return cli


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 900) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return exit_code, out, err


def _run_bash_script(ssh: paramiko.SSHClient, script: str, *, timeout: int) -> tuple[int, str, str]:
    """
    Execute a bash script without the caller needing to escape '$', quotes, etc.
    """
    stdin, stdout, stderr = ssh.exec_command("bash -s", timeout=timeout)
    stdin.write(script)
    stdin.channel.shutdown_write()
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return exit_code, out, err


def _detect_panel_port(ssh: paramiko.SSHClient) -> int | None:
    # Try to find a listening port owned by x-ui.
    # We avoid parsing locale-specific output; `ss` is consistent enough.
    code, out, err = _run(ssh, "ss -tlnp 2>/dev/null | grep -i x-ui || true", timeout=30)
    for line in out.splitlines():
        # Example: LISTEN 0 4096 0.0.0.0:2053 ... users:(("x-ui",pid=...,fd=...))
        # Keep regex intentionally simple and robust.
        if "x-ui" not in line.lower():
            continue
        m = re.search(r":(\d{2,5})\b", line)
        if m:
            port = int(m.group(1))
            if 1 <= port <= 65535:
                return port
    return None


def _install_3x_ui_noninteractive(ssh: paramiko.SSHClient) -> None:
    """
    Install 3x-ui without running the upstream interactive installer.
    We download the latest release tarball + service file, then start x-ui.
    """
    install = r"""
set -euo pipefail

arch() {
  case "$(uname -m)" in
    x86_64|x64|amd64) echo 'amd64' ;;
    aarch64|arm64) echo 'arm64' ;;
    *) echo 'unsupported' ;;
  esac
}

a="$(arch)"
if [ "$a" = "unsupported" ]; then
  echo "Unsupported arch: $(uname -m)" >&2
  exit 2
fi

tag="$(curl -4 -Ls "https://api.github.com/repos/MHSanaei/3x-ui/releases/latest" | grep '"tag_name":' | head -n 1 | sed -E 's/.*"([^"]+)".*/\1/')"
if [ -z "$tag" ]; then
  echo "Failed to fetch latest tag_name from GitHub API" >&2
  exit 3
fi

url="https://github.com/MHSanaei/3x-ui/releases/download/${tag}/x-ui-linux-${a}.tar.gz"
rm -f /tmp/x-ui-linux.tar.gz
curl -4fL -o /tmp/x-ui-linux.tar.gz "$url"

cd /usr/local
rm -rf x-ui
tar -xzf /tmp/x-ui-linux.tar.gz
rm -f /tmp/x-ui-linux.tar.gz

chmod +x /usr/local/x-ui/x-ui
chmod +x /usr/local/x-ui/x-ui.sh || true

curl -4fL -o /usr/bin/x-ui https://raw.githubusercontent.com/MHSanaei/3x-ui/main/x-ui.sh
chmod +x /usr/bin/x-ui

curl -4fL -o /etc/systemd/system/x-ui.service https://raw.githubusercontent.com/MHSanaei/3x-ui/main/x-ui.service.debian
chmod 644 /etc/systemd/system/x-ui.service
systemctl daemon-reload
systemctl enable x-ui
systemctl restart x-ui
"""
    code, out, err = _run_bash_script(ssh, install, timeout=1800)
    if code != 0:
        raise RuntimeError(f"3x-ui install failed (exit={code}): {err or out}")


def _configure_panel_access(ssh: paramiko.SSHClient) -> dict[str, object]:
    """
    Configure panel settings with randomized credentials and webBasePath.
    Returns a dict with: panel_user, panel_pass, panel_port, panel_path.
    """
    cfg = r"""
set -euo pipefail

rand() {
  python3 - "$1" <<'PY'
import secrets
import string
import sys

n = int(sys.argv[1])
alphabet = string.ascii_lowercase + string.digits
print("".join(secrets.choice(alphabet) for _ in range(n)))
PY
}

port="$(shuf -i 20000-62000 -n 1)"
web="$(rand 18)"
user="$(rand 10)"
pass="$(rand 18)"

/usr/local/x-ui/x-ui setting -username "$user" -password "$pass" -port "$port" -webBasePath "$web" >/dev/null
systemctl restart x-ui >/dev/null 2>&1 || true

echo "panel_user=$user"
echo "panel_pass=$pass"
echo "panel_port=$port"
echo "panel_path=$web"
"""
    code, out, err = _run_bash_script(ssh, cfg, timeout=120)
    if code != 0:
        raise RuntimeError(f"panel config failed (exit={code}): {err or out}")

    result: dict[str, object] = {}
    for line in out.splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k == "panel_port":
            try:
                result[k] = int(v)
            except Exception:
                continue
        else:
            result[k] = v
    return result


def _read_panel_access(ssh: paramiko.SSHClient) -> dict[str, object] | None:
    """
    Best-effort: read current panel settings from x-ui.
    Returns dict with panel_port, panel_path, and has_default_credential (bool) if possible.
    """
    code, out, err = _run(ssh, "/usr/local/x-ui/x-ui setting -show true 2>/dev/null || true", timeout=30)
    if not out.strip():
        return None
    # Example lines:
    # port: 2053
    # webBasePath: /abcdef
    # hasDefaultCredential: false
    res: dict[str, object] = {}
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("port:"):
            v = line.split(":", 1)[1].strip()
            try:
                res["panel_port"] = int(v)
            except Exception:
                pass
        if line.startswith("webBasePath:"):
            v = line.split(":", 1)[1].strip()
            res["panel_path"] = v.lstrip("/").strip()
        if line.startswith("hasDefaultCredential:"):
            v = line.split(":", 1)[1].strip().lower()
            res["has_default_credential"] = v in {"1", "true", "yes", "y"}
    return res


def _ensure_authorized_key(ssh: paramiko.SSHClient, pubkey: str) -> None:
    pubkey = pubkey.strip()
    if not pubkey.startswith(("ssh-ed25519 ", "ssh-rsa ", "ecdsa-sha2-nistp256 ", "ecdsa-sha2-nistp384 ", "ecdsa-sha2-nistp521 ")):
        return
    # Idempotent append.
    cmd = (
        "set -euo pipefail; "
        "mkdir -p /root/.ssh; chmod 700 /root/.ssh; "
        "touch /root/.ssh/authorized_keys; chmod 600 /root/.ssh/authorized_keys; "
        f"grep -Fqx {json.dumps(pubkey)} /root/.ssh/authorized_keys || echo {json.dumps(pubkey)} >> /root/.ssh/authorized_keys"
    )
    _run(ssh, cmd, timeout=30)


def bootstrap_node(
    node: Node,
    *,
    ssh_user: str,
    ssh_port: int,
    ssh_password: str,
    control_plane_ip: str,
    set_pubkey: str | None,
    dry_run: bool,
) -> dict:
    facts: dict[str, object] = {"code": node.code, "ip": node.ip, "role": node.role, "ok": False}

    ssh = _ssh_connect(node.ip, user=ssh_user, port=ssh_port, password=ssh_password)
    try:
        code, out, err = _run(ssh, "whoami && uname -a && (lsb_release -a 2>/dev/null || true)", timeout=30)
        facts["sys"] = (out + "\n" + err).strip()

        if set_pubkey:
            if not dry_run:
                _ensure_authorized_key(ssh, set_pubkey)
            facts["pubkey_added"] = True

        # Install base packages
        if not dry_run:
            _run(ssh, "DEBIAN_FRONTEND=noninteractive apt-get update -y", timeout=900)
            _run(
                ssh,
                "DEBIAN_FRONTEND=noninteractive apt-get install -y curl ca-certificates ufw fail2ban sqlite3",
                timeout=900,
            )

        # Install 3x-ui (if missing). Avoid interactive upstream installer.
        code, out, err = _run(ssh, "command -v x-ui >/dev/null 2>&1; echo $?", timeout=30)
        has_xui = out.strip().endswith("0")
        facts["xui_present"] = bool(has_xui)
        if not has_xui and not dry_run:
            _install_3x_ui_noninteractive(ssh)
            facts["xui_installed"] = True

        # Ensure service is running (best-effort).
        if not dry_run:
            _run(ssh, "systemctl enable x-ui >/dev/null 2>&1 || true", timeout=60)
            _run(ssh, "systemctl restart x-ui >/dev/null 2>&1 || true", timeout=60)

        # Configure panel credentials/path/port only if still default/unset.
        if not dry_run:
            try:
                existing = _read_panel_access(ssh) or {}
                facts.update({k: v for k, v in existing.items() if k in {"panel_port", "panel_path"}})
                needs_config = bool(existing.get("has_default_credential")) or not existing.get("panel_path")
                if needs_config:
                    panel_cfg = _configure_panel_access(ssh)
                    facts.update(panel_cfg)
            except Exception as e:
                facts["panel_config_error"] = str(e)

        panel_port = _detect_panel_port(ssh)
        facts["panel_port_detected"] = panel_port

        # Firewall (safe order: allow ssh first)
        if not dry_run:
            _run(ssh, f"ufw allow {ssh_port}/tcp || true", timeout=30)
            _run(ssh, "ufw allow 443/tcp || true", timeout=30)
            _run(
                ssh,
                (
                    "cat > /etc/fail2ban/jail.d/pokrov-sshd.conf <<'EOF'\n"
                    "[sshd]\n"
                    "enabled = true\n"
                    f"port = {int(ssh_port)}\n"
                    "filter = sshd\n"
                    "logpath = /var/log/auth.log\n"
                    "maxretry = 3\n"
                    "findtime = 10m\n"
                    "bantime = 1h\n"
                    "bantime.increment = true\n"
                    "bantime.factor = 2\n"
                    "bantime.maxtime = 24h\n"
                    "EOF\n"
                    "systemctl enable fail2ban >/dev/null 2>&1 || true\n"
                    "systemctl restart fail2ban >/dev/null 2>&1 || true"
                ),
                timeout=60,
            )
            allow_panel_port = facts.get("panel_port") if isinstance(facts.get("panel_port"), int) else panel_port
            if allow_panel_port and node.code != "brain":
                _run(
                    ssh,
                    f"ufw allow from {control_plane_ip} to any port {int(allow_panel_port)} proto tcp || true",
                    timeout=30,
                )
            _run(ssh, "ufw --force enable", timeout=60)

        facts["ok"] = True
        return facts
    finally:
        ssh.close()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    p.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    p.add_argument("--ssh-user", default="root")
    p.add_argument("--ssh-port", type=int, default=22)
    p.add_argument("--control-plane-ip", default="82.21.114.104", help="brain node public IP used for panel allowlist")
    p.add_argument(
        "--env-prefix",
        default="NODE_PASS_",
        help="env var prefix for per-node passwords, e.g. NODE_PASS_BRAIN, NODE_PASS_US, ...",
    )
    p.add_argument("--only", default="", help="comma-separated node codes to run (e.g. brain,pl,it,us)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--add-pubkeys", action="store_true", help="append local SSH public keys into /root/.ssh/authorized_keys")
    args = p.parse_args()

    nodes = _parse_inventory(Path(args.inventory))

    only = {c.strip() for c in args.only.split(",") if c.strip()}
    if only:
        nodes = [n for n in nodes if n.code in only]

    pw_file_candidates: dict[str, list[str]] = {}
    pw_path = Path(args.passwords)
    if pw_path.exists():
        requested_codes = [n.code for n in nodes]
        pw_file_candidates = parse_password_candidates(pw_path, requested_codes=requested_codes)
        legacy_map = _parse_passwords(pw_path)
        for code, password in legacy_map.items():
            if not password:
                continue
            candidates = pw_file_candidates.setdefault(code, [])
            if password not in candidates:
                candidates.append(password)

    pubkeys: dict[str, str] = {}
    if args.add_pubkeys:
        # Optional: set up key-based login for later. We do NOT rely on keys here.
        key_dir = REPO_ROOT / "VPN NODE SSH KEYS"
        for code, fname in {
            "brain": "BRAINnode_public",
            "us": "USnode_public",
            "pl": "PLnode_public",
            "it": "ITnode_public",
            "nl": "NLnode_public",
            "free": "FREEnode_public",
            "mini": "Russia_public",
        }.items():
            pth = key_dir / fname
            if pth.exists():
                pubkeys[code] = pth.read_text(encoding="utf-8", errors="replace").strip()

    results: list[dict] = []
    for n in nodes:
        passwords = _passwords_for(n.code, env_prefix=args.env_prefix, file_candidates=pw_file_candidates)
        if not passwords:
            raise SystemExit(f"Missing password for node {n.code}. Provide {args.env_prefix}{n.code.upper()} or fill PASSWORDS.txt.")

        print(f"[{n.code}] connecting to {n.ip} ...")
        last_error = ""
        for idx, pw in enumerate(passwords, 1):
            try:
                facts = bootstrap_node(
                    n,
                    ssh_user=args.ssh_user,
                    ssh_port=args.ssh_port,
                    ssh_password=pw,
                    control_plane_ip=args.control_plane_ip,
                    set_pubkey=pubkeys.get(n.code),
                    dry_run=bool(args.dry_run),
                )
                break
            except paramiko.AuthenticationException as e:
                last_error = f"password candidate {idx} failed: {e}"
                continue
        else:
            raise SystemExit(f"[{n.code}] SSH authentication failed after {len(passwords)} password candidate(s): {last_error}")
        results.append(facts)
        print(f"[{n.code}] ok={facts.get('ok')} panel_port={facts.get('panel_port')}")
        time.sleep(0.2)

    out_path = REPO_ROOT / f"node_facts-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out_path.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")
    print(f"Saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
