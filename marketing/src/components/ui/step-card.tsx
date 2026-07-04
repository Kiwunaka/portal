import type { ReactNode } from "react";

import { cn } from "../utils";

export function StepCard({
  className,
  illustration,
  index,
  text,
  title,
}: {
  className?: string;
  illustration?: ReactNode;
  index: number;
  text: string;
  title: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-4 rounded-(--radius-card) border border-line bg-surface p-6 shadow-soft",
        className,
      )}
    >
      {illustration ? (
        <div className="flex h-36 items-center justify-center overflow-hidden rounded-(--radius-control) bg-canvas-alt">
          {illustration}
        </div>
      ) : null}
      <div className="flex items-start gap-3">
        <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-brand-soft text-[0.9375rem] font-bold text-brand">
          {index}
        </span>
        <div className="flex flex-col gap-1">
          <h3 className="text-[1.0625rem] font-semibold text-ink">{title}</h3>
          <p className="text-[0.9375rem] leading-relaxed text-ink-soft">{text}</p>
        </div>
      </div>
    </div>
  );
}
