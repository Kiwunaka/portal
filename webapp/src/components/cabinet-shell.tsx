"use client";

import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  CircleUserRound,
  CreditCard,
  ExternalLink,
  LifeBuoy,
  LogOut,
  Menu,
  Moon,
  Shield,
  ShieldCheck,
  Sun,
  TriangleAlert,
  Wrench,
  X,
} from "lucide-react";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import AppRouteLink from "@/components/app-route-link";
import CabinetEntryAuth from "@/components/cabinet-entry-auth";
import RouteTransition from "@/components/route-transition";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SkeletonBlock, SkeletonLine, SkeletonRegion } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { ToastProvider } from "@/components/ui/toast";
import { cn, FOCUS_RING } from "@/components/utils";
import { resolvePlanLabel } from "@/lib/access-policy";
import { usePortalSession } from "@/lib/session";

import { POKROV_LEGACY_THEME_STORAGE_KEYS, POKROV_THEME_STORAGE_KEY, pokrovBranding } from "@/app/branding";
import PokrovLogo from "@/app/pokrov-logo";

type NavItem = {
  href: string;
  icon: LucideIcon;
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
    icon: Shield,
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
    icon: CreditCard,
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
    icon: LifeBuoy,
    label: "Помощь",
    description: "Вопросы и диалоги",
    match: (pathname) => pathname.startsWith("/support"),
  },
  {
    href: "/settings",
    icon: CircleUserRound,
    label: "Аккаунт",
    description: "Вход и бонусы",
    match: (pathname) => pathname.startsWith("/settings") || pathname.startsWith("/profile"),
  },
];

const ADMIN_NAV_ITEM: NavItem = {
  href: "/admin/dashboard",
  icon: Wrench,
  label: "Управление",
  description: "Админ-панель оператора",
  match: (pathname) => pathname.startsWith("/admin"),
};

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

type ProfileArgs = {
  username?: string | null;
  displayName?: string | null;
  email?: string | null;
  tgId?: number | null;
};

function profileLabel({ username, displayName, email, tgId }: ProfileArgs): string {
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

function profileMark({ username, displayName, email, tgId }: ProfileArgs): string {
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
    <main className="mx-auto grid min-h-[72vh] w-full max-w-[760px] place-items-center px-4 py-8">
      <section className="w-full rounded-panel border border-line bg-surface p-6 shadow-medium sm:p-8">
        <PokrovLogo
          showWordmark
          className="inline-flex items-center gap-3"
          markClassName="h-12 w-12 rounded-[18px] bg-canvas-alt p-2.5 ring-1 ring-line"
          caption={pokrovBranding.cabinetName}
          label="POKROV cabinet"
        />
        <p className="mt-6 text-xs font-bold tracking-[0.08em] text-ink-muted uppercase">{pokrovBranding.entryEyebrow}</p>
        <h1 className="mt-2 font-display text-[clamp(1.9rem,5vw,2.7rem)] leading-[1.02] font-semibold tracking-[-0.02em] text-ink">
          {title}
        </h1>
        <p className="mt-3 text-sm leading-7 text-ink-soft">{description}</p>
        {children ? <div className="mt-6">{children}</div> : null}
        {actions ? <div className="mt-6 flex flex-wrap gap-3">{actions}</div> : null}
      </section>
    </main>
  );
}

/** Honest cold-start screen: renders only when no usable session state exists. */
function BootstrapScreen() {
  return (
    <main
      className="mx-auto w-full max-w-[1400px] px-3 py-4 sm:px-4 lg:px-5"
      style={{ minHeight: "var(--tg-viewport-height, 100dvh)" }}
    >
      <SkeletonRegion label="Открываем кабинет POKROV">
        <div className="grid min-h-[calc(100dvh-2rem)] gap-4 lg:grid-cols-[252px_1fr]">
          <aside className="hidden rounded-panel border border-line bg-surface p-4 shadow-soft lg:block">
            <SkeletonLine className="h-11 w-36" />
            <div className="mt-5 space-y-2">
              {Array.from({ length: 5 }).map((_, index) => (
                <SkeletonBlock key={index} className="h-[52px]" />
              ))}
            </div>
          </aside>

          <section className="min-w-0 pb-24 lg:pb-8">
            <div className="mx-auto w-full max-w-[760px] space-y-4">
              <p className="text-sm font-semibold text-ink-soft">Открываем кабинет — проверяем сессию и данные доступа.</p>
              <SkeletonBlock className="h-32" />
              <SkeletonBlock className="h-44" />
              <SkeletonBlock className="h-32" />
            </div>
          </section>
        </div>
      </SkeletonRegion>
    </main>
  );
}

