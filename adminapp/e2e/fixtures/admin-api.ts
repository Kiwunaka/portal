import type { Page, Route } from "@playwright/test";

export type AdminApiCall = {
  method: string;
  path: string;
  headers?: Record<string, string>;
  body?: unknown;
};

export type AdminSearchResult = {
  kind: "user" | "order" | "node" | "key";
  id: string;
  title: string;
  subtitle: string;
  href: string;
};

const generatedAt = "2026-07-15T10:00:00Z";

export type RuScenario =
  | "fresh-pass"
  | "google-down"
  | "stale"
  | "missing"
  | "superseded-manifest"
  | "incomplete-latest-with-last-good"
  | "uploader-backlog"
  | "uploader-heartbeat-stale"
  | "uploader-fresh-failure"
  | "selected-missing"
  | "review-findings";

const nodeRows = [
  {
    code: "nl",
    name: "Нидерланды",
    country_code: "NL",
    enabled: true,
    accepting_new_clients: true,
    is_draining: false,
    mapped_users: 31,
    is_healthy: true,
    health_score: 97,
    capacity_state: "ok",
    capacity_reject_reason: null,
    cpu_percent: 28.5,
    network_utilization_percent: 41.2,
    provisioned_clients_count: 46,
    online_connections_hint: 19,
    freshness_status: "fresh",
    freshness_age_seconds: 420,
    last_health_at: "2026-07-15T09:53:00Z",
    hoster_family: "timeweb",
    hoster_asn: "AS209024",
    subnet: "198.51.100.0/24",
    alert_kinds: ["latency_high"],
    transport_profiles: {
      legacy_reality_fallback: { name: "legacy_reality_fallback", kind: "xray", enabled: true, port: 443 }
    }
  },
  {
    code: "de",
    name: "Германия",
    country_code: "DE",
    enabled: false,
    accepting_new_clients: false,
    is_draining: false,
    mapped_users: 0,
    is_healthy: true,
    health_score: 0,
    capacity_state: "unknown",
    capacity_reject_reason: null,
    cpu_percent: 0,
    network_utilization_percent: 0,
    provisioned_clients_count: 0,
    online_connections_hint: 0,
    freshness_status: "missing",
    freshness_age_seconds: null,
    last_health_at: null,
    hoster_family: null,
    hoster_asn: null,
    subnet: null,
    alert_kinds: [],
    transport_profiles: {}
  },
  {
    code: "brain",
    name: "Brain",
    country_code: "DE",
    enabled: true,
    accepting_new_clients: true,
    is_draining: false,
    mapped_users: 0,
    is_healthy: null,
    health_score: 0,
    capacity_state: "warm",
    capacity_reject_reason: null,
    cpu_percent: 0,
    network_utilization_percent: 0,
    provisioned_clients_count: 0,
    online_connections_hint: 0,
    freshness_status: "missing",
    freshness_age_seconds: null,
    last_health_at: null,
    hoster_family: "brain-host",
    hoster_asn: "AS64500",
    subnet: null,
    alert_kinds: [],
    transport_profiles: {}
  },
  {
    code: "probe-only",
    name: "Только dataplane",
    country_code: "DE",
    enabled: true,
    accepting_new_clients: true,
    is_draining: false,
    mapped_users: 0,
    is_healthy: true,
    health_score: 0,
    capacity_state: "healthy",
    capacity_reject_reason: null,
    cpu_percent: 0,
    network_utilization_percent: 0,
    provisioned_clients_count: 0,
    online_connections_hint: 0,
    freshness_status: "fresh",
    freshness_age_seconds: 30,
    last_health_at: null,
    hoster_family: "probe-host",
    hoster_asn: "AS64501",
    subnet: null,
    alert_kinds: [],
    transport_profiles: {}
  },
  {
    code: "capacity-unknown",
    name: "Неизвестная ёмкость",
    country_code: "DE",
    enabled: true,
    accepting_new_clients: true,
    is_draining: false,
    mapped_users: 0,
    is_healthy: true,
    health_score: 100,
    capacity_state: "unknown",
    capacity_reject_reason: null,
    cpu_percent: 12,
    network_utilization_percent: 5,
    provisioned_clients_count: 3,
    online_connections_hint: 1,
    freshness_status: "fresh",
    freshness_age_seconds: 30,
    last_health_at: "2026-07-15T09:59:30Z",
    hoster_family: "capacity-host",
    hoster_asn: "AS64502",
    subnet: null,
    alert_kinds: [],
    transport_profiles: {}
  }
];

const baselineStages = {
  dns: { status: "pass", latency_ms: 18 },
  tcp: { status: "fail", latency_ms: 41 },
  tls: { status: "not_run", latency_ms: null },
  http_large_body: { status: "not_applicable", latency_ms: null },
  transport_handshake: { status: "pass", latency_ms: 72 }
};

function runSummary(overrides: Record<string, unknown> = {}) {
  return {
    run_db_id: 401,
    run_id: "00000000-0000-4000-8000-000000000401",
    origin: "ru",
    probe_host_id: "mini",
    probe_host_label: "mini",
    runner_version: "2.1.0",
    started_at: "2026-07-15T09:48:00Z",
    finished_at: "2026-07-15T09:50:00Z",
    received_at: "2026-07-15T09:51:00Z",
    manifest_revision: "manifest-current-401",
    execution_status: "completed",
    evidence_code: null,
    environment_verdict: "available",
    release_verdict: "pass",
    current_eligible: true,
    ineligible_reason: null,
    google_reachable: true,
    xhttp_alive: true,
    hysteria_alive: null,
    server_reason: null,
    server_summary: null,
    ...overrides
  };
}

