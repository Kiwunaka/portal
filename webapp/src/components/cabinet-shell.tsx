"use client";

import type { ReactNode } from "react";

import AppRouteLink from "@/components/app-route-link";
import CabinetEntryAuth from "@/components/cabinet-entry-auth";
import RouteTransition from "@/components/route-transition";
import { resolvePlanLabel } from "@/lib/access-policy";
import { usePortalSession } from "@/lib/session";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { POKROV_LEGACY_THEME_STORAGE_KEYS, POKROV_THEME_STORAGE_KEY, pokrovBranding } from "@/app/branding";
import PokrovLogo from "@/app/pokrov-logo";

type NavItem = {
  href: string;
  icon: string;
  label: string;
  description: string;
  match: (pathname: string) => boolean;
};

type RouteMeta = {
  title: string;
  subtitle: string;
};

const CABINET_SITE_URL = pokrovBranding.marketingUrl;

const NAV_ITEMS: NavItem[] = [
  {
    href: "/dashboard",
    icon: "space_dashboard",
    label: "Главная",
    description: "Статус и следующие шаги",
    match: (pathname) => pathname === "/dashboard" || (pathname.startsWith("/dashboard/") && !pathname.startsWith("/dashboard/downloads")),
  },
  {
    href: "/subscription",
    icon: "payments",
    label: "Тарифы и оплата",
    description: "Продление, планы и коды",
    match: (pathname) => pathname.startsWith("/subscription") || pathname.startsWith("/redeem"),
  },
  {
    href: "/devices",
    icon: "devices",
    label: "Устройства",
    description: "Что уже подключено",
    match: (pathname) => pathname.startsWith("/devices"),
  },
  {
    href: "/statistics",
    icon: "query_stats",
    label: "Статистика",
    description: "Безопасные сводки",
    match: (pathname) => pathname.startsWith("/statistics"),
  },
  {
    href: "/downloads",
    icon: "download",
    label: "Загрузки",
    description: "Приложения и быстрый старт",
    match: (pathname) =>
      pathname === "/downloads" ||
      pathname.startsWith("/downloads/") ||
      pathname === "/dashboard/downloads" ||
      pathname.startsWith("/dashboard/downloads/"),
  },
  {
    href: "/support",
    icon: "support_agent",
    label: "Поддержка",
    description: "Тикеты и живой диалог",
    match: (pathname) => pathname.startsWith("/support"),
  },
  {
    href: "/settings",
    icon: "account_circle",
    label: "Настройки",
    description: "Вход, почта и бонусы",
    match: (pathname) => pathname.startsWith("/settings") || pathname.startsWith("/profile"),
  },
];

const MOBILE_NAV_ITEMS: Array<{ href: string; icon: string; label: string; match: (pathname: string) => boolean }> = [
  { href: "/dashboard", icon: "shield", label: "Главная", match: (p) => p === "/dashboard" || (p.startsWith("/dashboard/") && !p.startsWith("/dashboard/downloads")) },
  { href: "/subscription", icon: "payments", label: "Тариф", match: (p) => p.startsWith("/subscription") || p.startsWith("/redeem") },
  { href: "/devices", icon: "devices", label: "Устройства", match: (p) => p.startsWith("/devices") },
  { href: "/statistics", icon: "query_stats", label: "Статистика", match: (p) => p.startsWith("/statistics") },
  { href: "/support", icon: "support_agent", label: "Поддержка", match: (p) => p.startsWith("/support") },
];

