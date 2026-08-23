from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


EXACT_NPM_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?$")
PINNED_REQUIREMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*(?:\[[^]]+\])?==")
INSTALL_WORKFLOWS = {
    ".github/workflows/guardrails.yml",
    ".github/workflows/release-orchestrator-manual.yml",
    ".github/workflows/weekly-release-gate-snapshot.yml",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _requirements_lock_problems(path: Path) -> list[str]:
    if not path.exists():
        return [f"{path.as_posix()}: missing compiled dependency lock"]
    problems: list[str] = []
    for number, raw_line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith(("#", "--")) or raw_line[:1].isspace():
            continue
        if not PINNED_REQUIREMENT.match(line):
            problems.append(f"{path.as_posix()}:{number}: dependency is not pinned with ==")
    return problems


def _frontend_problems(repo_root: Path, contract: dict) -> list[str]:
    problems: list[str] = []
    node = contract["node"]
    expected_package_manager = f"npm@{node['npm']}"
    expected_engine = ".".join(node["version"].split(".")[:2]) + ".x"
    shared_versions = contract["shared_frontend_versions"]
    browser = contract["browser_tooling"]

    for frontend in contract["frontends"]:
        manifest_path = repo_root / frontend / "package.json"
        lock_path = repo_root / frontend / "package-lock.json"
        try:
            manifest = _load_json(manifest_path)
            lock = _load_json(lock_path)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            problems.append(f"{frontend}: unreadable npm manifest/lock: {exc}")
            continue

        if manifest.get("packageManager") != expected_package_manager:
            problems.append(f"{frontend}/package.json: packageManager must be {expected_package_manager}")
        if manifest.get("engines", {}).get("node") != expected_engine:
            problems.append(f"{frontend}/package.json: engines.node must be {expected_engine}")
        if lock.get("lockfileVersion") != node["lockfile_version"]:
            problems.append(
                f"{frontend}/package-lock.json: lockfileVersion must be {node['lockfile_version']}"
            )

        root_lock = lock.get("packages", {}).get("", {})
        for group in ("dependencies", "devDependencies"):
            declared = manifest.get(group, {})
            locked_declared = root_lock.get(group, {})
            if declared != locked_declared:
                problems.append(f"{frontend}: package.json {group} differs from package-lock root")
            for package, version in declared.items():
                if not EXACT_NPM_VERSION.fullmatch(str(version)):
                    problems.append(f"{frontend}: {package} must use an exact npm version, got {version}")
                    continue
                resolved = lock.get("packages", {}).get(f"node_modules/{package}", {}).get("version")
                if resolved != version:
                    problems.append(f"{frontend}: {package} resolves to {resolved}, expected {version}")

        declared_all = {**manifest.get("dependencies", {}), **manifest.get("devDependencies", {})}
        for package, version in shared_versions.items():
            if declared_all.get(package) != version:
                problems.append(f"{frontend}: shared {package} must be {version}")
        browser_package = browser["packages"][frontend]
        if declared_all.get(browser_package) != browser["version"]:
            problems.append(
                f"{frontend}: {browser_package} must be browser tooling {browser['version']}"
            )
    return problems


def _workflow_problems(repo_root: Path, contract: dict) -> list[str]:
    problems: list[str] = []
    python_version = contract["python"]["version"]
    pip_version = contract["python"]["pip"]
    node_version = contract["node"]["version"]
    npm_version = contract["node"]["npm"]

    for relative in contract["workflows"]:
        path = repo_root / relative
        if not path.exists():
            problems.append(f"{relative}: workflow missing")
            continue
        text = path.read_text(encoding="utf-8-sig")
        if f'python-version: "{python_version}"' not in text:
            problems.append(f"{relative}: Python must be pinned to {python_version}")
        if "actions/setup-node" in text and f'node-version: "{node_version}"' not in text:
            problems.append(f"{relative}: Node must be pinned to {node_version}")
        if re.search(r"pip install\s+pytest(?:\s+httpx)?", text):
            problems.append(f"{relative}: ad-hoc pytest/httpx install is forbidden")
        if relative in INSTALL_WORKFLOWS:
            required_fragments = (
                f"python -m pip install pip=={pip_version}",
                "python -m pip install --require-hashes -r requirements-test.txt",
                f"npm install --global npm@{npm_version}",
                "python scripts/check_dependency_contract.py",
            )
            for fragment in required_fragments:
                if fragment not in text:
                    problems.append(f"{relative}: missing `{fragment}`")
    return problems


def validate_repository(repo_root: Path) -> list[str]:
    contract_path = repo_root / "shared" / "dependency-contract.json"
    try:
        contract = _load_json(contract_path)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return [f"shared/dependency-contract.json: unreadable: {exc}"]

    problems: list[str] = []
    for relative in (
        "portal_bot/requirements.txt",
        "requirements-test.txt",
        "requirements-ops.txt",
    ):
        problems.extend(_requirements_lock_problems(repo_root / relative))

    test_lock = (repo_root / "requirements-test.txt").read_text(
        encoding="utf-8-sig", errors="replace"
    ).lower()
    for package in ("httpx2", "pytest"):
        if not re.search(rf"(?m)^{package}==", test_lock):
            problems.append(f"requirements-test.txt: missing pinned {package}")

    problems.extend(_frontend_problems(repo_root, contract))
    problems.extend(_workflow_problems(repo_root, contract))
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the pinned Python, Node and frontend dependency contract."
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    problems = validate_repository(args.repo_root.resolve())
    if problems:
        print("DEPENDENCY_CONTRACT: FAIL")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print("DEPENDENCY_CONTRACT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
