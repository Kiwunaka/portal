"use client";

import TelegramLoginWidget from "@/components/telegram-login-widget";
import { PortalSessionProvider, usePortalSession } from "@/lib/session";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

function EntryBody() {
  const router = useRouter();
  const {
    loading,
    error,
    webLoginRequired,
    webLoginBusy,
    webLoginError,
    user,
    dash,
    refresh,
    logoutWebSession,
  } = usePortalSession();

  useEffect(() => {
    if (!loading && !webLoginRequired && user && dash) {
      router.replace("/dashboard/");
    }
  }, [loading, webLoginRequired, user, dash, router]);

  if (loading) {
    return (
      <main className="mx-auto grid min-h-[70vh] w-[min(96vw,640px)] place-items-center">
        <section className="glass-card w-full p-7">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">portal webapp</p>
          <h1 className="mt-3 font-display text-4xl font-bold">Загружаем личный кабинет</h1>
          <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-200/80 dark:bg-slate-800">
            <div className="h-full w-1/3 animate-pulse rounded-full bg-violet-600" />
          </div>
        </section>
      </main>
    );
  }

  if (error) {
    return (
      <main className="mx-auto grid min-h-[70vh] w-[min(96vw,640px)] place-items-center">
        <section className="glass-card w-full p-7">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-rose-500">error</p>
          <h1 className="mt-3 font-display text-4xl font-bold">Не удалось открыть кабинет</h1>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">{error}</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <button className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]" onClick={() => void refresh()} type="button">
              Повторить
            </button>
            <Link href="https://t.me/net4ebur_bot" target="_blank" className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]">
              Открыть бота
            </Link>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="mx-auto grid min-h-[70vh] w-[min(96vw,680px)] place-items-center py-8">
      <section className="glass-card w-full p-7">
        <p className="font-mono text-xs uppercase tracking-[0.16em] text-violet-600 dark:text-violet-300">[web login]</p>
        <h1 className="mt-2 font-display text-4xl font-bold">Вход в личный кабинет PORTAL</h1>
        <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
          В Telegram вход произойдёт автоматически по initData. В браузере авторизуйтесь через Telegram Login Widget.
        </p>

        {webLoginRequired ? (
          <div className="mt-5 space-y-3">
            <TelegramLoginWidget />
            {webLoginBusy ? <p className="text-xs text-slate-500">Проверяем аккаунт...</p> : null}
            {webLoginError ? <p className="text-xs text-rose-500">{webLoginError}</p> : null}
          </div>
        ) : (
          <p className="mt-5 text-sm text-emerald-600 dark:text-emerald-300">Сессия найдена, открываем кабинет...</p>
        )}

        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="https://t.me/net4ebur_bot" target="_blank" className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]">
            Открыть бота
          </Link>
          <Link href="/dashboard/" className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]">
            Открыть кабинет
          </Link>
          <button className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]" onClick={logoutWebSession} type="button">
            Сбросить web-сессию
          </button>
        </div>
      </section>
    </main>
  );
}

export default function Page() {
  return (
    <PortalSessionProvider>
      <EntryBody />
    </PortalSessionProvider>
  );
}
