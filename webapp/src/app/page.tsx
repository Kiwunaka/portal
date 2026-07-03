"use client";

import AppRouteLink from "@/components/app-route-link";
import CabinetEntryAuth from "@/components/cabinet-entry-auth";
import { getCopyText } from "@/lib/portal";
import { PortalSessionProvider, usePortalSession } from "@/lib/session";
import { useEffect } from "react";

import { DoubleBezel } from "@/components/ui/double-bezel";
import { Preloader } from "@/components/ui/preloader";

import { pokrovBranding } from "./branding";
import PokrovLogo from "./pokrov-logo";

function EntrySkeleton() {
  return (
    <main className="mx-auto flex min-h-[100dvh] w-full max-w-[760px] items-center px-4 py-6 sm:px-6">
      <DoubleBezel className="w-full" innerClassName="p-5 sm:p-7">
        <div className="space-y-8">
          <div className="h-12 w-52 animate-pulse rounded-2xl bg-[color:var(--atlas-border)]" />
          <div className="h-10 w-60 animate-pulse rounded-2xl bg-[color:var(--atlas-border)]" />
          <div className="h-12 w-full animate-pulse rounded-[1.4rem] bg-[color:var(--atlas-border)]" />
          <div className="h-40 w-full animate-pulse rounded-[1.4rem] bg-[color:var(--atlas-border)]" />
        </div>
      </DoubleBezel>
    </main>
  );
}

function EntryBody() {
  const { loading, error, webLoginRequired, refresh, logoutWebSession } = usePortalSession();

  useEffect(() => {
    if (!loading && !webLoginRequired) {
      window.location.replace("/dashboard/");
    }
  }, [loading, webLoginRequired]);

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
          <div>
            <PokrovLogo
              showWordmark
              className="inline-flex items-center gap-3"
              markClassName="h-12 w-12 rounded-full bg-[color:var(--atlas-surface)] p-2.5 ring-1 ring-[color:var(--atlas-border)]"
              caption={pokrovBranding.cabinetName}
              label="POKROV cabinet"
            />
          </div>
          <div className="mt-6">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--atlas-status-danger-text)]">
              Нужен повторный вход
            </p>
            <h1 className="mt-2 font-display text-[clamp(2rem,5vw,3rem)] font-semibold leading-[0.98] tracking-[-0.04em] text-[color:var(--atlas-text)]">
              Не удалось открыть кабинет
            </h1>
            <p className="mt-3 text-sm leading-7 text-[color:var(--atlas-text-soft)]">
              {error}
            </p>
          </div>
          <div className="mt-8 flex flex-wrap gap-3">
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
          </div>
        </DoubleBezel>
      </main>
    );
  }

  return (
    <main className="relative mx-auto flex min-h-[100dvh] w-full max-w-[760px] items-center px-4 py-6 sm:px-6">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top_right,var(--atlas-status-success-bg),transparent_50%)]" />

      <DoubleBezel tone="glass" className="w-full" innerClassName="p-5 sm:p-7">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <PokrovLogo
            showWordmark
            className="inline-flex items-center gap-3"
            markClassName="h-12 w-12 rounded-full bg-[color:var(--atlas-surface)] p-2.5 shadow-sm ring-1 ring-[color:var(--atlas-border)]"
            caption={pokrovBranding.cabinetName}
            label="POKROV cabinet"
          />
          <AppRouteLink
            href={pokrovBranding.marketingUrl}
            hardNavigate
            className="rounded-full bg-[color:var(--atlas-canvas-alt)] px-4 py-2 text-xs font-semibold text-[color:var(--atlas-text-soft)] transition-colors hover:bg-[color:var(--atlas-border)]"
          >
            На сайт
          </AppRouteLink>
        </div>

        <div className="mt-8">
          <h1 className="font-display text-[clamp(2.15rem,7vw,3.2rem)] font-semibold leading-[1.02] text-[color:var(--atlas-text)]">
            {getCopyText("webapp.entry.title", "Кабинет POKROV")}
          </h1>
          <p className="mt-2 text-[15px] leading-relaxed text-[color:var(--atlas-text-soft)]">
            {getCopyText("webapp.entry.subtitle", "Войдите, чтобы скачать приложение, проверить доступ, продлить срок или написать в поддержку.")}
          </p>
        </div>

        <div className="mt-7">
          <CabinetEntryAuth siteUrl={pokrovBranding.marketingUrl} />
        </div>
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
