"use client";

import AppRouteLink from "@/components/app-route-link";
import { usePortalSession } from "@/lib/session";
import { ADMIN_NAV_GROUPS } from "./nav";

function AdminHomeSkeleton() {
  return (
    <section className="space-y-5" aria-busy="true" aria-live="polite">
      {Array.from({ length: 3 }).map((_, groupIndex) => (
        <section key={groupIndex} className="glass-card rounded-3xl p-5 sm:p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0 flex-1">
              <div className="h-3 w-28 animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
              <div className="mt-4 h-8 w-52 animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
              <div className="mt-4 space-y-2">
                <div className="h-4 w-full animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
                <div className="h-4 w-5/6 animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
              </div>
            </div>
            <div className="h-11 w-11 animate-pulse rounded-2xl bg-violet-600/10 dark:bg-violet-500/15" />
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 3 }).map((_, itemIndex) => (
              <div key={itemIndex} className="glass-card h-28 rounded-2xl border border-white/40 px-4 py-4 dark:border-white/10">
                <div className="h-5 w-32 animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
                <div className="mt-4 space-y-2">
                  <div className="h-4 w-full animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
                  <div className="h-4 w-4/5 animate-pulse rounded-full bg-slate-200 dark:bg-white/10" />
                </div>
              </div>
            ))}
          </div>
        </section>
      ))}
    </section>
  );
}

export default function AdminHomePage() {
  const { loading } = usePortalSession();

  if (loading) {
    return <AdminHomeSkeleton />;
  }

  return (
    <section className="space-y-5">
      {ADMIN_NAV_GROUPS.map((group) => (
        <section key={group.id} className="glass-card rounded-3xl p-5 sm:p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0">
              <p className="font-mono text-xs uppercase tracking-[0.14em] text-violet-500 dark:text-violet-300">
                {group.primaryHint}
              </p>
              <h2 className="mt-2 font-display text-2xl font-semibold">{group.label}</h2>
              <p className="mt-2 max-w-3xl text-sm text-slate-600 dark:text-slate-300">{group.description}</p>
            </div>
            <div className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-violet-600/10 text-violet-600 dark:bg-violet-500/15 dark:text-violet-200">
              <span className="material-symbols-rounded">{group.icon}</span>
            </div>
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {group.items.map((item) => (
              <AppRouteLink
                key={item.href}
                href={item.href}
                className="glass-card haptic-tap rounded-2xl border border-white/40 px-4 py-4 transition hover:scale-[1.01] hover:border-violet-200/70 dark:border-white/10 dark:hover:border-violet-500/30"
              >
                <div className="flex min-w-0 items-center gap-2">
                  <span className="material-symbols-rounded text-violet-600 dark:text-violet-300">{item.icon}</span>
                  <h3 className="min-w-0 truncate font-display text-lg font-semibold">{item.label}</h3>
                </div>
                <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">{item.summary}</p>
              </AppRouteLink>
            ))}
          </div>
        </section>
      ))}
    </section>
  );
}
