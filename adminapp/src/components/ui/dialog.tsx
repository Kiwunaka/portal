"use client";

import { useEffect, useId, useRef, type KeyboardEvent, type ReactNode, type RefObject } from "react";

import { cn } from "@/components/utils";

import { Button } from "./button";

const FOCUSABLE = "button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])";

export interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  id?: string;
  className?: string;
  initialFocusRef?: RefObject<HTMLElement | null>;
}

export function Dialog({ open, onOpenChange, title, description, children, footer, id, className, initialFocusRef }: DialogProps) {
  const generatedId = useId();
  const dialogId = id ?? `${generatedId}-dialog`;
  const titleId = `${dialogId}-title`;
  const descriptionId = `${dialogId}-description`;
  const dialogRef = useRef<HTMLDivElement>(null);
  const restoreFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    restoreFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const firstFocusable = dialogRef.current?.querySelector<HTMLElement>(FOCUSABLE);
    (initialFocusRef?.current ?? firstFocusable ?? dialogRef.current)?.focus();

    return () => {
      restoreFocusRef.current?.focus();
    };
  }, [initialFocusRef, open]);

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      onOpenChange(false);
      return;
    }

    if (event.key !== "Tab" || !dialogRef.current) {
      return;
    }

    const focusable = Array.from(dialogRef.current.querySelectorAll<HTMLElement>(FOCUSABLE));
    if (focusable.length === 0) {
      event.preventDefault();
      dialogRef.current.focus();
      return;
    }

    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4">
      <div
        ref={dialogRef}
        id={dialogId}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descriptionId : undefined}
        tabIndex={-1}
        onKeyDown={handleKeyDown}
        className={cn("max-h-[min(88dvh,52rem)] w-full max-w-2xl overflow-auto rounded-[var(--pokrov-radius-modal)] border border-[color:var(--atlas-border-strong)] bg-[color:var(--atlas-surface)] shadow-[var(--atlas-shadow-medium)] focus:outline-none", className)}
      >
        <header className="flex items-start justify-between gap-4 border-b border-[color:var(--atlas-border)] px-5 py-4">
          <div>
            <h2 id={titleId} className="text-base font-semibold text-[color:var(--atlas-text)]">{title}</h2>
            {description ? <p id={descriptionId} className="mt-1 text-xs leading-5 text-[color:var(--atlas-text-soft)]">{description}</p> : null}
          </div>
          <Button variant="ghost" size="icon" aria-label="Закрыть диалог" onClick={() => onOpenChange(false)}>
            <span aria-hidden="true" className="text-lg leading-none">×</span>
          </Button>
        </header>
        <div className="px-5 py-4 text-sm text-[color:var(--atlas-text)]">{children}</div>
        {footer ? <footer className="flex flex-wrap justify-end gap-2 border-t border-[color:var(--atlas-border)] px-5 py-4">{footer}</footer> : null}
      </div>
    </div>
  );
}
