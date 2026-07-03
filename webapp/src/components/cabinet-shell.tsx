"use client";

import type { ReactNode } from "react";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

import AppRouteLink from "@/components/app-route-link";
import { CabinetIcon } from "@/components/cabinet/icon";
import CabinetEntryAuth from "@/components/cabinet-entry-auth";
import RouteTransition from "@/components/route-transition";
import { ToastProvider } from "@/components/cabinet/toast";
import { Button } from "@/components/cabinet/ui";
import { FOCUS_RING } from "@/components/utils";
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
    icon: "shield",
    label: "Главная",
    description: "Статус и устройство",
    match: (pathname) =>
      pathname === "/dashboard" ||
      pathname.startsWith("/devices") ||
      pathname.startsWith("/statistics") ||
      (pathname.startsWith("/dashboard/") && !pathname.startsWith("/dashboard/downloads")),
  },
  {
    href: "/subscription",
    icon: "payments",
    label: "Доступ",
    description: "Продление и коды",
    match: (pathname) =>
      pathname.startsWith("/subscription") ||
      pathname.startsWith("/redeem") ||
      pathname === "/downloads" ||
      pathname.startsWith("/downloads/") ||
      pathname === "/dashboard/downloads" ||
      pathname.startsWith("/dashboard/downloads/"),
  },
  {
    href: "/support",
    icon: "support_agent",
    label: "Помощь",
    description: "Вопросы и диалоги",
    match: (pathname) => pathname.startsWith("/support"),
  },
  {
    href: "/settings",
    icon: "account_circle",
    label: "Аккаунт",
    description: "Вход и бонусы",
    match: (pathname) => pathname.startsWith("/settings") || pathname.startsWith("/profile"),
  },
];

const MOBILE_NAV_ITEMS: Array<{ href: string; icon: string; label: string; match: (pathname: string) => boolean }> = [
  {
    href: "/dashboard",
    icon: "shield",
    label: "Главная",
    match: (p) => p === "/dashboard" || p.startsWith("/devices") || p.startsWith("/statistics") || (p.startsWith("/dashboard/") && !p.startsWith("/dashboard/downloads")),
  },
  {
    href: "/subscription",
    icon: "payments",
    label: "Доступ",
    match: (p) => p.startsWith("/subscription") || p.startsWith("/redeem") || p.startsWith("/downloads") || p.startsWith("/dashboard/downloads"),
  },
  { href: "/support", icon: "support_agent", label: "Помощь", match: (p) => p.startsWith("/support") },
  { href: "/settings", icon: "account_circle", label: "Аккаунт", match: (p) => p.startsWith("/settings") || p.startsWith("/profile") },
];

const ROUTE_META: Array<{ match: (pathname: string) => boolean; meta: RouteMeta }> = [
  {
    match: (pathname) =>
      pathname === "/downloads" ||
      pathname.startsWith("/downloads/") ||
      pathname === "/dashboard/downloads" ||
      pathname.startsWith("/dashboard/downloads/"),
    meta: { title: "Доступ", subtitle: "Приложение и восстановление." },
  },
  {
    match: (pathname) => pathname === "/dashboard" || (pathname.startsWith("/dashboard/") && !pathname.startsWith("/dashboard/downloads")),
    meta: { title: "Главная", subtitle: "Статус и следующее действие." },
  },
  {
    match: (pathname) => pathname.startsWith("/subscription") || pathname.startsWith("/redeem"),
    meta: { title: "Доступ", subtitle: "Оплата и установка." },
  },
  {
    match: (pathname) => pathname.startsWith("/devices"),
    meta: { title: "Главная", subtitle: "Устройства и подключение." },
  },
  {
    match: (pathname) => pathname.startsWith("/statistics"),
    meta: { title: "Главная", subtitle: "Короткая сводка." },
  },
  {
    match: (pathname) => pathname.startsWith("/support"),
    meta: { title: "Помощь", subtitle: "Обращения и ответы." },
  },
  {
    match: (pathname) => pathname.startsWith("/settings") || pathname.startsWith("/profile"),
    meta: { title: "Аккаунт", subtitle: "Вход, бонусы и настройки." },
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
  if (isSyntheticEmailAccount(tgId)) return "Вход по email";
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
      <section className="w-full rounded-[var(--pokrov-radius-panel)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-6 shadow-[var(--atlas-shadow-medium)] sm:p-8">
        <PokrovLogo
          showWordmark
          className="inline-flex items-center gap-3"
          markClassName="h-12 w-12 rounded-[18px] bg-[color:var(--atlas-canvas-alt)] p-2.5 ring-1 ring-[color:var(--atlas-border)]"
          caption={pokrovBranding.cabinetName}
          label="POKROV cabinet"
        />
        <p className="mt-6 cab-eyebrow">{pokrovBranding.entryEyebrow}</p>
        <h1 className="mt-2 font-display text-[clamp(1.9rem,5vw,2.7rem)] font-semibold leading-[1.02] tracking-[-0.03em] text-[color:var(--atlas-text)]">
          {title}
        </h1>
        <p className="mt-3 text-sm leading-7 text-[color:var(--atlas-text-soft)]">{description}</p>
        {children ? <div className="mt-6">{children}</div> : null}
        {actions ? <div className="mt-6 flex flex-wrap gap-3">{actions}</div> : null}
      </section>
    </main>
  );
}

