import type { ReactNode } from "react";

import { StatusBadge } from "@/components/shell-primitives";
import { cn } from "@/components/utils";

type Tone = "success" | "warning" | "danger" | "info" | "neutral";

type CabinetPageProps = {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
};

type CabinetSectionProps = {
  title: ReactNode;
  description?: ReactNode;
  eyebrow?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
};

type CabinetFact = {
  label: ReactNode;
  value: ReactNode;
  hint?: ReactNode;
  tone?: Tone;
};

type CabinetFactGridProps = {
  facts: CabinetFact[];
  className?: string;
};

type CabinetActionItem = {
  key: string;
  title: ReactNode;
  body?: ReactNode;
  badge?: ReactNode;
  tone?: Tone;
  action?: ReactNode;
};

type CabinetActionListProps = {
  items: CabinetActionItem[];
  empty?: ReactNode;
  className?: string;
};

const FACT_TONE_CLASSES: Record<Tone, string> = {
  success: "border-emerald-200/70 bg-emerald-50/90 dark:border-emerald-400/25 dark:bg-emerald-400/10",
  warning: "border-amber-200/70 bg-amber-50/90 dark:border-amber-400/25 dark:bg-amber-400/10",
  danger: "border-rose-200/70 bg-rose-50/90 dark:border-rose-400/25 dark:bg-rose-400/10",
  info: "border-sky-200/70 bg-sky-50/90 dark:border-sky-400/25 dark:bg-sky-400/10",
  neutral: "border-slate-200/80 bg-slate-50/85 dark:border-white/10 dark:bg-white/[0.04]",
};

export function CabinetPage({ eyebrow, title, description, actions, children }: CabinetPageProps) {
  return (
    <main className="space-y-6">
      <section className="rounded-[1.75rem] border border-slate-200/80 bg-white/90 px-5 py-5 shadow-[0_24px_60px_-44px_rgba(15,23,42,0.2)] dark:border-white/10 dark:bg-[#101713]/88 sm:px-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 space-y-2">
            {eyebrow ? (
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">{eyebrow}</p>
            ) : null}
            <h1 className="font-display text-[clamp(1.9rem,3vw,2.75rem)] font-semibold leading-[0.96] tracking-[-0.04em] text-slate-950 dark:text-slate-50">
              {title}
            </h1>
            {description ? <p className="max-w-3xl text-sm leading-7 text-slate-600 dark:text-slate-300">{description}</p> : null}
          </div>
          {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
        </div>
      </section>

      {children}
    </main>
  );
}

export function CabinetSection({ title, description, eyebrow, actions, children, className }: CabinetSectionProps) {
  return (
    <section
      className={cn(
        "rounded-[1.6rem] border border-slate-200/80 bg-white/90 p-5 shadow-[0_24px_60px_-44px_rgba(15,23,42,0.16)] dark:border-white/10 dark:bg-[#101713]/88 sm:p-6",
        className,
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 space-y-2">
          {eyebrow ? (
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">{eyebrow}</p>
          ) : null}
          <h2 className="font-display text-[1.6rem] font-semibold leading-[1] tracking-[-0.03em] text-slate-950 dark:text-slate-50">
            {title}
          </h2>
          {description ? <p className="max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">{description}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
      </div>

      <div className="mt-5">{children}</div>
    </section>
  );
}

export function CabinetFactGrid({ facts, className }: CabinetFactGridProps) {
  return (
    <div className={cn("grid gap-3 md:grid-cols-2 xl:grid-cols-4", className)}>
      {facts.map((fact) => (
        <article
          key={String(fact.label)}
          className={cn("rounded-[1.2rem] border px-4 py-4 text-slate-950 dark:text-slate-50", FACT_TONE_CLASSES[fact.tone || "neutral"])}
        >
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">{fact.label}</p>
          <p className="mt-2 text-lg font-semibold leading-6">{fact.value}</p>
          {fact.hint ? <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{fact.hint}</p> : null}
        </article>
      ))}
    </div>
  );
}

export function CabinetActionList({ items, empty, className }: CabinetActionListProps) {
  if (!items.length) {
    return empty ? (
      <div className={cn("rounded-[1.3rem] border border-dashed border-slate-200/80 px-4 py-4 text-sm leading-6 text-slate-500 dark:border-white/10 dark:text-slate-400", className)}>
        {empty}
      </div>
    ) : null;
  }

  return (
    <div className={cn("space-y-3", className)}>
      {items.map((item, index) => (
        <article key={item.key} className="rounded-[1.3rem] border border-slate-200/80 bg-slate-50/90 px-4 py-4 dark:border-white/10 dark:bg-white/[0.04]">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge tone={item.tone || "neutral"}>{item.badge || String(index + 1).padStart(2, "0")}</StatusBadge>
                <h3 className="text-sm font-semibold text-slate-950 dark:text-slate-50">{item.title}</h3>
              </div>
              {item.body ? <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.body}</p> : null}
            </div>
            {item.action ? <div className="shrink-0">{item.action}</div> : null}
          </div>
        </article>
      ))}
    </div>
  );
}
