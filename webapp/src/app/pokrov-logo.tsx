"use client";

import PokrovMark from "@/components/pokrov-mark";

type PokrovLogoProps = {
  className?: string;
  label?: string;
  markClassName?: string;
  textClassName?: string;
  caption?: string;
  showWordmark?: boolean;
};

export default function PokrovLogo({
  className = "h-10 w-10",
  label,
  markClassName,
  textClassName,
  caption,
  showWordmark = false,
}: PokrovLogoProps) {
  if (!showWordmark) {
    return <PokrovMark className={className} label={label} />;
  }

  return (
    <span
      className={`inline-flex items-center gap-3 ${className}`}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    >
      <span className={`inline-flex shrink-0 ${markClassName || "h-10 w-10"}`}>
        <PokrovMark className="h-full w-full" label={label ? undefined : "POKROV logo"} />
      </span>
      <span className={`min-w-0 ${textClassName || ""}`}>
        <span className="block font-display text-[1.55rem] font-semibold leading-none tracking-[0.22em] text-slate-950 dark:text-slate-50">
          POKROV
        </span>
        {caption ? (
          <span className="mt-1 block text-[11px] uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
            {caption}
          </span>
        ) : null}
      </span>
    </span>
  );
}
