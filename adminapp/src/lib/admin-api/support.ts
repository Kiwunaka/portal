"use client";

import { AdminApiError, apiFetch, apiFetchBlob, type ApiRequestInit } from "./client";

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
  createdAt: string | null;
  updatedAt: string | null;
  closedAt: string | null;
  lastMessagePreview: string;
  messages: AdminTicketMessage[];
  operatorPresence: "online" | "away" | "offline" | "unknown";
  unreadForUser: number;
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
  const payload = await apiFetch<Record<string, unknown>>(`/api/admin/online/users?${query.toString()}`, init);
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
    createdAt: optionalText(row.created_at),
    updatedAt,
    closedAt: optionalText(row.closed_at),
    lastMessagePreview: text(row.last_message_preview),
    messages: records(row.messages).map((message) => ({
      id: positiveId(message.id),
      senderTgId: optionalNumber(message.sender_tg_id),
      senderRole: normalizedMessageRole(message.sender_role),
      body: text(message.body),
      attachment: mapTicketAttachment(message.attachment),
      createdAt: optionalText(message.created_at),
    })).filter((message) => message.id > 0),
    operatorPresence: presence === "online" || presence === "away" || presence === "offline" ? presence : "unknown",
    unreadForUser: number(row.unreadForUser),
  };
}

export async function fetchTickets(
  params: { status?: TicketStatusFilter; limit?: number } = {},
  init?: ApiRequestInit,
): Promise<AdminTicketsPayload> {
  const query = new URLSearchParams();
  query.set("status", params.status && params.status !== "active" ? params.status : "");
  query.set("limit", String(Math.max(1, Math.min(Number(params.limit || 100), 100))));
  const payload = await apiFetch<Record<string, unknown>>(`/api/admin/tickets?${query.toString()}`, init);
  return { tickets: records(payload.tickets).map(mapTicket).filter((ticket) => ticket.id > 0) };
}

export async function fetchTicketDetail(ticketId: number, init?: ApiRequestInit): Promise<AdminTicket> {
  const payload = await apiFetch<Record<string, unknown>>(`/api/admin/tickets/${encodeURIComponent(String(ticketId))}`, init);
  return mapTicket(payload.ticket);
}

export function downloadAdminTicketAttachment(path: string, init?: ApiRequestInit): Promise<Blob> {
  if (!/^\/api\/tickets\/attachments\/\d{8}-[A-Za-z0-9]{8,64}\.(?:png|jpg|jpeg|webp|pdf|txt)$/.test(path)) {
    throw new AdminApiError("Ссылка вложения не прошла проверку безопасности.", 400, "unsafe_attachment_path", null);
  }
  return apiFetchBlob(path, { ...init, method: "GET" });
}
