"use client";

import { OpsNavigation } from "@/components/ops/navigation";
import { Dialog } from "@/components/ui/dialog";
import type { OpsSectionId } from "@/lib/sections";

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
