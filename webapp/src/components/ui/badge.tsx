import type { ReactNode } from "react";

import { cn } from "@/components/utils";

export type Tone = "success" | "warning" | "danger" | "info" | "neutral";

const TONE_CLASS: Record<Tone, string> = {
  success: "border-ok-line bg-ok-bg text-ok-text",
  warning: "border-warn-line bg-warn-bg text-warn-text",
  danger: "border-danger-line bg-danger-bg text-danger-text",
  info: "border-info-line bg-info-bg text-info-text",
  neutral: "border-neutral-line bg-neutral-bg text-neutral-text",
};

export function Badge({
  tone = "neutral",
  dot,
  children,
  className,
}: {
  tone?: Tone;
  dot?: boolean;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        TONE_CLASS[tone],
        className,
      )}
      data-tone={tone}
    >
      {dot ? <span aria-hidden="true" className="size-1.5 shrink-0 rounded-full bg-current" /> : null}
      {children}
    </span>
  );
}
