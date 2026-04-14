from __future__ import annotations

import importlib
import sys
import warnings
from pathlib import Path


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def test_init_db_does_not_emit_sqlite_datetime_adapter_warning(monkeypatch, tmp_path):
    db_path = tmp_path / "portal-datetime-noise.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("BOT_TOKEN", "portal-test-token")
    monkeypatch.setenv("ADMIN_ID", "1")

    for name in ["config", "db", "migrations", "models"]:
        sys.modules.pop(name, None)

    importlib.import_module("config")
    db = importlib.import_module("db")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        db.init_db()

    adapter_warnings = [
        item
        for item in caught
        if "default datetime adapter is deprecated" in str(item.message)
    ]

    try:
        assert adapter_warnings == []
    finally:
        db.engine.dispose()
