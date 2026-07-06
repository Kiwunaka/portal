"use client";

import { useState } from "react";

import { cn, FOCUS_RING } from "@/components/utils";
import { hapticImpact } from "@/lib/telegram";

/** Canonical iOS-style switch (DESIGN.md control canon): geometry, colors,
 * and spring transition come from the component.switch token group.
 * Tactile detail: the thumb stretches while pressed and stays anchored to
 * its active side, like the system switch. */
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
  const [pressed, setPressed] = useState(false);

  const stretch = pressed && !disabled ? 5 : 0;

  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={ariaLabel}
      disabled={disabled}
      onClick={() => {
        hapticImpact("light");
        onChange(!checked);
      }}
      onPointerDown={() => setPressed(true)}
      onPointerUp={() => setPressed(false)}
      onPointerLeave={() => setPressed(false)}
      onPointerCancel={() => setPressed(false)}
      className={cn(
        "relative inline-flex shrink-0 items-center rounded-full transition-colors duration-200 disabled:opacity-55 motion-reduce:transition-none",
        FOCUS_RING,
        className,
      )}
      style={{
        width: "var(--pokrov-switch-width, 51px)",
        height: "var(--pokrov-switch-height, 31px)",
        background: checked ? "var(--pokrov-switch-on-bg)" : "var(--pokrov-switch-off-bg)",
      }}
    >
      <span
        aria-hidden="true"
        className="absolute rounded-full shadow-[0_3px_8px_rgba(0,0,0,0.15),0_1px_1px_rgba(0,0,0,0.16)] motion-reduce:transition-none"
        style={{
          width: `calc(var(--pokrov-switch-thumb, 27px) + ${stretch}px)`,
          height: "var(--pokrov-switch-thumb, 27px)",
          background: "var(--pokrov-switch-thumb-color, #ffffff)",
          left: "2px",
          transform: checked
            ? `translateX(calc(var(--pokrov-switch-width, 51px) - var(--pokrov-switch-thumb, 27px) - 4px - ${stretch}px))`
            : "translateX(0)",
          transition:
            "transform var(--pokrov-switch-transition, 220ms cubic-bezier(0.34, 1.3, 0.64, 1)), width 160ms var(--pokrov-easing, cubic-bezier(0.22, 1, 0.36, 1))",
        }}
      />
    </button>
  );
}
