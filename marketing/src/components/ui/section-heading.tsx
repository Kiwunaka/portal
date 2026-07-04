import type { ReactNode } from "react";

import { cn } from "../utils";

export function SectionHeading({
  align = "center",
  className,
  kicker,
  sub,
  title,
}: {
  align?: "center" | "left";
  className?: string;
  kicker?: ReactNode;
  sub?: ReactNode;
  title: ReactNode;
}) {
  return (
    <div
      className={cn(
        "mb-12 flex flex-col gap-3",
        align === "center" ? "items-center text-center" : "items-start text-left",
        className,
      )}
    >
      {kicker ? (
        <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">{kicker}</span>
      ) : null}
      <h2 className="font-display max-w-2xl text-[1.75rem] font-bold tracking-[-0.01em] text-ink sm:text-[2.125rem]">
        {title}
      </h2>
      {sub ? <p className="max-w-xl text-base leading-relaxed text-ink-soft">{sub}</p> : null}
    </div>
  );
}
