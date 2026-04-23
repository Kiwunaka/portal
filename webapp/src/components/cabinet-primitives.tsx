import type { ReactNode } from "react";

import { StatusBadge } from "./shell-primitives";
import { cn } from "./utils";

type HeroTone = "success" | "warning" | "danger" | "info" | "neutral";
type DetailTone = "emerald" | "amber" | "rose" | "slate";

const DETAIL_TONE_CLASSES: Record<DetailTone, string> = {
  emerald: "border-emerald-200/60 bg-emerald-50/80 dark:border-emerald-500/30 dark:bg-emerald-500/10",
  amber: "border-amber-200/60 bg-amber-50/80 dark:border-amber-500/30 dark:bg-amber-500/10",
  rose: "border-rose-200/60 bg-rose-50/80 dark:border-rose-500/30 dark:bg-rose-500/10",
  slate: "border-white/70 bg-white/72 dark:border-white/10 dark:bg-white/[0.04]",
};

type OperationalHeroProps = {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  status?: ReactNode;
  statusTone?: HeroTone;
  statusHint?: ReactNode;
  actions?: ReactNode;
  aside?: ReactNode;
  className?: string;
};

export function OperationalHero({
  eyebrow,
  title,
  description,
  status,
  statusTone = "info",
  statusHint,
  actions,
  aside,
  className,
}: OperationalHeroProps) {
  return (
    <section className={cn("glass-card p-7", className)}>
      <div className="grid gap-5 xl:grid-cols-[1.15fr,0.85fr]">
        <div className="min-w-0">
          {eyebrow ? (
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">{eyebrow}</p>
          ) : null}
          <h1 className="mt-2 font-display text-3xl font-semibold leading-[1.02] text-slate-900 dark:text-slate-50 sm:text-4xl">{title}</h1>
          {description ? <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600 dark:text-slate-300">{description}</p> : null}
          {actions ? <div className="mt-5 flex flex-wrap gap-3">{actions}</div> : null}
        </div>

        {(status || statusHint || aside) ? (
          <aside className="rounded-[1.6rem] border border-white/70 bg-white/72 p-5 dark:border-white/10 dark:bg-white/[0.04]">
            {status ? <StatusBadge tone={statusTone}>{status}</StatusBadge> : null}
            {statusHint ? <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{statusHint}</p> : null}
            {aside ? <div className={cn(status || statusHint ? "mt-4" : "")}>{aside}</div> : null}
          </aside>
        ) : null}
      </div>
    </section>
  );
}

type DetailCardItem = {
  label: ReactNode;
  value: ReactNode;
  hint?: ReactNode;
  tone?: DetailTone;
};

type DetailCardGridProps = {
  items: DetailCardItem[];
  className?: string;
};

export function DetailCardGrid({ items, className }: DetailCardGridProps) {
  return (
    <div className={cn("grid gap-3 md:grid-cols-2", className)}>
      {items.map((item, index) => (
        <article
          key={index}
          className={cn(
            "rounded-[1.35rem] border p-4 text-slate-900 dark:text-slate-50",
            DETAIL_TONE_CLASSES[item.tone || "slate"],
          )}
        >
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">{item.label}</p>
          <p className="mt-2 text-lg font-semibold leading-6">{item.value}</p>
          {item.hint ? <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.hint}</p> : null}
        </article>
      ))}
    </div>
  );
}

type SignalListItem = {
  title: ReactNode;
  body?: ReactNode;
  tone?: HeroTone;
  action?: ReactNode;
};

type SignalListProps = {
  items: SignalListItem[];
  className?: string;
};

export function SignalList({ items, className }: SignalListProps) {
  return (
    <div className={cn("space-y-3", className)}>
      {items.map((item, index) => (
        <article key={index} className="rounded-[1.35rem] border border-white/60 bg-white/65 p-4 dark:border-white/10 dark:bg-white/[0.04]">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <StatusBadge tone={item.tone || "neutral"}>{String(index + 1).padStart(2, "0")}</StatusBadge>
              <h3 className="mt-3 text-sm font-semibold text-slate-900 dark:text-slate-50">{item.title}</h3>
              {item.body ? <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.body}</p> : null}
            </div>
            {item.action ? <div className="shrink-0">{item.action}</div> : null}
          </div>
        </article>
      ))}
    </div>
  );
}
