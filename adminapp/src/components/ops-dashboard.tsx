"use client";

import type { OpsShellStatus } from "@/components/ops/shell-status";
import { AdminRouteBoundary } from "@/components/ops/route-boundary";
import { ActiveOpsRoute } from "@/features/registry";
import type { OperatorShellIdentity } from "@/lib/admin-api/identity";
import type { OpsSectionId } from "@/lib/sections";

export function OpsDashboard({
  section,
  identity,
  onShellStatus,
  onIdentity,
  onNavigate
}: {
  section: OpsSectionId;
  identity?: OperatorShellIdentity | null;
  onShellStatus?: (status: OpsShellStatus) => void;
  onIdentity?: (identity: OperatorShellIdentity | null) => void;
  onNavigate?: (href: string) => void;
}) {
  return (
    <AdminRouteBoundary onShellStatus={onShellStatus} onIdentity={onIdentity}>
      <ActiveOpsRoute section={section} identity={identity} onShellStatus={onShellStatus} onNavigate={onNavigate} />
    </AdminRouteBoundary>
  );
}
