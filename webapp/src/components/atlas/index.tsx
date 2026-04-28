import type { HTMLAttributes, ReactNode } from "react";
import { AlertTriangle, Inbox } from "lucide-react";

import { cn } from "../utils";

type AtlasTone = "success" | "warning" | "danger" | "info" | "neutral";
type AtlasSurfaceElement = "div" | "section" | "article" | "aside" | "main" | "header";

type SurfaceProps = HTMLAttributes<HTMLElement> & {
  as?: AtlasSurfaceElement;
  bleed?: boolean;
};

const surfaceClass =
  "border border-[color:var(--atlas-border)] bg-[var(--atlas-surface)] text-[var(--atlas-text)] [box-shadow:var(--atlas-shadow-soft)]";
const glassClass =
  "border border-[color:var(--atlas-border)] bg-[var(--atlas-glass)] text-[var(--atlas-text)] backdrop-blur-[var(--pokrov-glass-max-blur,16px)] [box-shadow:var(--atlas-shadow-soft),var(--atlas-inner-edge)]";
const focusClass =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--atlas-focus)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--atlas-canvas)]";

const statusToneClass: Record<AtlasTone, string> = {
  success:
    "border-[color:var(--atlas-status-success-line)] bg-[var(--atlas-status-success-bg)] text-[var(--atlas-status-success-text)]",
  warning:
    "border-[color:var(--atlas-status-warning-line)] bg-[var(--atlas-status-warning-bg)] text-[var(--atlas-status-warning-text)]",
  danger:
    "border-[color:var(--atlas-status-danger-line)] bg-[var(--atlas-status-danger-bg)] text-[var(--atlas-status-danger-text)]",
  info:
    "border-[color:var(--atlas-status-info-line)] bg-[var(--atlas-status-info-bg)] text-[var(--atlas-status-info-text)]",
  neutral:
    "border-[color:var(--atlas-status-neutral-line)] bg-[var(--atlas-status-neutral-bg)] text-[var(--atlas-status-neutral-text)]",
};

const progressToneClass: Record<Exclude<AtlasTone, "info" | "neutral"> | "primary", string> = {
  primary: "bg-[image:var(--atlas-progress-fill)]",
  success: "bg-[image:var(--atlas-progress-fill)]",
  warning: "bg-[image:var(--atlas-progress-warning-fill)]",
  danger: "bg-[image:var(--atlas-progress-danger-fill)]",
};

export function Surface({ as: Tag = "section", bleed = false, className, ...props }: SurfaceProps) {
  return (
    <Tag
      className={cn(
        surfaceClass,
        bleed ? "rounded-none" : "rounded-[var(--pokrov-radius-panel,1rem)]",
        "p-[var(--pokrov-panel-padding,1.25rem)]",
        className,
      )}
      {...props}
    />
  );
}

export function GlassPanel({ as: Tag = "section", bleed = false, className, ...props }: SurfaceProps) {
  return (
    <Tag
      className={cn(
        glassClass,
        bleed ? "rounded-none" : "rounded-[var(--pokrov-radius-panel,1rem)]",
        "p-[var(--pokrov-panel-padding,1.25rem)]",
        className,
      )}
      {...props}
    />
  );
}

export function BentoCard({ as: Tag = "article", className, ...props }: SurfaceProps) {
  return (
    <Tag
      className={cn(
        glassClass,
        "min-w-0 rounded-[var(--pokrov-radius-card,0.875rem)] p-[var(--pokrov-card-padding,1rem)] transition duration-[var(--pokrov-duration-base,180ms)] motion-safe:hover:-translate-y-0.5",
        className,
      )}
      {...props}
    />
  );
}

type MetricTileProps = HTMLAttributes<HTMLElement> & {
  label: ReactNode;
  value: ReactNode;
  hint?: ReactNode;
  tone?: AtlasTone;
};

export function MetricTile({ label, value, hint, tone = "neutral", className, ...props }: MetricTileProps) {
  return (
    <article
      className={cn(
        "min-w-0 rounded-[var(--pokrov-radius-card,0.875rem)] border bg-[var(--atlas-surface)] p-[var(--pokrov-card-padding,1rem)] [box-shadow:var(--atlas-shadow-soft)]",
        statusToneClass[tone],
        className,
      )}
      {...props}
    >
      <p className="text-[0.72rem] font-semibold uppercase leading-5 tracking-[0.08em] text-[var(--atlas-text-muted)]">{label}</p>
      <p className="mt-2 font-mono text-2xl font-semibold leading-none text-[var(--atlas-text)]">{value}</p>
      {hint ? <p className="mt-2 text-sm leading-6 text-[var(--atlas-text-soft)]">{hint}</p> : null}
    </article>
  );
}

type ActionCardProps = HTMLAttributes<HTMLElement> & {
  icon?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  tone?: AtlasTone;
};

export function ActionCard({ icon, title, description, action, tone = "info", className, ...props }: ActionCardProps) {
  const interactive = Boolean(props.onClick || props.role === "button" || props.tabIndex !== undefined);

  return (
    <article
      {...props}
      className={cn(
        glassClass,
        focusClass,
        "grid min-w-0 gap-4 rounded-[var(--pokrov-radius-card,0.875rem)] p-[var(--pokrov-card-padding,1rem)] transition active:scale-[0.99]",
        className,
      )}
      tabIndex={interactive ? props.tabIndex ?? 0 : undefined}
    >
      <div className="flex items-start gap-3">
        {icon ? (
          <span className={cn("grid h-11 w-11 shrink-0 place-items-center rounded-2xl border", statusToneClass[tone])}>
            {icon}
          </span>
        ) : null}
        <div className="min-w-0">
          <h3 className="text-base font-semibold leading-6 text-[var(--atlas-text)]">{title}</h3>
          {description ? <p className="mt-1 text-sm leading-6 text-[var(--atlas-text-soft)]">{description}</p> : null}
        </div>
      </div>
      {action ? <div className="flex flex-wrap gap-2">{action}</div> : null}
    </article>
  );
}

type StatusBadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: AtlasTone;
};

export function StatusBadge({ tone = "neutral", className, ...props }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex min-h-7 items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold leading-none",
        statusToneClass[tone],
        className,
      )}
      {...props}
    />
  );
}

type ProgressMeterProps = HTMLAttributes<HTMLDivElement> & {
  value: number;
  max?: number;
  label?: ReactNode;
  tone?: "primary" | "success" | "warning" | "danger";
};

export function ProgressMeter({ value, max = 100, label, tone = "primary", className, ...props }: ProgressMeterProps) {
  const normalizedMax = max > 0 ? max : 100;
  const percent = Math.min(100, Math.max(0, (value / normalizedMax) * 100));

  return (
    <div className={cn("grid gap-2", className)} {...props}>
      {label ? <div className="text-sm font-medium leading-5 text-[var(--atlas-text-soft)]">{label}</div> : null}
      <div
        className="h-2 overflow-hidden rounded-full bg-[var(--atlas-progress-track)]"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={normalizedMax}
        aria-valuenow={Math.min(normalizedMax, Math.max(0, value))}
      >
        <div className={cn("h-full rounded-full transition-[width] duration-300", progressToneClass[tone])} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

type SkeletonBlockProps = HTMLAttributes<HTMLDivElement> & {
  lines?: number;
};

export function SkeletonBlock({ lines, className, ...props }: SkeletonBlockProps) {
  if (lines && lines > 1) {
    return (
      <div className={cn("grid gap-2", className)} {...props}>
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={index}
            className={cn("atlas-skeleton h-3 rounded-full", index === lines - 1 ? "w-2/3" : "w-full")}
            aria-hidden="true"
          />
        ))}
      </div>
    );
  }

  return <div className={cn("atlas-skeleton min-h-16 rounded-[var(--pokrov-radius-card,0.875rem)]", className)} {...props} />;
}

type PageHeaderProps = HTMLAttributes<HTMLElement> & {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
};

export function PageHeader({ eyebrow, title, description, actions, className, ...props }: PageHeaderProps) {
  return (
    <header className={cn("flex flex-wrap items-start justify-between gap-4", className)} {...props}>
      <div className="min-w-0">
        {eyebrow ? <p className="text-xs font-semibold uppercase leading-5 tracking-[0.08em] text-[var(--atlas-text-muted)]">{eyebrow}</p> : null}
        <h1 className="mt-2 font-display text-[clamp(1.9rem,3vw,2.75rem)] font-semibold leading-[1.02] text-[var(--atlas-text)]">
          {title}
        </h1>
        {description ? <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--atlas-text-soft)]">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </header>
  );
}

type StateProps = HTMLAttributes<HTMLDivElement> & {
  icon?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
};

export function EmptyState({ icon, title, description, actions, className, ...props }: StateProps) {
  return (
    <div
      className={cn(
        "grid justify-items-center rounded-[var(--pokrov-radius-panel,1rem)] border border-dashed border-[color:var(--atlas-border)] bg-[var(--atlas-glass)] px-6 py-10 text-center",
        className,
      )}
      {...props}
    >
      <span className="grid h-12 w-12 place-items-center rounded-2xl border border-[color:var(--atlas-status-neutral-line)] bg-[var(--atlas-status-neutral-bg)] text-[var(--atlas-status-neutral-text)]">
        {icon || <Inbox aria-hidden="true" size={22} strokeWidth={1.75} />}
      </span>
      <h2 className="mt-4 text-lg font-semibold leading-6 text-[var(--atlas-text)]">{title}</h2>
      {description ? <p className="mt-2 max-w-xl text-sm leading-6 text-[var(--atlas-text-soft)]">{description}</p> : null}
      {actions ? <div className="mt-5 flex flex-wrap justify-center gap-2">{actions}</div> : null}
    </div>
  );
}

export function ErrorState({ icon, title, description, actions, className, ...props }: StateProps) {
  return (
    <div
      className={cn(
        "grid justify-items-center rounded-[var(--pokrov-radius-panel,1rem)] border border-[color:var(--atlas-status-danger-line)] bg-[var(--atlas-status-danger-bg)] px-6 py-10 text-center text-[var(--atlas-status-danger-text)]",
        className,
      )}
      {...props}
    >
      <span className="grid h-12 w-12 place-items-center rounded-2xl border border-[color:var(--atlas-status-danger-line)] bg-[var(--atlas-surface)]">
        {icon || <AlertTriangle aria-hidden="true" size={22} strokeWidth={1.75} />}
      </span>
      <h2 className="mt-4 text-lg font-semibold leading-6">{title}</h2>
      {description ? <p className="mt-2 max-w-xl text-sm leading-6">{description}</p> : null}
      {actions ? <div className="mt-5 flex flex-wrap justify-center gap-2">{actions}</div> : null}
    </div>
  );
}
