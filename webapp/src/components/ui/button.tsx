"use client";

import type { MouseEventHandler, ReactNode } from "react";
import { Loader2 } from "lucide-react";

import AppRouteLink from "@/components/app-route-link";
import { cn, FOCUS_RING } from "@/components/utils";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "md" | "sm";

const BASE =
  "inline-flex items-center justify-center gap-2 rounded-control font-semibold transition-[background-color,border-color,color,transform,box-shadow] duration-200 ease-apple select-none active:scale-[0.97] disabled:pointer-events-none disabled:opacity-55 motion-reduce:transition-none motion-reduce:active:scale-100";

const SIZE_CLASS: Record<ButtonSize, string> = {
  md: "min-h-11 px-5 text-[0.9375rem]",
  sm: "min-h-9 px-3.5 text-sm",
};

const VARIANT_CLASS: Record<ButtonVariant, string> = {
  primary: "bg-brand text-brand-contrast hover:bg-brand-strong active:bg-brand-strong shadow-soft",
  secondary: "border border-line bg-surface text-ink hover:bg-canvas-alt",
  ghost: "text-ink-soft hover:bg-nav-hover hover:text-ink",
  danger: "border border-danger-line bg-danger-bg text-danger-text hover:brightness-97",
};

export type ButtonProps = {
  variant?: ButtonVariant;
  size?: ButtonSize;
  block?: boolean;
  loading?: boolean;
  className?: string;
  children: ReactNode;
  onClick?: MouseEventHandler<HTMLElement>;
  disabled?: boolean;
  type?: "button" | "submit" | "reset";
  href?: string;
  target?: string;
  rel?: string;
  hardNavigate?: boolean;
  "aria-label"?: string;
  title?: string;
};

export function Button({
  variant = "primary",
  size = "md",
  block,
  loading,
  className,
  children,
  onClick,
  disabled,
  type = "button",
  href,
  target,
  rel,
  hardNavigate,
  ...aria
}: ButtonProps) {
  const classes = cn(BASE, SIZE_CLASS[size], VARIANT_CLASS[variant], block && "w-full", FOCUS_RING, className);

  if (href !== undefined) {
    return (
      <AppRouteLink
        href={href}
        target={target}
        rel={rel}
        hardNavigate={hardNavigate}
        className={classes}
        onClick={onClick as MouseEventHandler<HTMLAnchorElement>}
        aria-label={aria["aria-label"]}
        title={aria.title}
      >
        {children}
      </AppRouteLink>
    );
  }

  return (
    <button
      type={type}
      className={classes}
      onClick={onClick as MouseEventHandler<HTMLButtonElement>}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      aria-label={aria["aria-label"]}
      title={aria.title}
    >
      {loading ? <Loader2 size={16} strokeWidth={2.2} className="animate-spin motion-reduce:animate-none" aria-hidden="true" /> : null}
      <span className="min-w-0">{children}</span>
    </button>
  );
}
