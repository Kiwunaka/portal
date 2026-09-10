"""Read only runtime identities, public configuration and scoped source hashes."""
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

here = Path(__file__).resolve().parent
manifest = json.loads((here / "manifest.json").read_text())
root = Path("/root/portal_bot")
files_match = all(hashlib.sha256((root / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() == row["after"]
                  for name, row in manifest["files"].items())
assert files_match
services = {}
for unit in ("portal-api", "portal-helpbot"):
    raw = subprocess.check_output(["systemctl", "show", unit, "--property=ActiveState,NRestarts,MainPID"], text=True)
    state = dict(line.split("=", 1) for line in raw.splitlines())
    assert state["ActiveState"] == "active" and state["NRestarts"] == "0"
    env = {}
    for entry in Path("/proc/" + state["MainPID"] + "/environ").read_bytes().split(b"\0"):
        if b"=" in entry:
            key, value = entry.split(b"=", 1)
            if key.decode() in {"SUPPORT_AI_MODEL", "SUPPORT_AI_REASONING_EFFORT", "SUPPORT_AI_AGENT_ENABLED", "SUPPORT_PI_NODE"}:
                env[key.decode()] = value.decode()
    assert env["SUPPORT_AI_MODEL"] == "deepseek/deepseek-v4.1-flash"
    assert env["SUPPORT_AI_REASONING_EFFORT"] == "high"
    assert env["SUPPORT_AI_AGENT_ENABLED"] == "true"
    assert env["SUPPORT_PI_NODE"] == "/opt/pokrov-support-node/bin/node"
    services[unit] = {**state, "support": env}
node = subprocess.check_output(["/opt/pokrov-support-node/bin/node", "--version"], text=True).strip()
assert node == "v24.15.0"
lock = hashlib.sha256((root / "support_pi/package-lock.json").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
assert (root / "support_pi/installed-lock.sha256").read_text().strip() == lock
packages = {}
for package in ("pi-agent-core", "pi-ai"):
    packages[package] = json.loads((root / "support_pi/node_modules/@earendil-works" / package / "package.json").read_text())["version"]
assert set(packages.values()) == {"0.85.1"}
with urllib.request.urlopen("https://api.pokrov.space/api/health", timeout=15) as response:
    assert response.status == 200
print(json.dumps({"candidate": manifest["candidate"], "origin": "brain-origin", "status": "PASS",
                  "files_match": files_match, "services": services, "node": node, "packages": packages,
                  "lock_sha256": lock, "public_health": "PASS"}, indent=2))
