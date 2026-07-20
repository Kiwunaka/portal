import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADMIN_SHELL = ROOT / "webapp" / "src" / "components" / "admin" / "admin-shell.tsx"
ADMIN_LAYOUT = ROOT / "webapp" / "src" / "app" / "(admin)" / "admin" / "layout.tsx"
MARKETING_GLOBALS = ROOT / "marketing" / "src" / "app" / "globals.css"
MARKETING_LAYOUT = ROOT / "marketing" / "src" / "app" / "layout.tsx"
WEBAPP_LAYOUT = ROOT / "webapp" / "src" / "app" / "layout.tsx"
WEBAPP_GLOBALS = ROOT / "webapp" / "src" / "app" / "globals.css"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_admin_layout_uses_admin_density_tokens() -> None:
    source = _read(ADMIN_LAYOUT)

    # Scoped density overrides must come from the density emitter so inline
    # styles never freeze adaptive colors (DESIGN.md theme model).
    assert 'getDesignTokenDensityCssVariables("admin")' in source
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


def test_marketing_globals_bridge_to_design_tokens() -> None:
    # The legacy --lp-* bridge died with the sub-project 1 rebuild; marketing
    # utilities now resolve through the Tailwind v4 @theme token bridge.
    source = _read(MARKETING_GLOBALS)

    required_bridges = [
        "--color-canvas: var(--pokrov-bg)",
        "--color-surface: var(--pokrov-surface)",
        "--color-ink: var(--pokrov-text)",
        "--color-ink-soft: var(--pokrov-text-soft)",
        "--color-brand: var(--pokrov-accent)",
        "--color-line: var(--pokrov-line)",
        "--radius-card: var(--pokrov-radius-card)",
        "--shadow-soft: var(--pokrov-shadow-soft)",
    ]

    for bridge in required_bridges:
        assert bridge in source

    assert "--lp-" not in source


def test_public_surfaces_bundle_the_canonical_cyrillic_fonts() -> None:
    marketing_layout = _read(MARKETING_LAYOUT)
    webapp_layout = _read(WEBAPP_LAYOUT)
    marketing_globals = _read(MARKETING_GLOBALS)
    webapp_globals = _read(WEBAPP_GLOBALS)

    for source in (marketing_layout, webapp_layout):
        assert 'from "next/font/google"' in source
        assert "Golos_Text" in source
        assert 'subsets: ["latin", "cyrillic"]' in source
        assert 'variable: "--font-golos"' in source

    assert "JetBrains_Mono" in webapp_layout
    assert 'variable: "--font-jetbrains"' in webapp_layout
    for globals_source in (marketing_globals, webapp_globals):
        assert '--font-golos: "Golos Text"' not in globals_source
