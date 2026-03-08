"use client";

import AppRouteLink from "@/components/app-route-link";
import TelegramLoginWidget from "@/components/telegram-login-widget";
import { getPortalPublicConfig } from "@/lib/portal";
import { PortalSessionProvider, usePortalSession } from "@/lib/session";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const BOT_WEBLOGIN_URL = `${config.botUrl}${config.botUrl.includes("?") ? "&" : "?"}start=weblogin`;

function EntryBody() {
  const router = useRouter();
  const { loading, error, webLoginRequired, webLoginBusy, webLoginError, refresh, logoutWebSession } =
    usePortalSession();

  useEffect(() => {
    if (!loading && !webLoginRequired) {
      router.replace("/dashboard/");
    }
  }, [loading, router, webLoginRequired]);

  if (loading) {
    return (
      <main className="mx-auto grid min-h-[70vh] w-[min(96vw,640px)] place-items-center">
        <section className="glass-card w-full p-7">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">portal webapp</p>
          <h1 className="mt-3 font-display text-4xl font-bold">Загружаем кабинет</h1>
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
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-rose-500">ошибка</p>
          <h1 className="mt-3 font-display text-4xl font-bold">Не удалось открыть кабинет</h1>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">{error}</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <button
              className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]"
              onClick={() => void refresh()}
              type="button"
            >
              Повторить
            </button>
            <AppRouteLink
              href={BOT_WEBLOGIN_URL}
              target="_blank"
              hardNavigate={false}
              className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]"
            >
              Продолжить через Telegram
            </AppRouteLink>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="mx-auto grid min-h-[70vh] w-[min(96vw,680px)] place-items-center py-8">
      <section className="glass-card w-full p-7">
        <p className="font-mono text-xs uppercase tracking-[0.16em] text-violet-600 dark:text-violet-300">
          portal entry
        </p>
        <h1 className="mt-2 font-display text-4xl font-bold">Продолжить вход в PORTAL</h1>
        <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
          В браузере вход подтверждается через Telegram. После подтверждения кабинет откроется сразу, без лишнего промежуточного экрана.
        </p>

        {webLoginRequired ? (
          <div className="mt-5 space-y-3">
            <TelegramLoginWidget />
            <p className="text-xs text-slate-500">
              Если виджет не открылся, кнопка ниже сделает тот же вход через Telegram.
            </p>
            {webLoginBusy ? <p className="text-xs text-slate-500">Проверяем аккаунт...</p> : null}
            {webLoginError ? <p className="text-xs text-rose-500">{webLoginError}</p> : null}
          </div>
        ) : (
          <p className="mt-5 text-sm text-emerald-600 dark:text-emerald-300">Вход подтверждён, открываем кабинет...</p>
        )}

        <div className="mt-6 flex flex-wrap gap-3">
          <AppRouteLink
            href={BOT_WEBLOGIN_URL}
            target="_blank"
            hardNavigate={false}
            className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]"
          >
            Открыть Telegram
          </AppRouteLink>
          <AppRouteLink
            href="/webapp/?clear_web_session=1"
            className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]"
          >
            Очистить веб-вход
          </AppRouteLink>
        </div>
      </section>
    </main>
  );
}

export default function Page() {
  return (
    <PortalSessionProvider mode="entry">
      <EntryBody />
    </PortalSessionProvider>
  );
}
