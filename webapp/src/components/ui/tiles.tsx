import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { ChevronRight } from "lucide-react";

import AppRouteLink from "@/components/app-route-link";
import type { Tone } from "@/components/ui/badge";
import { cn } from "@/components/utils";

const TILE_ICON_TONE: Record<Tone, string> = {
  success: "bg-ok-bg text-ok-text",
  warning: "bg-warn-bg text-warn-text",
  danger: "bg-danger-bg text-danger-text",
  info: "bg-info-bg text-info-text",
  neutral: "bg-canvas-alt text-brand",
};

export function TileGrid({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("grid grid-cols-2 gap-3 xl:grid-cols-4", className)}>{children}</div>;
}

export function Tile({
  icon: Icon,
  label,
  value,
  hint,
  tone = "neutral",
  href,
  className,
}: {
  icon?: LucideIcon;
  label: ReactNode;
  value: ReactNode;
  hint?: ReactNode;
  tone?: Tone;
  href?: string;
  className?: string;
}) {
  const content = (
    <>
      <span className="flex items-center justify-between">
        {Icon ? (
          <span className={cn("grid size-9 place-items-center rounded-[10px]", TILE_ICON_TONE[tone])}>
            <Icon size={18} strokeWidth={2} aria-hidden="true" />
          </span>
        ) : (
          <span />
        )}
        {href ? <ChevronRight size={18} strokeWidth={2} aria-hidden="true" className="text-ink-muted" /> : null}
      </span>
      <span className="mt-3 block truncate text-lg font-bold text-ink">{value}</span>
      <span className="block text-[13px] font-medium text-ink-soft">{label}</span>
      {hint ? <span className="mt-0.5 block text-xs text-ink-muted">{hint}</span> : null}
    </>
  );

  const classes = cn(
    "block rounded-card border border-line bg-surface p-4 shadow-soft",
    href &&
      "transition-[transform,box-shadow,border-color] duration-200 ease-apple hover:-translate-y-px hover:border-line-strong hover:shadow-medium motion-reduce:transition-none motion-reduce:hover:translate-y-0",
    className,
  );

  if (href) {
    return (
      <AppRouteLink href={href} className={classes}>
        {content}
      </AppRouteLink>
    );
  }
  return <div className={classes}>{content}</div>;
}

export function ActionGrid({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("grid gap-3 sm:grid-cols-2", className)}>{children}</div>;
}

export function ActionCard({
  icon: Icon,
  title,
  hint,
  href,
  className,
}: {
  icon?: LucideIcon;
  title: ReactNode;
  hint?: ReactNode;
  href: string;
  className?: string;
}) {
  return (
    <AppRouteLink
      href={href}
      className={cn(
        "group flex items-center gap-3 rounded-card border border-line bg-surface p-4 shadow-soft transition-[transform,box-shadow,border-color] duration-200 ease-apple hover:-translate-y-px hover:border-line-strong hover:shadow-medium motion-reduce:transition-none motion-reduce:hover:translate-y-0",
        className,
      )}
    >
      {Icon ? (
        <span className="grid size-10 shrink-0 place-items-center rounded-[12px] bg-brand-soft text-brand">
          <Icon size={19} strokeWidth={2} aria-hidden="true" />
        </span>
      ) : null}
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-semibold text-ink">{title}</span>
        {hint ? <span className="mt-0.5 block text-[13px] leading-5 text-ink-muted">{hint}</span> : null}
      </span>
      <ChevronRight
        size={18}
        strokeWidth={2}
        aria-hidden="true"
        className="shrink-0 text-ink-muted transition-transform duration-200 group-hover:translate-x-0.5 motion-reduce:transition-none motion-reduce:group-hover:translate-x-0"
      />
    </AppRouteLink>
  );
}
