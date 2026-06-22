import { expect, test, type Page } from "@playwright/test";

type AdminUserRowMock = {
  tg_id: number;
  username?: string | null;
  display_name?: string | null;
  sub_type: string;
  is_active: boolean;
  effective_active?: boolean;
  status: "active" | "expired" | "blocked" | "manual_test";
  origin: "telegram" | "app" | "hybrid" | "manual_test";
  is_manual?: boolean;
  expiry_at?: string | null;
  stars_paid: number;
  created_at?: string | null;
  linked_telegram_id?: number | null;
  linked_telegram_username?: string | null;
  app_install_id?: string | null;
  observer_state?: "ok" | "watch" | "suspicious";
  observer_updated_at?: string | null;
};

type MockOptions = {
  isAdmin: boolean;
  adminSummary?: unknown;
  userRows?: AdminUserRowMock[];
  paymentOrders?: PaymentOrderMock[];
  metricsStatus?: unknown;
  nodeHealth?: unknown;
  networkRolloutConfig?: unknown;
  tickets?: TicketMock[];
};

type TicketMessageMock = {
  id: number;
  sender_role: "user" | "admin";
  body: string;
  created_at?: string | null;
};

type TicketMock = {
  id: number;
  user_tg_id: number;
  status: "open" | "in_progress" | "closed";
  status_title: string;
  subject?: string | null;
  updated_at?: string | null;
  last_message_preview?: string | null;
  messages: TicketMessageMock[];
};

type PaymentOrderMock = {
  id: number;
  order_id: string;
  provider: string;
  tg_id?: number | null;
  plan_code?: string | null;
  amount: number;
  currency: string;
  status: string;
  source?: string | null;
  campaign?: string | null;
  promo_code?: string | null;
  created_at?: string | null;
  paid_at?: string | null;
  event_count: number;
  last_event?: {
    event_type: string;
    external_id: string;
    signature_ok: boolean;
    processed_ok: boolean;
    created_at?: string | null;
  } | null;
};

function mockSessionUser(isAdmin: boolean) {
  return {
    tg_id: 1001,
    username: "qa_admin",
    subscription_url: "https://connect.pokrov.space/s8Kx2mP7qR4wT/mock_token",
    is_active: true,
    is_admin: isAdmin,
    sub_type: "PAID",
    segment: "PAID",
    access_state: "paid_unlimited",
    expiry_at: "2030-01-01T00:00:00",
    family_slots: 0,
    devices: [],
    sync: {
      app_identity_known: false,
      telegram_linked: true,
      subscription_ready: true,
      device_count: 0,
    },
    nodes: [],
    limits: { device_limit: 5, total_gb: 0, speed_mbps: 100 },
    traffic: { used_gb: 0, used_bytes: 0, total_gb: 0, remaining_gb: 0, source: "panel_runtime" },
    traffic_policy: {
      kind: "unlimited",
      label: "Безлимитный трафик",
      limit_gb: null,
      remaining_gb: null,
      next_reset_at: null,
      soft_mode_active: false,
    },
    traffic_limit_gb: null,
    traffic_remaining_gb: null,
    next_reset_at: null,
    soft_mode_active: false,
    connections: {
      status: "online",
      active_connections: 0,
      active_nodes: 0,
      known_nodes: 0,
      last_online_at: null,
      last_online_age_seconds: null,
      source: "panel_runtime",
    },
    support: {
      username: "pokrov_supportbot",
      link: "https://t.me/pokrov_supportbot",
      new_ticket_link: "https://t.me/pokrov_supportbot?start=ticket_new",
    },
    bonuses: {
      wheel: { last_spin_at: null, streak_months: 0 },
      referral_count: 0,
      channel_bonus: { premium_days: 0, claimed_at: null, can_claim: false },
    },
    referral: { code: "mock", link: "https://t.me/pokrov_vpnbot?start=ref_mock", bonus_days: 0 },
    channel: { username: "pokrov_vpn", link: "https://t.me/pokrov_vpn", subscriber: true, speed_bump_active: false },
    actions: {
      open_helpbot: "https://t.me/pokrov_supportbot",
      open_channel: "https://t.me/pokrov_vpn",
      pay_via_bot: "https://t.me/pokrov_vpnbot?start=pay",
    },
    points: { available: 0, expiring_soon: 0, monthly_cap: 300, expires_days: 90 },
    features: { haptic: true, lottie: true },
  };
}

function mockDashboard() {
  return {
    tg_id: 1001,
    sub_type: "PAID",
    current_plan_code: "1_month",
    segment: "PAID",
    access_state: "paid_unlimited",
    is_active: true,
    expiry_at: "2030-01-01T00:00:00",
    used_gb: 0,
    total_gb: 0,
    remaining_gb: 0,
    active_sessions: 0,
    active_sessions_source: "panel_ip_count",
    device_limit: 5,
    speed_limit_mbps: 100,
    free_next_reset_at: null,
    traffic_policy: {
      kind: "unlimited",
      label: "Безлимитный трафик",
      limit_gb: null,
      remaining_gb: null,
      next_reset_at: null,
      soft_mode_active: false,
    },
    traffic_limit_gb: null,
    traffic_remaining_gb: null,
    next_reset_at: null,
    soft_mode_active: false,
    family_slots: 0,
    subscription_url: "https://connect.pokrov.space/s8Kx2mP7qR4wT/mock_token",
    connection_snapshot: {
      status: "online",
      active_connections: 0,
      active_nodes: 0,
      known_nodes: 0,
      last_online_at: null,
      last_online_age_seconds: null,
      source: "panel_runtime",
    },
    active_offer: null,
    points: { available: 0, expiring_soon: 0, monthly_cap: 300, expires_days: 90 },
    features: { haptic: true, lottie: true },
  };
}

function mockAdminSummary() {
  return {
    actor_tg_id: 1001,
    users: { total: 3, active: 2, free: 0, paid: 2 },
    observer: { watch_users: 0, suspicious_users: 0 },
    retention: {
      expiring_3d: 0,
      expired_7d: 1,
      reactivation_candidates: 1,
      pings_24h: {
        welcome: 0,
        t3: 0,
        t1: 0,
        t0: 0,
        reactivation: 0,
        start99_offer: 0,
      },
    },
    tickets: { open: 0 },
    nodes: { healthy: 1, total: 1 },
    errors: {
      stale_metrics: false,
      unhealthy_nodes: 0,
      open_tickets: 0,
      payment_callback_failures_24h: 0,
      subscription_numeric_fallbacks_24h: 0,
    },
    resilience: {
      single_point_risk: false,
      free_node_enabled: true,
    },
    bonus_events_24h: {
      channel_activated: 0,
      channel_denied: 0,
      promo_redeemed: 0,
      promo_denied: 0,
      gift_redeemed: 0,
      gift_denied: 0,
    },
    top_nodes: [
      {
        code: "us",
        health_score: 8.4,
        panel_latency_ms: 42,
        active_clients: 25,
        last_health_at: "2030-01-01T00:00:00",
      },
    ],
  };
}

function makeAdminUserRow(overrides: Partial<AdminUserRowMock> = {}): AdminUserRowMock {
  return {
    tg_id: 1001,
    username: "qa_admin",
    display_name: "QA Admin",
    sub_type: "PAID",
    is_active: true,
    effective_active: true,
    status: "active",
    origin: "hybrid",
    is_manual: false,
    expiry_at: "2030-01-01T00:00:00",
    stars_paid: 0,
    created_at: "2029-12-01T00:00:00",
    linked_telegram_id: 1001,
    linked_telegram_username: "qa_admin",
    app_install_id: "android-qa",
    observer_state: "ok",
    observer_updated_at: "2030-01-01T00:00:00",
    ...overrides,
  };
}

