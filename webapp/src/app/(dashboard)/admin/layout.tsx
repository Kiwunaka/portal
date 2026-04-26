"use client";

import AppRouteLink from "@/components/app-route-link";
import {
  AdminBadge,
  adminButtonClass,
  adminRailCardClass,
  adminSidebarClass,
  adminShellFrameClass,
  adminTopbarClass,
} from "@/components/admin/admin-shell";
import { usePortalSession } from "@/lib/session";
import { usePathname } from "next/navigation";
import { useMemo, type ReactNode } from "react";

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
    <main className="grid min-h-[72vh] place-items-center">
      <section className="w-full max-w-[760px] rounded-[1.35rem] border border-[#1a2732] bg-[#0b1218] p-8 text-slate-200 shadow-[0_34px_90px_-56px_rgba(2,6,23,0.94)]">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{eyebrow}</p>
        <h1 className="mt-3 text-[clamp(1.8rem,4vw,2.5rem)] font-semibold leading-tight tracking-[-0.05em] text-slate-50">{title}</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">{description}</p>
        <div className="mt-6 flex flex-wrap gap-3">
          <AppRouteLink href={primaryHref} className={adminButtonClass("primary")}>
            {primaryLabel}
          </AppRouteLink>
          <AppRouteLink href={MARKETING_SITE_URL} hardNavigate className={adminButtonClass("secondary")}>
            {pokrovBranding.siteLinkLabel}
          </AppRouteLink>
        </div>
      </section>
    </main>
  );
}

