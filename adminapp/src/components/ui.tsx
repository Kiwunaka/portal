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
        "rounded-[var(--pokrov-radius-panel)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-[var(--pokrov-panel-padding)] shadow-[var(--atlas-shadow-soft)]",
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

export function Button({
  children,
  tone = "secondary",
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { tone?: "primary" | "secondary" | "danger" | "ghost" }) {
  return (
    <button
      className={cn(
        "inline-flex min-h-9 items-center justify-center gap-2 rounded-[var(--pokrov-radius-control)] px-3 text-xs font-semibold transition active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-55",
        tone === "primary" && "border border-transparent bg-[color:var(--atlas-primary)] text-[color:var(--atlas-primary-text)] hover:bg-[color:var(--atlas-primary-hover)]",
        tone === "secondary" && "border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] text-[color:var(--atlas-text)] hover:border-[color:var(--atlas-border-strong)]",
        tone === "danger" && "border border-[color:var(--atlas-status-danger-line)] bg-[color:var(--atlas-status-danger-bg)] text-[color:var(--atlas-status-danger-text)]",
        tone === "ghost" && "border border-transparent bg-transparent text-[color:var(--atlas-text-soft)] hover:bg-[color:var(--atlas-status-neutral-bg)]",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function Progress({ value, tone = "info" }: { value: number; tone?: Tone }) {
  const clamped = Math.max(0, Math.min(100, Number(value || 0)));
  return (
    <div className="h-2 overflow-hidden rounded-full bg-[color:var(--atlas-status-neutral-bg)]">
      <div
        className={cn(
          "h-full rounded-full",
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
    <div className="mb-4 flex flex-col gap-1">
      <h2 className="text-lg font-semibold leading-tight text-[color:var(--atlas-text)]">{title}</h2>
      {description ? <p className="max-w-3xl text-sm leading-6 text-[color:var(--atlas-text-soft)]">{description}</p> : null}
    </div>
  );
}
