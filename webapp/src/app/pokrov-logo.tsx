"use client";

import PokrovMark from "@/components/pokrov-mark";
import { cn } from "@/components/utils";

const POKROV_WORDMARK_PATHS = [
  "m16.09 148.6h-12.39v28.29h6.01v-7.98h6.38c7.73 0 11.94-4.06 11.94-9.99 0-6.26-4.22-10.32-11.94-10.32zm-0.25 15.2h-6.13v-10.09h6.13c4.47 0 5.88 2.35 5.88 5.3 0 2.6-1.41 4.79-5.88 4.79z",
  "m48.58 148.4c-9.4 0-14.86 6.71-14.86 14.65 0 7.95 5.46 14.05 14.86 14.05s15.23-6.7 15.23-14.05c0-7.94-5.46-14.65-15.23-14.65zm0 23.35c-5.92 0-9.35-4.32-9.35-8.97 0-5.25 3.29-9.03 9.35-9.03 6.21 0 9.45 4.32 9.45 9.03 0 4.94-3.29 8.97-9.45 8.97z",
  "m96.75 148.6h-7.1l-12.67 13.99v-13.99h-5.92v27.21h5.92v-6.5l4.63-4.71 8.25 11.21h7.62l-11.77-15.08 11.04-12.13z",
  "m126.8 158.9c0-6.26-4.59-10.31-11.23-10.31h-13.2v27.21h6.06v-7.6h7.16l4.56 7.6h7.51l-6.5-8.98c3.73-1.67 5.64-4.12 5.64-7.92zm-11.68 4.64h-6.69v-9.84h6.69c3.73 0 5.37 2.19 5.37 4.91 0 2.44-1.64 4.93-5.37 4.93z",
  "m147.6 148.4c-9.4 0-14.86 6.71-14.86 14.65 0 7.95 5.46 14.05 14.86 14.05s15.23-6.7 15.23-14.05c0-7.94-5.46-14.65-15.23-14.65zm0 23.35c-5.92 0-9.35-4.32-9.35-8.97 0-5.25 3.29-9.03 9.35-9.03 6.21 0 9.45 4.32 9.45 9.03 0 4.94-3.29 8.97-9.45 8.97z",
  "m190 148.6-8.37 21.16-9.2-21.16h-6.31l11.97 27.41h6.22l12-27.41h-6.31z",
];

type PokrovLogoProps = {
  className?: string;
  label?: string;
  markClassName?: string;
  textClassName?: string;
  caption?: string;
  showWordmark?: boolean;
};

export default function PokrovLogo({
  className,
  label,
  markClassName,
  textClassName,
  caption,
  showWordmark = false,
}: PokrovLogoProps) {
  if (!showWordmark) {
    return <PokrovMark className={className ?? "h-10 w-10"} label={label} />;
  }

  return (
    <span
      className={cn("inline-flex items-center gap-3", className)}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    >
      <span className={cn("inline-flex shrink-0", markClassName || "h-10 w-10")}>
        <PokrovMark className="h-full w-full" label={label ? undefined : "POKROV logo"} />
      </span>
      <span className={cn("min-w-0", textClassName)}>
        <svg
          aria-hidden="true"
          className="block h-auto w-[10.25rem] max-w-full text-[color:var(--atlas-text)]"
          fill="none"
          viewBox="3 148 193 29"
          xmlns="http://www.w3.org/2000/svg"
        >
          {POKROV_WORDMARK_PATHS.map((path) => (
            <path key={path} d={path} fill="currentColor" />
          ))}
        </svg>
        {caption ? (
          <span className="mt-1 block text-[11px] uppercase tracking-[0.18em] text-[color:var(--atlas-text-soft)]">
            {caption}
          </span>
        ) : null}
      </span>
    </span>
  );
}
