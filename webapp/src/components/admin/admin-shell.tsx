"use client";

import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/components/utils";

type AdminTone = "neutral" | "success" | "warning" | "danger" | "accent";
type AdminButtonTone = "primary" | "secondary" | "ghost" | "danger";
type AdminButtonSize = "sm" | "md" | "xs";

const PANEL_TONE_CLASSES: Record<AdminTone, string> = {
  neutral: "border-[#1e2a35] bg-[#0d141b] text-slate-200 shadow-[0_18px_40px_-32px_rgba(2,6,23,0.92)]",
  success: "border-emerald-900/60 bg-[rgba(7,32,24,0.95)] text-emerald-100 shadow-[0_18px_40px_-32px_rgba(5,46,22,0.9)]",
  warning: "border-amber-900/60 bg-[rgba(41,26,8,0.95)] text-amber-100 shadow-[0_18px_40px_-32px_rgba(69,26,3,0.9)]",
  danger: "border-rose-950/65 bg-[rgba(44,12,21,0.95)] text-rose-100 shadow-[0_18px_40px_-32px_rgba(76,5,25,0.92)]",
  accent: "border-sky-900/60 bg-[rgba(10,28,45,0.95)] text-sky-100 shadow-[0_18px_40px_-32px_rgba(7,23,48,0.92)]",
};

const BUTTON_TONE_CLASSES: Record<AdminButtonTone, string> = {
  primary:
    "border border-slate-100 bg-slate-100 text-slate-950 hover:bg-white hover:text-slate-950",
  secondary:
    "border border-[#2a3945] bg-[#111922] text-slate-100 hover:border-[#364958] hover:bg-[#16212b]",
  ghost:
    "border border-transparent bg-[#16212b] text-slate-300 hover:bg-[#1b2934] hover:text-slate-100",
  danger:
    "border border-rose-900/60 bg-rose-950/40 text-rose-200 hover:bg-rose-900/35 hover:text-rose-100",
};

const BUTTON_SIZE_CLASSES: Record<AdminButtonSize, string> = {
  md: "min-h-10 rounded-xl px-4 text-sm",
  sm: "min-h-9 rounded-lg px-3 text-xs",
  xs: "min-h-8 rounded-lg px-2.5 text-[11px]",
};

export const adminShellFrameClass =
  "rounded-[1.3rem] border border-[#17212b] bg-[#070d13] text-slate-200 shadow-[0_36px_80px_-54px_rgba(2,6,23,0.95)]";

export const adminSidebarClass =
  "rounded-[1.25rem] border border-[#17212b] bg-[#0a1117] text-slate-200 shadow-[0_24px_60px_-44px_rgba(2,6,23,0.95)]";

export const adminTopbarClass =
  "rounded-[1.15rem] border border-[#1b2732] bg-[#0c131a] text-slate-200 shadow-[0_22px_48px_-38px_rgba(2,6,23,0.92)]";

export const adminRailCardClass =
  "rounded-[1rem] border border-[#202d38] bg-[#101821] p-4 text-slate-200 shadow-[0_18px_36px_-32px_rgba(2,6,23,0.88)]";

export function adminPanelClass(tone: AdminTone = "neutral"): string {
  return cn("overflow-hidden rounded-[1.05rem] border p-4", PANEL_TONE_CLASSES[tone]);
}

export const adminInsetPanelClass =
  "rounded-[0.95rem] border border-[#24313d] bg-[#111922] p-3";

export const adminFieldClass =
  "min-h-10 w-full rounded-[0.9rem] border border-[#24313d] bg-[#0a1117] px-3 py-2 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-[#4d6375] focus:ring-2 focus:ring-slate-200/5";

export const adminTextAreaClass = cn(adminFieldClass, "min-h-[120px] resize-y py-3");

export const adminCheckboxLabelClass = "inline-flex items-center gap-2 text-[11px] font-medium text-slate-400";

