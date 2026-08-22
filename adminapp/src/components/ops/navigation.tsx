"use client";

import {
  Activity,
  Bell,
  ClipboardList,
  CreditCard,
  Dices,
  FileCheck2,
  Gauge,
  Gift,
  Headphones,
  LayoutDashboard,
  KeyRound,
  LineChart,
  Megaphone,
  Network,
  Newspaper,
  Radio,
  Rocket,
  Server,
  Share2,
  Shield,
  ShieldAlert,
  Siren,
  Ticket,
  TrendingUp,
  Users,
  WalletCards,
  Wifi,
  type LucideIcon
} from "lucide-react";
import type { MouseEvent } from "react";

import { cn } from "@/components/utils";
import {
  OPS_WORKSPACES,
  opsWorkspaceForSection,
  type OpsSectionId,
  type OpsWorkspaceId
} from "@/lib/sections";

export const SECTION_ICONS: Record<OpsSectionId, LucideIcon> = {
  shift: ClipboardList,
  support: Headphones,
  network: Network,
  money: WalletCards,
  growth: TrendingUp,
  releases: Rocket,
  governance: Shield,
  dashboard: LayoutDashboard,
  nodes: Server,
  traffic: Activity,
  alerts: Bell,
  incidents: Siren,
  "provider-caps": Gauge,
  "emergency-network": ShieldAlert,
  "free-tier": Gift,
  access: KeyRound,
  users: Users,
  online: Wifi,
  tickets: Ticket,
  payments: CreditCard,
  funnel: LineChart,
  bonuses: Dices,
  programs: FileCheck2,
  promos: Megaphone,
  referrals: Share2,
  release: Rocket,
  broadcast: Radio,
  news: Newspaper
};

export interface OpsNavigationProps {
  active: OpsSectionId;
  onNavigate: (href: string) => void;
  className?: string;
  label?: string;
}

export type OpsDesktopNavigationProps = Pick<OpsNavigationProps, "active" | "onNavigate">;

function isPlainPrimaryClick(event: MouseEvent<HTMLAnchorElement>): boolean {
  return event.button === 0 && !event.metaKey && !event.altKey && !event.ctrlKey && !event.shiftKey;
}

function navigationClick(event: MouseEvent<HTMLAnchorElement>, href: string, onNavigate: (href: string) => void) {
  if (event.defaultPrevented || !isPlainPrimaryClick(event)) return;
  event.preventDefault();
  onNavigate(href);
}

export function OpsNavigation({
  active,
  onNavigate,
  className,
  label = "Рабочие области центра управления"
}: OpsNavigationProps) {
  const activeWorkspace = opsWorkspaceForSection(active).id;

  return (
    <nav aria-label={label} className={cn("ops-scrollbar flex flex-col gap-5 overflow-y-auto", className)}>
      {OPS_WORKSPACES.map((workspace) => {
        const WorkspaceIcon = SECTION_ICONS[workspace.id];
        const workspaceActive = activeWorkspace === workspace.id;
        return (
          <section key={workspace.id} aria-labelledby={`ops-workspace-${workspace.id}`}>
            <a
              id={`ops-workspace-${workspace.id}`}
              href={workspace.href}
              aria-current={active === workspace.id ? "page" : undefined}
              onClick={(event) => navigationClick(event, workspace.href, onNavigate)}
              className={cn(
                "flex min-h-10 items-center gap-2 rounded-[var(--pokrov-radius-card)] px-3 text-sm font-semibold",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--atlas-focus)]",
                workspaceActive
                  ? "bg-[color:var(--pokrov-nav-active-bg)] text-[color:var(--atlas-text)]"
                  : "text-[color:var(--atlas-text-soft)] hover:bg-[color:var(--pokrov-nav-hover-bg)]"
              )}
            >
              <WorkspaceIcon aria-hidden="true" size={17} strokeWidth={1.85} />
              <span className="truncate">{workspace.label}</span>
            </a>
            {workspace.sections.length ? (
              <div className="mt-1 space-y-0.5 border-l border-[color:var(--atlas-border)] pl-3 ml-5">
                {workspace.sections.map((item) => {
                  const Icon = SECTION_ICONS[item.id];
                  const selected = active === item.id;
                  return (
                    <a
                      key={item.id}
                      href={item.href}
                      aria-current={selected ? "page" : undefined}
                      onClick={(event) => navigationClick(event, item.href, onNavigate)}
                      className={cn(
                        "flex min-h-9 items-center gap-2 rounded-[var(--pokrov-radius-card)] px-2.5 text-xs font-medium",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--atlas-focus)]",
                        selected
                          ? "bg-[color:var(--atlas-canvas-alt)] text-[color:var(--atlas-primary)]"
                          : "text-[color:var(--pokrov-nav-text)] hover:bg-[color:var(--pokrov-nav-hover-bg)]"
                      )}
                    >
                      <Icon aria-hidden="true" size={15} strokeWidth={1.8} />
                      <span className="truncate">{item.label}</span>
                    </a>
                  );
                })}
              </div>
            ) : null}
          </section>
        );
      })}
    </nav>
  );
}

export function OpsDesktopNavigation({ active, onNavigate }: OpsDesktopNavigationProps) {
  return (
    <aside className="hidden w-64 shrink-0 border-r border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] xl:block">
      <OpsNavigation
        active={active}
        onNavigate={onNavigate}
        className="sticky top-16 h-[calc(100dvh-4rem)] px-3 py-4"
      />
    </aside>
  );
}

export const MOBILE_PRIMARY_WORKSPACES: readonly OpsWorkspaceId[] = ["shift", "support", "network", "money"];
