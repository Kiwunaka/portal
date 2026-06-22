"use client";

import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/components/utils";

type AdminTone = "neutral" | "success" | "warning" | "danger" | "accent";
type AdminButtonTone = "primary" | "secondary" | "ghost" | "danger";
type AdminButtonSize = "sm" | "md" | "xs";

/*
 * Admin operator surface — token-driven (POKROV design tokens, light operator theme).
 * Colours come from the shared --pokrov-* variables applied on the admin <main>,
 * so every page that uses these factories shares one calm, on-brand palette.
 */

const PANEL_TONE_CLASSES: Record<AdminTone, string> = {
  neutral:
    "border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] text-[color:var(--atlas-text)] shadow-[var(--atlas-shadow-soft)]",
  success:
    "border-[color:var(--atlas-status-success-line)] bg-[color:var(--atlas-status-success-bg)] text-[color:var(--atlas-status-success-text)]",
  warning:
    "border-[color:var(--atlas-status-warning-line)] bg-[color:var(--atlas-status-warning-bg)] text-[color:var(--atlas-status-warning-text)]",
  danger:
    "border-[color:var(--atlas-status-danger-line)] bg-[color:var(--atlas-status-danger-bg)] text-[color:var(--atlas-status-danger-text)]",
  accent:
    "border-[color:var(--atlas-status-info-line)] bg-[color:var(--atlas-status-info-bg)] text-[color:var(--atlas-status-info-text)]",
};

const BUTTON_TONE_CLASSES: Record<AdminButtonTone, string> = {
  primary:
    "border border-transparent bg-[color:var(--atlas-primary)] text-[color:var(--atlas-primary-text)] hover:bg-[color:var(--atlas-primary-hover)]",
  secondary:
    "border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] text-[color:var(--atlas-text)] hover:border-[color:var(--atlas-border-strong)]",
  ghost:
    "border border-transparent bg-[color:var(--atlas-status-neutral-bg)] text-[color:var(--atlas-text-soft)] hover:text-[color:var(--atlas-text)]",
  danger:
    "border border-[color:var(--atlas-status-danger-line)] bg-[color:var(--atlas-status-danger-bg)] text-[color:var(--atlas-status-danger-text)] hover:brightness-[0.97]",
};

const BUTTON_SIZE_CLASSES: Record<AdminButtonSize, string> = {
  md: "min-h-10 rounded-[var(--pokrov-radius-control)] px-4 text-sm",
  sm: "min-h-9 rounded-[var(--pokrov-radius-control)] px-3 text-xs",
  xs: "min-h-8 rounded-[var(--pokrov-radius-control)] px-2.5 text-[11px]",
};

const TONE_SOFT_CLASSES: Record<AdminTone, string> = {
  neutral: "border-[color:var(--atlas-status-neutral-line)] bg-[color:var(--atlas-status-neutral-bg)] text-[color:var(--atlas-status-neutral-text)]",
  success: "border-[color:var(--atlas-status-success-line)] bg-[color:var(--atlas-status-success-bg)] text-[color:var(--atlas-status-success-text)]",
  warning: "border-[color:var(--atlas-status-warning-line)] bg-[color:var(--atlas-status-warning-bg)] text-[color:var(--atlas-status-warning-text)]",
  danger: "border-[color:var(--atlas-status-danger-line)] bg-[color:var(--atlas-status-danger-bg)] text-[color:var(--atlas-status-danger-text)]",
  accent: "border-[color:var(--atlas-status-info-line)] bg-[color:var(--atlas-status-info-bg)] text-[color:var(--atlas-status-info-text)]",
};

const EYEBROW_CLASS = "text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--atlas-text-muted)]";

export const adminShellFrameClass =
  "rounded-[var(--pokrov-radius-panel)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] text-[color:var(--atlas-text)] shadow-[var(--atlas-shadow-medium)]";

export const adminSidebarClass =
  "rounded-[var(--pokrov-radius-panel)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] text-[color:var(--atlas-text)] shadow-[var(--atlas-shadow-soft)]";

export const adminTopbarClass = adminSidebarClass;

export const adminRailCardClass =
  "rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-[var(--pokrov-card-padding)] text-[color:var(--atlas-text)] shadow-[var(--atlas-shadow-soft)]";

export function adminPanelClass(tone: AdminTone = "neutral"): string {
  return cn("overflow-hidden rounded-[var(--pokrov-radius-panel)] border p-[var(--pokrov-panel-padding)]", PANEL_TONE_CLASSES[tone]);
}

export const adminInsetPanelClass =
  "rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] p-[var(--pokrov-card-padding)]";

export const adminFieldClass =
  "min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] px-3 py-2 text-sm text-[color:var(--atlas-text)] outline-none transition placeholder:text-[color:var(--atlas-text-muted)] focus:border-[color:var(--atlas-focus)] focus:ring-2 focus:ring-[color:var(--atlas-focus)]/25";

export const adminTextAreaClass = cn(adminFieldClass, "min-h-[120px] resize-y py-3");

export const adminCheckboxLabelClass = "inline-flex items-center gap-2 text-[11px] font-medium text-[color:var(--atlas-text-soft)]";

export const adminTableShellClass =
  "overflow-hidden rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)]";

export const adminCompactCardClass =
  "rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] p-[var(--pokrov-card-padding)] text-[color:var(--atlas-text)]";

