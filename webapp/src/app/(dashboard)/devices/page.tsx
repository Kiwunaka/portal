"use client";

import AppRouteLink from "@/components/app-route-link";
import {
  getAccessState,
  getDeviceLimit,
  getTrafficLimitGb,
  isFreeMonthlyState,
  isPaidUnlimitedState,
  isTrialPremiumState,
} from "@/lib/access-policy";
import { getPortalPublicConfig } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { AnimatePresence, motion } from "framer-motion";
import { useMemo, useState } from "react";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

function fmtNumber(value: number): string {
  if (!Number.isFinite(value)) return "0";
  return new Intl.NumberFormat("ru-RU").format(Math.max(0, Math.floor(value)));
}

export default function DevicesPage() {
  const { loading, error, user, dash } = usePortalSession();
  const [toast, setToast] = useState<string | null>(null);

  const activeConnections = Math.max(0, Number(dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? 0));
  const deviceLimit = getDeviceLimit(dash, user);
  const knownAppDevices = Math.max(0, Number(user?.sync?.device_count ?? user?.devices?.length ?? 0));
  const activeNodes = Math.max(0, Number(dash?.connection_snapshot?.active_nodes ?? 0));
  const knownNodes = Math.max(0, Number(dash?.connection_snapshot?.known_nodes ?? user?.nodes?.length ?? 0));
  const accessState = getAccessState(dash, user);
  const paidMode = isPaidUnlimitedState(accessState);
  const trialMode = isTrialPremiumState(accessState);
  const freeMode = isFreeMonthlyState(accessState);
  const freeLimitGb = getTrafficLimitGb(dash, user);

  const nodes = useMemo(() => {
    const list = [...(user?.nodes || [])];
    list.sort((a, b) => Number(Boolean(b.enabled)) - Number(Boolean(a.enabled)));
    return list;
  }, [user?.nodes]);

  const copySubscription = async (): Promise<void> => {
    const value = String(user?.subscription_url || "").trim();
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      setToast("Ссылка подключения скопирована.");
    } catch {
      setToast("Ссылка не скопировалась. Попробуйте ещё раз.");
    }
    window.setTimeout(() => setToast(null), 1800);
  };

  if (loading) {
    return (
      <main className="space-y-6">
        <section className="glass-card p-7">
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">устройства</p>
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
          <AppRouteLink
            href={config.botUrl}
            target="_blank"
            hardNavigate={false}
            className="outline-btn mt-5 inline-flex rounded-xl px-4 py-2 text-sm font-semibold"
          >
            Открыть Telegram
          </AppRouteLink>
        </section>
      </main>
    );
  }

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">устройства</p>
        <h1 className="mt-2 font-display text-4xl font-bold">Устройства и подключения</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Живые подключения считаются по runtime-нодам POKROV. Это работает и для приложения, и для импортированного
          конфига на сайте, в боте и вручную.
        </p>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          {paidMode
            ? "На paid доступно до 5 устройств и безлимитный трафик."
            : trialMode
              ? "Во время премиум-периода можно спокойно проверить сервис на нескольких своих устройствах."
              : freeMode
                ? `На бесплатном режиме доступно до ${deviceLimit} устройства и ${freeLimitGb ? `${fmtNumber(freeLimitGb)} ГБ в месяц` : "месячная квота"}.`
                : "Текущее число подключений зависит от активной политики профиля."}
        </p>

        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl bg-white/70 p-3 dark:bg-white/10">
            <p className="text-xs text-slate-500">Подключений сейчас</p>
            <p className="mt-1 text-2xl font-semibold">
              {fmtNumber(activeConnections)} / {fmtNumber(deviceLimit)}
            </p>
            <p className="mt-1 text-[11px] text-slate-500">Из доступных слотов тарифа</p>
          </div>
          <div className="rounded-xl bg-white/70 p-3 dark:bg-white/10">
            <p className="text-xs text-slate-500">Нод с активностью</p>
            <p className="mt-1 text-2xl font-semibold">
              {fmtNumber(activeNodes)} / {fmtNumber(knownNodes)}
            </p>
            <p className="mt-1 text-[11px] text-slate-500">Где сейчас виден ваш ключ</p>
          </div>
          <div className="rounded-xl bg-white/70 p-3 dark:bg-white/10">
            <p className="text-xs text-slate-500">Известных app-устройств</p>
            <p className="mt-1 text-2xl font-semibold">{fmtNumber(knownAppDevices)}</p>
            <p className="mt-1 text-[11px] text-slate-500">Это отдельная app-first телеметрия</p>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          <button type="button" onClick={() => void copySubscription()} className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
            Скопировать ссылку подключения
          </button>
          <AppRouteLink href="/dashboard/downloads" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
            Мои приложения
          </AppRouteLink>
          <AppRouteLink
            href={config.supportTelegramUrl}
            target="_blank"
            hardNavigate={false}
            className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold"
          >
            Служба заботы
          </AppRouteLink>
        </div>
      </section>

      {!paidMode ? (
        <section className="glass-card p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-orange-500">
                {trialMode ? "премиум-период" : "бесплатный режим"}
              </p>
              <h2 className="mt-2 font-display text-2xl font-semibold">
                {trialMode ? "Нужны дополнительные устройства после премиум-периода?" : "Нужен безлимит и больше устройств?"}
              </h2>
              <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-300">
                {trialMode
                  ? "После премиум-периода профиль перейдёт в бесплатный режим 5 ГБ в месяц, поэтому paid-тариф лучше выбрать заранее, если устройств несколько."
                  : "Paid оставляет до 5 устройств и безлимитный трафик, а бесплатный профиль остаётся месячным вариантом с квотой."}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <AppRouteLink href="/subscription" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
                Перейти к тарифам
              </AppRouteLink>
              <AppRouteLink
                href={config.botUrl}
                target="_blank"
                hardNavigate={false}
                className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold"
              >
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
          <p className="text-sm text-slate-500">Точки подключения пока не назначены. Если это выглядит неожиданно, напишите в службу заботы.</p>
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
