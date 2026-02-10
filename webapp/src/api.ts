import { getInitData } from "./telegram";

export type NodeInfo = {
  code: string;
  name: string;
  host: string;
  port: number;
  enabled: boolean;
};

export type NodeStatus = {
  code: string;
  country: string;
  host: string;
  ping_ms?: number | null;
  port_open: boolean;
  dns_sni_status: string;
  is_healthy: boolean;
  updated_at?: string | null;
};

export type DashboardSnapshot = {
  tg_id: number;
  sub_type: string;
  segment?: string;
  is_active: boolean;
  expiry_at?: string | null;
  used_gb: number;
  total_gb: number;
  remaining_gb: number;
  active_sessions: number;
  device_limit: number;
  family_slots?: number;
  subscription_url: string;
  active_offer?: {
    id: number;
    offer_type: string;
    plan_code: string;
    price_stars: number;
    trigger_reason?: string | null;
    expires_at?: string | null;
    status: string;
  } | null;
  points?: {
    available: number;
    expiring_soon?: number;
    monthly_cap?: number;
    expires_days?: number;
  };
  features: {
    haptic: boolean;
    lottie: boolean;
  };
};

export type TicketMessage = {
  id: number;
  ticket_id: number;
  sender_tg_id: number;
  sender_role: "user" | "admin";
  body: string;
  media_type?: string | null;
  media_file_id?: string | null;
  media_payload?: string | null;
  created_at?: string | null;
};

export type TicketInfo = {
  id: number;
  user_tg_id: number;
  status: string;
  status_title: string;
  subject?: string | null;
  assigned_admin_tg_id?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
  closed_at?: string | null;
  last_message_preview?: string;
  messages: TicketMessage[];
};

export type UserPayload = {
  tg_id: number;
  username?: string | null;
  subscription_url: string;
  is_active: boolean;
  is_admin: boolean;
  sub_type: string;
  segment?: string;
  expiry_at: string | null;
  family_slots?: number;
  nodes: NodeInfo[];
  limits: {
    device_limit: number;
    total_gb: number;
  };
  traffic: {
    used_gb: number;
    total_gb: number;
    remaining_gb: number;
  };
  support: {
    username: string;
    link: string;
    new_ticket_link: string;
  };
  bonuses: {
    wheel: {
      last_spin_at: string | null;
      streak_months: number;
    };
    referral_count: number;
    channel_bonus?: {
      premium_days: number;
      claimed_at?: string | null;
      can_claim: boolean;
    };
  };
  referral: {
    code: string;
    link: string;
    bonus_days: number;
  };
  channel: {
    username: string;
    link: string;
  };
  actions: {
    open_helpbot: string;
    open_channel: string;
    pay_via_bot: string;
  };
  points?: {
    available: number;
    expiring_soon?: number;
    monthly_cap?: number;
    expires_days?: number;
  };
  active_offer?: {
    id: number;
    offer_type: string;
    plan_code: string;
    price_stars: number;
    trigger_reason?: string | null;
    expires_at?: string | null;
    status: string;
  } | null;
  features?: {
    haptic: boolean;
    lottie: boolean;
  };
};

export type PointsSnapshot = {
  tg_id: number;
  available_points: number;
  expiring_soon_points: number;
  monthly_cap: number;
  points_expiry_days: number;
  preview: {
    plan_price_stars: number;
    redeemable_points: number;
    max_points_by_plan_cap: number;
    max_points_by_total_cap: number;
  };
};

export type PayAttemptStartResult = {
  ok: boolean;
  attempt_id: number;
  plan_code: string;
  amount_stars: number;
  pay_url: string;
};

export type BonusPayload = {
  tg_id: number;
  referral_count: number;
  referral_code: string;
  referral_bonus_days: number;
  streak_months: number;
  last_wheel_spin: string | null;
  channel_bonus_premium_days?: number;
  channel_bonus_claimed_at?: string | null;
  channel_username?: string;
};

export type ReviewPayload = {
  username: string;
  rating: number;
  text: string;
  date: string;
};

export type AdminSummaryPayload = {
  actor_tg_id: number;
  users: { total: number; active: number; free: number; paid: number };
  tickets: { open: number };
  nodes: { total: number; healthy: number };
  top_nodes: Array<{
    code: string;
    health_score: number;
    panel_latency_ms?: number | null;
    active_clients: number;
    last_health_at?: string | null;
  }>;
};

export type AdminUserRow = {
  tg_id: number;
  username?: string | null;
  display_name?: string | null;
  sub_type: string;
  is_active: boolean;
  is_manual?: boolean;
  expiry_at?: string | null;
  stars_paid: number;
  created_at?: string | null;
};

export type AdminUserCard = {
  user: {
    tg_id: number;
    username?: string | null;
    display_name?: string | null;
    sub_type: string;
    is_active: boolean;
    is_manual?: boolean;
    expiry_at?: string | null;
    stars_paid: number;
    total_gb: number;
    trial_used: boolean;
    referral_count: number;
    streak_months: number;
    created_at?: string | null;
  };
  tickets: TicketInfo[];
};

