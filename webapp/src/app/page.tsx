"use client";

import AppRouteLink from "@/components/app-route-link";
import CabinetEntryAuth from "@/components/cabinet-entry-auth";
import { Button } from "@/components/ui/button";
import { SkeletonBlock, SkeletonLine, SkeletonRegion } from "@/components/ui/skeleton";
import { getCopyText } from "@/lib/portal";
import { PortalSessionProvider, usePortalSession } from "@/lib/session";
import { useEffect } from "react";

import { pokrovBranding } from "./branding";
import PokrovLogo from "./pokrov-logo";

function EntryPanel({ children }: { children: React.ReactNode }) {
  return (
    <main className="relative mx-auto flex min-h-[100dvh] w-full max-w-[760px] items-center px-4 py-6 sm:px-6">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top_right,var(--pokrov-status-success-bg),transparent_50%)]" />
      <section className="w-full rounded-panel border border-line bg-surface p-5 shadow-medium sm:p-7">{children}</section>
    </main>
  );
}

function EntrySkeleton() {
  return (
    <EntryPanel>
      <SkeletonRegion label="Открываем кабинет POKROV">
        <p className="text-sm font-semibold text-ink-soft">Открываем кабинет — проверяем сессию.</p>
        <SkeletonLine className="h-12 w-52" />
        <SkeletonLine className="h-10 w-60" />
        <SkeletonBlock className="h-12 w-full" />
        <SkeletonBlock className="h-40 w-full" />
      </SkeletonRegion>
    </EntryPanel>
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
    return <EntrySkeleton />;
  }

  if (error) {
    return (
      <EntryPanel>
        <PokrovLogo
          showWordmark
          className="inline-flex items-center gap-3"
          markClassName="h-12 w-12 rounded-full bg-canvas-alt p-2.5 ring-1 ring-line"
          caption={pokrovBranding.cabinetName}
          label="POKROV cabinet"
        />
        <div className="mt-6">
          <p className="text-[11px] font-semibold tracking-[0.18em] text-danger-text uppercase">Нужен повторный вход</p>
          <h1 className="mt-2 font-display text-[clamp(2rem,5vw,3rem)] leading-[0.98] font-semibold tracking-[-0.03em] text-ink">
            Не удалось открыть кабинет
          </h1>
          <p className="mt-3 text-sm leading-7 text-ink-soft">{error}</p>
        </div>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button onClick={() => void refresh()}>Повторить</Button>
          <Button variant="secondary" onClick={logoutWebSession}>Сменить аккаунт</Button>
          <Button variant="secondary" href="/support/">Поддержка</Button>
        </div>
      </EntryPanel>
    );
  }

  return (
    <EntryPanel>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <PokrovLogo
          showWordmark
          className="inline-flex items-center gap-3"
          markClassName="h-12 w-12 rounded-full bg-canvas-alt p-2.5 shadow-sm ring-1 ring-line"
          caption={pokrovBranding.cabinetName}
          label="POKROV cabinet"
        />
        <AppRouteLink
          href={pokrovBranding.marketingUrl}
          hardNavigate
          className="rounded-full bg-canvas-alt px-4 py-2 text-xs font-semibold text-ink-soft transition-colors hover:bg-nav-hover hover:text-ink motion-reduce:transition-none"
        >
          На сайт
        </AppRouteLink>
      </div>

      <div className="mt-8">
        <h1 className="font-display text-[clamp(2.15rem,7vw,3.2rem)] leading-[1.02] font-semibold tracking-[-0.02em] text-ink">
          {getCopyText("webapp.entry.title", "Кабинет POKROV")}
        </h1>
        <p className="mt-2 text-[15px] leading-relaxed text-ink-soft">
          {getCopyText("webapp.entry.subtitle", "Войдите, чтобы скачать приложение, проверить доступ, продлить срок или написать в поддержку.")}
        </p>
      </div>

      <div className="mt-7">
        <CabinetEntryAuth siteUrl={pokrovBranding.marketingUrl} />
      </div>
    </EntryPanel>
  );
}

export default function Page() {
  return (
    <PortalSessionProvider mode="entry">
      <EntryBody />
    </PortalSessionProvider>
  );
}