export const adminTableShellClass =
  "overflow-hidden rounded-[1rem] border border-[#22303c] bg-[#0b1218]";

export const adminCompactCardClass =
  "rounded-[0.9rem] border border-[#24313d] bg-[#111922] p-3 text-slate-200";

export function adminIconFrameClass(tone: AdminTone = "neutral"): string {
  const palette: Record<AdminTone, string> = {
    neutral: "border-[#2c3b47] bg-[#141d25] text-slate-300",
    success: "border-emerald-900/65 bg-emerald-950/45 text-emerald-200",
    warning: "border-amber-900/65 bg-amber-950/45 text-amber-200",
    danger: "border-rose-900/65 bg-rose-950/45 text-rose-200",
    accent: "border-sky-900/65 bg-sky-950/45 text-sky-200",
  };

  return cn("inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-[0.8rem] border", palette[tone]);
}

export const adminProgressTrackClass = "h-2 overflow-hidden rounded-full bg-slate-800";

export function adminProgressFillClass(tone: AdminTone = "accent"): string {
  const palette: Record<AdminTone, string> = {
    neutral: "bg-slate-400",
    success: "bg-emerald-400",
    warning: "bg-amber-400",
    danger: "bg-rose-400",
    accent: "bg-sky-400",
  };

  return cn("h-full rounded-full", palette[tone]);
}

export function adminButtonClass(tone: AdminButtonTone = "secondary", size: AdminButtonSize = "md"): string {
  return cn(
    "inline-flex items-center justify-center gap-2 font-semibold tracking-[0.01em] transition disabled:cursor-not-allowed disabled:opacity-55",
    BUTTON_TONE_CLASSES[tone],
    BUTTON_SIZE_CLASSES[size],
  );
}

export function adminBadgeClass(tone: AdminTone = "neutral"): string {
  const palette: Record<AdminTone, string> = {
    neutral: "border-[#2c3b47] bg-[#141d25] text-slate-300",
    success: "border-emerald-900/70 bg-emerald-950/45 text-emerald-200",
    warning: "border-amber-900/70 bg-amber-950/45 text-amber-200",
    danger: "border-rose-900/70 bg-rose-950/45 text-rose-200",
    accent: "border-sky-900/70 bg-sky-950/45 text-sky-200",
  };

  return cn("inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-semibold", palette[tone]);
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
        <h1 className="text-[1.52rem] font-semibold leading-tight tracking-[-0.04em] text-slate-50">{title}</h1>
        {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">{description}</p> : null}
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
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">{item.label}</p>
          <p className="mt-2 text-xl font-semibold leading-none text-slate-50">{item.value}</p>
          {item.hint ? <p className="mt-2 text-xs leading-5 text-slate-400">{item.hint}</p> : null}
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
        {eyebrow ? <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">{eyebrow}</p> : null}
        <h1 className="mt-1 font-display text-[1.78rem] font-semibold leading-none text-slate-50">{title}</h1>
        {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">{description}</p> : null}
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
        {eyebrow ? <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">{eyebrow}</p> : null}
        <h2 className="mt-1 text-lg font-semibold text-slate-50">{title}</h2>
        {description ? <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-400">{description}</p> : null}
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
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</p>
          <p className="mt-2 text-2xl font-semibold leading-none text-slate-50">{value}</p>
        </div>
        {meta ? <div className="shrink-0 text-right text-[11px] text-slate-500">{meta}</div> : null}
      </div>
      {hint ? <p className="mt-2 text-xs leading-5 text-slate-400">{hint}</p> : null}
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
    <div className={cn(adminPanelClass("neutral"), "flex min-h-[160px] flex-col items-center justify-center gap-2 border-dashed border-[#2a3945] text-center", className)}>
      <p className="text-sm font-semibold text-slate-100">{title}</p>
      {description ? <p className="max-w-md text-xs leading-5 text-slate-400">{description}</p> : null}
    </div>
  );
}
