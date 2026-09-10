"""One-shot, digest-guarded support-only deployment on owned Brain."""
import argparse
import hashlib
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ["portal_bot/helpbot.py", "portal_bot/support_ai_service.py",
         "portal_bot/support_agent_service.py", "portal_bot/support_agent_provider.py",
         "portal_bot/support_agent_harness.py", "portal_bot/support_agent_policy.py",
         "portal_bot/support_case_context.py", "shared/support-agent-policy.json"]
ENV = Path("/root/portal_bot/support-case.env")
UNITS = ["portal-api", "portal-helpbot"]
def digest(raw):
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
def units():
    result = {}
    for unit in UNITS:
        raw = subprocess.check_output(["systemctl", "show", unit, "--property=ActiveState,NRestarts,MainPID"], text=True)
        result[unit] = dict(line.split("=", 1) for line in raw.splitlines())
    return result
def verify():
    state = units()
    assert all(x["ActiveState"] == "active" and x["NRestarts"] == "0" for x in state.values())
    with urllib.request.urlopen("https://api.pokrov.space/api/health", timeout=15) as response:
        assert response.status == 200
    return state
def restart():
    subprocess.run(["systemctl", "reset-failed", *UNITS], check=True)
    subprocess.run(["systemctl", "restart", *UNITS], check=True)
    time.sleep(12)
    return verify()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    manifest = json.loads((HERE / "manifest.json").read_text())
    assert args.candidate == manifest["candidate"]
    assert set(manifest["files"]) == set(FILES)
    changes = {}
    for name in FILES:
        target = Path("/root") / name
        staged = HERE / name
        before, after = target.read_bytes(), staged.read_bytes()
        assert digest(before) == manifest["files"][name]["before"], "live drift: " + name
        assert digest(after) == manifest["files"][name]["after"], "stage drift: " + name
        if name.endswith(".py"):
            compile(after, name, "exec")
        else:
            json.loads(after)
        changes[target] = (before, after, target.stat().st_mode & 0o777)
    env_before = ENV.read_bytes()
    env_text = env_before.decode()
    assert "SUPPORT_AI_MODEL=deepseek/deepseek-v4-flash-vision-exp" in env_text
    assert "SUPPORT_AI_REASONING_EFFORT=medium" in env_text
    env_after = env_text.replace("SUPPORT_AI_MODEL=deepseek/deepseek-v4-flash-vision-exp", "SUPPORT_AI_MODEL=deepseek/deepseek-v4.1-flash").replace("SUPPORT_AI_REASONING_EFFORT=medium", "SUPPORT_AI_REASONING_EFFORT=high").encode()
    changes[ENV] = (env_before, env_after, ENV.stat().st_mode & 0o777)
    preflight = verify()
    receipt = dict(candidate=args.candidate, status="PLAN_PASS", units_before=preflight, changed_files=FILES,
                   common_environment_changed=False, database_mutated=False)
    if not args.apply:
        print(json.dumps(receipt)); return
    backup = Path("/root/portal_bot.deploy-backups") / ("manual-support-ds41-" + args.candidate[:12])
    backup.mkdir(mode=0o700)
    for target, (before, after, mode) in changes.items():
        saved = backup / target.relative_to("/root")
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes(before)
        saved.chmod(mode)
    def install(target, content, mode):
        temporary = target.with_name(target.name + ".ds41-new")
        with temporary.open("xb") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        temporary.chmod(mode)
        os.replace(temporary, target)
    try:
        for target, (before, after, mode) in changes.items():
            assert target.read_bytes() == before, "concurrent change: " + str(target)
            install(target, after, mode)
        receipt["units_after"] = restart()
        assert all(target.read_bytes() == after for target, (_, after, _) in changes.items())
        receipt.update(status="PASS", backup=str(backup), health="PASS")
    except Exception:
        for target, (before, after, mode) in changes.items():
            current = target.read_bytes()
            if current == after:
                install(target, before, mode)
            else:
                assert current == before, "rollback blocked by concurrent change"
        receipt.update(status="ROLLED_BACK", units_after=restart(), backup=str(backup))
        (backup / "receipt.json").write_text(json.dumps(receipt, indent=2))
        print(json.dumps(receipt))
        raise SystemExit(1)
    (backup / "receipt.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt))
if __name__ == "__main__":
    main()
