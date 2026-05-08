"use client";

import AppRouteLink from "@/components/app-route-link";
import CabinetEntryAuth from "@/components/cabinet-entry-auth";
import { PortalSessionProvider, usePortalSession } from "@/lib/session";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { DoubleBezel } from "@/components/ui/double-bezel";
import { FadeUp } from "@/components/ui/fade-up";
import { Preloader } from "@/components/ui/preloader";

import { pokrovBranding } from "./branding";
import PokrovLogo from "./pokrov-logo";

const ENTRY_STEPS = [
  "Проверить срок доступа и быстро вернуться в рабочий кабинет.",
  "Открыть продление, загрузки, ключ доступа или поддержку без нового старта.",
  "Продолжить с тем же профилем, который уже связан с приложением POKROV.",
] as const;

function EntrySkeleton() {
  return (
    <main className="mx-auto flex min-h-[100dvh] w-full max-w-[1180px] items-center px-4 py-8 sm:px-6">
      <DoubleBezel className="w-full" innerClassName="grid gap-5 p-6 lg:grid-cols-[1.02fr_0.98fr] lg:p-8">
        <div className="space-y-8">
          <div className="h-12 w-52 animate-pulse rounded-2xl bg-slate-200 dark:bg-slate-800" />
          <div className="h-4 w-28 animate-pulse rounded-full bg-slate-200 dark:bg-slate-800" />
          <div className="h-14 w-full max-w-2xl animate-pulse rounded-[1.4rem] bg-slate-200 dark:bg-slate-800" />
          <div className="h-24 w-full max-w-2xl animate-pulse rounded-[1.4rem] bg-slate-200 dark:bg-slate-800" />
        </div>
        <div className="rounded-[1.7rem] bg-slate-50 p-5 dark:bg-white/[0.04]">
          <div className="h-4 w-32 animate-pulse rounded-full bg-slate-200 dark:bg-slate-800" />
          <div className="mt-4 h-11 w-full animate-pulse rounded-2xl bg-slate-200 dark:bg-slate-800" />
          <div className="mt-4 h-28 w-full animate-pulse rounded-[1.4rem] bg-slate-200 dark:bg-slate-800" />
        </div>
      </DoubleBezel>
    </main>
  );
}

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
      <>
        <Preloader />
        <EntrySkeleton />
      </>
    );
  }

  if (error) {
    return (
      <main className="mx-auto flex min-h-[100dvh] w-full max-w-[880px] items-center px-4 py-8 sm:px-6">
        <DoubleBezel tone="danger" className="w-full" innerClassName="p-6 sm:p-8">
          <FadeUp delay={0.1}>
            <PokrovLogo
              showWordmark
              className="inline-flex items-center gap-3"
              markClassName="h-12 w-12 rounded-full bg-white/90 p-2.5 ring-1 ring-emerald-900/10 dark:bg-white/[0.08] dark:ring-white/10"
              caption={pokrovBranding.cabinetName}
              label="POKROV cabinet"
            />
          </FadeUp>
          <FadeUp delay={0.2} className="mt-6">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-rose-600 dark:text-rose-300">
              Нужен повторный вход
            </p>
            <h1 className="mt-2 font-display text-[clamp(2rem,5vw,3rem)] font-semibold leading-[0.98] tracking-[-0.04em] text-slate-950 dark:text-slate-50">
              Кабинет сейчас не открылся
            </h1>
            <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
              {error}
            </p>
          </FadeUp>
          <FadeUp delay={0.3} className="mt-8 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => void refresh()}
              className="btn-primary rounded-2xl px-6 py-3.5 text-sm font-semibold uppercase tracking-[0.12em]"
            >
              Повторить
            </button>
            <button
              type="button"
              onClick={logoutWebSession}
              className="outline-btn rounded-2xl px-6 py-3.5 text-sm font-semibold uppercase tracking-[0.12em]"
            >
              Сменить аккаунт
            </button>
            <AppRouteLink
              href="/support/"
              className="outline-btn rounded-2xl px-6 py-3.5 text-sm font-semibold uppercase tracking-[0.12em]"
            >
              Поддержка
            </AppRouteLink>
          </FadeUp>
        </DoubleBezel>
      </main>
    );
  }

  return (
    <main className="relative mx-auto flex min-h-[100dvh] w-full max-w-[1240px] items-center px-4 py-8 sm:px-6">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top_right,rgba(209,250,229,0.3),transparent_50%)] dark:bg-[radial-gradient(ellipse_at_top_right,rgba(16,185,129,0.05),transparent_50%)]" />

      <DoubleBezel tone="glass" className="w-full" innerClassName="grid gap-5 p-6 lg:grid-cols-[1.05fr_0.95fr] lg:p-8">
        <div className="space-y-8 pr-0 lg:pr-8">
          <FadeUp delay={0.1} className="flex flex-wrap items-center justify-between gap-4">
            <PokrovLogo
              showWordmark
              className="inline-flex items-center gap-3"
              markClassName="h-12 w-12 rounded-full bg-white p-2.5 shadow-sm ring-1 ring-emerald-900/5 dark:bg-white/[0.04] dark:ring-white/10"
              caption={pokrovBranding.cabinetName}
              label="POKROV cabinet"
            />
            <AppRouteLink
              href={pokrovBranding.marketingUrl}
              hardNavigate
              className="rounded-full bg-black/5 px-5 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-600 transition-colors hover:bg-black/10 dark:bg-white/5 dark:text-slate-300 dark:hover:bg-white/10"
            >
              {pokrovBranding.siteLinkLabel}
            </AppRouteLink>
          </FadeUp>

          <FadeUp delay={0.2} className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 ring-1 ring-inset ring-emerald-200/50 dark:bg-emerald-500/10 dark:ring-emerald-400/20">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-800 dark:text-emerald-300">
                {pokrovBranding.entryEyebrow}
              </p>
            </div>
            <h1 className="font-display text-[clamp(2.5rem,6vw,4.5rem)] font-semibold leading-[0.92] tracking-[-0.04em] text-slate-950 dark:text-slate-50">
              Продолжите с того места, где остановились
            </h1>
            <p className="max-w-xl text-[15px] leading-relaxed text-slate-600 dark:text-slate-300">
              Это не вторая витрина POKROV. Здесь открывается личный кабинет: срок доступа, устройства,
              ключи доступа, загрузки и поддержка. Подключение и ежедневный выбор режима остаются в приложении.
            </p>
          </FadeUp>

          <FadeUp delay={0.3} className="grid gap-3 sm:grid-cols-3">
            {ENTRY_STEPS.map((step, index) => (
              <article
                key={step}
                className="group relative overflow-hidden rounded-[1.5rem] bg-slate-50/50 p-5 ring-1 ring-inset ring-slate-200/50 transition-colors hover:bg-emerald-50/50 hover:ring-emerald-200/50 dark:bg-white/[0.02] dark:ring-white/5 dark:hover:bg-emerald-500/5 dark:hover:ring-emerald-500/20"
              >
                <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-800/70 transition-colors group-hover:text-emerald-800 dark:text-emerald-400/70 dark:group-hover:text-emerald-400">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <p className="mt-3 text-sm leading-relaxed text-slate-700 dark:text-slate-300">{step}</p>
              </article>
            ))}
          </FadeUp>
        </div>

        <FadeUp delay={0.4} className="h-full">
          <div className="relative flex h-full flex-col justify-center overflow-hidden rounded-[2rem] bg-white p-6 shadow-[0_20px_60px_-20px_rgba(15,23,42,0.1)] ring-1 ring-slate-200/50 dark:bg-[#0a0f0d] dark:ring-white/10 sm:p-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
              Вход в браузере
            </p>
            <h2 className="mt-3 font-display text-[2.2rem] font-semibold leading-[1.05] tracking-[-0.03em] text-slate-950 dark:text-slate-50">
              Подтвердите аккаунт и продолжайте
            </h2>
            <p className="mt-4 text-[15px] leading-relaxed text-slate-600 dark:text-slate-300">
              Telegram остается самым быстрым путем подтверждения. Если email-доставка включена, рядом появится email-вход.
              Мы не просим заново знакомиться с продуктом: вход нужен только чтобы показать именно ваш доступ, обращения и устройства.
            </p>
            <div className="mt-8">
              <CabinetEntryAuth siteUrl={pokrovBranding.marketingUrl} />
            </div>

            <div className="mt-8 rounded-2xl bg-slate-50 p-4 dark:bg-white/[0.02]">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                Спокойная логика входа
              </p>
              <p className="mt-2 text-[13px] leading-relaxed text-slate-600 dark:text-slate-400">
                Если браузер уже знает вашу сессию, мы сразу переведем вас в кабинет. Email-вход показывается только по зеленому статусу доставки писем; если он недоступен, кабинет честно подскажет Telegram или поддержку.
              </p>
            </div>
          </div>
        </FadeUp>
      </DoubleBezel>
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
