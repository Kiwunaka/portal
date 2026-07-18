"use client";

import { Command, Menu, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatSourceAge, statusPresentation } from "@/lib/ops-status/presentation";

import type { OpsShellStatus } from "./shell-status";

export interface OpsTopbarProps {
  sectionLabel: string;
  status: OpsShellStatus;
  onOpenCommands: () => void;
  onOpenNavigation: () => void;
  onRefresh: () => void;
}

export function OpsTopbar({
  sectionLabel,
  status,
  onOpenCommands,
  onOpenNavigation,
  onRefresh
}: OpsTopbarProps) {
  const apiPresentation = statusPresentation(status.api);
  const sessionPresentation = statusPresentation(status.session);

  return (
    <header className="sticky top-0 z-30 border-b border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)]/95 px-4 py-3 backdrop-blur lg:px-6">
      <div className="flex flex-wrap items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          aria-label="Открыть навигацию"
          className="lg:hidden"
          onClick={onOpenNavigation}
        >
          <Menu aria-hidden="true" size={18} />
        </Button>

        <div className="min-w-0 flex-1">
          <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[color:var(--atlas-text-muted)]">
            Центр управления
          </div>
          <h1 className="truncate text-xl font-semibold leading-tight text-[color:var(--atlas-text)]">{sectionLabel}</h1>
        </div>

        <div className="order-3 flex w-full flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)] lg:order-none lg:w-auto">
          <span className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] px-3 py-1.5">
            Старейший источник:{" "}
            {status.oldestRequiredSourceAt ? (
              <time dateTime={status.oldestRequiredSourceAt}>{formatSourceAge(status.oldestRequiredSourceAt)}</time>
            ) : (
              "Нет данных"
            )}
          </span>
          <span className="inline-flex items-center gap-1.5" aria-label={`Состояние API: ${apiPresentation.label}`}>
            API <StatusBadge status={status.api} />
          </span>
          <span className="inline-flex items-center gap-1.5" aria-label={`Состояние сессии: ${sessionPresentation.label}`}>
            Сессия <StatusBadge status={status.session} />
          </span>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <Button variant="secondary" onClick={onRefresh}>
            <RefreshCw aria-hidden="true" size={15} />
            Обновить
          </Button>
          <Button variant="secondary" aria-label="Команды" onClick={onOpenCommands}>
            <Command aria-hidden="true" size={15} />
            Команды
            <kbd aria-hidden="true" className="hidden rounded border border-[color:var(--atlas-border)] px-1.5 py-0.5 font-mono text-[10px] sm:inline">
              Ctrl K
            </kbd>
          </Button>
        </div>
      </div>
    </header>
  );
}
