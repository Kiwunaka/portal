"use client";

import { useId, type ReactNode } from "react";

import { cn } from "@/components/utils";
import { formatSourceAge, statusPresentation } from "@/lib/ops-status/presentation";
import type { OpsStatusCode } from "@/lib/ops-status/types";

import { StatusBadge } from "./status-badge";
import { OpsTooltip } from "./tooltip";

export interface SourceRowProps {
  source: string;
  status: OpsStatusCode;
  sampledAt: string | null;
  threshold?: string | null;
  detail?: ReactNode;
  action?: ReactNode;
  tooltipId?: string;
  className?: string;
}

function sourceDetail(status: OpsStatusCode, detail: ReactNode): ReactNode {
  if (status === "missing") {
    return "Нет данных";
  }
  if (status === "unavailable") {
    return "Недоступно";
  }
  if (detail === null || detail === undefined) {
    return "Нет данных";
  }
  if (typeof detail === "number" && !Number.isFinite(detail)) {
    return "Нет данных";
  }
  return detail;
}

export function SourceRow({ source, status, sampledAt, threshold = null, detail, action, tooltipId, className }: SourceRowProps) {
  const generatedId = useId();
  const presentation = statusPresentation(status);
  const resolvedTooltipId = tooltipId ?? `${generatedId}-ops-tooltip`;

  return (
    <div className={cn("grid min-h-14 grid-cols-[minmax(0,1fr)_auto] items-center gap-3 border-b border-[color:var(--atlas-border)] px-3 py-2 last:border-b-0", className)}>
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="truncate text-xs font-semibold text-[color:var(--atlas-text)]">{source}</span>
          <StatusBadge status={status} />
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-[color:var(--atlas-text-muted)]">
          <span className="text-[color:var(--atlas-text-soft)]">{sourceDetail(status, detail)}</span>
          {sampledAt ? <time dateTime={sampledAt}>{formatSourceAge(sampledAt)}</time> : <span>Нет данных</span>}
        </div>
      </div>
      <OpsTooltip
        id={resolvedTooltipId}
        content={presentation.explanation}
        source={source}
        sampledAt={sampledAt}
        threshold={threshold}
        action={action}
      />
    </div>
  );
}
