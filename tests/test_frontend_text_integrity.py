from pathlib import Path
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
    ROOT / "docs" / "README.md",
    ROOT / "docs" / "product",
    ROOT / "docs" / "architecture",
    ROOT / "docs" / "operations",
    ROOT / "docs" / "user",
    ROOT / "docs" / "launch",
    ROOT / "docs" / "developer" / "developer-guide.md",
    ROOT / "docs" / "developer" / "repository-map.md",
]


def test_active_release_text_sources_have_no_mojibake() -> None:
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
