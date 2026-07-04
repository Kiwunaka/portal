import designTokensJson from "./design-tokens.json";

export type DesignTokens = typeof designTokensJson;
export type DesignDensity = keyof DesignTokens["density"];
export type DesignDensityInput = DesignDensity;

export const designTokens: DesignTokens = designTokensJson;

export function getDesignTokens(): DesignTokens {
  return designTokens;
}

export function normalizeDesignDensity(density: DesignDensityInput = "public"): DesignDensity {
  return density;
}

export function getDesignDensityTokens(density: DesignDensityInput = "public") {
  return designTokens.density[normalizeDesignDensity(density)];
}

export function getDesignTokenCssVariables(density: DesignDensityInput = "public"): Record<string, string> {
  const { palette, radius, semantic, shadow, typography } = designTokens.theme;
  const { component, glass, motion, spacing } = designTokens;
  const densityTokens = getDesignDensityTokens(density);

  return {
    "--pokrov-bg": palette.canvas,
    "--pokrov-bg-alt": palette.canvas_alt,
    "--pokrov-bg-dark": palette.canvas_dark,
    "--pokrov-bg-dark-alt": palette.canvas_dark_alt,
    "--pokrov-surface": palette.surface,
    "--pokrov-surface-strong": palette.surface_strong,
    "--pokrov-surface-subtle": palette.surface_subtle,
    "--pokrov-surface-muted": palette.surface_muted,
    "--pokrov-surface-dark": palette.surface_dark,
    "--pokrov-surface-dark-strong": palette.surface_dark_strong,
    "--pokrov-surface-subtle-dark": palette.surface_subtle_dark,
    "--pokrov-surface-muted-dark": palette.surface_muted_dark,
    "--pokrov-surface-glass": palette.surface_glass,
    "--pokrov-surface-glass-strong": palette.surface_glass_strong,
    "--pokrov-surface-glass-dark": palette.surface_glass_dark,
    "--pokrov-surface-glass-dark-strong": palette.surface_glass_dark_strong,
    "--pokrov-surface-raised": palette.surface_raised,
    "--pokrov-surface-raised-dark": palette.surface_raised_dark,
    "--pokrov-text": palette.text,
    "--pokrov-text-soft": palette.text_soft,
    "--pokrov-text-muted": palette.text_muted,
    "--pokrov-text-dark": palette.text_dark,
    "--pokrov-text-dark-soft": palette.text_dark_soft,
    "--pokrov-text-dark-muted": palette.text_dark_muted,
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
    "--pokrov-line-dark-strong": palette.line_dark_strong,
    "--pokrov-focus-ring": palette.focus_ring,
    "--pokrov-focus-ring-dark": palette.focus_ring_dark,
    "--pokrov-status-green": palette.status_green,
    "--pokrov-accent": palette.emerald,
    "--pokrov-accent-hover": palette.emerald_strong,
    "--pokrov-accent-contrast": component.button.text,
    "--pokrov-accent-soft": palette.emerald_soft,
    "--pokrov-status-success-bg": semantic.success.bg,
    "--pokrov-status-success-text": semantic.success.text,
    "--pokrov-status-success-line": semantic.success.line,
    "--pokrov-status-success-bg-dark": semantic.success.bg_dark,
    "--pokrov-status-success-text-dark": semantic.success.text_dark,
    "--pokrov-status-success-line-dark": semantic.success.line_dark,
    "--pokrov-status-warning-bg": semantic.warning.bg,
    "--pokrov-status-warning-text": semantic.warning.text,
    "--pokrov-status-warning-line": semantic.warning.line,
    "--pokrov-status-warning-bg-dark": semantic.warning.bg_dark,
    "--pokrov-status-warning-text-dark": semantic.warning.text_dark,
    "--pokrov-status-warning-line-dark": semantic.warning.line_dark,
    "--pokrov-status-danger-bg": semantic.danger.bg,
    "--pokrov-status-danger-text": semantic.danger.text,
    "--pokrov-status-danger-line": semantic.danger.line,
    "--pokrov-status-danger-bg-dark": semantic.danger.bg_dark,
    "--pokrov-status-danger-text-dark": semantic.danger.text_dark,
    "--pokrov-status-danger-line-dark": semantic.danger.line_dark,
    "--pokrov-status-info-bg": semantic.info.bg,
    "--pokrov-status-info-text": semantic.info.text,
    "--pokrov-status-info-line": semantic.info.line,
    "--pokrov-status-info-bg-dark": semantic.info.bg_dark,
    "--pokrov-status-info-text-dark": semantic.info.text_dark,
    "--pokrov-status-info-line-dark": semantic.info.line_dark,
    "--pokrov-status-neutral-bg": semantic.neutral.bg,
    "--pokrov-status-neutral-text": semantic.neutral.text,
    "--pokrov-status-neutral-line": semantic.neutral.line,
    "--pokrov-status-neutral-bg-dark": semantic.neutral.bg_dark,
    "--pokrov-status-neutral-text-dark": semantic.neutral.text_dark,
    "--pokrov-status-neutral-line-dark": semantic.neutral.line_dark,
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
    "--pokrov-shadow-soft-dark": shadow.soft_dark,
    "--pokrov-shadow-medium-dark": shadow.medium_dark,
    "--pokrov-shadow-strong-dark": shadow.strong_dark,
    "--pokrov-shadow-focus": shadow.focus,
    "--pokrov-card-padding": densityTokens.card_padding,
    "--pokrov-panel-padding": densityTokens.panel_padding,
    "--pokrov-grid-gap": densityTokens.grid_gap,
    "--pokrov-section-gap": densityTokens.section_gap,
    "--pokrov-space-2xs": spacing["2xs"],
    "--pokrov-space-xs": spacing.xs,
    "--pokrov-space-sm": spacing.sm,
    "--pokrov-space-md": spacing.md,
    "--pokrov-space-lg": spacing.lg,
    "--pokrov-space-xl": spacing.xl,
    "--pokrov-space-2xl": spacing["2xl"],
    "--pokrov-space-3xl": spacing["3xl"],
    "--pokrov-button-height": component.button.height,
    "--pokrov-button-compact-height": component.button.compact_height,
    "--pokrov-button-radius": component.button.radius,
    "--pokrov-button-icon-size": component.button.icon_size,
    "--pokrov-button-bg": component.button.background,
    "--pokrov-button-bg-hover": component.button.background_hover,
    "--pokrov-button-bg-dark": component.button.background_dark,
    "--pokrov-button-bg-dark-hover": component.button.background_dark_hover,
    "--pokrov-button-text": component.button.text,
    "--pokrov-button-text-dark": component.button.text_dark,
    "--pokrov-button-secondary-bg": component.button.secondary_background,
    "--pokrov-button-secondary-bg-dark": component.button.secondary_background_dark,
    "--pokrov-button-border": component.button.border,
    "--pokrov-button-border-dark": component.button.border_dark,
    "--pokrov-nav-item-min-height": component.nav.item_min_height,
    "--pokrov-nav-icon-size": component.nav.icon_size,
    "--pokrov-nav-active-bg": component.nav.active_bg,
    "--pokrov-nav-active-bg-dark": component.nav.active_bg_dark,
    "--pokrov-nav-hover-bg": component.nav.hover_bg,
    "--pokrov-nav-hover-bg-dark": component.nav.hover_bg_dark,
    "--pokrov-nav-text": component.nav.text,
    "--pokrov-nav-text-dark": component.nav.text_dark,
    "--pokrov-card-bg": component.card.background,
    "--pokrov-card-bg-dark": component.card.background_dark,
    "--pokrov-card-border": component.card.border,
    "--pokrov-card-border-dark": component.card.border_dark,
    "--pokrov-card-inner-edge": component.card.inner_edge,
    "--pokrov-card-inner-edge-dark": component.card.inner_edge_dark,
    "--pokrov-table-row-height": component.table.row_height,
    "--pokrov-table-header-bg": component.table.header_bg,
    "--pokrov-table-header-bg-dark": component.table.header_bg_dark,
    "--pokrov-table-divider": component.table.divider,
    "--pokrov-table-divider-dark": component.table.divider_dark,
    "--pokrov-table-row-hover-bg": component.table.row_hover_bg,
    "--pokrov-table-row-hover-bg-dark": component.table.row_hover_bg_dark,
    "--pokrov-skeleton-base": component.skeleton.base,
    "--pokrov-skeleton-highlight": component.skeleton.highlight,
    "--pokrov-skeleton-base-dark": component.skeleton.base_dark,
    "--pokrov-skeleton-highlight-dark": component.skeleton.highlight_dark,
    "--pokrov-progress-track": component.progress.track,
    "--pokrov-progress-track-dark": component.progress.track_dark,
    "--pokrov-progress-fill": component.progress.fill,
    "--pokrov-progress-fill-dark": component.progress.fill_dark,
    "--pokrov-progress-warning-fill": component.progress.warning_fill,
    "--pokrov-progress-danger-fill": component.progress.danger_fill,
    "--pokrov-app-connect-size-mobile": component.app_connect.size_mobile,
    "--pokrov-app-connect-size-desktop": component.app_connect.size_desktop,
    "--pokrov-app-connect-ring": component.app_connect.ring,
    "--pokrov-switch-width": component.switch.width,
    "--pokrov-switch-height": component.switch.height,
    "--pokrov-switch-thumb": component.switch.thumb,
    "--pokrov-switch-on-bg": component.switch.on_background,
    "--pokrov-switch-off-bg": component.switch.off_background,
    "--pokrov-switch-thumb-color": component.switch.thumb_color,
    "--pokrov-switch-transition": component.switch.transition,
    "--pokrov-glass-max-blur": glass.max_blur,
    "--pokrov-glass-border-alpha": glass.border_alpha,
    "--pokrov-duration-fast": motion.duration_fast,
    "--pokrov-duration-base": motion.duration_base,
    "--pokrov-duration-slow": motion.duration_slow,
    "--pokrov-easing": motion.easing,
    "--pokrov-easing-spring": motion.easing_spring,
    "--pokrov-font-body": typography.body_family,
    "--pokrov-font-display": typography.display_family,
    "--pokrov-font-mono": typography.mono_family,
    "--pokrov-letter-spacing": typography.letter_spacing,
    "--pokrov-display-letter-spacing": typography.display_letter_spacing,
    "--pokrov-compact-line-height": typography.compact_line_height,
    "--pokrov-body-line-height": typography.body_line_height,
    "--pokrov-font-size-display": typography.size_display,
    "--pokrov-font-size-title": typography.size_title,
    "--pokrov-font-size-title-2": typography.size_title_2,
    "--pokrov-font-size-title-3": typography.size_title_3,
    "--pokrov-font-size-body": typography.size_body,
    "--pokrov-font-size-callout": typography.size_callout,
    "--pokrov-font-size-footnote": typography.size_footnote,
    "--pokrov-font-size-caption": typography.size_caption,
    "--pokrov-font-weight-regular": typography.weight_regular,
    "--pokrov-font-weight-medium": typography.weight_medium,
    "--pokrov-font-weight-semibold": typography.weight_semibold,
    "--pokrov-font-weight-bold": typography.weight_bold,
  };
}