const ICON_BUTTON_CLASS = cn(
  "inline-flex h-11 w-11 items-center justify-center rounded-control text-ink-soft transition-colors duration-200 hover:bg-nav-hover hover:text-ink motion-reduce:transition-none",
  FOCUS_RING,
);

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
    return <BootstrapScreen />;
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
  const allNavItems = isAdmin ? [...NAV_ITEMS, ADMIN_NAV_ITEM] : NAV_ITEMS;
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

  const adminTag = (active: boolean) => (
    <span
      className={cn(
        "ml-auto inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-bold tracking-wider uppercase",
        active ? "bg-surface text-ink" : "bg-neutral-bg text-neutral-text",
      )}
    >
      admin
    </span>
  );

  const statusChip = (
    <Badge tone={dash.is_active ? "success" : "warning"}>
      {dash.is_active ? (
        <ShieldCheck size={14} strokeWidth={2} aria-hidden="true" />
      ) : (
        <TriangleAlert size={14} strokeWidth={2} aria-hidden="true" />
      )}
      {statusLabel}
    </Badge>
  );

  const sidebar = (
    <aside className="hidden w-[252px] shrink-0 lg:block xl:w-[280px]">
      <div className="sticky top-4 flex min-h-[calc(100vh-2rem)] flex-col rounded-panel border border-line bg-surface px-3 py-4 shadow-soft">
        <div className="px-2">
          <PokrovLogo
            showWordmark
            className="inline-flex items-center gap-3"
            markClassName="h-11 w-11 rounded-[16px] bg-canvas-alt p-2.5 ring-1 ring-line"
            caption={pokrovBranding.cabinetName}
            label="POKROV cabinet navigation"
          />
        </div>

        <nav className="mt-5 space-y-1">
          {allNavItems.map((item) => {
            const active = item.href === activeNav.href;
            const isAdminItem = item.href.startsWith("/admin");
            const Icon = item.icon;
            return (
              <AppRouteLink
                key={item.href}
                href={item.href}
                className={cn(
                  "group flex items-center gap-3 rounded-control px-2.5 py-2 text-sm font-semibold transition-colors duration-200 motion-reduce:transition-none",
                  active ? "bg-brand text-brand-contrast shadow-soft" : "text-ink-soft hover:bg-nav-hover hover:text-ink",
                )}
                aria-current={active ? "page" : undefined}
              >
                <span
                  className={cn(
                    "grid h-8 w-8 shrink-0 place-items-center rounded-[10px] transition-colors duration-200 motion-reduce:transition-none",
                    active ? "bg-white/20 text-current" : "bg-canvas-alt text-brand group-hover:bg-surface",
                  )}
                >
                  <Icon size={18} strokeWidth={2} aria-hidden="true" />
                </span>
                <span className="min-w-0 truncate">{item.label}</span>
                {isAdminItem ? adminTag(active) : null}
              </AppRouteLink>
            );
          })}
        </nav>

        <div className="mt-auto space-y-3 pt-4">
          <div className="rounded-card border border-line bg-canvas-alt p-3">
            <div className="flex items-center justify-between gap-2">
              {statusChip}
              <span className="text-xs text-ink-muted">{planLabel}</span>
            </div>
            <p className="mt-2 text-xs leading-5 text-ink-muted">{sidebarSummary}</p>
          </div>

          <div className="flex items-center justify-between gap-2 rounded-card border border-line bg-canvas-alt p-3">
            <span className="flex items-center gap-2 text-sm font-semibold text-ink">
              <Moon size={16} strokeWidth={2} aria-hidden="true" className="text-ink-soft" />
              Тёмная тема
            </span>
            <Switch checked={dark} onChange={setDark} aria-label="Переключить тему" />
          </div>

          <div className="flex items-center gap-3 rounded-card border border-line bg-canvas-alt p-3">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-brand text-xs font-semibold text-brand-contrast uppercase">
              {accountMark}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-ink">{accountLabel}</p>
            </div>
            <div className="flex gap-0.5">
              <AppRouteLink href={CABINET_SITE_URL} hardNavigate className={cn(ICON_BUTTON_CLASS, "h-9 w-9")} aria-label="На сайт">
                <ExternalLink size={17} strokeWidth={2} aria-hidden="true" />
              </AppRouteLink>
              <button type="button" onClick={logoutWebSession} className={cn(ICON_BUTTON_CLASS, "h-9 w-9")} aria-label="Выйти">
                <LogOut size={17} strokeWidth={2} aria-hidden="true" />
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
        className="h-full w-[min(86vw,340px)] overflow-y-auto rounded-panel border border-line bg-surface p-4 shadow-medium"
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
            markClassName="h-11 w-11 rounded-[16px] bg-canvas-alt p-2.5 ring-1 ring-line"
            caption={pokrovBranding.cabinetName}
            label="POKROV cabinet mobile menu"
          />
          <button type="button" onClick={() => setDrawerOpen(false)} className={ICON_BUTTON_CLASS} aria-label="Закрыть меню">
            <X size={20} strokeWidth={2} aria-hidden="true" />
          </button>
        </div>

        <div className="mt-5 space-y-1.5">
          {allNavItems.map((item) => {
            const active = item.href === activeNav.href;
            const isAdminItem = item.href.startsWith("/admin");
            const Icon = item.icon;
            return (
              <AppRouteLink
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-start gap-3 rounded-control px-3 py-3 transition-colors motion-reduce:transition-none",
                  active ? "bg-brand text-brand-contrast" : "text-ink-soft hover:bg-nav-hover",
                )}
              >
                <Icon size={20} strokeWidth={2} aria-hidden="true" className="mt-0.5 shrink-0" />
                <span className="min-w-0 flex-1">
                  <span className="flex items-center gap-2">
                    <span className="block text-sm font-semibold">{item.label}</span>
                    {isAdminItem ? adminTag(active) : null}
                  </span>
                  <span className={cn("block text-xs leading-5", active ? "opacity-80" : "text-ink-muted")}>{item.description}</span>
                </span>
              </AppRouteLink>
            );
          })}
        </div>

        <div className="mt-5 rounded-card border border-line bg-canvas-alt p-4">
          <p className="text-sm font-semibold text-ink">{accountLabel}</p>
          <p className="mt-1 text-sm text-ink-soft">{planLabel}</p>
          <div className="mt-3 flex items-center justify-between gap-2">
            <span className="flex items-center gap-2 text-sm font-semibold text-ink">
              <Moon size={16} strokeWidth={2} aria-hidden="true" className="text-ink-soft" />
              Тёмная тема
            </span>
            <Switch checked={dark} onChange={setDark} aria-label="Переключить тему" />
          </div>
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
            <header className="mb-4 flex items-center justify-between gap-3 rounded-panel border border-line bg-surface px-3 py-2 shadow-soft lg:hidden">
              <div className="flex min-w-0 items-center gap-2">
                <button type="button" onClick={() => setDrawerOpen(true)} className={ICON_BUTTON_CLASS} aria-label="Открыть меню">
                  <Menu size={20} strokeWidth={2} aria-hidden="true" />
                </button>
                <h1 className="truncate font-display text-[1.3rem] leading-none font-semibold tracking-[-0.02em] text-ink">
                  {meta.title}
                </h1>
              </div>

              <div className="flex items-center gap-1.5">
                <span className="hidden sm:inline-flex">{statusChip}</span>
                <button type="button" onClick={() => setDark((value) => !value)} className={ICON_BUTTON_CLASS} aria-label="Переключить тему">
                  {dark ? <Sun size={19} strokeWidth={2} aria-hidden="true" /> : <Moon size={19} strokeWidth={2} aria-hidden="true" />}
                </button>
                <AppRouteLink
                  href="/settings/"
                  className={cn(
                    "grid h-10 w-10 place-items-center rounded-full bg-brand text-xs font-semibold text-brand-contrast uppercase",
                    FOCUS_RING,
                  )}
                  aria-label={accountLabel}
                >
                  {accountMark}
                </AppRouteLink>
              </div>
            </header>

            {showActivity ? (
              <div className="mb-4 flex items-center gap-2" role="status">
                <div
                  className="h-0.5 flex-1 overflow-hidden rounded-full bg-progress-track"
                  aria-hidden="true"
                >
                  <div className="h-full w-1/3 rounded-full bg-progress-fill motion-safe:animate-pulse" />
                </div>
                {refreshing ? (
                  <span className="shrink-0 rounded-full bg-canvas-alt px-2.5 py-0.5 text-xs font-semibold text-ink-soft">
                    Обновляем данные
                  </span>
                ) : (
                  <span className="sr-only">Открываем раздел</span>
                )}
              </div>
            ) : null}

            <RouteTransition>{children}</RouteTransition>
          </div>
        </div>

        <AnimatePresence>{drawerOpen ? mobileMenu : null}</AnimatePresence>

        {!drawerOpen ? (
          <nav
            className="mobile-nav-root fixed inset-x-3 bottom-[calc(0.75rem+var(--tg-safe-area-bottom,0px))] z-40 flex items-center justify-between gap-1 overflow-hidden rounded-3xl border border-line bg-surface px-2 pt-2 pb-[calc(0.5rem+var(--tg-safe-area-bottom,0px))] shadow-medium lg:hidden"
            aria-label="Навигация кабинета"
          >
            {NAV_ITEMS.map((item) => {
              const active = item.match(pathname);
              const Icon = item.icon;
              return (
                <AppRouteLink
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex min-h-11 flex-1 flex-col items-center gap-0.5 rounded-2xl px-1 py-1.5 text-[0.625rem] font-semibold transition-colors duration-200 active:scale-95 motion-reduce:transition-none motion-reduce:active:scale-100",
                    active ? "bg-brand text-brand-contrast" : "text-ink-soft",
                  )}
                  aria-current={active ? "page" : undefined}
                >
                  <Icon size={22} strokeWidth={2} aria-hidden="true" />
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
