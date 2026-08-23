"use client";

import { useCallback, useEffect, useState } from "react";

import { CommandPalette } from "@/components/ops/command-palette";
import {
  MobileNavigation,
  MobilePrimaryNavigation
} from "@/components/ops/mobile-navigation";
import { OpsDesktopNavigation } from "@/components/ops/navigation";
import { EMPTY_OPS_SHELL_STATUS, type OpsShellStatus } from "@/components/ops/shell-status";
import { OpsTopbar } from "@/components/ops/topbar";
import { OpsDashboard } from "@/components/ops-dashboard";
import type { OperatorShellIdentity } from "@/lib/admin-api/identity";
import {
  RouteRefreshProvider,
  useRouteRefreshControls
} from "@/lib/route-refresh";
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

function OpsWorkspaceFrame({
  active,
  sectionLabel,
  status,
  identity,
  onNavigate,
  onShellStatus,
  onIdentity,
  onOpenCommands,
  onOpenNavigation
}: {
  active: OpsSectionId;
  sectionLabel: string;
  status: OpsShellStatus;
  identity: OperatorShellIdentity | null;
  onNavigate: (href: string) => void;
  onShellStatus: (status: OpsShellStatus) => void;
  onIdentity: (identity: OperatorShellIdentity | null) => void;
  onOpenCommands: () => void;
  onOpenNavigation: () => void;
}) {
  const { canRefresh, refresh } = useRouteRefreshControls();

  return (
    <>
      <OpsTopbar
        sectionLabel={sectionLabel}
        status={status}
        identity={identity}
        canRefresh={canRefresh}
        onOpenCommands={onOpenCommands}
        onOpenNavigation={onOpenNavigation}
        onRefresh={refresh}
      />
      <div className="flex min-w-0">
        <OpsDesktopNavigation active={active} onNavigate={onNavigate} />
        <main id="ops-main-content" tabIndex={-1} className="min-w-0 flex-1 px-3 pb-20 pt-3 outline-none sm:px-4 md:pb-4 lg:px-5 lg:py-4">
          <div className="mx-auto max-w-[1800px]">
            <OpsDashboard
              section={active}
              identity={identity}
              onShellStatus={onShellStatus}
              onIdentity={onIdentity}
              onNavigate={onNavigate}
            />
          </div>
        </main>
      </div>
    </>
  );
}

export function OpsShell({ section }: { section: string }) {
  const [active, setActive] = useState<OpsSectionId>(() => normalizeOpsSection(section));
  const [commandsOpen, setCommandsOpen] = useState(false);
  const [mobileNavigationOpen, setMobileNavigationOpen] = useState(false);
  const [shellStatus, setShellStatus] = useState<OpsShellStatus>(EMPTY_OPS_SHELL_STATUS);
  const [identity, setIdentity] = useState<OperatorShellIdentity | null>(null);

  const changeCommandsOpen = useCallback((open: boolean) => {
    if (open) setMobileNavigationOpen(false);
    setCommandsOpen(open);
  }, []);

  const changeMobileNavigationOpen = useCallback((open: boolean) => {
    if (open) setCommandsOpen(false);
    setMobileNavigationOpen(open);
  }, []);

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
      changeCommandsOpen(true);
    };
    window.addEventListener("keydown", openCommands);
    return () => window.removeEventListener("keydown", openCommands);
  }, [changeCommandsOpen]);

  const navigate = useCallback((href: string) => {
    const canonical = canonicalRouteHref(href);
    if (!canonical) return;
    window.history.pushState({ pokrovAdminSection: canonical.section }, "", canonical.href);
    window.dispatchEvent(new Event(URL_STATE_CHANGE_EVENT));
    setActive(canonical.section);
  }, []);

  const activeSection = opsSectionFromPath(`/${active === "dashboard" ? "" : active}`);

  return (
    <div className="min-h-dvh bg-[color:var(--atlas-canvas-alt)] text-[color:var(--atlas-text)]">
      <a
        href="#ops-main-content"
        className="fixed left-3 top-3 z-[110] -translate-y-24 rounded-[var(--pokrov-radius-control)] bg-[color:var(--atlas-primary)] px-4 py-2 text-sm font-semibold text-[color:var(--atlas-primary-text)] transition-transform focus:translate-y-0"
      >
        К основному содержанию
      </a>
      <RouteRefreshProvider scope={active}>
        <OpsWorkspaceFrame
          active={active}
          sectionLabel={activeSection.label}
          status={shellStatus}
          identity={identity}
          onNavigate={navigate}
          onShellStatus={setShellStatus}
          onIdentity={setIdentity}
          onOpenCommands={() => changeCommandsOpen(true)}
          onOpenNavigation={() => changeMobileNavigationOpen(true)}
        />
      </RouteRefreshProvider>

      <MobileNavigation
        open={mobileNavigationOpen}
        active={active}
        onOpenChange={changeMobileNavigationOpen}
        onNavigate={navigate}
      />
      <MobilePrimaryNavigation
        active={active}
        onNavigate={navigate}
        onOpenMore={() => changeMobileNavigationOpen(true)}
      />
      {commandsOpen ? <CommandPalette open onOpenChange={changeCommandsOpen} onNavigate={navigate} /> : null}
    </div>
  );
}
