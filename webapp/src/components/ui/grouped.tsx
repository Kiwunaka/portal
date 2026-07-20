import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { ChevronRight } from "lucide-react";

import AppRouteLink from "@/components/app-route-link";
import { cn } from "@/components/utils";

/** iOS grouped-list canon: white grouped box on canvas_alt, inset separators,
 * chevron affordance for navigation rows. */
export function GroupedSection({
  title,
  action,
  children,
  className,
}: {
  title?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("flex flex-col gap-2", className)}>
      {title || action ? (
        <div className="flex items-center justify-between gap-3 px-1">
          {title ? <h2 className="text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">{title}</h2> : <span />}
          {action ? <div className="shrink-0">{action}</div> : null}
        </div>
      ) : null}
      <div className="divide-y divide-line overflow-hidden rounded-card border border-line bg-surface shadow-soft">
        {children}
      </div>
    </section>
  );
}

export function Row({
  icon: Icon,
  label,
  value,
  hint,
  action,
  href,
  onClick,
  className,
}: {
  icon?: LucideIcon;
  label: ReactNode;
  value?: ReactNode;
  hint?: ReactNode;
  action?: ReactNode;
  href?: string;
  onClick?: () => void;
  className?: string;
}) {
  const content = (
    <>
      {Icon ? (
        <span className="grid size-9 shrink-0 place-items-center rounded-[10px] bg-brand-soft text-brand">
          <Icon size={18} strokeWidth={2} aria-hidden="true" />
        </span>
      ) : null}
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-semibold text-ink">{label}</span>
        {hint ? <span className="mt-0.5 block truncate text-[13px] leading-5 text-ink-soft">{hint}</span> : null}
      </span>
      {value ? <span className="max-w-[48%] min-w-0 truncate text-right text-sm font-medium text-ink-soft">{value}</span> : null}
      {action ? <span className="shrink-0">{action}</span> : null}
      {href || onClick ? (
        <ChevronRight
          size={18}
          strokeWidth={2}
          aria-hidden="true"
          className="shrink-0 text-ink-muted transition-transform duration-200 group-hover/row:translate-x-0.5 motion-reduce:transition-none motion-reduce:group-hover/row:translate-x-0"
        />
      ) : null}
    </>
  );

  const classes = cn(
    "group/row flex min-h-[52px] w-full items-center gap-3 px-4 py-2.5 text-left",
    (href || onClick) && "transition-colors duration-150 hover:bg-canvas-alt active:bg-nav-hover motion-reduce:transition-none",
    className,
  );

  if (href) {
    return (
      <AppRouteLink href={href} className={classes}>
        {content}
      </AppRouteLink>
    );
  }
  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={classes}>
        {content}
      </button>
    );
  }
  return <div className={classes}>{content}</div>;
}
