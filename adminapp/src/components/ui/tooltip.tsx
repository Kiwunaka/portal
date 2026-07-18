"use client";

import { useRef, useState, type KeyboardEvent, type ReactNode } from "react";

import { cn } from "@/components/utils";
import { formatSourceAge } from "@/lib/ops-status/presentation";

export interface OpsTooltipProps {
  id: string;
  content: ReactNode;
  source: string;
  sampledAt: string | null;
  threshold: string | null;
  action?: ReactNode;
  className?: string;
}

export function OpsTooltip({ id, content, source, sampledAt, threshold, action, className }: OpsTooltipProps) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const suppressFocusOpenRef = useRef(false);

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      suppressFocusOpenRef.current = true;
      setOpen(false);
      window.requestAnimationFrame(() => triggerRef.current?.focus());
    }
  }

  return (
    <div
      className={cn("relative inline-flex", className)}
      onMouseEnter={() => {
        suppressFocusOpenRef.current = false;
        setOpen(true);
      }}
      onMouseLeave={(event) => {
        if (!event.currentTarget.contains(document.activeElement)) {
          setOpen(false);
        }
      }}
      onFocusCapture={() => {
        if (!suppressFocusOpenRef.current) {
          setOpen(true);
        }
      }}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) {
          suppressFocusOpenRef.current = false;
          setOpen(false);
        }
      }}
      onKeyDown={handleKeyDown}
    >
      <button
        ref={triggerRef}
        type="button"
        aria-label="Показать пояснение"
        aria-describedby={id}
        className="inline-flex min-h-10 min-w-10 items-center justify-center rounded-[var(--pokrov-radius-control)] border border-transparent text-xs font-bold text-[color:var(--atlas-text-soft)] transition-colors hover:border-[color:var(--atlas-border-strong)] hover:bg-[color:var(--command-surface-raised)] hover:text-[color:var(--atlas-text)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--atlas-focus)] focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--atlas-canvas)]"
      >
        <span aria-hidden="true">i</span>
      </button>

      <div
        id={id}
        role="tooltip"
        aria-hidden={!open}
        className={cn(
          "absolute bottom-[calc(100%+0.5rem)] right-0 z-50 w-80 max-w-[calc(100vw-2rem)] rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border-strong)] bg-[color:var(--command-surface-raised)] p-3 text-left text-xs leading-5 text-[color:var(--atlas-text)] shadow-[var(--atlas-shadow-medium)] transition-[opacity,transform,visibility]",
          open ? "visible translate-y-0 opacity-100" : "pointer-events-none invisible translate-y-1 opacity-0"
        )}
      >
        <div>{content}</div>
        <dl className="mt-2 grid grid-cols-[auto_minmax(0,1fr)] gap-x-2 gap-y-1 text-[11px]">
          <dt className="text-[color:var(--atlas-text-muted)]">Источник</dt>
          <dd className="m-0 break-words text-[color:var(--atlas-text-soft)]">{source}</dd>
          <dt className="text-[color:var(--atlas-text-muted)]">Измерено</dt>
          <dd className="m-0 text-[color:var(--atlas-text-soft)]">
            {sampledAt ? (
              <time dateTime={sampledAt} className="flex flex-col">
                <span>{formatSourceAge(sampledAt)}</span>
                <span className="break-all font-mono text-[10px] text-[color:var(--atlas-text-muted)]">{sampledAt}</span>
              </time>
            ) : (
              "Нет данных"
            )}
          </dd>
          <dt className="text-[color:var(--atlas-text-muted)]">Порог</dt>
          <dd className="m-0 break-words text-[color:var(--atlas-text-soft)]">{threshold ?? "Не задан"}</dd>
        </dl>
        {action ? <div className="mt-2 border-t border-[color:var(--atlas-border)] pt-2">{action}</div> : null}
      </div>
    </div>
  );
}
