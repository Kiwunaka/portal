from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_script():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "cleanup_antiabuse_retention.py"
    spec = importlib.util.spec_from_file_location("cleanup_antiabuse_retention", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_cleanup_script_is_dry_run_without_apply(monkeypatch, capsys) -> None:
    module = _load_script()
    monkeypatch.setattr(module, "read_retention_backlog", lambda *_args, **_kwargs: {"antiabuse_raw_ip": 4})
    monkeypatch.setattr(
        module,
        "drain_antiabuse_retention",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("dry-run must not mutate")),
    )

    assert module.main([]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "DRY_RUN"
    assert payload["before"]["antiabuse_raw_ip"] == 4
    assert payload["after"] == payload["before"]


def test_cleanup_script_applies_explicit_drain_without_exposing_database_url(monkeypatch, capsys) -> None:
    module = _load_script()
    monkeypatch.setenv("DATABASE_URL", "postgresql://operator:super-secret@db/portal")
    monkeypatch.setattr(module, "read_retention_backlog", lambda *_args, **_kwargs: {"antiabuse_raw_ip": 0})
    monkeypatch.setattr(
        module,
        "drain_antiabuse_retention",
        lambda *_args, **_kwargs: {
            "status": "drained",
            "changed_batches": 2,
            "cleared": {"antiabuse_raw_ip": 4},
            "remaining": {"antiabuse_raw_ip": 0},
        },
    )

    assert module.main(["--apply", "--batch-limit", "200"]) == 0
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["status"] == "APPLIED"
    assert payload["batch_limit"] == 200
    assert payload["drain"]["cleared"]["antiabuse_raw_ip"] == 4
    assert "super-secret" not in output
    assert "postgresql://" not in output