function mockAdminUsers() {
  return {
    users: [makeAdminUserRow()],
    total: 1,
    page: 1,
    page_size: 80,
    sort: "created_desc",
  };
}

function mockAdminUserCard() {
  return {
    user: {
      tg_id: 1001,
      username: "qa_admin",
      display_name: "QA Admin",
      sub_type: "PAID",
      is_active: true,
      effective_active: true,
      status: "active",
      origin: "hybrid",
      is_manual: false,
      expiry_at: "2030-01-01T00:00:00",
      stars_paid: 0,
      total_gb: 0,
      trial_used: true,
      referral_count: 0,
      streak_months: 0,
      created_at: "2029-12-01T00:00:00",
      subscription_url: "https://connect.pokrov.space/s8Kx2mP7qR4wT/mock_token",
      subscription_token: "mock_token",
      linked_telegram_id: 1001,
      linked_telegram_username: "qa_admin",
      app_install_id: "android-qa",
      app_platform: "android",
      app_last_seen_at: "2030-01-01T00:00:00",
      observer_state: "ok",
      observer_updated_at: "2030-01-01T00:00:00",
    },
    tickets: [],
    keys: [],
    key_history: [],
    key_policies: [],
    admin_actions: [],
    risk: {
      score: 0,
      level: "low",
      window_days: 30,
      signals: {
        regen_count: 0,
        admin_key_ops: 0,
        unique_ips: 0,
        traffic_gb: 0,
        subid_mismatch_count: 0,
      },
      factors: [],
      updated_at: "2030-01-01T00:00:00",
    },
    observer: {
      state: "ok",
      reasons: [],
      observed_ip_count_24h: 0,
      observed_ip_count_7d: 0,
      observed_ip_count_30d: 0,
      observed_node_count_24h: 0,
      observed_node_count_7d: 0,
      observed_node_count_30d: 0,
      overlap_count_24h: 0,
      last_observed_at: null,
      updated_at: "2030-01-01T00:00:00",
      recent_ips: [],
      recent_nodes: [],
    },
    loyalty: {
      enabled: true,
      streak_days: 0,
      tiers: [],
    },
    summary: {
      nodes_total: 1,
      nodes_with_client: 1,
      nodes_online: 1,
      online_keys_now: 1,
      online_connections_now: 2,
      active_users_estimate: 1,
      active_users_source: "panel_ip_count_capped_by_unique_ip_24h",
      nodes_enabled: 1,
      subid_mismatch_count: 0,
      traffic_up_bytes: 0,
      traffic_down_bytes: 0,
      traffic_total_bytes: 0,
      traffic_total_gb: 0,
      panel_state: "ok",
      panel_error: null,
    },
  };
}

function buildAdminUserCard(row: AdminUserRowMock) {
  const base = mockAdminUserCard();
  return {
    ...base,
    user: {
      ...base.user,
      ...row,
      tg_id: row.tg_id,
      username: row.username ?? null,
      display_name: row.display_name ?? null,
      sub_type: row.sub_type,
      is_active: row.is_active,
      effective_active: row.effective_active,
      status: row.status,
      origin: row.origin,
      is_manual: row.is_manual,
      expiry_at: row.expiry_at ?? null,
      stars_paid: row.stars_paid,
      created_at: row.created_at ?? null,
      linked_telegram_id: row.linked_telegram_id ?? null,
      linked_telegram_username: row.linked_telegram_username ?? null,
      app_install_id: row.app_install_id ?? null,
      observer_state: row.observer_state ?? "ok",
      observer_updated_at: row.observer_updated_at ?? "2030-01-01T00:00:00",
    },
    observer: {
      ...base.observer,
      state: row.observer_state ?? "ok",
      updated_at: row.observer_updated_at ?? "2030-01-01T00:00:00",
      reasons:
        row.observer_state === "suspicious"
          ? ["multi_node_overlap_10m"]
          : row.observer_state === "watch"
            ? ["multi_ip_multi_node_24h"]
            : [],
      observed_ip_count_24h: row.observer_state === "suspicious" ? 5 : row.observer_state === "watch" ? 3 : 0,
      observed_ip_count_7d: row.observer_state === "suspicious" ? 6 : row.observer_state === "watch" ? 5 : 0,
      observed_ip_count_30d: row.observer_state === "suspicious" ? 6 : row.observer_state === "watch" ? 5 : 0,
      observed_node_count_24h: row.observer_state === "ok" ? 0 : 2,
      observed_node_count_7d: row.observer_state === "ok" ? 0 : 2,
      observed_node_count_30d: row.observer_state === "ok" ? 0 : 2,
      overlap_count_24h: row.observer_state === "suspicious" ? 1 : 0,
      last_observed_at: row.observer_updated_at ?? "2030-01-01T00:00:00",
      recent_ips:
        row.observer_state === "ok"
          ? []
          : [
              {
                source_ip_raw: "8.8.8.8",
                score_ip_key: "8.8.8.8",
                node_code: "pl",
                node_name: "Poland",
                last_seen_at: "2030-01-01T00:00:00",
                counts_for_suspicion: true,
              },
              {
                source_ip_raw: row.observer_state === "suspicious" ? "9.9.9.9" : "1.1.1.1",
                score_ip_key: row.observer_state === "suspicious" ? "9.9.9.9" : "1.1.1.1",
                node_code: "de",
                node_name: "Germany",
                last_seen_at: "2030-01-01T00:05:00",
                counts_for_suspicion: true,
              },
            ],
      recent_nodes:
        row.observer_state === "ok"
          ? []
          : [
              { node_id: 1, node_code: "pl", node_name: "Poland", last_seen_at: "2030-01-01T00:00:00", score_ip_count: 2 },
              { node_id: 2, node_code: "de", node_name: "Germany", last_seen_at: "2030-01-01T00:05:00", score_ip_count: 1 },
            ],
    },
  };
}

function mockMetricsStatus() {
  return {
    status: "fresh",
    last_sample_at: "2030-01-01T00:00:00",
    age_seconds: 30,
    stale_after_seconds: 900,
    nodes: [
      {
        node_code: "us",
        status: "fresh",
        last_sample_at: "2030-01-01T00:00:00",
        age_seconds: 30,
        cpu_percent: 42,
        memory_percent: 58,
        disk_percent: 61,
        active_clients: 25,
        observer_last_push_at: "2030-01-01T00:00:00",
        observer_is_stale: false,
        alert_kinds: [],
      },
    ],
    active_alerts: [],
  };
}

function mockNodeHealth() {
  return {
    nodes: [
      {
        code: "us",
        name: "US",
        enabled: true,
        accepting_new_clients: true,
        is_draining: false,
        mapped_users: 25,
        is_healthy: true,
        health_score: 8.4,
        panel_latency_ms: 42,
        panel_error_rate: 0,
        active_clients: 25,
        cpu_percent: 42,
        memory_used_mb: 1024,
        memory_total_mb: 2048,
        disk_used_gb: 80,
        disk_total_gb: 160,
        disk_free_gb: 80,
        last_ok_at: "2030-01-01T00:00:00",
        last_health_at: "2030-01-01T00:00:00",
        last_probe_stage: null,
        last_probe_error_kind: null,
        last_probe_error_message: null,
        hoster_family: null,
        hoster_asn: null,
        subnet: null,
        probe_classification: null,
        ipv4_health: null,
        ipv6_health: null,
        transport_health: null,
        transport_profiles: {
          legacy_reality_fallback: {
            name: "legacy_reality_fallback",
            kind: "reality",
            enabled: true,
            inbound_id: 1,
            host: "us.pokrov.space",
            port: 443,
            tls_server_name: "www.example.com",
          },
        },
        observer_last_push_at: "2030-01-01T00:00:00",
        observer_unmatched_count: 0,
        observer_parse_error_count: 0,
        observer_is_stale: false,
        weight: 1,
      },
    ],
  };
}

