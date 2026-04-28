"use client";

import type { ReactNode } from "react";

import { StatusBadge } from "@/components/atlas";
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
  success: "border-[color:var(--atlas-status-success-line)] bg-[var(--atlas-status-success-bg)]",
  warning: "border-[color:var(--atlas-status-warning-line)] bg-[var(--atlas-status-warning-bg)]",
  danger: "border-[color:var(--atlas-status-danger-line)] bg-[var(--atlas-status-danger-bg)]",
  info: "border-[color:var(--atlas-status-info-line)] bg-[var(--atlas-status-info-bg)]",
  neutral: "border-[color:var(--atlas-border)] bg-[var(--atlas-glass)]",
};

const SUBTLE_TONE_CLASSES: Record<CabinetTone, string> = {
  success: "border-[color:var(--atlas-status-success-line)] bg-[var(--atlas-status-success-bg)]",
  warning: "border-[color:var(--atlas-status-warning-line)] bg-[var(--atlas-status-warning-bg)]",
  danger: "border-[color:var(--atlas-status-danger-line)] bg-[var(--atlas-status-danger-bg)]",
  info: "border-[color:var(--atlas-status-info-line)] bg-[var(--atlas-status-info-bg)]",
  neutral: "border-[color:var(--atlas-border)] bg-[var(--atlas-surface)]",
};

const PANEL_BASE =
  "border text-[var(--atlas-text)] backdrop-blur-[var(--pokrov-glass-max-blur,16px)] [box-shadow:var(--atlas-shadow-soft),var(--atlas-inner-edge)]";
const LABEL_CLASS = "text-xs font-semibold leading-5 text-[var(--atlas-text-muted)]";
const TEXT_SOFT = "text-[var(--atlas-text-soft)]";
const FOCUS_CLASS =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--atlas-focus)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--atlas-canvas)]";

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
      <section className={cn(PANEL_BASE, "rounded-[var(--pokrov-radius-panel,1rem)] border-[color:var(--atlas-border)] bg-[var(--atlas-glass)] px-5 py-4 sm:px-6")}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            {eyebrow ? (
              <p className={LABEL_CLASS}>{eyebrow}</p>
            ) : null}
            <h1 className="mt-2 font-display text-[clamp(1.7rem,2.4vw,2.35rem)] font-semibold leading-tight text-[var(--atlas-text)]">
              {title}
            </h1>
            {description ? <p className={cn("mt-2 max-w-3xl text-sm leading-6", TEXT_SOFT)}>{description}</p> : null}
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
          className={cn(PANEL_BASE, "rounded-[var(--pokrov-radius-card,0.875rem)] px-4 py-4", SUBTLE_TONE_CLASSES[item.tone || "neutral"])}
        >
          <p className={LABEL_CLASS}>{item.label}</p>
          <p className="mt-2 font-mono text-xl font-semibold leading-6 text-[var(--atlas-text)]">{item.value}</p>
          {item.hint ? <p className={cn("mt-2 text-sm leading-6", TEXT_SOFT)}>{item.hint}</p> : null}
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
        PANEL_BASE,
        "rounded-[var(--pokrov-radius-panel,1rem)] border-[color:var(--atlas-border)] bg-[var(--atlas-glass)] p-5 sm:p-6",
        className,
      )}
    >
      <div className="grid gap-5 xl:grid-cols-[1.16fr_0.84fr]">
        <div className="min-w-0">
          {eyebrow ? (
            <p className={LABEL_CLASS}>{eyebrow}</p>
          ) : null}
          {badge ? <StatusBadge tone={badgeTone} className={eyebrow ? "mt-3" : ""}>{badge}</StatusBadge> : null}
          <h2 className="mt-3 font-display text-[clamp(2rem,3vw,3rem)] font-semibold leading-tight text-[var(--atlas-text)]">
            {title}
          </h2>
          {description ? <p className={cn("mt-3 max-w-3xl text-sm leading-7", TEXT_SOFT)}>{description}</p> : null}
          {actions ? <div className="mt-5 flex flex-wrap gap-3">{actions}</div> : null}
        </div>

        {details?.length ? (
          <aside className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            {details.map((detail, index) => (
              <article
                key={index}
                className={cn(
                  PANEL_BASE,
                  "rounded-[var(--pokrov-radius-card,0.875rem)] px-4 py-4",
                  SUBTLE_TONE_CLASSES[detail.tone || "neutral"],
                )}
              >
                <p className={LABEL_CLASS}>{detail.label}</p>
                <p className="mt-2 text-lg font-semibold leading-6 text-[var(--atlas-text)]">{detail.value}</p>
                {detail.hint ? <p className={cn("mt-2 text-sm leading-6", TEXT_SOFT)}>{detail.hint}</p> : null}
              </article>
            ))}
          </aside>
        ) : null}
      </div>

      {footer ? <div className="mt-5 border-t border-[color:var(--atlas-border)] pt-5">{footer}</div> : null}
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
        PANEL_BASE,
        "rounded-[var(--pokrov-radius-panel,1rem)] p-5 sm:p-6",
        PANEL_TONE_CLASSES[tone],
        className,
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          {eyebrow ? (
            <p className={LABEL_CLASS}>{eyebrow}</p>
          ) : null}
          <h2 className="mt-2 font-display text-[1.55rem] font-semibold leading-tight text-[var(--atlas-text)]">
            {title}
          </h2>
          {description ? <p className={cn("mt-2 max-w-3xl text-sm leading-6", TEXT_SOFT)}>{description}</p> : null}
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
      <div className={cn("rounded-[var(--pokrov-radius-card,0.875rem)] border border-dashed border-[color:var(--atlas-border)] bg-[var(--atlas-glass)] px-4 py-4 text-sm leading-6 text-[var(--atlas-text-soft)]", className)}>
        {empty}
      </div>
    ) : null;
  }

  return (
    <div className={cn("space-y-3", className)}>
      {items.map((item, index) => (
        <article key={item.key} className={cn(PANEL_BASE, "rounded-[var(--pokrov-radius-card,0.875rem)] px-4 py-4", SUBTLE_TONE_CLASSES[item.tone || "neutral"])}>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge tone={item.tone || "neutral"}>{item.badge || String(index + 1).padStart(2, "0")}</StatusBadge>
                <h3 className="text-sm font-semibold text-[var(--atlas-text)]">{item.title}</h3>
              </div>
              {item.body ? <p className={cn("mt-2 text-sm leading-6", TEXT_SOFT)}>{item.body}</p> : null}
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
            PANEL_BASE,
            FOCUS_CLASS,
            "flex min-h-44 flex-col rounded-[var(--pokrov-radius-card,0.875rem)] px-4 py-4 transition duration-[var(--pokrov-duration-base,180ms)] motion-safe:hover:-translate-y-0.5",
            SUBTLE_TONE_CLASSES[item.tone || "neutral"],
          )}
        >
          <StatusBadge tone={item.tone || "neutral"}>{item.badge || "Далее"}</StatusBadge>
          <h3 className="mt-3 text-sm font-semibold text-[var(--atlas-text)]">{item.title}</h3>
          {item.body ? <p className={cn("mt-2 text-sm leading-6", TEXT_SOFT)}>{item.body}</p> : null}
          {item.action ? <div className="mt-4">{item.action}</div> : null}
        </article>
      ))}
    </div>
  );
}
