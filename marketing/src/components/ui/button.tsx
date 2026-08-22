import Link from "next/link";
import type { AnchorHTMLAttributes, ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "../utils";

type ButtonVariant = "primary" | "secondary" | "ghost";
type ButtonSize = "md" | "lg";

const BASE =
  "inline-flex min-h-11 items-center justify-center gap-2 whitespace-nowrap rounded-full font-semibold no-underline transition-[transform,background-color,border-color,box-shadow] duration-200 ease-(--ease-apple) select-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand active:scale-[0.98]";

const VARIANTS: Record<ButtonVariant, string> = {
  primary: "bg-brand-strong text-ink-inverse shadow-soft hover:brightness-90",
  secondary:
    "border border-line bg-surface text-ink shadow-soft hover:border-line-strong hover:bg-surface-subtle",
  ghost: "text-ink hover:bg-canvas-alt",
};

const SIZES: Record<ButtonSize, string> = {
  md: "px-5 py-2.5 text-[0.9375rem]",
  lg: "px-7 py-3.5 text-base",
};

type CommonProps = {
  children: ReactNode;
  className?: string;
  size?: ButtonSize;
  variant?: ButtonVariant;
};

type ButtonAsLink = CommonProps & { href: string } & Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href" | "className">;
type ButtonAsButton = CommonProps & { href?: undefined } & Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className">;

export type ButtonProps = ButtonAsLink | ButtonAsButton;

export function Button(props: ButtonProps) {
  const { children, className, size = "md", variant = "primary" } = props;
  const classes = cn(BASE, VARIANTS[variant], SIZES[size], className);

  if (props.href !== undefined) {
    const { href, size: _s, variant: _v, className: _c, children: _ch, ...anchorProps } = props;
    const isInternal = href.startsWith("/") || href.startsWith("#");
    if (isInternal) {
      return (
        <Link href={href} className={classes} {...anchorProps}>
          {children}
        </Link>
      );
    }
    return (
      <a href={href} className={classes} {...anchorProps}>
        {children}
      </a>
    );
  }

  const { size: _s, variant: _v, className: _c, children: _ch, ...buttonProps } = props;
  return (
    <button type="button" className={classes} {...buttonProps}>
      {children}
    </button>
  );
}
