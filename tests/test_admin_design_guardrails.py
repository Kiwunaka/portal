import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADMIN_SHELL = ROOT / "webapp" / "src" / "components" / "admin" / "admin-shell.tsx"
ADMIN_LAYOUT = ROOT / "webapp" / "src" / "app" / "(admin)" / "admin" / "layout.tsx"
MARKETING_GLOBALS = ROOT / "marketing" / "src" / "app" / "globals.css"
MARKETING_LAYOUT = ROOT / "marketing" / "src" / "app" / "layout.tsx"
WEBAPP_LAYOUT = ROOT / "webapp" / "src" / "app" / "layout.tsx"
WEBAPP_GLOBALS = ROOT / "webapp" / "src" / "app" / "globals.css"
PORTAL_DIR = ROOT / "portal_bot"


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

    assert 'from "next/font/google"' in marketing_layout
    assert "Golos_Text" in marketing_layout
    assert 'subsets: ["latin", "cyrillic"]' in marketing_layout
    assert 'variable: "--font-golos"' in marketing_layout

    assert 'import "@fontsource-variable/golos-text"' in webapp_layout
    assert 'import "@fontsource-variable/jetbrains-mono"' in webapp_layout
    assert '--font-golos: "Golos Text Variable"' in webapp_globals
    assert '--font-jetbrains: "JetBrains Mono Variable"' in webapp_globals
    for globals_source in (marketing_globals, webapp_globals):
        assert '--font-golos: "Golos Text"' not in globals_source


def test_telegram_button_style_uses_label_and_real_destructive_callbacks() -> None:
    if str(PORTAL_DIR) not in sys.path:
        sys.path.insert(0, str(PORTAL_DIR))
    from telegram_buttons import BTN_STYLE_DANGER, infer_button_style

    assert infer_button_style("◀️ Назад", callback_data="show_key") is None
    assert infer_button_style("Отмена", callback_data="adm_user_42") is None
    assert infer_button_style("Открыть кабинет", callback_data="cabinet") is None
    assert infer_button_style("Обычное действие", callback_data="regular_action") is None
    assert infer_button_style("Удалить пользователя", callback_data="adm_del_42") == BTN_STYLE_DANGER
    assert infer_button_style("Обновить токен", callback_data="adm_regen_token_42") == BTN_STYLE_DANGER
