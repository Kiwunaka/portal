import type { ReactNode } from "react";

import AppRouteLink from "@/components/app-route-link";
import { cn } from "@/components/utils";

type CardPadding = "md" | "lg" | "none";

const PADDING_CLASS: Record<CardPadding, string> = {
  md: "p-4 sm:p-5",
  lg: "p-5 sm:p-7",
  none: "",
};

export function Card({
  padding = "md",
  hover,
  href,
  className,
  children,
  "aria-label": ariaLabel,
}: {
  padding?: CardPadding;
  hover?: boolean;
  href?: string;
  className?: string;
  children: ReactNode;
  "aria-label"?: string;
}) {
  const classes = cn(
    "block rounded-card border border-line bg-surface shadow-soft",
    PADDING_CLASS[padding],
    hover &&
      "transition-[transform,box-shadow,border-color] duration-200 ease-apple hover:-translate-y-px hover:border-line-strong hover:shadow-medium motion-reduce:transition-none motion-reduce:hover:translate-y-0",
    className,
  );

  if (href !== undefined) {
    return (
      <AppRouteLink href={href} className={cn(classes, "no-underline")} aria-label={ariaLabel}>
        {children}
      </AppRouteLink>
    );
  }
  return (
    <div className={classes} aria-label={ariaLabel}>
      {children}
    </div>
  );
}

/** Section panel: larger radius for page-level groupings. */
export function Panel({ className, children }: { className?: string; children: ReactNode }) {
  return <section className={cn("rounded-panel border border-line bg-surface p-5 shadow-soft sm:p-6", className)}>{children}</section>;
}
