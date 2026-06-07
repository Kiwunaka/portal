import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADMIN_SHELL = ROOT / "webapp" / "src" / "components" / "admin" / "admin-shell.tsx"
ADMIN_LAYOUT = ROOT / "webapp" / "src" / "app" / "(admin)" / "admin" / "layout.tsx"
MARKETING_GLOBALS = ROOT / "marketing" / "src" / "app" / "globals.css"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_admin_layout_uses_admin_density_tokens() -> None:
    source = _read(ADMIN_LAYOUT)

    assert 'getDesignTokenCssVariables("admin")' in source
    assert "style={ADMIN_DESIGN_TOKEN_VARS}" in source


def test_admin_shared_helpers_keep_radius_tokenized() -> None:
    source = _read(ADMIN_SHELL)

    assert "--pokrov-radius-panel" in source
    assert "--pokrov-radius-card" in source
    assert "--pokrov-radius-control" in source
    assert "--pokrov-panel-padding" in source
    assert "--pokrov-card-padding" in source

    arbitrary_radius = re.findall(r"rounded-\[(?!var\(--pokrov-radius)[^\]]+\]", source)
    assert arbitrary_radius == []

    legacy_tailwind_radius = sorted(set(re.findall(r"\brounded-(?:lg|xl|2xl|3xl)\b", source)))
    assert legacy_tailwind_radius == []


def test_marketing_lp_variables_bridge_to_design_tokens() -> None:
    source = _read(MARKETING_GLOBALS)

    required_bridges = [
        "--lp-bg: var(--pokrov-bg,",
        "--lp-bg-2: var(--pokrov-bg-alt,",
        "--lp-surface: var(--pokrov-surface-glass,",
        "--lp-surface-strong: var(--pokrov-surface-glass-strong,",
        "--lp-text: var(--pokrov-text,",
        "--lp-text-soft: var(--pokrov-text-soft,",
        "--lp-line: var(--pokrov-line,",
        "--lp-primary: var(--pokrov-emerald,",
        "--lp-shadow: var(--pokrov-shadow-medium,",
        "--lp-shadow-soft: var(--pokrov-shadow-soft,",
    ]

    for bridge in required_bridges:
        assert bridge in source
