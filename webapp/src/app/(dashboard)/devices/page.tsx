"use client";

import AppRouteLink from "@/components/app-route-link";
import { getPortalPublicConfig } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { AnimatePresence, motion } from "framer-motion";
import { useMemo, useState } from "react";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

function fmtNumber(value: number): string {
  if (!Number.isFinite(value)) return "0";
  return new Intl.NumberFormat("ru-RU").format(Math.max(0, Math.floor(value)));
}

function isTrialLike(subType?: string | null): boolean {
  const value = String(subType || "").toUpperCase();
  return value.includes("TRIAL") || value.includes("FREE");
}

export default function DevicesPage() {
  const { loading, error, user, dash } = usePortalSession();
  const [toast, setToast] = useState<string | null>(null);

  const activeSessions = Math.max(0, Number(dash?.active_sessions || 0));
  const deviceLimit = Math.max(1, Number(dash?.device_limit || user?.limits?.device_limit || 1));
  const freeSlots = Math.max(0, deviceLimit - activeSessions);
  const trialMode = isTrialLike(dash?.sub_type || dash?.current_plan_code || user?.sub_type);

  const nodes = useMemo(() => {
    const list = [...(user?.nodes || [])];
    list.sort((a, b) => Number(Boolean(b.enabled)) - Number(Boolean(a.enabled)));
    return list;
  }, [user?.nodes]);

  const popToast = (text: string): void => {
    setToast(text);
    window.setTimeout(() => setToast(null), 1800);
  };

  const copySubscription = async (): Promise<void> => {
    const value = String(user?.subscription_url || "").trim();
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      popToast("Ссылка доступа скопирована.");
    } catch {
      popToast("Не удалось скопировать ссылку.");
    }
  };

  if (loading) {
    return (
      <main className="space-y-6">
        <section className="glass-card p-7">
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">devices</p>
          <h1 className="mt-2 font-display text-4xl font-bold">Загружаем устройства...</h1>
        </section>
      </main>
    );
  }

  if (error || !user || !dash) {
    return (
      <main className="space-y-6">
        <section className="glass-card p-7">
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-rose-500">ошибка</p>
          <h1 className="mt-2 font-display text-4xl font-bold">Не удалось загрузить устройства</h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{error || "Нет данных профиля."}</p>
          <AppRouteLink href={config.botUrl} target="_blank" hardNavigate={false} className="outline-btn mt-5 inline-flex rounded-xl px-4 py-2 text-sm font-semibold">
            Открыть Telegram
          </AppRouteLink>
        </section>
      </main>
    );
  }

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">devices</p>
        <h1 className="mt-2 font-display text-4xl font-bold">Устройства и точки подключения</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Здесь видно, сколько устройств уже подключено, сколько слотов доступно сейчас и какие точки работают по вашему профилю.
        </p>

        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl bg-white/70 p-3 dark:bg-white/10">
            <p className="text-xs text-slate-500">Подключено сейчас</p>
            <p className="mt-1 text-2xl font-semibold">{fmtNumber(activeSessions)}</p>
          </div>
          <div className="rounded-xl bg-white/70 p-3 dark:bg-white/10">
            <p className="text-xs text-slate-500">Лимит устройств</p>
            <p className="mt-1 text-2xl font-semibold">{fmtNumber(deviceLimit)}</p>
          </div>
          <div className="rounded-xl bg-white/70 p-3 dark:bg-white/10">
            <p className="text-xs text-slate-500">Свободные слоты</p>
            <p className="mt-1 text-2xl font-semibold">{fmtNumber(freeSlots)}</p>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          <button type="button" onClick={() => void copySubscription()} className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
            Скопировать ссылку доступа
          </button>
          <AppRouteLink href="/dashboard/downloads" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
            Открыть приложения
          </AppRouteLink>
          <AppRouteLink href={config.supportTelegramUrl} target="_blank" hardNavigate={false} className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold">
            Поддержка
          </AppRouteLink>
        </div>
      </section>

      {trialMode ? (
        <section className="glass-card p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-orange-500">trial / free</p>
              <h2 className="mt-2 font-display text-2xl font-semibold">Нужны дополнительные устройства?</h2>
              <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-300">
                В тестовом и базовом режиме число устройств ограничено. Если хотите подключить больше техники и не думать о лимитах, переходите к тарифам или продолжайте в Telegram.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <AppRouteLink href="/dashboard/subscription" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
                Смотреть тарифы
              </AppRouteLink>
              <AppRouteLink href={config.botUrl} target="_blank" hardNavigate={false} className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold">
                Продолжить в Telegram
              </AppRouteLink>
            </div>
          </div>
        </section>
      ) : null}

      <section className="glass-card p-5">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="font-display text-2xl font-semibold">Точки подключения</h2>
          <span className="rounded-full bg-white/75 px-3 py-1 text-xs dark:bg-white/10">{fmtNumber(nodes.length)} шт.</span>
        </div>

        {nodes.length ? (
          <div className="space-y-2">
            {nodes.map((node) => (
              <article key={node.code} className="rounded-xl border border-white/30 bg-white/70 p-3 text-sm dark:border-white/10 dark:bg-white/5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-semibold">{node.name || node.code}</p>
                  <span className={`rounded-full px-2.5 py-1 text-[11px] uppercase tracking-[0.12em] ${node.enabled ? "bg-emerald-500 text-white" : "bg-slate-300 text-slate-700 dark:bg-slate-700 dark:text-slate-100"}`}>
                    {node.enabled ? "доступна" : "выключена"}
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-500">Код: {node.code}</p>
                <p className="text-xs text-slate-500">
                  Хост: {node.host}:{node.port}
                </p>
              </article>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-500">Точки подключения пока не назначены. Если это выглядит неожиданно, напишите в поддержку.</p>
        )}
      </section>

      <AnimatePresence>
        {toast ? (
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 14 }}
            className="fixed bottom-24 left-1/2 z-[210] -translate-x-1/2 rounded-full bg-slate-900 px-4 py-2 text-xs text-white shadow-xl"
          >
            {toast}
          </motion.div>
        ) : null}
      </AnimatePresence>
    </main>
  );
}
