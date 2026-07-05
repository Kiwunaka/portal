from __future__ import annotations

import sys
from pathlib import Path


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


from daily_panel_node_healthcheck import _panel_managed_identity  # noqa: E402


def test_panel_managed_identity_matches_tg_id() -> None:
    assert _panel_managed_identity({"tgId": "123", "id": "uuid-a"}, {}) == 123


def test_panel_managed_identity_matches_legacy_user_email() -> None:
    assert _panel_managed_identity({"email": "User_456", "id": "uuid-b"}, {}) == 456


def test_panel_managed_identity_matches_expected_uuid_without_tg_id() -> None:
    assert _panel_managed_identity({"email": "legacy", "id": "uuid-c"}, {"uuid-c": 789}) == 789
