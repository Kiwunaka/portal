"use client";

import {
  Activity,
  Bell,
  CreditCard,
  Gauge,
  Gift,
  LayoutDashboard,
  LineChart,
  Megaphone,
  Radio,
  Rocket,
  Server,
  Share2,
  Ticket,
  Users,
  Wifi,
  type LucideIcon
} from "lucide-react";
import type { MouseEvent } from "react";

import { cn } from "@/components/utils";
import { OPS_GROUPS, type OpsSectionId } from "@/lib/sections";

const SECTION_ICONS: Record<OpsSectionId, LucideIcon> = {
  dashboard: LayoutDashboard,
  nodes: Server,
  traffic: Activity,
  alerts: Bell,
  "provider-caps": Gauge,
  "free-tier": Gift,
  users: Users,
  online: Wifi,
  tickets: Ticket,
  payments: CreditCard,
  funnel: LineChart,
  promos: Megaphone,
  referrals: Share2,
  release: Rocket,
  broadcast: Radio
};

export interface OpsNavigationProps {
  active: OpsSectionId;
  onNavigate: (href: string) => void;
  className?: string;
  label?: string;
}

function isPlainPrimaryClick(event: MouseEvent<HTMLAnchorElement>): boolean {
  return event.button === 0 && !event.metaKey && !event.altKey && !event.ctrlKey && !event.shiftKey;
}

export function OpsNavigation({ active, onNavigate, className, label = "Разделы центра управления" }: OpsNavigationProps) {
  return (
    <nav aria-label={label} className={cn("ops-scrollbar flex flex-col gap-5 overflow-y-auto", className)}>
      {OPS_GROUPS.map((group) => (
        <section key={group.label} aria-labelledby={`ops-group-${group.sections[0].id}`}>
          <h2
            id={`ops-group-${group.sections[0].id}`}
            className="mb-1.5 px-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-[color:var(--atlas-text-muted)]"
          >
            {group.label}
          </h2>
          <div className="space-y-1">
            {group.sections.map((item) => {
              const Icon = SECTION_ICONS[item.id];
              const selected = active === item.id;
              return (
                <a
                  key={item.id}
                  href={item.href}
                  aria-current={selected ? "page" : undefined}
                  onClick={(event) => {
                    if (event.defaultPrevented || !isPlainPrimaryClick(event)) return;
                    event.preventDefault();
                    onNavigate(item.href);
                  }}
                  className={cn(
                    "flex min-h-[var(--pokrov-nav-item-min-height)] items-center gap-2 rounded-[var(--pokrov-radius-card)] px-3 text-sm font-medium transition-colors",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--atlas-focus)] focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--atlas-surface)]",
                    selected
                      ? "bg-[color:var(--pokrov-nav-active-bg)] text-[color:var(--atlas-text)]"
                      : "text-[color:var(--pokrov-nav-text)] hover:bg-[color:var(--pokrov-nav-hover-bg)]"
                  )}
                >
                  <Icon aria-hidden="true" size={17} strokeWidth={1.85} />
                  <span className="truncate">{item.label}</span>
                </a>
              );
            })}
          </div>
        </section>
      ))}
    </nav>
  );
}
