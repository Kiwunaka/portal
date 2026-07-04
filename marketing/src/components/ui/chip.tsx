import type { ReactNode } from "react";

import { cn } from "../utils";

type ChipTone = "brand" | "neutral" | "status";

const TONES: Record<ChipTone, string> = {
  brand: "bg-brand-soft text-brand-strong",
  neutral: "border border-line bg-surface text-ink-soft",
  status: "bg-brand-soft text-brand-strong",
};

export function Chip({
  children,
  className,
  tone = "brand",
}: {
  children: ReactNode;
  className?: string;
  tone?: ChipTone;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[0.8125rem] font-semibold",
        TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
