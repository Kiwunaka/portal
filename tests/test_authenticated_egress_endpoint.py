from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient


TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from test_smart_connect_api import _load_api


def test_authenticated_egress_probe_returns_owned_empty_marker(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    response = client.get("/api/public/authenticated-egress-probe")

    assert response.status_code == 204
    assert response.content == b""
    assert response.headers["X-Pokrov-Egress-Probe"] == "pokrov-authenticated-egress-v1"
    assert response.headers["Cache-Control"] == "no-store"
