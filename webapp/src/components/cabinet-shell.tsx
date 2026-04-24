"use client";

import type { ReactNode } from "react";

import AppRouteLink from "@/components/app-route-link";
import CabinetEntryAuth from "@/components/cabinet-entry-auth";
import { CabinetThemeToggle } from "@/components/cabinet/theme-control";
import { resolvePlanLabel, resolveTrafficStatusText } from "@/lib/access-policy";
import { usePortalSession } from "@/lib/session";
import { getTgUser } from "@/lib/telegram";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { pokrovBranding } from "@/app/branding";
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
    description: "Продление, планы и ключи",
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
    href: "/profile",
    icon: "account_circle",
    label: "Аккаунт",
    description: "Вход, тема и связанные каналы",
    match: (pathname) => pathname.startsWith("/profile"),
  },
  {
    href: "/profile/#settings",
    icon: "settings",
    label: "Настройки",
    description: "Тема, вход и безопасные действия",
    match: () => false,
  },
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
    meta: { title: "Тарифы и оплата", subtitle: "Текущий режим, варианты продления и работа с ключом." },
  },
  {
    match: (pathname) => pathname.startsWith("/devices"),
    meta: { title: "Устройства", subtitle: "Что уже связано с аккаунтом и как спокойно перенести доступ." },
  },
  {
    match: (pathname) => pathname.startsWith("/support"),
    meta: { title: "Поддержка", subtitle: "Один разговор на весь кейс, без потери контекста." },
  },
  {
    match: (pathname) => pathname.startsWith("/profile"),
    meta: { title: "Аккаунт", subtitle: "Вход, тема, связанные каналы и безопасные способы вернуться в доступ." },
  },
  {
    match: (pathname) => pathname.startsWith("/settings"),
    meta: { title: "Настройки", subtitle: "Тема, вход и безопасные действия кабинета." },
  },
];

function formatExpiry(value?: string | null): string {
  if (!value) return "срок уточняется";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "срок уточняется";
  return new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long" }).format(parsed);
}

function profileLabel(username?: string | null, tgId?: number | null): string {
  if (username) return `@${username}`;
  if (tgId) return `ID ${tgId}`;
  return "Аккаунт POKROV";
}