function mockNetworkRolloutConfig() {
  return {
    version: "2026-04-13-rollout",
    defaults: {
      routing_mode_default: "all_except_ru",
      transport_profile: "legacy_reality_fallback",
      dns_policy: "ru_direct_split",
      ip_version_preference: "ipv4_only",
    },
    carrier_overrides: {
      mts: {
        transport_profile: "grpc_443_primary",
        dns_policy: "remote_only",
      },
    },
    cohort_overrides: {
      "install-default": {
        transport_profile: "grpc_443_primary",
        dns_policy: "remote_only",
        routing_mode_default: "full_tunnel",
        ip_version_preference: "prefer_ipv6",
        install_ids: ["install-default-android", "install-default-windows"],
        tg_ids: [1001, 1002],
        linked_tg_ids: [2001],
        platforms: ["android", "windows"],
      },
    },
    operator_lab: {
      enabled: true,
      allowlist_install_ids: ["operator-device"],
      allowlist_tg_ids: [3001],
      allowlist_node_codes: ["pl"],
      expires_at: "2030-01-02T00:00:00",
    },
    package_catalog_feed: {
      version: "package-feed-v2",
    },
    routing_rules_feed: {
      version: "rules-feed-v7",
    },
    support_recovery_order: ["app", "web", "telegram"],
  };
}

function cloneJson<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function ticketStatusTitle(status: TicketMock["status"]): string {
  if (status === "in_progress") return "В работе";
  if (status === "closed") return "Закрыт";
  return "Открыт";
}

function makeTicketMessage(overrides: Partial<TicketMessageMock> = {}): TicketMessageMock {
  return {
    id: 1,
    sender_role: "user",
    body: "Не получается подключиться после оплаты.",
    created_at: "2030-01-01T00:00:00",
    ...overrides,
  };
}

function makeTicket(overrides: Partial<TicketMock> = {}): TicketMock {
  const status = overrides.status ?? "open";
  return {
    id: 1,
    user_tg_id: 1001,
    status,
    status_title: overrides.status_title ?? ticketStatusTitle(status),
    subject: "Не работает VPN",
    updated_at: "2030-01-01T00:00:00",
    last_message_preview: "Не получается подключиться после оплаты.",
    messages: [makeTicketMessage()],
    ...overrides,
  };
}

function makePaymentOrder(overrides: Partial<PaymentOrderMock> = {}): PaymentOrderMock {
  return {
    id: 1,
    order_id: "order-review-2403",
    provider: "freekassa",
    tg_id: 2403,
    plan_code: "start_99",
    amount: 99,
    currency: "RUB",
    status: "manual_review",
    source: "checkout",
    campaign: "beta",
    promo_code: "WELCOME20",
    created_at: "2030-01-01T00:00:00",
    paid_at: null,
    event_count: 1,
    last_event: {
      event_type: "result",
      external_id: "tx-review-2403",
      signature_ok: true,
      processed_ok: false,
      created_at: "2030-01-01T00:03:00",
    },
    ...overrides,
  };
}

function normalizeDate(value?: string | null): number {
  if (!value) return 0;
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? timestamp : 0;
}

