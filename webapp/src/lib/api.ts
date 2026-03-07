/* eslint-disable @typescript-eslint/no-explicit-any */
import { getInitData } from "./telegram";

const WEB_SESSION_TOKEN_KEY = "portal_web_session_token";

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

export type ClientPlatformAndroidApps = {
  play_url: string;
  apk_url: string;
  mirror_url: string;
};

export type ClientPlatformWindowsApps = {
  exe_url: string;
  mirror_url: string;
};

export type ClientAppsPayload = {
  android: ClientPlatformAndroidApps;
  windows: ClientPlatformWindowsApps;
  docs_url: string;
  updated_at: string;
};

export type DashboardSnapshot = {
  tg_id: number;
  sub_type: string;
  current_plan_code?: string | null;
  segment?: string;
  is_active: boolean;
  expiry_at?: string | null;
  used_gb: number;
  total_gb: number;
  remaining_gb: number;
  active_sessions: number;
  device_limit: number;
  speed_limit_mbps?: number | null;
  free_next_reset_at?: string | null;
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
    speed_mbps?: number | null;
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
    subscriber?: boolean;
    speed_bump_active?: boolean;
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
  free_cycle?: {
    next_reset_at?: string | null;
  };
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

export type RubCheckoutStartResult = {
  ok: boolean;
  order_id: string;
  payment_url?: string | null;
  amount_rub: number;
  currency: string;
  status: string;
  widget_enabled?: boolean;
  discount_applied?: boolean;
  base_amount_rub?: number | null;
  discount_pct?: number;
};

export type PlanCatalogRow = {
  code: string;
  label: string;
  amount_rub: number;
  amount_stars: number;
  days: number;
  device_limit: number;
  node_policy?: string | null;
  badge?: string | null;
  is_active: boolean;
  sort_order: number;
  created_at?: string | null;
  updated_at?: string | null;
};

export type LiveUpdateRow = {
  id: number;
  title: string;
  summary: string;
  link: string;
  date?: string;
  published_at?: string | null;
  is_active?: boolean;
  sort_order?: number;
  created_at?: string | null;
  updated_at?: string | null;
};

export type CampaignLinksBuildResult = {
  ok: boolean;
  bot_start_link: string;
  checkout_link: string;
  webapp_link: string;
  checkout_mode?: string;
  checkout_reason?: string;
};

export type PublicPlansPayload = {
  plans: PlanCatalogRow[];
  widget_enabled: boolean;
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
  retention: {
    expiring_3d: number;
    expired_7d: number;
    reactivation_candidates: number;
    pings_24h: {
      welcome: number;
      t3: number;
      t1: number;
      t0: number;
      reactivation: number;
      start99_offer: number;
    };
  };
  tickets: { open: number };
  nodes: { total: number; healthy: number };
  errors: {
    stale_metrics: boolean;
    unhealthy_nodes: number;
    open_tickets: number;
    payment_callback_failures_24h: number;
    subscription_numeric_fallbacks_24h: number;
  };
  resilience: {
    single_point_risk: boolean;
    free_node_enabled: boolean;
  };
  bonus_events_24h: {
    channel_activated: number;
    channel_denied: number;
    promo_redeemed: number;
    promo_denied: number;
    gift_redeemed: number;
    gift_denied: number;
  };
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
    subscription_url?: string;
    subscription_token?: string;
  };
  tickets: TicketInfo[];
  keys?: AdminUserKey[];
  key_history?: AdminUserKeyHistoryRow[];
  key_policies?: AdminUserKeyPolicy[];
  admin_actions?: AdminAuditRow[];
  risk?: AdminUserRisk;
  loyalty?: AdminUserLoyalty;
  summary?: {
    nodes_total: number;
    nodes_with_client: number;
    nodes_online: number;
    nodes_enabled: number;
    subid_mismatch_count: number;
    traffic_up_bytes: number;
    traffic_down_bytes: number;
    traffic_total_bytes: number;
    traffic_total_gb: number;
    panel_state?: "ok" | "error" | string;
    panel_error?: string | null;
  };
};

