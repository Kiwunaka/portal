from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from node_inventory import LEGACY_ACTIVE_INVENTORY, inventory_ipv4_map, read_inventory, resolve_inventory_path


def test_legacy_active_inventory_path_resolves_to_archive_snapshot() -> None:
    resolved = resolve_inventory_path(LEGACY_ACTIVE_INVENTORY)

    assert resolved == REPO_ROOT / "docs" / "archive" / "flat-docs" / "08-node-inventory.md"


def test_read_inventory_supports_current_archive_header_schema() -> None:
    rows = {row.code: row for row in read_inventory()}

    assert rows["brain"].ip == "82.21.114.104"
    assert rows["pl"].role == "Premium delivery"
    assert rows["mini"].country == "RU"
    assert "rf1" not in rows


def test_inventory_ipv4_map_supports_old_short_table_schema(tmp_path: Path) -> None:
    inventory = tmp_path / "inventory.md"
    inventory.write_text(
        "\n".join(
            [
                "| Code | Name | Role | IP |",
                "| --- | --- | --- | --- |",
                "| `pl` | `PLnode` | Premium | `203.0.113.10` |",
                "| `free` | `FREENLnode` | Free | `203.0.113.20` |",
            ]
        ),
        encoding="utf-8",
    )

    assert inventory_ipv4_map(inventory) == {
        "pl": "203.0.113.10",
        "free": "203.0.113.20",
    }
