import type { ReactNode } from "react";

import type { OpsShellStatus } from "@/components/ops/shell-status";
import { BroadcastPage } from "@/features/control/broadcast-page";
import { NewsPage } from "@/features/control/news-page";
import { ReleasePage } from "@/features/control/release-page";
import { GovernancePage } from "@/features/governance/governance-page";
import { IncidentRoomPage } from "@/features/incidents/incident-room-page";
import { BonusesPage } from "@/features/growth/bonuses-page";
import { ProgramsPage } from "@/features/growth/programs-page";
import { AccessPage } from "@/features/money/access-page";
import { AlertsPage } from "@/features/network/alerts-page";
import { EmergencyNetworkPage } from "@/features/network/emergency-network-page";
import { FreeTierPage } from "@/features/network/free-tier-page";
import { ProviderLimitsPage } from "@/features/network/provider-limits-page";
import { TrafficPage } from "@/features/network/traffic-page";
import { NodesPage } from "@/features/nodes/nodes-page";
import { OverviewPage } from "@/features/overview/overview-page";
import { ShiftPage } from "@/features/shift/shift-page";
import { FunnelPage } from "@/features/revenue/funnel-page";
import { PaymentsPage } from "@/features/revenue/payments-page";
import { PromosPage } from "@/features/revenue/promos-page";
import { ReferralsPage } from "@/features/revenue/referrals-page";
import { OnlinePage } from "@/features/support/online-page";
import { TicketsPage } from "@/features/support/tickets-page";
import { UsersPage } from "@/features/users/users-page";
import type { OperatorShellIdentity } from "@/lib/admin-api/identity";
import type { OpsSectionId } from "@/lib/sections";

type RouteProps = {
  identity?: OperatorShellIdentity | null;
  onShellStatus?: (status: OpsShellStatus) => void;
  onNavigate?: (href: string) => void;
};

type RouteRenderer = (props: RouteProps) => ReactNode;

export const OPS_FEATURE_REGISTRY: Record<OpsSectionId, RouteRenderer> = {
  shift: ({ onShellStatus }) => <ShiftPage onShellStatus={onShellStatus} />,
  support: ({ onShellStatus }) => <UsersPage onShellStatus={onShellStatus} />,
  network: ({ onShellStatus }) => <NodesPage onShellStatus={onShellStatus} />,
  money: ({ onShellStatus }) => <PaymentsPage onShellStatus={onShellStatus} />,
  growth: ({ onShellStatus }) => <FunnelPage onShellStatus={onShellStatus} />,
  releases: ({ onShellStatus }) => <ReleasePage onShellStatus={onShellStatus} />,
  governance: ({ onShellStatus }) => <GovernancePage onShellStatus={onShellStatus} />,
  dashboard: ({ onShellStatus, onNavigate }) => <OverviewPage onShellStatus={onShellStatus} onNavigate={onNavigate} />,
  nodes: ({ onShellStatus }) => <NodesPage onShellStatus={onShellStatus} />,
  "emergency-network": ({ onShellStatus }) => <EmergencyNetworkPage onShellStatus={onShellStatus} />,
  traffic: ({ onShellStatus }) => <TrafficPage onShellStatus={onShellStatus} />,
  alerts: ({ onShellStatus }) => <AlertsPage onShellStatus={onShellStatus} />,
  incidents: ({ onShellStatus }) => <IncidentRoomPage onShellStatus={onShellStatus} />,
  "provider-caps": ({ onShellStatus }) => <ProviderLimitsPage onShellStatus={onShellStatus} />,
  "free-tier": ({ onShellStatus }) => <FreeTierPage onShellStatus={onShellStatus} />,
  access: ({ onShellStatus }) => <AccessPage onShellStatus={onShellStatus} />,
  users: ({ onShellStatus }) => <UsersPage onShellStatus={onShellStatus} />,
  online: ({ onShellStatus }) => <OnlinePage onShellStatus={onShellStatus} />,
  tickets: ({ identity, onShellStatus }) => <TicketsPage identity={identity} onShellStatus={onShellStatus} />,
  payments: ({ onShellStatus }) => <PaymentsPage onShellStatus={onShellStatus} />,
  funnel: ({ onShellStatus }) => <FunnelPage onShellStatus={onShellStatus} />,
  bonuses: ({ onShellStatus }) => <BonusesPage onShellStatus={onShellStatus} />,
  programs: ({ onShellStatus }) => <ProgramsPage onShellStatus={onShellStatus} />,
  promos: ({ onShellStatus }) => <PromosPage onShellStatus={onShellStatus} />,
  referrals: ({ onShellStatus }) => <ReferralsPage onShellStatus={onShellStatus} />,
  release: ({ onShellStatus }) => <ReleasePage onShellStatus={onShellStatus} />,
  broadcast: ({ onShellStatus }) => <BroadcastPage onShellStatus={onShellStatus} />,
  news: ({ onShellStatus }) => <NewsPage onShellStatus={onShellStatus} />
};

export function ActiveOpsRoute({
  section,
  identity,
  onShellStatus,
  onNavigate
}: {
  section: OpsSectionId;
  identity?: OperatorShellIdentity | null;
  onShellStatus?: (status: OpsShellStatus) => void;
  onNavigate?: (href: string) => void;
}) {
  return <div key={section} className="ops-route min-w-0">{OPS_FEATURE_REGISTRY[section]({ identity, onShellStatus, onNavigate })}</div>;
}