function filterAdminUsers(rows: AdminUserRowMock[], url: URL) {
  const q = (url.searchParams.get("q") || "").trim().toLowerCase();
  const status = (url.searchParams.get("status") || "all").trim().toLowerCase();
  const origin = (url.searchParams.get("origin") || "all").trim().toLowerCase();
  const observerState = (url.searchParams.get("observer_state") || "all").trim().toLowerCase();
  const sort = (url.searchParams.get("sort") || "created_desc").trim().toLowerCase();
  const page = Math.max(1, Number(url.searchParams.get("page") || 1));
  const pageSize = Math.max(1, Number(url.searchParams.get("page_size") || 80));

  let filtered = [...rows];

  if (q) {
    filtered = filtered.filter((row) => {
      const haystack = [
        row.display_name,
        row.username,
        String(row.tg_id),
        row.linked_telegram_username,
        row.linked_telegram_id != null ? String(row.linked_telegram_id) : "",
        row.app_install_id,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(q);
    });
  }

  if (status !== "all") {
    filtered = filtered.filter((row) => {
      if (status === "inactive") return row.status === "expired" || row.status === "blocked";
      return row.status === status;
    });
  }

  if (origin !== "all") {
    filtered = filtered.filter((row) => row.origin === origin);
  }

  if (observerState !== "all") {
    filtered = filtered.filter((row) => (row.observer_state || "ok") === observerState);
  }

  filtered.sort((left, right) => {
    if (sort === "created_asc") return normalizeDate(left.created_at) - normalizeDate(right.created_at) || left.tg_id - right.tg_id;
    if (sort === "expiry_asc") return normalizeDate(left.expiry_at) - normalizeDate(right.expiry_at) || left.tg_id - right.tg_id;
    if (sort === "expiry_desc") return normalizeDate(right.expiry_at) - normalizeDate(left.expiry_at) || right.tg_id - left.tg_id;
    if (sort === "name_asc") {
      const leftName = String(left.display_name || left.username || "").toLowerCase();
      const rightName = String(right.display_name || right.username || "").toLowerCase();
      return leftName.localeCompare(rightName) || left.tg_id - right.tg_id;
    }
    return normalizeDate(right.created_at) - normalizeDate(left.created_at) || right.tg_id - left.tg_id;
  });

  const total = filtered.length;
  const start = (page - 1) * pageSize;
  const paged = filtered.slice(start, start + pageSize);

  return {
    users: paged,
    total,
    page,
    page_size: pageSize,
    sort,
  };
}

async function registerApiMocks(page: Page, opts: MockOptions): Promise<void> {
  await page.addInitScript(() => {
    window.localStorage.setItem("portal_web_session_token", "e2e_mock_token");
  });

  const user = mockSessionUser(opts.isAdmin);
  const dashboard = mockDashboard();
  const adminSummary = opts.adminSummary ?? mockAdminSummary();
  const metricsStatus = opts.metricsStatus ?? mockMetricsStatus();
  const nodeHealth = opts.nodeHealth ?? mockNodeHealth();
  let networkRolloutConfig = cloneJson(opts.networkRolloutConfig ?? mockNetworkRolloutConfig());
  let userRows = [...(opts.userRows || mockAdminUsers().users)];
  let tickets = [...(opts.tickets || [makeTicket()])];
  let paymentOrders = [...(opts.paymentOrders || [makePaymentOrder()])];
  let promoSlotAssignments = [
    {
      slot_id: "marketing.checkout.contextual",
      content_id: "beta_checkout_honest",
      enabled: true,
      title: "",
      body: "",
      cta_label: "",
      cta_href: "",
      contexts: ["checkout"],
      sort_order: 1,
    },
  ];

  await page.route("**/release-status.json", async (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        source_artifact: "e2e-release-status.json",
        verdict: "NO_GO",
        classification: "BLOCKED_BY_ACCESS",
        safe_to_publish_public_beta: false,
        checks: [
          {
            name: "brain_origin_static_deploy_verify",
            status: "PASS_STATIC_NO_GO",
            note: "Static deploy evidence only; runtime sync and paid checkout remain closed.",
          },
          {
            name: "paid_checkout_launch_evidence",
            status: "BLOCKED_BY_ACCESS",
            missing: ["lavatop_invoice", "webhook_replay", "email_key_delivery"],
          },
        ],
        safe_public_claims: ["POKROV is preparing a limited Android and Windows beta."],
        unsafe_public_claims: ["Public beta is live.", "Lava.top payments are live."],
      }),
    }),
  );

  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const json = (payload: unknown, status = 200) =>
      route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(payload),
      });

    if (path === "/api/dashboard") return json(dashboard);
    if (path.startsWith("/api/user/")) return json(user);
    if (path === "/api/client/apps") {
      return json({
        android: {
          play_url: "",
          apk_url: "https://github.com/kiwun/pokrov/releases/download/v0.2.0-beta.1/POKROV-Android.apk",
          mirror_url: "",
        },
        windows: {
          exe_url: "https://github.com/kiwun/pokrov/releases/download/v0.2.0-beta.1/POKROV-Windows.exe",
          mirror_url: "",
        },
        docs_url: "https://pokrov.space/install/",
        updated_at: "2030-01-01T00:00:00",
      });
    }
    if (path === "/api/auth/email/status") {
      return json({
        ok: true,
        enabled: true,
        public_enabled: true,
        delivery_configured: true,
        delivery_secret_configured: true,
        debug_echo: false,
        mode: "public",
        blocked_reasons: [],
      });
    }
    if (path === "/api/payments/providers") {
      return json({
        ok: true,
        blocked: true,
        blocked_reasons: ["post_deploy_payment_evidence_missing"],
        blocked_reason_texts: ["post-deploy Lava.top evidence is missing"],
        providers: [
          {
            code: "lavatop",
            label: "Lava.top",
            enabled: true,
            currency: "RUB",
          },
        ],
      });
    }

    if (path === "/api/admin/summary") return json(adminSummary);
    if (path === "/api/admin/metrics/status") return json(metricsStatus);
    if (path === "/api/admin/metrics/timeseries") return json({ from: "2029-12-26", to: "2030-01-01", points: [] });
    if (path === "/api/admin/nodes/health") return json(nodeHealth);
    if (path === "/api/admin/nodes/traffic") return json({ rows: [] });
    if (path === "/api/admin/network-rollout-config") {
      if (request.method() === "PUT") {
        networkRolloutConfig = cloneJson(JSON.parse(request.postData() || "{}"));
        return json({ ok: true, network_rollout_config: networkRolloutConfig });
      }
      return json({ network_rollout_config: networkRolloutConfig });
    }
    if (path === "/api/admin/users") return json(filterAdminUsers(userRows, url));
    if (path.startsWith("/api/admin/users/")) {
      const match = path.match(/^\/api\/admin\/users\/(-?\d+)(?:\/(.+))?$/);
      const tgId = Number(match?.[1] || 0);
      const action = String(match?.[2] || "");
      const row = userRows.find((item) => item.tg_id === tgId);

      if (request.method() === "POST" && (action === "safe-delete" || action === "delete-test-user")) {
        if (!row || row.status !== "manual_test") {
          return json({ detail: "Only manual/test users can be deleted" }, 400);
        }
        userRows = userRows.filter((item) => item.tg_id !== tgId);
        return json({ ok: true, tg_id: tgId, panel_deleted: true });
      }

      if (!row) {
        return json({ detail: "User not found" }, 404);
      }

      if (!action && request.method() === "GET") return json(buildAdminUserCard(row));
      if (action === "key-history") return json({ rows: [] });
      if (action === "key-limits") return json({ limits: [] });
      if (action === "risk") return json({ risk: mockAdminUserCard().risk });
      if (action === "loyalty") return json({ loyalty: mockAdminUserCard().loyalty });
      if (action === "loyalty/grant") return json({ ok: true, tier_days: 30, expiry_at: row.expiry_at, sync_ok: true });
      if (action === "presets/run") return json({ ok: true });
      if (action === "message") return json({ ok: true });
      if (action === "manual/extend" || action === "manual-extend") {
        return json({ ok: true, expiry_at: "2030-02-01T00:00:00", is_active: true, delta_days: 30 });
      }
      if (action === "manual/block") return json({ ok: true, is_active: false });
      if (action === "manual/regenerate-token") {
        return json({
          ok: true,
          subscription_url: "https://connect.pokrov.space/s8Kx2mP7qR4wT/manual_token",
          sync_ok: true,
        });
      }
      if (action.startsWith("keys/")) return json({ ok: true });
      return json({ ok: true });
    }
    if (path === "/api/admin/audit") return json({ rows: [] });
    if (path === "/api/admin/payments/orders") {
      return json({ orders: paymentOrders, total: paymentOrders.length, limit: 100, offset: 0 });
    }
    if (path.startsWith("/api/admin/payments/orders/") && path.endsWith("/reconcile") && request.method() === "POST") {
      const match = path.match(/^\/api\/admin\/payments\/orders\/([^/]+)\/([^/]+)\/reconcile$/);
      const provider = decodeURIComponent(String(match?.[1] || ""));
      const orderId = decodeURIComponent(String(match?.[2] || ""));
      const payload = JSON.parse(request.postData() || "{}");
      const note = String(payload.note || "").trim();
      if (!note) return json({ detail: "note is required" }, 422);
      const nextStatus = String(payload.status || "manual_review");
      const row = paymentOrders.find((order) => order.provider === provider && order.order_id === orderId);
      if (!row) return json({ detail: "Order not found" }, 404);
      const updated = { ...row, status: nextStatus };
      paymentOrders = paymentOrders.map((order) => (order.provider === provider && order.order_id === orderId ? updated : order));
      return json({ ok: true, order: updated });
    }
    if (path === "/api/admin/tickets") {
      const statusFilter = String(url.searchParams.get("status") || "").trim();
      return json({ tickets: statusFilter ? tickets.filter((ticket) => ticket.status === statusFilter) : tickets });
    }
    if (path.startsWith("/api/admin/tickets/")) {
      const match = path.match(/^\/api\/admin\/tickets\/(\d+)(?:\/(.+))?$/);
      const ticketId = Number(match?.[1] || 0);
      const action = String(match?.[2] || "");
      const row = tickets.find((ticket) => ticket.id === ticketId);

      if (!row) {
        return json({ detail: "Ticket not found" }, 404);
      }

      if (!action && request.method() === "GET") {
        return json({ ticket: row });
      }

      if (action === "reply" && request.method() === "POST") {
        const payload = JSON.parse(request.postData() || "{}");
        const body = String(payload.body || "").trim();
        const nextMessage: TicketMessageMock = {
          id: row.messages.length + 1,
          sender_role: "admin",
          body,
          created_at: "2030-01-01T00:05:00",
        };
        const updated: TicketMock = {
          ...row,
          updated_at: nextMessage.created_at,
          last_message_preview: body,
          messages: [...row.messages, nextMessage],
        };
        tickets = tickets.map((ticket) => (ticket.id === ticketId ? updated : ticket));
        return json({ ticket: updated });
      }

      if (action === "status" && request.method() === "POST") {
        const payload = JSON.parse(request.postData() || "{}");
        const nextStatus = String(payload.status || "open") as TicketMock["status"];
        const updated: TicketMock = {
          ...row,
          status: nextStatus,
          status_title: ticketStatusTitle(nextStatus),
          updated_at: "2030-01-01T00:03:00",
        };
        tickets = tickets.map((ticket) => (ticket.id === ticketId ? updated : ticket));
        return json({ ticket: updated });
      }

      return json({ ticket: row });
    }
    if (path === "/api/admin/access-keys/issue" && request.method() === "POST") {
      const payload = JSON.parse(request.postData() || "{}");
      const quantity = Math.max(1, Math.min(50, Number(payload.quantity || 1)));
      const plan = {
        code: String(payload.plan_code || "1_month"),
        label: "1 month",
        amount_rub: 249,
        amount_stars: 249,
        days: 30,
        duration_days: 30,
        device_limit: 5,
        node_policy: "paid_pool",
        is_active: true,
      };
      return json({
        ok: true,
        plan,
        issued: Array.from({ length: quantity }, (_, index) => ({
          key: `POKROV-TEST-${String(index + 1).padStart(4, "0")}`,
          plan,
          issued_at: "2030-01-01T00:00:00",
        })),
      });
    }
    if (path.startsWith("/api/access-keys/status/")) {
      const key = decodeURIComponent(path.split("/").pop() || "");
      return json({
        key,
        exists: key === "POKROV-TEST-0001",
        redeemed: false,
        issued_at: "2030-01-01T00:00:00",
        redeemed_at: null,
        plan: {
          code: "1_month",
          label: "1 month",
          amount_rub: 249,
          days: 30,
          duration_days: 30,
          device_limit: 5,
          node_policy: "paid_pool",
          is_active: true,
        },
        kind: "access_key",
        days: 30,
        device_limit: 5,
        node_policy: "paid_pool",
      });
    }
    if (path === "/api/admin/promo-slots") {
      if (request.method() === "PUT") {
        const payload = JSON.parse(request.postData() || "{}");
        promoSlotAssignments = Array.isArray(payload.assignments) ? payload.assignments : promoSlotAssignments;
        return json({
          ok: true,
          promo_slots: {
            version: "e2e-promo-slots",
            mode: "first_party",
            remote_available: true,
            fallback_behavior: "hide",
            assignments: promoSlotAssignments,
          },
        });
      }
      return json({
        promo_slots: {
          version: "e2e-promo-slots",
          mode: "first_party",
          remote_available: true,
          fallback_behavior: "hide",
          assignments: promoSlotAssignments,
          catalog: {
            version: "e2e-promo-slots",
            mode: "first_party",
            fallback_behavior: "hide",
            slots: [
              {
                id: "marketing.checkout.contextual",
                surface: "marketing.checkout",
                contexts: ["checkout"],
                allowed_content_ids: ["beta_checkout_honest"],
              },
            ],
            content_catalog: [
              {
                id: "beta_checkout_honest",
                kind: "payment_status",
                goal: "Keep checkout honest while Lava.top evidence is pending",
                default_enabled: true,
              },
            ],
          },
        },
      });
    }
    if (path === "/api/admin/promos") return json({ promos: [] });
    if (path === "/api/admin/gift-codes") return json({ gift_codes: [] });
    if (path === "/api/admin/plans") return json({ plans: [] });
    if (path === "/api/admin/live-updates") return json({ updates: [] });
    if (path === "/api/admin/start-links") return json({ start_links: [] });
    if (path === "/api/admin/wheel-config") {
      return json({ wheel_config: { preset: "balanced", cooldown_hours: 168, weights: [{ days: 1, weight: 100 }] } });
    }
    if (path === "/api/admin/campaign-links/build") {
      return json({
        ok: true,
        bot_start_link: "https://t.me/pokrov_vpnbot?start=x",
        checkout_link: "https://pay.pokrov.space/checkout/",
        webapp_link: "https://app.pokrov.space/",
      });
    }

    return json({ ok: true });
  });
}

