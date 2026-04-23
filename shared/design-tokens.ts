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
  const { palette, radius, shadow } = designTokens.theme;
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
    "--pokrov-text-inverse": palette.text_inverse,
    "--pokrov-emerald": palette.emerald,
    "--pokrov-emerald-strong": palette.emerald_strong,
    "--pokrov-emerald-soft": palette.emerald_soft,
    "--pokrov-emerald-dark": palette.emerald_dark,
    "--pokrov-gold-soft": palette.gold_soft,
    "--pokrov-line": palette.line,
    "--pokrov-line-strong": palette.line_strong,
    "--pokrov-line-dark": palette.line_dark,
    "--pokrov-focus-ring": palette.focus_ring,
    "--pokrov-radius-card": radius.card,
    "--pokrov-radius-panel": radius.panel,
    "--pokrov-radius-pill": radius.pill,
    "--pokrov-shadow-soft": shadow.soft,
    "--pokrov-shadow-medium": shadow.medium,
    "--pokrov-shadow-strong": shadow.strong,
    "--pokrov-card-padding": densityTokens.card_padding,
    "--pokrov-panel-padding": densityTokens.panel_padding,
    "--pokrov-grid-gap": densityTokens.grid_gap,
    "--pokrov-section-gap": densityTokens.section_gap,
  };
}
