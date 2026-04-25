import designTokensJson from "./design-tokens.json";

export type DesignTokens = typeof designTokensJson;
export type DesignDensity = keyof DesignTokens["density"];
export type DesignDensityInput = DesignDensity | "product";

export const designTokens: DesignTokens = designTokensJson;
const legacyDensityAliases: Partial<Record<DesignDensityInput, DesignDensity>> = {
  product: "public",
};

export function getDesignTokens(): DesignTokens {
  return designTokens;
}

export function normalizeDesignDensity(density: DesignDensityInput = "public"): DesignDensity {
  return legacyDensityAliases[density] || density;
}

export function getDesignDensityTokens(density: DesignDensityInput = "public") {
  return designTokens.density[normalizeDesignDensity(density)];
}

export function getDesignTokenCssVariables(density: DesignDensityInput = "public"): Record<string, string> {
  const { palette, radius, semantic, shadow, typography } = designTokens.theme;
  const { component, glass } = designTokens;
  const densityTokens = getDesignDensityTokens(density);

  return {
    "--pokrov-bg": palette.canvas,
    "--pokrov-bg-alt": palette.canvas_alt,
    "--pokrov-surface": palette.surface,
    "--pokrov-surface-strong": palette.surface_strong,
    "--pokrov-surface-dark": palette.surface_dark,
    "--pokrov-surface-dark-strong": palette.surface_dark_strong,
    "--pokrov-text": palette.text,
    "--pokrov-text-soft": palette.text_soft,
    "--pokrov-text-muted": palette.text_muted,
    "--pokrov-text-inverse": palette.text_inverse,
    "--pokrov-emerald": palette.emerald,
    "--pokrov-emerald-strong": palette.emerald_strong,
    "--pokrov-emerald-soft": palette.emerald_soft,
    "--pokrov-emerald-dark": palette.emerald_dark,
    "--pokrov-mint": palette.mint,
    "--pokrov-mint-strong": palette.mint_strong,
    "--pokrov-sage": palette.sage,
    "--pokrov-gold-soft": palette.gold_soft,
    "--pokrov-line": palette.line,
    "--pokrov-line-strong": palette.line_strong,
    "--pokrov-line-dark": palette.line_dark,
    "--pokrov-focus-ring": palette.focus_ring,
    "--pokrov-status-success-bg": semantic.success.bg,
    "--pokrov-status-success-text": semantic.success.text,
    "--pokrov-status-success-line": semantic.success.line,
    "--pokrov-status-warning-bg": semantic.warning.bg,
    "--pokrov-status-warning-text": semantic.warning.text,
    "--pokrov-status-warning-line": semantic.warning.line,
    "--pokrov-status-danger-bg": semantic.danger.bg,
    "--pokrov-status-danger-text": semantic.danger.text,
    "--pokrov-status-danger-line": semantic.danger.line,
    "--pokrov-status-info-bg": semantic.info.bg,
    "--pokrov-status-info-text": semantic.info.text,
    "--pokrov-status-info-line": semantic.info.line,
    "--pokrov-radius-card": densityTokens.radius_card || radius.card,
    "--pokrov-radius-panel": densityTokens.radius_panel || radius.panel,
    "--pokrov-radius-modal": radius.modal,
    "--pokrov-radius-control": radius.control,
    "--pokrov-radius-tile": radius.tile,
    "--pokrov-radius-pill": radius.pill,
    "--pokrov-radius-app-connect": radius.app_connect,
    "--pokrov-shadow-soft": shadow.soft,
    "--pokrov-shadow-medium": shadow.medium,
    "--pokrov-shadow-strong": shadow.strong,
    "--pokrov-shadow-focus": shadow.focus,
    "--pokrov-card-padding": densityTokens.card_padding,
    "--pokrov-panel-padding": densityTokens.panel_padding,
    "--pokrov-grid-gap": densityTokens.grid_gap,
    "--pokrov-section-gap": densityTokens.section_gap,
    "--pokrov-button-height": component.button.height,
    "--pokrov-button-compact-height": component.button.compact_height,
    "--pokrov-button-radius": component.button.radius,
    "--pokrov-button-icon-size": component.button.icon_size,
    "--pokrov-nav-item-min-height": component.nav.item_min_height,
    "--pokrov-nav-icon-size": component.nav.icon_size,
    "--pokrov-nav-active-bg": component.nav.active_bg,
    "--pokrov-table-row-height": component.table.row_height,
    "--pokrov-table-header-bg": component.table.header_bg,
    "--pokrov-table-divider": component.table.divider,
    "--pokrov-glass-max-blur": glass.max_blur,
    "--pokrov-glass-border-alpha": glass.border_alpha,
    "--pokrov-font-body": typography.body_family,
    "--pokrov-font-display": typography.display_family,
    "--pokrov-font-mono": typography.mono_family,
    "--pokrov-letter-spacing": typography.letter_spacing,
    "--pokrov-compact-line-height": typography.compact_line_height,
    "--pokrov-body-line-height": typography.body_line_height,
  };
}
