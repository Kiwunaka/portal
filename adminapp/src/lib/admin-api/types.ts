export type OpsAlert = {
  id: number;
  fingerprint: string;
  source: string;
  severity: "critical" | "warning" | "info" | string;
  status: "active" | "silenced" | "resolved" | string;
  title: string;
  body?: string | null;
  node_code?: string | null;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
  resolved_at?: string | null;
  acknowledged_at?: string | null;
  silence_until?: string | null;
  affected_count?: number | null;
};

export type ProviderQuotaStatus = {
  node_code: string;
  node_name?: string | null;
  configured: boolean;
  enabled: boolean;
  state: string;
  included_gb: number;
  used_gb: number;
  remaining_gb: number;
  used_pct: number;
  cycle_start?: string | null;
  cycle_end?: string | null;
  reset_day?: number;
  timezone?: string;
  warning_ratio?: number;
  critical_ratio?: number;
  source: string;
};

export type ProviderQuotaConfig = {
  id: number;
  node_code: string;
  included_bytes: number;
  included_gb: number;
  reset_day: number;
  timezone: string;
  warning_ratio: number;
  critical_ratio: number;
  enabled: boolean;
  notes?: string | null;
  updated_by?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type FreeTierSummary = {
  free_users: number;
  sampled_users: number;
  limit_gb_per_user: number;
  cycle_days: number;
  used_gb: number;
  limit_gb_total: number;
  remaining_gb: number;
  used_pct: number;
  near_cap_users: number;
  over_cap_users: number;
  burn_rate_gb_per_day: number;
  source: string;
};

export type FreeTierUser = {
  tg_id: number;
  username?: string | null;
  display_name?: string | null;
  is_active: boolean;
  used_gb: number;
  limit_gb: number;
  remaining_gb: number;
  used_pct: number;
  state: string;
  cycle_start?: string | null;
  cycle_end?: string | null;
  source: string;
};

export type TrafficSummaryRow = {
  date: string;
  node_code: string;
  pool_code: string;
  traffic_bytes: number;
  traffic_gb: number;
  samples: number;
};

export type NodeTimeseriesRow = {
  sampled_at: string;
  node_code: string;
  source: string;
  cpu_percent?: number | null;
  memory_used_mb?: number | null;
  memory_total_mb?: number | null;
  disk_used_gb?: number | null;
  disk_total_gb?: number | null;
  network_rx_mbps?: number | null;
  network_tx_mbps?: number | null;
  network_total_mbps?: number | null;
  traffic_bytes_total?: number | null;
  active_clients?: number | null;
  score?: number | null;
  capacity_score?: number | null;
  capacity_state?: string | null;
};

export type OpsOverview = {
  ok: boolean;
  generated_at: string;
  summary: {
    users: {
      total: number;
      active: number;
      free: number;
      paid: number;
      trial?: number;
      pending?: number;
      unique_install_ids_24h?: number;
      unique_install_ids_7d?: number;
    };
    tickets: { open: number };
    nodes: { total: number; healthy: number };
    errors: Record<string, number | boolean>;
    observer?: { watch_users: number; suspicious_users: number };
  };
  metrics: {
    status: string;
    age_seconds?: number | null;
    alerts?: Record<string, number>;
    nodes: Array<Record<string, unknown>>;
  };
  capacity: {
    nodes: Array<Record<string, unknown>>;
  };
  free_tier: FreeTierSummary;
  provider_quotas: ProviderQuotaStatus[];
  alerts: {
    active: OpsAlert[];
    active_count: number;
    critical_count: number;
    warning_count: number;
  };
  recent_admin_events?: Array<Record<string, unknown>>;
};

export type AdminModulePayload = {
  section: string;
  rows: Array<Record<string, unknown>>;
  payload: Record<string, unknown>;
};

export type AdminUserRow = Record<string, unknown> & {
  tg_id: number;
  username?: string | null;
  display_name?: string | null;
  sub_type?: string | null;
  status?: string | null;
  origin?: string | null;
  expiry_at?: string | null;
  observer_state?: string | null;
};

export type AdminUsersPayload = {
  page: number;
  page_size: number;
  total: number;
  sort: string;
  users: AdminUserRow[];
};

export type AdminUserCardPayload = Record<string, unknown> & {
  user?: Record<string, unknown>;
  tickets?: Array<Record<string, unknown>>;
  key_policies?: Array<Record<string, unknown>>;
  key_history?: Array<Record<string, unknown>>;
  admin_actions?: Array<Record<string, unknown>>;
  payment_orders?: Array<Record<string, unknown>>;
  observer?: Record<string, unknown>;
  risk?: Record<string, unknown>;
  summary?: Record<string, unknown>;
  keys?: Array<Record<string, unknown>>;
  keys_state?: {
    summary?: Record<string, unknown>;
    keys?: Array<Record<string, unknown>>;
  };
};

export type NodeHealthRow = Record<string, unknown> & {
  code: string;
  name?: string | null;
  enabled?: boolean;
  accepting_new_clients?: boolean;
  is_draining?: boolean;
  is_healthy?: boolean;
  health_score?: number | null;
  capacity_state?: string | null;
  freshness_status?: string | null;
  online_keys_now?: number | null;
  online_connections_now?: number | null;
  panel_latency_ms?: number | null;
  dataplane_ok?: boolean | null;
  dataplane_rtt_ms?: number | null;
  ipv4_health?: string | null;
  ipv6_health?: string | null;
  observer_is_stale?: boolean | null;
};

export type NodeRuntimePayload = {
  ok: boolean;
  updated_at?: string;
  nodes: Array<Record<string, unknown>>;
};

export type OnlineUserRow = {
  row_id: string;
  tg_id?: number | null;
  username?: string | null;
  display_name?: string | null;
  sub_type?: string | null;
  status?: string | null;
  nodes_online?: string[];
  online_keys_now?: number;
  online_connections_now?: number;
  ip_count?: number;
  risk_flags?: string[];
  last_online_at?: string | null;
};

export type OnlineUsersPayload = {
  ok: boolean;
  generated_at?: string;
  rows: OnlineUserRow[];
  total: number;
  limit: number;
  summary: Record<string, unknown>;
  panel_errors?: Array<{ node_code: string | null; evidence_code: string }>;
  notes?: string[];
};

export type PaymentsSummaryPayload = {
  ok: boolean;
  period: Record<string, unknown>;
  revenue: {
    currency: string;
    paid_count: number;
    amount: number;
    by_currency?: Array<Record<string, unknown>>;
  };
  status_counts: Record<string, number>;
  attention: {
    pending_count: number;
    manual_review_count: number;
    failed_count: number;
    problem_count: number;
  };
  abandoned: Record<string, unknown>;
  problem_orders: Array<Record<string, unknown>>;
};

export type AdminSessionPayload = {
  ok: boolean;
  token: string;
  expires_in: number;
  user?: {
    id: number;
    username?: string | null;
    role?: string | null;
  };
};
