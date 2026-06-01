"use client";

import AppRouteLink from "@/components/app-route-link";
import {
  AdminBadge,
  adminButtonClass,
  adminRailCardClass,
  adminSidebarClass,
  adminTopbarClass,
} from "@/components/admin/admin-shell";
import { adminSummary, type AdminSummaryPayload } from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { pokrovBranding } from "../../branding";
import { ADMIN_NAV_GROUPS, findAdminNavCategory, findAdminNavItem } from "./nav";

const MARKETING_SITE_URL = pokrovBranding.marketingUrl;

function formatOperatorName(user: { display_name?: string | null; username?: string | null; tg_id?: number | null } | null): string {
  if (!user) return "Оператор";
  return user.display_name || (user.username ? `@${user.username}` : user.tg_id ? `ID ${user.tg_id}` : "Оператор");
}

function adminAttentionCount(summary: AdminSummaryPayload | null, href: string): number {
  if (!summary) return 0;
  if (href.startsWith("/admin/tickets")) return Number(summary.tickets.open || 0);
  if (href.startsWith("/admin/payments")) return Number(summary.errors.payment_callback_failures_24h || 0);
  if (href.startsWith("/admin/nodes")) return Number(summary.errors.unhealthy_nodes || 0);
  if (href.startsWith("/admin/users")) return Number(summary.retention.expiring_3d || 0);
  if (href.startsWith("/admin/dashboard")) {
    return (
      Number(summary.tickets.open || 0) +
      Number(summary.errors.unhealthy_nodes || 0) +
      Number(summary.errors.payment_callback_failures_24h || 0) +
      Number(summary.errors.subscription_numeric_fallbacks_24h || 0)
    );
  }
  return 0;
}

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
      <section className="w-full max-w-[760px] rounded-[1.35rem] border border-slate-200/60 bg-white/90 p-8 text-slate-800 shadow-[0_34px_90px_-56px_rgba(15,23,42,0.10)] backdrop-blur-xl">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{eyebrow}</p>
        <h1 className="mt-3 text-[clamp(1.8rem,4vw,2.5rem)] font-semibold leading-tight tracking-[-0.05em] text-slate-900">{title}</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">{description}</p>
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
  const router = useRouter();
  const { error, loading, logoutWebSession, user, webLoginRequired } = usePortalSession();
  const [summary, setSummary] = useState<AdminSummaryPayload | null>(null);
  const [summaryError, setSummaryError] = useState("");

  const activeItem = useMemo(() => findAdminNavItem(pathname), [pathname]);
  const activeCategory = useMemo(() => findAdminNavCategory(pathname), [pathname]);
  const siblingItems = activeCategory.items.filter((item) => item.href !== activeItem.href);
  const operatorName = formatOperatorName(user);
  const unhealthyNodes = summary ? Math.max(0, Number(summary.nodes.total || 0) - Number(summary.nodes.healthy || 0)) : 0;
  const paymentsToCheck = summary ? Number(summary.errors.payment_callback_failures_24h || 0) : 0;
  const openTickets = summary ? Number(summary.tickets.open || 0) : 0;

  useEffect(() => {
    if (!user?.is_admin) {
      setSummary(null);
      return;
    }
    let cancelled = false;
    setSummaryError("");
    adminSummary()
      .then((payload) => {
        if (!cancelled) setSummary(payload);
      })
      .catch((err) => {
        if (!cancelled) setSummaryError(String((err as { message?: string })?.message || err || "Не удалось загрузить сводку."));
      });
    return () => {
      cancelled = true;
    };
  }, [user?.is_admin]);

  useEffect(() => {
    if (!loading && user && !user.is_admin) {
      router.replace("/dashboard/");
    }
  }, [loading, router, user]);

  if (loading) {
    return (
      <main className="grid min-h-[72vh] place-items-center">
        <section className="w-full rounded-[1.35rem] border border-slate-200/60 bg-white/90 p-8 text-slate-800 shadow-[0_34px_90px_-56px_rgba(15,23,42,0.10)] backdrop-blur-xl">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">admin / pokrov</p>
          <h1 className="mt-3 text-[clamp(1.8rem,4vw,2.5rem)] font-semibold tracking-[-0.05em] text-slate-900">Открываем POKROV Admin...</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">Проверяем права доступа, текущую сессию и рабочую область оператора.</p>
          <div className="mt-6 h-2 overflow-hidden rounded-full bg-slate-200">
            <div className="h-full w-1/3 animate-pulse rounded-full bg-emerald-500" />
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
    <main className="min-h-[100dvh] bg-slate-50 px-3 py-3 text-slate-800 sm:px-4">
      <div className="grid min-h-[calc(100dvh-1.5rem)] gap-4 2xl:grid-cols-[264px_minmax(0,1fr)_300px]">
        <aside className={`${adminSidebarClass} p-4 2xl:sticky 2xl:top-3 2xl:self-start`}>
          <div className="flex items-start justify-between gap-3 border-b border-slate-200/60 pb-4">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">admin shell</p>
              <h1 className="mt-2 text-lg font-semibold tracking-[-0.04em] text-slate-900">POKROV Ops</h1>
              <p className="mt-2 text-xs leading-5 text-slate-500">Операторский интерфейс: разделы, очереди, доступ, сеть и рабочие сообщения.</p>
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
                            ? "block rounded-[0.95rem] border border-emerald-300 bg-emerald-50/60 px-3 py-2.5 text-emerald-900 font-semibold"
                            : "block rounded-[0.95rem] border border-transparent bg-transparent px-3 py-2.5 text-slate-600 transition hover:border-slate-200 hover:bg-slate-50/60 hover:text-slate-900"
                        }
                      >
                        <span className="flex items-center justify-between gap-2 text-sm font-semibold">
                          <span>{item.label}</span>
                          {adminAttentionCount(summary, item.href) > 0 ? (
                            <span
                              className={
                                selected
                                  ? "inline-flex min-w-6 justify-center rounded-full bg-emerald-700 px-2 py-0.5 text-[10px] text-white"
                                  : "inline-flex min-w-6 justify-center rounded-full bg-amber-100 px-2 py-0.5 text-[10px] text-amber-800"
                              }
                            >
                              {adminAttentionCount(summary, item.href)}
                            </span>
                          ) : null}
                        </span>
                        <span className={selected ? "mt-1 block text-xs leading-5 text-emerald-700" : "mt-1 block text-xs leading-5 text-slate-500"}>
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
                <h1 className="mt-3 text-[1.55rem] font-semibold tracking-[-0.04em] text-slate-900">{activeItem.label}</h1>
                <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-500">{activeCategory.primaryHint}</p>
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

            <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-slate-200/60 pt-4 text-[11px] font-semibold text-slate-500">
              <AppRouteLink href="/admin/dashboard" className="transition hover:text-emerald-700">
                POKROV Ops
              </AppRouteLink>
              <span>/</span>
              <AppRouteLink href={activeCategory.items[0]?.href || "/admin/dashboard"} className="transition hover:text-emerald-700">
                {activeCategory.label}
              </AppRouteLink>
              <span>/</span>
              <span className="text-slate-900">{activeItem.label}</span>
            </div>
          </header>

          <div className="min-w-0">{children}</div>
        </section>

        <aside className="space-y-4 2xl:sticky 2xl:top-3 2xl:self-start">
          <section className={adminRailCardClass}>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Смена</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-900">{operatorName}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">Рабочий экран: {activeItem.label}. Веб-админка остаётся основным путём, Telegram — запасной канал.</p>
            <div className="mt-3 grid gap-2 text-xs">
              <div className="flex items-center justify-between rounded-[0.85rem] border border-slate-200/70 bg-white/70 px-3 py-2">
                <span className="text-slate-500">Открытые тикеты</span>
                <span className="font-mono font-semibold text-slate-900">{summary ? openTickets : "-"}</span>
              </div>
              <div className="flex items-center justify-between rounded-[0.85rem] border border-slate-200/70 bg-white/70 px-3 py-2">
                <span className="text-slate-500">Ноды с риском</span>
                <span className="font-mono font-semibold text-slate-900">{summary ? unhealthyNodes : "-"}</span>
              </div>
              <div className="flex items-center justify-between rounded-[0.85rem] border border-slate-200/70 bg-white/70 px-3 py-2">
                <span className="text-slate-500">Callback 24 ч</span>
                <span className="font-mono font-semibold text-slate-900">{summary ? paymentsToCheck : "-"}</span>
              </div>
            </div>
            {summaryError ? <p className="mt-3 text-xs leading-5 text-rose-600">{summaryError}</p> : null}
          </section>

          <section className={adminRailCardClass}>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Быстрые переходы</p>
            <div className="mt-3 space-y-2">
              <AppRouteLink href="/admin/dashboard" className="block rounded-[0.95rem] border border-slate-200/60 bg-white/60 px-3 py-2.5 transition hover:border-emerald-300 hover:bg-emerald-50/40">
                <span className="block text-sm font-semibold text-slate-800">Сводка смены</span>
                <span className="mt-1 block text-xs leading-5 text-slate-500">Начать с тревог, очередей и свежести данных.</span>
              </AppRouteLink>
              <AppRouteLink href="/admin/payments?status=manual_review" className="block rounded-[0.95rem] border border-slate-200/60 bg-white/60 px-3 py-2.5 transition hover:border-emerald-300 hover:bg-emerald-50/40">
                <span className="block text-sm font-semibold text-slate-800">Платежи на сверку</span>
                <span className="mt-1 block text-xs leading-5 text-slate-500">Открыть журнал сразу с ручной проверкой.</span>
              </AppRouteLink>
              <AppRouteLink href="/admin/tickets" className="block rounded-[0.95rem] border border-slate-200/60 bg-white/60 px-3 py-2.5 transition hover:border-emerald-300 hover:bg-emerald-50/40">
                <span className="block text-sm font-semibold text-slate-800">Очередь поддержки</span>
                <span className="mt-1 block text-xs leading-5 text-slate-500">Ответы, статусы и шаблоны оператора.</span>
              </AppRouteLink>
              {siblingItems.slice(0, 2).map((item) => (
                <AppRouteLink
                  key={item.href}
                  href={item.href}
                  className="block rounded-[0.95rem] border border-slate-200/60 bg-white/60 px-3 py-2.5 transition hover:border-emerald-300 hover:bg-emerald-50/40"
                >
                  <span className="block text-sm font-semibold text-slate-800">{item.label}</span>
                  <span className="mt-1 block text-xs leading-5 text-slate-500">{item.summary}</span>
                </AppRouteLink>
              ))}
            </div>
          </section>

          <section className={adminRailCardClass}>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Операторский режим</p>
            <div className="mt-3 space-y-2 text-xs leading-5 text-slate-500">
              <p>Сначала смотрите очередь, свежесть данных и тревоги. Потом переходите к точечным действиям.</p>
              <p>Не растаскивайте смену по чатам: рабочая навигация, таблицы и карточки должны жить здесь.</p>
              <p>Telegram оставляйте только как запасной канал, когда нужно быстро закрыть уже разобранный кейс.</p>
            </div>
          </section>
        </aside>
      </div>
    </main>
  );
}
