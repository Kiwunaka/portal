from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_serve_export():
    module_path = ROOT / "webapp" / "scripts" / "serve_export.py"
    spec = importlib.util.spec_from_file_location("webapp_serve_export_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _handler(module, directory: Path):
    handler = object.__new__(module.ExportStaticHandler)
    handler._export_directory = directory.resolve()
    return handler


def test_export_static_handler_normalized_candidates_cover_spa_routes(tmp_path: Path) -> None:
    module = _load_serve_export()
    handler = _handler(module, tmp_path)

    assert handler._normalized_candidates("/") == [Path("index.html")]
    assert handler._normalized_candidates("/settings/") == [Path("settings/index.html")]
    assert handler._normalized_candidates("/settings") == [
        Path("settings"),
        Path("settings/index.html"),
        Path("settings.html"),
    ]
    assert handler._normalized_candidates("/support/thread?id=1") == [
        Path("support/thread"),
        Path("support/thread/index.html"),
        Path("support/thread.html"),
    ]
    assert handler._normalized_candidates("/%2e%2e/admin") == [
        Path("admin"),
        Path("admin/index.html"),
        Path("admin.html"),
    ]


def test_export_static_handler_open_candidate_stays_inside_export_root(tmp_path: Path) -> None:
    module = _load_serve_export()
    export_root = tmp_path / "out"
    export_root.mkdir()
    (export_root / "index.html").write_text("ok", encoding="utf-8")
    outside = tmp_path / "secret.html"
    outside.write_text("secret", encoding="utf-8")
    symlink = export_root / "linked-secret.html"
    try:
        symlink.symlink_to(outside)
    except OSError:
        symlink = None

    handler = _handler(module, export_root)

    with handler._open_candidate(Path("index.html")) as handle:
        assert handle.read() == b"ok"

    assert handler._open_candidate(Path("../secret.html")) is None
    assert handler._open_candidate(Path("missing.html")) is None
    if symlink is not None:
        assert handler._open_candidate(Path("linked-secret.html")) is None
