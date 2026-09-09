"use client";

import { AdminApiError, apiFetch, apiFetchBlob, type ApiRequestInit } from "./client";
import type { AdminV2Envelope } from "./types";

export type OnlineSourceFilter = "all" | "user" | "panel";

export type AdminOnlineUser = {
  rowId: string;
  tgId: number | null;
  username: string | null;
  displayName: string | null;
  plan: string | null;
  status: string;
  origin: string | null;
  source: "user" | "panel";
  nodesOnline: string[];
  onlineKeysNow: number;
  onlineConnectionsNow: number;
  connectionAddressCount: number;
  riskFlags: string[];
  lastOnlineAt: string | null;
  trafficGb24h: number;
  pressureScore: number;
};

export type AdminOnlinePayload = {
  generatedAt: string | null;
  total: number;
  limit: number;
  rows: AdminOnlineUser[];
  summary: {
    onlineIdentities: number;
    knownUsersOnline: number;
    unknownOnlineKeys: number;
    onlineKeysNow: number;
    onlineConnectionsNow: number;
    nodesWithPanelErrors: number;
  };
  panelErrors: Array<{ nodeCode: string | null; evidenceCode: string }>;
};

export type TicketStatusFilter = "active" | "open" | "in_progress" | "closed";
export type TicketPriority = "critical" | "high" | "normal" | "low";
export type TicketPriorityFilter = "all" | TicketPriority;

export type AdminTicketAttachment = {
  type: "image" | "file" | "video" | "audio" | "attachment";
  name: string | null;
  contentType: string | null;
  sizeBytes: number | null;
  downloadUrl: string | null;
};

export type AdminTicketMessage = {
  id: number;
  senderTgId: number | null;
  senderRole: "user" | "admin" | "assistant" | "unknown";
  visibility: "public" | "internal";
  macroCode: string | null;
  body: string;
  attachment: AdminTicketAttachment | null;
  createdAt: string | null;
};

export type AdminTicket = {
  id: number;
  userTgId: number;
  status: string;
  statusTitle: string;
  subject: string;
  priority: TicketPriority;
  queue: string;
  assignedAdminTgId: number | null;
  assignedTeam: string | null;
  waitingOn: string | null;
  slaDueAt: string | null;
  slaStatus: "ok" | "at_risk" | "breached" | "stopped" | "missing";
  escalatedAt: string | null;
  incidentId: string | null;
  attemptRef: string | null;
  version: number;
  createdAt: string | null;
  updatedAt: string | null;
  closedAt: string | null;
  lastMessagePreview: string;
  messages: AdminTicketMessage[];
  operatorPresence: "online" | "away" | "offline" | "unknown";
  unreadForUser: number;
  supportBundles: AdminSupportBundle[];
};

export type AdminSupportBundle = {
  bundleRef: string;
  attemptRef: string | null;
  attemptLinkSource: string | null;
  status: string;
  diagnosticProfile: string | null;
  appVersion: string | null;
  buildNumber: string | null;
  platform: string | null;
  architecture: string | null;
  lastPhase: string | null;
  lastErrorCode: string | null;
  proofOutcome: string | null;
  expiresAt: string | null;
  retentionHold: boolean;
  accessCount: number;
  lastAccessAction: string | null;
  lastAccessAt: string | null;
};

export type SupportMacro = { code: string; title: string; body: string };

export type SupportAttemptEvent = {
  eventId: number;
  eventName: string;
  fingerprint: string;
  result: string | null;
  subsystem: string | null;
  stage: string | null;
  errorCode: string | null;
  platform: string | null;
  appVersion: string | null;
  buildNumber: string | null;
  occurredAt: string | null;
  receivedAt: string | null;
};

export type SupportKnownIssue = {
  candidateLabel: string;
  issueCode: string;
  appVersion: string;
  buildNumber: string | null;
  platform: string;
  severity: string;
  status: string;
  title: string;
  safeSummary: string;
  errorCode: string;
  incidentRef: string | null;
  releaseRef: string | null;
  updatedAt: string | null;
};

