"use client";

import { usePortalSession } from "@/lib/session";
import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { useMemo, useState } from "react";

const BOT_BASE_URL = String(process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "https://t.me/portal_privacy_bot")
  .trim()
  .replace(/\/+$/, "");

function fmtNumber(value: number): string {
  if (!Number.isFinite(value)) return "0";
  return new Intl.NumberFormat("ru-RU").format(Math.max(0, Math.floor(value)));
}

export default function DevicesPage() {
  const { loading, error, user, dash } = usePortalSession();
  const [toast, setToast] = useState<string | null>(null);

  const activeSessions = Math.max(0, Number(dash?.active_sessions || 0));
  const deviceLimit = Math.max(1, Number(dash?.device_limit || user?.limits?.device_limit || 1));
  const freeSlots = Math.max(0, deviceLimit - activeSessions);

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
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">устройства</p>
          <h1 className="mt-2 font-display text-4xl font-bold">Загружаем данные...</h1>
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
          <Link href={BOT_BASE_URL} target="_blank" className="outline-btn mt-5 inline-flex rounded-xl px-4 py-2 text-sm font-semibold">
            Открыть бота
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">устройства</p>
        <h1 className="mt-2 font-display text-4xl font-bold">Устройства и сессии</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Показываем реальные данные учётной записи: активные сессии, лимиты и доступные ноды.
        </p>

        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl bg-white/70 p-3 dark:bg-white/10">
            <p className="text-xs text-slate-500">Активные сессии</p>
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
            Копировать ссылку доступа
          </button>
          <Link href="/dashboard/downloads" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
            Скачать приложения
          </Link>
          <Link href={BOT_BASE_URL} target="_blank" className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold">
            Открыть бота
          </Link>
        </div>
      </section>

      <section className="glass-card p-5">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="font-display text-2xl font-semibold">Ноды пользователя</h2>
          <span className="rounded-full bg-white/75 px-3 py-1 text-xs dark:bg-white/10">
            {fmtNumber(nodes.length)} шт.
          </span>
        </div>

        {nodes.length ? (
          <div className="space-y-2">
            {nodes.map((node) => (
              <article key={node.code} className="rounded-xl border border-white/30 bg-white/70 p-3 text-sm dark:border-white/10 dark:bg-white/5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-semibold">{node.name || node.code}</p>
                  <span className={`rounded-full px-2.5 py-1 text-[11px] uppercase tracking-[0.12em] ${node.enabled ? "bg-emerald-500 text-white" : "bg-slate-300 text-slate-700 dark:bg-slate-700 dark:text-slate-100"}`}>
                    {node.enabled ? "включена" : "выключена"}
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-500">Код: {node.code}</p>
                <p className="text-xs text-slate-500">Хост: {node.host}:{node.port}</p>
              </article>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-500">Ноды пока не привязаны к пользователю.</p>
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