function SkeletonLine({ className }: { className: string }) {
  return <div className={`motion-safe:animate-pulse rounded-full bg-[color:var(--atlas-skeleton-base)] ${className}`} aria-hidden="true" />;
}

function SkeletonPanel({ className }: { className: string }) {
  return (
    <div
      className={`motion-safe:animate-pulse rounded-[var(--pokrov-radius-panel)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] ${className}`}
      aria-hidden="true"
    />
  );
}

function InitialCabinetSkeleton() {
  return (
    <main
      className="mx-auto w-full max-w-[1400px] px-3 py-4 sm:px-4 lg:px-5"
      style={{ minHeight: "var(--tg-viewport-height, 100dvh)" }}
      aria-busy="true"
      aria-live="polite"
    >
      <div className="grid min-h-[calc(100dvh-2rem)] gap-4 lg:grid-cols-[252px,1fr]">
        <aside className="hidden rounded-[var(--pokrov-radius-panel)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-4 shadow-[var(--atlas-shadow-soft)] lg:block">
          <SkeletonLine className="h-11 w-36" />
          <div className="mt-5 space-y-2">
            {Array.from({ length: 5 }).map((_, index) => (
              <SkeletonPanel key={index} className="h-[52px]" />
            ))}
          </div>
        </aside>

        <section className="min-w-0 pb-24 lg:pb-8" aria-label="Открываем кабинет POKROV">
          <div className="mx-auto w-full max-w-[760px] space-y-4">
            <SkeletonPanel className="h-32" />
            <SkeletonPanel className="h-44" />
            <SkeletonPanel className="h-32" />
          </div>
        </section>
      </div>
    </main>
  );
}

