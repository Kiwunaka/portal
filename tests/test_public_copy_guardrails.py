import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PUBLIC_COPY_FILES = [
    ROOT / "copy/catalog.ru.json",
    ROOT / "marketing/src/app/page.tsx",
    ROOT / "marketing/src/app/checkout/page.tsx",
    ROOT / "marketing/src/app/offer/page.tsx",
    ROOT / "marketing/src/app/privacy/page.tsx",
    ROOT / "webapp/src/app/page.tsx",
    ROOT / "webapp/src/app/(dashboard)/dashboard/page.tsx",
    ROOT / "webapp/src/app/(dashboard)/subscription/page.tsx",
    ROOT / "webapp/src/app/(dashboard)/subscription/checkout/page.tsx",
    ROOT / "webapp/src/app/(dashboard)/support/page.tsx",
]

BANNED_PATTERNS = [
    re.compile(r"\b100%\b", re.IGNORECASE),
    re.compile(r"гарантирован\w*", re.IGNORECASE),
    re.compile(r"без\s+ограничений", re.IGNORECASE),
]

PUBLIC_FORBIDDEN_PATTERNS = [
    re.compile(r"safe checkout flow", re.IGNORECASE),
    re.compile(r"tg_id=", re.IGNORECASE),
    re.compile(r"Telegram\s+Stars", re.IGNORECASE),
    re.compile(r"\bStars\b", re.IGNORECASE),
    re.compile(r"зв[её]зд", re.IGNORECASE),
]

MOJIBAKE_MARKERS = ["РЎ", "Рџ", "СЃ", "вЂ", "рџ", "вљ", "вњ"]


def _public_text(path: Path) -> str:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        items = payload.get("items") or {}
        return "\n".join(str((item or {}).get("ru") or "") for item in items.values())
    return path.read_text(encoding="utf-8")


def test_public_copy_has_no_banned_claims() -> None:
    violations: list[str] = []
    for path in PUBLIC_COPY_FILES:
        text = _public_text(path)
        for pattern in BANNED_PATTERNS:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
                violations.append(f"{path.relative_to(ROOT)}: /{pattern.pattern}/ -> {snippet}")
    assert not violations, "\n".join(violations)


def test_public_copy_has_no_forbidden_public_terms() -> None:
    violations: list[str] = []
    for path in PUBLIC_COPY_FILES:
        text = _public_text(path)
        for pattern in PUBLIC_FORBIDDEN_PATTERNS:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
                violations.append(f"{path.relative_to(ROOT)}: /{pattern.pattern}/ -> {snippet}")
    assert not violations, "\n".join(violations)


def test_public_copy_has_no_mojibake_markers() -> None:
    violations: list[str] = []
    for path in PUBLIC_COPY_FILES:
        text = _public_text(path)
        for marker in MOJIBAKE_MARKERS:
            if marker in text:
                violations.append(f"{path.relative_to(ROOT)}: found mojibake marker {marker!r}")
    assert not violations, "\n".join(violations)


def test_trial_first_copy_pack_is_present_on_key_public_pages() -> None:
    expected_substrings = {
        ROOT / "marketing/src/app/page.tsx": [
            "PORTAL VPN. Свободный интернет через Telegram.",
        ],
        ROOT / "marketing/src/components/marketing-landing.tsx": [
            "Свободный интернет без танцев с бубном.",
            "Потому что так честнее.",
        ],
        ROOT / "webapp/src/app/pricing/page.tsx": [
            "Выберите свой PORTAL",
            "Базовый доступ (на всякий случай)",
        ],
        ROOT / "webapp/src/app/(dashboard)/dashboard/page.tsx": [
            "Тест уже работает. Останется только решить, нужен ли полный доступ.",
        ],
        ROOT / "webapp/src/app/(dashboard)/subscription/page.tsx": [
            "Чтобы забыть про лимиты и спокойно пользоваться сервисом каждый день, переходите на полный доступ.",
        ],
        ROOT / "webapp/src/app/(dashboard)/support/page.tsx": [
            "Поддержка PORTAL. Мы на связи.",
            "Застряли на старте? Не мучайтесь — поможем всё настроить за пару минут.",
        ],
    }

    missing: list[str] = []
    for path, snippets in expected_substrings.items():
        text = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                missing.append(f"{path.relative_to(ROOT)} missing: {snippet}")

    assert not missing, "\n".join(missing)
