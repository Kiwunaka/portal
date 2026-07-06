import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import type { Tone } from "@/components/ui/badge";
import { cn } from "@/components/utils";

const HERO_TONE: Record<Tone, { panel: string; emblem: string }> = {
  success: {
    panel: "border-ok-line bg-[linear-gradient(135deg,var(--pokrov-status-success-bg),var(--pokrov-surface)_70%)]",
    emblem: "bg-ok-bg text-ok-text ring-ok-line",
  },
  warning: {
    panel: "border-warn-line bg-[linear-gradient(135deg,var(--pokrov-status-warning-bg),var(--pokrov-surface)_70%)]",
    emblem: "bg-warn-bg text-warn-text ring-warn-line",
  },
  danger: {
    panel: "border-danger-line bg-[linear-gradient(135deg,var(--pokrov-status-danger-bg),var(--pokrov-surface)_70%)]",
    emblem: "bg-danger-bg text-danger-text ring-danger-line",
  },
  info: {
    panel: "border-info-line bg-[linear-gradient(135deg,var(--pokrov-status-info-bg),var(--pokrov-surface)_70%)]",
    emblem: "bg-info-bg text-info-text ring-info-line",
  },
  neutral: {
    panel: "border-line bg-surface",
    emblem: "bg-canvas-alt text-brand ring-line",
  },
};

/** Page-level status hero: one dominant state, one primary action. */
export function StatusHero({
  title,
  meta,
  body,
  tone = "neutral",
  icon: Icon,
  action,
  children,
  className,
}: {
  title: ReactNode;
  meta?: ReactNode;
  body?: ReactNode;
  tone?: Tone;
  icon?: LucideIcon;
  action?: ReactNode;
  children?: ReactNode;
  className?: string;
}) {
  const toneStyle = HERO_TONE[tone];
  return (
    <section className={cn("rounded-panel border p-5 shadow-soft sm:p-6", toneStyle.panel, className)} data-tone={tone}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-4">
          {Icon ? (
            <span className={cn("relative grid size-14 shrink-0 place-items-center rounded-2xl ring-1", toneStyle.emblem)} aria-hidden="true">
              {tone === "success" ? (
                <span className="absolute inset-0 rounded-2xl ring-2 ring-ok-line motion-safe:animate-[heroPulse_2.8s_ease-out_infinite]" />
              ) : null}
              <Icon size={26} strokeWidth={1.9} />
            </span>
          ) : null}
          <div className="min-w-0">
            {meta ? <p className="text-[13px] leading-5 font-medium text-ink-soft">{meta}</p> : null}
            <h1 className="mt-1 font-display text-[1.45rem] leading-tight font-bold tracking-[-0.02em] text-ink sm:text-[1.65rem]">
              {title}
            </h1>
            {body ? <p className="mt-2 max-w-2xl text-sm leading-6 text-ink-soft">{body}</p> : null}
          </div>
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
      {children ? <div className="mt-4 border-t border-line pt-4">{children}</div> : null}
    </section>
  );
}
