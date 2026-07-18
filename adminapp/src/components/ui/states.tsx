import type { ReactNode } from "react";

import { cn } from "@/components/utils";

type StateTone = "neutral" | "danger";

interface StatePanelProps {
  title: string;
  description?: string;
  action?: ReactNode;
  tone?: StateTone;
  busy?: boolean;
  className?: string;
}

function StatePanel({ title, description, action, tone = "neutral", busy = false, className }: StatePanelProps) {
  return (
    <div
      role={tone === "danger" ? "alert" : "status"}
      aria-live={tone === "danger" ? "assertive" : "polite"}
      aria-busy={busy || undefined}
      className={cn(
        "flex min-h-32 flex-col items-start justify-center rounded-[var(--pokrov-radius-card)] border p-4",
        tone === "danger"
          ? "border-[color:var(--command-status-danger-line)] bg-[color:var(--command-status-danger-bg)]"
          : "border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)]",
        className
      )}
    >
      <h3 className={cn("text-sm font-semibold", tone === "danger" ? "text-[color:var(--command-status-danger-text)]" : "text-[color:var(--atlas-text)]")}>{title}</h3>
      {description ? <p className="mt-1 max-w-2xl text-xs leading-5 text-[color:var(--atlas-text-soft)]">{description}</p> : null}
      {action ? <div className="mt-3">{action}</div> : null}
    </div>
  );
}

export interface EmptyStateProps {
  title?: string;
  description: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ title = "Нет данных", description, action, className }: EmptyStateProps) {
  return <StatePanel title={title} description={description} action={action} className={className} />;
}

export interface LoadingStateProps {
  title?: string;
  description?: string;
  className?: string;
}

export function LoadingState({ title = "Загрузка данных", description = "Подождите, источник ещё отвечает.", className }: LoadingStateProps) {
  return <StatePanel title={title} description={description} busy className={className} />;
}

export interface ErrorStateProps {
  title?: string;
  description: string;
  action?: ReactNode;
  className?: string;
}

export function ErrorState({ title = "Не удалось загрузить данные", description, action, className }: ErrorStateProps) {
  return <StatePanel title={title} description={description} action={action} tone="danger" className={className} />;
}