export type SupportAttempt = {
  attemptRef: string;
  installationRef: string;
  sessionRef: string;
  startedAt: string | null;
  endedAt: string | null;
  outcome: string | null;
  eventCount: number;
  fingerprints: string[];
  events: SupportAttemptEvent[];
};

export type SupportAttemptExplorer = {
  tgId: number;
  ticketId: number | null;
  linkedAttemptRef: string | null;
  selected: SupportAttempt | null;
  attempts: SupportAttempt[];
  fingerprints: Array<{ fingerprint: string; count: number; platform: string | null; appVersion: string | null; subsystem: string | null; stage: string | null; result: string | null; errorCode: string | null }>;
};

export type SupportUser360 = {
  entity: { tgId: number; accountRef: string; username: string | null; displayName: string | null; status: string; plan: string | null; platform: string | null; appVersion: string | null; lastSeenAt: string | null };
  installations: Array<{ installationRef: string; attempts: number; sessions: number; lastSeenAt: string | null }>;
  sessions: Array<{ sessionRef: string; installationRef: string; attempts: number; lastSeenAt: string | null }>;
  attempts: SupportAttempt[];
  fingerprints: SupportAttemptExplorer["fingerprints"];
  observer: { authority: string; state: string; observedIpCount24h: number; observedNodeCount24h: number; lastObservedAt: string | null };
  fieldAccess: { supportDiagnostics: boolean };
  networkContext: Array<{ deviceRef: string; observedAt: string | null; originStatus: string; publicIp: string | null; networkClass: string; carrier: string | null; countryCode: string | null; region: string | null; platform: string | null; appVersion: string | null; runtimePhase: string | null }>;
};

