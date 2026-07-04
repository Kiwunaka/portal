import type { ReactNode } from "react";

import { cn } from "../utils";

export function Card({
  children,
  className,
  hover = false,
}: {
  children: ReactNode;
  className?: string;
  /** Adds the subtle-lift hover from the motion canon. */
  hover?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-(--radius-card) border border-line bg-surface p-6 shadow-soft",
        hover &&
          "transition-[transform,box-shadow] duration-200 ease-(--ease-apple) hover:-translate-y-0.5 hover:shadow-medium motion-reduce:transition-none motion-reduce:hover:translate-y-0",
        className,
      )}
    >
      {children}
    </div>
  );
}
