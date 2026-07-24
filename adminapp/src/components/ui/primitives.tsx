import type { ReactNode } from "react";

import { cn } from "@/components/utils";

export type Tone = "neutral" | "success" | "warning" | "danger" | "info";

const toneClasses: Record<Tone, string> = {
  neutral: "border-[color:var(--atlas-status-neutral-line)] bg-[color:var(--atlas-status-neutral-bg)] text-[color:var(--atlas-status-neutral-text)]",
  success: "border-[color:var(--atlas-status-success-line)] bg-[color:var(--atlas-status-success-bg)] text-[color:var(--atlas-status-success-text)]",
  warning: "border-[color:var(--atlas-status-warning-line)] bg-[color:var(--atlas-status-warning-bg)] text-[color:var(--atlas-status-warning-text)]",
  danger: "border-[color:var(--atlas-status-danger-line)] bg-[color:var(--atlas-status-danger-bg)] text-[color:var(--atlas-status-danger-text)]",
  info: "border-[color:var(--atlas-status-info-line)] bg-[color:var(--atlas-status-info-bg)] text-[color:var(--atlas-status-info-text)]"
};

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <section
      className={cn(
        "rounded-[var(--pokrov-radius-panel)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-[var(--pokrov-panel-padding)] shadow-[var(--atlas-shadow-soft)] transition-[border-color,box-shadow]",
        className
      )}
    >
      {children}
    </section>
  );
}

export function Badge({ children, tone = "neutral", className }: { children: ReactNode; tone?: Tone; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full border px-2 py-1 text-[11px] font-semibold", toneClasses[tone], className)}>
      {children}
    </span>
  );
}

export function Progress({ value, tone = "info", label = "Заполнение" }: { value: number; tone?: Tone; label?: string }) {
  const clamped = Math.max(0, Math.min(100, Number(value || 0)));
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={clamped}
      className="h-2 overflow-hidden rounded-full bg-[color:var(--atlas-status-neutral-bg)]"
    >
      <div
        className={cn(
          "h-full rounded-full transition-[width]",
          tone === "success" && "bg-[color:var(--atlas-status-success-text)]",
          tone === "warning" && "bg-[color:var(--atlas-status-warning-text)]",
          tone === "danger" && "bg-[color:var(--atlas-status-danger-text)]",
          tone === "info" && "bg-[color:var(--atlas-status-info-text)]",
          tone === "neutral" && "bg-[color:var(--atlas-text-muted)]"
        )}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}

export function SectionTitle({ title, description }: { title: string; description?: string }) {
  return (
    <header className="mb-4 flex max-w-4xl flex-col gap-1">
      <h2 className="text-balance text-lg font-semibold leading-tight tracking-[-0.015em] text-[color:var(--atlas-text)]">{title}</h2>
      {description ? <p className="max-w-[68ch] text-pretty text-sm leading-6 text-[color:var(--atlas-text-soft)]">{description}</p> : null}
    </header>
  );
}

export function MetricStrip({ children, className, label = "Ключевые показатели" }: { children: ReactNode; className?: string; label?: string }) {
  return (
    <section aria-label={label} className={cn("ops-metric-strip", className)}>
      {children}
    </section>
  );
}

export function MetricCell({
  icon,
  label,
  value,
  detail,
  tone = "neutral",
  aside
}: {
  icon?: ReactNode;
  label: string;
  value: ReactNode;
  detail?: ReactNode;
  tone?: Tone;
  aside?: ReactNode;
}) {
  return (
    <div className="ops-metric-cell">
      <div className={cn("ops-metric-icon", toneClasses[tone])}>{icon}</div>
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <div className="text-[11px] font-medium text-[color:var(--atlas-text-soft)]">{label}</div>
          {aside}
        </div>
        <div className="mt-1 truncate text-xl font-semibold tracking-[-0.02em] text-[color:var(--atlas-text)] tabular-nums">{value}</div>
        {detail ? <div className="mt-1 truncate text-[10px] text-[color:var(--atlas-text-muted)]">{detail}</div> : null}
      </div>
    </div>
  );
}
