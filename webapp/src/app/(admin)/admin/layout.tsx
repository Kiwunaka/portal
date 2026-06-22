"use client";

import AppRouteLink from "@/components/app-route-link";
import type { CSSProperties } from "react";
import {
  AdminBadge,
  adminButtonClass,
  adminRailCardClass,
  adminSidebarClass,
  adminTopbarClass,
} from "@/components/admin/admin-shell";
import { adminSummary, type AdminSummaryPayload } from "@/lib/api";
import { getDesignTokenCssVariables } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { pokrovBranding } from "@/app/branding";
import { ADMIN_NAV_GROUPS, findAdminNavCategory, findAdminNavItem } from "./nav";

const MARKETING_SITE_URL = pokrovBranding.marketingUrl;
const ADMIN_DESIGN_TOKEN_VARS = getDesignTokenCssVariables("admin") as CSSProperties;

const EYEBROW = "text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--atlas-text-muted)]";
const NAV_ACTIVE =
  "block rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-status-success-line)] bg-[color:var(--atlas-status-success-bg)] px-3 py-2.5 font-semibold text-[color:var(--atlas-status-success-text)]";
const NAV_IDLE =
  "block rounded-[var(--pokrov-radius-card)] border border-transparent bg-transparent px-3 py-2.5 text-[color:var(--atlas-text-soft)] transition hover:border-[color:var(--atlas-border)] hover:bg-[color:var(--atlas-canvas-alt)] hover:text-[color:var(--atlas-text)]";
const QUICK_LINK =
  "block rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] px-3 py-2.5 transition hover:border-[color:var(--atlas-status-success-line)] hover:bg-[color:var(--atlas-status-success-bg)]";

function formatOperatorName(user: { display_name?: string | null; username?: string | null; tg_id?: number | null } | null): string {
  if (!user) return "Оператор";
  return user.display_name || (user.username ? `@${user.username}` : user.tg_id ? `ID ${user.tg_id}` : "Оператор");
}