function ruNode(status: string, reasonCode: string, sampledAt: string | null = "2026-07-15T09:50:00Z", nodeCode = "nl") {
  return {
    node_code: nodeCode,
    status,
    sampled_at: sampledAt,
    age_seconds: sampledAt ? (status === "stale" ? 28860 : 600) : null,
    threshold_seconds: 25200,
    reason_code: reasonCode,
    run_id: sampledAt ? "00000000-0000-4000-8000-000000000401" : null,
    target: sampledAt
      ? {
          target_id: `node:${nodeCode}`,
          target_kind: "delivery_node",
          scope: "release_required",
          node_code: nodeCode,
          observed_at: sampledAt,
          overall_status: status === "ok" ? "pass" : status === "unavailable" ? "unavailable_probe_host" : "incomplete",
          current_eligible: status === "ok" || status === "stale",
          ineligible_reason: status === "ok" || status === "stale" ? null : reasonCode,
          reason_code: reasonCode,
          stages: baselineStages,
          address_family_status: { ipv4: "pass", ipv6: "not_run" },
          transport: {
            profile: "legacy_reality_fallback",
            probe_mode: "delivery_tls",
            handshake_status: "pass",
            classification: "ok"
          }
        }
      : null
  };
}

function ruLatestPayload(scenario: RuScenario) {
  let status = "ok";
  let sampledAt: string | null = "2026-07-15T09:50:00Z";
  let ageSeconds: number | null = 600;
  let reasonCode = "current_ru_run";
  let environmentVerdict = "available";
  let environmentStatus = "ok";
  let latestReceived: Record<string, unknown> | null = runSummary();
  let latestEligible: Record<string, unknown> | null = runSummary();
  let node = ruNode("ok", "target_pass");

  if (scenario === "google-down") {
    status = "unavailable";
    reasonCode = "google_unavailable";
    environmentVerdict = "unavailable";
    environmentStatus = "unavailable";
    latestReceived = runSummary({ environment_verdict: "unavailable", release_verdict: "incomplete", google_reachable: false, server_reason: "google_unavailable" });
    latestEligible = latestReceived;
    node = ruNode("unavailable", "google_unavailable");
  } else if (scenario === "stale") {
    status = "stale";
    sampledAt = "2026-07-15T02:00:00Z";
    ageSeconds = 28860;
    reasonCode = "eligible_run_stale";
    latestReceived = runSummary({ finished_at: sampledAt, received_at: "2026-07-15T02:01:00Z" });
    latestEligible = latestReceived;
    node = ruNode("stale", "eligible_run_stale", sampledAt);
  } else if (scenario === "missing") {
    status = "missing";
    sampledAt = null;
    ageSeconds = null;
    reasonCode = "eligible_run_missing";
    environmentVerdict = "unknown";
    environmentStatus = "missing";
    latestReceived = null;
    latestEligible = null;
    node = ruNode("missing", "eligible_run_missing", null);
  } else if (scenario === "superseded-manifest") {
    status = "degraded";
    reasonCode = "superseded_manifest";
    environmentVerdict = "unknown";
    environmentStatus = "degraded";
    latestReceived = runSummary({
      run_db_id: 402,
      run_id: "00000000-0000-4000-8000-000000000402",
      manifest_revision: "manifest-old-402",
      current_eligible: false,
      ineligible_reason: "superseded_manifest",
      release_verdict: "superseded_manifest"
    });
    latestEligible = null;
    node = ruNode("degraded", "superseded_manifest");
  } else if (scenario === "incomplete-latest-with-last-good") {
    latestReceived = runSummary({
      run_db_id: 403,
      run_id: "00000000-0000-4000-8000-000000000403",
      finished_at: "2026-07-15T09:58:00Z",
      received_at: "2026-07-15T09:59:00Z",
      execution_status: "partial",
      release_verdict: "incomplete",
      current_eligible: false,
      ineligible_reason: "required_target_incomplete",
      server_reason: "required_target_incomplete"
    });
    latestEligible = runSummary({
      run_db_id: 400,
      run_id: "00000000-0000-4000-8000-000000000400",
      finished_at: "2026-07-15T04:00:00Z",
      received_at: "2026-07-15T04:01:00Z"
    });
    sampledAt = "2026-07-15T04:00:00Z";
    ageSeconds = 22200;
    node = ruNode("ok", "target_pass", sampledAt);
  } else if (scenario === "review-findings") {
    status = "failed";
    reasonCode = "required_target_failed";
    latestReceived = runSummary({ release_verdict: "fail", current_eligible: false, ineligible_reason: "required_target_failed" });
    latestEligible = null;
    node = ruNode("failed", "target_failed");
  }

  const fallbackNode = {
    node_code: "de",
    status: "not_in_scope",
    sampled_at: null,
    age_seconds: null,
    threshold_seconds: 25200,
    reason_code: "not_in_scope",
    run_id: null,
    target: null
  };

  return {
    ok: true,
    generated_at: generatedAt,
    status,
    sampled_at: sampledAt,
    age_seconds: ageSeconds,
    threshold_seconds: 25200,
    reason_code: reasonCode,
    environment_verdict: environmentVerdict,
    environment: {
      status: environmentStatus,
      sampled_at: sampledAt,
      age_seconds: ageSeconds,
      threshold_seconds: 25200,
      reason_code: environmentVerdict === "available" ? "google_available" : reasonCode,
      verdict: environmentVerdict
    },
    latest_received_attempt: latestReceived,
    latest_eligible_run: latestEligible,
    eligible_run: latestEligible,
    nodes: scenario === "selected-missing"
      ? [fallbackNode]
      : [
          node,
          fallbackNode,
          ...(scenario === "review-findings"
            ? [
                ruNode("ok", "target_pass", "2026-07-15T09:59:30Z", "probe-only"),
                ruNode("ok", "target_pass", "2026-07-15T09:59:30Z", "capacity-unknown")
              ]
            : [])
        ]
  };
}

