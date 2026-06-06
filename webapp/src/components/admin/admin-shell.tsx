"use client";

import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/components/utils";

type AdminTone = "neutral" | "success" | "warning" | "danger" | "accent";
type AdminButtonTone = "primary" | "secondary" | "ghost" | "danger";
type AdminButtonSize = "sm" | "md" | "xs";

const PANEL_TONE_CLASSES: Record<AdminTone, string> = {
  neutral: "border-slate-200/60 bg-white/80 text-slate-800 shadow-[0_18px_40px_-32px_rgba(15,23,42,0.08)]",
  success: "border-emerald-200/50 bg-emerald-50/40 text-emerald-900 shadow-[0_18px_40px_-32px_rgba(5,46,22,0.08)]",
  warning: "border-amber-200/50 bg-amber-50/40 text-amber-900 shadow-[0_18px_40px_-32px_rgba(69,26,3,0.08)]",
  danger: "border-rose-200/50 bg-rose-50/40 text-rose-900 shadow-[0_18px_40px_-32px_rgba(76,5,25,0.08)]",
  accent: "border-sky-200/50 bg-sky-50/40 text-sky-900 shadow-[0_18px_40px_-32px_rgba(7,23,48,0.08)]",
};

const BUTTON_TONE_CLASSES: Record<AdminButtonTone, string> = {
  primary:
    "border border-emerald-700 bg-emerald-700 text-white hover:bg-emerald-800 hover:border-emerald-800",
  secondary:
    "border border-slate-200 bg-white text-slate-800 hover:border-slate-300 hover:bg-slate-50",
  ghost:
    "border border-transparent bg-slate-100 text-slate-700 hover:bg-slate-200 hover:text-slate-900",
  danger:
    "border border-rose-300 bg-rose-50 text-rose-700 hover:bg-rose-100 hover:text-rose-800",
};

const BUTTON_SIZE_CLASSES: Record<AdminButtonSize, string> = {
  md: "min-h-10 rounded-xl px-4 text-sm",
  sm: "min-h-9 rounded-lg px-3 text-xs",
  xs: "min-h-8 rounded-lg px-2.5 text-[11px]",
};

export const adminShellFrameClass =
  "rounded-xl border border-slate-200/60 bg-slate-50/60 text-slate-800 shadow-[0_28px_64px_-52px_rgba(15,23,42,0.10)]";

export const adminSidebarClass =
  "rounded-xl border border-slate-200/60 bg-white/80 text-slate-800 shadow-[0_20px_52px_-44px_rgba(15,23,42,0.10)] backdrop-blur-xl";

export const adminTopbarClass =
  "rounded-xl border border-slate-200/60 bg-white/80 text-slate-800 shadow-[0_18px_42px_-38px_rgba(15,23,42,0.08)] backdrop-blur-xl";

export const adminRailCardClass =
  "rounded-lg border border-slate-200/60 bg-white/70 p-3 text-slate-800 shadow-[0_14px_30px_-28px_rgba(15,23,42,0.08)] backdrop-blur-xl";

export function adminPanelClass(tone: AdminTone = "neutral"): string {
  return cn("overflow-hidden rounded-xl border p-3.5 backdrop-blur-sm", PANEL_TONE_CLASSES[tone]);
}

export const adminInsetPanelClass =
  "rounded-lg border border-slate-200/50 bg-white/60 p-3 backdrop-blur-sm";

export const adminFieldClass =
  "min-h-10 w-full rounded-[0.9rem] border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-200/30";

export const adminTextAreaClass = cn(adminFieldClass, "min-h-[120px] resize-y py-3");

export const adminCheckboxLabelClass = "inline-flex items-center gap-2 text-[11px] font-medium text-slate-500";

export const adminTableShellClass =
  "overflow-hidden rounded-lg border border-slate-200/60 bg-white/80 backdrop-blur-sm";

export const adminCompactCardClass =
  "rounded-lg border border-slate-200/50 bg-white/60 p-3 text-slate-800 backdrop-blur-sm";

export function adminIconFrameClass(tone: AdminTone = "neutral"): string {
  const palette: Record<AdminTone, string> = {
    neutral: "border-slate-200 bg-slate-100 text-slate-600",
    success: "border-emerald-200 bg-emerald-100 text-emerald-700",
    warning: "border-amber-200 bg-amber-100 text-amber-700",
    danger: "border-rose-200 bg-rose-100 text-rose-700",
    accent: "border-sky-200 bg-sky-100 text-sky-700",
  };

  return cn("inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border", palette[tone]);
}

export const adminProgressTrackClass = "h-2 overflow-hidden rounded-full bg-slate-200";

export function adminProgressFillClass(tone: AdminTone = "accent"): string {
  const palette: Record<AdminTone, string> = {
    neutral: "bg-slate-400",
    success: "bg-emerald-500",
    warning: "bg-amber-500",
    danger: "bg-rose-500",
    accent: "bg-sky-500",
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
    neutral: "border-slate-200 bg-slate-100 text-slate-600",
    success: "border-emerald-200 bg-emerald-100 text-emerald-700",
    warning: "border-amber-200 bg-amber-100 text-amber-700",
    danger: "border-rose-200 bg-rose-100 text-rose-700",
    accent: "border-sky-200 bg-sky-100 text-sky-700",
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
        <h1 className="text-[1.52rem] font-semibold leading-tight tracking-[-0.04em] text-slate-900">{title}</h1>
        {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">{description}</p> : null}
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
          <p className="mt-2 text-xl font-semibold leading-none text-slate-900">{item.value}</p>
          {item.hint ? <p className="mt-2 text-xs leading-5 text-slate-500">{item.hint}</p> : null}
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
        <h1 className="mt-1 font-display text-[1.78rem] font-semibold leading-none text-slate-900">{title}</h1>
        {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">{description}</p> : null}
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
        <h2 className="mt-1 text-lg font-semibold text-slate-900">{title}</h2>
        {description ? <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-500">{description}</p> : null}
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
          <p className="mt-2 text-2xl font-semibold leading-none text-slate-900">{value}</p>
        </div>
        {meta ? <div className="shrink-0 text-right text-[11px] text-slate-500">{meta}</div> : null}
      </div>
      {hint ? <p className="mt-2 text-xs leading-5 text-slate-500">{hint}</p> : null}
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
    <div className={cn(adminPanelClass("neutral"), "flex min-h-[160px] flex-col items-center justify-center gap-2 border-dashed border-slate-300 text-center", className)}>
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      {description ? <p className="max-w-md text-xs leading-5 text-slate-500">{description}</p> : null}
    </div>
  );
}