export type AdminUserKey = {
  node_code: string;
  node_name?: string;
  node_host?: string;
  exists: boolean;
  client_uuid?: string;
  panel_email?: string;
  enabled: boolean;
  online?: boolean | null;
  sub_id?: string;
  expected_sub_id?: string;
  sub_id_match?: boolean;
  up_bytes: number;
  down_bytes: number;
  total_bytes: number;
  total_gb: number;
  last_online_at?: string | null;
  last_online_age_seconds?: number | null;
  vless_link?: string;
  panel_error?: string | null;
  policy?: AdminUserKeyPolicy | null;
};

export type AdminUserKeyHistoryRow = {
  id: number;
  tg_id?: number;
  node_code?: string | null;
  action: string;
  actor_tg_id?: number | null;
  source?: string;
  meta?: Record<string, unknown>;
  created_at?: string | null;
};

export type AdminUserKeyPolicy = {
  node_code: string;
  burst_mbps?: number | null;
  soft_cap_gb?: number | null;
  hard_cap_gb?: number | null;
  notify_soft: boolean;
  notify_hard: boolean;
  auto_disable_on_hard: boolean;
  updated_by?: number | null;
  updated_at?: string | null;
};

export type AdminUserRisk = {
  score: number;
  level: "low" | "medium" | "high" | "critical" | string;
  window_days: number;
  signals: {
    regen_count: number;
    admin_key_ops: number;
    unique_ips: number;
    traffic_gb: number;
    subid_mismatch_count: number;
  };
  factors: Array<{ key: string; weight: number; value: number | string }>;
  updated_at?: string | null;
};

export type AdminUserLoyalty = {
  enabled: boolean;
  streak_days: number;
  tiers: Array<{
    days: number;
    bonus_days: number;
    perk: string;
    unlocked: boolean;
    claimed: boolean;
    reward_key: string;
  }>;
};

export type AdminAuditRow = {
  id: number;
  actor_tg_id: number;
  action: string;
  target_tg_id?: number | null;
  meta?: Record<string, unknown>;
  created_at?: string | null;
};

export type AdminReferralQueueRow = {
  id: number;
  order_id: string;
  referrer_tg_id: number;
  referred_tg_id: number;
  queued_at?: string | null;
  ready_at?: string | null;
  status: string;
  processed_at?: string | null;
  meta?: Record<string, unknown>;
};

export type AdminIncentiveCampaign = {
  id: number;
  name: string;
  campaign_type: "promo" | "gift" | string;
  target_value: string;
  segment: string;
  starts_at?: string | null;
  ends_at?: string | null;
  max_activations: number;
  activations_count: number;
  auto_disable: boolean;
  is_active: boolean;
  created_by?: number | null;
  metadata?: Record<string, unknown>;
  created_at?: string | null;
  updated_at?: string | null;
};

