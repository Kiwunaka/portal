import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { CircleAlert, Compass } from "lucide-react";

import { EmptyState, ErrorState } from "@/components/ui/state";

/** Shared recovery surface for error and not-found boundaries. */
export function CabinetBoundary({
  kind,
  icon,
  title,
  description,
  actions,
}: {
  kind: "error" | "not-found";
  icon?: LucideIcon;
  title: ReactNode;
  description: ReactNode;
  actions: ReactNode;
}) {
  const State = kind === "error" ? ErrorState : EmptyState;
  return (
    <main className="mx-auto flex min-h-[72vh] w-full max-w-[720px] items-center px-4 py-8">
      <State
        icon={icon || (kind === "error" ? CircleAlert : Compass)}
        title={title}
        body={description}
        actions={actions}
        className="w-full rounded-panel px-6 py-12 shadow-medium"
      />
    </main>
  );
}
