"use client";

import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/components/utils";

type AdminTone = "neutral" | "success" | "warning" | "danger" | "accent";
type AdminButtonTone = "primary" | "secondary" | "ghost" | "danger";
type AdminButtonSize = "sm" | "md" | "xs";

const PANEL_TONE_CLASSES: Record<AdminTone, string> = {
  neutral: "border-[#b8ded1] bg-white text-slate-900 shadow-[0_18px_42px_-34px_rgba(10,92,67,0.34)]",
  success: "border-emerald-200 bg-emerald-50 text-emerald-950 shadow-[0_18px_42px_-34px_rgba(10,92,67,0.34)]",
  warning: "border-amber-200 bg-amber-50 text-amber-950 shadow-[0_18px_42px_-34px_rgba(146,64,14,0.22)]",
  danger: "border-rose-300 bg-rose-50 text-rose-950 shadow-[0_18px_42px_-34px_rgba(159,18,57,0.22)]",
  accent: "border-teal-200 bg-teal-50 text-teal-950 shadow-[0_18px_42px_-34px_rgba(15,118,110,0.24)]",
};

const BUTTON_TONE_CLASSES: Record<AdminButtonTone, string> = {
  primary:
    "border border-emerald-700 bg-emerald-700 !text-white hover:border-emerald-800 hover:bg-emerald-800",
  secondary:
    "border border-[#99cdbb] bg-white text-emerald-950 hover:border-[#68ad94] hover:bg-emerald-50",
  ghost:
    "border border-transparent bg-emerald-50 text-emerald-950 hover:bg-emerald-100",
  danger:
    "border border-rose-300 bg-rose-50 text-rose-800 hover:bg-rose-100",
};

const BUTTON_SIZE_CLASSES: Record<AdminButtonSize, string> = {
  md: "min-h-10 rounded-xl px-4 text-sm",
  sm: "min-h-9 rounded-lg px-3 text-xs",
  xs: "min-h-8 rounded-lg px-2.5 text-[11px]",
};

export const adminShellFrameClass =
  "rounded-[1.3rem] border border-[#b8ded1] bg-[#f2fbf7] text-slate-900 shadow-[0_36px_80px_-54px_rgba(10,92,67,0.34)] [&_.text-slate-50]:text-slate-950 [&_.text-slate-100]:text-slate-900 [&_.text-slate-200]:text-slate-800 [&_.text-slate-300]:text-slate-700 [&_.text-slate-400]:text-slate-600 [&_.text-slate-500]:text-slate-500";

export const adminSidebarClass =
  "rounded-[1.25rem] border border-[#b8ded1] bg-[#e8f7f0] text-slate-900 shadow-[0_24px_60px_-44px_rgba(10,92,67,0.3)]";

export const adminTopbarClass =
  "rounded-[1.15rem] border border-[#b8ded1] bg-white text-slate-900 shadow-[0_22px_48px_-38px_rgba(10,92,67,0.24)]";

export const adminRailCardClass =
  "rounded-[1rem] border border-[#b8ded1] bg-white p-4 text-slate-900 shadow-[0_18px_36px_-32px_rgba(10,92,67,0.24)]";

export function adminPanelClass(tone: AdminTone = "neutral"): string {
  return cn("overflow-hidden rounded-[1.05rem] border p-4", PANEL_TONE_CLASSES[tone]);
}

export const adminInsetPanelClass =
  "rounded-[0.75rem] border border-[#c6e6db] bg-[#f8fffc] p-3";

export const adminFieldClass =
  "min-h-10 w-full rounded-[0.75rem] border border-[#b8ded1] bg-white px-3 py-2 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-[#2f8f70] focus:ring-2 focus:ring-emerald-200";

export const adminTextAreaClass = cn(adminFieldClass, "min-h-[120px] resize-y py-3");

export const adminCheckboxLabelClass = "inline-flex items-center gap-2 text-[11px] font-medium text-slate-600";

export const adminTableShellClass =
  "overflow-hidden rounded-[0.85rem] border border-[#b8ded1] bg-white";

export function adminButtonClass(tone: AdminButtonTone = "secondary", size: AdminButtonSize = "md"): string {
  return cn(
    "inline-flex items-center justify-center gap-2 font-semibold tracking-[0.01em] transition disabled:cursor-not-allowed disabled:opacity-55",
    BUTTON_TONE_CLASSES[tone],
    BUTTON_SIZE_CLASSES[size],
  );
}

export function adminBadgeClass(tone: AdminTone = "neutral"): string {
  const palette: Record<AdminTone, string> = {
    neutral: "border-[#b8ded1] bg-white text-slate-700",
    success: "border-emerald-200 bg-emerald-50 text-emerald-800",
    warning: "border-amber-200 bg-amber-50 text-amber-800",
    danger: "border-rose-200 bg-rose-50 text-rose-800",
    accent: "border-teal-200 bg-teal-50 text-teal-800",
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
    <div className={cn(adminPanelClass("neutral"), "flex min-h-[160px] flex-col items-center justify-center gap-2 border-dashed border-[#b8ded1] text-center", className)}>
      <p className="text-sm font-semibold text-slate-100">{title}</p>
      {description ? <p className="max-w-md text-xs leading-5 text-slate-400">{description}</p> : null}
    </div>
  );
}

export function AdminConfirmDialog({
  open,
  title,
  description,
  reason,
  onReasonChange,
  onCancel,
  onConfirm,
  confirmLabel = "Подтвердить",
  cancelLabel = "Отмена",
  busy = false,
  danger = false,
  minReasonLength = 8,
  children,
}: {
  open: boolean;
  title: ReactNode;
  description?: ReactNode;
  reason: string;
  onReasonChange: (value: string) => void;
  onCancel: () => void;
  onConfirm: () => void;
  confirmLabel?: ReactNode;
  cancelLabel?: ReactNode;
  busy?: boolean;
  danger?: boolean;
  minReasonLength?: number;
  children?: ReactNode;
}) {
  if (!open) return null;
  const reasonOk = reason.trim().length >= minReasonLength;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4">
      <div className="w-full max-w-lg rounded-[1rem] border border-[#b8ded1] bg-white p-5 text-slate-900 shadow-[0_28px_70px_-40px_rgba(10,92,67,0.45)]">
        <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
        {description ? <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p> : null}
        {children ? <div className="mt-4">{children}</div> : null}
        <label className="mt-4 block text-xs font-semibold uppercase tracking-[0.14em] text-slate-500" htmlFor="admin-confirm-reason">
          Причина
        </label>
        <textarea
          id="admin-confirm-reason"
          className={`${adminTextAreaClass} mt-2 min-h-[88px]`}
          value={reason}
          onChange={(event) => onReasonChange(event.target.value)}
          placeholder="Например: обращение пользователя, плановое окно, номер инцидента"
        />
        <p className={reasonOk ? "mt-2 text-xs text-emerald-700" : "mt-2 text-xs text-amber-700"}>
          Укажите причину минимум {minReasonLength} символов.
        </p>
        <div className="mt-5 flex flex-wrap justify-end gap-2">
          <button type="button" className={adminButtonClass("ghost", "sm")} onClick={onCancel} disabled={busy}>
            {cancelLabel}
          </button>
          <button
            type="button"
            className={adminButtonClass(danger ? "danger" : "primary", "sm")}
            onClick={onConfirm}
            disabled={busy || !reasonOk}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
