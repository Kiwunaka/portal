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

function EntrySkeleton() {
  return (
    <main className="mx-auto flex min-h-[100dvh] w-full max-w-[760px] items-center px-4 py-6 sm:px-6">
      <DoubleBezel className="w-full" innerClassName="p-5 sm:p-7">
        <div className="space-y-8">
          <div className="h-12 w-52 animate-pulse rounded-2xl bg-slate-200 dark:bg-slate-800" />
          <div className="h-10 w-60 animate-pulse rounded-2xl bg-slate-200 dark:bg-slate-800" />
          <div className="h-12 w-full animate-pulse rounded-[1.4rem] bg-slate-200 dark:bg-slate-800" />
          <div className="h-40 w-full animate-pulse rounded-[1.4rem] bg-slate-200 dark:bg-slate-800" />
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
    <main className="relative mx-auto flex min-h-[100dvh] w-full max-w-[760px] items-center px-4 py-6 sm:px-6">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top_right,rgba(209,250,229,0.3),transparent_50%)] dark:bg-[radial-gradient(ellipse_at_top_right,rgba(16,185,129,0.05),transparent_50%)]" />

      <DoubleBezel tone="glass" className="w-full" innerClassName="p-5 sm:p-7">
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
            className="rounded-full bg-black/5 px-4 py-2 text-xs font-semibold text-slate-600 transition-colors hover:bg-black/10 dark:bg-white/5 dark:text-slate-300 dark:hover:bg-white/10"
          >
            На сайт
          </AppRouteLink>
        </FadeUp>

        <FadeUp delay={0.2} className="mt-8">
          <h1 className="font-display text-[clamp(2.15rem,7vw,3.2rem)] font-semibold leading-[1.02] text-slate-950 dark:text-slate-50">
            Вход в аккаунт
          </h1>
          <p className="mt-2 text-[15px] leading-relaxed text-slate-600 dark:text-slate-300">
            Доступ, устройства, оплата и поддержка.
          </p>
        </FadeUp>

        <FadeUp delay={0.3} className="mt-7">
          <CabinetEntryAuth siteUrl={pokrovBranding.marketingUrl} />
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
