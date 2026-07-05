from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
PORTAL_BOT_DIR = ROOT / "portal_bot"
for path in (SCRIPTS_DIR, PORTAL_BOT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


from collect_node_metrics import _inbound_clients  # noqa: E402


def test_inbound_clients_accepts_xui_dict_settings() -> None:
    inbound = {"settings": {"clients": [{"id": "a"}, {"id": "b"}]}}

    assert _inbound_clients(inbound) == [{"id": "a"}, {"id": "b"}]


def test_inbound_clients_accepts_xui_json_settings() -> None:
    inbound = {"settings": '{"clients":[{"id":"a"}]}'}

    assert _inbound_clients(inbound) == [{"id": "a"}]
