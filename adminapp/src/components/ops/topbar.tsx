"use client";

import { Command, Menu, RefreshCw, ShieldCheck } from "lucide-react";

import { OpsDesktopNavigation } from "@/components/ops/navigation";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatSourceAge, statusPresentation } from "@/lib/ops-status/presentation";
import type { OpsSectionId } from "@/lib/sections";

import type { OpsShellStatus } from "./shell-status";

export interface OpsTopbarProps {
  sectionLabel: string;
  active: OpsSectionId;
  status: OpsShellStatus;
  onNavigate: (href: string) => void;
  onOpenCommands: () => void;
  onOpenNavigation: () => void;
  onRefresh: () => void;
}

export function OpsTopbar({
  sectionLabel,
  active,
  status,
  onNavigate,
  onOpenCommands,
  onOpenNavigation,
  onRefresh
}: OpsTopbarProps) {
  const apiPresentation = statusPresentation(status.api);
  const sessionPresentation = statusPresentation(status.session);
  const systemHealthy = status.api === "ok" && status.session === "ok";

  return (
    <header className="sticky top-0 z-30 border-b border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)]/96 shadow-[0_1px_0_rgba(17,24,20,0.03)] backdrop-blur">
      <div className="mx-auto flex min-h-16 max-w-[1800px] flex-wrap items-center gap-3 px-4 py-2 lg:px-6">
        <Button variant="ghost" size="icon" aria-label="Открыть навигацию" className="xl:hidden" onClick={onOpenNavigation}>
          <Menu aria-hidden="true" size={18} strokeWidth={1.8} />
        </Button>

        <div className="flex shrink-0 items-center gap-2.5">
          <div className="grid h-9 w-9 place-items-center rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border-strong)] bg-[color:var(--pokrov-status-success-bg)] text-[color:var(--atlas-primary)]">
            <ShieldCheck aria-hidden="true" size={21} strokeWidth={1.8} />
          </div>
          <div className="leading-none">
            <div className="text-sm font-bold tracking-[0.01em]">POKROV OPS</div>
            <div className="mt-1 text-[10px] text-[color:var(--atlas-text-muted)]">Центр управления</div>
          </div>
        </div>

        <div className="hidden h-8 w-px bg-[color:var(--atlas-border)] sm:block" />
        <h1 className="min-w-0 flex-1 truncate text-lg font-semibold leading-tight text-[color:var(--atlas-text)]">{sectionLabel}</h1>

        <div
          className="hidden items-center gap-2 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] px-3 py-2 text-xs font-semibold xl:flex"
          aria-label={systemHealthy ? "Система под контролем" : "Система требует внимания"}
        >
          <span className={`h-2 w-2 rounded-full ${systemHealthy ? "bg-emerald-600" : "bg-amber-500"}`} />
          {systemHealthy ? "Система под контролем" : "Требует внимания"}
        </div>

        <div className="hidden items-center gap-2 text-xs text-[color:var(--atlas-text-soft)] lg:flex">
          <span className="inline-flex items-center gap-1.5" aria-label={`Состояние API: ${apiPresentation.label}`}>
            API <StatusBadge status={status.api} />
          </span>
          <span className="inline-flex items-center gap-1.5" aria-label={`Состояние сессии: ${sessionPresentation.label}`}>
            Сессия <StatusBadge status={status.session} />
          </span>
          <span className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] px-2.5 py-1.5">
            Старейший источник:{" "}
            {status.oldestRequiredSourceAt ? (
              <time dateTime={status.oldestRequiredSourceAt}>{formatSourceAge(status.oldestRequiredSourceAt)}</time>
            ) : (
              "Нет данных"
            )}
          </span>
        </div>

        <Button variant="ghost" size="icon" aria-label="Обновить" onClick={onRefresh}>
          <RefreshCw aria-hidden="true" size={17} strokeWidth={1.8} />
        </Button>
        <Button variant="secondary" aria-label="Команды" onClick={onOpenCommands}>
          <Command aria-hidden="true" size={15} strokeWidth={1.8} />
          <span className="hidden sm:inline">Команды</span>
          <kbd aria-hidden="true" className="hidden rounded border border-[color:var(--atlas-border)] px-1.5 py-0.5 font-mono text-[10px] xl:inline">
            Ctrl K
          </kbd>
        </Button>
      </div>
      <OpsDesktopNavigation active={active} onNavigate={onNavigate} />
    </header>
  );
}
