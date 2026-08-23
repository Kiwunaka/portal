"use client";

import { MoreHorizontal } from "lucide-react";
import type { MouseEvent } from "react";

import {
  MOBILE_PRIMARY_WORKSPACES,
  OpsNavigation,
  SECTION_ICONS
} from "@/components/ops/navigation";
import { cn } from "@/components/utils";
import { Dialog } from "@/components/ui/dialog";
import {
  OPS_WORKSPACES,
  opsWorkspaceForSection,
  type OpsSectionId
} from "@/lib/sections";

export interface MobileNavigationProps {
  open: boolean;
  active: OpsSectionId;
  onOpenChange: (open: boolean) => void;
  onNavigate: (href: string) => void;
}

export function MobileNavigation({ open, active, onOpenChange, onNavigate }: MobileNavigationProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Навигация по разделам"
      description="Выберите рабочий раздел. После перехода меню закроется."
      className="mr-auto h-[calc(100dvh-2rem)] max-h-none max-w-sm rounded-[var(--pokrov-radius-modal)]"
    >
      <OpsNavigation
        active={active}
        label="Мобильная навигация"
        className="max-h-[calc(100dvh-9rem)] pr-1"
        onNavigate={(href) => {
          onNavigate(href);
          onOpenChange(false);
        }}
      />
    </Dialog>
  );
}

function isPlainPrimaryClick(event: MouseEvent<HTMLAnchorElement>): boolean {
  return event.button === 0 && !event.metaKey && !event.altKey && !event.ctrlKey && !event.shiftKey;
}

export function MobilePrimaryNavigation({
  active,
  onNavigate,
  onOpenMore
}: {
  active: OpsSectionId;
  onNavigate: (href: string) => void;
  onOpenMore: () => void;
}) {
  const activeWorkspace = opsWorkspaceForSection(active).id;
  const primary = OPS_WORKSPACES.filter((workspace) => MOBILE_PRIMARY_WORKSPACES.includes(workspace.id));

  return (
    <nav
      aria-label="Основные рабочие области"
      className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)]/98 px-1 pb-[max(env(safe-area-inset-bottom),0.25rem)] pt-1 shadow-[0_-8px_24px_rgba(17,24,20,0.08)] backdrop-blur md:hidden"
    >
      {primary.map((workspace) => {
        const Icon = SECTION_ICONS[workspace.id];
        const selected = activeWorkspace === workspace.id;
        return (
          <a
            key={workspace.id}
            href={workspace.href}
            aria-current={active === workspace.id ? "page" : undefined}
            onClick={(event) => {
              if (!isPlainPrimaryClick(event)) return;
              event.preventDefault();
              onNavigate(workspace.href);
            }}
            className={cn(
              "flex min-h-12 flex-col items-center justify-center gap-0.5 rounded-[var(--pokrov-radius-control)] px-1 text-[10px] font-semibold",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--atlas-focus)]",
              selected ? "text-[color:var(--atlas-primary)]" : "text-[color:var(--atlas-text-muted)]"
            )}
          >
            <Icon aria-hidden="true" size={17} strokeWidth={1.8} />
            <span className="max-w-full truncate">{workspace.shortLabel}</span>
          </a>
        );
      })}
      <button
        type="button"
        onClick={onOpenMore}
        className="flex min-h-12 flex-col items-center justify-center gap-0.5 rounded-[var(--pokrov-radius-control)] px-1 text-[10px] font-semibold text-[color:var(--atlas-text-muted)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--atlas-focus)]"
      >
        <MoreHorizontal aria-hidden="true" size={18} strokeWidth={1.8} />
        <span>Ещё</span>
      </button>
    </nav>
  );
}
