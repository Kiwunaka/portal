"use client";

import AppRouteLink from "@/components/app-route-link";
import TelegramLoginWidget from "@/components/telegram-login-widget";
import { getCopyText, getPortalPublicConfig } from "@/lib/portal";
import { PortalSessionProvider, usePortalSession } from "@/lib/session";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const BOT_WEBLOGIN_URL = `${config.botUrl}${config.botUrl.includes("?") ? "&" : "?"}start=weblogin`;

const ENTRY_PILLARS = [
  {
    icon: "lock",
    title: "Вход без паролей",
    text: "Подтверждаете Telegram и возвращаетесь в кабинет без лишних шагов и ручных кодов.",
  },
  {
    icon: "vpn_key",
    title: "Доступ и продление в одном месте",
    text: "Статус подписки, продление и ссылка подключения собираются в одной спокойной точке входа.",
  },
  {
    icon: "support_agent",
    title: "Поддержка рядом",
    text: "Если что-то пойдет не так, служба заботы уже находится внутри того же маршрута, без поиска по чатам.",
  },
] as const;

const LOGIN_FACTS = [
  {
    label: "Подтверждение обычно занимает",
    value: "до минуты",
  },
  {
    label: "Оплаченный доступ открывает",
    value: "до 5 устройств",
  },
  {
    label: "Telegram-бонус после привязки",
    value: "+10 дней",
  },
] as const;

