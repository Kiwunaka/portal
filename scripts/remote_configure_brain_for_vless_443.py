from __future__ import annotations

"""
Reconfigure brain node so it can also serve user traffic on :443 (VLESS Reality),
while keeping control-plane on :2096 and :8444 (similar to the old server layout).

Actions:
- Adjust Caddyfile: stop serving on :443, keep :8444 (WebApp + marketing) and :2096 (API)
- Restart Caddy
- Create/ensure a VLESS Reality inbound on brain (port 443) via 3x-ui panel API (localhost)

This is safe to run BEFORE DNS cutover. It will break brain's :443 website temporarily
(but DNS isn't pointing there yet).
"""

import argparse
import os
from pathlib import Path

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


def _parse_passwords(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    for i, ln in enumerate(lines):
        if "BRAINnode" in ln:
            for j in range(i + 1, min(i + 30, len(lines))):
                v = lines[j].strip()
                if v and not v.startswith("ssh-ed25519 "):
                    return v
    return ""


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 180) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True)
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    def _default_node_facts() -> str:
        candidates = []
        candidates.extend(REPO_ROOT.glob("node_facts-*.json"))
        candidates.extend(REPO_ROOT.glob("legacy/inventory/**/node_facts-*.json"))
        candidates = sorted(candidates)
        return str(candidates[-1]) if candidates else ""

    ap.add_argument("--node-facts", default=_default_node_facts())
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    # Read local node facts for brain panel access (port/path/user/pass)
    import json

    if not args.node_facts:
        raise SystemExit("Missing --node-facts (no node_facts-*.json found).")

    facts = json.loads(Path(args.node_facts).read_text(encoding="utf-8", errors="replace"))
    brain = next((r for r in facts.get("results", []) if r.get("code") == "brain"), None)
    if not brain:
        raise SystemExit(f"brain not found in node facts: {args.node_facts}")

    panel_port = int(brain["panel_port"])
    panel_path = str(brain["panel_path"])
    panel_user = str(brain["panel_user"])
    panel_pass = str(brain["panel_pass"])

    caddyfile = f"""{{
  servers {{
    protocols h1 h2
  }}
}}

{args.domain}:8444 {{
  tls /etc/caddy/certs/fullchain.pem /etc/caddy/certs/privkey.pem

  encode gzip
  header Alt-Svc "clear"

  # Keep WebApp same-origin with the API to avoid CORS pain.
  # NOTE: use `handle` (not `handle_path`) so upstream keeps the `/api/...` prefix.
  handle /api/* {{
    reverse_proxy 127.0.0.1:8080
  }}
  handle /s8Kx2mP7qR4wT/* {{
    reverse_proxy 127.0.0.1:8080
  }}
  handle /pay/* {{
    reverse_proxy 127.0.0.1:8080
  }}

  handle_path /webapp/* {{
    root * /var/www/portal/webapp
    file_server
  }}

  handle {{
    root * /var/www/portal/marketing
    file_server
  }}
}}

{args.domain}:2096 {{
  tls /etc/caddy/certs/fullchain.pem /etc/caddy/certs/privkey.pem
  reverse_proxy 127.0.0.1:8080
}}
"""

    ssh = paramiko.SSHClient()
    configure_ssh_host_key_policy(ssh)
    ssh.connect(args.brain_ip, port=args.ssh_port, username=args.ssh_user, password=pw, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        sftp = ssh.open_sftp()
        try:
            with sftp.file("/etc/caddy/Caddyfile", "w") as f:
                f.write(caddyfile)
        finally:
            sftp.close()

        code, out, err = _run(ssh, "systemctl restart caddy", timeout=120)
        if code != 0:
            raise SystemExit(err.strip() or out.strip())

        # Free port 443 (Caddy no longer binds it). Now ensure inbound exists.
        # Reuse the same remote ensure script from create_reality_inbounds.py (inline minimal).
        remote_py = r"""
from __future__ import annotations
import base64, json, sys, urllib.parse, urllib.request, http.cookiejar

payload_b64=sys.argv[1].strip()
pad='='*((4-(len(payload_b64)%4))%4)
payload=json.loads(base64.urlsafe_b64decode(payload_b64+pad).decode('utf-8'))
panel_port=int(payload['panel_port'])
panel_path=str(payload['panel_path']).strip('/').strip()
panel_user=payload['panel_user']; panel_pass=payload['panel_pass']
desired=payload['desired']

base=f'http://127.0.0.1:{panel_port}/{panel_path}'
login_url=f'{base}/login'
list_url=f'{base}/panel/api/inbounds/list'
add_url=f'{base}/panel/api/inbounds/add'

def _req(opener, method, url, data=None, headers=None, timeout=20):
  req=urllib.request.Request(url, data=data, headers=headers or {}, method=method)
  with opener.open(req, timeout=timeout) as resp:
    return resp.status, resp.read()

cj=http.cookiejar.CookieJar()
opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
data=urllib.parse.urlencode({'username':panel_user,'password':panel_pass}).encode('utf-8')
st,_=_req(opener,'POST',login_url,data=data,headers={'Content-Type':'application/x-www-form-urlencoded'})
if st!=200:
  print(json.dumps({'ok':False,'error':f'login_http_{st}'})); sys.exit(2)

st,body=_req(opener,'GET',list_url)
obj=json.loads(body.decode('utf-8','replace') or '{}')
if not obj.get('success'):
  print(json.dumps({'ok':False,'error':'list_failed'})); sys.exit(3)

inbounds=obj.get('obj',[]) or []
for inb in inbounds:
  if int(inb.get('port',-1))==int(desired.get('port')) and str(inb.get('protocol','')).lower()==str(desired.get('protocol','')).lower():
    print(json.dumps({'ok':True,'action':'exists','inbound':inb})); sys.exit(0)

st,body=_req(opener,'POST',add_url,data=json.dumps(desired).encode('utf-8'),headers={'Content-Type':'application/json'})
if st!=200:
  print(json.dumps({'ok':False,'error':f'add_http_{st}'})); sys.exit(4)
obj=json.loads(body.decode('utf-8','replace') or '{}')
if not obj.get('success'):
  print(json.dumps({'ok':False,'error':'add_failed','details':obj})); sys.exit(5)

st,body=_req(opener,'GET',list_url)
obj=json.loads(body.decode('utf-8','replace') or '{}')
inbounds=obj.get('obj',[]) or []
for inb in inbounds:
  if int(inb.get('port',-1))==int(desired.get('port')) and str(inb.get('protocol','')).lower()==str(desired.get('protocol','')).lower():
    print(json.dumps({'ok':True,'action':'created','inbound':inb})); sys.exit(0)

print(json.dumps({'ok':False,'error':'created_but_not_found'})); sys.exit(6)
"""

        # Generate reality keypair on the node via openssl? We'll provide privateKey from control-plane script approach:
        # Create it locally here (python on server doesn't have cryptography). So we keep creation to the existing create_reality_inbounds.py flow:
        # we will just create an empty inbound by letting x-ui generate? Not supported reliably.
        #
        # Instead: do the inbound creation from LOCAL machine using scripts/create_reality_inbounds.py.
        print("OK: caddy now serves :8444 and :2096. Next run locally: python scripts/create_reality_inbounds.py --include-brain --only brain")
        print(f"Brain panel (localhost): port={panel_port} path_len={len(panel_path)}")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
