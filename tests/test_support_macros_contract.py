from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_MACROS = ROOT / "shared" / "support-macros.ts"
WEBAPP_REEXPORT = ROOT / "webapp" / "src" / "lib" / "support-macros.ts"
ADMIN_TICKETS = ROOT / "webapp" / "src" / "app" / "(admin)" / "admin" / "tickets" / "page.tsx"
SUPPORT_RUNBOOK = ROOT / "docs" / "launch" / "support-macros.md"

REQUIRED_MACRO_IDS = [
    "diagnostic_context",
    "cannot_connect",
    "payment_or_key",
    "download_not_visible",
    "windows_smartscreen",
    "telegram_bonus_missing",
    "manual_profile_safety",
    "operator_escalation",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_support_macros_have_shared_source_and_admin_consumer() -> None:
    shared = _read(SHARED_MACROS)
    reexport = _read(WEBAPP_REEXPORT)
    admin = _read(ADMIN_TICKETS)

    assert "SUPPORT_REPLY_MACROS" in shared
    assert "SupportReplyMacro" in shared
    assert "../../../shared/support-macros" in reexport
    assert 'from "@/lib/support-macros"' in admin
    assert "SUPPORT_REPLY_MACROS.map" in admin
    assert "ADMIN_REPLY_TEMPLATES" not in admin


def test_support_macro_ids_are_documented() -> None:
    shared = _read(SHARED_MACROS)
    runbook = _read(SUPPORT_RUNBOOK)

    for macro_id in REQUIRED_MACRO_IDS:
        assert f'id: "{macro_id}"' in shared
        assert f"`{macro_id}`" in runbook


def test_support_macros_keep_sensitive_data_boundaries_visible() -> None:
    shared = _read(SHARED_MACROS)
    runbook = _read(SUPPORT_RUNBOOK)

    assert "Данные карты присылать не нужно" in shared
    assert "Не используйте неофициальные зеркала" in shared
    assert "Не отправляйте личную ссылку или QR" in shared
    assert "do not ask users to send card data" in runbook
    assert "do not point users to unofficial mirrors" in runbook