function profileMark(username?: string | null, tgId?: number | null): string {
  if (username) return username.slice(0, 1).toUpperCase();
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
          label="Кабинет POKROV"
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

export default function CabinetShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { loading, error, webLoginRequired, user, dash, logoutWebSession, refresh } = usePortalSession();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const inTelegramContext = useMemo(() => Boolean(getTgUser()), []);

  useEffect(() => {
    document.body.classList.toggle("modal-open", drawerOpen);
    return () => document.body.classList.remove("modal-open");
  }, [drawerOpen]);

  useEffect(() => {
    setDrawerOpen(false);
  }, [pathname]);

  if (loading) {
    return (
      <ShellState title="Подтягиваем кабинет" description="Проверяем сессию и собираем ваши данные, чтобы открыть нужный экран без лишних шагов.">
        <div className="h-2 rounded-full bg-slate-200 dark:bg-slate-800">
          <div className="h-full w-1/3 animate-pulse rounded-full bg-emerald-700 dark:bg-emerald-400" />
        </div>
      </ShellState>
    );
  }

  if (webLoginRequired) {
    return (
      <ShellState
        title="Подтвердите вход"
        description="Кабинет продолжает доступ в браузере. Само подключение по-прежнему живет в приложении POKROV."
      >
        <CabinetEntryAuth siteUrl={CABINET_SITE_URL} />
      </ShellState>
    );
  }

  if (error || !user || !dash) {
    return (
      <ShellState
        title="Не получилось открыть кабинет"
        description={error || "Данные аккаунта сейчас не загрузились. Можно повторить попытку или быстро перейти в поддержку."}
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

  const meta = routeMetaFor(pathname);
  const activeNav = NAV_ITEMS.find((item) => item.match(pathname)) || NAV_ITEMS[0];
  const accountLabel = profileLabel(user.username, user.tg_id);
  const planLabel = resolvePlanLabel(dash, user);
  const trafficLabel = resolveTrafficStatusText(dash, user);
  const statusLabel = dash.is_active ? "Доступ активен" : "Нужно продление";
  const sidebarSummary = dash.is_active
    ? `План ${planLabel.toLowerCase()} до ${formatExpiry(dash.expiry_at)}.`
    : "Срок закончился. Продление вернет доступ без нового старта.";

  const sidebar = (
    <aside className="hidden w-[292px] shrink-0 xl:block">
      <div className="sticky top-4 flex min-h-[calc(100vh-2rem)] flex-col rounded-[1.9rem] border border-slate-200/80 bg-[#fbfaf7]/96 px-4 py-4 shadow-[0_28px_70px_-48px_rgba(15,23,42,0.18)] dark:border-white/10 dark:bg-[#101713]/92">
        <div>
          <div className="rounded-[1.5rem] border border-slate-200/80 bg-white/90 p-4 dark:border-white/10 dark:bg-white/[0.04]">
            <PokrovLogo
              showWordmark
              className="inline-flex items-center gap-3"
              markClassName="h-12 w-12 rounded-[18px] bg-white/90 p-2.5 ring-1 ring-emerald-900/10 dark:bg-white/[0.08] dark:ring-white/10"
              caption={pokrovBranding.cabinetName}
              label="Навигация кабинета POKROV"
            />
            <p className="mt-4 text-sm leading-6 text-slate-600 dark:text-slate-300">{pokrovBranding.cabinetTagline}</p>
          </div>

          <nav className="mt-5 space-y-2">
            {NAV_ITEMS.map((item) => {
              const active = item.href === activeNav.href;
              return (
                <AppRouteLink
                  key={item.href}
                  href={item.href}
                  className={`flex items-start gap-3 rounded-[1.2rem] px-3 py-3 transition ${
                    active
                      ? "border border-emerald-200/80 bg-emerald-50 text-emerald-950 dark:border-emerald-400/20 dark:bg-emerald-400/10 dark:text-emerald-100"
                      : "border border-transparent text-slate-600 hover:border-slate-200 hover:bg-white dark:text-slate-300 dark:hover:border-white/10 dark:hover:bg-white/[0.04]"
                  }`}
                  aria-current={active ? "page" : undefined}
                >
                  <span className="material-symbols-rounded pt-0.5 text-[21px]">{item.icon}</span>
                  <span className="min-w-0">
                    <span className="block text-sm font-semibold">{item.label}</span>
                    <span className="block text-xs leading-5 text-slate-500 dark:text-slate-400">{item.description}</span>
                  </span>
                </AppRouteLink>
              );
            })}
          </nav>
        </div>

        <div className="mt-5 space-y-3">
          <div className="rounded-[1.4rem] border border-slate-200/80 bg-white/90 p-4 dark:border-white/10 dark:bg-white/[0.04]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Сейчас</p>
            <p className="mt-2 text-sm font-semibold text-slate-950 dark:text-slate-50">{statusLabel}</p>
            <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{sidebarSummary}</p>
            <dl className="mt-4 space-y-2 text-sm">
              <div className="flex items-start justify-between gap-3">
                <dt className="text-slate-500 dark:text-slate-400">Трафик</dt>
                <dd className="text-right font-medium text-slate-900 dark:text-slate-100">{trafficLabel}</dd>
              </div>
              <div className="flex items-start justify-between gap-3">
                <dt className="text-slate-500 dark:text-slate-400">Устройств</dt>
                <dd className="text-right font-medium text-slate-900 dark:text-slate-100">до {dash.device_limit}</dd>
              </div>
            </dl>
          </div>

          <div className="rounded-[1.4rem] border border-slate-200/80 bg-white/90 p-4 dark:border-white/10 dark:bg-white/[0.04]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Аккаунт</p>
            <div className="mt-3 flex items-center gap-3">
              <span className="grid h-11 w-11 place-items-center rounded-full bg-emerald-900 text-sm font-semibold uppercase text-white dark:bg-emerald-700">
                {profileMark(user.username, user.tg_id)}
              </span>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-slate-950 dark:text-slate-50">{accountLabel}</p>
                <p className="truncate text-xs text-slate-500 dark:text-slate-400">{planLabel}</p>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <CabinetThemeToggle className="rounded-full px-4 py-2 text-xs uppercase tracking-[0.12em]" />
              <AppRouteLink href={CABINET_SITE_URL} hardNavigate className="outline-btn rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em]">
                На сайт
              </AppRouteLink>
              <button type="button" onClick={logoutWebSession} className="outline-btn rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em]">
                Выйти
              </button>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );

  const mobileMenu = (
    <div className="fixed inset-0 z-50 bg-slate-950/42 p-3 xl:hidden" onClick={() => setDrawerOpen(false)}>
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
            label="Мобильное меню кабинета POKROV"
          />
          <button type="button" onClick={() => setDrawerOpen(false)} className="outline-btn rounded-xl p-2" aria-label="Закрыть меню">
            <span className="material-symbols-rounded">close</span>
          </button>
        </div>

        <div className="mt-5 space-y-2">
          {NAV_ITEMS.map((item) => {
            const active = item.href === activeNav.href;
            return (
              <AppRouteLink
                key={item.href}
                href={item.href}
                className={`block rounded-[1.15rem] px-4 py-3 ${
                  active
                    ? "bg-emerald-900 text-white dark:bg-emerald-700"
                    : "border border-slate-200/80 bg-white/90 text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200"
                }`}
              >
                <div className="flex items-start gap-3">
                  <span className="material-symbols-rounded pt-0.5 text-[20px]">{item.icon}</span>
                  <span className="min-w-0">
                    <span className="block text-sm font-semibold">{item.label}</span>
                    <span className={`block text-xs leading-5 ${active ? "text-white/80" : "text-slate-500 dark:text-slate-400"}`}>{item.description}</span>
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
            <CabinetThemeToggle className="rounded-full px-4 py-2 text-xs uppercase tracking-[0.12em]" />
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
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[linear-gradient(180deg,_#f8faf7_0%,_#ffffff_42%,_#eef8f2_100%)] dark:bg-[linear-gradient(180deg,_#0f1714_0%,_#101713_100%)]" />
      <div className="mx-auto flex min-h-screen max-w-[1500px] gap-4 px-3 py-4 sm:px-4 lg:px-5">
        {sidebar}

        <div className="min-w-0 flex-1 pb-24 xl:pb-8" style={{ paddingTop: "max(0.5rem, var(--tg-safe-area-top, 0px))" }}>
          <header className="mb-5 rounded-[1.5rem] border border-slate-200/80 bg-white/90 px-4 py-4 shadow-[0_18px_48px_-36px_rgba(15,23,42,0.18)] dark:border-white/10 dark:bg-[#101713]/88 sm:px-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="flex min-w-0 items-start gap-3">
                <button
                  type="button"
                  onClick={() => setDrawerOpen(true)}
                  className="outline-btn inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl xl:hidden"
                  aria-label="Открыть меню"
                >
                  <span className="material-symbols-rounded">menu</span>
                </button>
                <div className="min-w-0">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">{pokrovBranding.entryEyebrow}</p>
                  <h1 className="mt-1 truncate font-display text-[1.6rem] font-semibold leading-none tracking-[-0.03em] text-slate-950 dark:text-slate-50">
                    {meta.title}
                  </h1>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300">{meta.subtitle}</p>
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-end gap-2">
                <span className={`rounded-full px-3 py-2 text-xs font-semibold uppercase tracking-[0.14em] ${dash.is_active ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-400/10 dark:text-emerald-200" : "bg-amber-50 text-amber-800 dark:bg-amber-400/10 dark:text-amber-200"}`}>
                  {statusLabel}
                </span>
                <CabinetThemeToggle className="min-w-11" />
                <AppRouteLink href="/profile/" className="inline-flex items-center gap-3 rounded-full border border-slate-200/80 bg-white px-2 py-2 text-sm shadow-sm dark:border-white/10 dark:bg-white/[0.04]">
                  <span className="grid h-9 w-9 place-items-center rounded-full bg-emerald-900 text-sm font-semibold uppercase text-white dark:bg-emerald-700">
                    {profileMark(user.username, user.tg_id)}
                  </span>
                  <span className="hidden max-w-[170px] truncate pr-2 font-medium text-slate-900 dark:text-slate-100 sm:block">{accountLabel}</span>
                </AppRouteLink>
              </div>
            </div>
          </header>

          {children}
        </div>
      </div>

      {drawerOpen ? mobileMenu : null}

      {inTelegramContext ? (
        <nav
          className="fixed bottom-[calc(1rem+var(--tg-safe-area-bottom,0px))] left-1/2 z-40 flex w-[min(94vw,620px)] -translate-x-1/2 items-center justify-between gap-2 rounded-[1.6rem] border border-slate-200/80 bg-white/94 px-3 py-2 shadow-[0_26px_60px_-36px_rgba(15,23,42,0.25)] backdrop-blur xl:hidden dark:border-white/10 dark:bg-[#101713]/92"
          aria-label="Навигация кабинета"
        >
          {NAV_ITEMS.map((item) => {
            const active = item.href === activeNav.href;
            return (
              <AppRouteLink
                key={item.href}
                href={item.href}
                className={`flex min-w-0 flex-1 flex-col items-center gap-1 rounded-[1rem] px-2 py-2 text-[10px] font-medium ${
                  active ? "bg-emerald-900 text-white dark:bg-emerald-700" : "text-slate-600 dark:text-slate-300"
                }`}
              >
                <span className="material-symbols-rounded text-[19px]">{item.icon}</span>
                <span className="truncate">{item.label}</span>
              </AppRouteLink>
            );
          })}
        </nav>
      ) : null}
    </div>
  );
}
