"use client";

import AppRouteLink from "@/components/app-route-link";
import TelegramLoginWidget from "@/components/telegram-login-widget";
import { getPortalPublicConfig } from "@/lib/portal";
import { PortalSessionProvider, usePortalSession } from "@/lib/session";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const BOT_WEBLOGIN_URL = `${config.botUrl}${config.botUrl.includes("?") ? "&" : "?"}start=weblogin`;

const ENTRY_STEPS = [
  {
    title: "Откройте Telegram",
    text: "Нажмите кнопку ниже или дождитесь встроенного виджета. Вход начнётся прямо через Telegram.",
  },
  {
    title: "Подтвердите аккаунт",
    text: "Telegram сверит данные и вернёт вас обратно без лишних промежуточных экранов.",
  },
  {
    title: "Добро пожаловать",
    text: "Если доступ уже подтверждён, кабинет откроется автоматически и сразу покажет ваш статус.",
  },
] as const;

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
      <main className="relative mx-auto flex min-h-[calc(100vh-2rem)] w-[min(96vw,1040px)] items-center justify-center px-4 py-8 sm:px-6">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.16),_transparent_32%),radial-gradient(circle_at_bottom_right,_rgba(245,158,11,0.12),_transparent_30%)]" />
        <section className="glass-card w-full overflow-hidden border border-white/60 p-8 shadow-2xl shadow-slate-950/10 dark:border-slate-800/80 dark:shadow-black/30">
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-300">
            POKROV VPN
          </p>
          <h1 className="mt-3 font-display text-4xl font-bold">Подтягиваем ваш кабинет</h1>
          <p className="mt-3 max-w-xl text-sm leading-6 text-slate-600 dark:text-slate-300">
            Проверяем доступ и готовим безопасный вход через Telegram. Обычно это занимает всего несколько секунд.
          </p>
          <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-200/80 dark:bg-slate-800">
            <div className="h-full w-1/3 animate-pulse rounded-full bg-emerald-600" />
          </div>
        </section>
      </main>
    );
  }

  if (error) {
    return (
      <main className="relative mx-auto flex min-h-[calc(100vh-2rem)] w-[min(96vw,920px)] items-center justify-center px-4 py-8 sm:px-6">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.15),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(239,68,68,0.10),_transparent_30%)]" />
        <section className="glass-card w-full overflow-hidden border border-white/60 p-8 shadow-2xl shadow-slate-950/10 dark:border-slate-800/80 dark:shadow-black/30">
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-rose-500">POKROV VPN</p>
          <h1 className="mt-3 font-display text-4xl font-bold">Не удалось открыть кабинет</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300">{error}</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button
              className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]"
              onClick={() => void refresh()}
              type="button"
            >
              Проверить ещё раз
            </button>
            <AppRouteLink
              href={BOT_WEBLOGIN_URL}
              target="_blank"
              hardNavigate={false}
              className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]"
            >
              Открыть Telegram
            </AppRouteLink>
            <button
              className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]"
              onClick={() => logoutWebSession()}
              type="button"
            >
              Начать заново
            </button>
          </div>
          <p className="mt-5 text-xs leading-5 text-slate-500 dark:text-slate-400">
            Если вы уже подтвердили вход в Telegram, просто попробуйте повторить проверку. Если нет, откройте бота и завершите авторизацию там.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="relative mx-auto flex min-h-[calc(100vh-2rem)] w-[min(96vw,1120px)] items-center justify-center px-4 py-8 sm:px-6">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.16),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(245,158,11,0.12),_transparent_30%)]" />
      <section className="glass-card relative w-full overflow-hidden border border-white/60 shadow-2xl shadow-slate-950/10 dark:border-slate-800/80 dark:shadow-black/30">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-400/70 to-transparent" />
        <div className="grid gap-0 lg:grid-cols-[1.08fr_0.92fr]">
          <div className="space-y-6 px-6 py-8 sm:px-8 sm:py-10 lg:border-r lg:border-white/60 lg:dark:border-slate-800/80">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200/70 bg-emerald-50/80 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-200">
              POKROV VPN
            </div>
            <div className="max-w-2xl space-y-4">
              <h1 className="font-display text-4xl font-bold leading-[1.05] sm:text-5xl">
                Продолжим вход и сразу откроем кабинет
              </h1>
              <p className="max-w-xl text-sm leading-6 text-slate-600 dark:text-slate-300">
                В браузере вход подтверждается через Telegram. Если доступ уже есть, мы переведём вас в кабинет автоматически. Если нет, покажем понятную кнопку и не оставим в тупике.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              {ENTRY_STEPS.map((step, index) => (
                <article
                  key={step.title}
                  className="rounded-2xl border border-slate-200/70 bg-white/70 p-4 shadow-sm shadow-slate-900/5 dark:border-slate-800/70 dark:bg-slate-950/25 dark:shadow-black/10"
                >
                  <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">
                    0{index + 1}
                  </p>
                  <h2 className="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{step.title}</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{step.text}</p>
                </article>
              ))}
            </div>

            <div className="rounded-3xl border border-slate-200/70 bg-slate-50/80 p-5 dark:border-slate-800/70 dark:bg-slate-950/30">
              <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-emerald-600 dark:text-emerald-300">
                Памятка
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                Если Telegram не откроется автоматически, нажмите кнопку ниже. Это тот же вход, только в ручном режиме.
              </p>
            </div>
          </div>

          <div className="px-6 py-8 sm:px-8 sm:py-10">
            <div className="rounded-3xl border border-slate-200/70 bg-white/85 p-5 shadow-lg shadow-slate-900/5 backdrop-blur dark:border-slate-800/70 dark:bg-slate-950/35 dark:shadow-black/20">
              <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">
                Telegram login
              </p>
              <h2 className="mt-2 font-display text-2xl font-bold">Подтвердите аккаунт</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                Нажмите кнопку Telegram, вернитесь обратно и мы продолжим без лишних экранов.
              </p>

              <div className="mt-5">
                <TelegramLoginWidget />
              </div>

              <div className="mt-5 flex flex-wrap gap-3">
                <AppRouteLink
                  href={BOT_WEBLOGIN_URL}
                  target="_blank"
                  hardNavigate={false}
                  className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]"
                >
                  Открыть Telegram
                </AppRouteLink>
                <button
                  className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]"
                  onClick={() => logoutWebSession()}
                  type="button"
                >
                  Сбросить вход
                </button>
              </div>

              <p className="mt-4 text-xs leading-5 text-slate-500 dark:text-slate-400" aria-live="polite">
                {webLoginBusy
                  ? "Проверяем вход через Telegram..."
                  : webLoginError
                    ? webLoginError
                    : "Если вход уже подтверждён, кабинет откроется автоматически."}
              </p>
            </div>

            <p className="mt-4 text-xs leading-5 text-slate-500 dark:text-slate-400">
              Вход подтверждается на стороне Telegram. Мы не просим лишних данных и не делаем лишних шагов между вами и кабинетом.
            </p>
          </div>
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