export type AdminLoyaltyConfig = {
  enabled: boolean;
  tiers: Array<{ days: number; bonus_days: number; perk: string }>;
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

export type AdminMetricsStatus = {
  status: "fresh" | "stale";
  last_sample_at?: string | null;
  age_seconds?: number | null;
  stale_after_seconds: number;
};

export type AdminMetricsPoint = {
  date: string;
  registrations: number;
  churn: number;
  revenue_stars: number;
  revenue_rub: number;
  nodes: Record<
    string,
    {
      devices: number;
      traffic_bytes: number;
      traffic_gb: number;
    }
  >;
};

export type AdminMetricsTimeseries = {
  from: string;
  to: string;
  points: AdminMetricsPoint[];
};

export type AdminNodeTrafficRow = {
  date: string;
  node_code: string;
  devices: number;
  traffic_bytes: number;
  traffic_gb: number;
};

export type AdminStartLinkRow = {
  id: number;
  code: string;
  description?: string | null;
  target_action?: string | null;
  is_active: boolean;
  bot_start_link: string;
  created_at?: string | null;
  updated_at?: string | null;
};

export type AdminWheelConfig = {
  preset: string;
  cooldown_hours: number;
  weights: Array<{
    days: number;
    weight: number;
  }>;
};

export type AdminPromoRow = {
  code: string;
  promo_type: "discount" | "days" | string;
  value: number;
  uses_left: number;
  used_count: number;
  expires_at?: string | null;
  created_at?: string | null;
};

export type AdminTemplateRow = {
  key: string;
  text: string;
  created_at?: string | null;
};

export type AdminGiftCodeRow = {
  code: string;
  card_type: string;
  days: number;
  stars: number;
  created_by: number;
  created_at?: string | null;
  redeemed_by?: number | null;
  redeemed_at?: string | null;
};

export type ManualCreateIn = {
  display_name: string;
  days: number;
};

export type TicketAttachmentInput = {
  media_type?: string | null;
  media_file_id?: string | null;
  media_payload?: string | null;
};

export type TicketAttachmentPayload = {
  url: string;
  name: string;
  content_type: string;
  size: number;
};

export type TicketAttachmentUploadResult = {
  ok: boolean;
  attachment: TicketAttachmentInput;
  attachment_payload: TicketAttachmentPayload;
};

export type TelegramWebLoginPayload = {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
};

export type WebLoginResult = {
  ok: boolean;
  token: string;
  user: { id: number; username?: string | null };
  expires_in: number;
};

function getWebSessionToken(): string {
  if (typeof window === "undefined") return "";
  return String(window.localStorage.getItem(WEB_SESSION_TOKEN_KEY) || "").trim();
}

function applyAuthHeaders(headers: Headers): void {
  const initData = getInitData();
  const token = getWebSessionToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
    headers.set("X-Web-Auth-Token", token);
  }
  if (initData) {
    headers.set("X-Telegram-Init-Data", initData);
  }
}

export function hasWebSessionToken(): boolean {
  return getWebSessionToken().length > 0;
}

export function setWebSessionToken(token: string): void {
  if (typeof window === "undefined") return;
  const value = String(token || "").trim();
  if (!value) return;
  window.localStorage.setItem(WEB_SESSION_TOKEN_KEY, value);
}

export function consumeWebSessionTokenFromUrl(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const current = new URL(window.location.href);
    const token = String(
      current.searchParams.get("web_session_token") || current.searchParams.get("web_session") || "",
    ).trim();
    if (!token) return false;

    setWebSessionToken(token);
    current.searchParams.delete("web_session_token");
    current.searchParams.delete("web_session");
    const next = `${current.pathname}${current.search}${current.hash}`;
    window.history.replaceState({}, "", next || "/");
    return true;
  } catch {
    return false;
  }
}

export function clearWebSessionToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(WEB_SESSION_TOKEN_KEY);
}

function defaultApiBase(): string {
  if (typeof window !== "undefined") {
    return window.location.origin;
  }
  return "https://portal-privacy.online";
}

function candidateApiBases(): string[] {
  const envBaseRaw = (
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.NEXT_PUBLIC_PUBLIC_API_BASE_URL ||
    process.env.VITE_PUBLIC_API_BASE_URL ||
    ""
  ).trim();
  if (envBaseRaw) return [envBaseRaw.replace(/\/+$/, "")];
  if (typeof window === "undefined") return [defaultApiBase().replace(/\/+$/, ""), "https://kiwunaka.space"];

  const origin = window.location.origin.replace(/\/+$/, "");
  const proto = window.location.protocol;
  const host = window.location.hostname;
  const legacy = `${proto}//${host}:2096`;
  const useLegacyFallback =
    String(process.env.NEXT_PUBLIC_ENABLE_LEGACY_PORT_FALLBACK || process.env.VITE_ENABLE_LEGACY_PORT_FALLBACK || "")
      .toLowerCase() === "true";
  const defaults = [origin, "https://kiwunaka.space"];
  if (useLegacyFallback) defaults.push(legacy.replace(/\/+$/, ""));
  return Array.from(new Set(defaults));
}

