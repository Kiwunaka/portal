"""Exact-file support pi cutover; run on owned Brain after source acceptance."""
import argparse
import hashlib
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ["api.py", "helpbot.py", "support_agent_harness.py", "support_agent_service.py",
         "support_case_context.py", "support_case_tools.py", "support_pi_bridge.py",
         "support_work_service.py", "tickets_repo.py", "support_pi/runner.mjs",
         "support_pi/package.json", "support_pi/package-lock.json"]
ROOT = Path("/root/portal_bot")
UNITS = ["portal-api", "portal-helpbot"]


def digest(raw):
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def health():
    state = {}
    for unit in UNITS:
        raw = subprocess.check_output(["systemctl", "show", unit, "--property=ActiveState,NRestarts,MainPID"], text=True)
        state[unit] = dict(line.split("=", 1) for line in raw.splitlines())
        assert state[unit]["ActiveState"] == "active" and state[unit]["NRestarts"] == "0"
    with urllib.request.urlopen("https://api.pokrov.space/api/health", timeout=15) as response:
        assert response.status == 200
    return state


def restart():
    subprocess.run(["systemctl", "reset-failed", *UNITS], check=True)
    subprocess.run(["systemctl", "restart", *UNITS], check=True)
    time.sleep(12)
    return health()


def install(path, raw, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".pi-new")
    with temporary.open("xb") as target:
        target.write(raw)
        target.flush()
        os.fsync(target.fileno())
    temporary.chmod(mode)
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((HERE / "manifest.json").read_text())
    prereqs = json.loads((HERE / "prerequisites.json").read_text())
    assert args.candidate == manifest["candidate"] and set(manifest["files"]) == set(FILES)
    changes = {}
    for name in FILES:
        path = ROOT / name
        before = path.read_bytes() if path.exists() else None
        after = (HERE / "portal_bot" / name).read_bytes()
        assert (digest(before) if before is not None else None) == manifest["files"][name]["before"], "live drift: " + name
        assert digest(after) == manifest["files"][name]["after"], "candidate drift: " + name
        if name.endswith(".py"):
            compile(after, name, "exec")
        elif name.endswith(".json"):
            json.loads(after)
        changes[path] = (before, after, path.stat().st_mode & 0o777 if before is not None else 0o644)
    env_path = ROOT / "support-case.env"
    env_before = env_path.read_bytes()
    assert digest(env_before) == manifest["environment_before_sha256"]
    assert b"SUPPORT_AI_MODEL=deepseek/deepseek-v4.1-flash" in env_before
    assert b"SUPPORT_AI_REASONING_EFFORT=high" in env_before
    assert b"SUPPORT_PI_NODE=" not in env_before
    env_after = env_before.rstrip() + b"\nSUPPORT_PI_NODE=/opt/pokrov-support-node/bin/node\n"
    changes[env_path] = (env_before, env_after, env_path.stat().st_mode & 0o777)
    marker = ROOT / "support_pi/installed-lock.sha256"
    assert not marker.exists()
    changes[marker] = (None, (prereqs["lock_sha256"] + "\n").encode(), 0o644)
    node_target = Path(prereqs["node_path"])
    deps_target = Path(prereqs["dependencies_path"])
    assert node_target == Path("/opt/pokrov-node-v24.15.0")
    assert deps_target == Path("/opt/pokrov-support-pi") / prereqs["lock_sha256"]
    assert digest((deps_target / "package-lock.json").read_bytes()) == prereqs["lock_sha256"]
    assert digest(changes[ROOT / "support_pi/package-lock.json"][1]) == prereqs["lock_sha256"]
    assert subprocess.check_output([str(node_target / "bin/node"), "--version"], text=True).strip() == "v24.15.0"
    subprocess.run([str(node_target / "bin/node"), "--check", str(HERE / "portal_bot/support_pi/runner.mjs")], check=True)
    for package in ("pi-agent-core", "pi-ai"):
        info = json.loads((deps_target / "node_modules/@earendil-works" / package / "package.json").read_text())
        assert info["version"] == "0.85.1"
    links = {Path("/opt/pokrov-support-node"): node_target,
             ROOT / "support_pi/node_modules": deps_target / "node_modules"}
    assert all(not p.exists() and not p.is_symlink() for p in links)
    receipt = {"candidate": args.candidate, "status": "PLAN_PASS", "origin": "brain-origin",
               "services_before": health(), "files": FILES, "node": "v24.15.0", "pi": "0.85.1",
               "lock_sha256": prereqs["lock_sha256"], "database_mutated": False}
    if not args.apply:
        print(json.dumps(receipt)); return
    backup = Path("/root/portal_bot.deploy-backups") / ("manual-support-pi-" + args.candidate[:12])
    backup.mkdir(mode=0o700)
    for path, (before, _, mode) in changes.items():
        if before is not None:
            saved = backup / path.relative_to("/root")
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_bytes(before)
            saved.chmod(mode)
    (backup / "new-files.json").write_text(json.dumps([str(p) for p, (before, _, _) in changes.items() if before is None]))
    try:
        for path, (before, after, mode) in changes.items():
            assert (path.read_bytes() if path.exists() else None) == before, "concurrent change"
            install(path, after, mode)
        for link, target in links.items():
            link.symlink_to(target, target_is_directory=True)
        receipt["services_after"] = restart()
        assert all(path.read_bytes() == after for path, (_, after, _) in changes.items())
        receipt.update(status="PASS", backup=str(backup), health="PASS")
    except Exception:
        for link, target in links.items():
            if link.is_symlink() and link.readlink() == target:
                link.unlink()
        for path, (before, after, mode) in changes.items():
            current = path.read_bytes() if path.exists() else None
            if current == after:
                if before is None:
                    path.unlink()
                else:
                    install(path, before, mode)
            else:
                assert current == before, "rollback blocked by concurrent change"
        receipt.update(status="ROLLED_BACK", backup=str(backup), services_after=restart())
        (backup / "receipt.json").write_text(json.dumps(receipt, indent=2))
        print(json.dumps(receipt)); raise SystemExit(1)
    (backup / "receipt.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