export function adminIconFrameClass(tone: AdminTone = "neutral"): string {
  return cn("inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--pokrov-radius-card)] border", TONE_SOFT_CLASSES[tone]);
}

export const adminProgressTrackClass = "h-2 overflow-hidden rounded-full bg-[color:var(--atlas-progress-track)]";

export function adminProgressFillClass(tone: AdminTone = "accent"): string {
  const palette: Record<AdminTone, string> = {
    neutral: "bg-[color:var(--atlas-text-muted)]",
    success: "bg-[color:var(--atlas-primary)]",
    warning: "bg-[color:var(--atlas-status-warning-text)]",
    danger: "bg-[color:var(--atlas-status-danger-text)]",
    accent: "bg-[color:var(--atlas-status-info-text)]",
  };

  return cn("h-full rounded-full", palette[tone]);
}

export function adminButtonClass(tone: AdminButtonTone = "secondary", size: AdminButtonSize = "md"): string {
  return cn(
    "inline-flex items-center justify-center gap-2 font-semibold transition active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-55",
    BUTTON_TONE_CLASSES[tone],
    BUTTON_SIZE_CLASSES[size],
  );
}

export function adminBadgeClass(tone: AdminTone = "neutral"): string {
  return cn("inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-semibold", TONE_SOFT_CLASSES[tone]);
}

export function AdminBadge({
  tone = "neutral",
  children,
  className,
}: {
  tone?: AdminTone;
  children: ReactNode;
  className?: string;
}) {
  return <span className={cn(adminBadgeClass(tone), className)}>{children}</span>;
}

export function AdminSurfaceHeader({
  title,
  description,
  actions,
  meta,
}: {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  meta?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
      <div className="min-w-0">
        <h1 className="text-[1.5rem] font-semibold leading-tight tracking-[-0.02em] text-[color:var(--atlas-text)]">{title}</h1>
        {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-[color:var(--atlas-text-soft)]">{description}</p> : null}
        {meta ? <div className="mt-3 flex flex-wrap gap-2">{meta}</div> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

export function AdminMetricStrip({
  items,
}: {
  items: Array<{
    label: ReactNode;
    value: ReactNode;
    hint?: ReactNode;
    tone?: AdminTone;
  }>;
}) {
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <article key={String(item.label)} className={cn(adminPanelClass(item.tone || "neutral"), "p-3.5")}>
          <p className={EYEBROW_CLASS}>{item.label}</p>
          <p className="mt-2 text-xl font-semibold leading-none text-[color:var(--atlas-text)]">{item.value}</p>
          {item.hint ? <p className="mt-2 text-xs leading-5 text-[color:var(--atlas-text-soft)]">{item.hint}</p> : null}
        </article>
      ))}
    </div>
  );
}

export function AdminPageHeader({
  eyebrow,
  title,
  description,
  actions,
  className,
}: {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between", className)}>
      <div className="min-w-0">
        {eyebrow ? <p className={EYEBROW_CLASS}>{eyebrow}</p> : null}
        <h1 className="mt-1 font-display text-[1.7rem] font-semibold leading-none tracking-[-0.02em] text-[color:var(--atlas-text)]">{title}</h1>
        {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-[color:var(--atlas-text-soft)]">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

export function AdminPanelHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
      <div className="min-w-0">
        {eyebrow ? <p className={EYEBROW_CLASS}>{eyebrow}</p> : null}
        <h2 className="mt-1 text-lg font-semibold text-[color:var(--atlas-text)]">{title}</h2>
        {description ? <p className="mt-1 max-w-3xl text-sm leading-6 text-[color:var(--atlas-text-soft)]">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

export function AdminKpiCard({
  label,
  value,
  hint,
  meta,
  tone = "neutral",
  className,
}: {
  label: ReactNode;
  value: ReactNode;
  hint?: ReactNode;
  meta?: ReactNode;
  tone?: AdminTone;
  className?: string;
}) {
  return (
    <article className={cn(adminPanelClass(tone), "p-4", className)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className={EYEBROW_CLASS}>{label}</p>
          <p className="mt-2 text-2xl font-semibold leading-none text-[color:var(--atlas-text)]">{value}</p>
        </div>
        {meta ? <div className="shrink-0 text-right text-[11px] text-[color:var(--atlas-text-soft)]">{meta}</div> : null}
      </div>
      {hint ? <p className="mt-2 text-xs leading-5 text-[color:var(--atlas-text-soft)]">{hint}</p> : null}
    </article>
  );
}

export function AdminInlineNote({
  tone = "neutral",
  children,
  className,
}: HTMLAttributes<HTMLDivElement> & { tone?: AdminTone }) {
  return (
    <div className={cn(adminPanelClass(tone), "p-3 text-sm leading-6", className)}>
      {children}
    </div>
  );
}

export function AdminEmptyState({
  title,
  description,
  className,
}: {
  title: ReactNode;
  description?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn(adminPanelClass("neutral"), "flex min-h-[160px] flex-col items-center justify-center gap-2 border-dashed text-center", className)}>
      <p className="text-sm font-semibold text-[color:var(--atlas-text)]">{title}</p>
      {description ? <p className="max-w-md text-xs leading-5 text-[color:var(--atlas-text-soft)]">{description}</p> : null}
    </div>
  );
}