export function resolveApiUrl(path: string): string {
  const raw = String(path || "").trim();
  if (!raw) return "";
  if (/^https?:\/\//i.test(raw)) return raw;
  const normalizedPath = raw.startsWith("/") ? raw : `/${raw}`;
  const [base] = candidateApiBases();
  return `${base}${normalizedPath}`;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const bases = candidateApiBases();
  let lastErr: any = null;
  for (const base of bases) {
    try {
      const headers = new Headers(init?.headers || {});
      applyAuthHeaders(headers);
      const r = await fetch(`${base}${path}`, { ...init, headers });
      if (!r.ok) {
        const text = await r.text();
        if (r.status === 401 && !getInitData() && getWebSessionToken()) {
          clearWebSessionToken();
        }
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

export function fetchPublicPlans(): Promise<PublicPlansPayload> {
  return apiFetch<PublicPlansPayload>("/api/public/plans");
}

export async function fetchPublicLiveUpdates(limit = 3): Promise<LiveUpdateRow[]> {
  const data = await apiFetch<{ updates: LiveUpdateRow[] }>(`/api/public/live-updates?limit=${Math.max(1, Math.min(10, limit))}`);
  return data.updates || [];
}

export function fetchDashboard(): Promise<DashboardSnapshot> {
  return apiFetch<DashboardSnapshot>("/api/dashboard");
}

export async function fetchNodeStatus(): Promise<NodeStatus[]> {
  const data = await apiFetch<{ nodes: NodeStatus[] }>("/api/nodes/status");
  return data.nodes || [];
}

export function fetchClientApps(): Promise<ClientAppsPayload> {
  return apiFetch<ClientAppsPayload>("/api/client/apps");
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

export function redeemGiftCode(code: string): Promise<any> {
  return apiFetch<any>("/api/gift/redeem", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
}

export async function authByTelegramWebLogin(payload: TelegramWebLoginPayload): Promise<WebLoginResult> {
  const bases = candidateApiBases();
  let lastErr: any = null;
  for (const base of bases) {
    try {
      const r = await fetch(`${base}/api/auth/telegram/web-login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!r.ok) {
        const text = await r.text();
        throw new Error(text || `API error: ${r.status}`);
      }
      return (await r.json()) as WebLoginResult;
    } catch (e: any) {
      lastErr = e;
    }
  }
  throw lastErr || new Error("API error");
}

export async function fetchTickets(limit = 20): Promise<TicketInfo[]> {
  const data = await apiFetch<{ tickets: TicketInfo[] }>(`/api/tickets?limit=${limit}`);
  return data.tickets || [];
}

export async function createTicket(subject: string, body: string, attachment?: TicketAttachmentInput): Promise<TicketInfo> {
  const data = await apiFetch<{ ticket: TicketInfo }>("/api/tickets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      subject,
      body,
      media_type: attachment?.media_type ?? null,
      media_file_id: attachment?.media_file_id ?? null,
      media_payload: attachment?.media_payload ?? null,
    }),
  });
  return data.ticket;
}

export async function uploadTicketAttachment(file: File): Promise<TicketAttachmentUploadResult> {
  return apiFetch<TicketAttachmentUploadResult>("/api/tickets/uploads", {
    method: "POST",
    headers: {
      "Content-Type": file.type || "application/octet-stream",
      "X-Upload-Filename": file.name || "attachment.bin",
    },
    body: file,
  });
}

export async function getTicket(ticketId: number): Promise<TicketInfo> {
  const data = await apiFetch<{ ticket: TicketInfo }>(`/api/tickets/${ticketId}`);
  return data.ticket;
}

export async function addTicketMessage(ticketId: number, body: string, attachment?: TicketAttachmentInput): Promise<TicketInfo> {
  const data = await apiFetch<{ ticket: TicketInfo }>(`/api/tickets/${ticketId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      body,
      media_type: attachment?.media_type ?? null,
      media_file_id: attachment?.media_file_id ?? null,
      media_payload: attachment?.media_payload ?? null,
    }),
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

export function createRubCheckoutOrder(payload: {
  plan_code: string;
  source?: "site" | "bot";
  tg_id?: number;
  campaign?: string;
  promo_code?: string;
  currency?: string;
}): Promise<RubCheckoutStartResult> {
  return apiFetch("/api/payments/freekassa/orders/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function createPublicRubCheckoutOrder(payload: {
  plan_code: string;
  checkout_ticket: string;
  currency?: string;
}): Promise<RubCheckoutStartResult> {
  return apiFetch("/api/payments/freekassa/orders/create-public", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function checkChannelSubscriberStatus(): Promise<{
  ok: boolean;
  subscriber: boolean;
  reason?: string;
  points_granted?: number;
  campaign_marked?: boolean;
}> {
  return apiFetch("/api/channel/subscriber/check", { method: "POST" });
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
      applyAuthHeaders(headers);
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

export async function adminUserKeyHistory(tgId: number, limit = 100): Promise<AdminUserKeyHistoryRow[]> {
  const data = await apiFetch<{ rows: AdminUserKeyHistoryRow[] }>(`/api/admin/users/${tgId}/key-history?limit=${Math.max(1, Math.min(500, limit))}`);
  return data.rows || [];
}

export async function adminUserKeyLimits(tgId: number): Promise<AdminUserKeyPolicy[]> {
  const data = await apiFetch<{ limits: AdminUserKeyPolicy[] }>(`/api/admin/users/${tgId}/key-limits`);
  return data.limits || [];
}

export function adminUserKeyLimitUpdate(
  tgId: number,
  nodeCode: string,
  payload: {
    burst_mbps?: number | null;
    soft_cap_gb?: number | null;
    hard_cap_gb?: number | null;
    notify_soft?: boolean;
    notify_hard?: boolean;
    auto_disable_on_hard?: boolean;
    apply_now?: boolean;
  },
): Promise<{ ok: boolean; policy?: AdminUserKeyPolicy; applied?: boolean | null }> {
  return apiFetch(`/api/admin/users/${tgId}/key-limits/${encodeURIComponent(nodeCode)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminBulkKeyAction(payload: {
  action: "disable" | "enable" | "reset" | "resync";
  segment: string;
  node_codes?: string[];
  tg_ids?: number[];
  q?: string;
  limit?: number;
  dry_run?: boolean;
  force?: boolean;
}): Promise<any> {
  return apiFetch("/api/admin/users/keys/bulk-action", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminUserRisk(tgId: number): Promise<{ risk: AdminUserRisk }> {
  return apiFetch(`/api/admin/users/${tgId}/risk`);
}

export function adminUserLoyalty(tgId: number): Promise<{ loyalty: AdminUserLoyalty }> {
  return apiFetch(`/api/admin/users/${tgId}/loyalty`);
}

export function adminUserLoyaltyGrant(tgId: number, tierDays: number): Promise<{ ok: boolean; tier_days: number; expiry_at?: string | null; sync_ok?: boolean }> {
  return apiFetch(`/api/admin/users/${tgId}/loyalty/grant`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tier_days: tierDays }),
  });
}

export function adminUserPresetRun(
  tgId: number,
  preset: "reset_key" | "rotate_link" | "extend_1d" | "send_guide",
): Promise<{ ok: boolean; preset: string; changed?: number; failed?: number; subscription_url?: string }> {
  return apiFetch(`/api/admin/users/${tgId}/presets/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preset }),
  });
}

export async function adminAuditLog(params?: { limit?: number; offset?: number; action?: string; target_tg_id?: number }): Promise<AdminAuditRow[]> {
  const q = new URLSearchParams();
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.offset != null) q.set("offset", String(params.offset));
  if (params?.action) q.set("action", params.action);
  if (params?.target_tg_id != null) q.set("target_tg_id", String(params.target_tg_id));
  const data = await apiFetch<{ rows: AdminAuditRow[] }>(`/api/admin/audit${q.toString() ? `?${q.toString()}` : ""}`);
  return data.rows || [];
}

export async function adminReferralQueue(limit = 200, status = ""): Promise<AdminReferralQueueRow[]> {
  const qs = `limit=${Math.max(1, Math.min(1000, limit))}&status=${encodeURIComponent(status || "")}`;
  const data = await apiFetch<{ rows: AdminReferralQueueRow[] }>(`/api/admin/referrals/pending?${qs}`);
  return data.rows || [];
}

export function adminReferralProcess(payload: { limit?: number; force_without_activity?: boolean }): Promise<{ ok: boolean; processed: number; rewarded: number; waiting: number; rejected: number }> {
  return apiFetch("/api/admin/referrals/process", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminLoyaltyConfig(): Promise<{ loyalty_config: AdminLoyaltyConfig }> {
  return apiFetch("/api/admin/loyalty-config");
}

export function adminLoyaltyConfigUpdate(payload: AdminLoyaltyConfig): Promise<{ ok: boolean; loyalty_config: AdminLoyaltyConfig }> {
  return apiFetch("/api/admin/loyalty-config", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function adminCampaigns(limit = 200): Promise<AdminIncentiveCampaign[]> {
  const data = await apiFetch<{ campaigns: AdminIncentiveCampaign[] }>(`/api/admin/campaigns?limit=${Math.max(1, Math.min(1000, limit))}`);
  return data.campaigns || [];
}

export function adminCampaignCreate(payload: {
  name: string;
  campaign_type: "promo" | "gift";
  target_value: string;
  segment?: string;
  starts_at?: string | null;
  ends_at?: string | null;
  max_activations?: number;
  auto_disable?: boolean;
  is_active?: boolean;
  metadata?: Record<string, unknown>;
}): Promise<{ ok: boolean; id: number }> {
  return apiFetch("/api/admin/campaigns", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminCampaignUpdate(
  campaignId: number,
  payload: {
    name?: string;
    segment?: string;
    starts_at?: string | null;
    ends_at?: string | null;
    max_activations?: number;
    auto_disable?: boolean;
    is_active?: boolean;
    metadata?: Record<string, unknown>;
  },
): Promise<{ ok: boolean; id: number }> {
  return apiFetch(`/api/admin/campaigns/${campaignId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminCampaignDelete(campaignId: number): Promise<{ ok: boolean }> {
  return apiFetch(`/api/admin/campaigns/${campaignId}`, { method: "DELETE" });
}

export function adminUserKeyToggle(tgId: number, nodeCode: string, enable: boolean): Promise<{ ok: boolean; enabled: boolean }> {
  return apiFetch(`/api/admin/users/${tgId}/keys/${encodeURIComponent(nodeCode)}/toggle`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enable }),
  });
}

export function adminUserKeyResetTraffic(tgId: number, nodeCode: string): Promise<{ ok: boolean }> {
  return apiFetch(`/api/admin/users/${tgId}/keys/${encodeURIComponent(nodeCode)}/reset-traffic`, {
    method: "POST",
  });
}

export function adminUserKeyResyncSubId(
  tgId: number,
  nodeCode: string,
): Promise<{ ok: boolean; expected_sub_id?: string }> {
  return apiFetch(`/api/admin/users/${tgId}/keys/${encodeURIComponent(nodeCode)}/resync-subid`, {
    method: "POST",
  });
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

export function adminManualRegenerateToken(tgId: number): Promise<{ ok: boolean; subscription_url: string; sync_ok?: boolean }> {
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

export function adminMetricsStatus(): Promise<AdminMetricsStatus> {
  return apiFetch<AdminMetricsStatus>("/api/admin/metrics/status");
}

export function adminNodesSync(payload: { tg_id?: number; segment?: string; limit?: number }): Promise<any> {
  return apiFetch<any>("/api/admin/nodes/sync", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function adminPromos(limit = 200): Promise<AdminPromoRow[]> {
  const data = await apiFetch<{ promos: AdminPromoRow[] }>(`/api/admin/promos?limit=${Math.max(1, Math.min(500, limit))}`);
  return data.promos || [];
}

export function adminPromoCreate(payload: {
  code: string;
  promo_type: "discount" | "days";
  value: number;
  uses_left: number;
  expires_at?: string | null;
}): Promise<{ ok: boolean; code: string }> {
  return apiFetch("/api/admin/promos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminPromoUpdate(
  code: string,
  payload: { new_code?: string; promo_type?: "discount" | "days"; value?: number; uses_left?: number; expires_at?: string | null },
): Promise<{ ok: boolean; code: string }> {
  return apiFetch(`/api/admin/promos/${encodeURIComponent(code)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminPromoDelete(code: string): Promise<{ ok: boolean }> {
  return apiFetch(`/api/admin/promos/${encodeURIComponent(code)}`, { method: "DELETE" });
}

export async function adminTemplates(limit = 200): Promise<AdminTemplateRow[]> {
  const data = await apiFetch<{ templates: AdminTemplateRow[] }>(`/api/admin/templates?limit=${Math.max(1, Math.min(500, limit))}`);
  return data.templates || [];
}

export function adminTemplateCreate(payload: { key: string; text: string }): Promise<{ ok: boolean; key: string }> {
  return apiFetch("/api/admin/templates", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminTemplateUpdate(
  key: string,
  payload: { new_key?: string; text?: string },
): Promise<{ ok: boolean; key: string }> {
  return apiFetch(`/api/admin/templates/${encodeURIComponent(key)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminTemplateDelete(key: string): Promise<{ ok: boolean }> {
  return apiFetch(`/api/admin/templates/${encodeURIComponent(key)}`, { method: "DELETE" });
}

export async function adminGiftCodes(limit = 100): Promise<AdminGiftCodeRow[]> {
  const data = await apiFetch<{ gift_codes: AdminGiftCodeRow[] }>(
    `/api/admin/gift-codes?limit=${Math.max(1, Math.min(500, limit))}`,
  );
  return data.gift_codes || [];
}

export function adminGiftCodeCreate(card_type: "mini" | "standard" | "premium"): Promise<{
  ok: boolean;
  gift_code: { code: string; card_type: string; days: number; stars: number };
}> {
  return apiFetch("/api/admin/gift-codes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ card_type }),
  });
}

export async function adminPlans(include_inactive = true): Promise<PlanCatalogRow[]> {
  const data = await apiFetch<{ plans: PlanCatalogRow[] }>(`/api/admin/plans?include_inactive=${include_inactive ? "true" : "false"}`);
  return data.plans || [];
}

export function adminPlanCreate(payload: {
  code: string;
  label: string;
  amount_rub: number;
  amount_stars: number;
  days: number;
  device_limit: number;
  node_policy?: string | null;
  badge?: string | null;
  is_active?: boolean;
  sort_order?: number;
}): Promise<{ ok: boolean; code: string }> {
  return apiFetch("/api/admin/plans", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminPlanUpdate(
  code: string,
  payload: {
    label?: string;
    amount_rub?: number;
    amount_stars?: number;
    days?: number;
    device_limit?: number;
    node_policy?: string | null;
    badge?: string | null;
    is_active?: boolean;
    sort_order?: number;
  },
): Promise<{ ok: boolean; code: string }> {
  return apiFetch(`/api/admin/plans/${encodeURIComponent(code)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminPlanDelete(code: string): Promise<{ ok: boolean }> {
  return apiFetch(`/api/admin/plans/${encodeURIComponent(code)}`, { method: "DELETE" });
}

export async function adminLiveUpdates(include_inactive = true): Promise<LiveUpdateRow[]> {
  const data = await apiFetch<{ updates: LiveUpdateRow[] }>(`/api/admin/live-updates?include_inactive=${include_inactive ? "true" : "false"}`);
  return data.updates || [];
}

export function adminLiveUpdateCreate(payload: {
  title: string;
  summary: string;
  link: string;
  published_at?: string | null;
  is_active?: boolean;
  sort_order?: number;
}): Promise<{ ok: boolean; id: number }> {
  return apiFetch("/api/admin/live-updates", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminLiveUpdateUpdate(
  id: number,
  payload: {
    title?: string;
    summary?: string;
    link?: string;
    published_at?: string | null;
    is_active?: boolean;
    sort_order?: number;
  },
): Promise<{ ok: boolean; id: number }> {
  return apiFetch(`/api/admin/live-updates/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminLiveUpdateDelete(id: number): Promise<{ ok: boolean }> {
  return apiFetch(`/api/admin/live-updates/${id}`, { method: "DELETE" });
}

export function adminBuildCampaignLinks(payload: {
  promo_code?: string;
  campaign_key?: string;
  plan_code?: string;
  source?: "site" | "bot";
}): Promise<CampaignLinksBuildResult> {
  return apiFetch("/api/admin/campaign-links/build", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminMetricsTimeseries(params?: { from?: string; to?: string }): Promise<AdminMetricsTimeseries> {
  const qs = new URLSearchParams();
  if (params?.from) qs.set("from", params.from);
  if (params?.to) qs.set("to", params.to);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiFetch<AdminMetricsTimeseries>(`/api/admin/metrics/timeseries${suffix}`);
}

export async function adminNodesTraffic(params?: { from?: string; to?: string }): Promise<AdminNodeTrafficRow[]> {
  const qs = new URLSearchParams();
  if (params?.from) qs.set("from", params.from);
  if (params?.to) qs.set("to", params.to);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  const data = await apiFetch<{ rows: AdminNodeTrafficRow[] }>(`/api/admin/nodes/traffic${suffix}`);
  return data.rows || [];
}

export async function adminStartLinks(include_inactive = true): Promise<AdminStartLinkRow[]> {
  const data = await apiFetch<{ start_links: AdminStartLinkRow[] }>(
    `/api/admin/start-links?include_inactive=${include_inactive ? "true" : "false"}`,
  );
  return data.start_links || [];
}

export function adminStartLinkCreate(payload: {
  code: string;
  description?: string | null;
  target_action?: string | null;
  is_active?: boolean;
}): Promise<{ ok: boolean; id: number; code: string }> {
  return apiFetch("/api/admin/start-links", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminStartLinkUpdate(
  id: number,
  payload: { code?: string; description?: string | null; target_action?: string | null; is_active?: boolean },
): Promise<{ ok: boolean; id: number; code: string }> {
  return apiFetch(`/api/admin/start-links/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminStartLinkDelete(id: number): Promise<{ ok: boolean; id: number }> {
  return apiFetch(`/api/admin/start-links/${id}`, { method: "DELETE" });
}

export async function adminWheelConfig(): Promise<AdminWheelConfig> {
  const data = await apiFetch<{ wheel_config: AdminWheelConfig }>("/api/admin/wheel-config");
  return data.wheel_config;
}

export function adminWheelConfigUpdate(payload: AdminWheelConfig): Promise<{ ok: boolean; wheel_config: AdminWheelConfig }> {
  return apiFetch("/api/admin/wheel-config", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