export default function CabinetShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { loading, refreshing, error, webLoginRequired, user, dash, logoutWebSession, refresh } = usePortalSession();
  const reduceMotion = useReducedMotion();
  const [dark, setDark] = useState(() => {
    if (typeof window === "undefined") return false;
    const saved = readStoredThemePreference();
    return saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
  });
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [routeActivity, setRouteActivity] = useState(false);
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
      <ShellState title="Вход в аккаунт" description="Доступ, устройства, оплата и поддержка.">
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
            <Button onClick={() => void refresh()}>Повторить</Button>
            <Button variant="secondary" href="/support/">Поддержка</Button>
            <Button variant="ghost" onClick={logoutWebSession}>Сменить аккаунт</Button>
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

  const navItemClass = (active: boolean) =>
    `group flex items-center gap-3 rounded-[var(--pokrov-radius-control)] px-2.5 py-2 text-sm font-semibold transition-all duration-200 ${
      active
        ? "bg-[color:var(--atlas-primary)] text-[color:var(--atlas-primary-text)] shadow-[var(--atlas-shadow-soft)]"
        : "text-[color:var(--atlas-text-soft)] hover:bg-[color:var(--atlas-nav-hover)] hover:text-[color:var(--atlas-text)] hover:translate-x-0.5"
    }`;

  const navIconClass = (active: boolean) =>
    `grid h-8 w-8 shrink-0 place-items-center rounded-[10px] transition-colors duration-200 ${
      active
        ? "bg-white/20 text-current"
        : "bg-[color:var(--atlas-canvas-alt)] text-[color:var(--atlas-primary)] group-hover:bg-[color:var(--atlas-surface)]"
    }`;

  const adminTag = (active: boolean) => (
    <span
      className={`ml-auto inline-flex items-center rounded-[var(--pokrov-radius-pill)] px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
        active ? "bg-[color:var(--atlas-surface)] text-current" : "bg-[color:var(--atlas-status-neutral-bg)] text-[color:var(--atlas-status-neutral-text)]"
      }`}
    >
      admin
    </span>
  );

  const iconButtonClass = `inline-flex h-9 w-9 items-center justify-center rounded-[var(--pokrov-radius-control)] text-[color:var(--atlas-text-muted)] transition-colors hover:bg-[color:var(--atlas-nav-hover)] hover:text-[color:var(--atlas-text)] ${FOCUS_RING}`;

  const statusChip = (
    <span className="cab-badge" data-tone={dash.is_active ? "success" : "warning"}>
      <CabinetIcon name={dash.is_active ? "shield_check" : "warning"} className="h-3.5 w-3.5" />
      {statusLabel}
    </span>
  );

  const sidebar = (
    <aside className="hidden w-[252px] shrink-0 lg:block xl:w-[280px]">
      <div className="sticky top-4 flex min-h-[calc(100vh-2rem)] flex-col rounded-[var(--pokrov-radius-panel)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] px-3 py-4 shadow-[var(--atlas-shadow-soft)]">
        <div className="px-2">
          <PokrovLogo
            showWordmark
            className="inline-flex items-center gap-3"
            markClassName="h-11 w-11 rounded-[16px] bg-[color:var(--atlas-canvas-alt)] p-2.5 ring-1 ring-[color:var(--atlas-border)]"
            caption={pokrovBranding.cabinetName}
            label="POKROV cabinet navigation"
          />
        </div>

        <nav className="mt-5 space-y-1">
          {allNavItems.map((item) => {
            const active = item.href === activeNav.href;
            const isAdminItem = item.href.startsWith("/admin");
            return (
              <AppRouteLink key={item.href} href={item.href} className={navItemClass(active)} aria-current={active ? "page" : undefined}>
                <span className={navIconClass(active)}>
                  <CabinetIcon name={item.icon} className="h-[18px] w-[18px]" />
                </span>
                <span className="min-w-0 truncate">{item.label}</span>
                {isAdminItem ? adminTag(active) : null}
              </AppRouteLink>
            );
          })}
        </nav>

        <div className="mt-auto space-y-3 pt-4">
          <div className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] p-3">
            <div className="flex items-center justify-between gap-2">
              {statusChip}
              <span className="text-xs text-[color:var(--atlas-text-muted)]">{planLabel}</span>
            </div>
            <p className="mt-2 text-xs leading-5 text-[color:var(--atlas-text-muted)]">{sidebarSummary}</p>
          </div>

          <div className="flex items-center gap-3 rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] p-3">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[color:var(--atlas-primary)] text-xs font-semibold uppercase text-[color:var(--atlas-primary-text)]">
              {accountMark}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-[color:var(--atlas-text)]">{accountLabel}</p>
            </div>
            <div className="flex gap-1">
              <button type="button" onClick={() => setDark((value) => !value)} className={iconButtonClass} aria-label="Переключить тему">
                <CabinetIcon name={dark ? "light_mode" : "dark_mode"} className="h-[18px] w-[18px]" />
              </button>
              <AppRouteLink href={CABINET_SITE_URL} hardNavigate className={iconButtonClass} aria-label="На сайт">
                <CabinetIcon name="open_in_new" className="h-[18px] w-[18px]" />
              </AppRouteLink>
              <button type="button" onClick={logoutWebSession} className={iconButtonClass} aria-label="Выйти">
                <CabinetIcon name="logout" className="h-[18px] w-[18px]" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );

  const mobileMenu = (
    <motion.div
      className="fixed inset-0 z-50 bg-black/45 p-3 backdrop-blur-sm lg:hidden"
      onClick={() => setDrawerOpen(false)}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: reduceMotion ? 0 : 0.22, ease: [0.22, 1, 0.36, 1] }}
    >
      <motion.aside
        className="h-full w-[min(86vw,340px)] rounded-[var(--pokrov-radius-panel)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-4 shadow-[var(--atlas-shadow-medium)]"
        onClick={(event) => event.stopPropagation()}
        initial={reduceMotion ? { opacity: 0 } : { opacity: 0, x: -24 }}
        animate={{ opacity: 1, x: 0 }}
        exit={reduceMotion ? { opacity: 0 } : { opacity: 0, x: -24 }}
        transition={{ duration: reduceMotion ? 0 : 0.22, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="flex items-start justify-between gap-3">
          <PokrovLogo
            showWordmark
            className="inline-flex items-center gap-3"
            markClassName="h-11 w-11 rounded-[16px] bg-[color:var(--atlas-canvas-alt)] p-2.5 ring-1 ring-[color:var(--atlas-border)]"
            caption={pokrovBranding.cabinetName}
            label="POKROV cabinet mobile menu"
          />
          <button type="button" onClick={() => setDrawerOpen(false)} className={iconButtonClass} aria-label="Закрыть меню">
            <CabinetIcon name="close" className="h-5 w-5" />
          </button>
        </div>

        <div className="mt-5 space-y-1.5">
          {allNavItems.map((item) => {
            const active = item.href === activeNav.href;
            const isAdminItem = item.href.startsWith("/admin");
            return (
              <AppRouteLink
                key={item.href}
                href={item.href}
                className={`flex items-start gap-3 rounded-[var(--pokrov-radius-control)] px-3 py-3 transition-colors ${
                  active
                    ? "bg-[color:var(--atlas-primary)] text-[color:var(--atlas-primary-text)]"
                    : "text-[color:var(--atlas-text-soft)] hover:bg-[color:var(--atlas-nav-hover)]"
                }`}
              >
                <CabinetIcon name={item.icon} className="mt-0.5 h-5 w-5 shrink-0" />
                <span className="min-w-0 flex-1">
                  <span className="flex items-center gap-2">
                    <span className="block text-sm font-semibold">{item.label}</span>
                    {isAdminItem ? adminTag(active) : null}
                  </span>
                  <span className={`block text-xs leading-5 ${active ? "opacity-80" : "text-[color:var(--atlas-text-muted)]"}`}>{item.description}</span>
                </span>
              </AppRouteLink>
            );
          })}
        </div>

        <div className="mt-5 rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] p-4">
          <p className="text-sm font-semibold text-[color:var(--atlas-text)]">{accountLabel}</p>
          <p className="mt-1 text-sm text-[color:var(--atlas-text-soft)]">{planLabel}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button variant="secondary" size="sm" href={CABINET_SITE_URL} hardNavigate>На сайт</Button>
            <Button variant="ghost" size="sm" onClick={logoutWebSession}>Выйти</Button>
          </div>
        </div>
      </motion.aside>
    </motion.div>
  );

  return (
    <ToastProvider>
      <div
        data-testid="cabinet-shell"
        className="relative min-h-screen overflow-x-hidden"
        style={{ minHeight: "var(--tg-viewport-height, 100dvh)" }}
      >
        <div className="mx-auto flex min-h-screen max-w-[1400px] gap-4 px-3 py-4 sm:px-4 lg:px-5">
          {sidebar}

          <div className="min-w-0 flex-1 pb-24 lg:pb-8" style={{ paddingTop: "max(0.25rem, var(--tg-safe-area-top, 0px))" }}>
            <header className="mb-4 flex items-center justify-between gap-3 rounded-[var(--pokrov-radius-panel)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] px-3 py-2.5 shadow-[var(--atlas-shadow-soft)] lg:hidden">
              <div className="flex min-w-0 items-center gap-2">
                <button type="button" onClick={() => setDrawerOpen(true)} className={iconButtonClass} aria-label="Открыть меню">
                  <CabinetIcon name="menu" className="h-5 w-5" />
                </button>
                <h1 className="truncate font-display text-[1.3rem] font-semibold leading-none tracking-[-0.02em] text-[color:var(--atlas-text)]">
                  {meta.title}
                </h1>
              </div>

              <div className="flex items-center gap-1.5">
                <span className="cab-badge hidden sm:inline-flex" data-tone={dash.is_active ? "success" : "warning"}>
                  <CabinetIcon name={dash.is_active ? "shield_check" : "warning"} className="h-3.5 w-3.5" />
                  {statusLabel}
                </span>
                <button type="button" onClick={() => setDark((value) => !value)} className={iconButtonClass} aria-label="Переключить тему">
                  <CabinetIcon name={dark ? "light_mode" : "dark_mode"} className="h-5 w-5" />
                </button>
                <AppRouteLink
                  href="/settings/"
                  className={`grid h-9 w-9 place-items-center rounded-full bg-[color:var(--atlas-primary)] text-xs font-semibold uppercase text-[color:var(--atlas-primary-text)] ${FOCUS_RING}`}
                  aria-label={accountLabel}
                >
                  {accountMark}
                </AppRouteLink>
              </div>
            </header>

            {showActivity ? (
              <div
                className="mb-4 h-1 overflow-hidden rounded-full bg-[color:var(--atlas-progress-track)] lg:h-0.5"
                role="status"
                aria-label={refreshing ? "Обновляем данные кабинета" : "Открываем раздел"}
              >
                <div className="h-full w-1/3 rounded-full bg-[color:var(--atlas-primary)] motion-safe:animate-pulse" />
              </div>
            ) : null}

            <RouteTransition>{children}</RouteTransition>
          </div>
        </div>

        <AnimatePresence>{drawerOpen ? mobileMenu : null}</AnimatePresence>

        {!drawerOpen ? (
          <nav className="mobile-nav-root lg:hidden" aria-label="Навигация кабинета">
            {MOBILE_NAV_ITEMS.map((item) => {
              const active = item.match(pathname);
              return (
                <AppRouteLink key={item.href} href={item.href} className={`mobile-nav-item ${active ? "active" : ""}`}>
                  <CabinetIcon name={item.icon} className="h-[22px] w-[22px]" />
                  <span className="truncate">{item.label}</span>
                </AppRouteLink>
              );
            })}
          </nav>
        ) : null}
      </div>
    </ToastProvider>
  );
}
