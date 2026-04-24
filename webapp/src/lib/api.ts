/* eslint-disable @typescript-eslint/no-explicit-any */
import { classifyApiPayload, resolveCandidateApiBases, resolvePrimaryApiBase } from "./api-base.mjs";
import { getInitData } from "./telegram";

const WEB_SESSION_TOKEN_KEY = "portal_web_session_token";
const DIRECT_API_BASE = "https://api.pokrov.space";
const DEFAULT_API_TIMEOUT_MS = 15000;
const STABLE_API_CACHE_TTL_MS = 30000;
const NODE_STATUS_CACHE_TTL_MS = 30000;
let authSessionCacheKey = "";
let authSessionCacheValue: AuthSessionPayload | null = null;
let authSessionCachePromise: Promise<AuthSessionPayload> | null = null;

type StableApiCacheEntry<T> = {
  data: T | null;
  expiresAt: number;
  promise: Promise<T> | null;
};

function createStableApiCache<T>(): StableApiCacheEntry<T> {
  return {
    data: null,
    expiresAt: 0,
    promise: null,
  };
}

const dashboardCache = createStableApiCache<DashboardSnapshot>();
const publicPlansCache = createStableApiCache<PublicPlansPayload>();
const publicCatalogCache = createStableApiCache<PublicCatalogPayload>();
const clientAppsCache = createStableApiCache<ClientAppsPayload>();
const userPayloadCaches = new Map<string, StableApiCacheEntry<UserPayload>>();

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
  access_state?: string;
  segment?: string;
  is_active: boolean;
  expiry_at?: string | null;
  used_gb: number;
  total_gb: number;
  remaining_gb: number;
  traffic_policy?: {
    kind: "unlimited" | "metered" | "soft_limited";
    label?: string | null;
    limit_gb?: number | null;
    remaining_gb?: number | null;
    next_reset_at?: string | null;
  } | null;
  traffic_limit_gb?: number | null;
  traffic_remaining_gb?: number | null;
  next_reset_at?: string | null;
  soft_mode_active?: boolean;
  active_sessions: number;
  active_sessions_source?: string | null;
  device_limit: number;
  speed_limit_mbps?: number | null;
  free_next_reset_at?: string | null;
  family_slots?: number;
  subscription_url: string;
  connection_snapshot?: {
    status: string;
    active_connections: number;
    active_users_estimate: number;
    active_users_source?: string | null;
    active_nodes: number;
    known_nodes: number;
    last_online_at?: string | null;
    last_online_age_seconds?: number | null;
    source?: string | null;
  } | null;
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
  linked_identities?: LinkedIdentityPayload | null;
  free_caps?: {
    location_code?: string | null;
    traffic_limit_gb?: number | null;
    cycle_days?: number | null;
    speed_limit_mbps?: number | null;
    device_limit?: number | null;
    monthly_reset?: boolean;
  } | null;
  redeem_eligibility?: {
    eligible?: boolean;
    reason?: string | null;
  } | null;
  promo_slots?: ClientPromoSlotsPayload | null;
  hidden_transport_matrix?: {
    ordered_transport_set?: string[];
    logical_location_count?: number;
    xhttp_enabled?: boolean;
  } | null;
  location_matrix?: {
    locations?: Array<{
      code?: string | null;
      label?: string | null;
      transport_order?: string[];
    }>;
  } | null;
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
  current_plan_code?: string | null;
  access_state?: string;
  segment?: string;
  expiry_at: string | null;
  family_slots?: number;
  traffic_policy?: {
    kind: "unlimited" | "metered" | "soft_limited";
    label?: string | null;
    limit_gb?: number | null;
    remaining_gb?: number | null;
    next_reset_at?: string | null;
  } | null;
  traffic_limit_gb?: number | null;
  traffic_remaining_gb?: number | null;
  next_reset_at?: string | null;
  soft_mode_active?: boolean;
  nodes: NodeInfo[];
  limits: {
    device_limit: number;
    total_gb: number;
    speed_mbps?: number | null;
  };
  devices?: Array<{
    id: string;
    name: string;
    platform?: string | null;
    os_version?: string | null;
    app_version?: string | null;
    last_seen_at?: string | null;
    is_active?: boolean;
    is_current?: boolean;
  }>;
  sync?: {
    app_identity_known?: boolean;
    telegram_linked?: boolean;
    subscription_ready?: boolean;
    device_count?: number;
  };
  traffic: {
    used_gb: number;
    used_bytes?: number;
    total_gb: number;
    remaining_gb: number;
    source?: string | null;
  };
  connections?: {
    status: string;
    active_connections: number;
    active_users_estimate: number;
    active_users_source?: string | null;
    active_nodes: number;
    known_nodes: number;
    last_online_at?: string | null;
    last_online_age_seconds?: number | null;
    source?: string | null;
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
  linked_identities?: LinkedIdentityPayload | null;
  free_caps?: {
    location_code?: string | null;
    traffic_limit_gb?: number | null;
    cycle_days?: number | null;
    speed_limit_mbps?: number | null;
    device_limit?: number | null;
    monthly_reset?: boolean;
  } | null;
  redeem_eligibility?: {
    eligible?: boolean;
    reason?: string | null;
  } | null;
  promo_slots?: ClientPromoSlotsPayload | null;
  hidden_transport_matrix?: {
    ordered_transport_set?: string[];
    logical_location_count?: number;
    xhttp_enabled?: boolean;
  } | null;
  location_matrix?: {
    locations?: Array<{
      code?: string | null;
      label?: string | null;
      transport_order?: string[];
    }>;
  } | null;
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
  provider?: string;
  provider_label?: string | null;
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

export type RubPaymentProvider = {
  code: string;
  label: string;
  accent?: string;
  checkout_hint?: string;
  supports_bot?: boolean;
  supports_webapp?: boolean;
  supports_public?: boolean;
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

export type PublicCatalogPayload = {
  catalog_version: string;
  commerce_model: {
    primary_purchase_flow: string;
    primary_fulfillment_flow: string;
    managed_access_mode: string;
    raw_subscription_link_policy: string;
  };
  public_surface_policy: {
    acquisition_owner: string;
    pricing_owner: string;
    webapp_mode: string;
    public_platform_scope: string[];
  };
  pricing_preview: {
    discount_codes?: Record<string, number>;
  };
  plans: PlanCatalogRow[];
  free_tier: {
    plan_code: string;
    location_code: string;
    traffic_limit_gb: number;
    cycle_days: number;
    speed_limit_mbps: number;
    soft_mode_speed_limit_mbps?: number;
    device_limit: number;
    node_policy: string;
    monthly_reset: boolean;
  };
  public_defaults: {
    routing_mode: string;
    public_platform_scope: string[];
    logical_location_count: number;
    logical_location_label: string;
    raw_subscription_link_policy: string;
    hidden_transport_order: string[];
  };
  promo_slots: {
    mode: string;
    fallback_behavior: string;
    slot_ids: string[];
  };
};

export type AccessKeyStatusPayload = {
  key: string;
  exists: boolean;
  redeemed: boolean;
  redeemed_at?: string | null;
  issued_at?: string | null;
  plan?: PlanCatalogRow | null;
  kind: string;
  legacy_type?: string | null;
  days: number;
  device_limit: number;
  node_policy?: string | null;
  created_by?: number | null;
  redeemed_by?: number | null;
};

export type AccessKeyRedeemPayload = {
  ok: boolean;
  key: string;
  status: AccessKeyStatusPayload;
  plan?: PlanCatalogRow | null;
  access?: Record<string, unknown>;
  linked_identities?: Record<string, unknown> | null;
  free_caps?: Record<string, unknown> | null;
  redeem_eligibility?: Record<string, unknown> | null;
  promo_slots?: ClientPromoSlotsPayload | null;
  hidden_transport_matrix?: Record<string, unknown> | null;
  location_matrix?: Record<string, unknown> | null;
  sync_ok?: boolean;
};

export type PromoSlotAssignmentPayload = {
  slot_id: string;
  content_id: string;
  enabled: boolean;
  title?: string | null;
  body?: string | null;
  cta_label?: string | null;
  cta_href?: string | null;
  contexts: string[];
  sort_order: number;
};

export type ClientPromoSlotsPayload = {
  surface: string;
  access_state: string;
  remote_available: boolean;
  fallback_behavior: string;
  mode: string;
  approved_slots: PromoSlotCatalogSlot[];
  slots: Array<
    PromoSlotAssignmentPayload & {
      surface: string;
      goal?: string | null;
      kind?: string | null;
    }
  >;
};

export type PromoSlotCatalogSlot = {
  id: string;
  surface: string;
  contexts: string[];
  allowed_content_ids: string[];
};

export type PromoSlotCatalogContent = {
  id: string;
  kind: string;
  goal: string;
  default_enabled: boolean;
};

export type AdminPromoSlotsPayload = {
  promo_slots: {
    version: string;
    mode: string;
    remote_available: boolean;
    fallback_behavior: string;
    assignments: PromoSlotAssignmentPayload[];
    catalog: {
      version: string;
      mode: string;
      fallback_behavior: string;
      slots: PromoSlotCatalogSlot[];
      content_catalog: PromoSlotCatalogContent[];
    };
  };
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
  observer: {
    watch_users: number;
    suspicious_users: number;
  };
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

export type AdminUserStatus = "active" | "expired" | "blocked" | "manual_test";
export type AdminUserOrigin = "telegram" | "app" | "hybrid" | "manual_test";
export type AdminObserverState = "ok" | "watch" | "suspicious";

export type AdminObserverBlock = {
  state: AdminObserverState;
  reasons: string[];
  observed_ip_count_24h: number;
  observed_ip_count_7d: number;
  observed_ip_count_30d: number;
  observed_node_count_24h: number;
  observed_node_count_7d: number;
  observed_node_count_30d: number;
  overlap_count_24h: number;
  last_observed_at?: string | null;
  updated_at?: string | null;
  recent_ips: Array<{
    source_ip_raw: string;
    score_ip_key: string;
    node_code?: string | null;
    node_name?: string | null;
    last_seen_at?: string | null;
    counts_for_suspicion: boolean;
  }>;
  recent_nodes: Array<{
    node_id: number;
    node_code?: string | null;
    node_name?: string | null;
    last_seen_at?: string | null;
    score_ip_count: number;
  }>;
};

export type AdminUserRow = {
  tg_id: number;
  username?: string | null;
  display_name?: string | null;
  sub_type: string;
  is_active: boolean;
  effective_active?: boolean;
  status: AdminUserStatus;
  origin: AdminUserOrigin;
  is_manual?: boolean;
  expiry_at?: string | null;
  stars_paid: number;
  created_at?: string | null;
  linked_telegram_id?: number | null;
  linked_telegram_username?: string | null;
  app_install_id?: string | null;
  observer_state: AdminObserverState;
  observer_updated_at?: string | null;
};

export type AdminUserCard = {
  user: {
    tg_id: number;
    username?: string | null;
    display_name?: string | null;
    sub_type: string;
    is_active: boolean;
    effective_active?: boolean;
    status: AdminUserStatus;
    origin: AdminUserOrigin;
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
    linked_telegram_id?: number | null;
    linked_telegram_username?: string | null;
    app_install_id?: string | null;
    app_platform?: string | null;
    app_last_seen_at?: string | null;
    observer_state: AdminObserverState;
    observer_updated_at?: string | null;
  };
  tickets: TicketInfo[];
  keys?: AdminUserKey[];
  key_history?: AdminUserKeyHistoryRow[];
  key_policies?: AdminUserKeyPolicy[];
  admin_actions?: AdminAuditRow[];
  risk?: AdminUserRisk;
  loyalty?: AdminUserLoyalty;
  observer: AdminObserverBlock;
  summary?: {
    nodes_total: number;
    nodes_with_client: number;
    nodes_online: number;
    online_keys_now: number;
    online_connections_now: number;
    active_users_estimate: number;
    active_users_source?: string | null;
    online_node_codes_now: string[];
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
  current_connections: number;
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
  accepting_new_clients: boolean;
  is_draining: boolean;
  mapped_users: number;
  online_keys_now: number;
  online_connections_now: number;
  is_healthy: boolean;
  health_score: number;
  panel_latency_ms?: number | null;
  panel_error_rate: number;
  active_clients: number;
  cpu_percent?: number | null;
  memory_used_mb?: number | null;
  memory_total_mb?: number | null;
  disk_used_gb?: number | null;
  disk_total_gb?: number | null;
  disk_free_gb?: number | null;
  network_rx_bytes_total?: number | null;
  network_tx_bytes_total?: number | null;
  network_rx_mbps?: number | null;
  network_tx_mbps?: number | null;
  network_total_mbps?: number | null;
  network_peak_mbps_24h?: number | null;
  network_port_capacity_mbps?: number | null;
  network_utilization_percent?: number | null;
  network_peak_utilization_percent_24h?: number | null;
  last_ok_at?: string | null;
  last_health_at?: string | null;
  last_probe_stage?: string | null;
  last_probe_error_kind?: string | null;
  last_probe_error_message?: string | null;
  observer_last_push_at?: string | null;
  observer_unmatched_count: number;
  observer_parse_error_count: number;
  observer_is_stale: boolean;
  hoster_family?: string | null;
  hoster_asn?: string | null;
  subnet?: string | null;
  probe_classification?: string | null;
  ipv4_health?: string | null;
  ipv6_health?: string | null;
  transport_health?: unknown | null;
  transport_profiles?: Record<string, AdminTransportProfile> | null;
  weight: number;
};

export type AdminTransportProfile = {
  name?: string | null;
  kind?: string | null;
  enabled?: boolean | null;
  inbound_id?: number | null;
  host?: string | null;
  port?: number | null;
  tls_server_name?: string | null;
};

export type AdminNetworkRolloutOverride = {
  transport_profile?: string;
  dns_policy?: string;
  routing_mode_default?: string;
  ip_version_preference?: string;
  install_ids?: string[];
  tg_ids?: number[];
  linked_tg_ids?: number[];
  platforms?: string[];
};

export type AdminNetworkRolloutOperatorLab = {
  enabled: boolean;
  allowlist_install_ids: string[];
  allowlist_tg_ids: number[];
  allowlist_node_codes: string[];
  expires_at?: string | null;
};

export type AdminNetworkRolloutConfig = {
  version: string;
  defaults: {
    routing_mode_default: string;
    transport_profile: string;
    dns_policy: string;
    ip_version_preference?: string | null;
  };
  carrier_overrides: Record<string, AdminNetworkRolloutOverride>;
  cohort_overrides: Record<string, AdminNetworkRolloutOverride>;
  operator_lab: AdminNetworkRolloutOperatorLab;
  package_catalog_feed?: unknown | null;
  routing_rules_feed?: unknown | null;
  support_recovery_order: string[];
};

type ApiRequestInit = RequestInit & {
  timeoutMs?: number;
};

type StableCacheRequestInit = ApiRequestInit & {
  cacheTtlMs?: number;
  forceRefresh?: boolean;
};

type NodeStatusRequestInit = ApiRequestInit & {
  cacheTtlMs?: number;
  forceRefresh?: boolean;
};

export type AdminNodeDriftRow = {
  node_code: string;
  node_name: string;
  node_host: string;
  status: "ok" | "drift";
  mismatches: string[];
  error?: string;
  expected: {
    inbound_id: number;
    port: number;
    sni: string;
    sid: string;
    pbk: string;
  };
  runtime: {
    inbound_id?: number;
    remark?: string;
    enable?: boolean;
    port?: number;
    protocol?: string;
    network?: string;
    security?: string;
    dest?: string;
    server_names?: string[];
    short_ids?: string[];
    public_key?: string;
  };
  checks: Record<string, boolean>;
};

export type AdminNodeDriftReport = {
  summary: {
    total: number;
    ok: number;
    drift: number;
  };
  results: AdminNodeDriftRow[];
};

export type AdminMetricsStatus = {
  status: "fresh" | "stale" | "missing";
  last_sample_at?: string | null;
  age_seconds?: number | null;
  stale_after_seconds: number;
  nodes?: Array<{
    node_code: string;
    status: "fresh" | "stale";
    last_sample_at?: string | null;
    age_seconds?: number | null;
    cpu_percent?: number;
    memory_percent?: number;
    disk_percent?: number;
    active_clients?: number;
    observer_last_push_at?: string | null;
    observer_is_stale?: boolean;
    alert_kinds?: string[];
  }>;
  active_alerts?: Array<{
    node_code: string;
    kind: string;
    status: "fresh" | "stale";
    age_seconds?: number | null;
    last_sample_at?: string | null;
  }>;
};

export type AdminUsersQuery = {
  q?: string;
  status?: string;
  origin?: string;
  observer_state?: string;
  sort?: string;
  page?: number;
  page_size?: number;
};

export type AdminUsersResponse = {
  users: AdminUserRow[];
  total: number;
  page: number;
  page_size: number;
  sort: string;
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
  user: { id: number; username?: string | null; email?: string | null };
  expires_in: number;
};

export type EmailDeliveryPayload = {
  status?: string;
  kind?: string;
  email?: string;
  mode?: string;
  detail?: string | null;
  http_status?: number | null;
};

export type EmailIdentityPayload = {
  email: string;
  verified?: boolean;
  linked_tg_id?: number | null;
  verified_at?: string | null;
};

export type LinkedIdentityPayload = {
  telegram?: {
    id?: number | null;
    username?: string | null;
  } | null;
  email?: EmailIdentityPayload | null;
};

export type TelegramOidcStartResult = {
  ok: boolean;
  mode: "oidc";
  auth_url: string;
  redirect_uri: string;
};

export type TelegramOidcFinishPayload = {
  code: string;
  state: string;
};

export type AuthSessionPayload = {
  ok: boolean;
  user: {
    id: number;
    account_id?: string;
    username?: string | null;
    email?: string | null;
    device_name?: string | null;
    linked_telegram_id?: number | null;
    linked_telegram_username?: string | null;
    is_authorized?: boolean;
    auth_type?: string | null;
    auth_origin?: string | null;
    linked_identities?: LinkedIdentityPayload | null;
  };
};

export type EmailRegisterPayload = {
  email: string;
  password: string;
  display_name?: string;
};

export type EmailVerifyPayload = {
  token: string;
};

export type EmailLoginPayload = {
  email: string;
  password: string;
};

export type EmailRecoveryStartPayload = {
  email: string;
};

export type EmailRecoveryFinishPayload = {
  token: string;
  password: string;
};

export type EmailRegisterResult = {
  ok: boolean;
  verification_required: boolean;
  delivery?: EmailDeliveryPayload;
  identity?: EmailIdentityPayload | null;
  debug?: {
    verify_token?: string;
    reset_token?: string;
  } | null;
};

export type EmailRecoveryStartResult = {
  ok: boolean;
  recovery_requested: boolean;
  delivery?: EmailDeliveryPayload;
  debug?: {
    verify_token?: string;
    reset_token?: string;
  } | null;
};

function getWebSessionToken(): string {
  if (typeof window === "undefined") return "";
  return String(window.localStorage.getItem(WEB_SESSION_TOKEN_KEY) || "").trim();
}

function clearAuthSessionCache(): void {
  authSessionCacheKey = "";
  authSessionCacheValue = null;
  authSessionCachePromise = null;
  dashboardCache.data = null;
  dashboardCache.expiresAt = 0;
  dashboardCache.promise = null;
  userPayloadCaches.clear();
}

function getAuthSessionCacheKey(): string {
  const token = getWebSessionToken();
  if (token) {
    return `token:${token}`;
  }
  const initData = getInitData();
  if (initData) {
    return `telegram:${initData}`;
  }
  return "";
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
  clearAuthSessionCache();
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
  clearAuthSessionCache();
  window.localStorage.removeItem(WEB_SESSION_TOKEN_KEY);
}

function dispatchAuthRequired(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent("portal-auth-required"));
}

async function readApiError(r: Response): Promise<string> {
  const text = (await r.text()).trim();
  if (!text) return `API error: ${r.status}`;
  if (classifyApiPayload({ bodyText: text, contentType: r.headers.get("content-type") || "" }) === "html") {
    return "Received app shell instead of API response";
  }
  try {
    const parsed = JSON.parse(text) as { detail?: string; message?: string };
    return String(parsed?.detail || parsed?.message || text);
  } catch {
    return text;
  }
}

function candidateApiBases(): string[] {
  const envBaseRaw = (
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.NEXT_PUBLIC_PUBLIC_API_BASE_URL ||
    process.env.VITE_PUBLIC_API_BASE_URL ||
    ""
  ).trim();
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  const hasSessionToken = typeof window !== "undefined" && !!getWebSessionToken();
  const useLegacyFallback =
    String(process.env.NEXT_PUBLIC_ENABLE_LEGACY_PORT_FALLBACK || process.env.VITE_ENABLE_LEGACY_PORT_FALLBACK || "")
      .toLowerCase() === "true";
  return resolveCandidateApiBases({
    envBase: envBaseRaw,
    origin,
    directApiBase: DIRECT_API_BASE,
    hasSessionToken,
    enableLegacyPortFallback: useLegacyFallback,
  });
}

export function resolveApiUrl(path: string): string {
  const raw = String(path || "").trim();
  if (!raw) return "";
  if (/^https?:\/\//i.test(raw)) return raw;
  const normalizedPath = raw.startsWith("/") ? raw : `/${raw}`;
  const base = resolvePrimaryApiBase({
    envBase:
      process.env.NEXT_PUBLIC_API_BASE_URL ||
      process.env.NEXT_PUBLIC_PUBLIC_API_BASE_URL ||
      process.env.VITE_PUBLIC_API_BASE_URL ||
      "",
    origin: typeof window !== "undefined" ? window.location.origin : "",
    directApiBase: DIRECT_API_BASE,
  });
  return `${base}${normalizedPath}`;
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  const kind = classifyApiPayload({
    bodyText: text,
    contentType: response.headers.get("content-type") || "",
  });
  if (kind === "html") {
    throw new Error("Received app shell instead of API response");
  }
  if (!text.trim()) {
    return {} as T;
  }
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error("Invalid API JSON response");
  }
}

function createAbortError(reason?: unknown): Error {
  if (reason instanceof Error) {
    return reason;
  }
  if (typeof DOMException !== "undefined") {
    return new DOMException("Request aborted", "AbortError");
  }
  const error = new Error("Request aborted");
  error.name = "AbortError";
  return error;
}

function createTimeoutError(timeoutMs: number): Error {
  if (typeof DOMException !== "undefined") {
    return new DOMException(`Request timed out after ${Math.round(timeoutMs / 1000)}s`, "TimeoutError");
  }
  const error = new Error(`Request timed out after ${Math.round(timeoutMs / 1000)}s`);
  error.name = "TimeoutError";
  return error;
}

function createManagedRequestSignal(signal: AbortSignal | null | undefined, timeoutMs: number) {
  const controller = new AbortController();
  let abortedByCaller = false;
  let abortedByTimeout = false;
  let timeoutHandle: ReturnType<typeof setTimeout> | null = null;

  const abortFromSignal = () => {
    abortedByCaller = true;
    controller.abort(signal?.reason);
  };

  if (signal?.aborted) {
    abortFromSignal();
  } else if (signal) {
    signal.addEventListener("abort", abortFromSignal, { once: true });
  }

  if (!controller.signal.aborted && timeoutMs > 0) {
    timeoutHandle = setTimeout(() => {
      abortedByTimeout = true;
      controller.abort(createTimeoutError(timeoutMs));
    }, timeoutMs);
  }

  return {
    signal: controller.signal,
    abortedByCaller: () => abortedByCaller,
    abortedByTimeout: () => abortedByTimeout,
    cleanup: () => {
      if (timeoutHandle) {
        clearTimeout(timeoutHandle);
      }
      if (signal) {
        signal.removeEventListener("abort", abortFromSignal);
      }
    },
  };
}

function withAbortSignal<T>(promise: Promise<T>, signal?: AbortSignal | null): Promise<T> {
  if (!signal) {
    return promise;
  }
  if (signal.aborted) {
    return Promise.reject(createAbortError(signal.reason));
  }
  return new Promise<T>((resolve, reject) => {
    const onAbort = () => {
      cleanup();
      reject(createAbortError(signal.reason));
    };
    const cleanup = () => signal.removeEventListener("abort", onAbort);
    signal.addEventListener("abort", onAbort, { once: true });
    promise.then(
      (value) => {
        cleanup();
        resolve(value);
      },
      (error) => {
        cleanup();
        reject(error);
      },
    );
  });
}

function readStableApiCache<T>(
  cache: StableApiCacheEntry<T>,
  loader: () => Promise<T>,
  init?: StableCacheRequestInit,
): Promise<T> {
  const { cacheTtlMs = STABLE_API_CACHE_TTL_MS, forceRefresh = false, signal } = init || {};
  const now = Date.now();
  if (!forceRefresh && cache.data && cache.expiresAt > now) {
    return Promise.resolve(cache.data);
  }
  if (!forceRefresh && cache.promise) {
    return withAbortSignal(cache.promise, signal);
  }
  const request = loader()
    .then((data) => {
      cache.data = data;
      cache.expiresAt = Date.now() + Math.max(0, cacheTtlMs);
      return data;
    })
    .finally(() => {
      if (cache.promise === request) {
        cache.promise = null;
      }
    });
  cache.promise = request;
  return withAbortSignal(request, signal);
}

function stableCacheApiInit(init?: StableCacheRequestInit): ApiRequestInit | undefined {
  if (!init) return undefined;
  const { cacheTtlMs: _cacheTtlMs, forceRefresh: _forceRefresh, ...requestInit } = init;
  return requestInit;
}

const nodeStatusCache: {
  data: NodeStatus[] | null;
  expiresAt: number;
  promise: Promise<NodeStatus[]> | null;
} = {
  data: null,
  expiresAt: 0,
  promise: null,
};

async function unauthenticatedJsonPost<T>(path: string, payload: unknown, init?: ApiRequestInit): Promise<T> {
  const bases = candidateApiBases();
  let lastErr: any = null;
  const { timeoutMs = DEFAULT_API_TIMEOUT_MS, signal, ...requestInit } = init || {};
  for (const base of bases) {
    const managedSignal = createManagedRequestSignal(signal, timeoutMs);
    try {
      const headers = new Headers({ "Content-Type": "application/json" });
      applyAuthHeaders(headers);
      const response = await fetch(`${base}${path}`, {
        ...requestInit,
        method: "POST",
        headers,
        body: JSON.stringify(payload),
        cache: "no-store",
        signal: managedSignal.signal,
      });
      if (!response.ok) {
        const text = await readApiError(response);
        throw new Error(text || `API error: ${response.status}`);
      }
      return await parseJsonResponse<T>(response);
    } catch (error: any) {
      lastErr = managedSignal.abortedByTimeout() ? createTimeoutError(timeoutMs) : error;
      if (managedSignal.abortedByCaller()) {
        throw createAbortError(signal?.reason);
      }
      const msg = String(lastErr?.message || lastErr);
      if (
        managedSignal.abortedByTimeout() ||
        msg.includes("Failed to fetch") ||
        msg.includes("NetworkError") ||
        msg.includes("fetch") ||
        msg.includes("Received app shell instead of API response")
      ) {
        continue;
      }
      break;
    } finally {
      managedSignal.cleanup();
    }
  }
  throw lastErr || new Error("API error");
}

async function apiFetch<T>(path: string, init?: ApiRequestInit): Promise<T> {
  const bases = candidateApiBases();
  let lastErr: any = null;
  const { timeoutMs = DEFAULT_API_TIMEOUT_MS, signal, ...requestInit } = init || {};
  for (const base of bases) {
    const managedSignal = createManagedRequestSignal(signal, timeoutMs);
    try {
      const headers = new Headers(requestInit.headers || {});
      applyAuthHeaders(headers);
      const r = await fetch(`${base}${path}`, { ...requestInit, headers, signal: managedSignal.signal });
      if (!r.ok) {
        const text = await readApiError(r);
        if (r.status === 401) {
          clearWebSessionToken();
          dispatchAuthRequired();
        }
        throw new Error(text || `API error: ${r.status}`);
      }
      if (r.status === 204) return {} as T;
      return await parseJsonResponse<T>(r);
    } catch (e: any) {
      lastErr = managedSignal.abortedByTimeout() ? createTimeoutError(timeoutMs) : e;
      if (managedSignal.abortedByCaller()) {
        throw createAbortError(signal?.reason);
      }
      const msg = String(lastErr?.message || lastErr);
      if (
        managedSignal.abortedByTimeout() ||
        msg.includes("Failed to fetch") ||
        msg.includes("NetworkError") ||
        msg.includes("fetch") ||
        msg.includes("Received app shell instead of API response")
      ) {
        continue;
      }
      break;
    } finally {
      managedSignal.cleanup();
    }
  }
  throw lastErr || new Error("API error");
}

export function fetchUser(tgId: number, init?: StableCacheRequestInit): Promise<UserPayload> {
  const cacheKey = String(tgId);
  let cache = userPayloadCaches.get(cacheKey);
  if (!cache) {
    cache = createStableApiCache<UserPayload>();
    userPayloadCaches.set(cacheKey, cache);
  }
  return readStableApiCache(cache, () => apiFetch<UserPayload>(`/api/user/${tgId}`, stableCacheApiInit(init)), init);
}

export function fetchPublicPlans(init?: StableCacheRequestInit): Promise<PublicPlansPayload> {
  return readStableApiCache(publicPlansCache, () => apiFetch<PublicPlansPayload>("/api/public/plans", stableCacheApiInit(init)), init);
}

export function fetchPublicCatalog(init?: StableCacheRequestInit): Promise<PublicCatalogPayload> {
  return readStableApiCache(publicCatalogCache, () => apiFetch<PublicCatalogPayload>("/api/public/catalog", stableCacheApiInit(init)), init);
}

export async function fetchPublicLiveUpdates(limit = 3): Promise<LiveUpdateRow[]> {
  const data = await apiFetch<{ updates: LiveUpdateRow[] }>(`/api/public/live-updates?limit=${Math.max(1, Math.min(10, limit))}`);
  return data.updates || [];
}

export function fetchDashboard(init?: StableCacheRequestInit): Promise<DashboardSnapshot> {
  return readStableApiCache(dashboardCache, () => apiFetch<DashboardSnapshot>("/api/dashboard", stableCacheApiInit(init)), init);
}

export async function fetchNodeStatus(init?: NodeStatusRequestInit): Promise<NodeStatus[]> {
  const { cacheTtlMs = NODE_STATUS_CACHE_TTL_MS, forceRefresh = false, signal, ...requestInit } = init || {};
  const now = Date.now();
  if (!forceRefresh && nodeStatusCache.data && nodeStatusCache.expiresAt > now) {
    return nodeStatusCache.data;
  }
  if (!forceRefresh && nodeStatusCache.promise) {
    return withAbortSignal(nodeStatusCache.promise, signal);
  }
  const requestPromise = apiFetch<{ nodes: NodeStatus[] }>("/api/nodes/status", {
    ...requestInit,
  })
    .then((data) => {
      const rows = data.nodes || [];
      nodeStatusCache.data = rows;
      nodeStatusCache.expiresAt = Date.now() + Math.max(0, cacheTtlMs);
      return rows;
    })
    .finally(() => {
      if (nodeStatusCache.promise === requestPromise) {
        nodeStatusCache.promise = null;
      }
    });
  nodeStatusCache.promise = requestPromise;
  return withAbortSignal(requestPromise, signal);
}

export function fetchClientApps(init?: StableCacheRequestInit): Promise<ClientAppsPayload> {
  return readStableApiCache(clientAppsCache, () => apiFetch<ClientAppsPayload>("/api/client/apps", stableCacheApiInit(init)), init);
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

export function fetchAccessKeyStatus(key: string): Promise<AccessKeyStatusPayload> {
  return apiFetch<AccessKeyStatusPayload>(`/api/access-keys/status/${encodeURIComponent(String(key || "").trim())}`);
}

export function redeemAccessKey(key: string): Promise<AccessKeyRedeemPayload> {
  return apiFetch<AccessKeyRedeemPayload>("/api/access-keys/redeem", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key }),
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
        const text = await readApiError(r);
        throw new Error(text || `API error: ${r.status}`);
      }
      return await parseJsonResponse<WebLoginResult>(r);
    } catch (e: any) {
      lastErr = e;
    }
  }
  throw lastErr || new Error("API error");
}

