import type { HTMLAttributes } from "react";

import { cn } from "@/components/utils";
import { statusPresentation } from "@/lib/ops-status/presentation";
import type { OpsStatusCode, OpsStatusTone } from "@/lib/ops-status/types";

export interface StatusBadgeProps extends Omit<HTMLAttributes<HTMLSpanElement>, "children"> {
  status: OpsStatusCode;
}

const toneClasses: Record<OpsStatusTone, string> = {
  success: "border-[color:var(--command-status-success-line)] bg-[color:var(--command-status-success-bg)] text-[color:var(--command-status-success-text)]",
  warning: "border-[color:var(--command-status-warning-line)] bg-[color:var(--command-status-warning-bg)] text-[color:var(--command-status-warning-text)]",
  danger: "border-[color:var(--command-status-danger-line)] bg-[color:var(--command-status-danger-bg)] text-[color:var(--command-status-danger-text)]",
  neutral: "border-[color:var(--command-status-neutral-line)] bg-[color:var(--command-status-neutral-bg)] text-[color:var(--command-status-neutral-text)]"
};

export function StatusBadge({ status, className, ...props }: StatusBadgeProps) {
  const presentation = statusPresentation(status);

  return (
    <span
      className={cn("inline-flex min-h-6 items-center rounded-full border px-2 py-0.5 text-[11px] font-semibold leading-none", toneClasses[presentation.tone], className)}
      data-status={status}
      {...props}
    >
      {presentation.label}
    </span>
  );
}
