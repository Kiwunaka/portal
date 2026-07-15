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