function observabilityPayload(scenario: RuScenario) {
  const latest = ruLatestPayload(scenario);
  const ru = scenario === "selected-missing" ? ruNode("ok", "target_pass") : latest.nodes[0];
  const metricAlertKinds = [
    "stale_metrics",
    "cpu_high",
    "memory_high",
    "disk_high",
    "network_high",
    "latency_high",
    "error_rate_high",
    "client_density_high",
    "observer_push_stale"
  ];
  const alerts = scenario === "review-findings"
    ? [
        ...metricAlertKinds.map((kind, index) => ({
          id: 31 + index,
          fingerprint: `node_metrics:nl:${kind}`,
          source: "node_metrics",
          severity: kind === "stale_metrics" || kind === "network_high" || kind === "error_rate_high" ? "critical" : "warning",
          status: "active",
          title: `Node nl metric alert: ${kind}`,
          first_seen_at: "2026-07-15T08:00:00Z",
          last_seen_at: "2026-07-15T09:55:00Z",
          resolved_at: null,
          acknowledged_at: null,
          silence_until: null
        })),
        {
          id: 50,
          fingerprint: "node_capacity:nl",
          source: "node_capacity",
          severity: "critical",
          status: "active",
          title: "Node nl capacity: hard_reject",
          first_seen_at: "2026-07-15T08:00:00Z",
          last_seen_at: "2026-07-15T09:55:00Z",
          resolved_at: null,
          acknowledged_at: null,
          silence_until: null
        }
      ]
    : [];
  return {
    ok: true,
    generated_at: generatedAt,
    node: { code: "nl", name: "Нидерланды", hoster_family: "timeweb", hoster_asn: "AS209024", subnet: "198.51.100.0/24", weight: 100 },
    lifecycle: { enabled: true, accepting_new_clients: true, is_draining: false, mapped_users: 31 },
    capacity: { state: scenario === "review-findings" ? "hard_reject" : "healthy", score: 91, reject_reason: null, tx_mbps: 412, tx_ratio: 0.412, capacity_mbps: 1000, provisioned_clients_count: 46, online_connections_hint: 19 },
    sources: {
      brain_metrics: {
        status: "ok",
        sampled_at: "2026-07-15T09:53:00Z",
        age_seconds: 420,
        threshold_seconds: 900,
        reason_code: "brain_metrics_fresh",
        details: { cpu_percent: 28.5, memory_used_mb: 2048, memory_total_mb: 4096, disk_used_gb: 24, disk_total_gb: 80, network_rx_mbps: 91, network_tx_mbps: 321, network_total_mbps: 412, panel_latency_ms: 83, panel_error_rate: scenario === "review-findings" ? 0.31 : 0, probe_stage: "tls", probe_error_kind: null, probe_classification: "ok" }
      },
      runtime: {
        status: "ok",
        sampled_at: "2026-07-15T09:54:00Z",
        age_seconds: 360,
        threshold_seconds: 900,
        reason_code: "runtime_fresh",
        details: { source: "control_panel", provisioned_clients_count: 46, online_connections_hint: 19, network_rx_mbps_1m: 89, network_tx_mbps_1m: 318, network_rx_mbps_5m: 84, network_tx_mbps_5m: 306, capacity_score: 91, capacity_state: "ok", reject_reason: null }
      },
      observer: {
        status: "ok",
        sampled_at: "2026-07-15T09:52:00Z",
        age_seconds: 480,
        threshold_seconds: 900,
        reason_code: "observer_fresh",
        details: { last_batch_id: "batch-safe-401", unmatched_count: 1, parse_error_count: 0 }
      },
      ru_origin: ru
    },
    network: { ipv4_health: "ok", ipv6_health: "unknown", dataplane_ok: true, dataplane_rtt_ms: 42, packet_loss_percent: 0.2, tcp_retrans_percent: 0.1, probe_classification: "ok", last_probe_stage: "tls", last_probe_error_kind: null },
    transports: [{ name: "legacy_reality_fallback", enabled: true, kind: "xray", port: 443, has_inbound: true }],
    ru: { latest: ru, history: { items: [], next_cursor: null, limit: 10 } },
    alerts
  };
}

