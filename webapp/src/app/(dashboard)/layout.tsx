"use client";

import type { DashboardSnapshot } from "@/lib/api";
import AppRouteLink from "@/components/app-route-link";
import TelegramLoginWidget from "@/components/telegram-login-widget";
import { getPortalPublicConfig } from "@/lib/portal";
import { PortalSessionProvider, usePortalSession } from "@/lib/session";
import { getTgUser } from "@/lib/telegram";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

type NavItem = {
  href: string;
  icon: string;
  label: string;
  match: (path: string) => boolean;
};

const BASE_NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", icon: "dashboard", label: "Главная", match: (path) => path === "/dashboard" || path.startsWith("/dashboard/") },
  { href: "/subscription", icon: "account_balance_wallet", label: "Подписка", match: (path) => path.startsWith("/subscription") },
  { href: "/devices", icon: "devices", label: "Устройства", match: (path) => path.startsWith("/devices") },
  { href: "/statistics", icon: "bar_chart", label: "Статистика", match: (path) => path.startsWith("/statistics") },
  { href: "/support", icon: "support_agent", label: "Служба заботы", match: (path) => path.startsWith("/support") },
];

const ACCESS_STATE_LABELS: Record<string, string> = {
  trial_premium: "Тест премиум",
  bonus_premium: "Бонус премиум",
  free_monthly: "Свободный месяц",
  free_soft_mode: "Мягкий лимит",
  paid_unlimited: "Платный доступ",
  expired_or_blocked: "Нужна реактивация",
};

const PLAN_LABELS: Record<string, string> = {
  start_99: "Приветственный план",
  "1_month": "1 месяц",
  "3_months": "3 месяца",
  "6_months": "6 месяцев",
  "9_months": "9 месяцев",
  "12_months": "12 месяцев",
  free_monthly: "Свободный месяц",
  trial: "Тестовый доступ",
};

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const BOT_BASE_URL = config.botUrl;
const BOT_WEBLOGIN_URL = `${BOT_BASE_URL}${BOT_BASE_URL.includes("?") ? "&" : "?"}start=weblogin`;

function formatDateLabel(value?: string | null): string {
  if (!value) return "дата уточняется";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "дата уточняется";

  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
  }).format(parsed);
}

function formatAccessState(dash: DashboardSnapshot): string {
  return ACCESS_STATE_LABELS[dash.access_state || ""] || (dash.is_active ? "Доступ активен" : "Нужна реактивация");
}

function formatPlanLabel(dash: DashboardSnapshot): string {
  const key = String(dash.current_plan_code || dash.sub_type || "").trim();
  return PLAN_LABELS[key] || "Ваш план";
}

function formatTrafficLabel(dash: DashboardSnapshot): string {
  const policy = dash.traffic_policy;
  if (policy?.kind === "unlimited") {
    return "Безлимитный трафик";
  }

  const remaining = policy?.remaining_gb ?? dash.remaining_gb;
  const limit = policy?.limit_gb ?? dash.total_gb;
  const remainingText = `${remaining < 10 ? remaining.toFixed(1) : Math.round(remaining)} GB`;
  const limitText = `${limit < 10 ? limit.toFixed(1) : Math.round(limit)} GB`;

  return `${remainingText} из ${limitText}`;
}

function formatConnectionsLabel(dash: DashboardSnapshot): string {
  const liveConnections = dash.connection_snapshot?.active_connections;
  if (typeof liveConnections === "number" && liveConnections > 0) {
    return `${liveConnections} активн. сейчас`;
  }
  if (dash.active_sessions > 0) {
    return `${dash.active_sessions} активн. сессий`;
  }
  return "Автообновление статуса";
}

