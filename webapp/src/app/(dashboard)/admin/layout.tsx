"use client";

import AppRouteLink from "@/components/app-route-link";
import { usePortalSession } from "@/lib/session";
import { Shield } from "lucide-react";
import { usePathname } from "next/navigation";
import { useMemo } from "react";
import { ADMIN_NAV_ITEMS } from "./nav";

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
    <main className="space-y-4">
      <section className="glass-card p-6">
        <p className="font-mono text-xs uppercase tracking-[0.15em] text-rose-500">{eyebrow}</p>
        <h1 className="mt-2 font-display text-3xl font-bold">{title}</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{description}</p>
        <div className="mt-4">
          <AppRouteLink href={primaryHref} className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em]">
            {primaryLabel}
          </AppRouteLink>
        </div>
      </section>
    </main>
  );
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { error, loading, user, webLoginRequired } = usePortalSession();

  const active = useMemo(
    () => ADMIN_NAV_ITEMS.find((item) => item.match(pathname))?.href || "/admin/dashboard",
    [pathname],
  );

  if (loading) {
    return (
      <main className="space-y-4">
        <section className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.15em] text-slate-500">админ</p>
          <h1 className="mt-2 font-display text-3xl font-bold">Открываем панель управления...</h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
            Подгружаем права доступа, метрики и рабочие разделы. Обычно это занимает пару секунд.
          </p>
          <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-200/60 dark:bg-slate-800">
            <div className="h-full w-1/3 animate-pulse rounded-full bg-violet-600" />
          </div>
        </section>
      </main>
    );
  }

  if (webLoginRequired) {
    return (
      <AdminStateCard
        eyebrow="сессия истекла"
        title="Нужно заново подтвердить вход"
        description="Браузерная сессия закончилась. Просто войдите через Telegram ещё раз, и админка откроется без дополнительных действий."
        primaryHref="/"
        primaryLabel="Открыть вход"
      />
    );
  }

  if (error && !user) {
    return (
      <AdminStateCard
        eyebrow="ошибка доступа"
        title="Не удалось проверить права администратора"
        description={error}
      />
    );
  }

  if (!user?.is_admin) {
    return (
      <AdminStateCard
        eyebrow="доступ закрыт"
        title="Раздел только для администраторов"
        description="У этого аккаунта нет прав администратора. Если доступ нужен для работы, назначьте роль в системе и попробуйте снова."
      />
    );
  }

  return (
    <main className="space-y-5">
      <section className="stat-card p-6">
        <div className="flex items-start gap-4">
          <div className="stat-icon stat-icon-violet">
            <Shield size={22} />
          </div>
          <div className="flex-1">
            <p className="font-mono text-xs uppercase tracking-[0.15em] text-violet-500 dark:text-violet-300">админ / pokrov</p>
            <h1 className="mt-1 font-display text-3xl font-bold">Панель управления</h1>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
              Здесь вы управляете пользователями, нодами, платежами, обращениями и рассылками. Если заходите впервые, начните со вкладки «Сводка».
            </p>
          </div>
        </div>
      </section>

      <section className="glass-card overflow-x-auto p-2">
        <nav className="flex flex-wrap gap-1.5">
          {ADMIN_NAV_ITEMS.map((item) => {
            const selected = active === item.href;
            return (
              <AppRouteLink
                key={item.href}
                href={item.href}
                className={`haptic-tap inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-semibold uppercase tracking-[0.1em] transition-all duration-200 ${
                  selected
                    ? "bg-gradient-to-r from-violet-600 to-violet-700 text-white shadow-lg shadow-violet-600/25"
                    : "text-slate-600 hover:bg-white/70 dark:text-slate-300 dark:hover:bg-white/10"
                }`}
              >
                <span className="material-symbols-rounded text-base" style={{ fontSize: "16px" }}>{item.icon}</span>
                <span className="hidden sm:inline">{item.label}</span>
              </AppRouteLink>
            );
          })}
        </nav>
        <div className="px-3 pb-3 pt-2 text-xs text-slate-500 dark:text-slate-400">
          «Сводка» показывает общее состояние сервиса, «Пользователи» помогает решать частные кейсы, а «Ноды» нужна для контроля инфраструктуры.
        </div>
      </section>

      {children}
    </main>
  );
}