function historyPayload(scenario: RuScenario, cursor: string | null = null, pageOneRequest = 0) {
  if (scenario === "missing") return { items: [], next_cursor: null, limit: 50 };
  const summary = (runDbId: number, finishedAt: string) => runSummary({
    run_db_id: runDbId,
    run_id: `00000000-0000-4000-8000-${String(runDbId).padStart(12, "0")}`,
    finished_at: finishedAt,
    received_at: new Date(Date.parse(finishedAt) + 60_000).toISOString(),
    release_verdict: "fail",
    current_eligible: false,
    ineligible_reason: "required_target_failed",
    targets: [{ ...ruNode("degraded", "target_failed").target, overall_status: "failed", current_eligible: false, stages: baselineStages }]
  });
  if (scenario === "review-findings") {
    if (cursor === "cursor-safe-next") {
      return {
        items: [summary(390, "2026-07-14T22:00:00Z"), summary(389, "2026-07-14T16:00:00Z")],
        next_cursor: "cursor-abort-next",
        limit: 50
      };
    }
    if (cursor === "cursor-abort-next") {
      return { items: [summary(388, "2026-07-14T10:00:00Z")], next_cursor: null, limit: 50 };
    }
    if (cursor === "cursor-refreshed-next") {
      return {
        items: [summary(390, "2026-07-14T22:00:00Z"), summary(389, "2026-07-14T16:00:00Z")],
        next_cursor: null,
        limit: 50
      };
    }
    return pageOneRequest > 0
      ? { items: [summary(391, "2026-07-15T00:00:00Z")], next_cursor: "cursor-refreshed-next", limit: 50 }
      : { items: [summary(390, "2026-07-14T22:00:00Z")], next_cursor: "cursor-safe-next", limit: 50 };
  }
  return { items: [summary(cursor ? 389 : 390, cursor ? "2026-07-14T16:00:00Z" : "2026-07-14T22:00:00Z")], next_cursor: null, limit: 50 };
}

function uploaderPayload(scenario: RuScenario) {
  const stale = scenario === "uploader-heartbeat-stale";
  const backlog = scenario === "uploader-backlog";
  const freshFailure = scenario === "uploader-fresh-failure";
  return {
    ok: true,
    generated_at: generatedAt,
    status: stale ? "stale" : "ok",
    sampled_at: stale ? "2026-07-15T08:40:00Z" : "2026-07-15T09:55:00Z",
    age_seconds: stale ? 4800 : 300,
    threshold_seconds: 2700,
    reason_code: stale ? "uploader_heartbeat_stale" : "uploader_heartbeat_fresh",
    heartbeat: {
      probe_host_id: "mini",
      observed_at: stale ? "2026-07-15T08:40:00Z" : "2026-07-15T09:55:00Z",
      received_at: stale ? "2026-07-15T08:41:00Z" : "2026-07-15T09:55:10Z",
      service_version: "2.1.0",
      pending_count: backlog || stale ? 4 : 0,
      blocked_count: backlog || stale ? 1 : 0,
      quarantine_count: backlog || stale ? 2 : 0,
      oldest_pending_at: backlog || stale ? "2026-07-15T06:00:00Z" : null,
      archive_write_ok: !stale && !freshFailure,
      disk_free_bytes: stale ? 1024 : freshFailure ? 512_000_000 : 10_000_000_000,
      disk_state: stale ? "critical" : freshFailure ? "warning" : "ok",
      last_error_code: stale || freshFailure ? "archive_write_failed" : null
    }
  };
}

const searchResults: AdminSearchResult[] = [
  {
    kind: "node",
    id: "nl",
    title: "Нода NL",
    subtitle: "Нидерланды · требуется проверка",
    href: "/nodes?selected=nl"
  },
  {
    kind: "user",
    id: "1001",
    title: "Пользователь 1001",
    subtitle: "Активный доступ · профиль проверен",
    href: "/users?selected=1001"
  },
  {
    kind: "user",
    id: "safe-colon-label",
    title: "Безопасная метка ID",
    subtitle: "ID: 1001",
    href: "/users?selected=1001"
  }
];

