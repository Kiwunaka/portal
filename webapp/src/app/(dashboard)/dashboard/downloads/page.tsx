"use client";

import { fetchClientApps, type ClientAppsPayload } from "@/lib/api";
import { getCopyText, getPortalPublicConfig } from "@/lib/portal";
import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

type AppCard = {
  name: string;
  details: string;
  icon: string;
  links: Array<{ label: string; href: string }>;
};

function buildCards(payload: ClientAppsPayload | null): AppCard[] {
  const androidPlay = payload?.android?.play_url || config.androidPlayUrl;
  const androidApk = payload?.android?.apk_url || config.androidApkUrl;
  const androidMirror = payload?.android?.mirror_url || config.androidMirrorUrl;
  const windowsExe = payload?.windows?.exe_url || config.windowsExeUrl;
  const windowsMirror = payload?.windows?.mirror_url || config.windowsMirrorUrl;
  const docsUrl = payload?.docs_url || config.docsUrl;

  return [
    {
      name: "Android",
      details: "Google Play, APK и резервный вариант",
      icon: "android",
      links: [
        { label: "Google Play", href: androidPlay },
        { label: "APK", href: androidApk },
        { label: "Резервная ссылка", href: androidMirror }
      ].filter((item) => item.href)
    },
    {
      name: "Windows",
      details: "EXE и резервный вариант",
      icon: "desktop_windows",
      links: [
        { label: "Скачать EXE", href: windowsExe },
        { label: "Резервная ссылка", href: windowsMirror }
      ].filter((item) => item.href)
    },
    {
      name: "Справка",
      details: "Короткие инструкции и быстрый запуск",
      icon: "menu_book",
      links: docsUrl ? [{ label: "Открыть справку", href: docsUrl }] : []
    }
  ].filter((card) => card.links.length > 0);
}

export default function DownloadsPage() {
  const [payload, setPayload] = useState<ClientAppsPayload | null>(null);
  const [error, setError] = useState("");
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const next = await fetchClientApps();
        if (!cancelled) {
          setPayload(next);
          setError("");
        }
      } catch (nextError) {
        if (!cancelled) {
          setError(String((nextError as { message?: string })?.message || nextError || ""));
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const cards = useMemo(() => buildCards(payload), [payload]);

  const notify = (message: string): void => {
    setToast(message);
    window.setTimeout(() => setToast(null), 1800);
  };

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <div className="flex flex-col items-start justify-between gap-4 md:flex-row md:items-center">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">приложения</p>
            <h1 className="mt-2 font-display text-4xl font-bold">{getCopyText("webapp.downloads.title", "Приложения и быстрый запуск")}</h1>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              {getCopyText(
                "webapp.downloads.subtitle",
                "Показываем только актуальные ссылки для Android, Windows и справки.",
              )}
            </p>
          </div>
          <Link href="/dashboard" className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]">
            Открыть кабинет
          </Link>
        </div>
      </section>

      <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {cards.map((app, idx) => (
          <motion.article
            key={app.name}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.05 }}
            className="glass-card p-6"
          >
            <span className="float-slow material-symbols-rounded rounded-xl bg-violet-100 p-3 text-3xl text-violet-600 dark:bg-violet-900/35 dark:text-violet-200">
              {app.icon}
            </span>
            <h2 className="mt-4 font-display text-3xl font-semibold">{app.name}</h2>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{app.details}</p>
            <div className="mt-6 grid gap-2">
              {app.links.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => notify(`${app.name}: открыли ссылку.`)}
                  className="btn-primary rounded-xl py-2.5 text-center text-sm font-semibold uppercase tracking-[0.12em]"
                >
                  {link.label}
                </a>
              ))}
            </div>
          </motion.article>
        ))}
      </section>

      <section className="glass-card p-7">
        <div className="flex flex-col items-start justify-between gap-5 md:flex-row md:items-center">
          <div>
            <h3 className="font-display text-2xl font-semibold">Нужна помощь с установкой?</h3>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              Если что-то пошло не так, наша дружелюбная служба заботы мгновенно поможет в Telegram.
            </p>
            {payload?.updated_at ? <p className="mt-1 text-xs text-slate-500">Актуальность ссылок: {new Date(payload.updated_at).toLocaleString("ru-RU")}</p> : null}
            {error ? <p className="mt-2 text-xs text-amber-600 dark:text-amber-300">Часть ссылок не подтянулась автоматически: {error}</p> : null}
          </div>
          <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="btn-primary rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Открыть службу заботы
          </a>
        </div>
      </section>

      <AnimatePresence>
        {toast ? (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            className="fixed bottom-24 left-1/2 z-[210] -translate-x-1/2 rounded-full bg-slate-900 px-4 py-2 text-xs text-white shadow-xl"
          >
            {toast}
          </motion.div>
        ) : null}
      </AnimatePresence>
    </main>
  );
}
