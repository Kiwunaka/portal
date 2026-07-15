import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_status_mapper_has_the_seven_approved_russian_labels() -> None:
    text = (ROOT / "adminapp/src/lib/ops-status/presentation.ts").read_text(encoding="utf-8")
    for label in (
        "Норма",
        "Требует внимания",
        "Сбой",
        "Устарело",
        "Недоступно",
        "Нет данных",
        "Доступ заблокирован",
    ):
        assert label in text


def test_tooltip_contract_is_not_a_title_attribute() -> None:
    text = (ROOT / "adminapp/src/components/ui/tooltip.tsx").read_text(encoding="utf-8")
    assert "aria-describedby" in text
    assert 'role="tooltip"' in text
    assert 'event.key === "Escape"' in text
    assert " title=" not in text


def test_tooltip_escape_does_not_reopen_on_restored_focus() -> None:
    text = (ROOT / "adminapp/src/components/ui/tooltip.tsx").read_text(encoding="utf-8")
    assert "suppressFocusOpenRef.current = true" in text
    assert "if (!suppressFocusOpenRef.current)" in text


def test_source_row_suppresses_measurements_without_a_verdict() -> None:
    text = (ROOT / "adminapp/src/components/ui/source-row.tsx").read_text(encoding="utf-8")
    match = re.search(r"function sourceDetail\((.*?)\n}\n", text, re.DOTALL)
    assert match is not None
    contract = match.group(0)
    assert "status: OpsStatusCode" in contract
    assert 'status === "missing"' in contract
    assert 'status === "unavailable"' in contract
    assert 'return "Нет данных"' in contract
    assert 'return "Недоступно"' in contract
    assert contract.index('status === "missing"') < contract.index("return detail")
    assert contract.index('status === "unavailable"') < contract.index("return detail")
    assert "sourceDetail(status, detail)" in text


def test_empty_and_error_states_require_operator_guidance() -> None:
    text = (ROOT / "adminapp/src/components/ui/states.tsx").read_text(encoding="utf-8")
    for props_name in ("EmptyStateProps", "ErrorStateProps"):
        match = re.search(rf"export interface {props_name} {{(.*?)\n}}", text, re.DOTALL)
        assert match is not None
        assert "description: string;" in match.group(1)
