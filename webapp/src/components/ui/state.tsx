import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { CircleAlert, Inbox } from "lucide-react";

import { cn } from "@/components/utils";

function StateShell({
  icon: Icon,
  iconClassName,
  title,
  body,
  actions,
  className,
  role,
}: {
  icon: LucideIcon;
  iconClassName?: string;
  title: ReactNode;
  body?: ReactNode;
  actions?: ReactNode;
  className?: string;
  role?: "alert" | "status";
}) {
  return (
    <div
      role={role}
      className={cn(
        "flex flex-col items-center gap-3 rounded-card border border-line bg-surface px-6 py-10 text-center",
        className,
      )}
    >
      <span className={cn("flex size-12 items-center justify-center rounded-full bg-canvas-alt", iconClassName)}>
        <Icon size={22} strokeWidth={1.8} aria-hidden="true" />
      </span>
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      {body ? <p className="max-w-sm text-sm leading-relaxed text-ink-soft">{body}</p> : null}
      {actions ? <div className="mt-2 flex flex-wrap justify-center gap-2">{actions}</div> : null}
    </div>
  );
}

export function EmptyState({
  icon = Inbox,
  title,
  body,
  actions,
  className,
}: {
  icon?: LucideIcon;
  title: ReactNode;
  body?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return <StateShell role="status" icon={icon} iconClassName="text-ink-soft" title={title} body={body} actions={actions} className={className} />;
}

export function ErrorState({
  icon = CircleAlert,
  title,
  body,
  actions,
  className,
}: {
  icon?: LucideIcon;
  title: ReactNode;
  body?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <StateShell
      role="alert"
      icon={icon}
      iconClassName="bg-danger-bg text-danger-text"
      title={title}
      body={body}
      actions={actions}
      className={className}
    />
  );
}