const CABINET_AREAS = [
  "Статус доступа и срок действия без ручной проверки.",
  "Продление и планы в том же кабинете, без новой настройки.",
  "Ссылка подключения и служба заботы под рукой, когда они реально нужны.",
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
      <main className="relative mx-auto flex min-h-[calc(100vh-2rem)] w-[min(96vw,1120px)] items-center justify-center px-4 py-8 sm:px-6 lg:py-10">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(11,72,50,0.16),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(197,138,42,0.14),_transparent_32%)]" />
        <section className="glass-card w-full overflow-hidden border border-white/70 dark:border-[#243129]/80">
          <div className="grid gap-0 lg:grid-cols-[1.06fr_0.94fr]">
            <div className="space-y-5 px-6 py-8 sm:px-8 sm:py-10 lg:px-10 lg:py-11">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-900/10 bg-emerald-900/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-900/70 dark:border-emerald-100/10 dark:bg-emerald-100/5 dark:text-emerald-100/70">
                cabinet access
              </div>
              <div className="space-y-3">
                <h1 className="font-display text-4xl font-semibold leading-[0.98] text-slate-900 dark:text-slate-50 sm:text-5xl">
                  Подготавливаем ваш кабинет POKROV VPN
                </h1>
                <p className="max-w-xl text-sm leading-7 text-slate-600 dark:text-slate-300">
                  Проверяем текущий вход и собираем аккуратный маршрут в кабинет, чтобы доступ, продление и поддержка открылись без лишнего шума.
                </p>
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                {LOGIN_FACTS.map((item) => (
                  <div
                    key={item.label}
                    className="rounded-[22px] border border-white/60 bg-white/65 px-4 py-4 dark:border-white/10 dark:bg-white/[0.04]"
                  >
                    <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                      {item.label}
                    </p>
                    <p className="mt-2 font-display text-2xl font-semibold text-slate-900 dark:text-slate-50">
                      {item.value}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-white/60 bg-white/55 px-6 py-8 dark:border-white/10 dark:bg-white/[0.03] lg:border-l lg:border-t-0 lg:px-10 lg:py-11">
              <div className="rounded-[28px] border border-white/70 bg-white/88 p-6 shadow-[0_24px_60px_-38px_rgba(18,48,36,0.55)] dark:border-white/10 dark:bg-[#121b17]/90">
                <div className="space-y-3">
                  <div className="h-3 w-28 rounded-full bg-slate-200/80 dark:bg-slate-800" />
                  <div className="h-11 rounded-2xl bg-slate-200/70 dark:bg-slate-800" />
                  <div className="h-11 rounded-2xl bg-slate-200/70 dark:bg-slate-800" />
                  <div className="h-2 overflow-hidden rounded-full bg-slate-200/80 dark:bg-slate-800">
                    <div className="h-full w-1/3 animate-pulse rounded-full bg-emerald-700 dark:bg-emerald-500" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    );
  }

  if (error) {
    return (
      <main className="relative mx-auto flex min-h-[calc(100vh-2rem)] w-[min(96vw,980px)] items-center justify-center px-4 py-8 sm:px-6 lg:py-10">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(11,72,50,0.12),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(190,24,93,0.10),_transparent_30%)]" />
        <section className="glass-card w-full overflow-hidden border border-white/70 p-7 dark:border-[#243129]/80 sm:p-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-rose-200/70 bg-rose-50/80 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-rose-700 dark:border-rose-400/20 dark:bg-rose-400/10 dark:text-rose-200">
            нужен повторный вход
          </div>
          <h1 className="mt-4 font-display text-4xl font-semibold leading-[1.02] text-slate-900 dark:text-slate-50 sm:text-5xl">
            Не получилось открыть кабинет
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">{error}</p>

          <div className="mt-7 grid gap-3 sm:grid-cols-3">
            {CABINET_AREAS.map((text, index) => (
              <article
                key={text}
                className="rounded-[24px] border border-white/70 bg-white/68 p-4 dark:border-white/10 dark:bg-white/[0.04]"
              >
                <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">0{index + 1}</p>
                <p className="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">{text}</p>
              </article>
            ))}
          </div>

          <div className="mt-7 flex flex-wrap gap-3">
            <button
              className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
              onClick={() => void refresh()}
              type="button"
            >
              Повторить попытку
            </button>
            <AppRouteLink
              href={BOT_WEBLOGIN_URL}
              target="_blank"
              hardNavigate={false}
              className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
            >
              Открыть Telegram
            </AppRouteLink>
            <button
              className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
              onClick={() => logoutWebSession()}
              type="button"
            >
              Сменить аккаунт
            </button>
          </div>

          <p className="mt-5 text-xs leading-6 text-slate-500 dark:text-slate-400">
            Если открыли кабинет отдельно от Telegram, просто заново подтвердите вход. После этого мы вернем вас обратно в кабинет автоматически.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="relative mx-auto flex min-h-[calc(100vh-2rem)] w-[min(96vw,1220px)] items-center justify-center px-4 py-8 sm:px-6 lg:py-10">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(11,72,50,0.16),_transparent_32%),radial-gradient(circle_at_bottom_right,_rgba(197,138,42,0.14),_transparent_32%)]" />
      <section className="glass-card relative w-full overflow-hidden border border-white/70 dark:border-[#243129]/80">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-700/45 to-transparent dark:via-emerald-300/30" />
        <div className="grid gap-0 lg:grid-cols-[1.08fr_0.92fr]">
          <div className="relative space-y-8 px-6 py-8 sm:px-8 sm:py-10 lg:px-10 lg:py-11">
            <div className="absolute right-0 top-0 hidden h-56 w-56 rounded-full bg-emerald-900/5 blur-3xl lg:block dark:bg-emerald-300/5" />

            <div className="space-y-5">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-900/10 bg-emerald-900/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-900/70 dark:border-emerald-100/10 dark:bg-emerald-100/5 dark:text-emerald-100/70">
                personal cabinet
              </div>

              <div className="max-w-2xl space-y-4">
                <h1 className="font-display text-4xl font-semibold leading-[0.96] text-slate-900 dark:text-slate-50 sm:text-5xl lg:text-[3.6rem]">
                  {getCopyText("webapp.entry.title", "Личный кабинет POKROV VPN")}
                </h1>
                <p className="max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300 sm:text-[15px]">
                  {getCopyText(
                    "webapp.entry.subtitle",
                    "Здесь удобно продолжать доступ: проверить статус, спокойно продлить подписку, открыть ссылку подключения и быстро выйти на поддержку, если она понадобится.",
                  )}
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                {LOGIN_FACTS.map((item) => (
                  <article
                    key={item.label}
                    className="rounded-[24px] border border-white/70 bg-white/68 px-4 py-4 dark:border-white/10 dark:bg-white/[0.04]"
                  >
                    <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                      {item.label}
                    </p>
                    <p className="mt-2 font-display text-[1.7rem] font-semibold leading-none text-slate-900 dark:text-slate-50">
                      {item.value}
                    </p>
                  </article>
                ))}
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              {ENTRY_PILLARS.map((item) => (
                <article
                  key={item.title}
                  className="rounded-[26px] border border-white/70 bg-white/62 p-5 shadow-[0_24px_50px_-40px_rgba(18,48,36,0.45)] dark:border-white/10 dark:bg-white/[0.04]"
                >
                  <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-900/8 text-emerald-800 dark:bg-emerald-200/10 dark:text-emerald-200">
                    <span className="material-symbols-rounded text-[22px]">{item.icon}</span>
                  </span>
                  <h2 className="mt-4 text-base font-semibold text-slate-900 dark:text-slate-50">{item.title}</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.text}</p>
                </article>
              ))}
            </div>

            <div className="rounded-[30px] border border-emerald-900/8 bg-[linear-gradient(135deg,rgba(255,255,255,0.88),rgba(243,247,244,0.92))] p-5 shadow-[0_30px_60px_-44px_rgba(18,48,36,0.45)] dark:border-emerald-200/10 dark:bg-[linear-gradient(135deg,rgba(18,27,23,0.88),rgba(14,22,18,0.94))]">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-800/80 dark:text-emerald-200/80">
                Что откроется внутри
              </p>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                {CABINET_AREAS.map((text, index) => (
                  <div
                    key={text}
                    className="rounded-[22px] border border-emerald-900/8 bg-white/72 p-4 dark:border-emerald-200/10 dark:bg-white/[0.03]"
                  >
                    <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">0{index + 1}</p>
                    <p className="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">{text}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="border-t border-white/60 bg-white/55 px-6 py-8 dark:border-white/10 dark:bg-white/[0.03] sm:px-8 sm:py-10 lg:border-l lg:border-t-0 lg:px-10 lg:py-11">
            <div className="rounded-[30px] border border-white/70 bg-white/88 p-6 shadow-[0_26px_60px_-38px_rgba(18,48,36,0.5)] dark:border-white/10 dark:bg-[#121b17]/90">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                secure Telegram login
              </p>
              <h2 className="mt-3 font-display text-[2rem] font-semibold leading-[0.98] text-slate-900 dark:text-slate-50">
                {getCopyText("webapp.entry.card_title", "Подтвердите вход и продолжайте")}
              </h2>
              <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
                {getCopyText(
                  "webapp.entry.card_body",
                  "После подтверждения кабинет сразу вернет вас к статусу доступа, продлению, ключу подключения и службе заботы, без дополнительной настройки.",
                )}
              </p>

              <div className="mt-6 rounded-[24px] border border-emerald-900/8 bg-[#f8f5ef]/90 p-4 dark:border-emerald-200/10 dark:bg-[#0f1714]">
                <TelegramLoginWidget />
              </div>

              <div className="mt-6 flex flex-wrap gap-3">
                <AppRouteLink
                  href={BOT_WEBLOGIN_URL}
                  target="_blank"
                  hardNavigate={false}
                  className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
                >
                  {getCopyText("webapp.entry.primary_cta", "Открыть Telegram")}
                </AppRouteLink>
                <button
                  className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
                  onClick={() => logoutWebSession()}
                  type="button"
                >
                  {getCopyText("webapp.entry.secondary_cta", "Сменить аккаунт")}
                </button>
              </div>

              <div
                className="mt-5 rounded-[22px] border border-emerald-900/8 bg-emerald-900/[0.03] px-4 py-3 text-sm leading-6 text-slate-600 dark:border-emerald-200/10 dark:bg-emerald-200/[0.04] dark:text-slate-300"
                aria-live="polite"
              >
                <div className="flex items-start gap-3">
                  <span className="mt-0.5 inline-flex h-8 w-8 items-center justify-center rounded-full bg-white text-emerald-800 shadow-sm dark:bg-white/10 dark:text-emerald-200">
                    <span className="material-symbols-rounded text-[18px]">
                      {webLoginBusy ? "progress_activity" : webLoginError ? "priority_high" : "verified_user"}
                    </span>
                  </span>
                  <p>
                    {webLoginBusy
                      ? "Проверяем подтверждение входа и готовим возврат в кабинет."
                      : webLoginError
                        ? webLoginError
                        : "Если Telegram уже открыт на этом устройстве, подтверждение обычно занимает один спокойный шаг."}
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-4 grid gap-3">
              {ENTRY_PILLARS.map((item) => (
                <div
                  key={item.title}
                  className="flex items-start gap-3 rounded-[24px] border border-white/70 bg-white/68 px-4 py-4 dark:border-white/10 dark:bg-white/[0.04]"
                >
                  <span className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-emerald-900/8 text-emerald-800 dark:bg-emerald-200/10 dark:text-emerald-200">
                    <span className="material-symbols-rounded text-[20px]">{item.icon}</span>
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-slate-50">{item.title}</p>
                    <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.text}</p>
                  </div>
                </div>
              ))}
            </div>
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