export type AdminNodeHealthRow = {
  code: string;
  name: string;
  enabled: boolean;
  is_healthy: boolean;
  health_score: number;
  panel_latency_ms?: number | null;
  panel_error_rate: number;
  active_clients: number;
  last_ok_at?: string | null;
  last_health_at?: string | null;
  weight: number;
};

export type ManualCreateIn = {
  display_name: string;
  days: number;
};

function defaultApiBase(): string {
  if (typeof window !== "undefined") {
    return window.location.origin;
  }
  return "https://localhost:2096";
}

function candidateApiBases(): string[] {
  const envBase = (import.meta as any).env?.VITE_PUBLIC_API_BASE_URL as string | undefined;
  if (envBase) return [envBase];
  if (typeof window === "undefined") return [defaultApiBase()];

  const proto = window.location.protocol;
  const host = window.location.hostname;
  const origin = window.location.origin;
  const legacy = `${proto}//${host}:2096`;
  return [origin, legacy];
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const bases = candidateApiBases();
  let lastErr: any = null;
  for (const base of bases) {
    try {
      const headers = new Headers(init?.headers || {});
      headers.set("X-Telegram-Init-Data", getInitData());
      const r = await fetch(`${base}${path}`, { ...init, headers });
      if (!r.ok) {
        const text = await r.text();
        throw new Error(text || `API error: ${r.status}`);
      }
      if (r.status === 204) return {} as T;
      return (await r.json()) as T;
    } catch (e: any) {
      lastErr = e;
      const msg = String(e?.message || e);
      if (msg.includes("Failed to fetch") || msg.includes("NetworkError") || msg.includes("fetch")) {
        continue;
      }
      break;
    }
  }
  throw lastErr || new Error("API error");
}

export function fetchUser(tgId: number): Promise<UserPayload> {
  return apiFetch<UserPayload>(`/api/user/${tgId}`);
}

export function fetchDashboard(): Promise<DashboardSnapshot> {
  return apiFetch<DashboardSnapshot>("/api/dashboard");
}

export async function fetchNodeStatus(): Promise<NodeStatus[]> {
  const data = await apiFetch<{ nodes: NodeStatus[] }>("/api/nodes/status");
  return data.nodes || [];
}

export function runNodeDiagnostics(): Promise<{
  ok: boolean;
  checked_at: string;
  dns_status: string;
  sni_status: string;
  summary: string;
}> {
  return apiFetch("/api/nodes/diagnostics/run", { method: "POST" });
}

export async function fetchFeaturedReviews(): Promise<ReviewPayload[]> {
  const data = await apiFetch<{ reviews: ReviewPayload[] }>("/api/reviews", { method: "GET" });
  return data.reviews || [];
}

export async function createReview(rating: number, text: string): Promise<{ ok: boolean; review_id: number }> {
  return apiFetch<{ ok: boolean; review_id: number }>("/api/reviews", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rating, text }),
  });
}

export function fetchBonuses(): Promise<BonusPayload> {
  return apiFetch<BonusPayload>("/api/bonuses");
}

export function claimChannelBonus(): Promise<{
  ok: boolean;
  already_claimed: boolean;
  premium_days: number;
  claimed_at?: string | null;
  expiry_at?: string | null;
  sub_type?: string;
  channel?: string;
  sync_ok?: boolean;
}> {
  return apiFetch("/api/bonuses/channel/claim", { method: "POST" });
}

export function redeemPromo(code: string): Promise<any> {
  return apiFetch<any>("/api/promo/redeem", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
}

export async function fetchTickets(limit = 20): Promise<TicketInfo[]> {
  const data = await apiFetch<{ tickets: TicketInfo[] }>(`/api/tickets?limit=${limit}`);
  return data.tickets || [];
}

export async function createTicket(subject: string, body: string): Promise<TicketInfo> {
  const data = await apiFetch<{ ticket: TicketInfo }>("/api/tickets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ subject, body }),
  });
  return data.ticket;
}

export async function getTicket(ticketId: number): Promise<TicketInfo> {
  const data = await apiFetch<{ ticket: TicketInfo }>(`/api/tickets/${ticketId}`);
  return data.ticket;
}

