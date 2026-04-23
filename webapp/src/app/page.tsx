"use client";

import AppRouteLink from "@/components/app-route-link";
import CabinetEntryAuth from "@/components/cabinet-entry-auth";
import { PortalSessionProvider, usePortalSession } from "@/lib/session";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { pokrovBranding } from "./branding";
import PokrovLogo from "./pokrov-logo";

const ENTRY_STEPS = [
  "Проверить, всё ли в порядке со сроком и доступом.",
  "Открыть тарифы, загрузки или поддержку без нового старта.",
  "Вернуться к своим устройствам и продолжить тем же профилем.",
] as const;

function EntryBody() {
  const router = useRouter();
  const { loading, error, webLoginRequired, refresh, logoutWebSession } = usePortalSession();

  useEffect(() => {
    if (!loading && !webLoginRequired) {
      router.replace("/dashboard/");
    }
  }, [loading, router, webLoginRequired]);

  if (loading) {
    return (
      <main className="mx-auto flex min-h-[100dvh] w-full max-w-[1180px] items-center px-4 py-8 sm:px-6">
        <section className="grid w-full gap-5 rounded-[2rem] border border-slate-200/80 bg-white/94 p-6 shadow-[0_28px_80px_-54px_rgba(15,23,42,0.22)] dark:border-white/10 dark:bg-[#101713]/92 lg:grid-cols-[1.02fr_0.98fr] lg:p-8">
          <div className="space-y-5">
            <div className="h-12 w-52 animate-pulse rounded-2xl bg-slate-200 dark:bg-slate-800" />
            <div className="h-4 w-28 animate-pulse rounded-full bg-slate-200 dark:bg-slate-800" />
            <div className="h-14 w-full max-w-2xl animate-pulse rounded-[1.4rem] bg-slate-200 dark:bg-slate-800" />
            <div className="h-20 w-full max-w-2xl animate-pulse rounded-[1.4rem] bg-slate-200 dark:bg-slate-800" />
          </div>
          <div className="rounded-[1.7rem] border border-slate-200/80 bg-slate-50/90 p-5 dark:border-white/10 dark:bg-white/[0.04]">
            <div className="h-4 w-32 animate-pulse rounded-full bg-slate-200 dark:bg-slate-800" />
            <div className="mt-4 h-11 w-full animate-pulse rounded-2xl bg-slate-200 dark:bg-slate-800" />
            <div className="mt-4 h-28 w-full animate-pulse rounded-[1.4rem] bg-slate-200 dark:bg-slate-800" />
          </div>
        </section>
      </main>
    );
  }

  if (error) {
    return (
      <main className="mx-auto flex min-h-[100dvh] w-full max-w-[880px] items-center px-4 py-8 sm:px-6">
        <section className="w-full rounded-[2rem] border border-slate-200/80 bg-white/94 p-6 shadow-[0_28px_80px_-54px_rgba(15,23,42,0.22)] dark:border-white/10 dark:bg-[#101713]/92 sm:p-8">
          <PokrovLogo
            showWordmark
            className="inline-flex items-center gap-3"
            markClassName="h-12 w-12 rounded-[18px] bg-white/90 p-2.5 ring-1 ring-emerald-900/10 dark:bg-white/[0.08] dark:ring-white/10"
            caption={pokrovBranding.cabinetName}
            label="POKROV cabinet"
          />
          <p className="mt-6 text-[11px] font-semibold uppercase tracking-[0.18em] text-rose-600 dark:text-rose-300">
            Нужно повторить вход
          </p>
          <h1 className="mt-2 font-display text-[clamp(2rem,5vw,3rem)] font-semibold leading-[0.98] tracking-[-0.04em] text-slate-950 dark:text-slate-50">
            Кабинет сейчас не открылся
          </h1>
          <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">{error}</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => void refresh()}
              className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
            >
              Повторить
            </button>
            <button
              type="button"
              onClick={logoutWebSession}
              className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
            >
              Сменить аккаунт
            </button>
            <AppRouteLink
              href={pokrovBranding.marketingUrl}
              hardNavigate
              className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
            >
              {pokrovBranding.siteLinkLabel}
            </AppRouteLink>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="relative mx-auto flex min-h-[100dvh] w-full max-w-[1240px] items-center px-4 py-8 sm:px-6">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(11,72,50,0.05),_transparent_30%),radial-gradient(circle_at_bottom_right,_rgba(197,138,42,0.05),_transparent_28%)]" />
      <section className="grid w-full gap-5 rounded-[2rem] border border-slate-200/80 bg-white/94 p-6 shadow-[0_28px_80px_-54px_rgba(15,23,42,0.22)] dark:border-white/10 dark:bg-[#101713]/92 lg:grid-cols-[1.02fr_0.98fr] lg:p-8">
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <PokrovLogo
              showWordmark
              className="inline-flex items-center gap-3"
              markClassName="h-12 w-12 rounded-[18px] bg-white/90 p-2.5 ring-1 ring-emerald-900/10 dark:bg-white/[0.08] dark:ring-white/10"
              caption={pokrovBranding.cabinetName}
              label="POKROV cabinet"
            />
            <AppRouteLink
              href={pokrovBranding.marketingUrl}
              hardNavigate
              className="outline-btn rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em]"
            >
              {pokrovBranding.siteLinkLabel}
            </AppRouteLink>
          </div>

          <div className="space-y-3">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
              {pokrovBranding.entryEyebrow}
            </p>
            <h1 className="font-display text-[clamp(2.2rem,5vw,4rem)] font-semibold leading-[0.94] tracking-[-0.05em] text-slate-950 dark:text-slate-50">
              Здесь только статус, оплата и поддержка
            </h1>
            <p className="max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
              Основной путь остаётся в приложении POKROV. Кабинет в браузере нужен рядом: посмотреть срок, открыть загрузки,
              продлить доступ и быстро написать в поддержку, если что-то пошло не так.
            </p>
          </div>

          <div className="rounded-[1.7rem] border border-emerald-200/70 bg-emerald-50/90 p-5 dark:border-emerald-400/20 dark:bg-emerald-400/10">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-800 dark:text-emerald-200">
              Спокойный сценарий
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">
              Подключение и выбор режима по-прежнему живут в приложении. Кабинет не подменяет его, а просто продолжает историю:
              статус, срок, устройства, загрузки и поддержка в одном месте.
            </p>
          </div>

          <div className="rounded-[1.7rem] border border-slate-200/80 bg-slate-50/90 p-5 dark:border-white/10 dark:bg-white/[0.04]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
              Что можно сделать здесь
            </p>
            <ul className="mt-4 space-y-3">
              {ENTRY_STEPS.map((step) => (
                <li key={step} className="flex items-start gap-3 text-sm leading-6 text-slate-700 dark:text-slate-200">
                  <span className="mt-2 h-2 w-2 rounded-full bg-emerald-700 dark:bg-emerald-400" />
                  <span>{step}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="rounded-[1.8rem] border border-slate-200/80 bg-[#fbfaf7]/95 p-5 dark:border-white/10 dark:bg-[#0f1714]/92 sm:p-6">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
            Вход в браузере
          </p>
          <h2 className="mt-2 font-display text-[2rem] font-semibold leading-[0.96] tracking-[-0.04em] text-slate-950 dark:text-slate-50">
            Подтвердите вход и продолжайте
          </h2>
          <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
            Telegram уже работает. Email-вход скоро подключим, а пока вход и восстановление держим через Telegram, чтобы не
            обещать то, чего ещё нет на бэке.
          </p>
          <div className="mt-6">
            <CabinetEntryAuth siteUrl={pokrovBranding.marketingUrl} />
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