function adminAttentionCount(summary: AdminSummaryPayload | null, href: string): number {
  if (!summary) return 0;
  const errors = (summary.errors ?? {}) as Partial<AdminSummaryPayload["errors"]>;
  const retention = (summary.retention ?? {}) as Partial<AdminSummaryPayload["retention"]>;
  const tickets = (summary.tickets ?? {}) as Partial<AdminSummaryPayload["tickets"]>;
  if (href.startsWith("/admin/tickets")) return Number(tickets.open || 0);
  if (href.startsWith("/admin/payments")) return Number(errors.payment_callback_failures_24h || 0);
  if (href.startsWith("/admin/nodes")) return Number(errors.unhealthy_nodes || 0);
  if (href.startsWith("/admin/users")) return Number(retention.expiring_3d || 0);
  if (href.startsWith("/admin/dashboard")) {
    return (
      Number(tickets.open || 0) +
      Number(errors.unhealthy_nodes || 0) +
      Number(errors.payment_callback_failures_24h || 0) +
      Number(errors.subscription_numeric_fallbacks_24h || 0)
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
    <main className="grid min-h-[72vh] place-items-center px-4" style={ADMIN_DESIGN_TOKEN_VARS}>
      <section className="w-full max-w-[760px] rounded-[var(--pokrov-radius-panel)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-8 text-[color:var(--atlas-text)] shadow-[var(--atlas-shadow-medium)]">
        <p className={EYEBROW}>{eyebrow}</p>
        <h1 className="mt-3 text-[clamp(1.8rem,4vw,2.5rem)] font-semibold leading-tight tracking-[-0.03em] text-[color:var(--atlas-text)]">{title}</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-[color:var(--atlas-text-soft)]">{description}</p>
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
  const summaryErrors = (summary?.errors ?? {}) as Partial<AdminSummaryPayload["errors"]>;
  const summaryNodes = summary?.nodes ?? { healthy: 0, total: 0 };
  const summaryTickets = summary?.tickets ?? { open: 0 };
  const unhealthyNodes = summary ? Math.max(0, Number(summaryNodes.total || 0) - Number(summaryNodes.healthy || 0)) : 0;
  const paymentsToCheck = summary ? Number(summaryErrors.payment_callback_failures_24h || 0) : 0;
  const openTickets = summary ? Number(summaryTickets.open || 0) : 0;

  useEffect(() => {
    let cancelled = false;
    if (!user?.is_admin) {
      queueMicrotask(() => {
        if (!cancelled) setSummary(null);
      });
      return () => {
        cancelled = true;
      };
    }
    queueMicrotask(() => {
      if (!cancelled) setSummaryError("");
    });
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
      <main className="grid min-h-[72vh] place-items-center px-4" style={ADMIN_DESIGN_TOKEN_VARS}>
        <section className="w-full max-w-[760px] rounded-[var(--pokrov-radius-panel)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-8 text-[color:var(--atlas-text)] shadow-[var(--atlas-shadow-medium)]">
          <p className={EYEBROW}>Админка</p>
          <h1 className="mt-3 text-[clamp(1.8rem,4vw,2.5rem)] font-semibold tracking-[-0.03em] text-[color:var(--atlas-text)]">Открываем админку…</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[color:var(--atlas-text-soft)]">Проверяем доступ и загружаем рабочее пространство оператора.</p>
          <div className="mt-6 h-2 overflow-hidden rounded-full bg-[color:var(--atlas-progress-track)]">
            <div className="h-full w-1/3 animate-pulse rounded-full bg-[color:var(--atlas-primary)]" />
          </div>
        </section>
      </main>
    );
  }

  if (webLoginRequired) {
    return (
      <AdminStateCard
        eyebrow="Сессия завершена"
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
        eyebrow="Не удалось проверить доступ"
        title="Не получилось подтвердить права администратора"
        description={error}
      />
    );
  }

  if (!user?.is_admin) {
    return (
      <AdminStateCard
        eyebrow="Доступ ограничен"
        title="Этот раздел открыт только для администраторов"
        description="У текущего аккаунта нет операторских прав. Назначьте роль в системе и повторите вход."
      />
    );
  }

  return (
    <main className="min-h-[100dvh] bg-[color:var(--atlas-canvas)] px-3 py-3 text-[color:var(--atlas-text)] sm:px-4" style={ADMIN_DESIGN_TOKEN_VARS}>
      <div className="grid min-h-[calc(100dvh-1.5rem)] gap-4 xl:grid-cols-[232px_minmax(0,1fr)] 2xl:grid-cols-[232px_minmax(0,1fr)_280px]">
        <aside className={`${adminSidebarClass} p-4 xl:sticky xl:top-3 xl:self-start`}>
          <div className="border-b border-[color:var(--atlas-border)] pb-4">
            <p className={EYEBROW}>Админка</p>
            <h1 className="mt-2 text-lg font-semibold tracking-[-0.02em] text-[color:var(--atlas-text)]">POKROV для оператора</h1>
            <p className="mt-2 text-xs leading-5 text-[color:var(--atlas-text-soft)]">Разделы, очереди обращений, доступ, серверы и сообщения — в одном месте.</p>
          </div>

          <nav aria-label="Admin sections" className="mt-4 space-y-4">
            {ADMIN_NAV_GROUPS.map((group) => (
              <section key={group.id} className="space-y-2">
                <div className="px-1">
                  <p className={EYEBROW}>{group.label}</p>
                </div>
                <div className="space-y-1.5">
                  {group.items.map((item) => {
                    const selected = item.href === activeItem.href;
                    const attention = adminAttentionCount(summary, item.href);
                    return (
                      <AppRouteLink
                        key={item.href}
                        href={item.href}
                        aria-current={selected ? "page" : undefined}
                        className={selected ? NAV_ACTIVE : NAV_IDLE}
                      >
                        <span className="flex items-center justify-between gap-2 text-sm font-semibold">
                          <span>{item.label}</span>
                          {attention > 0 ? (
                            <span
                              className={
                                selected
                                  ? "inline-flex min-w-6 justify-center rounded-full bg-[color:var(--atlas-primary)] px-2 py-0.5 text-[10px] text-[color:var(--atlas-primary-text)]"
                                  : "inline-flex min-w-6 justify-center rounded-full bg-[color:var(--atlas-status-warning-bg)] px-2 py-0.5 text-[10px] text-[color:var(--atlas-status-warning-text)]"
                              }
                            >
                              {attention}
                            </span>
                          ) : null}
                        </span>
                        <span className={selected ? "mt-1 block text-xs leading-5 text-[color:var(--atlas-status-success-text)] opacity-80" : "mt-1 block text-xs leading-5 text-[color:var(--atlas-text-muted)]"}>
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
                  <AdminBadge>Веб-админка — основной путь</AdminBadge>
                </div>
                <h1 className="mt-3 text-[1.5rem] font-semibold tracking-[-0.02em] text-[color:var(--atlas-text)]">{activeItem.label}</h1>
                <p className="mt-2 max-w-4xl text-sm leading-6 text-[color:var(--atlas-text-soft)]">{activeCategory.primaryHint}</p>
              </div>

              <div className="flex flex-wrap gap-2">
                <AppRouteLink href="/dashboard/" className={adminButtonClass("secondary", "sm")}>
                  Вернуться в кабинет
                </AppRouteLink>
                <button type="button" onClick={logoutWebSession} className={adminButtonClass("danger", "sm")}>
                  Сменить аккаунт
                </button>
              </div>
            </div>
          </header>

          <div className="min-w-0">{children}</div>
        </section>

        <aside className="space-y-4 xl:col-start-2 2xl:col-start-auto 2xl:sticky 2xl:top-3 2xl:self-start">
          <section className={adminRailCardClass}>
            <p className={EYEBROW}>Смена оператора</p>
            <h2 className="mt-2 text-lg font-semibold text-[color:var(--atlas-text)]">{operatorName}</h2>
            <p className="mt-2 text-sm leading-6 text-[color:var(--atlas-text-soft)]">Сейчас открыт раздел: {activeItem.label}.</p>
            <div className="mt-3 grid gap-2 text-xs">
              <div className="flex items-center justify-between rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] px-3 py-2">
                <span className="text-[color:var(--atlas-text-soft)]">Открытые обращения</span>
                <span className="font-mono font-semibold text-[color:var(--atlas-text)]">{summary ? openTickets : "—"}</span>
              </div>
              <div className="flex items-center justify-between rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] px-3 py-2">
                <span className="text-[color:var(--atlas-text-soft)]">Серверы с проблемами</span>
                <span className="font-mono font-semibold text-[color:var(--atlas-text)]">{summary ? unhealthyNodes : "—"}</span>
              </div>
              <div className="flex items-center justify-between rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] px-3 py-2">
                <span className="text-[color:var(--atlas-text-soft)]">Сбои оплат за 24 ч</span>
                <span className="font-mono font-semibold text-[color:var(--atlas-text)]">{summary ? paymentsToCheck : "—"}</span>
              </div>
            </div>
            {summaryError ? <p className="mt-3 text-xs leading-5 text-[color:var(--atlas-status-danger-text)]">{summaryError}</p> : null}
          </section>

          <section className={adminRailCardClass}>
            <p className={EYEBROW}>Быстрые переходы</p>
            <div className="mt-3 space-y-2">
              <AppRouteLink href="/admin/dashboard" className={QUICK_LINK}>
                <span className="block text-sm font-semibold text-[color:var(--atlas-text)]">Сводка смены</span>
                <span className="mt-1 block text-xs leading-5 text-[color:var(--atlas-text-soft)]">Начните с главного: проблемы, очереди и свежесть данных.</span>
              </AppRouteLink>
              <AppRouteLink href="/admin/payments?status=manual_review" className={QUICK_LINK}>
                <span className="block text-sm font-semibold text-[color:var(--atlas-text)]">Платежи на проверку</span>
                <span className="mt-1 block text-xs leading-5 text-[color:var(--atlas-text-soft)]">Открыть оплаты, которые нужно проверить вручную.</span>
              </AppRouteLink>
              <AppRouteLink href="/admin/tickets" className={QUICK_LINK}>
                <span className="block text-sm font-semibold text-[color:var(--atlas-text)]">Очередь поддержки</span>
                <span className="mt-1 block text-xs leading-5 text-[color:var(--atlas-text-soft)]">Ответы, статусы и шаблоны для операторов.</span>
              </AppRouteLink>
              {siblingItems.slice(0, 2).map((item) => (
                <AppRouteLink key={item.href} href={item.href} className={QUICK_LINK}>
                  <span className="block text-sm font-semibold text-[color:var(--atlas-text)]">{item.label}</span>
                  <span className="mt-1 block text-xs leading-5 text-[color:var(--atlas-text-soft)]">{item.summary}</span>
                </AppRouteLink>
              ))}
            </div>
          </section>
        </aside>
      </div>
    </main>
  );
}