export async function addTicketMessage(ticketId: number, body: string): Promise<TicketInfo> {
  const data = await apiFetch<{ ticket: TicketInfo }>(`/api/tickets/${ticketId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ body }),
  });
  return data.ticket;
}

export function trackEvent(event_name: string, source = "webapp", meta?: Record<string, unknown>, session_id?: string): Promise<{ ok: boolean; event_id?: number | null }> {
  return apiFetch("/api/events", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ event_name, source, meta: meta || {}, session_id: session_id || null }),
  });
}

export function startPayAttempt(plan_code: string, source = "webapp", offer_id?: number): Promise<PayAttemptStartResult> {
  return apiFetch("/api/pay/attempts/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ plan_code, source, offer_id: offer_id ?? null }),
  });
}

export function confirmConnect(): Promise<{ ok: boolean; event_id?: number | null }> {
  return apiFetch("/api/connect/confirm", { method: "POST" });
}

export function getActiveOffer(): Promise<{ offer: DashboardSnapshot["active_offer"] }> {
  return apiFetch("/api/offers/active");
}

export function acceptOffer(offer_id: number): Promise<{ ok: boolean }> {
  return apiFetch(`/api/offers/${offer_id}/accept`, { method: "POST" });
}

export function getPoints(): Promise<PointsSnapshot> {
  return apiFetch<PointsSnapshot>("/api/points");
}

export async function runNetworkProbe(size_mb = 2): Promise<{ latencyMs: number; downloadMs: number; quality: "good" | "fair" | "poor" }> {
  const start = performance.now();
  await apiFetch<any>("/api/health");
  const latencyMs = Math.max(1, Math.round(performance.now() - start));

  const dlStart = performance.now();
  const bases = candidateApiBases();
  let ok = false;
  for (const base of bases) {
    try {
      const headers = new Headers();
      headers.set("X-Telegram-Init-Data", getInitData());
      const resp = await fetch(`${base}/api/network/probe?size_mb=${Math.max(1, Math.min(3, size_mb))}`, { headers, cache: "no-store" });
      if (!resp.ok) throw new Error(`probe failed: ${resp.status}`);
      await resp.arrayBuffer();
      ok = true;
      break;
    } catch {
      // try next base
    }
  }
  if (!ok) throw new Error("Network probe failed");
  const downloadMs = Math.max(1, Math.round(performance.now() - dlStart));
  const quality: "good" | "fair" | "poor" =
    latencyMs < 180 && downloadMs < 1500 ? "good" : (latencyMs < 350 && downloadMs < 3000 ? "fair" : "poor");
  return { latencyMs, downloadMs, quality };
}

export function adminSummary(): Promise<AdminSummaryPayload> {
  return apiFetch<AdminSummaryPayload>("/api/admin/summary");
}

export async function adminUsers(q: string, limit = 50, offset = 0): Promise<AdminUserRow[]> {
  const query = encodeURIComponent(q || "");
  const data = await apiFetch<{ users: AdminUserRow[] }>(`/api/admin/users?q=${query}&limit=${limit}&offset=${offset}`);
  return data.users || [];
}

export function adminUserCard(tgId: number): Promise<AdminUserCard> {
  return apiFetch<AdminUserCard>(`/api/admin/users/${tgId}`);
}

export function adminUserMessage(tgId: number, text: string): Promise<{ ok: boolean }> {
  return apiFetch<{ ok: boolean }>(`/api/admin/users/${tgId}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

export function adminManualCreate(payload: ManualCreateIn): Promise<{
  ok: boolean;
  user: { tg_id: number; display_name?: string; sub_type: string; is_active: boolean; expiry_at?: string | null; subscription_url: string };
  sync_ok: boolean;
}> {
  return apiFetch("/api/admin/users/manual", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminManualExtend(tgId: number, days: number): Promise<{ ok: boolean; expiry_at: string }> {
  return apiFetch(`/api/admin/users/${tgId}/manual/extend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ days }),
  });
}

export function adminManualBlock(tgId: number, blocked: boolean): Promise<{ ok: boolean; is_active: boolean }> {
  return apiFetch(`/api/admin/users/${tgId}/manual/block`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ blocked }),
  });
}

export function adminManualRegenerateToken(tgId: number): Promise<{ ok: boolean; subscription_url: string }> {
  return apiFetch(`/api/admin/users/${tgId}/manual/regenerate-token`, { method: "POST" });
}

export function adminBroadcast(payload: {
  text: string;
  segment: string;
  limit: number;
  tg_ids?: number[];
}): Promise<any> {
  return apiFetch<any>("/api/admin/broadcast", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function adminTickets(status = "", limit = 30): Promise<TicketInfo[]> {
  const qs = `status=${encodeURIComponent(status)}&limit=${limit}`;
  const data = await apiFetch<{ tickets: TicketInfo[] }>(`/api/admin/tickets?${qs}`);
  return data.tickets || [];
}

export async function adminTicketReply(ticketId: number, body: string): Promise<TicketInfo> {
  const data = await apiFetch<{ ticket: TicketInfo }>(`/api/admin/tickets/${ticketId}/reply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ body }),
  });
  return data.ticket;
}

export async function adminTicketStatus(ticketId: number, status: string): Promise<TicketInfo> {
  const data = await apiFetch<{ ticket: TicketInfo }>(`/api/admin/tickets/${ticketId}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  return data.ticket;
}

export async function adminNodesHealth(): Promise<AdminNodeHealthRow[]> {
  const data = await apiFetch<{ nodes: AdminNodeHealthRow[] }>("/api/admin/nodes/health");
  return data.nodes || [];
}

export function adminNodesSync(payload: { tg_id?: number; segment?: string; limit?: number }): Promise<any> {
  return apiFetch<any>("/api/admin/nodes/sync", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
