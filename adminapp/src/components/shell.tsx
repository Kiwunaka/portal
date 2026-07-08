"use client";

import { useCallback, useEffect, useState, type FormEvent, type MouseEvent } from "react";
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
  Search,
  Server,
  Share2,
  ShieldCheck,
  Ticket,
  Users,
  Wifi,
  type LucideIcon
} from "lucide-react";

import { OpsDashboard } from "@/components/ops-dashboard";
import { cn } from "@/components/utils";
import { OPS_SECTIONS, normalizeOpsSection, type OpsSectionId } from "@/lib/sections";

const icons: Record<OpsSectionId, LucideIcon> = {
  dashboard: LayoutDashboard,
  online: Wifi,
  nodes: Server,
  traffic: Activity,
  "free-tier": Gift,
  "provider-caps": Gauge,
  alerts: Bell,
  users: Users,
  tickets: Ticket,
  payments: CreditCard,
  promos: Megaphone,
  referrals: Share2,
  release: Rocket,
  broadcast: Radio,
  funnel: LineChart
};

const sectionMap = new Map(OPS_SECTIONS.map((item) => [item.id, item]));

function sectionFromPath(pathname: string): OpsSectionId {
  const raw = pathname.replace(/^\/+|\/+$/g, "");
  return normalizeOpsSection(raw || "dashboard");
}

export function OpsShell({ section }: { section: string }) {
  const [active, setActive] = useState<OpsSectionId>(() => normalizeOpsSection(section));
  const [globalSearch, setGlobalSearch] = useState("");

  useEffect(() => {
    const syncFromHistory = () => setActive(sectionFromPath(window.location.pathname));
    window.addEventListener("popstate", syncFromHistory);
    return () => window.removeEventListener("popstate", syncFromHistory);
  }, []);

  const handleNavClick = useCallback((event: MouseEvent<HTMLAnchorElement>, item: (typeof OPS_SECTIONS)[number]) => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.altKey || event.ctrlKey || event.shiftKey) {
      return;
    }

    event.preventDefault();
    setActive(item.id);
    window.history.pushState({ pokrovAdminSection: item.id }, "", item.href);
  }, []);

  const submitGlobalSearch = useCallback((event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const q = globalSearch.trim();
    if (!q) return;
    setActive("users");
    const href = `/users?q=${encodeURIComponent(q)}`;
    window.history.pushState({ pokrovAdminSection: "users", q }, "", href);
    window.dispatchEvent(new CustomEvent("pokrov-admin-global-search", { detail: { q } }));
  }, [globalSearch]);

  return (
    <div className="min-h-screen bg-[color:var(--atlas-canvas-alt)] text-[color:var(--atlas-text)]">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-[248px] border-r border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] px-3 py-4 lg:block">
        <div className="mb-5 flex items-center gap-3 px-2">
          <div className="grid h-9 w-9 place-items-center rounded-[var(--pokrov-radius-card)] bg-[color:var(--atlas-primary)] text-sm font-bold text-[color:var(--atlas-primary-text)]">
            P
          </div>
          <div className="min-w-0">
            <div className="text-sm font-semibold leading-tight">POKROV Admin</div>
            <div className="text-[11px] text-[color:var(--atlas-text-muted)]">admin.pokrov.space</div>
          </div>
        </div>
        <nav className="ops-scrollbar flex max-h-[calc(100vh-92px)] flex-col gap-1 overflow-y-auto pr-1">
          {OPS_SECTIONS.map((item) => {
            const Icon = icons[item.id];
            const selected = active === item.id;
            return (
              <a
                key={item.id}
                href={item.href}
                onClick={(event) => handleNavClick(event, item)}
                className={cn(
                  "flex min-h-[var(--pokrov-nav-item-min-height)] items-center gap-2 rounded-[var(--pokrov-radius-card)] px-3 text-sm font-medium text-[color:var(--pokrov-nav-text)] transition",
                  selected && "bg-[color:var(--pokrov-nav-active-bg)] text-[color:var(--atlas-text)]",
                  !selected && "hover:bg-[color:var(--pokrov-nav-hover-bg)]"
                )}
              >
                <Icon size={17} strokeWidth={1.85} />
                <span className="truncate">{item.label}</span>
              </a>
            );
          })}
        </nav>
      </aside>

      <div className="lg:pl-[248px]">
        <header className="sticky top-0 z-10 border-b border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)]/95 px-4 py-3 backdrop-blur lg:px-6">
          <div className="grid min-h-10 gap-3 xl:grid-cols-[minmax(180px,0.7fr),minmax(320px,1.2fr),auto] xl:items-center">
            <div>
              <div className="text-[11px] uppercase tracking-[0.08em] text-[color:var(--atlas-text-muted)]">Ops admin</div>
              <h1 className="text-xl font-semibold leading-tight">{sectionMap.get(active)?.label}</h1>
            </div>
            <form onSubmit={submitGlobalSearch} className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[color:var(--atlas-text-muted)]" size={16} />
              <input
                value={globalSearch}
                onChange={(event) => setGlobalSearch(event.target.value)}
                placeholder="Найти: tg_id, username, заказ, нода, ключ/email"
                className="h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] pl-9 pr-3 text-sm outline-none transition focus:border-[color:var(--atlas-focus)]"
              />
            </form>
            <div className="hidden items-center gap-2 sm:flex">
              <span className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] px-3 py-1 text-xs text-[color:var(--atlas-text-soft)]">
                POKROV API
              </span>
              <span className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] px-3 py-1 text-xs text-[color:var(--atlas-text-soft)]">
                superadmin v1
              </span>
            </div>
          </div>
          <nav className="ops-scrollbar mt-3 flex gap-2 overflow-x-auto pb-1 lg:hidden">
            {OPS_SECTIONS.map((item) => {
              const Icon = icons[item.id];
              const selected = active === item.id;
              return (
                <a
                  key={item.id}
                  href={item.href}
                  onClick={(event) => handleNavClick(event, item)}
                  className={cn(
                    "inline-flex h-9 shrink-0 items-center gap-2 rounded-[var(--pokrov-radius-card)] border px-3 text-xs font-semibold",
                    selected
                      ? "border-[color:var(--atlas-border-strong)] bg-[color:var(--pokrov-nav-active-bg)]"
                      : "border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] text-[color:var(--atlas-text-soft)]"
                  )}
                >
                  <Icon size={15} />
                  {item.label}
                </a>
              );
            })}
          </nav>
        </header>
        <main className="px-4 py-4 lg:px-6 lg:py-5">
          <OpsDashboard section={active} />
        </main>
      </div>
      <div className="fixed bottom-3 right-3 z-30 hidden rounded-full border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] px-3 py-2 text-xs text-[color:var(--atlas-text-soft)] shadow-[var(--atlas-shadow-soft)] md:block">
        <ShieldCheck className="mr-1 inline" size={14} />
        Admin only
      </div>
    </div>
  );
}
