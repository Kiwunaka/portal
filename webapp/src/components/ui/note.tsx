import type { ReactNode } from "react";

import type { Tone } from "@/components/ui/badge";
import { cn } from "@/components/utils";

const TONE_CLASS: Record<Tone, string> = {
  success: "border-ok-line bg-ok-bg text-ok-text",
  warning: "border-warn-line bg-warn-bg text-warn-text",
  danger: "border-danger-line bg-danger-bg text-danger-text",
  info: "border-info-line bg-info-bg text-info-text",
  neutral: "border-neutral-line bg-neutral-bg text-neutral-text",
};

export function Note({ tone = "neutral", children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <p className={cn("rounded-control border px-3.5 py-2.5 text-sm leading-6", TONE_CLASS[tone], className)} data-tone={tone}>
      {children}
    </p>
  );
}
