"use client";

import { cn, FOCUS_RING } from "@/components/utils";

/** Canonical iOS-style switch (DESIGN.md control canon): geometry, colors,
 * and spring transition come from the component.switch token group. */
export function Switch({
  checked,
  onChange,
  disabled,
  className,
  "aria-label": ariaLabel,
}: {
  checked: boolean;
  onChange: (next: boolean) => void;
  disabled?: boolean;
  className?: string;
  "aria-label"?: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={ariaLabel}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative inline-flex shrink-0 items-center rounded-full transition-colors disabled:opacity-55 motion-reduce:transition-none",
        FOCUS_RING,
        className,
      )}
      style={{
        width: "var(--pokrov-switch-width, 51px)",
        height: "var(--pokrov-switch-height, 31px)",
        background: checked ? "var(--pokrov-switch-on-bg)" : "var(--pokrov-switch-off-bg)",
        transitionDuration: "220ms",
      }}
    >
      <span
        aria-hidden="true"
        className="absolute rounded-full shadow-[0_3px_8px_rgba(0,0,0,0.15),0_1px_1px_rgba(0,0,0,0.16)] motion-reduce:transition-none"
        style={{
          width: "var(--pokrov-switch-thumb, 27px)",
          height: "var(--pokrov-switch-thumb, 27px)",
          background: "var(--pokrov-switch-thumb-color, #ffffff)",
          left: "2px",
          transform: checked
            ? "translateX(calc(var(--pokrov-switch-width, 51px) - var(--pokrov-switch-thumb, 27px) - 4px))"
            : "translateX(0)",
          transition: "transform var(--pokrov-switch-transition, 220ms cubic-bezier(0.34, 1.3, 0.64, 1))",
        }}
      />
    </button>
  );
}
