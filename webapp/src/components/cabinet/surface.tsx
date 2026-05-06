"use client";

import type { ReactNode } from "react";

import { StatusBadge } from "@/components/atlas";
import { cn } from "@/components/utils";
import { DoubleBezel } from "@/components/ui/double-bezel";
import { FadeUp } from "@/components/ui/fade-up";

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
  tone?: CabinetTone;
  action?: ReactNode;
};

export type CabinetDetail = {
  label: ReactNode;
  value: ReactNode;
  hint?: ReactNode;
  tone?: CabinetTone;
};

const LABEL_CLASS = "text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400";
const TEXT_SOFT = "text-slate-600 dark:text-slate-300";

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
      <FadeUp delay={0.1}>
        <div className="px-1 py-2 sm:px-2">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0">
              {eyebrow ? <p className={LABEL_CLASS}>{eyebrow}</p> : null}
              <h1 className="mt-2 font-display text-[clamp(1.7rem,2.4vw,2.35rem)] font-semibold leading-[1.05] tracking-[-0.03em] text-slate-950 dark:text-slate-50">
                {title}
              </h1>
              {description ? <p className={cn("mt-3 max-w-3xl text-sm leading-relaxed", TEXT_SOFT)}>{description}</p> : null}
            </div>
            {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
          </div>
        </div>
      </FadeUp>

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
    <FadeUp delay={0.2} className={cn("grid gap-4 md:grid-cols-2 xl:grid-cols-4", className)}>
      {items.map((item, index) => (
        <DoubleBezel
          key={String(item.label) + index}
          tone={item.tone === "neutral" ? "default" : item.tone}
          innerClassName="px-5 py-5"
        >
          <p className={LABEL_CLASS}>{item.label}</p>
          <div className="mt-3 font-mono text-[1.4rem] font-semibold tracking-tight text-slate-900 dark:text-slate-50">
            {item.value}
          </div>
          {item.hint ? <p className={cn("mt-2 text-[13px] leading-relaxed", TEXT_SOFT)}>{item.hint}</p> : null}
        </DoubleBezel>
      ))}
    </FadeUp>
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
    <FadeUp delay={0.3} className={className}>
      <DoubleBezel tone="default" innerClassName="p-6 sm:p-8">
        <div className="grid gap-8 xl:grid-cols-[1.16fr_0.84fr]">
          <div className="min-w-0">
            {eyebrow ? <p className={LABEL_CLASS}>{eyebrow}</p> : null}
            {badge ? <StatusBadge tone={badgeTone} className={eyebrow ? "mt-4" : ""}>{badge}</StatusBadge> : null}
            <h2 className="mt-4 font-display text-[clamp(2rem,3vw,3rem)] font-semibold leading-[1.05] tracking-[-0.03em] text-slate-950 dark:text-slate-50">
              {title}
            </h2>
            {description ? <p className={cn("mt-4 max-w-3xl text-[15px] leading-relaxed", TEXT_SOFT)}>{description}</p> : null}
            {actions ? <div className="mt-6 flex flex-wrap gap-4">{actions}</div> : null}
          </div>

          {details?.length ? (
            <aside className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
              {details.map((detail, index) => (
                <div
                  key={index}
                  className="rounded-[1.3rem] border border-slate-200/50 bg-slate-50/50 p-5 dark:border-white/5 dark:bg-white/[0.02]"
                >
                  <p className={LABEL_CLASS}>{detail.label}</p>
                  <p className="mt-2 text-lg font-semibold tracking-tight text-slate-900 dark:text-slate-50">
                    {detail.value}
                  </p>
                  {detail.hint ? <p className={cn("mt-2 text-[13px] leading-relaxed", TEXT_SOFT)}>{detail.hint}</p> : null}
                </div>
              ))}
            </aside>
          ) : null}
        </div>

        {footer ? <div className="mt-8 border-t border-slate-200/50 pt-6 dark:border-white/10">{footer}</div> : null}
      </DoubleBezel>
    </FadeUp>
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
    <FadeUp delay={0.4} as="section" className={className}>
      <DoubleBezel tone={tone === "neutral" ? "default" : tone} innerClassName="p-6 sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            {eyebrow ? <p className={LABEL_CLASS}>{eyebrow}</p> : null}
            <h2 className="mt-3 font-display text-[1.65rem] font-semibold leading-[1.05] tracking-[-0.03em] text-slate-950 dark:text-slate-50">
              {title}
            </h2>
            {description ? <p className={cn("mt-3 max-w-3xl text-[15px] leading-relaxed", TEXT_SOFT)}>{description}</p> : null}
          </div>
          {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
        </div>

        <div className="mt-6">{children}</div>
      </DoubleBezel>
    </FadeUp>
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
      <div className={cn("rounded-[1.2rem] border border-dashed border-slate-200 bg-slate-50 px-5 py-6 text-sm leading-relaxed text-slate-500 dark:border-white/10 dark:bg-white/[0.02] dark:text-slate-400", className)}>
        {empty}
      </div>
    ) : null;
  }

  return (
    <div className={cn("space-y-4", className)}>
      {items.map((item, index) => (
        <article key={item.key} className="group relative overflow-hidden rounded-[1.4rem] border border-slate-200/50 bg-slate-50/50 px-5 py-5 transition-colors hover:bg-emerald-50/50 hover:border-emerald-200/50 dark:border-white/5 dark:bg-white/[0.02] dark:hover:bg-white/[0.04] dark:hover:border-white/10">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-3">
                <StatusBadge tone={item.tone || "neutral"}>{item.badge || String(index + 1).padStart(2, "0")}</StatusBadge>
                <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">{item.title}</h3>
              </div>
              {item.body ? <p className={cn("mt-3 text-[14px] leading-relaxed", TEXT_SOFT)}>{item.body}</p> : null}
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
    <div className={cn("grid gap-4 md:grid-cols-2 xl:grid-cols-3", className)}>
      {items.map((item) => (
        <article
          key={item.key}
          className="group flex min-h-[12rem] flex-col overflow-hidden rounded-[1.6rem] border border-slate-200/60 bg-white p-5 transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] hover:-translate-y-1 hover:shadow-[0_20px_40px_-20px_rgba(15,23,42,0.1)] dark:border-white/10 dark:bg-[#101713] dark:hover:shadow-[0_20px_40px_-20px_rgba(0,0,0,0.5)]"
        >
          <StatusBadge tone={item.tone || "neutral"}>{item.badge || "Далее"}</StatusBadge>
          <h3 className="mt-4 text-[15px] font-semibold text-slate-950 dark:text-slate-50">{item.title}</h3>
          {item.body ? <p className={cn("mt-3 flex-1 text-[14px] leading-relaxed", TEXT_SOFT)}>{item.body}</p> : null}
          {item.action ? <div className="mt-5">{item.action}</div> : null}
        </article>
      ))}
    </div>
  );
}
