"use client";

import AppRouteLink from "@/components/app-route-link";
import {
  AdminBadge,
  adminButtonClass,
  adminFieldClass,
  adminRailCardClass,
  adminSidebarClass,
  adminShellFrameClass,
  adminTopbarClass,
} from "@/components/admin/admin-shell";
import { hasWebSessionToken, resolveApiUrl, setWebSessionToken } from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";

import { pokrovBranding } from "../../branding";
import { ADMIN_NAV_GROUPS, findAdminNavCategory, findAdminNavItem } from "./nav";

const MARKETING_SITE_URL = pokrovBranding.marketingUrl;

function isLocalDevHost(): boolean {
  if (typeof window === "undefined") return false;
  return isLoopbackHost(window.location.hostname);
}

function isLoopbackHost(hostname: string): boolean {
  return ["localhost", "127.0.0.1", "::1", "[::1]"].includes(String(hostname || "").toLowerCase());
}

function resolvedDevLoginTarget(): { apiBase: string; apiLoopback: boolean; url: string } {
  const url = resolveApiUrl("/api/auth/dev/web-login");
  try {
    const parsed = new URL(url);
    return {
      apiBase: parsed.origin,
      apiLoopback: isLoopbackHost(parsed.hostname),
      url,
    };
  } catch {
    return { apiBase: url || "unknown", apiLoopback: false, url };
  }
}