const ROUTE_META: Array<{ match: (pathname: string) => boolean; meta: RouteMeta }> = [
  {
    match: (pathname) =>
      pathname === "/downloads" ||
      pathname.startsWith("/downloads/") ||
      pathname === "/dashboard/downloads" ||
      pathname.startsWith("/dashboard/downloads/"),
    meta: { title: "Загрузки", subtitle: "Прямые ссылки на приложения и короткий путь к установке." },
  },
  {
    match: (pathname) => pathname === "/dashboard" || (pathname.startsWith("/dashboard/") && !pathname.startsWith("/dashboard/downloads")),
    meta: { title: "Главная", subtitle: "Только статус, что требует внимания и что делать дальше." },
  },
  {
    match: (pathname) => pathname.startsWith("/subscription") || pathname.startsWith("/redeem"),
    meta: { title: "Тарифы и оплата", subtitle: "Текущий доступ, варианты продления и код активации." },
  },
  {
    match: (pathname) => pathname.startsWith("/devices"),
    meta: { title: "Устройства", subtitle: "Что уже связано с аккаунтом и как подключить новый экран." },
  },
  {
    match: (pathname) => pathname.startsWith("/statistics"),
    meta: { title: "Статистика", subtitle: "Безопасные сводки без личных ссылок и технических деталей." },
  },
  {
    match: (pathname) => pathname.startsWith("/support"),
    meta: { title: "Поддержка", subtitle: "Один разговор на весь кейс, без потери контекста." },
  },
  {
    match: (pathname) => pathname.startsWith("/settings") || pathname.startsWith("/profile"),
    meta: { title: "Настройки", subtitle: "Способы входа, почта, Telegram и бонусы." },
  },
];

function readStoredThemePreference(): "light" | "dark" | null {
  if (typeof window === "undefined") return null;
  for (const key of [POKROV_THEME_STORAGE_KEY, ...POKROV_LEGACY_THEME_STORAGE_KEYS]) {
    const value = window.localStorage.getItem(key);
    if (value === "light" || value === "dark") {
      if (key !== POKROV_THEME_STORAGE_KEY) {
        window.localStorage.setItem(POKROV_THEME_STORAGE_KEY, value);
      }
      return value;
    }
  }
  return null;
}

function formatExpiry(value?: string | null): string {
  if (!value) return "срок уточняется";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "срок уточняется";
  return new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long" }).format(parsed);
}

const SYNTHETIC_EMAIL_ACCOUNT_MIN = 8_000_000_000_000;
const SYNTHETIC_EMAIL_ACCOUNT_MAX = 9_000_000_000_000;

function isSyntheticEmailAccount(tgId?: number | null): boolean {
  return typeof tgId === "number" && tgId >= SYNTHETIC_EMAIL_ACCOUNT_MIN && tgId < SYNTHETIC_EMAIL_ACCOUNT_MAX;
}

function cleanProfileText(value?: string | null): string {
  return String(value || "").trim();
}

function profileLabel({
  username,
  displayName,
  email,
  tgId,
}: {
  username?: string | null;
  displayName?: string | null;
  email?: string | null;
  tgId?: number | null;
}): string {
  const name = cleanProfileText(displayName);
  if (name) return name;
  const handle = cleanProfileText(username);
  if (handle) return `@${handle}`;
  const mail = cleanProfileText(email);
  if (mail) return mail;
  if (isSyntheticEmailAccount(tgId)) return "Email-аккаунт";
  if (tgId) return `ID ${tgId}`;
  return "Аккаунт POKROV";
}

function profileMark({
  username,
  displayName,
  email,
  tgId,
}: {
  username?: string | null;
  displayName?: string | null;
  email?: string | null;
  tgId?: number | null;
}): string {
  const source = cleanProfileText(displayName) || cleanProfileText(username) || cleanProfileText(email).split("@")[0];
  if (source) return source.slice(0, 1).toUpperCase();
  if (isSyntheticEmailAccount(tgId)) return "PK";
  if (tgId) return String(tgId).slice(-2);
  return "PK";
}

function routeMetaFor(pathname: string): RouteMeta {
  return ROUTE_META.find((item) => item.match(pathname))?.meta || { title: "Кабинет", subtitle: "Продолжение доступа в браузере." };
}