/**
 * Density-only variables (paddings, gaps, radii). Theme-independent.
 * Use for scoped density overrides (for example the admin subtree)
 * so that inline styles never freeze theme-adaptive color variables.
 */
export function getDesignTokenDensityCssVariables(density: DesignDensityInput = "public"): Record<string, string> {
  const densityTokens = getDesignDensityTokens(density);
  const { radius } = designTokens.theme;

  return {
    "--pokrov-radius-card": densityTokens.radius_card || radius.card,
    "--pokrov-radius-panel": densityTokens.radius_panel || radius.panel,
    "--pokrov-card-padding": densityTokens.card_padding,
    "--pokrov-panel-padding": densityTokens.panel_padding,
    "--pokrov-grid-gap": densityTokens.grid_gap,
    "--pokrov-section-gap": densityTokens.section_gap,
  };
}

/**
 * Dark-theme remap for the adaptive variable set.
 * Every variable listed here keeps the same name in dark mode and simply
 * receives its dark value, so consumers write `var(--pokrov-surface)` once
 * and never hand-author `.dark` overrides again.
 * Legacy `-dark`-suffixed variables stay static for backward compatibility.
 */
export function getDesignTokenDarkCssVariables(): Record<string, string> {
  const { palette, semantic, shadow } = designTokens.theme;
  const { component } = designTokens;

  return {
    "--pokrov-bg": palette.canvas_dark,
    "--pokrov-bg-alt": palette.canvas_dark_alt,
    "--pokrov-surface": palette.surface_dark,
    "--pokrov-surface-strong": palette.surface_dark_strong,
    "--pokrov-surface-subtle": palette.surface_subtle_dark,
    "--pokrov-surface-muted": palette.surface_muted_dark,
    "--pokrov-surface-glass": palette.surface_glass_dark,
    "--pokrov-surface-glass-strong": palette.surface_glass_dark_strong,
    "--pokrov-surface-raised": palette.surface_raised_dark,
    "--pokrov-text": palette.text_dark,
    "--pokrov-text-soft": palette.text_dark_soft,
    "--pokrov-text-muted": palette.text_dark_muted,
    "--pokrov-line": palette.line_dark,
    "--pokrov-line-strong": palette.line_dark_strong,
    "--pokrov-focus-ring": palette.focus_ring_dark,
    "--pokrov-status-green": palette.status_green_dark,
    "--pokrov-accent": component.button.background_dark,
    "--pokrov-accent-hover": component.button.background_dark_hover,
    "--pokrov-accent-contrast": component.button.text_dark,
    "--pokrov-accent-soft": semantic.success.bg_dark,
    "--pokrov-status-success-bg": semantic.success.bg_dark,
    "--pokrov-status-success-text": semantic.success.text_dark,
    "--pokrov-status-success-line": semantic.success.line_dark,
    "--pokrov-status-warning-bg": semantic.warning.bg_dark,
    "--pokrov-status-warning-text": semantic.warning.text_dark,
    "--pokrov-status-warning-line": semantic.warning.line_dark,
    "--pokrov-status-danger-bg": semantic.danger.bg_dark,
    "--pokrov-status-danger-text": semantic.danger.text_dark,
    "--pokrov-status-danger-line": semantic.danger.line_dark,
    "--pokrov-status-info-bg": semantic.info.bg_dark,
    "--pokrov-status-info-text": semantic.info.text_dark,
    "--pokrov-status-info-line": semantic.info.line_dark,
    "--pokrov-status-neutral-bg": semantic.neutral.bg_dark,
    "--pokrov-status-neutral-text": semantic.neutral.text_dark,
    "--pokrov-status-neutral-line": semantic.neutral.line_dark,
    "--pokrov-shadow-soft": shadow.soft_dark,
    "--pokrov-shadow-medium": shadow.medium_dark,
    "--pokrov-shadow-strong": shadow.strong_dark,
    "--pokrov-button-bg": component.button.background_dark,
    "--pokrov-button-bg-hover": component.button.background_dark_hover,
    "--pokrov-button-text": component.button.text_dark,
    "--pokrov-button-secondary-bg": component.button.secondary_background_dark,
    "--pokrov-button-border": component.button.border_dark,
    "--pokrov-nav-active-bg": component.nav.active_bg_dark,
    "--pokrov-nav-hover-bg": component.nav.hover_bg_dark,
    "--pokrov-nav-text": component.nav.text_dark,
    "--pokrov-card-bg": component.card.background_dark,
    "--pokrov-card-border": component.card.border_dark,
    "--pokrov-card-inner-edge": component.card.inner_edge_dark,
    "--pokrov-table-header-bg": component.table.header_bg_dark,
    "--pokrov-table-divider": component.table.divider_dark,
    "--pokrov-table-row-hover-bg": component.table.row_hover_bg_dark,
    "--pokrov-skeleton-base": component.skeleton.base_dark,
    "--pokrov-skeleton-highlight": component.skeleton.highlight_dark,
    "--pokrov-progress-track": component.progress.track_dark,
    "--pokrov-progress-fill": component.progress.fill_dark,
    "--pokrov-switch-on-bg": component.switch.on_background_dark,
    "--pokrov-switch-off-bg": component.switch.off_background_dark,
  };
}

function cssVariableBlock(variables: Record<string, string>): string {
  return Object.entries(variables)
    .map(([name, value]) => `${name}:${value};`)
    .join("");
}

/**
 * Full theme stylesheet: light values on `:root`, dark remap under both
 * `.dark` (webapp) and `[data-theme="dark"]` (marketing) roots.
 * Inject once per document as a `<style>` tag instead of inline `style`
 * attributes, otherwise the dark remap cannot cascade.
 */
export function getDesignTokenThemeCss(density: DesignDensityInput = "public"): string {
  const lightBlock = cssVariableBlock(getDesignTokenCssVariables(density));
  const darkBlock = cssVariableBlock(getDesignTokenDarkCssVariables());

  return [
    `:root{${lightBlock}color-scheme:light;}`,
    `:root.dark,:root[data-theme="dark"]{${darkBlock}color-scheme:dark;}`,
  ].join("\n");
}
