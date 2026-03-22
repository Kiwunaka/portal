"use client";

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
  { href: "/support", icon: "support_agent", label: "Поддержка", match: (path) => path.startsWith("/support") },
];

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const BOT_BASE_URL = config.botUrl;
const BOT_WEBLOGIN_URL = `${BOT_BASE_URL}${BOT_BASE_URL.includes("?") ? "&" : "?"}start=weblogin`;

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

  if (loading) {
    return (
      <main className="mx-auto grid min-h-[70vh] w-[min(96vw,720px)] place-items-center py-8">
        <section className="glass-card w-full p-7">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">pokrov webapp</p>
          <h1 className="mt-3 font-display text-4xl font-bold">Загружаем данные профиля</h1>
          <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-200/80 dark:bg-slate-800">
            <div className="h-full w-1/3 animate-pulse rounded-full bg-violet-600" />
          </div>
        </section>
      </main>
    );
  }

  if (webLoginRequired) {
    return (
      <main className="mx-auto grid min-h-[70vh] w-[min(96vw,680px)] place-items-center py-8">
        <section className="glass-card w-full p-7">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-violet-600 dark:text-violet-300">[web login]</p>
          <h1 className="mt-2 font-display text-4xl font-bold">Вход через Telegram</h1>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">Подтвердите вход через Telegram, чтобы открыть кабинет POKROV VPN в браузере.</p>
          <div className="mt-5 space-y-3">
            <TelegramLoginWidget />
            {webLoginBusy ? <p className="text-xs text-slate-500">Проверяем аккаунт...</p> : null}
            {webLoginError ? <p className="text-xs text-rose-500">{webLoginError}</p> : null}
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            <AppRouteLink href={BOT_WEBLOGIN_URL} target="_blank" hardNavigate={false} className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]">
              Открыть бота
            </AppRouteLink>
            <button className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]" type="button" onClick={logoutWebSession}>
              Сбросить web-сессию
            </button>
          </div>
        </section>
      </main>
    );
  }

  if (error || !user || !dash) {
    return (
      <main className="mx-auto grid min-h-[70vh] w-[min(96vw,720px)] place-items-center py-8">
        <section className="glass-card w-full p-7">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-rose-500">error</p>
          <h1 className="mt-2 font-display text-4xl font-bold">Ошибка загрузки</h1>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">{error || "Нет данных пользователя"}</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]" type="button" onClick={() => void refresh()}>
              Повторить
            </button>
            <button className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]" type="button" onClick={logoutWebSession}>
              Сбросить web-сессию
            </button>
          </div>
        </section>
      </main>
    );
  }

  return (
    <div className="relative min-h-screen" style={{ minHeight: "var(--tg-viewport-height, 100dvh)" }}>
      <div className="mx-auto flex min-h-screen max-w-[1500px]">
        {!isAdminRoute ? (
          <aside className="hidden w-72 flex-col justify-between px-5 py-7 lg:flex">
          <div>
            <div className="mb-9 flex items-center gap-3 px-3">
              <span className="material-symbols-rounded rounded-xl bg-violet-500/20 p-2 text-2xl text-violet-600 dark:text-violet-300">grid_view</span>
              <div>
                <p className="font-display text-xl font-bold tracking-[0.12em]">POKROV</p>
                <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-slate-500">dashboard</p>
              </div>
            </div>

            <nav className="space-y-1.5">
              {navItems.map((item) => {
                const selected = active === item.href;
                return (
                  <AppRouteLink
                    key={item.href}
                    href={item.href}
                    className={`haptic-tap flex items-center gap-3 rounded-xl px-4 py-3 text-sm transition ${
                      selected ? "glass-card text-violet-700 dark:text-violet-200" : "text-slate-600 hover:bg-white/55 dark:text-slate-300 dark:hover:bg-white/5"
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

          <button
            type="button"
            onClick={logoutWebSession}
            className="haptic-tap flex items-center gap-3 rounded-xl px-4 py-3 text-sm text-slate-500 transition hover:bg-white/50 hover:text-rose-500 dark:text-slate-300 dark:hover:bg-white/5"
          >
            <span className="material-symbols-rounded text-[20px]">logout</span>
            Выйти из web-сессии
          </button>
          </aside>
        ) : null}

        <div
          className={`flex-1 px-3 pt-4 md:px-6 lg:pt-7 ${isAdminRoute ? "pb-6" : "pb-28"}`}
          style={{
            paddingTop: "max(1rem, var(--tg-safe-area-top, 0px))",
            paddingBottom: isAdminRoute ? "calc(1.25rem + var(--tg-safe-area-bottom, 0px))" : "calc(7rem + var(--tg-safe-area-bottom, 0px))",
          }}
        >
          <header className="glass-card mb-5 flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              {!isAdminRoute ? (
                <button
                  type="button"
                  onClick={() => setMobileMenuPath(pathname)}
                  className="haptic-tap rounded-xl bg-white/70 p-2 text-slate-600 lg:hidden dark:bg-white/10 dark:text-slate-300"
                  aria-label="Открыть меню"
                >
                  <span className="material-symbols-rounded">menu</span>
                </button>
              ) : null}
              <p className="font-mono text-[11px] uppercase tracking-[0.15em] text-slate-500 md:text-xs">личный кабинет</p>
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setDark((prev) => !prev)}
                className="haptic-tap rounded-xl bg-white/70 p-2 text-slate-600 transition hover:scale-105 dark:bg-white/10 dark:text-slate-300"
                aria-label="Переключить тему"
              >
                <span suppressHydrationWarning className="material-symbols-rounded">{dark ? "light_mode" : "dark_mode"}</span>
              </button>
              <div className="flex items-center gap-2 rounded-full bg-white/75 px-2 py-1.5 text-sm dark:bg-white/10">
                <span className="grid h-8 w-8 place-items-center rounded-full bg-violet-500 text-white">{String(user.tg_id).slice(-1)}</span>
                <span className="hidden pr-2 text-slate-700 dark:text-slate-100 md:inline">{user.username ? `@${user.username}` : `ID ${user.tg_id}`}</span>
              </div>
            </div>
          </header>

          {children}
        </div>
      </div>

      {!isAdminRoute && inTelegramContext ? (
        <nav className={`tg-bottom-nav glass-card fixed left-1/2 z-40 flex w-[min(96vw,540px)] -translate-x-1/2 justify-between rounded-2xl px-4 py-3 lg:hidden ${mobileMenuOpen ? "pointer-events-none opacity-0" : ""}`}>
        {navItems.map((item) => {
          const selected = active === item.href;
          return (
            <AppRouteLink
              key={item.href}
              href={item.href}
              className={`haptic-tap flex min-w-12 flex-col items-center text-[10px] ${selected ? "text-violet-600 dark:text-violet-300" : "text-slate-500"}`}
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
          className="fixed inset-0 z-50 bg-slate-950/45 p-3 opacity-100 transition-opacity duration-200 lg:hidden"
          onClick={() => setMobileMenuPath(null)}
        >
          <aside
            className="glass-card h-full w-[min(82vw,320px)] p-5 transition-transform duration-200"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mb-6 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-rounded rounded-xl bg-violet-500/20 p-2 text-violet-600 dark:text-violet-300">grid_view</span>
                <div>
                  <p className="font-display text-lg font-bold tracking-[0.12em]">POKROV</p>
                  <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500">menu</p>
                </div>
              </div>
              <button type="button" onClick={() => setMobileMenuPath(null)} className="haptic-tap rounded-lg bg-white/75 p-2 dark:bg-white/10" aria-label="Закрыть меню">
                <span className="material-symbols-rounded">close</span>
              </button>
            </div>

            <nav className="space-y-2">
              {navItems.map((item) => {
                const selected = active === item.href;
                return (
                  <AppRouteLink
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuPath(null)}
                    className={`haptic-tap flex items-center gap-3 rounded-xl px-3 py-3 text-sm ${selected ? "bg-violet-600 text-white" : "bg-white/60 text-slate-700 dark:bg-white/10 dark:text-slate-200"}`}
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
              className="haptic-tap mt-6 flex w-full items-center gap-2 rounded-xl bg-white/60 px-3 py-3 text-sm text-rose-600 dark:bg-white/10 dark:text-rose-300"
            >
              <span className="material-symbols-rounded text-[20px]">logout</span>
              Выйти из web-сессии
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

