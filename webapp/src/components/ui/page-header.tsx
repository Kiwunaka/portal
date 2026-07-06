import type { ReactNode } from "react";

import { cn } from "@/components/utils";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  status,
  className,
}: {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  status?: ReactNode;
  className?: string;
}) {
  return (
    <header className={cn("flex flex-wrap items-start justify-between gap-3", className)}>
      <div className="min-w-0">
        {eyebrow ? (
          <p className="mb-1 text-xs font-bold tracking-[0.08em] text-ink-muted uppercase">{eyebrow}</p>
        ) : null}
        <div className="flex flex-wrap items-center gap-2.5">
          <h1 className="font-display text-[1.65rem] leading-tight font-bold tracking-[-0.01em] text-ink sm:text-[1.9rem]">
            {title}
          </h1>
          {status}
        </div>
        {description ? <p className="mt-1.5 max-w-xl text-[0.9375rem] leading-relaxed text-ink-soft">{description}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}
