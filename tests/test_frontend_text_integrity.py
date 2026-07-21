from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from text_integrity import scan_mojibake  # noqa: E402


ACTIVE_TEXT_ROOTS = [
    ROOT / "webapp" / "src",
    ROOT / "marketing" / "src",
    ROOT / "shared",
    ROOT / "copy",
    ROOT / "docs" / "design",
]

TELEGRAM_PROMISE_FILES = [
    ROOT / "marketing/src/lib/seo-pages.ts",
    ROOT / "marketing/src/lib/marketing-site.ts",
    ROOT / "marketing/src/app/checkout/checkout-client.tsx",
    ROOT / "marketing/src/app/telegram/page.tsx",
    ROOT / "marketing/src/app/vpn/page.tsx",
    ROOT / "marketing/public/llms.txt",
    ROOT / "marketing/public/pricing.md",
    ROOT / "webapp/src/app/(dashboard)/settings/page.tsx",
]


def test_active_frontend_sources_have_no_mojibake() -> None:
    issues = scan_mojibake(ACTIVE_TEXT_ROOTS)
    assert not issues, "\n".join(issue.format(ROOT) for issue in issues)


def test_mojibake_scanner_detects_active_text(tmp_path: Path) -> None:
    source = tmp_path / "active" / "page.tsx"
    source.parent.mkdir()
    source.write_text("const label = 'РЎРѓ broken';\n", encoding="utf-8")

    issues = scan_mojibake([tmp_path / "active"])

    assert len(issues) == 1
    assert issues[0].path == source


def test_mojibake_scanner_detects_common_cp1251_artifacts(tmp_path: Path) -> None:
    source = tmp_path / "active" / "loading.tsx"
    source.parent.mkdir()
    source.write_text("const label = 'РџРѕРґС‚СЏРіРёРІР°РµРј РєР°Р±РёРЅРµС‚';\n", encoding="utf-8")

    issues = scan_mojibake([tmp_path / "active"])

    assert len(issues) == 1
    assert issues[0].path == source


def test_mojibake_scanner_ignores_archives(tmp_path: Path) -> None:
    archived = tmp_path / "docs" / "archive" / "old.md"
    archived.parent.mkdir(parents=True)
    archived.write_text("Retained old mojibake: РЎРѓ\n", encoding="utf-8")

    assert scan_mojibake([tmp_path / "docs"]) == []


def test_active_telegram_copy_never_presents_channel_bonus_as_direct_plus_ten() -> None:
    violations: list[str] = []
    direct_plus_ten = re.compile(r"\+\s*10\s*(?:д(?:ень|ня|ней)|day)", re.IGNORECASE)
    for path in TELEGRAM_PROMISE_FILES:
        text = path.read_text(encoding="utf-8")
        for match in direct_plus_ten.finditer(text):
            snippet = text[max(0, match.start() - 70):match.end() + 70].replace("\n", " ")
            violations.append(f"{path.relative_to(ROOT)}: {snippet}")

    assert violations == [], "\n".join(violations)
