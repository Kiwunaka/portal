"use client";

import type { AnchorHTMLAttributes, ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";
import { createElement, forwardRef } from "react";

import { cn, FOCUS_RING } from "./utils";

type SurfaceProps = HTMLAttributes<HTMLElement> & {
  as?: "div" | "section" | "article" | "aside" | "main";
};

export const Surface = forwardRef<HTMLElement, SurfaceProps>(function Surface(
  { as: Tag = "div", className, ...props },
  ref,
) {
  return createElement(Tag, {
    ref,
    className: cn("glass-card", className),
    ...props,
  });
});

type StatusTone = "success" | "warning" | "danger" | "info" | "neutral";

const STATUS_TONE_CLASSES: Record<StatusTone, string> = {
  success: "badge-success",
  warning: "badge-warning",
  danger: "badge-danger",
  info: "badge-info",
  neutral: "badge-violet",
};

type StatusBadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: StatusTone;
};

export function StatusBadge({ className, tone = "info", ...props }: StatusBadgeProps) {
  return <span className={cn("badge", STATUS_TONE_CLASSES[tone], className)} {...props} />;
}

type SectionHeaderProps = {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
};

export function SectionHeader({ eyebrow, title, description, actions, className }: SectionHeaderProps) {
  return (
    <div className={cn("flex flex-wrap items-start justify-between gap-4", className)}>
      <div className="min-w-0">
        {eyebrow ? <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[color:var(--atlas-text-soft)] dark:text-slate-400">{eyebrow}</p> : null}
        <h1 className="mt-2 font-display text-3xl font-semibold leading-[1.02] text-[color:var(--atlas-text)] dark:text-slate-50 sm:text-4xl">{title}</h1>
        {description ? <p className="mt-3 max-w-3xl text-sm leading-7 text-[color:var(--atlas-text-soft)] dark:text-slate-300">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

type MetricCardProps = {
  label: ReactNode;
  value: ReactNode;
  hint?: ReactNode;
  tone?: "emerald" | "amber" | "rose" | "slate";
};

const METRIC_TONE_CLASSES: Record<NonNullable<MetricCardProps["tone"]>, string> = {
  emerald: "border-[color:var(--atlas-status-success-line)] bg-[color:var(--atlas-status-success-bg)] text-[color:var(--atlas-status-success-text)] dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200",
  amber: "border-[color:var(--atlas-status-warning-line)] bg-[color:var(--atlas-status-warning-bg)] text-[color:var(--atlas-status-warning-text)] dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200",
  rose: "border-[color:var(--atlas-status-danger-line)] bg-[color:var(--atlas-status-danger-bg)] text-[color:var(--atlas-status-danger-text)] dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200",
  slate: "border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] text-[color:var(--atlas-text-soft)] dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200",
};

export function MetricCard({ label, value, hint, tone = "slate" }: MetricCardProps) {
  return (
    <article className={cn("stat-card overflow-hidden rounded-[1.2rem] p-4", METRIC_TONE_CLASSES[tone])}>
      <p className="text-[11px] uppercase tracking-[0.16em] text-[color:var(--atlas-text-soft)] dark:text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-semibold leading-none text-[color:var(--atlas-text)] dark:text-slate-50">{value}</p>
      {hint ? <p className="mt-2 text-[11px] leading-5 text-[color:var(--atlas-text-soft)] dark:text-slate-400">{hint}</p> : null}
    </article>
  );
}

type DialogShellProps = {
  title?: ReactNode;
  description?: ReactNode;
  eyebrow?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function DialogShell({ title, description, eyebrow, actions, children, className }: DialogShellProps) {
  return (
    <Surface className={cn("w-full overflow-hidden border border-[color:var(--atlas-border)] p-6 dark:border-[#243129]/80 sm:p-8", className)}>
      {(title || description) ? (
        <div className="mb-6">
          <SectionHeader eyebrow={eyebrow} title={title || ""} description={description} actions={actions} />
        </div>
      ) : eyebrow || actions ? (
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          {eyebrow ? <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[color:var(--atlas-text-soft)] dark:text-slate-400">{eyebrow}</p> : null}
          {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
        </div>
      ) : null}
      {children}
    </Surface>
  );
}

type FormFieldProps = {
  label: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  required?: boolean;
  className?: string;
  children: ReactNode;
};

export function FormField({ label, hint, error, required, className, children }: FormFieldProps) {
  return (
    <label className={cn("block space-y-2", className)}>
      <span className="block text-sm font-medium text-[color:var(--atlas-text-soft)] dark:text-slate-200">
        {label}
        {required ? <span className="ml-1 text-[color:var(--atlas-status-danger-text)]">*</span> : null}
      </span>
      {children}
      {hint ? <span className="block text-xs leading-5 text-[color:var(--atlas-text-soft)] dark:text-slate-400">{hint}</span> : null}
      {error ? <span className="block text-xs leading-5 text-[color:var(--atlas-status-danger-text)]">{error}</span> : null}
    </label>
  );
}

type EmptyStateProps = {
  icon: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
};

export function EmptyState({ icon, title, description, actions, className }: EmptyStateProps) {
  return (
    <div className={cn("empty-state rounded-[1.75rem] border border-dashed border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] dark:border-white/10 dark:bg-white/[0.03]", className)}>
      <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-900/10 text-[color:var(--atlas-status-success-text)] dark:bg-emerald-200/10 dark:text-emerald-200">
        {icon}
      </div>
      <h2 className="mt-4 font-display text-2xl font-semibold text-[color:var(--atlas-text)] dark:text-slate-50">{title}</h2>
      {description ? <p className="mt-2 max-w-xl text-sm leading-7 text-[color:var(--atlas-text-soft)] dark:text-slate-300">{description}</p> : null}
      {actions ? <div className="mt-5 flex flex-wrap justify-center gap-3">{actions}</div> : null}
    </div>
  );
}

type TimelineItem = {
  title: ReactNode;
  description?: ReactNode;
  tone?: StatusTone;
};

type TimelineProps = {
  items: TimelineItem[];
  className?: string;
};

export function Timeline({ items, className }: TimelineProps) {
  return (
    <ol className={cn("space-y-3", className)}>
      {items.map((item, index) => (
        <li key={index} className="flex gap-3 rounded-[1.15rem] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-4 dark:border-white/10 dark:bg-white/[0.04]">
          <StatusBadge tone={item.tone || "neutral"} className="mt-0.5 shrink-0">
            {String(index + 1).padStart(2, "0")}
          </StatusBadge>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-[color:var(--atlas-text)] dark:text-slate-50">{item.title}</p>
            {item.description ? <p className="mt-1 text-sm leading-6 text-[color:var(--atlas-text-soft)] dark:text-slate-300">{item.description}</p> : null}
          </div>
        </li>
      ))}
    </ol>
  );
}

type ShellButtonProps = ButtonHTMLAttributes<HTMLButtonElement>;
type ShellLinkProps = AnchorHTMLAttributes<HTMLAnchorElement>;

export const shellButtonClass = cn(
  FOCUS_RING,
  "inline-flex items-center justify-center gap-2 rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] transition",
  "disabled:cursor-not-allowed disabled:opacity-60",
);

export const shellLinkClass = cn(
  FOCUS_RING,
  "inline-flex items-center justify-center gap-2 rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] transition",
);

export function shellButtonProps<T extends ShellButtonProps>(props: T): T {
  return props;
}

export function shellLinkProps<T extends ShellLinkProps>(props: T): T {
  return props;
}
