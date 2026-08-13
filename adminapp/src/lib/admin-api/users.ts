"use client";

import { apiFetch, type ApiRequestInit } from "./client";

export type UserListStatus = "all" | "active" | "inactive" | "expired" | "blocked" | "manual";
export type UserListSort = "created_desc" | "created_asc" | "expiry_asc" | "expiry_desc" | "name_asc" | "name_desc";

export type AdminUserListRow = {
  tgId: number;
  username: string | null;
  displayName: string | null;
  plan: string | null;
  status: string;
  origin: string | null;
  isManual: boolean;
  expiryAt: string | null;
  createdAt: string | null;
  installId: string | null;
  deviceName: string | null;
  appPlatform: string | null;
  linkedTelegramUsername: string | null;
  observerState: string;
  observerUpdatedAt: string | null;
};

export type AdminUsersPage = {
  page: number;
  pageSize: number;
  total: number;
  sort: UserListSort;
  users: AdminUserListRow[];
};

export type AdminUserIdentity = AdminUserListRow & {
  isActive: boolean;
  effectiveActive: boolean;
  starsPaid: number;
  totalGb: number;
  trialUsed: boolean;
  referralCount: number;
  streakMonths: number;
  linkedTelegramId: number | null;
  appLastSeenAt: string | null;
};

export type AdminUserKey = {
  nodeCode: string;
  nodeName: string | null;
  exists: boolean | null;
  enabled: boolean | null;
  online: boolean | null;
  currentConnections: number | null;
  subIdMatches: boolean | null;
  totalGb: number | null;
  lastOnlineAt: string | null;
  lastOnlineAgeSeconds: number | null;
  panelState: "ok" | "error";
};

export type AdminUserSummary = {
  nodesTotal: number | null;
  nodesWithClient: number | null;
  nodesOnline: number | null;
  onlineKeysNow: number | null;
  onlineConnectionsNow: number | null;
  activeUsersEstimate: number | null;
  onlineNodeCodesNow: string[] | null;
  nodesEnabled: number | null;
  subIdMismatchCount: number | null;
  trafficTotalGb: number | null;
  panelState: "ok" | "partial" | "error" | "missing";
};

export type AdminUserObserverSummary = {
  state: string;
  reasons: string[];
  observedIpCount24h: number;
  observedIpCount7d: number;
  observedIpCount30d: number;
  observedNodeCount24h: number;
  observedNodeCount7d: number;
  observedNodeCount30d: number;
  overlapCount24h: number;
  lastObservedAt: string | null;
  updatedAt: string | null;
  recentNodes: Array<{
    nodeId: number | null;
    nodeCode: string | null;
    nodeName: string | null;
    lastSeenAt: string | null;
    scoreIpCount: number;
  }>;
};

export type AdminUserInvestigation = {
  tgId: number;
  generatedAt: string | null;
  observer: AdminUserObserverSummary & {
    recentIps: Array<{
      sourceIp: string;
      nodeCode: string | null;
      nodeName: string | null;
      lastSeenAt: string | null;
      countsForSuspicion: boolean;
    }>;
  };
};

export type AdminUserRisk = {
  score: number;
  level: string;
  windowDays: number;
  updatedAt: string | null;
  signals: {
    regenerationCount: number;
    keyActionCount: number;
    uniqueIpCount: number;
    observerState: string;
    trafficGb: number;
    subIdMismatchCount: number;
  };
  factors: Array<{ key: string; weight: number; value: string }>;
};

export type AdminUserTicketSummary = {
  id: number;
  status: string;
  statusTitle: string;
  subject: string;
  updatedAt: string | null;
  lastMessagePreview: string;
};

export type AdminUserPayment = {
  id: number;
  orderId: string;
  provider: string;
  planCode: string | null;
  amount: number;
  currency: string;
  status: string;
  createdAt: string | null;
  paidAt: string | null;
};

export type AdminUserAuditItem = {
  id: number;
  action: string;
  nodeCode: string | null;
  actorTgId: number | null;
  source: string | null;
  createdAt: string | null;
};

export type AdminUserDetail = {
  user: AdminUserIdentity;
  summary: AdminUserSummary;
  keys: AdminUserKey[];
  tickets: AdminUserTicketSummary[];
  payments: AdminUserPayment[];
  keyHistory: AdminUserAuditItem[];
  adminActions: AdminUserAuditItem[];
  observer: AdminUserObserverSummary;
  risk: AdminUserRisk;
};

