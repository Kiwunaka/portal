"use client";

import AppRouteLink from "@/components/app-route-link";
import { AdminBadge, adminButtonClass, adminPanelClass } from "@/components/admin/admin-shell";
import { ArrowRight } from "lucide-react";
import type { ReactNode } from "react";

export type DashboardTone = "neutral" | "success" | "warning" | "danger" | "accent";

export const adminUserQueueGridClass = "grid grid-cols-[minmax(0,1.4fr)_112px_116px_104px] gap-3";

export function MiniBars({
  values,
  tone = "emerald",
  label,
}: {
  values: number[];
  tone?: "emerald" | "slate" | "rose";
  label: string;
}) {
  if (!values.length) return null;
  const max = Math.max(...values, 1);
  const colorClass = tone === "rose" ? "bg-rose-500" : tone === "slate" ? "bg-slate-400" : "bg-emerald-500";

  return (
    <div className="flex h-9 items-end gap-[4px]" role="img" aria-label={label}>
      {values.map((value, index) => (
        <div
          key={index}
          className={`w-[7px] rounded-sm ${colorClass}`}
          style={{ height: `${Math.max(10, (Number(value || 0) / max) * 100)}%`, opacity: 0.36 + (Number(value || 0) / max) * 0.64 }}
        />
      ))}
    </div>
  );
}

export function DashboardCell({
  title,
  subtitle,
  actions,
  children,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <article className={adminPanelClass("neutral")}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
          {subtitle ? <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500">{subtitle}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
      </div>
      <div className="mt-4">{children}</div>
    </article>
  );
}

export function ShiftMetric({
  label,
  value,
  hint,
  tone = "neutral",
  icon,
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  tone?: DashboardTone;
  icon: ReactNode;
}) {
  const palette = {
    neutral: "border-slate-200 bg-white/70 text-slate-700",
    success: "border-emerald-200 bg-emerald-50/70 text-emerald-800",
    warning: "border-amber-200 bg-amber-50/70 text-amber-800",
    danger: "border-rose-200 bg-rose-50/70 text-rose-800",
    accent: "border-sky-200 bg-sky-50/70 text-sky-800",
  }[tone];

  return (
    <div className={`min-h-[108px] rounded-[0.95rem] border p-3 ${palette}`}>
      <div className="flex items-start justify-between gap-3">
        <p className="text-[10px] font-semibold uppercase tracking-[0.16em] opacity-70">{label}</p>
        <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-[0.75rem] border border-current/15 bg-white/55">
          {icon}
        </span>
      </div>
      <p className="mt-3 font-mono text-[1.55rem] font-semibold leading-none text-slate-950">{value}</p>
      {hint ? <p className="mt-2 text-xs leading-5 text-slate-500">{hint}</p> : null}
    </div>
  );
}

export function SignalRow({
  title,
  body,
  tone,
}: {
  title: string;
  body: string;
  tone: Exclude<DashboardTone, "neutral">;
}) {
  const label = tone === "danger" ? "Риск" : tone === "warning" ? "Проверить" : tone === "success" ? "Норма" : "Очередь";

  return (
    <div className="grid gap-3 border-b border-slate-200/60 py-3 last:border-b-0 md:grid-cols-[minmax(0,1fr)_92px]">
      <div className="min-w-0">
        <p className="text-sm font-semibold text-slate-900">{title}</p>
        <p className="mt-1 text-xs leading-5 text-slate-500">{body}</p>
      </div>
      <div className="md:text-right">
        <AdminBadge tone={tone}>{label}</AdminBadge>
      </div>
    </div>
  );
}

export function WorkQueueCard({
  title,
  value,
  hint,
  href,
  tone = "neutral",
}: {
  title: string;
  value: ReactNode;
  hint: ReactNode;
  href: string;
  tone?: DashboardTone;
}) {
  return (
    <AppRouteLink
      href={href}
      className="group block rounded-[0.95rem] border border-slate-200/70 bg-white/65 p-3 transition hover:border-emerald-300 hover:bg-emerald-50/35 active:translate-y-[1px]"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">{title}</p>
          <p className="mt-2 font-mono text-2xl font-semibold leading-none text-slate-950">{value}</p>
        </div>
        <AdminBadge tone={tone}>
          <ArrowRight aria-hidden className="h-3.5 w-3.5 transition group-hover:translate-x-0.5" />
        </AdminBadge>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-500">{hint}</p>
    </AppRouteLink>
  );
}

export function CompactTableShell({ children }: { children: ReactNode }) {
  return <div className="overflow-hidden rounded-[1rem] border border-slate-200/70 bg-white/60">{children}</div>;
}

export function AdminDashboardSkeleton() {
  return (
    <section className="space-y-4" aria-busy="true" aria-live="polite">
      <div className="h-28 animate-pulse rounded-[1rem] bg-slate-200/80" />
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-28 animate-pulse rounded-[1rem] bg-slate-200/80" />
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-72 animate-pulse rounded-[1rem] bg-slate-200/80" />
        ))}
      </div>
    </section>
  );
}
