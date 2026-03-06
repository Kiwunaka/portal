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
    re.compile(r"\bVPN\b", re.IGNORECASE),
    re.compile(r"safe checkout flow", re.IGNORECASE),
    re.compile(r"tg_id=", re.IGNORECASE),
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
