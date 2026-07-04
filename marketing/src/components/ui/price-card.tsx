import type { ReactNode } from "react";

import { Button } from "./button";
import { cn } from "../utils";

export type PriceCardProps = {
  className?: string;
  ctaHref: string;
  ctaLabel: string;
  deviceNote: string;
  durationNote: string;
  featured?: boolean;
  featuredNote?: string;
  perMonthNote?: string;
  price: string;
  title: string;
};

export function PriceCard({
  className,
  ctaHref,
  ctaLabel,
  deviceNote,
  durationNote,
  featured = false,
  featuredNote,
  perMonthNote,
  price,
  title,
}: PriceCardProps) {
  return (
    <div
      className={cn(
        "relative flex flex-col gap-4 rounded-(--radius-card) border bg-surface p-6 shadow-soft transition-[transform,box-shadow] duration-200 ease-(--ease-apple) hover:-translate-y-0.5 hover:shadow-medium motion-reduce:transition-none motion-reduce:hover:translate-y-0",
        featured ? "border-brand shadow-medium" : "border-line",
        className,
      )}
    >
      {featured && featuredNote ? (
        <span className="absolute -top-3.5 left-6 rounded-full bg-brand px-3 py-1 text-xs font-semibold text-ink-inverse">
          {featuredNote}
        </span>
      ) : null}
      <div className="flex flex-col gap-1">
        <span className="text-[0.9375rem] font-semibold text-ink-soft">{title}</span>
        <div className="flex items-baseline gap-2">
          <span className="font-display text-[2rem] font-bold tracking-[-0.01em] text-ink">{price}</span>
          <span className="text-sm text-ink-soft">{durationNote}</span>
        </div>
        {perMonthNote ? <span className="text-sm font-medium text-brand">{perMonthNote}</span> : null}
      </div>
      <span className="text-sm text-ink-soft">{deviceNote}</span>
      <Button
        href={ctaHref}
        variant={featured ? "primary" : "secondary"}
        className="mt-auto w-full"
      >
        {ctaLabel}
      </Button>
    </div>
  );
}