const unsafeSearchResults: Array<Record<string, unknown>> = [
  {
    kind: "node",
    id: "privacy-01",
    title: "Проверка адреса четыре",
    subtitle: "Источник 192.0.2.44",
    href: "/nodes?selected=privacy-01"
  },
  {
    kind: "node",
    id: "privacy-02",
    title: "Проверка адреса шесть кратко",
    subtitle: "Источник 2001:db8::44",
    href: "/nodes?selected=privacy-02"
  },
  {
    kind: "node",
    id: "privacy-03",
    title: "Проверка адреса шесть полно",
    subtitle: "Источник 2001:0db8:0000:0000:0000:0000:0000:0044",
    href: "/nodes?selected=privacy-03"
  },
  {
    kind: "user",
    id: "privacy-04",
    title: "Проверка веб-ссылки",
    subtitle: "https://example.invalid/profile",
    href: "/users?selected=privacy-04"
  },
  {
    kind: "user",
    id: "privacy-05",
    title: "Проверка сетевого пути",
    subtitle: "//host/path",
    href: "/users?selected=privacy-05"
  },
  {
    kind: "user",
    id: "privacy-06",
    title: "Проверка доменного пути",
    subtitle: "example.invalid/path",
    href: "/users?selected=privacy-06"
  },
  {
    kind: "key",
    id: "privacy-07",
    title: "Проверка схемы",
    subtitle: "vless:",
    href: "/users?selected=privacy-07"
  },
  {
    kind: "key",
    id: "privacy-08",
    title: "Проверка английского слова",
    subtitle: "token",
    href: "/users?selected=privacy-08"
  },
  {
    kind: "key",
    id: "privacy-09",
    title: "Проверка русского слова",
    subtitle: "токен",
    href: "/users?selected=privacy-09"
  },
  {
    kind: "key",
    id: "privacy-10",
    title: "Проверка маркера один",
    subtitle: "subscription",
    href: "/users?selected=privacy-10"
  },
  {
    kind: "key",
    id: "privacy-11",
    title: "Проверка маркера два",
    subtitle: "подписка",
    href: "/users?selected=privacy-11"
  },
  {
    kind: "key",
    id: "privacy-12",
    title: "Проверка маркера три",
    subtitle: "private_key",
    href: "/users?selected=privacy-12"
  },
  {
    kind: "key",
    id: "privacy-13",
    title: "Проверка маркера четыре",
    subtitle: "secret",
    href: "/users?selected=privacy-13"
  },
  {
    kind: "user",
    id: "privacy-14",
    title: "Проверка структуры",
    subtitle: "Публичное описание",
    href: "/users?selected=privacy-14",
    internal_value: "поле вне публичного контракта"
  },
  {
    kind: "user",
    id: "privacy-15",
    title: "Проверка фрагмента",
    subtitle: "Публичное описание",
    href: "/users?selected=privacy-15#details"
  },
  {
    kind: "user",
    id: "privacy-16",
    title: "Проверка внешнего адреса",
    subtitle: "Публичное описание",
    href: "https://outside.invalid/users"
  },
  {
    kind: "user",
    id: "privacy-17",
    title: "Проверка обратной черты",
    subtitle: "Публичное описание",
    href: "/\\outside.invalid/users"
  },
  {
    kind: "user",
    id: "privacy-18",
    title: "Проверка двойного слеша",
    subtitle: "Публичное описание",
    href: "//outside/users"
  },
  {
    kind: "user",
    id: "privacy-19",
    title: "Проверка ключа запроса",
    subtitle: "Публичное описание",
    href: "/users?token_hint=safe"
  },
  {
    kind: "user",
    id: "privacy-20",
    title: "Проверка значения запроса",
    subtitle: "Публичное описание",
    href: "/users?selected=secret"
  },
  {
    kind: "user",
    id: "privacy-21",
    title: "Проверка IDN-домена",
    subtitle: "пример.рф/путь",
    href: "/users?selected=privacy-21"
  }
];

type AdminApiMockOptions = {
  ruScenario?: RuScenario;
  includeUnsafeSearchResults?: boolean;
  overviewStatus?: number;
  ruLatestStatus?: number;
  ruHistoryStatus?: number;
  ruUploaderStatus?: number;
  nodeObservabilityStatus?: number;
  nodeObservabilityDelayMs?: number;
  ruLatestReasonCodes?: string[];
  searchStatus?: number;
  trafficStatus?: number;
  promoRows?: Array<Record<string, unknown>>;
  referralsStatus?: number;
  broadcastStatus?: number;
  failAllLegacyRequests?: boolean;
  delayFirstOverviewFailure?: boolean;
};

const LEGACY_GET_PATHS = new Set([
  "/api/admin/ops/overview",
  "/api/admin/probes/ru-origin/latest",
  "/api/admin/alerts",
  "/api/admin/free-tier/users",
  "/api/admin/traffic/summary",
  "/api/admin/nodes/timeseries",
  "/api/admin/provider-quotas",
  "/api/admin/nodes/health",
  "/api/admin/nodes/runtime",
  "/api/admin/online/users",
  "/api/admin/payments/summary",
  "/api/admin/payments/orders",
  "/api/admin/keys/pressure",
  "/api/admin/tickets",
  "/api/admin/live-updates",
  "/api/admin/funnel/summary",
  "/api/admin/users",
  "/api/admin/promos",
  "/api/admin/referrals/pending"
]);

const FOCUSED_GET_PATHS = new Set([...LEGACY_GET_PATHS, "/api/admin/search"]);

function isNodeObservabilityPath(pathname: string): boolean {
  return /^\/api\/admin\/nodes\/[^/]+\/observability$/.test(pathname);
}

function isNodeActionPath(pathname: string): boolean {
  return /^\/api\/admin\/nodes\/[^/]+\/(drain|undrain|enable|disable|resync)$/.test(pathname);
}

function isFocusedGetPath(pathname: string): boolean {
  return FOCUSED_GET_PATHS.has(pathname)
    || pathname === "/api/admin/probes/ru-origin/runs"
    || pathname === "/api/admin/probes/ru-origin/uploader-status"
    || isNodeObservabilityPath(pathname);
}

function fulfillJson(route: Route, data: unknown, status = 200) {
  const origin = route.request().headers().origin || "http://127.0.0.1:3107";
  return route.fulfill({
    status,
    contentType: "application/json",
    headers: {
      "access-control-allow-origin": origin,
      "access-control-allow-credentials": "true",
      "access-control-allow-methods": "GET,POST,PATCH,DELETE,OPTIONS",
      "access-control-allow-headers": "authorization,content-type,x-telegram-init-data,x-web-auth-token,x-admin-intent-id,x-admin-idempotency-key,x-admin-confirmation-sha256"
    },
    body: JSON.stringify(data)
  });
}

