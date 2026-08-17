import type { ReactNode } from "react";

import type { OpsShellStatus } from "@/components/ops/shell-status";
import { BroadcastPage } from "@/features/control/broadcast-page";
import { NewsPage } from "@/features/control/news-page";
import { ReleasePage } from "@/features/control/release-page";
import { AlertsPage } from "@/features/network/alerts-page";
import { EmergencyNetworkPage } from "@/features/network/emergency-network-page";
import { FreeTierPage } from "@/features/network/free-tier-page";
import { ProviderLimitsPage } from "@/features/network/provider-limits-page";
import { TrafficPage } from "@/features/network/traffic-page";
import { NodesPage } from "@/features/nodes/nodes-page";
import { OverviewPage } from "@/features/overview/overview-page";
import { FunnelPage } from "@/features/revenue/funnel-page";
import { PaymentsPage } from "@/features/revenue/payments-page";
import { PromosPage } from "@/features/revenue/promos-page";
import { ReferralsPage } from "@/features/revenue/referrals-page";
import { OnlinePage } from "@/features/support/online-page";
import { TicketsPage } from "@/features/support/tickets-page";
import { UsersPage } from "@/features/users/users-page";
import type { OpsSectionId } from "@/lib/sections";

type RouteProps = {
  onShellStatus?: (status: OpsShellStatus) => void;
  onNavigate?: (href: string) => void;
};

type RouteRenderer = (props: RouteProps) => ReactNode;

export const OPS_FEATURE_REGISTRY: Record<OpsSectionId, RouteRenderer> = {
  dashboard: ({ onShellStatus, onNavigate }) => <OverviewPage onShellStatus={onShellStatus} onNavigate={onNavigate} />,
  nodes: ({ onShellStatus }) => <NodesPage onShellStatus={onShellStatus} />,
  "emergency-network": ({ onShellStatus }) => <EmergencyNetworkPage onShellStatus={onShellStatus} />,
  traffic: ({ onShellStatus }) => <TrafficPage onShellStatus={onShellStatus} />,
  alerts: ({ onShellStatus }) => <AlertsPage onShellStatus={onShellStatus} />,
  "provider-caps": ({ onShellStatus }) => <ProviderLimitsPage onShellStatus={onShellStatus} />,
  "free-tier": ({ onShellStatus }) => <FreeTierPage onShellStatus={onShellStatus} />,
  users: ({ onShellStatus }) => <UsersPage onShellStatus={onShellStatus} />,
  online: ({ onShellStatus }) => <OnlinePage onShellStatus={onShellStatus} />,
  tickets: ({ onShellStatus }) => <TicketsPage onShellStatus={onShellStatus} />,
  payments: ({ onShellStatus }) => <PaymentsPage onShellStatus={onShellStatus} />,
  funnel: ({ onShellStatus }) => <FunnelPage onShellStatus={onShellStatus} />,
  promos: ({ onShellStatus }) => <PromosPage onShellStatus={onShellStatus} />,
  referrals: ({ onShellStatus }) => <ReferralsPage onShellStatus={onShellStatus} />,
  release: ({ onShellStatus }) => <ReleasePage onShellStatus={onShellStatus} />,
  broadcast: ({ onShellStatus }) => <BroadcastPage onShellStatus={onShellStatus} />,
  news: ({ onShellStatus }) => <NewsPage onShellStatus={onShellStatus} />
};

export function ActiveOpsRoute({
  section,
  onShellStatus,
  onNavigate
}: {
  section: OpsSectionId;
  onShellStatus?: (status: OpsShellStatus) => void;
  onNavigate?: (href: string) => void;
}) {
  return <div key={section} className="ops-route min-w-0">{OPS_FEATURE_REGISTRY[section]({ onShellStatus, onNavigate })}</div>;
}
