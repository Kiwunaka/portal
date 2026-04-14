"use client";

import AppRouteLink from "@/components/app-route-link";
import { usePortalSession } from "@/lib/session";
import { Shield } from "lucide-react";
import { usePathname } from "next/navigation";
import { useMemo } from "react";
import { pokrovBranding } from "../../branding";
import { ADMIN_NAV_GROUPS, findAdminNavCategory, findAdminNavItem } from "./nav";

const MARKETING_SITE_URL = pokrovBranding.marketingUrl;

function AdminStateCard({
  eyebrow,
  title,
  description,
  primaryHref = "/dashboard/",
  primaryLabel = "Вернуться в кабинет",
}: {
  eyebrow: string;
  title: string;
  description: string;
  primaryHref?: string;
  primaryLabel?: string;
}) {
  return (
    <main className="space-y-4">
      <section className="glass-card p-6">
        <p className="font-mono text-xs uppercase tracking-[0.15em] text-rose-500">{eyebrow}</p>
        <h1 className="mt-2 font-display text-3xl font-bold">{title}</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{description}</p>
        <div className="mt-4 flex flex-wrap gap-3">
          <AppRouteLink
            href={primaryHref}
            className="outline-btn inline-flex w-full justify-center rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em] sm:w-auto"
          >
            {primaryLabel}
          </AppRouteLink>
          <AppRouteLink
            href={MARKETING_SITE_URL}
            hardNavigate
            className="outline-btn inline-flex w-full justify-center rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em] sm:w-auto"
          >
            {pokrovBranding.siteLinkLabel}
          </AppRouteLink>
        </div>
      </section>
    </main>
  );
}

function AdminGroupedNav({ activeHref }: { activeHref: string }) {
  return (
    <section className="glass-card p-4 sm:p-5">
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
            Workspace map
          </p>
          <h2 className="mt-1 font-display text-2xl font-semibold text-slate-900 dark:text-slate-50">
            Категории админки
          </h2>
        </div>
        <p className="max-w-xl text-xs leading-6 text-slate-500 dark:text-slate-400">
          Рабочие сценарии сгруппированы по зонам, чтобы быстрее находить нужный раздел и не уводить оператора в
          Telegram без необходимости.
        </p>
      </div>

      <nav aria-label="Admin sections" className="grid gap-3 lg:grid-cols-2 2xl:grid-cols-3">
        {ADMIN_NAV_GROUPS.map((group) => (
          <article
            key={group.id}
            className="rounded-[1.4rem] border border-white/60 bg-white/60 p-4 dark:border-white/10 dark:bg-white/[0.04]"
          >
            <div className="flex items-start gap-3">
              <div className="stat-icon stat-icon-violet h-10 w-10 shrink-0">
                <span className="material-symbols-rounded text-base" style={{ fontSize: "18px" }}>
                  {group.icon}
                </span>
              </div>
              <div className="min-w-0">
                <p className="font-display text-lg font-semibold text-slate-900 dark:text-slate-50">{group.label}</p>
                <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">{group.description}</p>
              </div>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              {group.items.map((item) => {
                const selected = item.href === activeHref;
                return (
                  <AppRouteLink
                    key={item.href}
                    href={item.href}
                    className={`inline-flex min-w-0 items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold transition-all ${
                      selected
                        ? "bg-gradient-to-r from-violet-600 to-violet-700 text-white shadow-lg shadow-violet-600/20"
                        : "bg-white/80 text-slate-700 hover:bg-white dark:bg-white/[0.06] dark:text-slate-200 dark:hover:bg-white/[0.1]"
                    }`}
                  >
                    <span className="material-symbols-rounded text-sm" style={{ fontSize: "15px" }}>
                      {item.icon}
                    </span>
                    <span>{item.label}</span>
                  </AppRouteLink>
                );
              })}
            </div>
          </article>
        ))}
      </nav>
    </section>
  );
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { error, loading, user, webLoginRequired } = usePortalSession();

  const activeItem = useMemo(() => findAdminNavItem(pathname), [pathname]);
  const activeCategory = useMemo(() => findAdminNavCategory(pathname), [pathname]);

  if (loading) {
    return (
      <main className="space-y-4">
        <section className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.15em] text-slate-500">admin / pokrov</p>
          <h1 className="mt-2 font-display text-3xl font-bold">Открываем POKROV Admin...</h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
            Подгружаем права доступа, рабочие категории и навигацию по операторским разделам.
          </p>
          <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-200/60 dark:bg-slate-800">
            <div className="h-full w-1/3 animate-pulse rounded-full bg-violet-600" />
          </div>
        </section>
      </main>
    );
  }

  if (webLoginRequired) {
    return (
      <AdminStateCard
        eyebrow="сессия истекла"
        title="Нужно заново подтвердить вход"
        description="Браузерная сессия закончилась. Просто войдите через Telegram ещё раз, и админка откроется без дополнительных действий."
        primaryHref="/"
        primaryLabel="Открыть вход"
      />
    );
  }

  if (error && !user) {
    return (
      <AdminStateCard
        eyebrow="ошибка доступа"
        title="Не удалось проверить права администратора"
        description={error}
      />
    );
  }

  if (!user?.is_admin) {
    return (
      <AdminStateCard
        eyebrow="доступ закрыт"
        title="Раздел только для администраторов"
        description="У этого аккаунта нет прав администратора. Если доступ нужен для работы, назначьте роль в системе и попробуйте снова."
      />
    );
  }

  return (
    <main className="space-y-5">
      <section className="stat-card p-5 sm:p-6">
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.5fr),minmax(320px,0.9fr)]">
          <div className="flex min-w-0 gap-4">
            <div className="stat-icon stat-icon-violet">
              <Shield size={22} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="font-mono text-xs uppercase tracking-[0.15em] text-violet-500 dark:text-violet-300">
                admin / pokrov
              </p>
              <h1 className="mt-1 font-display text-3xl font-bold">POKROV Admin</h1>
              <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
                Веб-админка — основной операторский интерфейс. Telegram используйте только для быстрых
                fallback-действий.
              </p>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <div className="rounded-[1.25rem] border border-white/70 bg-white/72 p-4 dark:border-white/10 dark:bg-white/[0.04]">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                Cross-surface route
              </p>
              <div className="mt-3 flex flex-wrap gap-3">
                <AppRouteLink
                  href="/dashboard/"
                  className="outline-btn inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em]"
                >
                  Вернуться в кабинет
                </AppRouteLink>
                <AppRouteLink
                  href={MARKETING_SITE_URL}
                  hardNavigate
                  className="outline-btn inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em]"
                >
                  {pokrovBranding.siteLinkLabel}
                </AppRouteLink>
              </div>
            </div>

            <div className="rounded-[1.25rem] border border-violet-200/60 bg-white/70 p-4 dark:border-violet-500/20 dark:bg-white/[0.05]">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                Сейчас в фокусе
              </p>
              <p className="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-50">
                {activeCategory.label} / {activeItem.label}
              </p>
              <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">{activeItem.summary}</p>
            </div>

            <div className="rounded-[1.25rem] border border-emerald-200/60 bg-emerald-50/80 p-4 dark:border-emerald-500/20 dark:bg-emerald-500/10">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-700 dark:text-emerald-200">
                Primary ops surface
              </p>
              <p className="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-50">Сначала работайте здесь</p>
              <p className="mt-1 text-xs leading-5 text-slate-600 dark:text-slate-300">{activeCategory.primaryHint}</p>
            </div>
          </div>
        </div>
      </section>

      <AdminGroupedNav activeHref={activeItem.href} />

      {children}
    </main>
  );
}
