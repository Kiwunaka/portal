"use client";

import type { ReactNode } from "react";

import { StatusBadge } from "@/components/shell-primitives";
import { cn } from "@/components/utils";

export type CabinetTone = "success" | "warning" | "danger" | "info" | "neutral";

export type CabinetMetric = {
  label: ReactNode;
  value: ReactNode;
  hint?: ReactNode;
  tone?: CabinetTone;
};

export type CabinetListItem = {
  key: string;
  title: ReactNode;
  body?: ReactNode;
  badge?: ReactNode;
  icon?: ReactNode;
  tone?: CabinetTone;
  action?: ReactNode;
};

export type CabinetDetail = {
  label: ReactNode;
  value: ReactNode;
  hint?: ReactNode;
  tone?: CabinetTone;
};

const PANEL_TONE_CLASSES: Record<CabinetTone, string> = {
  success: "border-emerald-200/70 bg-emerald-50/90 dark:border-emerald-400/25 dark:bg-emerald-400/10",
  warning: "border-amber-200/70 bg-amber-50/90 dark:border-amber-400/25 dark:bg-amber-400/10",
  danger: "border-rose-200/70 bg-rose-50/90 dark:border-rose-400/25 dark:bg-rose-400/10",
  info: "border-teal-200/70 bg-teal-50/90 dark:border-teal-400/25 dark:bg-teal-400/10",
  neutral: "border-slate-200/80 bg-white/88 dark:border-emerald-300/12 dark:bg-[#132019]/82",
};

const SUBTLE_TONE_CLASSES: Record<CabinetTone, string> = {
  success: "border-emerald-200/70 bg-emerald-50/85 dark:border-emerald-400/25 dark:bg-emerald-400/10",
  warning: "border-amber-200/70 bg-amber-50/85 dark:border-amber-400/25 dark:bg-amber-400/10",
  danger: "border-rose-200/70 bg-rose-50/85 dark:border-rose-400/25 dark:bg-rose-400/10",
  info: "border-teal-200/70 bg-teal-50/85 dark:border-teal-400/25 dark:bg-teal-400/10",
  neutral: "border-slate-200/80 bg-white/82 dark:border-emerald-300/12 dark:bg-emerald-50/[0.045]",
};

const ICON_TONE_CLASSES: Record<CabinetTone, string> = {
  success: "bg-emerald-700 text-white shadow-emerald-900/10 dark:bg-emerald-500 dark:text-emerald-950",
  warning: "bg-amber-500 text-amber-950 shadow-amber-900/10 dark:bg-amber-300",
  danger: "bg-rose-600 text-white shadow-rose-900/10 dark:bg-rose-400 dark:text-rose-950",
  info: "bg-teal-600 text-white shadow-teal-900/10 dark:bg-teal-300 dark:text-teal-950",
  neutral: "bg-slate-900 text-white shadow-slate-900/10 dark:bg-white/12 dark:text-slate-100",
};

const EMPTY_ICON_CLASSES =
  "grid h-12 w-12 place-items-center rounded-2xl bg-emerald-700 text-white shadow-[0_18px_36px_-26px_rgba(4,120,87,0.45)] dark:bg-emerald-400 dark:text-emerald-950";

type CabinetRouteProps = {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  metrics?: CabinetMetric[];
  children: ReactNode;
};

export function CabinetRoute({ eyebrow, title, description, actions, metrics, children }: CabinetRouteProps) {
  return (
    <main className="space-y-6">
      <section className="rounded-2xl border border-slate-200/80 bg-white/86 px-5 py-4 shadow-[0_16px_45px_-40px_rgba(15,23,42,0.18)] dark:border-emerald-300/12 dark:bg-[#132019]/82 sm:px-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            {eyebrow ? (
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">{eyebrow}</p>
            ) : null}
            <h1 className="mt-2 font-display text-[clamp(1.7rem,2.4vw,2.35rem)] font-semibold leading-[0.96] tracking-[-0.04em] text-slate-950 dark:text-slate-50">
              {title}
            </h1>
            {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">{description}</p> : null}
          </div>
          {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
        </div>
      </section>

      {metrics?.length ? <CabinetKpiRow items={metrics} /> : null}

      {children}
    </main>
  );
}