function LocalDevAdminLogin() {
  const [status, setStatus] = useState({
    uiLoopback: false,
    apiLoopback: false,
    apiBase: "",
    url: "",
  });
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const target = resolvedDevLoginTarget();
    setStatus({
      uiLoopback: isLocalDevHost(),
      apiLoopback: target.apiLoopback,
      apiBase: target.apiBase,
      url: target.url,
    });
  }, []);

  const available = status.uiLoopback && status.apiLoopback;

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!available) return;
    setBusy(true);
    setError("");
    try {
      const response = await fetch(status.url || resolveApiUrl("/api/auth/dev/web-login"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      const payload = (await response.json().catch(() => ({}))) as { token?: string; detail?: string; message?: string };
      if (!response.ok || !payload.token) {
        throw new Error(payload.detail || payload.message || "Локальный вход сейчас не настроен.");
      }
      setWebSessionToken(payload.token);
      window.location.replace("/admin/dashboard/");
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось открыть локальный вход."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="mt-6 rounded-[0.9rem] border border-[#b8ded1] bg-[#f8fffc] p-4">
      <p className="text-sm font-semibold text-slate-950">Локальный вход для разработки</p>
      <p className="mt-1 text-xs leading-5 text-slate-600">
        Работает только на этом компьютере и только если сервер разрешил локальный вход.
      </p>
      <p className="mt-2 break-all text-xs leading-5 text-slate-600">Сервер: {status.apiBase || "проверяем..."}</p>
      <p className={available ? "mt-2 text-xs leading-5 text-emerald-700" : "mt-2 text-xs leading-5 text-amber-700"}>
        {available
          ? "Локальный вход доступен для этого предпросмотра."
          : "Локальный вход появится только рядом с локальным сервером."}
      </p>
      {available ? (
        <div className="mt-3 grid gap-2 sm:grid-cols-[minmax(0,1fr)_auto]">
          <input
            aria-label="Локальный пароль"
            className={adminFieldClass}
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Введите локальный пароль"
          />
          <button type="submit" className={`${adminButtonClass("primary", "sm")} whitespace-nowrap`} disabled={busy || !password.trim()}>
            {busy ? "Проверяем..." : "Войти в админку"}
          </button>
        </div>
      ) : null}
      {error ? <p className="mt-2 text-xs leading-5 text-rose-700">{error}</p> : null}
    </form>
  );
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
      <section className="w-full max-w-[760px] rounded-[1.15rem] border border-[#b8ded1] bg-[#ffffff] p-7 text-slate-900 shadow-[0_34px_90px_-56px_rgba(10,92,67,0.34)]">
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">{eyebrow}</p>
        <h1 className="mt-3 text-[clamp(1.7rem,4vw,2.35rem)] font-semibold leading-tight text-slate-950">{title}</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">{description}</p>
        <LocalDevAdminLogin />
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
  const [hasBrowserSession, setHasBrowserSession] = useState(() => hasWebSessionToken());

  const activeItem = useMemo(() => findAdminNavItem(pathname), [pathname]);
  const activeCategory = useMemo(() => findAdminNavCategory(pathname), [pathname]);
  const siblingItems = activeCategory.items.filter((item) => item.href !== activeItem.href);

  useEffect(() => {
    setHasBrowserSession(hasWebSessionToken());
  }, [loading, user, webLoginRequired]);

  if (loading) {
    return (
      <main className="grid min-h-[72vh] place-items-center">
        <section className="w-full rounded-[1.15rem] border border-[#b8ded1] bg-[#ffffff] p-7 text-slate-900 shadow-[0_34px_90px_-56px_rgba(10,92,67,0.34)]">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">admin / pokrov</p>
          <h1 className="mt-3 text-[clamp(1.7rem,4vw,2.35rem)] font-semibold text-slate-950">Открываем POKROV Admin...</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">Проверяем web-сессию, роль администратора и рабочее место оператора.</p>
          <div className="mt-6 h-2 overflow-hidden rounded-full bg-[#f8fffc]">
            <div className="h-full w-1/3 animate-pulse rounded-full bg-emerald-100" />
          </div>
        </section>
      </main>
    );
  }

  if (webLoginRequired || !hasBrowserSession) {
    return (
      <AdminStateCard
        eyebrow="нужна сессия"
        title="Войдите снова, чтобы открыть админку"
        description="Сессия браузера истекла. Откройте вход в кабинет или используйте локальный вход, если он включен на этом компьютере."
        primaryHref="/"
        primaryLabel="Открыть вход"
      />
    );
  }

  if (error && !user) {
    return (
      <AdminStateCard
        eyebrow="access check failed"
        title="Не удалось проверить роль администратора"
        description={error}
      />
    );
  }

  if (!user?.is_admin) {
    return (
      <AdminStateCard
        eyebrow="restricted"
        title="Эта консоль только для администраторов"
        description="У текущей учетной записи нет операторской роли. Назначьте роль в контрольной системе и войдите снова."
      />
    );
  }

  return (
    <div className={adminShellFrameClass}>
      <div className="grid gap-4 p-3 lg:p-4 xl:grid-cols-[248px_minmax(0,1fr)_288px]">
        <aside className={`${adminSidebarClass} p-3 xl:sticky xl:top-4 xl:self-start`}>
          <div className="border-b border-[#b8ded1] pb-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-700">рабочая панель</p>
                <h1 className="mt-2 text-lg font-semibold text-slate-50">POKROV Ops</h1>
              </div>
              <AdminBadge tone="accent">Админ</AdminBadge>
            </div>
            <p className="mt-3 text-xs leading-5 text-slate-400">
              Плотная рабочая консоль: пользователи, доступ, оплата, сообщения, диагностика и сеть в одном месте.
            </p>
          </div>

          <nav aria-label="Admin sections" className="mt-4 space-y-4">
            {ADMIN_NAV_GROUPS.map((group) => (
              <section key={group.id} className="space-y-2">
                <div className="px-1">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-700">{group.label}</p>
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
                            ? "block rounded-[0.85rem] border border-[#2f8f70] bg-[#dff3eb] px-3 py-2.5 text-slate-50"
                            : "block rounded-[0.85rem] border border-transparent bg-transparent px-3 py-2.5 text-slate-300 transition hover:border-[#99cdbb] hover:bg-[#f8fffc] hover:text-slate-100"
                        }
                      >
                        <span className="block text-sm font-semibold">{item.label}</span>
                        <span className={selected ? "mt-1 block text-xs leading-5 text-slate-300" : "mt-1 block text-xs leading-5 text-slate-500"}>
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
                  <AdminBadge tone="success">основная админка</AdminBadge>
                </div>
                <h1 className="mt-3 text-[1.45rem] font-semibold text-slate-50">Админка POKROV</h1>
                <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">
                  Веб-админка — основной операторский интерфейс. Telegram держим как резервный ручной канал.
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

            <div className="mt-4 flex flex-wrap gap-2 border-t border-[#b8ded1] pt-4">
              {ADMIN_NAV_GROUPS.map((group) => {
                const selected = group.id === activeCategory.id;
                return (
                  <AppRouteLink
                    key={group.id}
                    href={group.items[0]?.href || "/admin/dashboard"}
                    aria-label={`Open ${group.label}`}
                    className={
                      selected
                        ? "inline-flex min-h-8 items-center rounded-full border border-[#2f8f70] bg-[#dff3eb] px-3 text-[11px] font-semibold text-emerald-100"
                        : "inline-flex min-h-8 items-center rounded-full border border-[#c6e6db] bg-[#f8fffc] px-3 text-[11px] font-semibold text-slate-400 transition hover:border-[#2f8f70] hover:text-slate-200"
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

        <aside className="space-y-4 xl:sticky xl:top-4 xl:self-start">
          <section className={adminRailCardClass}>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-700">текущий контекст</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-50">{activeItem.label}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">{activeItem.summary}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <AdminBadge tone="accent">{activeCategory.label}</AdminBadge>
              <AdminBadge>{activeCategory.primaryHint}</AdminBadge>
            </div>
          </section>

          <section className={adminRailCardClass}>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-700">соседние разделы</p>
            <div className="mt-3 space-y-2">
              {siblingItems.length ? (
                siblingItems.map((item) => (
                  <AppRouteLink
                    key={item.href}
                    href={item.href}
                    className="block rounded-[0.85rem] border border-[#c6e6db] bg-[#f8fffc] px-3 py-2.5 transition hover:border-[#2f8f70] hover:bg-[#dff3eb]"
                  >
                    <span className="block text-sm font-semibold text-slate-100">{item.label}</span>
                    <span className="mt-1 block text-xs leading-5 text-slate-500">{item.summary}</span>
                  </AppRouteLink>
                ))
              ) : (
                <p className="text-xs leading-5 text-slate-500">В этой группе один рабочий раздел.</p>
              )}
            </div>
          </section>

          <section className={adminRailCardClass}>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-700">правила смены</p>
            <div className="mt-3 space-y-2 text-xs leading-5 text-slate-400">
              <p>Перед ручными действиями проверьте свежесть данных, очереди и сколько пользователей затронет изменение.</p>
              <p>Рискованные операции выполняйте здесь. Telegram оставляйте как резервный ручной канал.</p>
              <p>Используйте dry run, подтверждения и поле причины, когда действие это поддерживает.</p>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