function ShellState({
  title,
  description,
  actions,
  children,
}: {
  title: string;
  description: string;
  actions?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <main className="mx-auto grid min-h-[72vh] w-full max-w-[760px] place-items-center py-8">
      <section className="rounded-[1.8rem] border border-slate-200/80 bg-white/92 p-6 shadow-[0_28px_70px_-48px_rgba(15,23,42,0.22)] dark:border-white/10 dark:bg-[#101713]/90 sm:p-8">
        <PokrovLogo
          showWordmark
          className="inline-flex items-center gap-3"
          markClassName="h-12 w-12 rounded-[18px] bg-white/80 p-2.5 ring-1 ring-emerald-900/10 dark:bg-white/[0.08] dark:ring-white/10"
          caption={pokrovBranding.cabinetName}
          label="POKROV cabinet"
        />
        <p className="mt-6 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">{pokrovBranding.entryEyebrow}</p>
        <h1 className="mt-2 font-display text-[clamp(1.9rem,5vw,2.8rem)] font-semibold leading-[0.98] tracking-[-0.04em] text-slate-950 dark:text-slate-50">
          {title}
        </h1>
        <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">{description}</p>
        {children ? <div className="mt-6">{children}</div> : null}
        {actions ? <div className="mt-6 flex flex-wrap gap-3">{actions}</div> : null}
      </section>
    </main>
  );
}

function SkeletonLine({ className }: { className: string }) {
  return <div className={`motion-safe:animate-pulse rounded-full bg-slate-200/90 dark:bg-white/10 ${className}`} aria-hidden="true" />;
}

function SkeletonPanel({ className }: { className: string }) {
  return (
    <div
      className={`motion-safe:animate-pulse rounded-[1.35rem] border border-slate-200/80 bg-white/70 dark:border-white/10 dark:bg-white/[0.05] ${className}`}
      aria-hidden="true"
    />
  );
}

