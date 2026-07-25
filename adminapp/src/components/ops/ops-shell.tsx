"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { CommandPalette } from "@/components/ops/command-palette";
import { MobileNavigation } from "@/components/ops/mobile-navigation";
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
  const routeContentRef = useRef<HTMLDivElement>(null);

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

  const refresh = useCallback(() => {
    const refreshControl = Array.from(routeContentRef.current?.querySelectorAll("button") ?? []).find(
      (button) => button.textContent?.trim() === "Обновить"
    );
    if (refreshControl && !refreshControl.disabled) {
      refreshControl.click();
      return;
    }
    window.location.reload();
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
      <div>
        <OpsTopbar
          sectionLabel={activeSection.label}
          active={active}
          status={shellStatus}
          onNavigate={navigate}
          onOpenCommands={() => changeCommandsOpen(true)}
          onOpenNavigation={() => changeMobileNavigationOpen(true)}
          onRefresh={refresh}
        />
        <main id="ops-main-content" tabIndex={-1} className="px-3 py-3 outline-none sm:px-4 lg:px-5 lg:py-4">
          <div ref={routeContentRef} className="mx-auto max-w-[1800px]">
            <OpsDashboard section={active} onShellStatus={setShellStatus} onNavigate={navigate} />
          </div>
        </main>
      </div>

      <MobileNavigation
        open={mobileNavigationOpen}
        active={active}
        onOpenChange={changeMobileNavigationOpen}
        onNavigate={navigate}
      />
      {commandsOpen ? <CommandPalette open onOpenChange={changeCommandsOpen} onNavigate={navigate} /> : null}
    </div>
  );
}