export type AdminTicketsPayload = {
  tickets: AdminTicket[];
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

function mapOnlineUser(value: unknown, index: number): AdminOnlineUser {
  const row = record(value);
  const tgId = optionalNumber(row.tg_id);
  const lastOnlineAt = optionalText(row.last_online_at);
  return {
    rowId: text(row.row_id) || (tgId ? `user:${tgId}` : `panel:missing-${index}`),
    tgId,
    username: optionalText(row.username),
    displayName: optionalText(row.display_name),
    plan: optionalText(row.sub_type),
    status: text(row.status) || "unknown",
    origin: optionalText(row.origin),
    source: tgId ? "user" : "panel",
    nodesOnline: stringList(row.nodes_online),
    onlineKeysNow: number(row.online_keys_now),
    onlineConnectionsNow: number(row.online_connections_now),
    connectionAddressCount: number(row.ip_count),
    riskFlags: stringList(row.risk_flags),
    lastOnlineAt,
    trafficGb24h: number(row.traffic_gb_24h),
    pressureScore: number(row.pressure_score),
  };
}

export async function fetchOnlineUsers(
  params: { limit?: number; node?: string } = {},
  init?: ApiRequestInit,
): Promise<AdminOnlinePayload> {
  const query = new URLSearchParams();
  query.set("limit", String(Math.max(1, Math.min(Number(params.limit || 200), 500))));
  if (params.node?.trim()) query.set("only", params.node.trim().toLowerCase());
  const response = await apiFetch<AdminV2Envelope<Record<string, unknown>>>(`/api/admin/v2/support/online?${query.toString()}`, init);
  const payload = response.data;
  const generatedAt = optionalText(payload.generated_at);
  const summary = record(payload.summary);
  return {
    generatedAt,
    total: Math.max(0, number(payload.total)),
    limit: Math.max(1, number(payload.limit, params.limit || 200)),
    rows: records(payload.rows).map(mapOnlineUser),
    summary: {
      onlineIdentities: number(summary.online_identities),
      knownUsersOnline: number(summary.known_users_online),
      unknownOnlineKeys: number(summary.unknown_online_keys),
      onlineKeysNow: number(summary.online_keys_now),
      onlineConnectionsNow: number(summary.online_connections_now),
      nodesWithPanelErrors: number(summary.nodes_with_panel_errors),
    },
    panelErrors: records(payload.panel_errors).map((item) => ({
      nodeCode: optionalText(item.node_code),
      evidenceCode: text(item.evidence_code) || "panel_request_failed",
    })),
  };
}

function normalizedMessageRole(value: unknown): AdminTicketMessage["senderRole"] {
  const role = text(value).toLowerCase();
  return role === "user" || role === "admin" || role === "assistant" ? role : "unknown";
}

function normalizedMessageVisibility(value: unknown): AdminTicketMessage["visibility"] {
  return text(value).toLowerCase() === "internal" ? "internal" : "public";
}

function ticketPriority(status: string, updatedAt: string | null, explicit: unknown): TicketPriority {
  const configured = text(explicit).toLowerCase();
  if (configured === "critical" || configured === "high" || configured === "normal" || configured === "low") return configured;
  if (status === "closed") return "low";
  if (status === "in_progress") return "normal";
  if (updatedAt) {
    const timestamp = Date.parse(updatedAt);
    if (!Number.isNaN(timestamp) && Date.now() - timestamp >= 24 * 60 * 60 * 1000) return "critical";
  }
  return "high";
}

function mapTicketAttachment(value: unknown): AdminTicketAttachment | null {
  const row = record(value);
  if (!Object.keys(row).length) return null;
  const type = text(row.type).toLowerCase();
  const rawUrl = optionalText(row.download_url);
  const downloadUrl = rawUrl && /^\/api\/tickets\/attachments\/\d{8}-[A-Za-z0-9]{8,64}\.(?:png|jpg|jpeg|webp|pdf|txt)$/.test(rawUrl)
    ? rawUrl
    : null;
  const sizeBytes = optionalNumber(row.size_bytes);
  return {
    type: type === "image" || type === "file" || type === "video" || type === "audio" ? type : "attachment",
    name: optionalText(row.name),
    contentType: optionalText(row.content_type),
    sizeBytes: sizeBytes !== null && sizeBytes >= 0 ? sizeBytes : null,
    downloadUrl,
  };
}

function mapTicket(value: unknown): AdminTicket {
  const row = record(value);
  const status = text(row.status).toLowerCase() || "open";
  const updatedAt = optionalText(row.updated_at);
  const presence = text(row.operatorPresence).toLowerCase();
  return {
    id: positiveId(row.id),
    userTgId: signedUserId(row.user_tg_id),
    status,
    statusTitle: text(row.status_title) || (status === "closed" ? "Закрыт" : status === "in_progress" ? "В работе" : "Открыт"),
    subject: text(row.subject) || "Без темы",
    priority: ticketPriority(status, updatedAt, row.priority),
    queue: text(row.queue) || "general",
    assignedAdminTgId: optionalNumber(row.assigned_admin_tg_id),
    assignedTeam: optionalText(row.assigned_team),
    waitingOn: optionalText(row.waiting_on),
    slaDueAt: optionalText(row.sla_due_at),
    slaStatus: (["ok", "at_risk", "breached", "stopped", "missing"].includes(text(row.sla_status)) ? text(row.sla_status) : "missing") as AdminTicket["slaStatus"],
    escalatedAt: optionalText(row.escalated_at),
    incidentId: optionalText(row.incident_id),
    attemptRef: optionalText(row.attempt_ref),
    version: Math.max(1, number(row.version, 1)),
    createdAt: optionalText(row.created_at),
    updatedAt,
    closedAt: optionalText(row.closed_at),
    lastMessagePreview: text(row.last_message_preview),
    messages: records(row.messages).map((message) => ({
      id: positiveId(message.id),
      senderTgId: optionalNumber(message.sender_tg_id),
      senderRole: normalizedMessageRole(message.sender_role),
      visibility: normalizedMessageVisibility(message.visibility),
      macroCode: optionalText(message.macro_code),
      body: text(message.body),
      attachment: mapTicketAttachment(message.attachment),
      createdAt: optionalText(message.created_at),
    })).filter((message) => message.id > 0),
    operatorPresence: presence === "online" || presence === "away" || presence === "offline" ? presence : "unknown",
    unreadForUser: number(row.unreadForUser),
    supportBundles: records(row.support_bundles).map(mapSupportBundle),
  };
}

function mapSupportBundle(value: unknown): AdminSupportBundle {
  const row = record(value);
  const audit = record(row.access_audit);
  return {
    bundleRef: text(row.bundle_ref),
    attemptRef: optionalText(row.attempt_ref),
    attemptLinkSource: optionalText(row.attempt_link_source),
    status: text(row.status) || "unknown",
    diagnosticProfile: optionalText(row.diagnostic_profile),
    appVersion: optionalText(row.app_version),
    buildNumber: optionalText(row.build_number),
    platform: optionalText(row.platform),
    architecture: optionalText(row.architecture),
    lastPhase: optionalText(row.last_phase),
    lastErrorCode: optionalText(row.last_error_code),
    proofOutcome: optionalText(row.proof_outcome),
    expiresAt: optionalText(row.expires_at),
    retentionHold: Boolean(row.retention_hold),
    accessCount: Math.max(0, number(audit.count)),
    lastAccessAction: optionalText(audit.last_action),
    lastAccessAt: optionalText(audit.last_at),
  };
}

export async function fetchTickets(
  params: { status?: TicketStatusFilter; priority?: TicketPriorityFilter; queue?: string; assignment?: string; limit?: number } = {},
  init?: ApiRequestInit,
): Promise<AdminTicketsPayload> {
  const query = new URLSearchParams();
  query.set("status", params.status && params.status !== "active" ? params.status : "");
  if (params.priority && params.priority !== "all") query.set("priority", params.priority);
  if (params.queue && params.queue !== "all") query.set("queue", params.queue);
  if (params.assignment && params.assignment !== "all") query.set("assignment", params.assignment);
  query.set("limit", String(Math.max(1, Math.min(Number(params.limit || 100), 100))));
  const payload = await apiFetch<AdminV2Envelope<Record<string, unknown>>>(`/api/admin/v2/support/tickets?${query.toString()}`, init);
  return { tickets: records(payload.data.items).map(mapTicket).filter((ticket) => ticket.id > 0) };
}

export async function fetchTicketDetail(ticketId: number, init?: ApiRequestInit): Promise<AdminTicket> {
  const payload = await apiFetch<AdminV2Envelope<Record<string, unknown>>>(`/api/admin/v2/support/tickets/${encodeURIComponent(String(ticketId))}`, init);
  return mapTicket(payload.data);
}

export async function fetchSupportMacros(init?: ApiRequestInit): Promise<SupportMacro[]> {
  const payload = await apiFetch<AdminV2Envelope<Record<string, unknown>>>("/api/admin/v2/support/macros", init);
  return records(payload.data.items).map((row) => ({ code: text(row.code), title: text(row.title), body: text(row.body) })).filter((row) => row.code && row.title && row.body);
}

function mapAttempt(value: unknown): SupportAttempt {
  const row = record(value);
  return {
    attemptRef: text(row.attempt_ref),
    installationRef: text(row.installation_ref),
    sessionRef: text(row.session_ref),
    startedAt: optionalText(row.started_at),
    endedAt: optionalText(row.ended_at),
    outcome: optionalText(row.outcome),
    eventCount: Math.max(0, number(row.event_count)),
    fingerprints: stringList(row.fingerprints),
    events: records(row.events).map((event) => ({
      eventId: positiveId(event.event_id),
      eventName: text(event.event_name) || "unknown",
      fingerprint: text(event.fingerprint),
      result: optionalText(event.result),
      subsystem: optionalText(event.subsystem),
      stage: optionalText(event.stage),
      errorCode: optionalText(event.error_code),
      platform: optionalText(event.platform),
      appVersion: optionalText(event.app_version),
      buildNumber: optionalText(event.build_number),
      occurredAt: optionalText(event.occurred_at),
      receivedAt: optionalText(event.received_at),
    })),
  };
}

export async function fetchSupportAttempts(params: { ticketId?: number; tgId?: number; attemptRef?: string | null }, init?: ApiRequestInit): Promise<SupportAttemptExplorer> {
  const query = new URLSearchParams();
  if (params.ticketId) query.set("ticket_id", String(params.ticketId));
  if (params.tgId) query.set("tg_id", String(params.tgId));
  if (params.attemptRef) query.set("attempt_ref", params.attemptRef);
  const envelope = await apiFetch<AdminV2Envelope<Record<string, unknown>>>(`/api/admin/v2/support/attempts?${query.toString()}`, init);
  const payload = envelope.data;
  return {
    tgId: signedUserId(payload.tg_id),
    ticketId: optionalNumber(payload.ticket_id),
    linkedAttemptRef: optionalText(payload.linked_attempt_ref),
    selected: Object.keys(record(payload.selected)).length ? mapAttempt(payload.selected) : null,
    attempts: records(payload.attempts).map(mapAttempt).filter((row) => Boolean(row.attemptRef)),
    fingerprints: records(payload.fingerprints).map((row) => ({
      fingerprint: text(row.fingerprint), count: Math.max(0, number(row.count)), platform: optionalText(row.platform), appVersion: optionalText(row.app_version), subsystem: optionalText(row.subsystem), stage: optionalText(row.stage), result: optionalText(row.result), errorCode: optionalText(row.error_code),
    })).filter((row) => Boolean(row.fingerprint)),
  };
}

export async function fetchSupportUser360(tgId: number, init?: ApiRequestInit): Promise<SupportUser360> {
  const envelope = await apiFetch<AdminV2Envelope<Record<string, unknown>>>(`/api/admin/v2/support/users/${encodeURIComponent(String(tgId))}`, init);
  const payload = envelope.data;
  const entity = record(payload.entity);
  const observer = record(payload.observer);
  const fieldAccess = record(payload.field_access);
  const supportDiagnostics = record(fieldAccess.support_diagnostics);
  return {
    entity: {
      tgId: signedUserId(entity.tg_id) || tgId,
      accountRef: text(entity.account_ref),
      username: optionalText(entity.username),
      displayName: optionalText(entity.display_name),
      status: text(entity.status) || "unknown",
      plan: optionalText(entity.plan),
      platform: optionalText(entity.platform),
      appVersion: optionalText(entity.app_version),
      lastSeenAt: optionalText(entity.last_seen_at),
    },
    installations: records(payload.installations).map((row) => ({ installationRef: text(row.installation_ref), attempts: Math.max(0, number(row.attempts)), sessions: Math.max(0, number(row.sessions)), lastSeenAt: optionalText(row.last_seen_at) })).filter((row) => Boolean(row.installationRef)),
    sessions: records(payload.sessions).map((row) => ({ sessionRef: text(row.session_ref), installationRef: text(row.installation_ref), attempts: Math.max(0, number(row.attempts)), lastSeenAt: optionalText(row.last_seen_at) })).filter((row) => Boolean(row.sessionRef)),
    attempts: records(payload.attempts).map(mapAttempt).filter((row) => Boolean(row.attemptRef)),
    fingerprints: records(payload.fingerprints).map((row) => ({ fingerprint: text(row.fingerprint), count: Math.max(0, number(row.count)), platform: optionalText(row.platform), appVersion: optionalText(row.app_version), subsystem: optionalText(row.subsystem), stage: optionalText(row.stage), result: optionalText(row.result), errorCode: optionalText(row.error_code) })).filter((row) => Boolean(row.fingerprint)),
    observer: { authority: text(observer.authority), state: text(observer.state) || "missing", observedIpCount24h: Math.max(0, number(observer.observed_ip_count_24h)), observedNodeCount24h: Math.max(0, number(observer.observed_node_count_24h)), lastObservedAt: optionalText(observer.last_observed_at) },
    networkContext: text(supportDiagnostics.state) === "visible" ? records(payload.network_context).map((row) => ({ deviceRef: text(row.device_ref), observedAt: optionalText(row.observed_at), originStatus: text(row.origin_status) || "unavailable", publicIp: row.origin_status === "observed" ? optionalText(row.public_ip) : null, networkClass: text(row.network_class) || "unknown", carrier: optionalText(row.carrier), countryCode: optionalText(row.country_code), region: optionalText(row.region), platform: optionalText(row.platform), appVersion: optionalText(row.app_version), runtimePhase: optionalText(row.runtime_phase) })) : [],
    fieldAccess: { supportDiagnostics: text(supportDiagnostics.state) !== "redacted" },
  };
}

export async function fetchSupportKnownIssues(
  params: { errorCode?: string | null; appVersion?: string | null; buildNumber?: string | null; platform?: string | null },
  init?: ApiRequestInit,
): Promise<SupportKnownIssue[]> {
  const query = new URLSearchParams();
  if (params.errorCode) query.set("error_code", params.errorCode);
  if (params.appVersion) query.set("app_version", params.appVersion);
  if (params.buildNumber) query.set("build_number", params.buildNumber);
  if (params.platform) query.set("platform", params.platform.toLowerCase());
  const envelope = await apiFetch<AdminV2Envelope<Record<string, unknown>>>(`/api/admin/v2/support/known-issues?${query.toString()}`, init);
  return records(envelope.data.issues).map((row) => ({
    candidateLabel: text(row.candidate_label),
    issueCode: text(row.issue_code),
    appVersion: text(row.app_version),
    buildNumber: optionalText(row.build_number),
    platform: text(row.platform),
    severity: text(row.severity),
    status: text(row.status),
    title: text(row.title),
    safeSummary: text(row.safe_summary),
    errorCode: text(row.error_code),
    incidentRef: optionalText(row.incident_ref),
    releaseRef: optionalText(row.release_ref),
    updatedAt: optionalText(row.updated_at),
  })).filter((row) => Boolean(row.issueCode && row.errorCode));
}

export async function downloadSupportBundleCiphertext(
  ticketId: number,
  bundleRef: string,
  reasonCode: "customer_case" | "incident_review" | "release_validation" | "security_review",
): Promise<Blob> {
  const path = `/api/admin/v2/support/tickets/${encodeURIComponent(String(ticketId))}/bundles/${encodeURIComponent(bundleRef)}`;
  const grantEnvelope = await apiFetch<AdminV2Envelope<Record<string, unknown>>>(`${path}/access-grants`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason_code: reasonCode }),
  });
  const grant = text(grantEnvelope.data.access_grant);
  if (!grant) throw new AdminApiError("API не вернул одноразовый grant.", 502, "support_bundle_grant_missing", null);
  return apiFetchBlob(`${path}/content`, {
    method: "GET",
    headers: { "X-Pokrov-Support-Grant": grant },
  });
}

export function downloadAdminTicketAttachment(path: string, init?: ApiRequestInit): Promise<Blob> {
  if (!/^\/api\/tickets\/attachments\/\d{8}-[A-Za-z0-9]{8,64}\.(?:png|jpg|jpeg|webp|pdf|txt)$/.test(path)) {
    throw new AdminApiError("Ссылка вложения не прошла проверку безопасности.", 400, "unsafe_attachment_path", null);
  }
  return apiFetchBlob(path, { ...init, method: "GET" });
}