function InitialCabinetSkeleton() {
  return (
    <main
      className="mx-auto w-full max-w-[1500px] px-3 py-4 sm:px-4 lg:px-5"
      style={{ minHeight: "var(--tg-viewport-height, 100dvh)" }}
      aria-busy="true"
      aria-live="polite"
    >
      <div className="grid min-h-[calc(100dvh-2rem)] gap-4 lg:grid-cols-[260px,1fr] xl:grid-cols-[292px,1fr]">
        <aside className="hidden rounded-[1.9rem] border border-slate-200/80 bg-[#fbfaf7]/96 p-4 shadow-[0_28px_70px_-48px_rgba(15,23,42,0.18)] dark:border-white/10 dark:bg-[#101713]/92 lg:block">
          <div className="rounded-[1.5rem] border border-slate-200/80 bg-white/90 p-4 dark:border-white/10 dark:bg-white/[0.04]">
            <SkeletonLine className="h-11 w-36" />
            <SkeletonLine className="mt-4 h-3 w-full" />
            <SkeletonLine className="mt-2 h-3 w-4/5" />
          </div>
          <div className="mt-5 space-y-2">
            {Array.from({ length: 6 }).map((_, index) => (
              <SkeletonPanel key={index} className="h-[68px]" />
            ))}
          </div>
        </aside>

        <section className="min-w-0 pb-24 lg:pb-8" aria-label="Открываем кабинет POKROV">
          <header className="mb-5 rounded-[1.5rem] border border-slate-200/80 bg-white/90 px-4 py-4 shadow-[0_18px_48px_-36px_rgba(15,23,42,0.18)] dark:border-white/10 dark:bg-[#101713]/88 sm:px-5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">POKROV</p>
            <h1 className="mt-2 font-display text-[1.6rem] font-semibold leading-none tracking-[-0.03em] text-slate-950 dark:text-slate-50">
              Открываем кабинет
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300">
              Готовим оболочку и последние данные аккаунта.
            </p>
          </header>

          <div className="grid gap-4 lg:grid-cols-[1.25fr_0.75fr]">
            <section className="rounded-[1.6rem] border border-slate-200/80 bg-white/90 p-5 shadow-[0_18px_48px_-36px_rgba(15,23,42,0.18)] dark:border-white/10 dark:bg-[#101713]/88">
              <SkeletonLine className="h-3 w-28" />
              <SkeletonLine className="mt-4 h-12 w-3/4 max-w-xl" />
              <SkeletonLine className="mt-4 h-4 w-full max-w-2xl" />
              <SkeletonLine className="mt-2 h-4 w-5/6 max-w-xl" />
              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <SkeletonPanel className="h-28" />
                <SkeletonPanel className="h-28" />
              </div>
            </section>
            <div className="grid gap-4">
              <SkeletonPanel className="h-40" />
              <SkeletonPanel className="h-40" />
            </div>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <SkeletonPanel key={index} className="h-28" />
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

export default function CabinetShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { loading, refreshing, error, webLoginRequired, user, dash, logoutWebSession, refresh } = usePortalSession();
  const [dark, setDark] = useState(() => {
    if (typeof window === "undefined") return false;
    const saved = readStoredThemePreference();
    return saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
  });
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [routeActivity, setRouteActivity] = useState(false);
  const isAdminRoute = pathname.startsWith("/admin");
  const showActivity = refreshing || routeActivity;

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem(POKROV_THEME_STORAGE_KEY, dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    document.body.classList.toggle("modal-open", drawerOpen);
    return () => document.body.classList.remove("modal-open");
  }, [drawerOpen]);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      setDrawerOpen(false);
      setRouteActivity(false);
    });
    return () => window.cancelAnimationFrame(frame);
  }, [pathname]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    let clearTimer: number | undefined;
    const onRouteActivity = () => {
      setRouteActivity(true);
      if (clearTimer) window.clearTimeout(clearTimer);
      clearTimer = window.setTimeout(() => setRouteActivity(false), 3500);
    };
    window.addEventListener("pokrov-route-activity", onRouteActivity as EventListener);
    return () => {
      if (clearTimer) window.clearTimeout(clearTimer);
      window.removeEventListener("pokrov-route-activity", onRouteActivity as EventListener);
    };
  }, []);

  if (loading) {
    return <InitialCabinetSkeleton />;
  }

  if (webLoginRequired) {
    return (
      <ShellState
        title="Вход в аккаунт"
        description="Доступ, устройства, оплата и поддержка."
      >
        <CabinetEntryAuth siteUrl={CABINET_SITE_URL} />
      </ShellState>
    );
  }

  if (error || !user || !dash) {
    return (
      <ShellState
        title="Не получилось открыть кабинет"
        description={error || "Данные профиля сейчас не загрузились. Можно повторить попытку или быстро перейти в поддержку."}
        actions={
          <>
            <button className="btn-primary rounded-full px-5 py-3 text-sm font-semibold" type="button" onClick={() => void refresh()}>
              Повторить
            </button>
            <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
              Поддержка
            </AppRouteLink>
            <button className="outline-btn rounded-full px-5 py-3 text-sm font-semibold" type="button" onClick={logoutWebSession}>
              Сменить аккаунт
            </button>
          </>
        }
      />
    );
  }

  const isAdmin = Boolean(user?.is_admin);
  const adminNavItem: NavItem = {
    href: "/admin/dashboard",
    icon: "admin_panel_settings",
    label: "Управление",
    description: "Админ-панель оператора",
    match: (pathname) => pathname.startsWith("/admin"),
  };
  const allNavItems = isAdmin ? [...NAV_ITEMS, adminNavItem] : NAV_ITEMS;
  const meta = routeMetaFor(pathname);
  const activeNav = allNavItems.find((item) => item.match(pathname)) || allNavItems[0];
  const linkedEmail = user.email || user.linked_identities?.email?.email || null;
  const profileArgs = {
    username: user.username,
    displayName: user.display_name,
    email: linkedEmail,
    tgId: user.tg_id,
  };
  const accountLabel = profileLabel(profileArgs);
  const accountMark = profileMark(profileArgs);
  const planLabel = resolvePlanLabel(dash, user);
  const statusLabel = dash.is_active ? "Доступ активен" : "Нужно продление";
  const sidebarSummary = dash.is_active
    ? `План ${planLabel.toLowerCase()} до ${formatExpiry(dash.expiry_at)}.`
    : "Срок закончился. Продление вернет доступ в том же аккаунте.";

  const sidebar = (
    <aside className="hidden w-[260px] shrink-0 lg:block xl:w-[292px]">
      <div className="sticky top-4 flex min-h-[calc(100vh-2rem)] flex-col rounded-[1.9rem] border border-slate-200/80 bg-[#fbfaf7]/96 px-4 py-4 shadow-[0_28px_70px_-48px_rgba(15,23,42,0.18)] dark:border-white/10 dark:bg-[#101713]/92">
        <div>
          <div className="rounded-[1.5rem] border border-slate-200/80 bg-white/90 p-4 dark:border-white/10 dark:bg-white/[0.04]">
            <PokrovLogo
              showWordmark
              className="inline-flex items-center gap-3"
              markClassName="h-12 w-12 rounded-[18px] bg-white/90 p-2.5 ring-1 ring-emerald-900/10 dark:bg-white/[0.08] dark:ring-white/10"
              caption={pokrovBranding.cabinetName}
              label="POKROV cabinet navigation"
            />
            <p className="mt-4 text-sm leading-6 text-slate-600 dark:text-slate-300">{pokrovBranding.cabinetTagline}</p>
          </div>

          <nav className="mt-4 space-y-1">
            {allNavItems.map((item) => {
              const active = item.href === activeNav.href;
              const isAdminItem = item.href.startsWith("/admin");
              return (
                <AppRouteLink
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 rounded-[1rem] px-3 py-2.5 text-sm font-semibold transition ${
                    active
                      ? isAdminItem
                        ? "bg-slate-800 text-white dark:bg-slate-700"
                        : "bg-emerald-800 text-white dark:bg-emerald-700"
                      : isAdminItem
                        ? "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/[0.04]"
                        : "text-slate-600 hover:bg-white dark:text-slate-300 dark:hover:bg-white/[0.04]"
                  }`}
                  aria-current={active ? "page" : undefined}
                >
                  <span className="material-symbols-rounded text-[20px]">{item.icon}</span>
                  <span className="min-w-0">{item.label}</span>
                  {isAdminItem ? (
                    <span className="ml-auto inline-flex items-center rounded-full bg-slate-200 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-700 dark:bg-slate-700 dark:text-slate-300">
                      admin
                    </span>
                  ) : null}
                </AppRouteLink>
              );
            })}
          </nav>
        </div>

        <div className="mt-auto space-y-3">
          <div className="rounded-[1.25rem] border border-slate-200/80 bg-white/90 p-3 dark:border-white/10 dark:bg-white/[0.04]">
            <div className="flex items-center justify-between gap-2">
              <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${dash.is_active ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-400/10 dark:text-emerald-200" : "bg-amber-50 text-amber-800 dark:bg-amber-400/10 dark:text-amber-200"}`}>
                <span className="material-symbols-rounded text-[14px]">{dash.is_active ? "shield" : "warning"}</span>
                {statusLabel}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">{planLabel}</span>
            </div>
            <p className="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">{sidebarSummary}</p>
          </div>

          <div className="flex items-center gap-3 rounded-[1.25rem] border border-slate-200/80 bg-white/90 p-3 dark:border-white/10 dark:bg-white/[0.04]">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-emerald-900 text-xs font-semibold uppercase text-white dark:bg-emerald-700">
              {accountMark}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-slate-950 dark:text-slate-50">{accountLabel}</p>
            </div>
            <div className="flex gap-1">
              <AppRouteLink href={CABINET_SITE_URL} hardNavigate className="inline-flex h-8 w-8 items-center justify-center rounded-full text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/[0.04]" aria-label="На сайт">
                <span className="material-symbols-rounded text-[18px]">open_in_new</span>
              </AppRouteLink>
              <button type="button" onClick={logoutWebSession} className="inline-flex h-8 w-8 items-center justify-center rounded-full text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/[0.04]" aria-label="Выйти">
                <span className="material-symbols-rounded text-[18px]">logout</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );

  const mobileMenu = (
    <div className="fixed inset-0 z-50 bg-slate-950/42 p-3 lg:hidden" onClick={() => setDrawerOpen(false)}>
      <aside
        className="h-full w-[min(86vw,340px)] rounded-[1.8rem] border border-slate-200/80 bg-[#fbfaf7]/98 p-4 shadow-[0_32px_80px_-48px_rgba(15,23,42,0.4)] dark:border-white/10 dark:bg-[#101713]/98"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <PokrovLogo
            showWordmark
            className="inline-flex items-center gap-3"
            markClassName="h-11 w-11 rounded-[16px] bg-white/90 p-2.5 ring-1 ring-emerald-900/10 dark:bg-white/[0.08] dark:ring-white/10"
            caption={pokrovBranding.cabinetName}
            label="POKROV cabinet mobile menu"
          />
          <button type="button" onClick={() => setDrawerOpen(false)} className="outline-btn rounded-xl p-2" aria-label="Закрыть меню">
            <span className="material-symbols-rounded">close</span>
          </button>
        </div>

        <div className="mt-5 space-y-2">
          {allNavItems.map((item) => {
            const active = item.href === activeNav.href;
            const isAdminItem = item.href.startsWith("/admin");
            return (
              <AppRouteLink
                key={item.href}
                href={item.href}
                className={`block rounded-[1.15rem] px-4 py-3 ${
                  active
                    ? isAdminItem
                      ? "bg-slate-800 text-white dark:bg-slate-700"
                      : "bg-emerald-900 text-white dark:bg-emerald-700"
                    : isAdminItem
                      ? "border border-slate-200/80 bg-slate-50/80 text-slate-800 dark:border-white/10 dark:bg-slate-800/40 dark:text-slate-200"
                      : "border border-slate-200/80 bg-white/90 text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200"
                }`}
              >
                <div className="flex items-start gap-3">
                  <span className="material-symbols-rounded pt-0.5 text-[20px]">{item.icon}</span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center gap-2">
                      <span className="block text-sm font-semibold">{item.label}</span>
                      {isAdminItem ? (
                        <span className="inline-flex items-center rounded bg-slate-200 px-1 py-0.5 text-[10px] font-bold uppercase text-slate-600 dark:bg-slate-600 dark:text-slate-300">
                          admin
                        </span>
                      ) : null}
                    </span>
                    <span className={`block text-xs leading-5 ${active ? "text-white/80" : isAdminItem ? "text-slate-500 dark:text-slate-400" : "text-slate-500 dark:text-slate-400"}`}>{item.description}</span>
                  </span>
                </div>
              </AppRouteLink>
            );
          })}
        </div>

        <div className="mt-5 rounded-[1.3rem] border border-slate-200/80 bg-white/90 p-4 dark:border-white/10 dark:bg-white/[0.04]">
          <p className="text-sm font-semibold text-slate-950 dark:text-slate-50">{accountLabel}</p>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{planLabel}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <AppRouteLink href={CABINET_SITE_URL} hardNavigate className="outline-btn rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em]">
              На сайт
            </AppRouteLink>
            <button type="button" onClick={logoutWebSession} className="outline-btn rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em]">
              Выйти
            </button>
          </div>
        </div>
      </aside>
    </div>
  );

  return (
    <div className="relative min-h-screen overflow-x-hidden" style={{ minHeight: "var(--tg-viewport-height, 100dvh)" }}>
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(11,72,50,0.06),_transparent_30%),radial-gradient(circle_at_bottom_right,_rgba(197,138,42,0.06),_transparent_28%)]" />
      <div className="mx-auto flex min-h-screen max-w-[1500px] gap-4 px-3 py-4 sm:px-4 lg:px-5">
        {sidebar}

        <div className="min-w-0 flex-1 pb-24 lg:pb-8" style={{ paddingTop: "max(0.5rem, var(--tg-safe-area-top, 0px))" }}>
          <header className="mb-4 rounded-[1.25rem] border border-slate-200/80 bg-white/90 px-4 py-3 shadow-[0_12px_36px_-24px_rgba(15,23,42,0.15)] dark:border-white/10 dark:bg-[#101713]/88 sm:px-5">
            <div className="flex items-center justify-between gap-3">
              <div className="flex min-w-0 items-center gap-3">
                <button
                  type="button"
                  onClick={() => setDrawerOpen(true)}
                  className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-slate-600 hover:bg-slate-100 lg:hidden dark:text-slate-300 dark:hover:bg-white/[0.04]"
                  aria-label="Открыть меню"
                >
                  <span className="material-symbols-rounded">menu</span>
                </button>
                <h1 className="truncate font-display text-[1.4rem] font-semibold leading-none tracking-[-0.02em] text-slate-950 dark:text-slate-50">
                  {meta.title}
                </h1>
              </div>

              <div className="flex items-center gap-2">
                <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1.5 text-xs font-semibold ${dash.is_active ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-400/10 dark:text-emerald-200" : "bg-amber-50 text-amber-800 dark:bg-amber-400/10 dark:text-amber-200"}`}>
                  <span className="material-symbols-rounded text-[14px]">{dash.is_active ? "shield" : "warning"}</span>
                  <span className="hidden sm:inline">{statusLabel}</span>
                </span>
                <button type="button" onClick={() => setDark((value) => !value)} className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-white/[0.04]" aria-label="Переключить тему">
                  <span className="material-symbols-rounded">{dark ? "light_mode" : "dark_mode"}</span>
                </button>
                <AppRouteLink href="/settings/" className="inline-flex items-center gap-2 rounded-full border border-slate-200/80 bg-white px-1.5 py-1 text-sm shadow-sm dark:border-white/10 dark:bg-white/[0.04]">
                  <span className="grid h-8 w-8 place-items-center rounded-full bg-emerald-900 text-xs font-semibold uppercase text-white dark:bg-emerald-700">
                    {accountMark}
                  </span>
                  <span className="hidden max-w-[140px] truncate pr-1.5 font-medium text-slate-900 dark:text-slate-100 sm:block">{accountLabel}</span>
                </AppRouteLink>
              </div>
            </div>
            {showActivity ? (
              <div className="mt-4 h-1 overflow-hidden rounded-full bg-slate-200/70 dark:bg-white/10" role="status" aria-label={refreshing ? "Обновляем данные кабинета" : "Открываем раздел"}>
                <div className="h-full w-1/3 rounded-full bg-emerald-700 motion-safe:animate-pulse dark:bg-emerald-300" />
              </div>
            ) : null}
          </header>

          <RouteTransition>{children}</RouteTransition>
        </div>
      </div>

      {drawerOpen ? mobileMenu : null}

      {!isAdminRoute && !drawerOpen ? (
        <nav
          className="mobile-nav-root lg:hidden"
          aria-label="Навигация кабинета"
        >
          {MOBILE_NAV_ITEMS.map((item) => {
            const active = item.match(pathname);
            return (
              <AppRouteLink
                key={item.href}
                href={item.href}
                className={`mobile-nav-item ${active ? "active" : ""}`}
              >
                <span className="material-symbols-rounded text-[22px]">{item.icon}</span>
                <span className="truncate">{item.label}</span>
              </AppRouteLink>
            );
          })}
        </nav>
      ) : null}
    </div>
  );
}