export default function AdminLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { error, loading, logoutWebSession, user, webLoginRequired } = usePortalSession();

  const activeItem = useMemo(() => findAdminNavItem(pathname), [pathname]);
  const activeCategory = useMemo(() => findAdminNavCategory(pathname), [pathname]);
  const siblingItems = activeCategory.items.filter((item) => item.href !== activeItem.href);

  if (loading) {
    return (
      <main className="grid min-h-[72vh] place-items-center">
        <section className="w-full rounded-[1.35rem] border border-[#1a2732] bg-[#0b1218] p-8 text-slate-200 shadow-[0_34px_90px_-56px_rgba(2,6,23,0.94)]">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">admin / pokrov</p>
          <h1 className="mt-3 text-[clamp(1.8rem,4vw,2.5rem)] font-semibold tracking-[-0.05em] text-slate-50">Открываем POKROV Admin...</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">Проверяем права доступа, текущую сессию и рабочую область оператора.</p>
          <div className="mt-6 h-2 overflow-hidden rounded-full bg-[#111922]">
            <div className="h-full w-1/3 animate-pulse rounded-full bg-slate-200" />
          </div>
        </section>
      </main>
    );
  }

  if (webLoginRequired) {
    return (
      <AdminStateCard
        eyebrow="сессия завершена"
        title="Войдите снова, чтобы открыть админку"
        description="Сессия в браузере закончилась. Повторите обычный вход, и рабочее пространство оператора вернётся."
        primaryHref="/"
        primaryLabel="Открыть вход"
      />
    );
  }

  if (error && !user) {
    return (
      <AdminStateCard
        eyebrow="не удалось проверить доступ"
        title="Не получилось подтвердить права администратора"
        description={error}
      />
    );
  }

  if (!user?.is_admin) {
    return (
      <AdminStateCard
        eyebrow="доступ ограничен"
        title="Этот раздел открыт только для администраторов"
        description="У текущего аккаунта нет операторских прав. Назначьте роль в системе и повторите вход."
      />
    );
  }

  return (
    <div className={adminShellFrameClass}>
      <div className="grid gap-4 p-4 2xl:grid-cols-[252px_minmax(0,1fr)_292px]">
        <aside className={`${adminSidebarClass} p-4 2xl:sticky 2xl:top-4 2xl:self-start`}>
          <div className="flex items-start justify-between gap-3 border-b border-[#17212b] pb-4">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">admin shell</p>
              <h1 className="mt-2 text-lg font-semibold tracking-[-0.04em] text-slate-50">POKROV Ops</h1>
              <p className="mt-2 text-xs leading-5 text-slate-400">Строгая навигация по смене: разделы, очереди, доступ, сеть и рабочие сообщения.</p>
            </div>
            <AdminBadge tone="accent">v2</AdminBadge>
          </div>

          <nav aria-label="Admin sections" className="mt-4 space-y-4">
            {ADMIN_NAV_GROUPS.map((group) => (
              <section key={group.id} className="space-y-2">
                <div className="px-1">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">{group.label}</p>
                  <p className="mt-1 text-[11px] leading-5 text-slate-500">{group.description}</p>
                </div>
                <div className="space-y-1.5">
                  {group.items.map((item) => {
                    const selected = item.href === activeItem.href;
                    return (
                      <AppRouteLink
                        key={item.href}
                        href={item.href}
                        aria-current={selected ? "page" : undefined}
                        className={
                          selected
                            ? "block rounded-[0.95rem] border border-[#3a4b58] bg-[#151f28] px-3 py-2.5 text-slate-50"
                            : "block rounded-[0.95rem] border border-transparent bg-transparent px-3 py-2.5 text-slate-300 transition hover:border-[#21303b] hover:bg-[#111922] hover:text-slate-100"
                        }
                      >
                        <span className="block text-sm font-semibold">{item.label}</span>
                        <span className={selected ? "mt-1 block text-xs leading-5 text-slate-400" : "mt-1 block text-xs leading-5 text-slate-500"}>
                          {item.summary}
                        </span>
                      </AppRouteLink>
                    );
                  })}
                </div>
              </section>
            ))}
          </nav>
        </aside>

        <section className="min-w-0 space-y-4">
          <header className={`${adminTopbarClass} p-4`}>
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <AdminBadge tone="accent">{activeCategory.label}</AdminBadge>
                  <AdminBadge>{activeItem.label}</AdminBadge>
                  <AdminBadge tone="success">Веб-админка — основной путь</AdminBadge>
                </div>
                <h1 className="mt-3 text-[1.55rem] font-semibold tracking-[-0.04em] text-slate-50">Админка POKROV</h1>
                <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">
                  Веб-админка — основной операторский интерфейс. Telegram используйте только для быстрых fallback-действий.
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                <AppRouteLink href="/dashboard/" className={adminButtonClass("secondary", "sm")}>
                  Вернуться в кабинет
                </AppRouteLink>
                <AppRouteLink href={MARKETING_SITE_URL} hardNavigate className={adminButtonClass("secondary", "sm")}>
                  {pokrovBranding.siteLinkLabel}
                </AppRouteLink>
                <button type="button" onClick={logoutWebSession} className={adminButtonClass("danger", "sm")}>
                  Сменить аккаунт
                </button>
              </div>
            </div>

            <div className="mt-4 flex flex-wrap gap-2 border-t border-[#17212b] pt-4">
              {ADMIN_NAV_GROUPS.map((group) => {
                const selected = group.id === activeCategory.id;
                return (
                  <AppRouteLink
                    key={group.id}
                    href={group.items[0]?.href || "/admin/dashboard"}
                    aria-label={`Категория ${group.label}`}
                    className={
                      selected
                        ? "inline-flex min-h-8 items-center rounded-full border border-[#415362] bg-[#18232c] px-3 text-[11px] font-semibold text-slate-100"
                        : "inline-flex min-h-8 items-center rounded-full border border-[#23313d] bg-[#0f171f] px-3 text-[11px] font-semibold text-slate-400 transition hover:border-[#314251] hover:text-slate-200"
                    }
                  >
                    {group.label}
                  </AppRouteLink>
                );
              })}
            </div>
          </header>

          <div className="min-w-0">{children}</div>
        </section>

        <aside className="space-y-4 2xl:sticky 2xl:top-4 2xl:self-start">
          <section className={adminRailCardClass}>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Текущий контекст</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-50">{activeItem.label}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">{activeItem.summary}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <AdminBadge tone="accent">{activeCategory.label}</AdminBadge>
              <AdminBadge>{activeCategory.primaryHint}</AdminBadge>
            </div>
          </section>

          <section className={adminRailCardClass}>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Рядом по теме</p>
            <div className="mt-3 space-y-2">
              {siblingItems.length ? (
                siblingItems.map((item) => (
                  <AppRouteLink
                    key={item.href}
                    href={item.href}
                    className="block rounded-[0.95rem] border border-[#22303c] bg-[#0c131a] px-3 py-2.5 transition hover:border-[#304251] hover:bg-[#111922]"
                  >
                    <span className="block text-sm font-semibold text-slate-100">{item.label}</span>
                    <span className="mt-1 block text-xs leading-5 text-slate-500">{item.summary}</span>
                  </AppRouteLink>
                ))
              ) : (
                <p className="text-xs leading-5 text-slate-500">В этой категории пока один рабочий экран.</p>
              )}
            </div>
          </section>

          <section className={adminRailCardClass}>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Операторский режим</p>
            <div className="mt-3 space-y-2 text-xs leading-5 text-slate-400">
              <p>Сначала смотрите очередь, свежесть данных и тревоги. Потом переходите к точечным действиям.</p>
              <p>Не растаскивайте смену по чатам: рабочая навигация, таблицы и карточки должны жить здесь.</p>
              <p>Telegram оставляйте только как запасной канал, когда нужно быстро добить уже понятный кейс.</p>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
