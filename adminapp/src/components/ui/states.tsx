import { AlertTriangle, Inbox, LoaderCircle } from "lucide-react";
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
  icon?: ReactNode;
}

function StatePanel({ title, description, action, tone = "neutral", busy = false, className, icon }: StatePanelProps) {
  return (
    <div
      role={tone === "danger" ? "alert" : "status"}
      aria-live={tone === "danger" ? "assertive" : "polite"}
      aria-busy={busy || undefined}
      className={cn(
        "relative flex min-h-32 flex-col items-start justify-center overflow-hidden rounded-[var(--pokrov-radius-card)] border p-4",
        tone === "danger"
          ? "border-[color:var(--command-status-danger-line)] bg-[color:var(--command-status-danger-bg)] before:absolute before:inset-y-0 before:left-0 before:w-0.5 before:bg-[color:var(--command-status-danger-text)]"
          : "border-dashed border-[color:var(--atlas-border-strong)] bg-[color:var(--command-surface-raised)]",
        className
      )}
    >
      <div className="flex items-start gap-3">
        <span className={cn(
          "grid h-8 w-8 shrink-0 place-items-center rounded-[var(--pokrov-radius-control)] border",
          tone === "danger"
            ? "border-[color:var(--command-status-danger-line)] text-[color:var(--command-status-danger-text)]"
            : "border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] text-[color:var(--atlas-text-soft)]"
        )}>
          {icon}
        </span>
        <div>
          <h3 className={cn("text-sm font-semibold", tone === "danger" ? "text-[color:var(--command-status-danger-text)]" : "text-[color:var(--atlas-text)]")}>{title}</h3>
          {description ? <p className="mt-1 max-w-2xl text-xs leading-5 text-[color:var(--atlas-text-soft)]">{description}</p> : null}
        </div>
      </div>
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
  return <StatePanel title={title} description={description} action={action} className={className} icon={<Inbox aria-hidden="true" size={16} strokeWidth={1.8} />} />;
}

export interface LoadingStateProps {
  title?: string;
  description?: string;
  className?: string;
}

export function LoadingState({ title = "Загрузка данных", description = "Подождите, источник ещё отвечает.", className }: LoadingStateProps) {
  return <StatePanel title={title} description={description} busy className={className} icon={<LoaderCircle aria-hidden="true" className="animate-spin" size={16} strokeWidth={1.8} />} />;
}

export interface ErrorStateProps {
  title?: string;
  description: string;
  action?: ReactNode;
  className?: string;
}

export function ErrorState({ title = "Не удалось загрузить данные", description, action, className }: ErrorStateProps) {
  return <StatePanel title={title} description={description} action={action} tone="danger" className={className} icon={<AlertTriangle aria-hidden="true" size={16} strokeWidth={1.8} />} />;
}
