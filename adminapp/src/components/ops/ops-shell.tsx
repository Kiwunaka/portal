"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { CommandPalette } from "@/components/ops/command-palette";
import { MobileNavigation } from "@/components/ops/mobile-navigation";
import { OpsNavigation } from "@/components/ops/navigation";
import { EMPTY_OPS_SHELL_STATUS, type OpsShellStatus } from "@/components/ops/shell-status";
import { OpsTopbar } from "@/components/ops/topbar";
import { OpsDashboard } from "@/components/ops-dashboard";
import { opsSectionFromPath, normalizeOpsSection, type OpsSectionId } from "@/lib/sections";
import { URL_STATE_CHANGE_EVENT } from "@/lib/url-state";

function canonicalRouteHref(href: string): { href: string; section: OpsSectionId } | null {
  if (typeof window === "undefined" || !href.startsWith("/") || href.startsWith("//")) return null;
  const url = new URL(href, window.location.origin);
  if (url.origin !== window.location.origin) return null;
  const route = opsSectionFromPath(url.pathname);
  const pathname = url.pathname === "/" ? "/" : url.pathname.replace(/\/+$/, "");
  if (route.href !== pathname) return null;
  return { href: `${route.href}${url.search}`, section: route.id };
}

export function OpsShell({ section }: { section: string }) {
  const [active, setActive] = useState<OpsSectionId>(() => normalizeOpsSection(section));
  const [commandsOpen, setCommandsOpen] = useState(false);
  const [mobileNavigationOpen, setMobileNavigationOpen] = useState(false);
  const [shellStatus, setShellStatus] = useState<OpsShellStatus>(EMPTY_OPS_SHELL_STATUS);
  const legacyDashboardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const syncFromHistory = () => {
      setActive(opsSectionFromPath(window.location.pathname).id);
      setCommandsOpen(false);
      setMobileNavigationOpen(false);
    };

    const route = opsSectionFromPath(window.location.pathname);
    const currentPath = window.location.pathname === "/" ? "/" : window.location.pathname.replace(/\/+$/, "");
    if (currentPath !== route.href || window.location.pathname !== currentPath) {
      window.history.replaceState(window.history.state, "", `${route.href}${window.location.search}${window.location.hash}`);
    }
    syncFromHistory();
    window.addEventListener("popstate", syncFromHistory);
    return () => window.removeEventListener("popstate", syncFromHistory);
  }, []);

  useEffect(() => {
    const openCommands = (event: KeyboardEvent) => {
      if (event.defaultPrevented || event.altKey || event.shiftKey) return;
      if (!event.ctrlKey || event.metaKey || event.key.toLowerCase() !== "k") return;
      event.preventDefault();
      setCommandsOpen(true);
    };
    window.addEventListener("keydown", openCommands);
    return () => window.removeEventListener("keydown", openCommands);
  }, []);

  const navigate = useCallback((href: string) => {
    const canonical = canonicalRouteHref(href);
    if (!canonical) return;
    window.history.pushState({ pokrovAdminSection: canonical.section }, "", canonical.href);
    window.dispatchEvent(new Event(URL_STATE_CHANGE_EVENT));
    setActive(canonical.section);
  }, []);

  const refresh = useCallback(() => {
    const legacyRefresh = Array.from(legacyDashboardRef.current?.querySelectorAll("button") ?? []).find(
      (button) => button.textContent?.trim() === "Обновить"
    );
    if (legacyRefresh && !legacyRefresh.disabled) {
      legacyRefresh.click();
      return;
    }
    window.location.reload();
  }, []);

  const activeSection = opsSectionFromPath(`/${active === "dashboard" ? "" : active}`);

  return (
    <div className="min-h-screen bg-[color:var(--atlas-canvas-alt)] text-[color:var(--atlas-text)]">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[248px] border-r border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] px-3 py-4 lg:block">
        <div className="mb-6 flex items-center gap-3 px-2">
          <div className="grid h-9 w-9 place-items-center rounded-[var(--pokrov-radius-card)] bg-[color:var(--atlas-primary)] text-sm font-bold text-[color:var(--atlas-primary-text)]">
            P
          </div>
          <div className="min-w-0">
            <div className="text-sm font-semibold leading-tight">POKROV</div>
            <div className="text-[11px] text-[color:var(--atlas-text-muted)]">Центр управления</div>
          </div>
        </div>
        <OpsNavigation active={active} onNavigate={navigate} className="max-h-[calc(100vh-88px)] pr-1" />
      </aside>

      <div className="lg:pl-[248px]">
        <OpsTopbar
          sectionLabel={activeSection.label}
          status={shellStatus}
          onOpenCommands={() => setCommandsOpen(true)}
          onOpenNavigation={() => setMobileNavigationOpen(true)}
          onRefresh={refresh}
        />
        <main className="px-4 py-4 lg:px-6 lg:py-5">
          <div ref={legacyDashboardRef} className="[&>.space-y-4>div:first-child]:hidden">
            <OpsDashboard section={active} onShellStatus={setShellStatus} />
          </div>
        </main>
      </div>

      <MobileNavigation
        open={mobileNavigationOpen}
        active={active}
        onOpenChange={setMobileNavigationOpen}
        onNavigate={navigate}
      />
      {commandsOpen ? <CommandPalette open onOpenChange={setCommandsOpen} onNavigate={navigate} /> : null}
    </div>
  );
}
