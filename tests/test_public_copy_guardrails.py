from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

PUBLIC_COPY_FILES = [
    ROOT / "marketing/src/app/page.tsx",
    ROOT / "marketing/src/app/checkout/page.tsx",
    ROOT / "marketing/src/app/offer/page.tsx",
    ROOT / "marketing/src/app/privacy/page.tsx",
    ROOT / "webapp/src/App.tsx",
    ROOT / "webapp/src/legal.ts",
]

BANNED_PATTERNS = [
    re.compile(r"\bvpn\b", re.IGNORECASE),
    re.compile(r"\bвпн\b", re.IGNORECASE),
    re.compile(r"гарантирован\w*", re.IGNORECASE),
    re.compile(r"без\s+ограничений", re.IGNORECASE),
]


def test_public_copy_has_no_banned_claims() -> None:
    violations: list[str] = []
    for path in PUBLIC_COPY_FILES:
        text = path.read_text(encoding="utf-8")
        for pattern in BANNED_PATTERNS:
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
                violations.append(f"{path.relative_to(ROOT)}: /{pattern.pattern}/ -> {snippet}")
    assert not violations, "\n".join(violations)