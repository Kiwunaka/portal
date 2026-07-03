"use client";

import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  MouseEventHandler,
  ReactNode,
  TextareaHTMLAttributes,
} from "react";

import AppRouteLink from "@/components/app-route-link";
import { cn, FOCUS_RING } from "@/components/utils";

/* ── Button ──────────────────────────────────────────────── */

type ButtonVariant = "primary" | "secondary" | "ghost";
type ButtonSize = "md" | "sm";

const VARIANT_CLASS: Record<ButtonVariant, string> = {
  primary: "cab-btn--primary",
  secondary: "cab-btn--secondary",
  ghost: "cab-btn--ghost",
};

type ButtonProps = {
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

function ButtonSpinner() {
  return (
    <span className="cab-btn-spinner" aria-hidden="true">
      <svg className="cab-btn-spin" width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="6.25" stroke="currentColor" strokeWidth="2" opacity="0.25" />
        <path d="M14.25 8a6.25 6.25 0 0 0-6.25-6.25" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
    </span>
  );
}

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
  const classes = cn(
    "cab-btn",
    VARIANT_CLASS[variant],
    size === "sm" && "cab-btn--sm",
    block && "cab-btn--block",
    loading && "cab-btn--loading",
    FOCUS_RING,
    className,
  );

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
      <span className="cab-btn-label">{children}</span>
      {loading ? <ButtonSpinner /> : null}
    </button>
  );
}

/* ── Field / Input / Textarea ────────────────────────────── */

type FieldProps = {
  label?: ReactNode;
  hint?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function Field({ label, hint, children, className }: FieldProps) {
  return (
    <label className={cn("cab-field", className)}>
      {label ? <span className="cab-field-label">{label}</span> : null}
      {children}
      {hint ? <span className="cab-field-hint">{hint}</span> : null}
    </label>
  );
}

type InputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "className"> & { className?: string };

export function Input({ className, ...props }: InputProps) {
  return <input className={cn("cab-input", FOCUS_RING, className)} {...props} />;
}

type TextareaProps = Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "className"> & { className?: string };

export function Textarea({ className, ...props }: TextareaProps) {
  return <textarea className={cn("cab-input", FOCUS_RING, className)} {...props} />;
}

/* ── Badge ───────────────────────────────────────────────── */

export type Tone = "success" | "warning" | "danger" | "info" | "neutral";

export function Badge({ tone = "neutral", children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <span className={cn("cab-badge", className)} data-tone={tone}>
      {children}
    </span>
  );
}

/* ── Chip (segmented option) ─────────────────────────────── */

type ChipProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className"> & {
  active?: boolean;
  className?: string;
  children: ReactNode;
};

export function Chip({ active, className, children, type = "button", ...props }: ChipProps) {
  return (
    <button type={type} className={cn("cab-chip", FOCUS_RING, className)} data-active={active ? "true" : "false"} {...props}>
      {children}
    </button>
  );
}

/* ── Inline notice ───────────────────────────────────────── */

export function Note({ tone, children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <p className={cn("cab-note", className)} data-tone={tone}>
      {children}
    </p>
  );
}
