"use client";

import type { OpsShellStatus } from "@/components/ops/shell-status";
import { AdminRouteBoundary } from "@/components/ops/route-boundary";
import { ActiveOpsRoute } from "@/features/registry";
import type { OpsSectionId } from "@/lib/sections";

export function OpsDashboard({
  section,
  onShellStatus
}: {
  section: OpsSectionId;
  onShellStatus?: (status: OpsShellStatus) => void;
}) {
  return (
    <AdminRouteBoundary onShellStatus={onShellStatus}>
      <ActiveOpsRoute section={section} onShellStatus={onShellStatus} />
    </AdminRouteBoundary>
  );
}
