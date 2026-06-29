"use client";

import type { ReactNode } from "react";

import AppRouteLink from "@/components/app-route-link";
import { CabinetIcon } from "@/components/cabinet/icon";
import { cn } from "@/components/utils";

export type CabinetTone = "success" | "warning" | "danger" | "info" | "neutral";

type CabinetStatusProps = {
  title: ReactNode;
  meta?: ReactNode;
  body?: ReactNode;
  tone?: CabinetTone;
  action?: ReactNode;
  emblem?: ReactNode;
  children?: ReactNode;
  className?: string;
};

export function CabinetStatus({ title, meta, body, tone = "neutral", action, emblem, children, className }: CabinetStatusProps) {
  return (
    <section className={cn("cab-status", className)} data-tone={tone}>
      <div className="cab-status-glow" aria-hidden="true" />
      <div className="relative flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-4">
          {emblem ? <span className="cab-status-emblem" aria-hidden="true">{emblem}</span> : null}
          <div className="min-w-0">
            {meta ? <p className="text-[13px] font-medium leading-5 opacity-75">{meta}</p> : null}
            <h1 className="mt-1 text-[1.45rem] font-semibold leading-tight tracking-[-0.02em] sm:text-[1.6rem]">{title}</h1>
            {body ? <p className="mt-2 max-w-2xl text-sm leading-6 opacity-80">{body}</p> : null}
          </div>
        </div>
        {action ? <div className="relative shrink-0">{action}</div> : null}
      </div>
      {children ? <div className="relative mt-4 border-t border-current/10 pt-4">{children}</div> : null}
    </section>
  );
}

type CabinetTilesProps = { children: ReactNode; className?: string };

export function CabinetTiles({ children, className }: CabinetTilesProps) {
  return <div className={cn("cab-tiles", className)}>{children}</div>;
}

type CabinetTileProps = {
  icon?: ReactNode;
  label: ReactNode;
  value: ReactNode;
  hint?: ReactNode;
  tone?: CabinetTone;
  href?: string;
  className?: string;
};

export function CabinetTile({ icon, label, value, hint, tone = "neutral", href, className }: CabinetTileProps) {
  const content = (
    <>
      <span className="flex items-center justify-between">
        {icon ? <span className="cab-tileicon" data-tone={tone}>{icon}</span> : <span />}
        {href ? <CabinetIcon name="chevron_right" className="h-[18px] w-[18px] text-[color:var(--atlas-text-muted)] transition-transform duration-200" /> : null}
      </span>
      <span className="cab-tilevalue">{value}</span>
      <span className="cab-tilelabel">{label}</span>
      {hint ? <span className="cab-tilehint">{hint}</span> : null}
    </>
  );
  const classes = cn("cab-tile", href ? "cab-tile--link" : "", className);
  if (href) {
    return (
      <AppRouteLink href={href} className={classes}>
        {content}
      </AppRouteLink>
    );
  }
  return <div className={classes}>{content}</div>;
}

type CabinetActionGridProps = { children: ReactNode; className?: string };

export function CabinetActionGrid({ children, className }: CabinetActionGridProps) {
  return <div className={cn("cab-actiongrid", className)}>{children}</div>;
}

type CabinetActionCardProps = {
  icon?: ReactNode;
  title: ReactNode;
  hint?: ReactNode;
  href: string;
  className?: string;
};

export function CabinetActionCard({ icon, title, hint, href, className }: CabinetActionCardProps) {
  return (
    <AppRouteLink href={href} className={cn("cab-actioncard", className)}>
      {icon ? <span className="cab-actionicon">{icon}</span> : null}
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-semibold text-[color:var(--atlas-text)]">{title}</span>
        {hint ? <span className="mt-0.5 block text-[13px] leading-5 text-[color:var(--atlas-text-muted)]">{hint}</span> : null}
      </span>
      <CabinetIcon name="chevron_right" className="cab-actionarrow h-[18px] w-[18px] shrink-0 text-[color:var(--atlas-text-muted)]" />
    </AppRouteLink>
  );
}

type CabinetGroupProps = {
  title?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function CabinetGroup({ title, action, children, className }: CabinetGroupProps) {
  return (
    <section className={cn("flex flex-col gap-2", className)}>
      {title || action ? (
        <div className="flex items-center justify-between gap-3 px-1">
          {title ? <h2 className="cab-eyebrow">{title}</h2> : <span />}
          {action ? <div className="shrink-0">{action}</div> : null}
        </div>
      ) : null}
      <div className="cab-panel">{children}</div>
    </section>
  );
}

type CabinetRowProps = {
  icon?: ReactNode;
  label: ReactNode;
  value?: ReactNode;
  hint?: ReactNode;
  action?: ReactNode;
  href?: string;
  className?: string;
};

export function CabinetRow({ icon, label, value, hint, action, href, className }: CabinetRowProps) {
  const content = (
    <>
      {icon ? <span className="cab-rowicon">{icon}</span> : null}
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-semibold text-[color:var(--atlas-text)]">{label}</span>
        {hint ? <span className="mt-0.5 block truncate text-[13px] leading-5 text-[color:var(--atlas-text-muted)]">{hint}</span> : null}
      </span>
      {value ? (
        <span className="min-w-0 max-w-[48%] truncate text-right text-sm font-medium text-[color:var(--atlas-text-soft)]">{value}</span>
      ) : null}
      {action ? <span className="shrink-0">{action}</span> : null}
      {href ? <CabinetIcon name="chevron_right" className="h-[18px] w-[18px] shrink-0 text-[color:var(--atlas-text-muted)]" /> : null}
    </>
  );

  const classes = cn("cab-row", href ? "cab-row--link" : "", className);

  if (href) {
    return (
      <AppRouteLink href={href} className={classes}>
        {content}
      </AppRouteLink>
    );
  }

  return <div className={classes}>{content}</div>;
}