async function openRoute(page: Page, href: string): Promise<void> {
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      await page.goto(href, { waitUntil: "domcontentloaded" });
      await waitForPortalShell(page);
      return;
    } catch (error) {
      const message = String((error as Error)?.message || error || "");
      const retryable =
        message.includes("ERR_ABORTED") ||
        message.includes("toBeHidden") ||
        message.includes("Подтягиваем данные кабинета");
      if (attempt === 2 || !retryable) {
        throw error;
      }
      await page.waitForTimeout(250);
    }
  }
}

async function waitForPortalShell(page: Page): Promise<void> {
  const loadingHeadings = [
    page.getByRole("heading", { name: "Подтягиваем данные кабинета" }),
    page.getByRole("heading", { name: "Открываем POKROV Admin..." }),
  ];

  for (const heading of loadingHeadings) {
    const visible = await heading.isVisible().catch(() => false);
    if (!visible) continue;
    await expect(heading).toBeHidden({ timeout: 15_000 });
  }
}

test.describe("Admin gate", () => {
  test("redirects non-admin from /admin/* to /dashboard", async ({ page }) => {
    await registerApiMocks(page, { isAdmin: false });
    await openRoute(page, "admin/dashboard/");
    await expect(page).toHaveURL(/\/dashboard\/?$/);
  });

  test("allows admin to open all admin sections", async ({ page }) => {
    await registerApiMocks(page, { isAdmin: true });

    const sections = [
      "admin/dashboard/",
      "admin/release/",
      "admin/users/",
      "admin/network/",
      "admin/nodes/",
      "admin/tickets/",
      "admin/promos/",
      "admin/payments/",
      "admin/broadcast/",
      "admin/referrals/",
      "admin/bonuses/",
    ];

    for (const section of sections) {
      await openRoute(page, section);
      await expect(page).toHaveURL(new RegExp(`/${section.replace(/\//g, "\\/")}$`));
      await expect(page.getByTestId("cabinet-shell")).toHaveCount(0);
      await expect(page.getByRole("navigation", { name: "Admin sections" })).toBeVisible();
      await expect(page.locator("h1, h2").first()).toBeVisible();
    }
  });

  test("shows the release cockpit as a guarded NO-GO surface", async ({ page }) => {
    await registerApiMocks(page, { isAdmin: true });

    await openRoute(page, "admin/release/");

    await expect(page).toHaveURL(/\/admin\/release\/?$/);
    await expect(page.getByRole("navigation", { name: "Admin sections" }).getByRole("link", { name: /Релиз|GO\/NO-GO/ })).toBeVisible();
    await expect(page.locator("body")).toContainText("NO_GO");
    await expect(page.locator("body")).toContainText("GitHub Releases");
    await expect(page.locator("body")).toContainText("Lava.top");
    await expect(page.locator("body")).toContainText("RUNTIME LINK SYNC AUDIT BEFORE ANNOUNCEMENT");
    await expect(page.locator("body")).toContainText("CONFIRM_NO_PUBLIC_ANNOUNCEMENT_YET");
    await expect(page.locator("body")).toContainText("Public beta is live.");
  });

  test("lets admin issue access keys, look them up, and save promo slots", async ({ page }) => {
    await registerApiMocks(page, { isAdmin: true });

    await openRoute(page, "admin/promos/");

    await expect(page.getByRole("heading", { name: "Выпустить ключи" })).toBeVisible();
    await page.locator('input[type="number"]').first().fill("1");
    await page.getByRole("button", { name: "Выпустить" }).click();
    await expect(page.locator("body")).toContainText("POKROV-TEST-0001");

    await page.getByPlaceholder("POKROV-XXXX-XXXX").fill("POKROV-TEST-0001");
    await page.getByRole("button", { name: "Проверить" }).click();
    await expect(page.locator("body")).toContainText("1 month");

    await page.getByRole("button", { name: /^Сохранить$/ }).click();
    await expect(page.locator("body")).toContainText("Подсказки сохранены.");
  });

  test("keeps an explicit path back to the cabinet from admin", async ({ page }) => {
    await registerApiMocks(page, { isAdmin: true });

    await openRoute(page, "admin/dashboard/");

    const cabinetLink = page.getByRole("link", { name: "Вернуться в кабинет" }).first();
    await expect(cabinetLink).toBeVisible();
    await cabinetLink.click();
    await expect(page).toHaveURL(/\/dashboard\/?$/);
  });

  test("groups admin routes by operational category and keeps Telegram as fallback only", async ({ page }) => {
    await registerApiMocks(page, { isAdmin: true });

    await openRoute(page, "admin/");

    await expect(page.getByRole("navigation", { name: "Admin sections" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Сводка" }).first()).toBeVisible();
    await expect(page.getByText("Веб-админка — основной путь")).toBeVisible();

    for (const category of ["Рабочий стол", "Люди", "Доступ и промо", "Оплата", "Сеть", "Сообщения", "Поддержка"]) {
      await expect(page.getByText(category).first()).toBeVisible();
    }
  });

  test("keeps admin dashboard stable when summary omits optional blocks", async ({ page }) => {
    const pageErrors: string[] = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));

    await registerApiMocks(page, {
      isAdmin: true,
      adminSummary: {
        actor_tg_id: 1001,
        users: { total: 1, active: 1, free: 0, paid: 1 },
        tickets: { open: 0 },
        nodes: { healthy: 1, total: 1 },
      },
    });

    await openRoute(page, "admin/dashboard/");
    await expect(page).toHaveURL(/\/admin\/dashboard\/?$/);
    await expect(page.getByRole("button", { name: /обновить|refresh/i })).toBeVisible();
    expect(pageErrors).toEqual([]);
  });

  test("shows clean Russian copy across admin surfaces", async ({ page }) => {
    await registerApiMocks(page, { isAdmin: true });

    await openRoute(page, "admin/dashboard/");
    await expect(page.getByRole("heading", { name: "Сводка смены" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Тревоги" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "В работе" })).toBeVisible();

    await openRoute(page, "admin/users/");
    await expect(page.getByRole("link", { name: /Сводка/ }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: /Пользователи/ }).first()).toBeVisible();
    await expect(page.getByPlaceholder("Поиск по username, Telegram ID, имени или установке приложения")).toBeVisible();
    await expect(page.getByRole("button", { name: "Создать тестового пользователя" })).toBeVisible();

    await openRoute(page, "admin/nodes/");
    await expect(page.getByRole("heading", { name: "Серверы и состояние инфраструктуры" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Проверить расхождения" })).toBeVisible();

    await openRoute(page, "admin/tickets/");
    await expect(page.getByText("Здесь собраны обращения пользователей.")).toBeVisible();
    await expect(page.getByPlaceholder("Напишите ответ пользователю простыми словами")).toBeVisible();
  });

  test("lets admin search, sort, and paginate the users table", async ({ page }) => {
    const userRows = Array.from({ length: 81 }, (_, index) =>
      makeAdminUserRow({
        tg_id: 2000 + index,
        username: `user_${String(index + 1).padStart(3, "0")}`,
        display_name: `User ${String(index + 1).padStart(3, "0")}`,
        origin: "telegram",
        created_at: new Date(Date.UTC(2030, 0, 1, 0, index, 0)).toISOString(),
        expiry_at: new Date(Date.UTC(2030, 1, 1, 0, index, 0)).toISOString(),
      }),
    );

    await registerApiMocks(page, { isAdmin: true, userRows });
    await openRoute(page, "admin/users/");

    await expect(page.getByText("Показаны 1-80 из 81 пользователей.", { exact: true })).toBeVisible();
    await expect(page.locator("tbody tr").first()).toContainText("User 081");

    await page.locator("select").nth(3).selectOption("name_asc");
    await expect(page.locator("tbody tr").first()).toContainText("User 001");

    await page.getByRole("button", { name: /Следующая|Дальше/ }).first().click();
    await expect(page.getByText("Показаны 81-81 из 81 пользователей.", { exact: true })).toBeVisible();
    await expect(page.locator("tbody tr").first()).toContainText("User 081");

    await page.getByPlaceholder("Поиск по username, Telegram ID, имени или установке приложения").fill("User 081");
    await expect(page.getByText("Показаны 1-1 из 1 пользователей.", { exact: true })).toBeVisible();
    await expect(page.locator("tbody tr").first()).toContainText("User 081");
  });

  test("keeps the users filters synced into the URL and restores them on reload", async ({ page }) => {
    const userRows = Array.from({ length: 81 }, (_, index) =>
      makeAdminUserRow({
        tg_id: 3000 + index,
        username: `user_${String(index + 1).padStart(3, "0")}`,
        display_name: `User ${String(index + 1).padStart(3, "0")}`,
        origin: "telegram",
        created_at: new Date(Date.UTC(2030, 0, 1, 0, index, 0)).toISOString(),
      }),
    );

    await registerApiMocks(page, { isAdmin: true, userRows });
    await openRoute(page, "admin/users/?q=User&status=all&origin=telegram&observer_state=all&sort=name_asc&page=2");

    await expect(page.getByPlaceholder("Поиск по username, Telegram ID, имени или установке приложения")).toHaveValue("User");
    await expect(page.locator("tbody tr").first()).toContainText("User 081");

    await page.getByPlaceholder("Поиск по username, Telegram ID, имени или установке приложения").fill("User 008");
    await expect.poll(() => new URL(page.url()).searchParams.get("q")).toBe("User 008");
    await expect.poll(() => new URL(page.url()).searchParams.get("page")).toBe("1");
    await expect(page.getByPlaceholder("Поиск по username, Telegram ID, имени или установке приложения")).toHaveValue("User 008");

    await page.reload({ waitUntil: "domcontentloaded" });
    await expect(page.getByPlaceholder("Поиск по username, Telegram ID, имени или установке приложения")).toHaveValue("User 008");
    await expect(page.locator("tbody tr").first()).toContainText("User 008");
  });

  test("lets admin safely delete only manual or test users", async ({ page }) => {
    const userRows = [
      makeAdminUserRow(),
      makeAdminUserRow({
        tg_id: -7001,
        username: null,
        display_name: "Router Lab",
        sub_type: "MANUAL",
        is_active: true,
        effective_active: false,
        status: "manual_test",
        origin: "manual_test",
        is_manual: true,
        linked_telegram_id: null,
        linked_telegram_username: null,
        app_install_id: null,
        created_at: "2030-01-02T00:00:00",
      }),
    ];

    await registerApiMocks(page, { isAdmin: true, userRows });
    await openRoute(page, "admin/users/");

    await page.locator("select").nth(0).selectOption("manual_test");
    await page.locator("select").nth(1).selectOption("manual_test");
    await expect(page.locator("tbody tr").first()).toContainText("Router Lab");

    await page.locator("tbody tr").first().click();
    await expect(page.getByRole("button", { name: "Удалить тестового пользователя" }).first()).toBeVisible();

    await page.getByRole("button", { name: "Удалить тестового пользователя" }).first().click();
    await expect(page.getByRole("heading", { name: "Удалить тестового пользователя" })).toBeVisible();
    await page.getByRole("button", { name: "Удалить пользователя" }).click();

    await expect(page.getByText("Тестовый пользователь удалён.")).toBeVisible();
    await expect(page.getByText("По текущим фильтрам пользователей нет.").first()).toBeVisible();
  });

  test("shows observer-lite badges, filters, and detail diagnostics", async ({ page }) => {
    const userRows = [
      makeAdminUserRow({
        tg_id: 3101,
        username: "watch_user",
        display_name: "Watch User",
        observer_state: "watch",
      }),
      makeAdminUserRow({
        tg_id: 3102,
        username: "suspicious_user",
        display_name: "Suspicious User",
        observer_state: "suspicious",
      }),
    ];

    await registerApiMocks(page, {
      isAdmin: true,
      adminSummary: {
        ...mockAdminSummary(),
        observer: { watch_users: 1, suspicious_users: 1 },
      },
      userRows,
    });

    await openRoute(page, "admin/dashboard/");
    await expect(page.getByRole("heading", { name: "Сводка смены" })).toBeVisible();
    await expect(page.getByText("Observer watch")).not.toBeVisible();
    await expect(page.getByText("Observer suspicious")).not.toBeVisible();

    await openRoute(page, "admin/users/");
    await page.locator("select").nth(2).selectOption("suspicious");
    await expect(page.locator("tbody tr").first()).toContainText("Suspicious User");
    await expect(page.locator("tbody tr").first()).toContainText("проверить");

    await page.locator("tbody tr").first().click();
    await expect(page.getByText("Проверка по IP и нодам")).toBeVisible();
    await expect(page.getByText("multi_node_overlap_10m").first()).toBeVisible();
    await expect(page.getByText("8.8.8.8")).toBeVisible();
    await expect(page.getByText("PL").first()).toBeVisible();
  });

  test("shows observer-lite empty state instead of misleading zero-only activity", async ({ page }) => {
    await registerApiMocks(page, {
      isAdmin: true,
      userRows: [makeAdminUserRow()],
    });

    await openRoute(page, "admin/users/");
    await expect(page.getByText("Подтягиваем данные кабинета")).not.toBeVisible();
    await expect(page.locator("tbody tr").first()).toContainText("QA Admin");
    await page.locator("tbody tr").first().click();
    await expect(page.getByText("Проверка по IP и нодам")).toBeVisible();
    await expect(page.getByText("Данных наблюдения пока нет.")).toBeVisible();
    await expect(page.getByText("No recent IPs.")).not.toBeVisible();
    await expect(page.getByText("No recent nodes.")).not.toBeVisible();
  });

  test("keeps admin pages clickable and inside the viewport on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await registerApiMocks(page, {
      isAdmin: true,
      userRows: [
        makeAdminUserRow({
          tg_id: -7001,
          username: null,
          display_name: "Router Lab",
          sub_type: "MANUAL",
          is_active: true,
          effective_active: false,
          status: "manual_test",
          origin: "manual_test",
          is_manual: true,
          linked_telegram_id: null,
          linked_telegram_username: null,
          app_install_id: null,
          created_at: "2030-01-02T00:00:00",
        }),
      ],
    });

    await openRoute(page, "admin/");
    await page.getByRole("link", { name: /Пользователи/i }).first().click();
    await expect(page).toHaveURL(/\/admin\/users\/?$/);

    await page.locator("select").nth(0).selectOption("manual_test");
    await page.locator("select").nth(1).selectOption("manual_test");
    await page.getByRole("button", { name: /Router Lab/ }).click();
    await page.getByRole("button", { name: "Удалить тестового пользователя" }).first().click();
    await expect(page.getByRole("button", { name: "Отмена" })).toBeVisible();
    await page.getByRole("button", { name: "Отмена" }).click();

    const usersWidth = await page.evaluate(() => ({
      viewport: window.innerWidth,
      page: document.documentElement.scrollWidth,
    }));
    expect(usersWidth.page).toBeLessThanOrEqual(usersWidth.viewport + 1);

    await openRoute(page, "admin/nodes/");
    const nodesWidth = await page.evaluate(() => ({
      viewport: window.innerWidth,
      page: document.documentElement.scrollWidth,
    }));
    expect(nodesWidth.page).toBeLessThanOrEqual(nodesWidth.viewport + 1);

    await openRoute(page, "admin/tickets/");
    await page.getByPlaceholder("Напишите ответ пользователю простыми словами").fill("Проверили мобильную админку.");
    await expect(page.getByRole("button", { name: "Отправить" })).toBeVisible();
    const ticketsWidth = await page.evaluate(() => ({
      viewport: window.innerWidth,
      page: document.documentElement.scrollWidth,
    }));
    expect(ticketsWidth.page).toBeLessThanOrEqual(ticketsWidth.viewport + 1);
  });

  test("shows node alert labels and probe failure details", async ({ page }) => {
    await registerApiMocks(page, {
      isAdmin: true,
      metricsStatus: {
        status: "stale",
        last_sample_at: "2030-01-01T00:00:00",
        age_seconds: 1800,
        stale_after_seconds: 900,
        nodes: [
          {
            node_code: "us",
            status: "stale",
            last_sample_at: "2030-01-01T00:00:00",
            age_seconds: 1800,
            cpu_percent: 88,
            memory_percent: 71,
            disk_percent: 61,
            active_clients: 240,
            observer_last_push_at: "2029-12-31T23:00:00",
            observer_is_stale: true,
            alert_kinds: ["client_density_high", "observer_push_stale"],
          },
        ],
        active_alerts: [
          {
            node_code: "us",
            kind: "observer_push_stale",
            status: "stale",
            age_seconds: 1800,
            last_sample_at: "2030-01-01T00:00:00",
          },
          {
            node_code: "us",
            kind: "client_density_high",
            status: "stale",
            age_seconds: 1800,
            last_sample_at: "2030-01-01T00:00:00",
          },
        ],
      },
      nodeHealth: {
        nodes: [
          {
            ...mockNodeHealth().nodes[0],
            active_clients: 240,
            last_probe_stage: "tls_sni",
            last_probe_error_kind: "tls_handshake_failed",
            last_probe_error_message: "tls handshake failed",
            hoster_family: "Hetzner",
            hoster_asn: "AS24940",
            subnet: "5.45.67.0/24",
            probe_classification: "provider_specific_path",
            ipv4_health: "degraded",
            ipv6_health: "unknown",
            transport_health: {
              dns_resolution: "healthy",
              tcp_connect: "healthy",
              tls_handshake: "degraded",
              reality_target: "degraded",
            },
            observer_last_push_at: "2029-12-31T23:00:00",
            observer_unmatched_count: 3,
            observer_parse_error_count: 2,
            observer_is_stale: true,
          },
        ],
      },
    });

    await openRoute(page, "admin/nodes/");
    await expect(page.getByText("US: Клиенты")).toBeVisible();
    await expect(page.locator(".badge", { hasText: "Нужно проверить данные" }).first()).toBeVisible();
    await expect(page.getByText(/Сбой проверки/i)).toBeVisible();
    await expect(page.getByText("tls handshake failed")).toBeVisible();
    await expect(page.getByText("US: Данные пользователей устарели")).toBeVisible();
    await expect(page.getByText("Сбор данных по пользователям")).toBeVisible();
    await expect(page.getByText("ошибки разбора: 2")).toBeVisible();
    await expect(page.getByText("без совпадения: 3")).toBeVisible();
  });

  test("shows node context with separate panel, dataplane, and transport detail", async ({ page }) => {
    await registerApiMocks(page, {
      isAdmin: true,
      nodeHealth: {
        nodes: [
          {
            ...mockNodeHealth().nodes[0],
            hoster_family: "Hetzner",
            hoster_asn: "AS24940",
            subnet: "5.45.67.0/24",
            probe_classification: "provider_specific_path",
            ipv4_health: "degraded",
            ipv6_health: "unknown",
            last_probe_stage: "reality_target",
            last_probe_error_kind: "reality_target_mismatch",
            last_probe_error_message: "certificate names do not match expected reality target",
            transport_health: {
              panel_state: "ok",
              panel_stage: "panel_inbound_lookup",
              panel_error_kind: "",
              panel_error_message: "",
              dataplane_state: "failed",
              dataplane_stage: "reality_target",
              dataplane_error_kind: "reality_target_mismatch",
              dataplane_error_message: "certificate names do not match expected reality target",
              root_cause_summary: "Panel sync is healthy, but the dataplane probe failed at the REALITY target validation stage.",
              root_cause_detail: "Telegram app path is blocked while the web path still resolves; certificate names do not match expected reality target.",
              dns_resolution: "healthy",
              tcp_connect: "healthy",
              tls_handshake: "degraded",
              reality_target: "degraded",
              telegram_app_path: "blocked",
              telegram_web_path: "healthy",
            },
            transport_profiles: {
              legacy_reality_fallback: {
                name: "legacy_reality_fallback",
                kind: "reality",
                enabled: true,
                inbound_id: 1,
                host: "us.pokrov.space",
                port: 443,
                tls_server_name: "www.example.com",
              },
              grpc_443_primary: {
                name: "grpc_443_primary",
                kind: "grpc",
                enabled: true,
                inbound_id: 2,
                host: "connect.pokrov.space",
                port: 443,
                tls_server_name: "connect.pokrov.space",
              },
            },
          },
        ],
      },
    });

    await openRoute(page, "admin/nodes/");
    const nodeCard = page.locator("article").filter({ hasText: "Хостинг" }).first();
    await expect(nodeCard.getByText(/Hetzner/i)).toBeVisible();
    await expect(nodeCard.getByText(/AS24940/)).toBeVisible();
    await expect(nodeCard.getByText("5.45.67.0/24")).toBeVisible();
    await expect(nodeCard.getByText(/Панель:/i)).toBeVisible();
    await expect(nodeCard.getByText(/Проверка подключения:/i)).toBeVisible();
    await expect(nodeCard.getByText(/Шаг проверки:/i)).toBeVisible();
    await expect(nodeCard.getByText(/Итог проверки:/i)).toBeVisible();
    await expect(nodeCard.getByText(/Путь Telegram App:/i)).toBeVisible();
    await expect(nodeCard.getByText(/Путь Telegram Web:/i)).toBeVisible();
    await expect(nodeCard.getByText(/TLS:/i)).toBeVisible();
    await expect(nodeCard.getByText(/REALITY:/i)).toBeVisible();
    await expect(nodeCard.getByText(/legacy_reality_fallback/i)).toBeVisible();
    await expect(nodeCard.getByText(/grpc_443_primary/i)).toBeVisible();
    await expect(nodeCard.getByText(/certificate names do not match expected reality target/i)).toBeVisible();
  });

  test("keeps rollout targeting fields and feed objects intact across save and reload", async ({ page }) => {
    await registerApiMocks(page, {
      isAdmin: true,
      networkRolloutConfig: mockNetworkRolloutConfig(),
    });

    await openRoute(page, "admin/network/");

    const textarea = page.locator("textarea");
    const feedsCard = page.locator("article").filter({ has: page.locator("h3", { hasText: "Списки и источники" }) });
    const targetingCard = page.locator("article").filter({ has: page.locator("h3", { hasText: "Правила для групп" }) });
    await expect(textarea).toHaveValue(/"version": "2026-04-13-rollout"/);
    await expect(textarea).toHaveValue(/"install_ids": \[/);
    await expect(textarea).toHaveValue(/"linked_tg_ids": \[/);
    await expect(textarea).toHaveValue(/"platforms": \[/);
    await expect(feedsCard.getByText("package-feed-v2", { exact: true })).toBeVisible();
    await expect(feedsCard.getByText("rules-feed-v7", { exact: true })).toBeVisible();
    await expect(targetingCard.getByText("install-default-android")).toBeVisible();
    await expect(targetingCard.getByText("1001")).toBeVisible();
    await expect(targetingCard.getByText(/платформы:/i).last()).toContainText("android");

    const initialJson = await textarea.inputValue();
    const nextJson = initialJson
      .replace('"transport_profile": "legacy_reality_fallback"', '"transport_profile": "grpc_443_primary"')
      .replace('"version": "package-feed-v2"', '"version": "package-feed-v3"');
    await textarea.fill(nextJson);
    await page.getByRole("button", { name: /Сохранить/i }).click();
    await expect(page.getByText(/Настройки сети сохранены/i)).toBeVisible();

    await page.reload({ waitUntil: "domcontentloaded" });
    await expect(textarea).toHaveValue(/"version": "2026-04-13-rollout"/);
    await expect(textarea).toHaveValue(/"transport_profile": "grpc_443_primary"/);
    await expect(textarea).toHaveValue(/"install_ids": \[/);
    await expect(textarea).toHaveValue(/"linked_tg_ids": \[/);
    await expect(textarea).toHaveValue(/"platforms": \[/);
    await expect(textarea).toHaveValue(/"version": "package-feed-v3"/);
    await expect(targetingCard.getByText("install-default-windows")).toBeVisible();
    await expect(feedsCard.getByText("rules-feed-v7", { exact: true })).toBeVisible();
  });

  test("lets admin triage a ticket and send a reply using stable status codes", async ({ page }) => {
    await registerApiMocks(page, {
      isAdmin: true,
      tickets: [
        makeTicket({
          id: 7,
          status: "open",
          status_title: "Открыт",
          subject: "Не открывается конфиг",
          last_message_preview: "Конфиг не импортируется на Android.",
          messages: [
            makeTicketMessage({
              id: 1,
              sender_role: "user",
              body: "Конфиг не импортируется на Android.",
            }),
          ],
        }),
      ],
    });

    await openRoute(page, "admin/tickets/");
    await expect(page.getByText("Не открывается конфиг")).toBeVisible();
    const statusButton = page.getByRole("button", { name: "В работе", exact: true });
    await statusButton.click();
    await expect(statusButton).toHaveClass(/bg-violet-600/);

    await page.getByPlaceholder("Напишите ответ пользователю простыми словами").fill("Проверили, сейчас пришлю новый конфиг.");
    await page.getByRole("button", { name: "Отправить" }).click();

    await expect(page.locator(".chat-bubble-admin").getByText("Проверили, сейчас пришлю новый конфиг.")).toBeVisible();
    await expect(statusButton).toBeVisible();
  });

  test("shows payment ledger and requires an audit note for manual reconciliation", async ({ page }) => {
    await registerApiMocks(page, {
      isAdmin: true,
      adminSummary: {
        ...mockAdminSummary(),
        errors: {
          ...mockAdminSummary().errors,
          payment_callback_failures_24h: 2,
        },
      },
      paymentOrders: [
        makePaymentOrder({
          order_id: "order-review-2403",
          status: "manual_review",
          last_event: {
            event_type: "result",
            external_id: "tx-review-2403",
            signature_ok: true,
            processed_ok: false,
            created_at: "2030-01-01T00:03:00",
          },
        }),
      ],
    });

    await openRoute(page, "admin/payments/");
    await expect(page.getByRole("heading", { name: "Платёжный журнал" }).first()).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Admin sections" }).getByRole("link", { name: /Платёжный журнал/ })).toContainText("2");
    await page.getByLabel("Статус платежа").selectOption("pending");
    await expect(page).toHaveURL(/status=pending/);
    await page.getByLabel("Платёжная система").selectOption("freekassa");
    await expect(page).toHaveURL(/provider=freekassa/);
    await page.getByPlaceholder("заказ, способ оплаты, план, кампания, Telegram ID").fill("order-review-2403");
    await expect(page).toHaveURL(/q=order-review-2403/);

    const reviewOrderRow = page.getByRole("row").filter({ hasText: "order-review-2403" });
    await expect(reviewOrderRow).toBeVisible();
    await expect(reviewOrderRow.getByText("manual_review")).toBeVisible();
    await expect(reviewOrderRow.getByText("tx-review-2403")).toBeVisible();
    await expect(page.getByText(/raw-provider-token/i)).not.toBeVisible();

    await page.getByRole("button", { name: "Сверка" }).first().click();
    await page.getByRole("button", { name: "Сохранить сверку" }).click();
    await expect(page.getByText("Для ручной сверки нужна заметка аудита.")).toBeVisible();

    await page
      .getByPlaceholder(/что видно на стороне оплаты/i)
      .fill("Кабинет провайдера подтверждает оплату; автоматическую выдачу доступа не меняем.");
    await page.getByRole("button", { name: "Сохранить сверку" }).click();
    await expect(page.getByText("Сверка сохранена. Доступ пользователя автоматически не менялся.")).toBeVisible();
  });
});
