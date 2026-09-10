"""Read-only support runtime identity; never emit credentials or customer data."""
import hashlib
import json
import subprocess
from pathlib import Path

manifest = json.loads(Path(__file__).with_name("manifest.json").read_text())
result = {"candidate": manifest["candidate"], "origin": "brain-origin", "services": {}, "files_match": True}
expected = {"SUPPORT_AI_MODEL": "deepseek/deepseek-v4.1-flash", "SUPPORT_AI_REASONING_EFFORT": "high",
            "SUPPORT_AI_ENABLED": "true", "SUPPORT_AI_AGENT_ENABLED": "true"}
for unit in ("portal-api", "portal-helpbot"):
    raw = subprocess.check_output(["systemctl", "show", unit, "--property=ActiveState,NRestarts,MainPID"], text=True)
    state = dict(line.split("=", 1) for line in raw.splitlines())
    env = dict(entry.split(b"=", 1) for entry in Path("/proc", state["MainPID"], "environ").read_bytes().split(b"\0") if b"=" in entry)
    state["support"] = {key: env.get(key.encode(), b"").decode() for key in expected}
    assert state["support"] == expected and state["ActiveState"] == "active" and state["NRestarts"] == "0"
    result["services"][unit] = state
for name, values in manifest["files"].items():
    raw = (Path("/root") / name).read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(raw).hexdigest() == values["after"], name
result["status"] = "PASS"
print(json.dumps(result, indent=2))