function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const {
    loading,
    error,
    webLoginRequired,
    webLoginBusy,
    webLoginError,
    user,
    dash,
    logoutWebSession,
    refresh,
  } = usePortalSession();

  const [dark, setDark] = useState(() => {
    if (typeof window === "undefined") return false;
    const saved = localStorage.getItem("pokrov-theme");
    return saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
  });
  const [inTelegramContext] = useState(() => Boolean(getTgUser()));
  const [mobileMenuPath, setMobileMenuPath] = useState<string | null>(null);
  const isAdminRoute = pathname.startsWith("/admin");
  const mobileMenuOpen = !isAdminRoute && mobileMenuPath === pathname;

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("pokrov-theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    document.body.classList.toggle("modal-open", mobileMenuOpen);
    return () => document.body.classList.remove("modal-open");
  }, [mobileMenuOpen]);

  const navItems = useMemo(() => {
    const list = [...BASE_NAV_ITEMS];
    if (user?.is_admin) {
      list.push({ href: "/admin/dashboard", icon: "admin_panel_settings", label: "Админ", match: (path) => path.startsWith("/admin") });
    }
    return list;
  }, [user?.is_admin]);

  const active = useMemo(
    () => navItems.find((item) => item.match(pathname))?.href || "/dashboard",
    [navItems, pathname],
  );

  const activeItem = useMemo(() => navItems.find((item) => item.href === active), [active, navItems]);

  if (loading) {
    return (
      <main className="mx-auto grid min-h-[72vh] w-[min(96vw,780px)] place-items-center py-8">
        <section className="glass-card w-full overflow-hidden border border-white/70 p-7 dark:border-[#243129]/80 sm:p-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-900/10 bg-emerald-900/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-900/70 dark:border-emerald-100/10 dark:bg-emerald-100/5 dark:text-emerald-100/70">
            personal cabinet
          </div>
          <h1 className="mt-4 font-display text-4xl font-semibold leading-[1.02] text-slate-900 dark:text-slate-50 sm:text-5xl">
            Подтягиваем данные кабинета
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
            Проверяем доступ, трафик и текущее состояние подписки, чтобы кабинет открылся уже с нужным контекстом.
          </p>
          <div className="mt-6 h-2 overflow-hidden rounded-full bg-slate-200/80 dark:bg-slate-800">
            <div className="h-full w-1/3 animate-pulse rounded-full bg-emerald-700 dark:bg-emerald-500" />
          </div>
        </section>
      </main>
    );
  }

  if (webLoginRequired) {
    return (
      <main className="mx-auto grid min-h-[72vh] w-[min(96vw,760px)] place-items-center py-8">
        <section className="glass-card w-full overflow-hidden border border-white/70 p-7 dark:border-[#243129]/80 sm:p-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-900/10 bg-emerald-900/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-900/70 dark:border-emerald-100/10 dark:bg-emerald-100/5 dark:text-emerald-100/70">
            secure login
          </div>
          <h1 className="mt-4 font-display text-4xl font-semibold leading-[1.02] text-slate-900 dark:text-slate-50 sm:text-5xl">
            Подтвердите вход и продолжайте
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
            Кабинет открывается после короткого подтверждения через Telegram. После этого вы сразу вернетесь к своему доступу, подписке и поддержке.
          </p>

          <div className="mt-6 rounded-[28px] border border-emerald-900/8 bg-[#f8f5ef]/88 p-5 dark:border-emerald-200/10 dark:bg-[#0f1714]">
            <TelegramLoginWidget />
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <AppRouteLink href={BOT_WEBLOGIN_URL} target="_blank" hardNavigate={false} className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
              Открыть Telegram
            </AppRouteLink>
            <button className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]" type="button" onClick={logoutWebSession}>
              Сменить аккаунт
            </button>
          </div>

          <div className="mt-5 rounded-[22px] border border-emerald-900/8 bg-emerald-900/[0.03] px-4 py-3 text-sm leading-6 text-slate-600 dark:border-emerald-200/10 dark:bg-emerald-200/[0.04] dark:text-slate-300">
            {webLoginBusy
              ? "Проверяем подтверждение входа."
              : webLoginError || "Если Telegram уже открыт на устройстве, подтверждение обычно занимает один шаг."}
          </div>
        </section>
      </main>
    );
  }

  if (error || !user || !dash) {
    return (
      <main className="mx-auto grid min-h-[72vh] w-[min(96vw,780px)] place-items-center py-8">
        <section className="glass-card w-full overflow-hidden border border-white/70 p-7 dark:border-[#243129]/80 sm:p-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-rose-200/70 bg-rose-50/80 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-rose-700 dark:border-rose-400/20 dark:bg-rose-400/10 dark:text-rose-200">
            cabinet recovery
          </div>
          <h1 className="mt-4 font-display text-4xl font-semibold leading-[1.02] text-slate-900 dark:text-slate-50 sm:text-5xl">
            Кабинет открылся не полностью
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
            {error || "Не удалось получить данные пользователя."}
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]" type="button" onClick={() => void refresh()}>
              Повторить
            </button>
            <button className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]" type="button" onClick={logoutWebSession}>
              Сменить аккаунт
            </button>
          </div>
        </section>
      </main>
    );
  }

  const profileTitle = user.username ? `@${user.username}` : `ID ${user.tg_id}`;
  const profileMark = user.username ? user.username.slice(0, 1).toUpperCase() : String(user.tg_id).slice(-2);
  const statusLabel = formatAccessState(dash);
  const planLabel = formatPlanLabel(dash);
  const trafficLabel = formatTrafficLabel(dash);
  const connectionsLabel = formatConnectionsLabel(dash);
  const expiryLabel = dash.expiry_at ? `до ${formatDateLabel(dash.expiry_at)}` : "срок обновляется";
  const resetLabel = dash.next_reset_at || dash.free_next_reset_at ? `Сброс ${formatDateLabel(dash.next_reset_at || dash.free_next_reset_at)}` : "Маршрут доступа активен";

  return (
    <div className="relative min-h-screen overflow-x-clip" style={{ minHeight: "var(--tg-viewport-height, 100dvh)" }}>
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(11,72,50,0.12),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(197,138,42,0.12),_transparent_34%)]" />

      <div className="mx-auto flex min-h-screen min-w-0 max-w-[1540px] gap-4 px-3 py-4 md:px-4 lg:px-5">
        {!isAdminRoute ? (
          <aside className="hidden w-[312px] shrink-0 lg:block">
            <div className="glass-card sticky top-4 flex min-h-[calc(100vh-2rem)] flex-col justify-between border border-white/70 px-5 py-5 dark:border-[#243129]/80">
              <div>
                <div className="flex items-center gap-3 px-1">
                  <span className="inline-flex h-14 w-14 items-center justify-center rounded-[20px] bg-emerald-900 text-white shadow-[0_20px_40px_-25px_rgba(18,48,36,0.7)] dark:bg-emerald-700">
                    <span className="material-symbols-rounded text-[28px]">shield_lock</span>
                  </span>
                  <div>
                    <p className="font-display text-[1.55rem] font-semibold tracking-[0.12em] text-slate-900 dark:text-slate-50">
                      POKROV
                    </p>
                    <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                      private cabinet
                    </p>
                  </div>
                </div>

                <div className="mt-6 rounded-[28px] border border-emerald-900/8 bg-[#f8f5ef]/88 p-4 dark:border-emerald-200/10 dark:bg-[#0f1714]">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Текущий доступ</p>
                      <h2 className="mt-2 font-display text-[1.9rem] font-semibold leading-[0.96] text-slate-900 dark:text-slate-50">
                        {planLabel}
                      </h2>
                    </div>
                    <span className="rounded-full bg-emerald-900 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-white dark:bg-emerald-700">
                      {statusLabel}
                    </span>
                  </div>

                  <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {profileTitle} · {expiryLabel}
                  </p>

                  <div className="mt-4 grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
                    <div className="rounded-[22px] border border-white/70 bg-white/72 px-4 py-3 dark:border-white/10 dark:bg-white/[0.04]">
                      <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Трафик</p>
                      <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-50">{trafficLabel}</p>
                    </div>
                    <div className="rounded-[22px] border border-white/70 bg-white/72 px-4 py-3 dark:border-white/10 dark:bg-white/[0.04]">
                      <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Устройства</p>
                      <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-50">До {dash.device_limit} устройств</p>
                    </div>
                    <div className="rounded-[22px] border border-white/70 bg-white/72 px-4 py-3 dark:border-white/10 dark:bg-white/[0.04]">
                      <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Сейчас</p>
                      <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-50">{connectionsLabel}</p>
                    </div>
                  </div>

                  <p className="mt-4 text-xs leading-6 text-slate-500 dark:text-slate-400">{resetLabel}</p>
                </div>

                <nav className="mt-6 space-y-2">
                  {navItems.map((item) => {
                    const selected = active === item.href;
                    return (
                      <AppRouteLink
                        key={item.href}
                        href={item.href}
                        className={`haptic-tap flex items-center gap-3 rounded-[22px] px-4 py-3 text-sm transition ${
                          selected
                            ? "bg-emerald-900 text-white shadow-[0_22px_44px_-28px_rgba(18,48,36,0.7)] dark:bg-emerald-700"
                            : "border border-transparent text-slate-600 hover:border-emerald-900/10 hover:bg-white/72 dark:text-slate-300 dark:hover:border-emerald-200/10 dark:hover:bg-white/[0.04]"
                        }`}
                        aria-current={selected ? "page" : undefined}
                      >
                        <span className="material-symbols-rounded text-[20px]">{item.icon}</span>
                        <span className="font-medium">{item.label}</span>
                      </AppRouteLink>
                    );
                  })}
                </nav>
              </div>

              <div className="space-y-3">
                <div className="rounded-[24px] border border-white/70 bg-white/72 px-4 py-4 dark:border-white/10 dark:bg-white/[0.04]">
                  <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Коротко</p>
                  <p className="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">
                    Кабинет хранит ваш доступ, продление и службу заботы в одном спокойном маршруте без лишних витрин.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={logoutWebSession}
                  className="haptic-tap flex w-full items-center gap-3 rounded-[22px] border border-rose-500/15 bg-rose-500/[0.05] px-4 py-3 text-sm font-medium text-rose-700 transition hover:bg-rose-500/[0.08] dark:border-rose-300/15 dark:bg-rose-300/[0.05] dark:text-rose-200"
                >
                  <span className="material-symbols-rounded text-[20px]">logout</span>
                  Сменить аккаунт
                </button>
              </div>
            </div>
          </aside>
        ) : null}

        <div
          className={`min-w-0 flex-1 ${isAdminRoute ? "pb-6" : "pb-28"}`}
          style={{
            paddingTop: "max(1rem, var(--tg-safe-area-top, 0px))",
            paddingBottom: isAdminRoute ? "calc(1.25rem + var(--tg-safe-area-bottom, 0px))" : "calc(7rem + var(--tg-safe-area-bottom, 0px))",
          }}
        >
          <header className="glass-card mb-5 flex flex-wrap items-center justify-between gap-4 border border-white/70 px-4 py-4 dark:border-[#243129]/80 sm:px-5">
            <div className="flex items-center gap-3">
              {!isAdminRoute ? (
                <button
                  type="button"
                  onClick={() => setMobileMenuPath(pathname)}
                  className="haptic-tap inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-white/78 text-slate-700 shadow-sm lg:hidden dark:bg-white/[0.05] dark:text-slate-200"
                  aria-label="Открыть меню"
                >
                  <span className="material-symbols-rounded">menu</span>
                </button>
              ) : null}

              <div>
                <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                  {isAdminRoute ? "operator surface" : "personal cabinet"}
                </p>
                <p className="mt-1 font-display text-[1.65rem] font-semibold leading-none text-slate-900 dark:text-slate-50">
                  {isAdminRoute ? "Админ" : activeItem?.label || "Кабинет"}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-3">
              {!isAdminRoute ? (
                <>
                  <div className="hidden rounded-full border border-white/70 bg-white/72 px-3 py-2 text-sm text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200 md:flex md:items-center md:gap-2">
                    <span className="material-symbols-rounded text-[18px] text-emerald-700 dark:text-emerald-300">verified_user</span>
                    {statusLabel}
                  </div>
                  <div className="hidden rounded-full border border-white/70 bg-white/72 px-3 py-2 text-sm text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200 xl:flex xl:items-center xl:gap-2">
                    <span className="material-symbols-rounded text-[18px] text-emerald-700 dark:text-emerald-300">network_check</span>
                    {trafficLabel}
                  </div>
                </>
              ) : null}

              <button
                type="button"
                onClick={() => setDark((prev) => !prev)}
                className="haptic-tap inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-white/78 text-slate-700 shadow-sm transition hover:scale-[1.02] dark:bg-white/[0.05] dark:text-slate-200"
                aria-label="Переключить тему"
              >
                <span suppressHydrationWarning className="material-symbols-rounded">
                  {dark ? "light_mode" : "dark_mode"}
                </span>
              </button>

              <div className="flex items-center gap-3 rounded-full border border-white/70 bg-white/78 px-2 py-2 shadow-sm dark:border-white/10 dark:bg-white/[0.05]">
                <span className="grid h-10 w-10 place-items-center rounded-full bg-emerald-900 text-sm font-semibold uppercase text-white dark:bg-emerald-700">
                  {profileMark}
                </span>
                <div className="hidden pr-2 md:block">
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-50">{profileTitle}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{planLabel}</p>
                </div>
              </div>
            </div>
          </header>

          {children}
        </div>
      </div>

      {!isAdminRoute && inTelegramContext ? (
        <nav className={`tg-bottom-nav glass-card fixed left-1/2 z-40 flex w-[min(96vw,560px)] -translate-x-1/2 justify-between rounded-[26px] border border-white/70 px-4 py-3 dark:border-[#243129]/80 ${mobileMenuOpen ? "pointer-events-none opacity-0" : ""}`}>
          {navItems.map((item) => {
            const selected = active === item.href;
            return (
              <AppRouteLink
                key={item.href}
                href={item.href}
                className={`haptic-tap flex min-w-12 flex-col items-center gap-1 text-[10px] ${
                  selected ? "text-emerald-800 dark:text-emerald-200" : "text-slate-500 dark:text-slate-400"
                }`}
                aria-current={selected ? "page" : undefined}
              >
                <span className="material-symbols-rounded text-lg">{item.icon}</span>
                {item.label}
              </AppRouteLink>
            );
          })}
        </nav>
      ) : null}

      {!isAdminRoute && mobileMenuOpen ? (
        <div
          className="fixed inset-0 z-50 bg-slate-950/48 p-3 opacity-100 transition-opacity duration-200 lg:hidden"
          onClick={() => setMobileMenuPath(null)}
        >
          <aside
            className="glass-card h-full w-[min(84vw,340px)] border border-white/70 p-5 dark:border-[#243129]/80"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="inline-flex h-12 w-12 items-center justify-center rounded-[18px] bg-emerald-900 text-white dark:bg-emerald-700">
                  <span className="material-symbols-rounded text-[24px]">shield_lock</span>
                </span>
                <div>
                  <p className="font-display text-xl font-semibold tracking-[0.12em] text-slate-900 dark:text-slate-50">POKROV</p>
                  <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">private cabinet</p>
                </div>
              </div>
              <button type="button" onClick={() => setMobileMenuPath(null)} className="haptic-tap inline-flex h-10 w-10 items-center justify-center rounded-xl bg-white/75 dark:bg-white/[0.06]" aria-label="Закрыть меню">
                <span className="material-symbols-rounded">close</span>
              </button>
            </div>

            <div className="mt-5 rounded-[24px] border border-emerald-900/8 bg-[#f8f5ef]/88 p-4 dark:border-emerald-200/10 dark:bg-[#0f1714]">
              <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Ваш доступ</p>
              <p className="mt-2 font-display text-2xl font-semibold leading-none text-slate-900 dark:text-slate-50">{planLabel}</p>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {statusLabel} · {trafficLabel}
              </p>
            </div>

            <nav className="mt-5 space-y-2">
              {navItems.map((item) => {
                const selected = active === item.href;
                return (
                  <AppRouteLink
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuPath(null)}
                    className={`haptic-tap flex items-center gap-3 rounded-[20px] px-4 py-3 text-sm ${
                      selected
                        ? "bg-emerald-900 text-white dark:bg-emerald-700"
                        : "border border-white/70 bg-white/70 text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200"
                    }`}
                    aria-current={selected ? "page" : undefined}
                  >
                    <span className="material-symbols-rounded text-[20px]">{item.icon}</span>
                    {item.label}
                  </AppRouteLink>
                );
              })}
            </nav>

            <button
              type="button"
              onClick={logoutWebSession}
              className="haptic-tap mt-6 flex w-full items-center gap-2 rounded-[20px] border border-rose-500/15 bg-rose-500/[0.05] px-4 py-3 text-sm text-rose-700 dark:border-rose-300/15 dark:bg-rose-300/[0.05] dark:text-rose-200"
            >
              <span className="material-symbols-rounded text-[20px]">logout</span>
              Сменить аккаунт
            </button>
          </aside>
        </div>
      ) : null}
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <PortalSessionProvider>
      <DashboardShell>{children}</DashboardShell>
    </PortalSessionProvider>
  );
}