function record(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function records(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? value.map(record) : [];
}

function text(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function optionalText(value: unknown): string | null {
  return text(value) || null;
}

function number(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function optionalNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function positiveId(value: unknown): number {
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed > 0 ? parsed : 0;
}

function signedUserId(value: unknown): number {
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed !== 0 ? parsed : 0;
}

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map(text).filter(Boolean) : [];
}

function mapUserRow(value: unknown): AdminUserListRow {
  const row = record(value);
  return {
    tgId: signedUserId(row.tg_id),
    username: optionalText(row.username),
    displayName: optionalText(row.display_name),
    plan: optionalText(row.sub_type),
    status: text(row.status) || "unknown",
    origin: optionalText(row.origin),
    isManual: Boolean(row.is_manual),
    expiryAt: optionalText(row.expiry_at),
    createdAt: optionalText(row.created_at),
    installId: optionalText(row.app_install_id),
    deviceName: optionalText(row.app_device_name),
    appPlatform: optionalText(row.app_platform),
    linkedTelegramUsername: optionalText(row.linked_telegram_username),
    observerState: text(row.observer_state) || "ok",
    observerUpdatedAt: optionalText(row.observer_updated_at),
  };
}

function mapIdentity(value: unknown): AdminUserIdentity {
  const row = record(value);
  return {
    ...mapUserRow(row),
    isActive: Boolean(row.is_active),
    effectiveActive: Boolean(row.effective_active),
    starsPaid: number(row.stars_paid),
    totalGb: number(row.total_gb),
    trialUsed: Boolean(row.trial_used),
    referralCount: number(row.referral_count),
    streakMonths: number(row.streak_months),
    linkedTelegramId: optionalNumber(row.linked_telegram_id),
    appLastSeenAt: optionalText(row.app_last_seen_at),
  };
}

function mapSummary(value: unknown): AdminUserSummary {
  const row = record(value);
  const panelState = text(row.panel_state);
  const panelComplete = panelState === "ok";
  const panelNumber = (field: unknown) => panelComplete ? optionalNumber(field) : null;
  return {
    nodesTotal: panelNumber(row.nodes_total),
    nodesWithClient: panelNumber(row.nodes_with_client),
    nodesOnline: panelNumber(row.nodes_online),
    onlineKeysNow: panelNumber(row.online_keys_now),
    onlineConnectionsNow: panelNumber(row.online_connections_now),
    activeUsersEstimate: panelNumber(row.active_users_estimate),
    onlineNodeCodesNow: panelComplete ? stringList(row.online_node_codes_now) : null,
    nodesEnabled: panelNumber(row.nodes_enabled),
    subIdMismatchCount: panelNumber(row.subid_mismatch_count),
    trafficTotalGb: panelNumber(row.traffic_total_gb),
    panelState: panelState === "ok" || panelState === "partial" || panelState === "error" ? panelState : "missing",
  };
}

function mapKey(value: unknown): AdminUserKey {
  const row = record(value);
  const panelState = text(row.panel_state) === "error" ? "error" : "ok";
  return {
    nodeCode: text(row.node_code),
    nodeName: optionalText(row.node_name),
    exists: panelState === "error" ? null : typeof row.exists === "boolean" ? row.exists : null,
    enabled: panelState === "error" ? null : typeof row.enabled === "boolean" ? row.enabled : null,
    online: typeof row.online === "boolean" ? row.online : null,
    currentConnections: panelState === "error" ? null : optionalNumber(row.current_connections),
    subIdMatches: panelState === "error" ? null : typeof row.sub_id_match === "boolean" ? row.sub_id_match : null,
    totalGb: panelState === "error" ? null : optionalNumber(row.total_gb),
    lastOnlineAt: optionalText(row.last_online_at),
    lastOnlineAgeSeconds: optionalNumber(row.last_online_age_seconds),
    panelState,
  };
}

function mapObserver(value: unknown): AdminUserObserverSummary {
  const row = record(value);
  return {
    state: text(row.state) || "ok",
    reasons: stringList(row.reasons),
    observedIpCount24h: number(row.observed_ip_count_24h),
    observedIpCount7d: number(row.observed_ip_count_7d),
    observedIpCount30d: number(row.observed_ip_count_30d),
    observedNodeCount24h: number(row.observed_node_count_24h),
    observedNodeCount7d: number(row.observed_node_count_7d),
    observedNodeCount30d: number(row.observed_node_count_30d),
    overlapCount24h: number(row.overlap_count_24h),
    lastObservedAt: optionalText(row.last_observed_at),
    updatedAt: optionalText(row.updated_at),
    recentNodes: records(row.recent_nodes).map((node) => ({
      nodeId: optionalNumber(node.node_id),
      nodeCode: optionalText(node.node_code),
      nodeName: optionalText(node.node_name),
      lastSeenAt: optionalText(node.last_seen_at),
      scoreIpCount: number(node.score_ip_count),
    })),
  };
}

function mapRisk(value: unknown): AdminUserRisk {
  const row = record(value);
  const signals = record(row.signals);
  return {
    score: number(row.score),
    level: text(row.level) || "low",
    windowDays: number(row.window_days, 30),
    updatedAt: optionalText(row.updated_at),
    signals: {
      regenerationCount: number(signals.regen_count),
      keyActionCount: number(signals.admin_key_ops),
      uniqueIpCount: number(signals.unique_ips),
      observerState: text(signals.observer_state) || "ok",
      trafficGb: number(signals.traffic_gb),
      subIdMismatchCount: number(signals.subid_mismatch_count),
    },
    factors: records(row.factors).map((factor) => ({
      key: text(factor.key),
      weight: number(factor.weight),
      value: String(factor.value ?? ""),
    })).filter((factor) => Boolean(factor.key)),
  };
}

function mapTicket(value: unknown): AdminUserTicketSummary {
  const row = record(value);
  return {
    id: positiveId(row.id),
    status: text(row.status) || "open",
    statusTitle: text(row.status_title) || "Открыт",
    subject: text(row.subject) || "Без темы",
    updatedAt: optionalText(row.updated_at),
    lastMessagePreview: text(row.last_message_preview),
  };
}

function mapPayment(value: unknown): AdminUserPayment {
  const row = record(value);
  return {
    id: positiveId(row.id),
    orderId: text(row.order_id),
    provider: text(row.provider) || "Не указан",
    planCode: optionalText(row.plan_code),
    amount: number(row.amount),
    currency: text(row.currency) || "RUB",
    status: text(row.status) || "unknown",
    createdAt: optionalText(row.created_at),
    paidAt: optionalText(row.paid_at),
  };
}

function mapAudit(value: unknown): AdminUserAuditItem {
  const row = record(value);
  return {
    id: positiveId(row.id),
    action: text(row.action) || "Действие без названия",
    nodeCode: optionalText(row.node_code),
    actorTgId: optionalNumber(row.actor_tg_id),
    source: optionalText(row.source),
    createdAt: optionalText(row.created_at),
  };
}

export async function fetchUsers(
  params: { q?: string; status?: UserListStatus; sort?: UserListSort; limit?: number; offset?: number } = {},
  init?: ApiRequestInit,
): Promise<AdminUsersPage> {
  const query = new URLSearchParams();
  query.set("page_size", String(Math.max(1, Math.min(Number(params.limit || 80), 200))));
  query.set("offset", String(Math.max(0, Number(params.offset || 0))));
  if (params.q?.trim()) query.set("q", params.q.trim());
  if (params.status && params.status !== "all") query.set("status", params.status);
  query.set("sort", params.sort || "created_desc");
  const payload = await apiFetch<Record<string, unknown>>(`/api/admin/users?${query.toString()}`, init);
  const sort = text(payload.sort) as UserListSort;
  return {
    page: Math.max(1, number(payload.page, 1)),
    pageSize: Math.max(1, number(payload.page_size, 80)),
    total: Math.max(0, number(payload.total)),
    sort: ["created_desc", "created_asc", "expiry_asc", "expiry_desc", "name_asc", "name_desc"].includes(sort) ? sort : "created_desc",
    users: records(payload.users).map(mapUserRow).filter((row) => row.tgId !== 0),
  };
}

export async function fetchUserDetail(tgId: number, init?: ApiRequestInit): Promise<AdminUserDetail> {
  const payload = await apiFetch<Record<string, unknown>>(`/api/admin/users/${encodeURIComponent(String(tgId))}`, init);
  const keysState = record(payload.keys_state);
  const user = mapIdentity(payload.user);
  return {
    user,
    summary: mapSummary(payload.summary ?? keysState.summary),
    keys: records(payload.keys ?? keysState.keys).map(mapKey).filter((key) => Boolean(key.nodeCode)),
    tickets: records(payload.tickets).map(mapTicket).filter((ticket) => ticket.id > 0),
    payments: records(payload.payment_orders).map(mapPayment).filter((payment) => payment.id > 0),
    keyHistory: records(payload.key_history).map(mapAudit).filter((item) => item.id > 0),
    adminActions: records(payload.admin_actions).map(mapAudit).filter((item) => item.id > 0),
    observer: mapObserver(payload.observer),
    risk: mapRisk(payload.risk),
  };
}

export async function fetchUserInvestigation(tgId: number, init?: ApiRequestInit): Promise<AdminUserInvestigation> {
  const payload = await apiFetch<Record<string, unknown>>(`/api/admin/users/${encodeURIComponent(String(tgId))}/investigation`, init);
  const observerRaw = record(payload.observer);
  return {
    tgId: signedUserId(payload.tg_id) || tgId,
    generatedAt: optionalText(payload.generated_at),
    observer: {
      ...mapObserver(observerRaw),
      recentIps: records(observerRaw.recent_ips).map((item) => ({
        sourceIp: text(item.source_ip_raw),
        nodeCode: optionalText(item.node_code),
        nodeName: optionalText(item.node_name),
        lastSeenAt: optionalText(item.last_seen_at),
        countsForSuspicion: Boolean(item.counts_for_suspicion),
      })).filter((item) => Boolean(item.sourceIp)),
    },
  };
}
