import { Fragment, type ReactNode } from "react";

import type { OpsShellStatus } from "@/components/ops/shell-status";
import { LegacySection } from "@/features/legacy/legacy-section";
import { AlertsPage } from "@/features/network/alerts-page";
import { FreeTierPage } from "@/features/network/free-tier-page";
import { ProviderLimitsPage } from "@/features/network/provider-limits-page";
import { TrafficPage } from "@/features/network/traffic-page";
import { NodesPage } from "@/features/nodes/nodes-page";
import { OverviewPage } from "@/features/overview/overview-page";
import { OnlinePage } from "@/features/support/online-page";
import { TicketsPage } from "@/features/support/tickets-page";
import { UsersPage } from "@/features/users/users-page";
import type { OpsSectionId } from "@/lib/sections";

type RouteProps = {
  onShellStatus?: (status: OpsShellStatus) => void;
};

type RouteRenderer = (props: RouteProps) => ReactNode;

export const OPS_FEATURE_REGISTRY: Record<OpsSectionId, RouteRenderer> = {
  dashboard: ({ onShellStatus }) => <OverviewPage onShellStatus={onShellStatus} />,
  nodes: ({ onShellStatus }) => <NodesPage onShellStatus={onShellStatus} />,
  traffic: ({ onShellStatus }) => <TrafficPage onShellStatus={onShellStatus} />,
  alerts: ({ onShellStatus }) => <AlertsPage onShellStatus={onShellStatus} />,
  "provider-caps": ({ onShellStatus }) => <ProviderLimitsPage onShellStatus={onShellStatus} />,
  "free-tier": ({ onShellStatus }) => <FreeTierPage onShellStatus={onShellStatus} />,
  users: ({ onShellStatus }) => <UsersPage onShellStatus={onShellStatus} />,
  online: ({ onShellStatus }) => <OnlinePage onShellStatus={onShellStatus} />,
  tickets: ({ onShellStatus }) => <TicketsPage onShellStatus={onShellStatus} />,
  payments: ({ onShellStatus }) => <LegacySection section="payments" onShellStatus={onShellStatus} />,
  funnel: ({ onShellStatus }) => <LegacySection section="funnel" onShellStatus={onShellStatus} />,
  promos: ({ onShellStatus }) => <LegacySection section="promos" onShellStatus={onShellStatus} />,
  referrals: ({ onShellStatus }) => <LegacySection section="referrals" onShellStatus={onShellStatus} />,
  release: ({ onShellStatus }) => <LegacySection section="release" onShellStatus={onShellStatus} />,
  broadcast: ({ onShellStatus }) => <LegacySection section="broadcast" onShellStatus={onShellStatus} />
};

export function ActiveOpsRoute({ section, onShellStatus }: { section: OpsSectionId; onShellStatus?: (status: OpsShellStatus) => void }) {
  return <Fragment key={section}>{OPS_FEATURE_REGISTRY[section]({ onShellStatus })}</Fragment>;
}
