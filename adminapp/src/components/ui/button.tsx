import { forwardRef, type ButtonHTMLAttributes } from "react";

import { cn } from "@/components/utils";

export type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";
export type ButtonSize = "default" | "compact" | "icon";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  tone?: ButtonVariant;
  size?: ButtonSize;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: "border-transparent bg-[color:var(--atlas-primary)] text-[color:var(--atlas-primary-text)] hover:bg-[color:var(--atlas-primary-hover)]",
  secondary: "border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] text-[color:var(--atlas-text)] hover:border-[color:var(--atlas-border-strong)] hover:bg-[color:var(--command-surface-raised)]",
  danger: "border-[color:var(--command-status-danger-line)] bg-[color:var(--command-status-danger-bg)] text-[color:var(--command-status-danger-text)] hover:border-[color:var(--command-status-danger-text)]",
  ghost: "border-transparent bg-transparent text-[color:var(--atlas-text-soft)] hover:bg-[color:var(--command-surface-raised)] hover:text-[color:var(--atlas-text)]"
};

const sizeClasses: Record<ButtonSize, string> = {
  default: "min-h-10 px-3.5",
  compact: "min-h-10 px-3",
  icon: "min-h-10 min-w-10 p-0"
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant, tone, size = "default", type = "button", ...props },
  ref
) {
  const resolvedVariant = variant ?? tone ?? "secondary";

  return (
    <button
      ref={ref}
      type={type}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-[var(--pokrov-radius-control)] border text-xs font-semibold transition-[color,background-color,border-color,transform] active:translate-y-px disabled:cursor-not-allowed disabled:opacity-50 disabled:active:translate-y-0",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--atlas-focus)] focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--atlas-canvas)]",
        variantClasses[resolvedVariant],
        sizeClasses[size],
        className
      )}
      {...props}
    />
  );
});
