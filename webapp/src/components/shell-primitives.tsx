"use client";

import type { HTMLAttributes, ReactNode } from "react";
import { createElement, forwardRef } from "react";

import { Badge, type Tone } from "./cabinet/ui";
import { cn } from "./utils";

type SurfaceProps = HTMLAttributes<HTMLElement> & {
  as?: "div" | "section" | "article" | "aside" | "main";
};

const Surface = forwardRef<HTMLElement, SurfaceProps>(function Surface(
  { as: Tag = "div", className, ...props },
  ref,
) {
  return createElement(Tag, {
    ref,
    className: cn("glass-card", className),
    ...props,
  });
});

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
        {eyebrow ? <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[color:var(--atlas-text-soft)]">{eyebrow}</p> : null}
        <h1 className="mt-2 font-display text-3xl font-semibold leading-[1.02] text-[color:var(--atlas-text)] sm:text-4xl">{title}</h1>
        {description ? <p className="mt-3 max-w-3xl text-sm leading-7 text-[color:var(--atlas-text-soft)]">{description}</p> : null}
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
  emerald: "border-[color:var(--atlas-status-success-line)] bg-[color:var(--atlas-status-success-bg)] text-[color:var(--atlas-status-success-text)]",
  amber: "border-[color:var(--atlas-status-warning-line)] bg-[color:var(--atlas-status-warning-bg)] text-[color:var(--atlas-status-warning-text)]",
  rose: "border-[color:var(--atlas-status-danger-line)] bg-[color:var(--atlas-status-danger-bg)] text-[color:var(--atlas-status-danger-text)]",
  slate: "border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] text-[color:var(--atlas-text-soft)]",
};

export function MetricCard({ label, value, hint, tone = "slate" }: MetricCardProps) {
  return (
    <article className={cn("stat-card overflow-hidden rounded-[1.2rem] p-4", METRIC_TONE_CLASSES[tone])}>
      <p className="text-[11px] uppercase tracking-[0.16em] text-[color:var(--atlas-text-soft)]">{label}</p>
      <p className="mt-2 text-2xl font-semibold leading-none text-[color:var(--atlas-text)]">{value}</p>
      {hint ? <p className="mt-2 text-[11px] leading-5 text-[color:var(--atlas-text-soft)]">{hint}</p> : null}
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
    <Surface className={cn("w-full overflow-hidden p-6 sm:p-8", className)}>
      {(title || description) ? (
        <div className="mb-6">
          <SectionHeader eyebrow={eyebrow} title={title || ""} description={description} actions={actions} />
        </div>
      ) : eyebrow || actions ? (
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          {eyebrow ? <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[color:var(--atlas-text-soft)]">{eyebrow}</p> : null}
          {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
        </div>
      ) : null}
      {children}
    </Surface>
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
    <div className={cn("empty-state rounded-[1.75rem] border border-dashed border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)]", className)}>
      <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-[color:var(--atlas-status-success-bg)] text-[color:var(--atlas-status-success-text)]">
        {icon}
      </div>
      <h2 className="mt-4 font-display text-2xl font-semibold text-[color:var(--atlas-text)]">{title}</h2>
      {description ? <p className="mt-2 max-w-xl text-sm leading-7 text-[color:var(--atlas-text-soft)]">{description}</p> : null}
      {actions ? <div className="mt-5 flex flex-wrap justify-center gap-3">{actions}</div> : null}
    </div>
  );
}

type TimelineItem = {
  title: ReactNode;
  description?: ReactNode;
  tone?: Tone;
};

type TimelineProps = {
  items: TimelineItem[];
  className?: string;
};

export function Timeline({ items, className }: TimelineProps) {
  return (
    <ol className={cn("space-y-3", className)}>
      {items.map((item, index) => (
        <li key={index} className="flex gap-3 rounded-[1.15rem] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-4">
          <Badge tone={item.tone || "neutral"} className="mt-0.5 shrink-0">
            {String(index + 1).padStart(2, "0")}
          </Badge>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-[color:var(--atlas-text)]">{item.title}</p>
            {item.description ? <p className="mt-1 text-sm leading-6 text-[color:var(--atlas-text-soft)]">{item.description}</p> : null}
          </div>
        </li>
      ))}
    </ol>
  );
}
