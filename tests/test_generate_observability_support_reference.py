from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts/generate_observability_support_reference.py"
SPEC = importlib.util.spec_from_file_location(
    "generate_observability_support_reference", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_generated_reference_contains_every_catalog_entry_once() -> None:
    catalog = json.loads(MODULE.CATALOG_PATH.read_text(encoding="utf-8"))
    rendered = MODULE.render_reference()
    for entry in catalog["entries"]:
        assert rendered.count(f"`{entry['code']}`") == 1
    assert f"- entries: `{len(catalog['entries'])}`" in rendered


def test_checked_in_reference_is_current() -> None:
    assert MODULE.OUTPUT_PATH.read_text(encoding="utf-8") == MODULE.render_reference()


def test_catalog_digest_is_stable_across_line_endings(tmp_path: Path) -> None:
    canonical = (
        b'{"schema_version":1,"catalog_version":"test",'
        b'"entries":[{"code":"TEST-001"}]}\n'
    )
    lf_path = tmp_path / "catalog-lf.json"
    crlf_path = tmp_path / "catalog-crlf.json"
    cr_path = tmp_path / "catalog-cr.json"
    lf_path.write_bytes(canonical)
    crlf_path.write_bytes(canonical.replace(b"\n", b"\r\n"))
    cr_path.write_bytes(canonical.replace(b"\n", b"\r"))

    expected = hashlib.sha256(canonical).hexdigest()
    assert MODULE._load_catalog(lf_path)["_sha256"] == expected
    assert MODULE._load_catalog(crlf_path)["_sha256"] == expected
    assert MODULE._load_catalog(cr_path)["_sha256"] == expected