export async function startTelegramOidcLogin(): Promise<TelegramOidcStartResult> {
  const bases = candidateApiBases();
  let lastErr: any = null;
  for (const base of bases) {
    try {
      const r = await fetch(`${base}/api/auth/telegram/oidc/start`, { method: "GET" });
      if (!r.ok) {
        const text = await readApiError(r);
        throw new Error(text || `API error: ${r.status}`);
      }
      return await parseJsonResponse<TelegramOidcStartResult>(r);
    } catch (error: any) {
      lastErr = error;
    }
  }
  throw lastErr || new Error("API error");
}

export async function finishTelegramOidcLogin(payload: TelegramOidcFinishPayload): Promise<WebLoginResult> {
  const bases = candidateApiBases();
  let lastErr: any = null;
  for (const base of bases) {
    try {
      const r = await fetch(`${base}/api/auth/telegram/oidc/finish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!r.ok) {
        const text = await readApiError(r);
        throw new Error(text || `API error: ${r.status}`);
      }
      return await parseJsonResponse<WebLoginResult>(r);
    } catch (error: any) {
      lastErr = error;
    }
  }
  throw lastErr || new Error("API error");
}

export function fetchAuthSession(): Promise<AuthSessionPayload> {
  const cacheKey = getAuthSessionCacheKey();
  if (cacheKey && authSessionCacheKey === cacheKey) {
    if (authSessionCacheValue) {
      return Promise.resolve(authSessionCacheValue);
    }
    if (authSessionCachePromise) {
      return authSessionCachePromise;
    }
  }

  const request = apiFetch<AuthSessionPayload>("/api/auth/session")
    .then((payload) => {
      if (authSessionCacheKey === cacheKey) {
        authSessionCacheValue = payload;
        authSessionCachePromise = null;
      }
      return payload;
    })
    .catch((error) => {
      if (authSessionCacheKey === cacheKey) {
        authSessionCacheValue = null;
        authSessionCachePromise = null;
      }
      throw error;
    });

  if (!cacheKey) {
    return request;
  }

  authSessionCacheKey = cacheKey;
  authSessionCacheValue = null;
  authSessionCachePromise = request;
  return request;
}

export function registerByEmail(payload: EmailRegisterPayload): Promise<EmailRegisterResult> {
  return unauthenticatedJsonPost<EmailRegisterResult>("/api/auth/email/register", payload);
}

export function verifyEmailToken(payload: EmailVerifyPayload): Promise<WebLoginResult> {
  return unauthenticatedJsonPost<WebLoginResult>("/api/auth/email/verify", payload);
}

export function loginByEmail(payload: EmailLoginPayload): Promise<WebLoginResult> {
  return unauthenticatedJsonPost<WebLoginResult>("/api/auth/email/login", payload);
}

export function startEmailRecovery(payload: EmailRecoveryStartPayload): Promise<EmailRecoveryStartResult> {
  return unauthenticatedJsonPost<EmailRecoveryStartResult>("/api/auth/email/recovery/start", payload);
}

export function finishEmailRecovery(payload: EmailRecoveryFinishPayload): Promise<WebLoginResult> {
  return unauthenticatedJsonPost<WebLoginResult>("/api/auth/email/recovery/finish", payload);
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
  provider: string;
  plan_code: string;
  source?: "site" | "bot";
  tg_id?: number;
  campaign?: string;
  promo_code?: string;
  currency?: string;
}): Promise<RubCheckoutStartResult> {
  return apiFetch("/api/payments/orders/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function createPublicRubCheckoutOrder(payload: {
  provider: string;
  plan_code: string;
  checkout_ticket: string;
  currency?: string;
}): Promise<RubCheckoutStartResult> {
  return apiFetch("/api/payments/orders/create-public", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getRubPaymentProviders(): Promise<{ ok: boolean; providers: RubPaymentProvider[] }> {
  return apiFetch("/api/payments/providers");
}

export function checkChannelSubscriberStatus(): Promise<{
  ok: boolean;
  subscriber: boolean;
  reason?: string;
  claim_required?: boolean;
  already_claimed?: boolean;
  bonus_days?: number;
  link_required?: boolean;
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

function normalizeAdminSummaryPayload(payload: Partial<AdminSummaryPayload> | null | undefined): AdminSummaryPayload {
  const data = payload || {};
  return {
    actor_tg_id: Number(data.actor_tg_id || 0),
    users: {
      total: Number(data.users?.total || 0),
      active: Number(data.users?.active || 0),
      free: Number(data.users?.free || 0),
      paid: Number(data.users?.paid || 0),
    },
    observer: {
      watch_users: Number(data.observer?.watch_users || 0),
      suspicious_users: Number(data.observer?.suspicious_users || 0),
    },
    retention: {
      expiring_3d: Number(data.retention?.expiring_3d || 0),
      expired_7d: Number(data.retention?.expired_7d || 0),
      reactivation_candidates: Number(data.retention?.reactivation_candidates || 0),
      pings_24h: {
        welcome: Number(data.retention?.pings_24h?.welcome || 0),
        t3: Number(data.retention?.pings_24h?.t3 || 0),
        t1: Number(data.retention?.pings_24h?.t1 || 0),
        t0: Number(data.retention?.pings_24h?.t0 || 0),
        reactivation: Number(data.retention?.pings_24h?.reactivation || 0),
        start99_offer: Number(data.retention?.pings_24h?.start99_offer || 0),
      },
    },
    tickets: { open: Number(data.tickets?.open || 0) },
    nodes: {
      total: Number(data.nodes?.total || 0),
      healthy: Number(data.nodes?.healthy || 0),
    },
    errors: {
      stale_metrics: Boolean(data.errors?.stale_metrics),
      unhealthy_nodes: Number(data.errors?.unhealthy_nodes || 0),
      open_tickets: Number(data.errors?.open_tickets || 0),
      payment_callback_failures_24h: Number(data.errors?.payment_callback_failures_24h || 0),
      subscription_numeric_fallbacks_24h: Number(data.errors?.subscription_numeric_fallbacks_24h || 0),
    },
    resilience: {
      single_point_risk: Boolean(data.resilience?.single_point_risk),
      free_node_enabled: Boolean(data.resilience?.free_node_enabled),
    },
    bonus_events_24h: {
      channel_activated: Number(data.bonus_events_24h?.channel_activated || 0),
      channel_denied: Number(data.bonus_events_24h?.channel_denied || 0),
      promo_redeemed: Number(data.bonus_events_24h?.promo_redeemed || 0),
      promo_denied: Number(data.bonus_events_24h?.promo_denied || 0),
      gift_redeemed: Number(data.bonus_events_24h?.gift_redeemed || 0),
      gift_denied: Number(data.bonus_events_24h?.gift_denied || 0),
    },
    top_nodes: Array.isArray(data.top_nodes)
      ? data.top_nodes.map((row) => ({
          code: String(row.code || ""),
          health_score: Number(row.health_score || 0),
          panel_latency_ms: row.panel_latency_ms ?? null,
          active_clients: Number(row.active_clients || 0),
          last_health_at: row.last_health_at ?? null,
        }))
      : [],
  };
}

function normalizeAdminObserverState(value: unknown): AdminObserverState {
  const raw = String(value || "").toLowerCase();
  if (raw === "watch" || raw === "suspicious") return raw;
  return "ok";
}

function normalizeAdminObserverBlock(payload: Partial<AdminObserverBlock> | null | undefined): AdminObserverBlock {
  const data = payload || {};
  return {
    state: normalizeAdminObserverState(data.state),
    reasons: Array.isArray(data.reasons) ? data.reasons.map((item) => String(item || "")) : [],
    observed_ip_count_24h: Number(data.observed_ip_count_24h || 0),
    observed_ip_count_7d: Number(data.observed_ip_count_7d || 0),
    observed_ip_count_30d: Number(data.observed_ip_count_30d || 0),
    observed_node_count_24h: Number(data.observed_node_count_24h || 0),
    observed_node_count_7d: Number(data.observed_node_count_7d || 0),
    observed_node_count_30d: Number(data.observed_node_count_30d || 0),
    overlap_count_24h: Number(data.overlap_count_24h || 0),
    last_observed_at: data.last_observed_at ?? null,
    updated_at: data.updated_at ?? null,
    recent_ips: Array.isArray(data.recent_ips)
      ? data.recent_ips.map((row) => ({
          source_ip_raw: String(row.source_ip_raw || ""),
          score_ip_key: String(row.score_ip_key || ""),
          node_code: row.node_code ?? null,
          node_name: row.node_name ?? null,
          last_seen_at: row.last_seen_at ?? null,
          counts_for_suspicion: Boolean(row.counts_for_suspicion),
        }))
      : [],
    recent_nodes: Array.isArray(data.recent_nodes)
      ? data.recent_nodes.map((row) => ({
          node_id: Number(row.node_id || 0),
          node_code: row.node_code ?? null,
          node_name: row.node_name ?? null,
          last_seen_at: row.last_seen_at ?? null,
          score_ip_count: Number(row.score_ip_count || 0),
        }))
      : [],
  };
}

function normalizeAdminMetricsStatus(payload: Partial<AdminMetricsStatus> | null | undefined): AdminMetricsStatus {
  const data = payload || {};
  const rawStatus = String(data.status || "").toLowerCase();
  const status: AdminMetricsStatus["status"] = rawStatus === "fresh" || rawStatus === "stale" ? rawStatus : "missing";
  return {
    status,
    last_sample_at: data.last_sample_at ?? null,
    age_seconds: data.age_seconds ?? null,
    stale_after_seconds: Number(data.stale_after_seconds || 0),
    nodes: Array.isArray(data.nodes)
      ? data.nodes.map((row) => ({
          node_code: String(row.node_code || ""),
          status: row.status === "fresh" ? "fresh" : "stale",
          last_sample_at: row.last_sample_at ?? null,
          age_seconds: row.age_seconds ?? null,
          cpu_percent: row.cpu_percent ?? 0,
          memory_percent: row.memory_percent ?? 0,
          disk_percent: row.disk_percent ?? 0,
          active_clients: row.active_clients ?? 0,
          observer_last_push_at: row.observer_last_push_at ?? null,
          observer_is_stale: Boolean(row.observer_is_stale),
          alert_kinds: Array.isArray(row.alert_kinds) ? row.alert_kinds.map((item) => String(item || "")) : [],
        }))
      : [],
    active_alerts: Array.isArray(data.active_alerts)
      ? data.active_alerts.map((row) => ({
          node_code: String(row.node_code || ""),
          kind: String(row.kind || ""),
          status: row.status === "fresh" ? "fresh" : "stale",
          age_seconds: row.age_seconds ?? null,
          last_sample_at: row.last_sample_at ?? null,
        }))
      : [],
  };
}

function normalizeAdminUsersResponse(payload: Partial<AdminUsersResponse> | null | undefined): AdminUsersResponse {
  const data = payload || {};
  return {
    users: Array.isArray(data.users)
      ? data.users.map((row) => ({
          tg_id: Number(row.tg_id || 0),
          username: row.username ?? null,
          display_name: row.display_name ?? null,
          sub_type: String(row.sub_type || ""),
          is_active: Boolean(row.is_active),
          effective_active: Boolean(row.effective_active),
          status: (row.status || "expired") as AdminUserStatus,
          origin: (row.origin || "telegram") as AdminUserOrigin,
          is_manual: Boolean(row.is_manual),
          expiry_at: row.expiry_at ?? null,
          stars_paid: Number(row.stars_paid || 0),
          created_at: row.created_at ?? null,
          linked_telegram_id: row.linked_telegram_id ?? null,
          linked_telegram_username: row.linked_telegram_username ?? null,
          app_install_id: row.app_install_id ?? null,
          observer_state: normalizeAdminObserverState(row.observer_state),
          observer_updated_at: row.observer_updated_at ?? null,
        }))
      : [],
    total: Number(data.total || 0),
    page: Number(data.page || 1),
    page_size: Number(data.page_size || 50),
    sort: String(data.sort || "created_desc"),
  };
}

function normalizeAdminNodeHealthRow(payload: Partial<AdminNodeHealthRow> | null | undefined): AdminNodeHealthRow {
  const data = payload || {};
  return {
    code: String(data.code || ""),
    name: String(data.name || ""),
    enabled: Boolean(data.enabled),
    accepting_new_clients: Boolean(data.accepting_new_clients),
    is_draining: Boolean(data.is_draining),
    mapped_users: Number(data.mapped_users || 0),
    online_keys_now: Number(data.online_keys_now || 0),
    online_connections_now: Number(data.online_connections_now || 0),
    is_healthy: Boolean(data.is_healthy),
    health_score: Number(data.health_score || 0),
    panel_latency_ms: data.panel_latency_ms ?? null,
    panel_error_rate: Number(data.panel_error_rate || 0),
    active_clients: Number(data.active_clients || 0),
    cpu_percent: data.cpu_percent == null ? null : Number(data.cpu_percent),
    memory_used_mb: data.memory_used_mb == null ? null : Number(data.memory_used_mb),
    memory_total_mb: data.memory_total_mb == null ? null : Number(data.memory_total_mb),
    disk_used_gb: data.disk_used_gb == null ? null : Number(data.disk_used_gb),
    disk_total_gb: data.disk_total_gb == null ? null : Number(data.disk_total_gb),
    disk_free_gb: data.disk_free_gb == null ? null : Number(data.disk_free_gb),
    network_rx_bytes_total: data.network_rx_bytes_total == null ? null : Number(data.network_rx_bytes_total),
    network_tx_bytes_total: data.network_tx_bytes_total == null ? null : Number(data.network_tx_bytes_total),
    network_rx_mbps: data.network_rx_mbps == null ? null : Number(data.network_rx_mbps),
    network_tx_mbps: data.network_tx_mbps == null ? null : Number(data.network_tx_mbps),
    network_total_mbps: data.network_total_mbps == null ? null : Number(data.network_total_mbps),
    network_peak_mbps_24h: data.network_peak_mbps_24h == null ? null : Number(data.network_peak_mbps_24h),
    network_port_capacity_mbps: data.network_port_capacity_mbps == null ? null : Number(data.network_port_capacity_mbps),
    network_utilization_percent: data.network_utilization_percent == null ? null : Number(data.network_utilization_percent),
    network_peak_utilization_percent_24h:
      data.network_peak_utilization_percent_24h == null ? null : Number(data.network_peak_utilization_percent_24h),
    last_ok_at: data.last_ok_at ?? null,
    last_health_at: data.last_health_at ?? null,
    last_probe_stage: data.last_probe_stage ?? null,
    last_probe_error_kind: data.last_probe_error_kind ?? null,
    last_probe_error_message: data.last_probe_error_message ?? null,
    observer_last_push_at: data.observer_last_push_at ?? null,
    observer_unmatched_count: Number(data.observer_unmatched_count || 0),
    observer_parse_error_count: Number(data.observer_parse_error_count || 0),
    observer_is_stale: Boolean(data.observer_is_stale),
    hoster_family: data.hoster_family ?? null,
    hoster_asn: data.hoster_asn ?? null,
    subnet: data.subnet ?? null,
    probe_classification: data.probe_classification ?? null,
    ipv4_health: data.ipv4_health ?? null,
    ipv6_health: data.ipv6_health ?? null,
    transport_health:
      data.transport_health == null
        ? null
        : data.transport_health && typeof data.transport_health === "object"
          ? Array.isArray(data.transport_health)
            ? [...data.transport_health]
            : { ...data.transport_health }
          : data.transport_health,
    transport_profiles: normalizeAdminTransportProfiles(data.transport_profiles),
    weight: Number(data.weight || 0),
  };
}

function normalizeStringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item)).filter((item) => item.trim().length > 0) : [];
}

function normalizeNumberList(value: unknown): number[] {
  return Array.isArray(value)
    ? value
        .map((item) => Number(item))
        .filter((item) => Number.isFinite(item))
        .map((item) => Math.trunc(item))
    : [];
}

function cloneJsonValue<T>(value: T): T {
  if (value == null) return value;
  if (typeof value !== "object") return value;
  try {
    return structuredClone(value);
  } catch {
    try {
      return JSON.parse(JSON.stringify(value)) as T;
    } catch {
      return value;
    }
  }
}

function normalizeAdminTransportProfile(
  key: string,
  payload: Partial<AdminTransportProfile> | null | undefined,
): AdminTransportProfile {
  const data = payload || {};
  return {
    name: data.name == null ? key || null : String(data.name),
    kind: data.kind == null ? null : String(data.kind),
    enabled: data.enabled == null ? null : Boolean(data.enabled),
    inbound_id: data.inbound_id == null ? null : Number(data.inbound_id),
    host: data.host == null ? null : String(data.host),
    port: data.port == null ? null : Number(data.port),
    tls_server_name: data.tls_server_name == null ? null : String(data.tls_server_name),
  };
}

function normalizeAdminTransportProfiles(value: unknown): Record<string, AdminTransportProfile> | null {
  if (Array.isArray(value)) {
    const entries = value
      .map((profile, index) => {
        const normalized = normalizeAdminTransportProfile("", profile as Partial<AdminTransportProfile>);
        const key = String(normalized.name || `profile_${index + 1}`);
        return [key, normalized] as const;
      })
      .filter(([key]) => key.trim().length > 0);
    return entries.length ? Object.fromEntries(entries) : null;
  }
  if (value && typeof value === "object") {
    const entries = Object.entries(value as Record<string, Partial<AdminTransportProfile>>)
      .map(([key, profile]) => [key, normalizeAdminTransportProfile(key, profile)] as const)
      .filter(([key]) => key.trim().length > 0);
    return entries.length ? Object.fromEntries(entries) : null;
  }
  return null;
}

function normalizeAdminNetworkRolloutOverride(payload: Partial<AdminNetworkRolloutOverride> | null | undefined): AdminNetworkRolloutOverride {
  const data = payload || {};
  const out: AdminNetworkRolloutOverride = {};
  if (data.transport_profile != null) out.transport_profile = String(data.transport_profile);
  if (data.dns_policy != null) out.dns_policy = String(data.dns_policy);
  if (data.routing_mode_default != null) out.routing_mode_default = String(data.routing_mode_default);
  if (data.ip_version_preference != null) out.ip_version_preference = String(data.ip_version_preference);
  if (data.install_ids != null) out.install_ids = normalizeStringList(data.install_ids);
  if (data.tg_ids != null) out.tg_ids = normalizeNumberList(data.tg_ids);
  if (data.linked_tg_ids != null) out.linked_tg_ids = normalizeNumberList(data.linked_tg_ids);
  if (data.platforms != null) out.platforms = normalizeStringList(data.platforms);
  return out;
}

function normalizeAdminNetworkRolloutConfig(payload: Partial<AdminNetworkRolloutConfig> | null | undefined): AdminNetworkRolloutConfig {
  const data = payload || {};
  const defaults = (data.defaults || {}) as Partial<AdminNetworkRolloutConfig["defaults"]>;
  const operatorLab = (data.operator_lab || {}) as Partial<AdminNetworkRolloutOperatorLab>;
  const normalizeOverrides = (value: unknown): Record<string, AdminNetworkRolloutOverride> =>
    value && typeof value === "object" && !Array.isArray(value)
      ? Object.fromEntries(
          Object.entries(value as Record<string, Partial<AdminNetworkRolloutOverride>>).map(([key, item]) => [key, normalizeAdminNetworkRolloutOverride(item)]),
        )
      : {};
  return {
    version: data.version == null ? "1" : String(data.version),
    defaults: {
      routing_mode_default: String(defaults.routing_mode_default || "all_except_ru"),
      transport_profile: String(defaults.transport_profile || "legacy_reality_fallback"),
      dns_policy: String(defaults.dns_policy || "ru_direct_split"),
      ip_version_preference: defaults.ip_version_preference == null ? null : String(defaults.ip_version_preference),
    },
    carrier_overrides: normalizeOverrides(data.carrier_overrides),
    cohort_overrides: normalizeOverrides(data.cohort_overrides),
    operator_lab: {
      enabled: Boolean(operatorLab.enabled),
      allowlist_install_ids: normalizeStringList(operatorLab.allowlist_install_ids),
      allowlist_tg_ids: normalizeNumberList(operatorLab.allowlist_tg_ids),
      allowlist_node_codes: normalizeStringList(operatorLab.allowlist_node_codes),
      expires_at: operatorLab.expires_at ?? null,
    },
    package_catalog_feed: cloneJsonValue(data.package_catalog_feed ?? null),
    routing_rules_feed: cloneJsonValue(data.routing_rules_feed ?? null),
    support_recovery_order: normalizeStringList(data.support_recovery_order),
  };
}

function normalizeAdminUserCard(payload: Partial<AdminUserCard> | null | undefined): AdminUserCard {
  const data = payload || {};
  const user = data.user || ({} as AdminUserCard["user"]);
  return {
    ...data,
    user: {
      tg_id: Number(user.tg_id || 0),
      username: user.username ?? null,
      display_name: user.display_name ?? null,
      sub_type: String(user.sub_type || ""),
      is_active: Boolean(user.is_active),
      effective_active: Boolean(user.effective_active),
      status: (user.status || "expired") as AdminUserStatus,
      origin: (user.origin || "telegram") as AdminUserOrigin,
      is_manual: Boolean(user.is_manual),
      expiry_at: user.expiry_at ?? null,
      stars_paid: Number(user.stars_paid || 0),
      total_gb: Number(user.total_gb || 0),
      trial_used: Boolean(user.trial_used),
      referral_count: Number(user.referral_count || 0),
      streak_months: Number(user.streak_months || 0),
      created_at: user.created_at ?? null,
      subscription_url: user.subscription_url || "",
      subscription_token: user.subscription_token || "",
      linked_telegram_id: user.linked_telegram_id ?? null,
      linked_telegram_username: user.linked_telegram_username ?? null,
      app_install_id: user.app_install_id ?? null,
      app_platform: user.app_platform ?? null,
      app_last_seen_at: user.app_last_seen_at ?? null,
      observer_state: normalizeAdminObserverState(user.observer_state),
      observer_updated_at: user.observer_updated_at ?? null,
    },
    tickets: Array.isArray(data.tickets) ? data.tickets : [],
    keys: Array.isArray(data.keys)
      ? data.keys.map((row) => ({
          node_code: String(row.node_code || ""),
          node_name: row.node_name ?? "",
          node_host: row.node_host ?? "",
          exists: Boolean(row.exists),
          client_uuid: row.client_uuid ?? "",
          panel_email: row.panel_email ?? "",
          enabled: Boolean(row.enabled),
          online: row.online ?? null,
          current_connections: Number(row.current_connections || 0),
          sub_id: row.sub_id ?? "",
          expected_sub_id: row.expected_sub_id ?? "",
          sub_id_match: Boolean(row.sub_id_match),
          up_bytes: Number(row.up_bytes || 0),
          down_bytes: Number(row.down_bytes || 0),
          total_bytes: Number(row.total_bytes || 0),
          total_gb: Number(row.total_gb || 0),
          last_online_at: row.last_online_at ?? null,
          last_online_age_seconds: row.last_online_age_seconds == null ? null : Number(row.last_online_age_seconds),
          vless_link: row.vless_link ?? "",
          panel_error: row.panel_error ?? null,
          policy: row.policy ?? null,
        }))
      : [],
    key_history: Array.isArray(data.key_history) ? data.key_history : [],
    key_policies: Array.isArray(data.key_policies) ? data.key_policies : [],
    admin_actions: Array.isArray(data.admin_actions) ? data.admin_actions : [],
    summary: data.summary
      ? {
          nodes_total: Number(data.summary.nodes_total || 0),
          nodes_with_client: Number(data.summary.nodes_with_client || 0),
          nodes_online: Number(data.summary.nodes_online || 0),
          online_keys_now: Number(data.summary.online_keys_now || 0),
          online_connections_now: Number(data.summary.online_connections_now || 0),
          active_users_estimate: Number(data.summary.active_users_estimate || 0),
          active_users_source: data.summary.active_users_source ?? null,
          online_node_codes_now: Array.isArray(data.summary.online_node_codes_now)
            ? data.summary.online_node_codes_now.map((value) => String(value || ""))
            : [],
          nodes_enabled: Number(data.summary.nodes_enabled || 0),
          subid_mismatch_count: Number(data.summary.subid_mismatch_count || 0),
          traffic_up_bytes: Number(data.summary.traffic_up_bytes || 0),
          traffic_down_bytes: Number(data.summary.traffic_down_bytes || 0),
          traffic_total_bytes: Number(data.summary.traffic_total_bytes || 0),
          traffic_total_gb: Number(data.summary.traffic_total_gb || 0),
          panel_state: String(data.summary.panel_state || "ok"),
          panel_error: data.summary.panel_error ?? null,
        }
      : undefined,
    observer: normalizeAdminObserverBlock(data.observer),
  } as AdminUserCard;
}

export async function adminSummary(): Promise<AdminSummaryPayload> {
  const data = await apiFetch<Partial<AdminSummaryPayload>>("/api/admin/summary");
  return normalizeAdminSummaryPayload(data);
}

export async function adminUsers(params: AdminUsersQuery = {}): Promise<AdminUsersResponse> {
  const qs = new URLSearchParams();
  if (params.q) qs.set("q", params.q);
  if (params.status) qs.set("status", params.status);
  if (params.origin) qs.set("origin", params.origin);
  if (params.observer_state) qs.set("observer_state", params.observer_state);
  if (params.sort) qs.set("sort", params.sort);
  if (params.page) qs.set("page", String(params.page));
  if (params.page_size) qs.set("page_size", String(params.page_size));
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  const data = await apiFetch<Partial<AdminUsersResponse>>(`/api/admin/users${suffix}`);
  return normalizeAdminUsersResponse(data);
}

export async function adminUserCard(tgId: number): Promise<AdminUserCard> {
  const data = await apiFetch<Partial<AdminUserCard>>(`/api/admin/users/${tgId}`);
  return normalizeAdminUserCard(data);
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

export async function adminNetworkRolloutConfig(): Promise<{ network_rollout_config: AdminNetworkRolloutConfig }> {
  const data = await apiFetch<Partial<{ network_rollout_config: AdminNetworkRolloutConfig }>>("/api/admin/network-rollout-config");
  return {
    network_rollout_config: normalizeAdminNetworkRolloutConfig(data.network_rollout_config),
  };
}

export function adminNetworkRolloutConfigUpdate(
  payload: AdminNetworkRolloutConfig,
) : Promise<{ ok: boolean; network_rollout_config: AdminNetworkRolloutConfig }> {
  return apiFetch<Partial<{ ok: boolean; network_rollout_config: AdminNetworkRolloutConfig }>>("/api/admin/network-rollout-config", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then((data) => ({
    ok: Boolean(data.ok),
    network_rollout_config: normalizeAdminNetworkRolloutConfig(data.network_rollout_config),
  }));
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

export function adminDeleteTestUser(tgId: number): Promise<{ ok: boolean; tg_id: number; panel_deleted?: boolean }> {
  return apiFetch(`/api/admin/users/${tgId}/safe-delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
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
  const data = await apiFetch<{ nodes: Partial<AdminNodeHealthRow>[] }>("/api/admin/nodes/health");
  return Array.isArray(data.nodes) ? data.nodes.map((row) => normalizeAdminNodeHealthRow(row)) : [];
}

export async function adminMetricsStatus(): Promise<AdminMetricsStatus> {
  const data = await apiFetch<Partial<AdminMetricsStatus>>("/api/admin/metrics/status");
  return normalizeAdminMetricsStatus(data);
}

export function adminNodesSync(payload: { tg_id?: number; segment?: string; limit?: number }): Promise<any> {
  return apiFetch<any>("/api/admin/nodes/sync", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminNodesDrift(only?: string[]): Promise<AdminNodeDriftReport> {
  const qs = new URLSearchParams();
  if (only?.length) qs.set("only", only.join(","));
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiFetch<AdminNodeDriftReport>(`/api/admin/nodes/drift${suffix}`);
}

export function adminNodeDrain(code: string): Promise<{ ok: boolean; node: AdminNodeHealthRow }> {
  return apiFetch(`/api/admin/nodes/${encodeURIComponent(code)}/drain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export function adminNodeEnable(code: string): Promise<{ ok: boolean; node: AdminNodeHealthRow }> {
  return apiFetch(`/api/admin/nodes/${encodeURIComponent(code)}/enable`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export function adminNodeDisable(code: string, payload?: { force?: boolean }): Promise<{ ok: boolean; node: AdminNodeHealthRow }> {
  return apiFetch(`/api/admin/nodes/${encodeURIComponent(code)}/disable`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
}

export function adminNodeResync(
  code: string,
  payload?: { limit?: number; dry_run?: boolean },
): Promise<{ ok: boolean; node_code: string; count: number; migrated: number; failed: number; skipped: number; dry_run: boolean; details: Array<Record<string, unknown>> }> {
  return apiFetch(`/api/admin/nodes/${encodeURIComponent(code)}/resync`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
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

export function adminAccessKeysIssue(payload: {
  plan_code: string;
  quantity?: number;
}): Promise<{
  ok: boolean;
  plan: PlanCatalogRow;
  issued: Array<{
    key: string;
    plan: PlanCatalogRow;
    issued_at?: string | null;
  }>;
}> {
  return apiFetch("/api/admin/access-keys/issue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function adminPromoSlots(): Promise<AdminPromoSlotsPayload> {
  return apiFetch<AdminPromoSlotsPayload>("/api/admin/promo-slots");
}

export function adminPromoSlotsUpdate(payload: {
  assignments: PromoSlotAssignmentPayload[];
}): Promise<{
  ok: boolean;
  promo_slots: {
    version: string;
    mode: string;
    remote_available: boolean;
    fallback_behavior: string;
    assignments: PromoSlotAssignmentPayload[];
  };
}> {
  return apiFetch("/api/admin/promo-slots", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
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
