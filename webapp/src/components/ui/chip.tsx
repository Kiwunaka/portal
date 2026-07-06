"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn, FOCUS_RING } from "@/components/utils";

type ChipProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className"> & {
  active?: boolean;
  className?: string;
  children: ReactNode;
};

export function Chip({ active, className, children, type = "button", ...props }: ChipProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex min-h-9 items-center gap-1.5 rounded-full border px-3.5 text-sm font-semibold transition-[background-color,border-color,color,transform] duration-200 ease-apple active:scale-[0.97] motion-reduce:transition-none motion-reduce:active:scale-100",
        active
          ? "border-brand bg-brand-soft text-brand-strong"
          : "border-line bg-surface text-ink-soft hover:bg-canvas-alt hover:text-ink",
        FOCUS_RING,
        className,
      )}
      aria-pressed={active}
      data-active={active ? "true" : "false"}
      {...props}
    >
      {children}
    </button>
  );
}
