from __future__ import annotations

import gzip
import importlib.util
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import performance_budget_gate as GATE


def _load_module():
    module_path = SCRIPTS_ROOT / "collect_web_performance.py"
    spec = importlib.util.spec_from_file_location("collect_web_performance", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = _load_module()
CONTRACT_PATH = (
    REPO_ROOT
    / "shared"
    / "contracts"
    / "performance"
    / "performance-budgets.v1.json"
)


def _write(path: Path, content: bytes | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def test_route_js_collection_deduplicates_referenced_chunks(tmp_path: Path) -> None:
    output = tmp_path / "out"
    script = b"const payload = 'bounded';" * 40
    _write(output / "_next" / "static" / "shared.js", script)
    html = (
        '<script src="/_next/static/shared.js"></script>'
        '<script src="/_next/static/shared.js"></script>'
    )
    _write(output / "index.html", html)
    _write(output / "checkout" / "index.html", html)

    value, files = MODULE._route_js_gzip_bytes(output, ["/", "/checkout"])

    assert value == len(gzip.compress(script, compresslevel=9, mtime=0))
    assert output.resolve() / "_next" / "static" / "shared.js" in files


def test_route_js_collection_rejects_missing_critical_route(tmp_path: Path) -> None:
    with pytest.raises(MODULE.ContractError, match="missing static route"):
        MODULE._route_js_gzip_bytes(tmp_path / "out", ["/checkout"])


def test_extension_sum_uses_unique_export_files(tmp_path: Path) -> None:
    output = tmp_path / "out"
    _write(output / "one.png", b"1" * 10)
    _write(output / "two.svg", b"2" * 20)
    _write(output / "ignored.js", b"3" * 30)

    value, files = MODULE._extension_sum(output, [".png", ".svg"])

    assert value == 30
    assert len(files) == 2


def test_collect_emits_all_local_static_metrics_and_valid_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    routes = {
        "marketing": ["/", "/checkout", "/install", "/mobile"],
        "webapp": ["/", "/dashboard", "/downloads", "/subscription/checkout"],
        "adminapp": ["/", "/network", "/money", "/support"],
    }
    for surface, surface_routes in routes.items():
        output = tmp_path / surface / "out"
        _write(output / "_next" / "static" / "app.js", b"let ok = true;")
        for route in surface_routes:
            relative = "index.html" if route == "/" else f"{route.strip('/')}/index.html"
            _write(
                output / relative,
                '<script src="/_next/static/app.js"></script>',
            )
        _write(output / "image.png", b"image")
        _write(output / "font.woff2", b"font")

    monkeypatch.setattr(MODULE, "_git_identity", lambda _: ("a" * 40, "dirty"))
    monkeypatch.setattr(MODULE, "_toolchain", lambda *_: "node@test;next@test")

    evidence = MODULE.collect(
        repo_root=tmp_path,
        contract_path=CONTRACT_PATH,
        release_version="1.2.0",
        candidate_label="local-test",
    )

    budget_ids = {item["budget_id"] for item in evidence["measurements"]}
    assert len(budget_ids) == 9
    assert evidence["release"]["working_tree_state"] == "dirty"
    assert len(evidence["environment"]["artifact_sha256"]) == 64

    contract = MODULE._load_json(CONTRACT_PATH)
    outcome = GATE.evaluate_evidence(
        contract,
        evidence,
        contract_path=CONTRACT_PATH,
        required_scopes={"local_static"},
    )
    assert outcome.summary["overall_status"] == "PASS"
