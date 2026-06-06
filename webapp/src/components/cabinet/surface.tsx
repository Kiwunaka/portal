"use client";

import type { ReactNode } from "react";

import AppRouteLink from "@/components/app-route-link";
import { cn } from "@/components/utils";

export type CabinetTone = "success" | "warning" | "danger" | "info" | "neutral";

const LABEL_CLASS = "text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400";

const STATUS_TONE_CLASSES: Record<CabinetTone, string> = {
  success: "border-emerald-200/70 bg-emerald-50/80 text-emerald-950 dark:border-emerald-500/25 dark:bg-emerald-500/10 dark:text-emerald-100",
  warning: "border-amber-200/80 bg-amber-50/85 text-amber-950 dark:border-amber-500/25 dark:bg-amber-500/10 dark:text-amber-100",
  danger: "border-rose-200/80 bg-rose-50/85 text-rose-950 dark:border-rose-500/25 dark:bg-rose-500/10 dark:text-rose-100",
  info: "border-sky-200/80 bg-sky-50/85 text-sky-950 dark:border-sky-500/25 dark:bg-sky-500/10 dark:text-sky-100",
  neutral: "border-slate-200/80 bg-white/86 text-slate-950 dark:border-white/10 dark:bg-white/[0.05] dark:text-slate-50",
};

type CabinetStatusProps = {
  title: ReactNode;
  meta?: ReactNode;
  body?: ReactNode;
  tone?: CabinetTone;
  action?: ReactNode;
  children?: ReactNode;
  className?: string;
};

export function CabinetStatus({ title, meta, body, tone = "neutral", action, children, className }: CabinetStatusProps) {
  return (
    <section className={cn("rounded-2xl border p-4 sm:p-5", STATUS_TONE_CLASSES[tone], className)}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          {meta ? <p className="text-[13px] font-medium leading-5 opacity-75">{meta}</p> : null}
          <h1 className="mt-1 text-[1.45rem] font-semibold leading-tight tracking-[-0.02em] sm:text-[1.65rem]">{title}</h1>
          {body ? <p className="mt-2 max-w-2xl text-sm leading-6 opacity-80">{body}</p> : null}
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
      {children ? <div className="mt-4 border-t border-current/10 pt-4">{children}</div> : null}
    </section>
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
    <section className={cn("space-y-2", className)}>
      {(title || action) ? (
        <div className="flex items-center justify-between gap-3 px-1">
          {title ? <h2 className={LABEL_CLASS}>{title}</h2> : <span />}
          {action ? <div className="shrink-0">{action}</div> : null}
        </div>
      ) : null}
      <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white/86 shadow-[0_18px_44px_-36px_rgba(15,23,42,0.18)] dark:border-white/10 dark:bg-white/[0.04]">
        {children}
      </div>
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
      {icon ? (
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-emerald-50 text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-200">
          {icon}
        </span>
      ) : null}
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-semibold text-slate-950 dark:text-slate-50">{label}</span>
        {hint ? <span className="mt-0.5 block truncate text-[13px] leading-5 text-slate-500 dark:text-slate-400">{hint}</span> : null}
      </span>
      {value ? <span className="min-w-0 max-w-[48%] truncate text-right text-sm font-medium text-slate-600 dark:text-slate-300">{value}</span> : null}
      {action ? <span className="shrink-0">{action}</span> : null}
      {href ? <span className="material-symbols-rounded shrink-0 text-[19px] text-slate-400">chevron_right</span> : null}
    </>
  );
  const classes = cn(
    "flex min-h-[58px] items-center gap-3 border-b border-slate-200/70 px-4 py-3 last:border-b-0 dark:border-white/8",
    href ? "transition hover:bg-slate-50/80 active:scale-[0.99] active:opacity-80 dark:hover:bg-white/[0.03]" : "",
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
