from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "portal_bot" / "release_announcement_job.py"
SPEC = importlib.util.spec_from_file_location("release_announcement_job_test_module", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _payload() -> dict:
    return {
        "schema_version": 1,
        "schedule_id": "release-1.1.5-0900-msk",
        "title": "POKROV 1.1.5",
        "summary": "Стабильное обновление Android и Windows уже доступно.",
        "link": "https://pokrov.space/install/",
        "telegram_text": "POKROV 1.1.5\n\nОбновление уже доступно.",
        "delete_after_success": True,
    }


def test_config_accepts_owned_https_link_and_bounded_copy(tmp_path: Path) -> None:
    path = tmp_path / "announcement.json"
    path.write_text(json.dumps(_payload(), ensure_ascii=False), encoding="utf-8")
    loaded = MODULE.load_announcement_config(path)
    assert loaded["schedule_id"] == "release-1.1.5-0900-msk"
    assert loaded["link"] == "https://pokrov.space/install/"


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("link", "https://example.com/install/", "link_not_allowed"),
        ("schedule_id", "../../bad", "schedule_id_invalid"),
        ("telegram_text", "", "telegram_text_invalid"),
        ("delete_after_success", "yes", "delete_after_success_invalid"),
    ],
)
def test_config_rejects_unsafe_or_unbounded_values(
    tmp_path: Path,
    field: str,
    value,
    code: str,
) -> None:
    payload = _payload()
    payload[field] = value
    path = tmp_path / "announcement.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(MODULE.AnnouncementConfigError, match=code):
        MODULE.load_announcement_config(path)


def test_idempotency_key_is_stable_per_schedule_and_action() -> None:
    first = MODULE._idempotency_key("release-1.1.5-0900-msk", "broadcast.send")
    second = MODULE._idempotency_key("release-1.1.5-0900-msk", "broadcast.send")
    other = MODULE._idempotency_key("release-1.1.5-0900-msk", "live_update.create")
    assert first == second
    assert first != other


def test_execution_facts_reads_guarded_external_result_shape() -> None:
    assert MODULE._execution_facts(
        {
            "ok": False,
            "status": "failed",
            "result": {
                "sent": 28,
                "failed": 33,
                "reason_counts": {"blocked": 33},
            },
        }
    ) == {
        "sent": 28,
        "failed": 33,
        "reason_counts": {"blocked": 33},
    }