export async function installAdminApiMock(
  page: Page,
  options: AdminApiMockOptions = {}
): Promise<{
  calls: AdminApiCall[];
  overviewResponses: number[];
  releaseFirstOverview: () => void;
  releaseHistoryContinuation: () => void;
}> {
  const calls: AdminApiCall[] = [];
  const overviewResponses: number[] = [];
  let releaseFirstOverview: () => void = () => undefined;
  const firstOverviewGate = new Promise<void>((resolve) => {
    releaseFirstOverview = () => resolve();
  });
  let releaseHistoryContinuation: () => void = () => undefined;
  const historyContinuationGate = new Promise<void>((resolve) => {
    releaseHistoryContinuation = () => resolve();
  });
  let overviewRequestCount = 0;
  let ruLatestRequestCount = 0;
  let historyPageOneRequestCount = 0;
  await page.route("**/api/admin/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();
    const requestHeaders = request.headers();
    let requestBody: unknown = undefined;
    if (method === "POST") {
      try {
        requestBody = request.postDataJSON();
      } catch {
        requestBody = undefined;
      }
    }
    calls.push({
      method,
      path: `${url.pathname}${url.search}`,
      body: requestBody,
      headers: {
        "x-admin-intent-id": requestHeaders["x-admin-intent-id"] || "",
        "x-admin-idempotency-key": requestHeaders["x-admin-idempotency-key"] || "",
        "x-admin-confirmation-sha256": requestHeaders["x-admin-confirmation-sha256"] || "",
      },
    });

    const knownPath = isFocusedGetPath(url.pathname)
      || url.pathname === "/api/admin/auth/session"
      || url.pathname === "/api/admin/broadcast"
      || url.pathname === "/api/admin/action-intents"
      || isNodeActionPath(url.pathname);
    const knownRequest =
      (method === "GET" && isFocusedGetPath(url.pathname)) ||
      (method === "POST" && url.pathname === "/api/admin/auth/session") ||
      (method === "POST" && url.pathname === "/api/admin/broadcast") ||
      (method === "POST" && url.pathname === "/api/admin/action-intents") ||
      (method === "POST" && isNodeActionPath(url.pathname)) ||
      (method === "OPTIONS" && knownPath);
    if (!knownRequest) {
      await fulfillJson(
        route,
        {
          detail: "Focused fixture contract rejected the request",
          code: "fixture_contract_error",
          method,
          path: url.pathname
        },
        501
      );
      return;
    }

    if (method === "OPTIONS") {
      await fulfillJson(route, {}, 204);
      return;
    }

    if (url.pathname === "/api/admin/auth/session") {
      await fulfillJson(route, {
        ok: true,
        token: "mock-admin-token",
        token_transport: "bearer",
        expires_in: 3600,
        user: { id: 9999, username: "owner", role: "superadmin" }
      });
      return;
    }

    if (url.pathname === "/api/admin/broadcast") {
      const status = options.broadcastStatus ?? 200;
      if (status !== 200) {
        await fulfillJson(
          route,
          { detail: "Сессия рассылки отклонена", code: "broadcast_session_rejected", correlation_id: "broadcast-test-id" },
          status
        );
        return;
      }
      await fulfillJson(route, { ok: true, attempted: 0, sent: 0, failed: 0 });
      return;
    }

    if (url.pathname === "/api/admin/action-intents") {
      const body = requestBody && typeof requestBody === "object" && !Array.isArray(requestBody)
        ? requestBody as Record<string, unknown>
        : {};
      const action = String(body.action || "node.disable");
      const target = body.target && typeof body.target === "object" && !Array.isArray(body.target)
        ? body.target as Record<string, unknown>
        : {};
      const nodeCode = String(target.id || "nl").trim().toLowerCase();
      const lifecycle = { enabled: true, accepting_new_clients: true, is_draining: false };
      const afterByAction: Record<string, Record<string, unknown>> = {
        "node.drain": { ...lifecycle, enabled: true, accepting_new_clients: false, is_draining: true },
        "node.undrain": { ...lifecycle },
        "node.enable": { ...lifecycle },
        "node.disable": { ...lifecycle, enabled: false, accepting_new_clients: false, is_draining: false },
        "node.resync": { code: nodeCode.toUpperCase(), planned_moves: 31, without_target: 0, dry_run: false },
      };
      const challenge = action === "node.disable" ? nodeCode.toUpperCase() : "ПОДТВЕРДИТЬ";
      await fulfillJson(route, {
        ok: true,
        intent_id: "00000000-0000-4000-8000-000000000713",
        action,
        target: { type: "node", id: nodeCode },
        risk_level: action === "node.disable" ? "L3" : "L2",
        preview: {
          title: action === "node.disable" ? `Отключение ноды ${nodeCode.toUpperCase()}` : `Команда для ноды ${nodeCode.toUpperCase()}`,
          summary: action === "node.disable" ? `Будет отключена нода ${nodeCode.toUpperCase()}` : `Будет изменена нода ${nodeCode.toUpperCase()}`,
          before: { code: nodeCode.toUpperCase(), ...lifecycle, mapped_users: 31 },
          after: { code: nodeCode.toUpperCase(), ...afterByAction[action], mapped_users: 31 },
          warnings: action === "node.disable" ? ["Принудительное отключение может оборвать активные подключения."] : [],
        },
        payload_hash: "1".repeat(64),
        snapshot_hash: "2".repeat(64),
        entity_version_hash: "3".repeat(64),
        confirmation_challenge: challenge,
        confirmation_challenge_kind: action === "node.disable" ? "exact_node_code" : "exact_phrase",
        expires_at: "2099-07-15T10:10:00Z",
      });
      return;
    }

    if (isNodeActionPath(url.pathname)) {
      if (!requestHeaders["x-admin-intent-id"] || !requestHeaders["x-admin-idempotency-key"] || !requestHeaders["x-admin-confirmation-sha256"]) {
        await fulfillJson(route, { detail: { code: "intent_required", message: "Нужно защищённое намерение" } }, 428);
        return;
      }
      await fulfillJson(route, {
        ok: true,
        status: "completed",
        action_intent_id: requestHeaders["x-admin-intent-id"],
        audit_id: 713,
        node: { code: "NL", enabled: false, accepting_new_clients: false, is_draining: false },
      });
      return;
    }

    if (options.failAllLegacyRequests && method === "GET" && LEGACY_GET_PATHS.has(url.pathname)) {
      await fulfillJson(route, { detail: "Legacy request failed", code: "legacy_test_failure" }, 500);
      if (url.pathname === "/api/admin/ops/overview") overviewResponses.push(500);
      return;
    }

    if (url.pathname === "/api/admin/ops/overview") {
      const requestNumber = overviewRequestCount;
      overviewRequestCount += 1;
      const delayedFailure = options.delayFirstOverviewFailure && requestNumber === 0;
      if (delayedFailure) await firstOverviewGate;
      const overviewStatus = delayedFailure ? 500 : options.overviewStatus;
      if (overviewStatus && overviewStatus !== 200) {
        await fulfillJson(
          route,
          {
            detail: "Сессия отклонена",
            code: "admin_session_rejected",
            correlation_id: "test-correlation-id"
          },
          overviewStatus
        );
        overviewResponses.push(overviewStatus);
        return;
      }
      await fulfillJson(route, {
        ok: true,
        generated_at: generatedAt,
        summary: {
          users: { total: 120, active: 88, free: 32, paid: 56 },
          tickets: { open: 3 },
          nodes: { total: 2, healthy: 2 },
          errors: {},
          observer: { watch_users: 0, suspicious_users: 0 }
        },
        metrics: { status: "fresh", age_seconds: 42, alerts: {}, nodes: [] },
        capacity: { nodes: [] },
        free_tier: {
          free_users: 32,
          sampled_users: 28,
          limit_gb_per_user: 5,
          cycle_days: 30,
          used_gb: 91.5,
          limit_gb_total: 160,
          remaining_gb: 68.5,
          used_pct: 57.2,
          near_cap_users: 0,
          over_cap_users: 0,
          burn_rate_gb_per_day: 3.1,
          source: "mock"
        },
        provider_quotas: [],
        alerts: { active: [], active_count: 0, critical_count: 0, warning_count: 0 }
      });
      overviewResponses.push(200);
      return;
    }

    if (url.pathname === "/api/admin/probes/ru-origin/latest") {
      if (options.ruLatestStatus && options.ruLatestStatus !== 200) {
        await fulfillJson(
          route,
          {
            detail: "RU-origin временно недоступен",
            code: "ru_origin_unavailable",
            correlation_id: "ru-origin-test-id"
          },
          options.ruLatestStatus
        );
        return;
      }
      if (options.ruScenario) {
        await fulfillJson(route, ruLatestPayload(options.ruScenario));
        return;
      }
      const configuredReasons = options.ruLatestReasonCodes || [];
      const reasonCode = configuredReasons.length
        ? configuredReasons[Math.min(ruLatestRequestCount, configuredReasons.length - 1)]
        : "current_ru_run";
      ruLatestRequestCount += 1;
      const releaseVerdict = reasonCode === "required_target_failed"
        ? "fail"
        : reasonCode === "required_target_incomplete"
          ? "incomplete"
          : "pass";
      await fulfillJson(route, {
        ok: true,
        generated_at: generatedAt,
        status: releaseVerdict === "fail" ? "failed" : releaseVerdict === "incomplete" ? "degraded" : "ok",
        sampled_at: "2026-07-15T09:50:00Z",
        age_seconds: 600,
        threshold_seconds: 25200,
        reason_code: reasonCode,
        environment_verdict: "available",
        environment: {
          status: "ok",
          sampled_at: "2026-07-15T09:50:00Z",
          age_seconds: 600,
          threshold_seconds: 25200,
          reason_code: "google_available"
        },
        latest_received_attempt: {
          run_id: "00000000-0000-4000-8000-000000000401",
          finished_at: "2026-07-15T09:50:00Z",
          release_verdict: releaseVerdict
        },
        latest_eligible_run: {
          run_id: "00000000-0000-4000-8000-000000000401",
          finished_at: "2026-07-15T09:50:00Z",
          release_verdict: releaseVerdict
        },
        nodes: [
          {
            node_code: "nl",
            status: "ok",
            sampled_at: "2026-07-15T09:50:00Z",
            age_seconds: 600,
            threshold_seconds: 25200,
            reason_code: "target_pass"
          }
        ]
      });
      return;
    }

    if (url.pathname === "/api/admin/probes/ru-origin/runs") {
      if (options.ruHistoryStatus && options.ruHistoryStatus !== 200) {
        await fulfillJson(route, { detail: "История RU-origin временно недоступна", code: "ru_history_unavailable" }, options.ruHistoryStatus);
        return;
      }
      const cursor = url.searchParams.get("cursor");
      const payload = historyPayload(options.ruScenario || "fresh-pass", cursor, historyPageOneRequestCount);
      if (!cursor) historyPageOneRequestCount += 1;
      if (options.ruScenario === "review-findings" && cursor === "cursor-abort-next") {
        await historyContinuationGate;
        await fulfillJson(route, payload).catch(() => undefined);
        return;
      }
      await fulfillJson(route, payload);
      return;
    }

    if (url.pathname === "/api/admin/probes/ru-origin/uploader-status") {
      if (options.ruUploaderStatus && options.ruUploaderStatus !== 200) {
        await fulfillJson(route, { detail: "Статус загрузчика временно недоступен", code: "ru_uploader_unavailable" }, options.ruUploaderStatus);
        return;
      }
      await fulfillJson(route, uploaderPayload(options.ruScenario || "fresh-pass"));
      return;
    }

    if (isNodeObservabilityPath(url.pathname)) {
      const code = decodeURIComponent(url.pathname.split("/").at(-2) || "").toLowerCase();
      if (options.nodeObservabilityDelayMs) {
        await new Promise((resolve) => setTimeout(resolve, options.nodeObservabilityDelayMs));
      }
      if (options.nodeObservabilityStatus && options.nodeObservabilityStatus !== 200) {
        await fulfillJson(route, { detail: options.nodeObservabilityStatus === 404 ? "Node not found" : "Node unavailable" }, options.nodeObservabilityStatus);
        return;
      }
      if (code !== "nl") {
        await fulfillJson(route, { detail: "Node not found" }, 404);
        return;
      }
      await fulfillJson(route, observabilityPayload(options.ruScenario || "fresh-pass"));
      return;
    }

    if (url.pathname === "/api/admin/payments/summary") {
      await fulfillJson(route, {
        ok: true,
        period: { key: url.searchParams.get("period") || "7d", from: generatedAt, to: generatedAt },
        revenue: { currency: "RUB", paid_count: 0, amount: 0, by_currency: [] },
        status_counts: { paid: 0, pending: 0, manual_review: 0, failed: 0 },
        attention: { pending_count: 0, manual_review_count: 0, failed_count: 0, problem_count: 0 },
        abandoned: {
          buy_clicks: 0,
          checkout_started: 0,
          paid: 0,
          buy_click_not_paid: 0,
          checkout_not_paid: 0
        },
        problem_orders: []
      });
      return;
    }

    if (url.pathname === "/api/admin/traffic/summary") {
      if (options.trafficStatus && options.trafficStatus !== 200) {
        await fulfillJson(
          route,
          { detail: "Доступ к сводке отклонён", code: "traffic_access_rejected", correlation_id: "traffic-test-id" },
          options.trafficStatus
        );
        return;
      }
      await fulfillJson(route, { rows: [] });
      return;
    }

    if (url.pathname === "/api/admin/search") {
      if (options.searchStatus === 404) {
        await fulfillJson(route, { detail: "Сервис временно выключен" }, 404);
        return;
      }
      await fulfillJson(
        route,
        { results: options.includeUnsafeSearchResults ? [...searchResults, ...unsafeSearchResults] : searchResults },
        options.searchStatus ?? 200
      );
      return;
    }

    if (url.pathname === "/api/admin/referrals/pending" && options.referralsStatus && options.referralsStatus !== 200) {
      await fulfillJson(
        route,
        { detail: "Источник рефералов временно недоступен", code: "referrals_unavailable" },
        options.referralsStatus
      );
      return;
    }

    const minimalPayloads: Record<string, unknown> = {
      "/api/admin/alerts": { alerts: [] },
      "/api/admin/free-tier/users": { users: [] },
      "/api/admin/nodes/timeseries": { rows: [] },
      "/api/admin/provider-quotas": { quotas: [] },
      "/api/admin/nodes/health": { nodes: options.ruScenario ? nodeRows : [] },
      "/api/admin/nodes/runtime": { ok: true, nodes: [] },
      "/api/admin/online/users": { ok: true, generated_at: generatedAt, rows: [] },
      "/api/admin/payments/orders": { orders: [] },
      "/api/admin/keys/pressure": { rows: [] },
      "/api/admin/tickets": { tickets: [] },
      "/api/admin/live-updates": { updates: [] },
      "/api/admin/funnel/summary": { stages: [], sources: [] },
      "/api/admin/users": { page: 1, page_size: 80, total: 0, sort: "created_desc", users: [] },
      "/api/admin/promos": { promos: options.promoRows ?? [] },
      "/api/admin/referrals/pending": { rows: [] }
    };
    const payload = minimalPayloads[url.pathname];
    if (payload !== undefined) {
      await fulfillJson(route, payload);
      return;
    }

    await fulfillJson(
      route,
      { detail: "Focused fixture response missing", code: "fixture_contract_error", method, path: url.pathname },
      501
    );
  });

  return { calls, overviewResponses, releaseFirstOverview, releaseHistoryContinuation };
}
