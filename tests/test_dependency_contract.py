from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / "scripts" / "check_dependency_contract.py"
    spec = importlib.util.spec_from_file_location("check_dependency_contract", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = _load_module()


def test_repository_dependency_contract_is_closed() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    assert MODULE.validate_repository(repo_root) == []


def test_npm_exact_version_classifier_rejects_ranges() -> None:
    assert MODULE.EXACT_NPM_VERSION.fullmatch("16.2.10")
    assert not MODULE.EXACT_NPM_VERSION.fullmatch("^16.2.10")
    assert not MODULE.EXACT_NPM_VERSION.fullmatch("~16.2.10")


def test_requirements_lock_reports_unpinned_packages(tmp_path: Path) -> None:
    lock = tmp_path / "requirements.txt"
    lock.write_text("good==1.0.0\nloose>=2.0\nhttpx2==2.10.0\n", encoding="utf-8")

    problems = MODULE._requirements_lock_problems(lock)

    assert any("not pinned" in problem for problem in problems)
    assert not any("httpx2" in problem for problem in problems)