type CabinetKpiRowProps = {
  items: CabinetMetric[];
  className?: string;
};

export function CabinetKpiRow({ items, className }: CabinetKpiRowProps) {
  return (
    <div className={cn("grid gap-3 md:grid-cols-2 xl:grid-cols-4", className)}>
      {items.map((item) => (
        <article
          key={String(item.label)}
          className={cn("rounded-xl border px-4 py-4 text-slate-950 shadow-[0_14px_36px_-34px_rgba(15,23,42,0.14)] dark:text-slate-50", SUBTLE_TONE_CLASSES[item.tone || "neutral"])}
        >
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">{item.label}</p>
          <p className="mt-2 text-xl font-semibold leading-6">{item.value}</p>
          {item.hint ? <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.hint}</p> : null}
        </article>
      ))}
    </div>
  );
}

type CabinetHeroProps = {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  badge?: ReactNode;
  badgeTone?: CabinetTone;
  actions?: ReactNode;
  details?: CabinetDetail[];
  footer?: ReactNode;
  className?: string;
};

export function CabinetHero({
  eyebrow,
  title,
  description,
  badge,
  badgeTone = "neutral",
  actions,
  details,
  footer,
  className,
}: CabinetHeroProps) {
  return (
    <section
      className={cn(
        "rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-[0_18px_60px_-48px_rgba(15,23,42,0.2)] dark:border-emerald-300/12 dark:bg-[#132019]/86 sm:p-6",
        className,
      )}
    >
      <div className="grid gap-5 xl:grid-cols-[1.16fr_0.84fr]">
        <div className="min-w-0">
          {eyebrow ? (
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">{eyebrow}</p>
          ) : null}
          {badge ? <StatusBadge tone={badgeTone} className={eyebrow ? "mt-3" : ""}>{badge}</StatusBadge> : null}
          <h2 className="mt-3 font-display text-[clamp(2rem,3vw,3rem)] font-semibold leading-[0.95] tracking-[-0.05em] text-slate-950 dark:text-slate-50">
            {title}
          </h2>
          {description ? <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600 dark:text-slate-300">{description}</p> : null}
          {actions ? <div className="mt-5 flex flex-wrap gap-3">{actions}</div> : null}
        </div>

        {details?.length ? (
          <aside className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            {details.map((detail, index) => (
              <article
                key={index}
                className={cn(
                  "rounded-xl border px-4 py-4 text-slate-950 dark:text-slate-50",
                  SUBTLE_TONE_CLASSES[detail.tone || "neutral"],
                )}
              >
                <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">{detail.label}</p>
                <p className="mt-2 text-lg font-semibold leading-6">{detail.value}</p>
                {detail.hint ? <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{detail.hint}</p> : null}
              </article>
            ))}
          </aside>
        ) : null}
      </div>

      {footer ? <div className="mt-5 border-t border-slate-200/80 pt-5 dark:border-white/10">{footer}</div> : null}
    </section>
  );
}

type CabinetSectionProps = {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  tone?: CabinetTone;
};

export function CabinetSection({ eyebrow, title, description, actions, children, className, tone = "neutral" }: CabinetSectionProps) {
  return (
    <section
      className={cn(
        "rounded-2xl border p-5 shadow-none sm:p-6",
        PANEL_TONE_CLASSES[tone],
        className,
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          {eyebrow ? (
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">{eyebrow}</p>
          ) : null}
          <h2 className="mt-2 font-display text-[1.55rem] font-semibold leading-[1] tracking-[-0.03em] text-slate-950 dark:text-slate-50">
            {title}
          </h2>
          {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">{description}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
      </div>

      <div className="mt-5">{children}</div>
    </section>
  );
}

type CabinetListProps = {
  items: CabinetListItem[];
  empty?: ReactNode;
  className?: string;
};

export function CabinetList({ items, empty, className }: CabinetListProps) {
  if (!items.length) {
    return empty ? (
      <div
        className={cn(
          "rounded-[1.35rem] border border-dashed border-emerald-200/80 bg-emerald-50/45 px-4 py-5 text-sm leading-6 text-slate-600 dark:border-emerald-300/18 dark:bg-emerald-400/[0.055] dark:text-slate-300",
          className,
        )}
      >
        <div className="flex items-start gap-4">
          <span className={EMPTY_ICON_CLASSES}>
            <span className="material-symbols-rounded text-[23px]">add_task</span>
          </span>
          <div className="min-w-0">
            <p className="text-base font-semibold leading-6 text-slate-950 dark:text-slate-50">Пока здесь пусто</p>
            <div className="mt-1">{empty}</div>
          </div>
        </div>
      </div>
    ) : null;
  }

  return (
    <div className={cn("space-y-3", className)}>
      {items.map((item, index) => (
        <article
          key={item.key}
          className={cn(
            "rounded-[1.35rem] border px-4 py-4 shadow-[0_16px_42px_-38px_rgba(15,23,42,0.18)] transition hover:-translate-y-0.5 hover:shadow-[0_24px_54px_-42px_rgba(15,23,42,0.26)]",
            SUBTLE_TONE_CLASSES[item.tone || "neutral"],
          )}
        >
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex min-w-0 flex-1 items-start gap-3">
              <span
                className={cn(
                  "grid h-11 w-11 shrink-0 place-items-center rounded-2xl text-sm font-semibold shadow-lg",
                  ICON_TONE_CLASSES[item.tone || "neutral"],
                )}
                aria-hidden="true"
              >
                {item.icon || String(index + 1).padStart(2, "0")}
              </span>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge tone={item.tone || "neutral"}>{item.badge || "Статус"}</StatusBadge>
                  <h3 className="text-sm font-semibold text-slate-950 dark:text-slate-50">{item.title}</h3>
                </div>
                {item.body ? <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.body}</p> : null}
              </div>
            </div>
            {item.action ? <div className="shrink-0">{item.action}</div> : null}
          </div>
        </article>
      ))}
    </div>
  );
}

type CabinetCardGridProps = {
  items: CabinetListItem[];
  className?: string;
};

export function CabinetCardGrid({ items, className }: CabinetCardGridProps) {
  return (
    <div className={cn("grid gap-3 md:grid-cols-2 xl:grid-cols-3", className)}>
      {items.map((item) => (
        <article
          key={item.key}
          className={cn(
            "rounded-[1.35rem] border px-4 py-4 shadow-[0_16px_42px_-38px_rgba(15,23,42,0.18)] transition hover:-translate-y-0.5 hover:shadow-[0_24px_54px_-42px_rgba(15,23,42,0.26)]",
            SUBTLE_TONE_CLASSES[item.tone || "neutral"],
          )}
        >
          <div className="flex items-start justify-between gap-3">
            <StatusBadge tone={item.tone || "neutral"}>{item.badge || "Далее"}</StatusBadge>
            {item.icon ? (
              <span className={cn("grid h-10 w-10 shrink-0 place-items-center rounded-2xl shadow-lg", ICON_TONE_CLASSES[item.tone || "neutral"])} aria-hidden="true">
                {item.icon}
              </span>
            ) : null}
          </div>
          <h3 className="mt-3 text-sm font-semibold text-slate-950 dark:text-slate-50">{item.title}</h3>
          {item.body ? <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.body}</p> : null}
          {item.action ? <div className="mt-4">{item.action}</div> : null}
        </article>
      ))}
    </div>
  );
}
