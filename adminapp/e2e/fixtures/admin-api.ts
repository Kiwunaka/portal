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
  requireInitDataForSession?: boolean;
  ruScenario?: RuScenario;
  includeUnsafeSearchResults?: boolean;
  overviewStatus?: number;
  overviewAlerts?: Array<Record<string, unknown>>;
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
  broadcastOutcome?: "completed" | "failed" | "uncertain";
  broadcastStatusOutcome?: "completed" | "failed" | "uncertain" | "prepared";
  actionIntentPrepareStatus?: number;
  failAllLegacyRequests?: boolean;
  delayFirstOverviewFailure?: boolean;
  ticketReplyOutcomes?: Array<"completed" | "failed" | "uncertain">;
  networkScenario?: "populated";
  networkDelayMs?: number;
  revenueScenario?: "populated";
  paymentOrdersStatus?: number;
  funnelStatus?: number;
  promosStatus?: number;
};

const releaseCandidates = [
  {
    candidate_id: "a".repeat(64),
    component: "adminapp",
    version: "2026.07.17.1",
    revision: "1".repeat(40),
    artifact_sha256: "2".repeat(64),
    descriptor_sha256: "a".repeat(64),
    imported_at: "2026-07-15T09:58:00Z",
    age_seconds: 120,
  },
  {
    candidate_id: "b".repeat(64),
    component: "portal_bot",
    version: "2026.07.17.2",
    revision: "3".repeat(40),
    artifact_sha256: "4".repeat(64),
    descriptor_sha256: "b".repeat(64),
    imported_at: "2026-07-15T09:50:00Z",
    age_seconds: 600,
  },
];

function releaseCheck(origin: "current" | "brain" | "ru", status: string, marker: string) {
  return {
    origin,
    check_name: `${origin}_origin_reachability`,
    required: true,
    status,
    observed_at: status === "MISSING" ? null : "2026-07-15T09:55:00Z",
    evidence_ref: status === "MISSING" ? null : marker.repeat(64),
    evidence_sha256: status === "MISSING" ? null : marker.repeat(64),
    ru_probe_run_id: origin === "ru" && status !== "MISSING" ? "00000000-0000-4000-8000-000000000719" : null,
    detail: {},
    reason: status === "MISSING" ? "missing_required_evidence" : `reported_${status.toLowerCase()}`,
  };
}

function releaseReadiness(candidateId: string) {
  const candidate = releaseCandidates.find((item) => item.candidate_id === candidateId) || releaseCandidates[0];
  const allPass = candidate.candidate_id === releaseCandidates[1].candidate_id;
  const origins = allPass
    ? [
      { origin: "current", status: "PASS", checks: [releaseCheck("current", "PASS", "5")], diagnostics: [] },
      { origin: "brain", status: "PASS", checks: [releaseCheck("brain", "PASS", "6")], diagnostics: [] },
      { origin: "ru", status: "PASS", checks: [releaseCheck("ru", "PASS", "7")], diagnostics: [] },
    ]
    : [
      { origin: "current", status: "PASS", checks: [releaseCheck("current", "PASS", "5")], diagnostics: [] },
      { origin: "brain", status: "OPERATOR_ATTESTED", checks: [releaseCheck("brain", "OPERATOR_ATTESTED", "6")], diagnostics: [] },
      { origin: "ru", status: "BLOCKED_BY_ACCESS", checks: [releaseCheck("ru", "BLOCKED_BY_ACCESS", "7")], diagnostics: [releaseCheck("ru", "MISSING", "8")] },
    ];
  return {
    candidate,
    candidate_id: candidate.candidate_id,
    required_check_matrix_version: 1,
    status: allPass ? "PASS" : "BLOCKED_BY_ACCESS",
    ready: allPass,
    generated_at: generatedAt,
    origins,
  };
}

const revenueOrders = [
  { id: 901, order_id: "order-review-901", provider: "freekassa", tg_id: 1001, user: { tg_id: 1001, username: "operator_test", display_name: "Иван Проверочный", status: "active" }, plan_code: "start_99", amount: 99, currency: "RUB", status: "manual_review", source: "checkout", campaign: "summer", promo_code: "WELCOME20", created_at: "2026-07-15T08:30:00Z", paid_at: null, event_count: 2, last_event: { id: 9901, provider: "freekassa", event_type: "result", external_id: "safe-event-9901", order_id: "order-review-901", signature_ok: true, processed_ok: false, created_at: "2026-07-15T08:31:00Z" } },
  { id: 902, order_id: "order-paid-902", provider: "stars", tg_id: 1002, user: null, plan_code: "month", amount: 299, currency: "RUB", status: "paid", source: "bot", campaign: null, promo_code: null, created_at: "2026-07-15T07:00:00Z", paid_at: "2026-07-15T07:02:00Z", event_count: 1, last_event: { id: 9902, provider: "stars", event_type: "success", external_id: "safe-event-9902", order_id: "order-paid-902", signature_ok: true, processed_ok: true, created_at: "2026-07-15T07:02:00Z" } },
];

const revenueFunnel = {
  period: { from: "2026-06-16", to: "2026-07-15" },
  acquisition: {
    cohort: "first_touch_in_period",
    totals: { sessions: 1200, entry_intents: 720, resolved_entries: 540, checkouts: 310, paid: 180, connected: 151 },
    stages: [
      { key: "visit_to_entry", label: "Первый визит → скачивание или бот", entered: 1200, reached_next: 720, dropped: 480, conversion_pct: 60 },
      { key: "entry_to_bound", label: "Скачивание/бот → подтверждённый вход", entered: 720, reached_next: 540, dropped: 180, conversion_pct: 75 },
      { key: "bound_to_checkout", label: "Вход → начало оплаты", entered: 540, reached_next: 310, dropped: 230, conversion_pct: 57.4 },
      { key: "checkout_to_paid", label: "Начали оплату → оплатили", entered: 310, reached_next: 180, dropped: 130, conversion_pct: 58.1 },
      { key: "paid_to_connected", label: "Оплатили → подключились", entered: 180, reached_next: 151, dropped: 29, conversion_pct: 83.9 },
    ],
    drop_reasons: [{ reason: "Не начали оплату", count: 230 }, { reason: "Оплата не подтверждена", count: 130 }],
    by_source: [
      { source: "site", sessions: 800, entry_intents: 440, resolved_entries: 330, checkouts: 190, paid: 108, connected: 91 },
      { source: "bot", sessions: 400, entry_intents: 280, resolved_entries: 210, checkouts: 120, paid: 72, connected: 60 },
    ],
  },
  product: {
    cohort: "known_user_open_in_period",
    totals: { opened: 720, checkouts: 310, paid: 180, connected: 151 },
    stages: [
      { key: "open_to_checkout", label: "Открыли продукт → начали оплату", entered: 720, reached_next: 310, dropped: 410, conversion_pct: 43.1 },
      { key: "checkout_to_paid", label: "Начали оплату → оплатили", entered: 310, reached_next: 180, dropped: 130, conversion_pct: 58.1 },
      { key: "paid_to_connected", label: "Оплатили → подключились", entered: 180, reached_next: 151, dropped: 29, conversion_pct: 83.9 },
    ],
    drop_reasons: [{ reason: "Открыли продукт, но не начали оплату", count: 410 }],
  },
  notes: ["Raw identifiers are not returned."]
};

const revenuePromos = [
  { code: "WELCOME20", promo_type: "discount", value: 20, uses_left: 90, used_count: 10, expires_at: "2026-09-15T00:00:00Z", created_at: "2026-07-01T10:00:00Z" },
  { code: "BONUS7", promo_type: "days", value: 7, uses_left: -1, used_count: 4, expires_at: null, created_at: "2026-07-02T10:00:00Z" },
];

const revenueReferrals = [
  { id: 302, order_id: "ref-order-302", referrer_tg_id: 1102, referred_tg_id: 2102, queued_at: "2026-07-15T07:00:00Z", ready_at: "2026-07-15T09:00:00Z", status: "pending", processed_at: null, basis: "waiting_for_activity", meta_present: true, meta_sha256: "a".repeat(64) },
  { id: 301, order_id: "ref-order-301", referrer_tg_id: 1101, referred_tg_id: 2101, queued_at: "2026-07-15T06:00:00Z", ready_at: "2026-07-15T08:00:00Z", status: "pending", processed_at: null, basis: "reward_ready", meta_present: false, meta_sha256: "b".repeat(64) },
  { id: 299, order_id: "ref-order-299", referrer_tg_id: 1099, referred_tg_id: 2099, queued_at: "2026-07-14T06:00:00Z", ready_at: "2026-07-14T08:00:00Z", status: "rewarded", processed_at: "2026-07-14T09:00:00Z", basis: "rewarded", meta_present: false, meta_sha256: "c".repeat(64) },
];

const networkTrafficRows = [
  { date: "2026-07-13", node_code: "nl", pool_code: "paid_pool", traffic_bytes: 8053063680, traffic_gb: 7.5, samples: 18 },
  { date: "2026-07-14", node_code: "nl", pool_code: "paid_pool", traffic_bytes: null, traffic_gb: null, samples: null },
  { date: "2026-07-15", node_code: "nl", pool_code: "paid_pool", traffic_bytes: 9932111872, traffic_gb: 9.25, samples: 22 },
  { date: "2026-07-13", node_code: "nl-free", pool_code: "free_pool", traffic_bytes: 1610612736, traffic_gb: 1.5, samples: 7 },
  { date: "2026-07-15", node_code: "nl-free", pool_code: "free_pool", traffic_bytes: 2147483648, traffic_gb: 2, samples: 9 },
];

const networkQuotaConfig = {
  id: 71,
  node_code: "nl",
  included_bytes: 107374182400,
  included_gb: 100,
  reset_day: 1,
  timezone: "UTC",
  warning_ratio: 0.8,
  critical_ratio: 0.95,
  enabled: true,
  notes_present: false,
  notes_length: 0,
  notes_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  created_at: "2026-07-01T10:00:00Z",
  updated_at: "2026-07-15T09:55:00Z",
};

const networkQuotaStatuses = [
  { node_code: "nl", node_name: "Нидерланды", configured: true, enabled: true, state: "warning", included_gb: 100, used_gb: 84.25, remaining_gb: 15.75, used_pct: 84.3, warning_ratio: 0.8, critical_ratio: 0.95, cycle_start: "2026-07-01T00:00:00Z", cycle_end: "2026-08-01T00:00:00Z", reset_day: 1, timezone: "UTC", sample_count: 120, source: "node_health_samples_total_counter_delta", updated_at: "2026-07-15T09:55:00Z" },
  { node_code: "de", node_name: "Германия", configured: false, enabled: false, state: "unconfigured", included_gb: null, used_gb: null, remaining_gb: null, used_pct: null, warning_ratio: null, critical_ratio: null, cycle_start: null, cycle_end: null, reset_day: null, timezone: null, sample_count: null, source: "not_configured", updated_at: null },
];

const networkAlerts = [
  { id: 81, fingerprint: "provider_quota:nl", source: "provider_quota", severity: "warning", status: "active", title: "Лимит NL приближается", body: "Использовано 84,3% текущего лимита.", node_code: "nl", tg_id: null, key_id: null, first_seen_at: "2026-07-15T07:00:00Z", last_seen_at: "2026-07-15T09:50:00Z", resolved_at: null, acknowledged_at: null, silence_until: null },
  { id: 82, fingerprint: "free_tier:over_cap", source: "free_tier", severity: "warning", status: "active", title: "Есть пользователи сверх лимита", body: "Проверьте бесплатный контур.", node_code: null, tg_id: null, key_id: null, first_seen_at: "2026-07-15T08:00:00Z", last_seen_at: "2026-07-15T09:45:00Z", resolved_at: null, acknowledged_at: null, silence_until: null },
];

const networkFreeSummary = {
  generated_at: generatedAt,
  free_users: 2,
  sampled_users: 2,
  limit_gb_per_user: 5,
  cycle_days: 30,
  used_gb: 6.7,
  limit_gb_total: 10,
  remaining_gb: 3.3,
  used_pct: 67,
  near_cap_users: 1,
  over_cap_users: 1,
  burn_rate_gb_per_day: 0.478,
  source: "key_usage_rollups",
};

const networkFreeFacts = { node_pool: "NL-free", traffic_limit_gb: 5, cycle_days: 30, speed_limit_mbps: 50, device_limit: 1, monthly_reset: true, source: "shared_product_facts" };
const networkFreeUsers = [
  { tg_id: 2001, username: "free_one", display_name: "Анна Бесплатная", is_active: true, current_plan_code: "free", used_gb: 5.2, limit_gb: 5, remaining_gb: 0, used_pct: 104, state: "over_cap", cycle_start: "2026-07-01T00:00:00Z", cycle_end: "2026-07-31T00:00:00Z", next_reset_at: "2026-07-31T00:00:00Z", source: "key_usage_rollups", rollup_count: 12 },
  { tg_id: 2002, username: "free_two", display_name: "Илья Бесплатный", is_active: true, current_plan_code: "free", used_gb: 1.5, limit_gb: 5, remaining_gb: 3.5, used_pct: 30, state: "ok", cycle_start: "2026-07-01T00:00:00Z", cycle_end: "2026-07-31T00:00:00Z", next_reset_at: "2026-07-31T00:00:00Z", source: "key_usage_rollups", rollup_count: 8 },
];

const clientUserRows = [
  {
    tg_id: 1001,
    username: "operator_test",
    display_name: "Иван Проверочный",
    sub_type: "paid",
    status: "active",
    origin: "app",
    is_manual: false,
    expiry_at: "2026-08-15T10:00:00Z",
    created_at: "2026-06-01T09:00:00Z",
    app_install_id: "install-safe-1001",
    observer_state: "watch",
    observer_updated_at: "2026-07-15T09:55:00Z",
  },
  {
    tg_id: -42,
    username: null,
    display_name: "Ручной тест",
    sub_type: "manual",
    status: "manual_test",
    origin: "manual_test",
    is_manual: true,
    expiry_at: "2026-07-30T10:00:00Z",
    created_at: "2026-07-01T09:00:00Z",
    app_install_id: null,
    observer_state: "ok",
    observer_updated_at: "2026-07-15T09:55:00Z",
  },
];

function clientUserDetail(tgId: number) {
  const listRow = clientUserRows.find((row) => row.tg_id === tgId) || clientUserRows[0];
  return {
    user: {
      ...listRow,
      tg_id: tgId,
      is_active: true,
      effective_active: true,
      stars_paid: tgId > 0 ? 1200 : 0,
      total_gb: 18.5,
      trial_used: true,
      referral_count: 2,
      streak_months: 3,
      linked_telegram_id: null,
      linked_telegram_username: null,
      app_platform: tgId > 0 ? "android" : null,
      app_last_seen_at: "2026-07-15T09:54:00Z",
    },
    summary: {
      nodes_total: null,
      nodes_with_client: null,
      nodes_online: null,
      online_keys_now: null,
      online_connections_now: null,
      active_users_estimate: null,
      online_node_codes_now: null,
      nodes_enabled: null,
      subid_mismatch_count: null,
      traffic_total_gb: null,
      panel_state: "partial",
    },
    keys: [
      {
        node_code: "nl",
        node_name: "Нидерланды",
        exists: true,
        enabled: true,
        online: true,
        current_connections: 2,
        sub_id_match: true,
        total_gb: 18.5,
        last_online_at: "2026-07-15T09:59:00Z",
        last_online_age_seconds: 60,
        panel_state: "ok",
      },
      {
        node_code: "de",
        node_name: "Германия",
        exists: null,
        enabled: null,
        online: null,
        current_connections: null,
        sub_id_match: null,
        total_gb: null,
        last_online_at: null,
        last_online_age_seconds: null,
        panel_state: "error",
      },
    ],
    tickets: [{ id: 501, status: "open", status_title: "Открыт", subject: "Не подключается", updated_at: "2026-07-15T09:45:00Z", last_message_preview: "Нужна помощь" }],
    payment_orders: [{ id: 701, order_id: "ORDER-701", provider: "stars", plan_code: "month", amount: 299, currency: "RUB", status: "paid", created_at: "2026-07-01T10:00:00Z", paid_at: "2026-07-01T10:01:00Z" }],
    key_history: [{ id: 801, action: "admin_user_key_toggle", node_code: "nl", actor_tg_id: 9999, source: "admin", created_at: "2026-07-10T10:00:00Z" }],
    admin_actions: [{ id: 901, action: "admin_manual_extend", node_code: null, actor_tg_id: 9999, source: "admin", created_at: "2026-07-11T10:00:00Z" }],
    observer: {
      state: "watch",
      reasons: ["multi_ip"],
      observed_ip_count_24h: 2,
      observed_ip_count_7d: 3,
      observed_ip_count_30d: 4,
      observed_node_count_24h: 1,
      observed_node_count_7d: 2,
      observed_node_count_30d: 2,
      overlap_count_24h: 0,
      last_observed_at: "2026-07-15T09:58:00Z",
      updated_at: "2026-07-15T09:59:00Z",
      recent_nodes: [{ node_id: 1, node_code: "nl", node_name: "Нидерланды", last_seen_at: "2026-07-15T09:58:00Z", score_ip_count: 2 }],
    },
    risk: {
      score: 35,
      level: "medium",
      window_days: 30,
      updated_at: "2026-07-15T09:59:00Z",
      signals: { regen_count: 0, admin_key_ops: 1, unique_ips: 2, observer_state: "watch", traffic_gb: 18.5, subid_mismatch_count: 0 },
      factors: [{ key: "multi_ip", weight: 35, value: "2" }],
    },
  };
}

const clientInvestigation = {
  tg_id: 1001,
  generated_at: generatedAt,
  observer: {
    ...clientUserDetail(1001).observer,
    recent_ips: [{
      source_ip_raw: "203.0.113.44",
      node_code: "nl",
      node_name: "Нидерланды",
      last_seen_at: "2026-07-15T09:58:00Z",
      counts_for_suspicion: true,
    }],
  },
};

const clientOnlinePayload = {
  ok: true,
  generated_at: generatedAt,
  total: 1,
  limit: 200,
  rows: [{
    row_id: "user:1001",
    tg_id: 1001,
    username: "operator_test",
    display_name: "Иван Проверочный",
    sub_type: "paid",
    status: "active",
    origin: "app",
    nodes_online: ["nl"],
    online_keys_now: 1,
    online_connections_now: 2,
    ip_count: 2,
    risk_flags: ["multi_ip"],
    last_online_at: "2026-07-15T09:59:00Z",
    traffic_gb_24h: 1.5,
    pressure_score: 20,
  }],
  summary: {
    online_identities: 1,
    known_users_online: 1,
    unknown_online_keys: 0,
    online_keys_now: 1,
    online_connections_now: 2,
    nodes_with_panel_errors: 0,
  },
  panel_errors: [],
};

const clientTicketList = {
  id: 501,
  user_tg_id: 1001,
  status: "open",
  status_title: "Открыт",
  subject: "Не подключается",
  priority: "high",
  created_at: "2026-07-15T08:00:00Z",
  updated_at: "2026-07-15T09:45:00Z",
  closed_at: null,
  last_message_preview: "Нужна помощь с подключением",
};

const clientTicketDetail = {
  ...clientTicketList,
  messages: [
    {
      id: 1,
      sender_tg_id: 1001,
      sender_role: "user",
      body: "Нужна помощь с подключением",
      attachment: { type: "file", name: "диагностика.txt", content_type: "text/plain", size_bytes: 512, download_url: "/api/tickets/attachments/20260715-Abcdefgh1234.txt" },
      created_at: "2026-07-15T08:00:00Z",
    },
    { id: 2, sender_tg_id: 9999, sender_role: "admin", body: "Уточните платформу", created_at: "2026-07-15T08:05:00Z" },
  ],
};

const LEGACY_GET_PATHS = new Set([
  "/api/admin/ops/overview",
  "/api/admin/probes/ru-origin/latest",
  "/api/admin/alerts",
  "/api/admin/free-tier/users",
  "/api/admin/traffic/summary",
  "/api/admin/nodes/timeseries",
  "/api/admin/provider-quotas",
  "/api/admin/provider-quotas/status",
  "/api/admin/emergency-network/status",
  "/api/admin/free-tier/summary",
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

function isUserDetailPath(pathname: string): boolean {
  return /^\/api\/admin\/users\/-?[1-9]\d*$/.test(pathname);
}

function isUserInvestigationPath(pathname: string): boolean {
  return /^\/api\/admin\/users\/-?[1-9]\d*\/investigation$/.test(pathname);
}

function isUserActionPath(pathname: string): boolean {
  return /^\/api\/admin\/users\/-?[1-9]\d*\/(manual\/(extend|block|regenerate-token)|presets\/run|safe-delete|message|keys\/[^/]+\/(toggle|reset-traffic|resync-subid)|key-limits\/[^/]+)$/.test(pathname);
}

function isTicketDetailPath(pathname: string): boolean {
  return /^\/api\/admin\/tickets\/[1-9]\d*$/.test(pathname);
}

function isTicketActionPath(pathname: string): boolean {
  return /^\/api\/admin\/tickets\/[1-9]\d*\/(reply|status)$/.test(pathname);
}

function isProviderQuotaMutationPath(pathname: string): boolean {
  return pathname === "/api/admin/provider-quotas" || /^\/api\/admin\/provider-quotas\/[^/]+$/.test(pathname);
}

function isPaymentDetailPath(pathname: string): boolean {
  return /^\/api\/admin\/payments\/orders\/[^/]+\/[^/]+$/.test(pathname);
}

function isRevenueMutationPath(pathname: string): boolean {
  return /^\/api\/admin\/payments\/orders\/[^/]+\/[^/]+\/reconcile$/.test(pathname)
    || pathname === "/api/admin/promos"
    || /^\/api\/admin\/promos\/[^/]+$/.test(pathname)
    || pathname === "/api/admin/referrals/process";
}

function isAlertActionPath(pathname: string): boolean {
  return /^\/api\/admin\/alerts\/[1-9]\d*\/(ack|silence)$/.test(pathname);
}

function isReleaseReadinessPath(pathname: string): boolean {
  return /^\/api\/admin\/releases\/[a-f0-9]{64}\/readiness$/.test(pathname);
}

function isActionIntentStatusPath(pathname: string): boolean {
  return /^\/api\/admin\/action-intents\/[0-9a-f-]{36}$/.test(pathname);
}

function isFocusedGetPath(pathname: string): boolean {
  return FOCUSED_GET_PATHS.has(pathname)
    || pathname === "/api/admin/probes/ru-origin/runs"
    || pathname === "/api/admin/probes/ru-origin/uploader-status"
    || isNodeObservabilityPath(pathname)
    || isUserDetailPath(pathname)
    || isUserInvestigationPath(pathname)
    || isTicketDetailPath(pathname)
    || isPaymentDetailPath(pathname)
    || pathname === "/api/admin/releases/candidates"
    || isReleaseReadinessPath(pathname)
    || isActionIntentStatusPath(pathname);
}

function fulfillJson(route: Route, data: unknown, status = 200) {
  const origin = route.request().headers().origin || "http://127.0.0.1:3107";
  return route.fulfill({
    status,
    contentType: "application/json",
    headers: {
      "access-control-allow-origin": origin,
      "access-control-allow-credentials": "true",
      "access-control-allow-methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
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
  let ticketReplyRequestCount = 0;
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();
    const requestHeaders = request.headers();
    let requestBody: unknown = undefined;
    if (method !== "GET" && method !== "OPTIONS") {
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
        authorization: requestHeaders.authorization || "",
        "x-telegram-init-data": requestHeaders["x-telegram-init-data"] || "",
        "x-admin-intent-id": requestHeaders["x-admin-intent-id"] || "",
        "x-admin-idempotency-key": requestHeaders["x-admin-idempotency-key"] || "",
        "x-admin-confirmation-sha256": requestHeaders["x-admin-confirmation-sha256"] || "",
      },
    });

    if (
      method === "GET"
      && options.networkDelayMs
      && [
        "/api/admin/traffic/summary",
        "/api/admin/alerts",
        "/api/admin/provider-quotas",
        "/api/admin/provider-quotas/status",
        "/api/admin/free-tier/summary",
        "/api/admin/free-tier/users",
      ].includes(url.pathname)
    ) {
      await new Promise((resolve) => setTimeout(resolve, options.networkDelayMs));
    }

    const knownPath = isFocusedGetPath(url.pathname)
      || url.pathname === "/api/admin/auth/session"
      || url.pathname === "/api/admin/broadcast"
      || url.pathname === "/api/admin/action-intents"
      || isNodeActionPath(url.pathname)
      || isUserActionPath(url.pathname)
      || isTicketActionPath(url.pathname)
      || isProviderQuotaMutationPath(url.pathname)
      || isRevenueMutationPath(url.pathname)
      || isAlertActionPath(url.pathname);
    const knownRequest =
      (method === "GET" && isFocusedGetPath(url.pathname)) ||
      (method === "POST" && url.pathname === "/api/admin/auth/session") ||
      (method === "POST" && url.pathname === "/api/admin/broadcast") ||
      (method === "POST" && url.pathname === "/api/admin/action-intents") ||
      (method === "POST" && isNodeActionPath(url.pathname)) ||
      ((method === "POST" || method === "PUT") && isUserActionPath(url.pathname)) ||
      (method === "POST" && isTicketActionPath(url.pathname)) ||
      ((method === "POST" || method === "PATCH" || method === "DELETE") && isProviderQuotaMutationPath(url.pathname)) ||
      ((method === "POST" || method === "PATCH" || method === "DELETE") && isRevenueMutationPath(url.pathname)) ||
      (method === "POST" && isAlertActionPath(url.pathname)) ||
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
      if (options.requireInitDataForSession && !requestHeaders["x-telegram-init-data"]) {
        await fulfillJson(
          route,
          {
            detail: "Нужен Telegram initData",
            code: "admin_init_data_required",
            correlation_id: "session-test-id"
          },
          401
        );
        return;
      }
      await fulfillJson(route, {
        ok: true,
        token: "mock-admin-token",
        token_transport: "bearer",
        expires_in: 3600,
        user: { id: 9999, username: "owner", role: "superadmin" }
      });
      return;
    }

    if (url.pathname === "/api/admin/releases/candidates") {
      await fulfillJson(route, { items: releaseCandidates, next_cursor: null, limit: 50 });
      return;
    }

    if (isReleaseReadinessPath(url.pathname)) {
      const candidateId = url.pathname.split("/").at(-2) || "";
      await fulfillJson(route, releaseReadiness(candidateId));
      return;
    }

    if (isActionIntentStatusPath(url.pathname)) {
      const intentId = url.pathname.split("/").at(-1) || "";
      const outcome = options.broadcastStatusOutcome || options.broadcastOutcome || "uncertain";
      await fulfillJson(route, {
        ok: outcome === "completed",
        status: outcome,
        action_intent_id: intentId,
        audit_id: outcome === "uncertain" ? 719 : 718,
        result_code: outcome === "completed" ? "broadcast_sent" : outcome === "failed" ? "broadcast_partial" : "external_timeout",
        ...(outcome === "completed" ? { result: { attempted: 12, sent: 12, failed: 0 } } : {}),
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
      if (!requestHeaders["x-admin-intent-id"] || !requestHeaders["x-admin-idempotency-key"] || !requestHeaders["x-admin-confirmation-sha256"]) {
        await fulfillJson(route, { detail: { code: "intent_required", message: "Нужно защищённое намерение" } }, 428);
        return;
      }
      const outcome = options.broadcastOutcome || "completed";
      await fulfillJson(route, {
        ok: outcome === "completed",
        status: outcome,
        action_intent_id: requestHeaders["x-admin-intent-id"],
        audit_id: 718,
        result_code: outcome === "completed" ? "broadcast_sent" : outcome === "failed" ? "broadcast_partial" : "external_timeout",
        ...(outcome === "completed" ? { attempted: 12, sent: 12, failed: 0 } : {}),
      });
      return;
    }

    if (url.pathname === "/api/admin/action-intents") {
      const prepareStatus = options.actionIntentPrepareStatus ?? 200;
      if (prepareStatus !== 200) {
        await fulfillJson(
          route,
          { detail: { code: "intent_prepare_rejected", message: "Предпросмотр рассылки отклонён", correlation_id: "broadcast-prepare-test-id" } },
          prepareStatus,
        );
        return;
      }
      const body = requestBody && typeof requestBody === "object" && !Array.isArray(requestBody)
        ? requestBody as Record<string, unknown>
        : {};
      const action = String(body.action || "node.disable");
      const target = body.target && typeof body.target === "object" && !Array.isArray(body.target)
        ? body.target as Record<string, unknown>
        : {};
      const targetType = String(target.type || "node").trim().toLowerCase();
      const targetId = String(target.id || "nl").trim();
      const nodeCode = targetId.toLowerCase();
      const lifecycle = { enabled: true, accepting_new_clients: true, is_draining: false };
      const afterByAction: Record<string, Record<string, unknown>> = {
        "node.drain": { ...lifecycle, enabled: true, accepting_new_clients: false, is_draining: true },
        "node.undrain": { ...lifecycle },
        "node.enable": { ...lifecycle },
        "node.disable": { ...lifecycle, enabled: false, accepting_new_clients: false, is_draining: false },
        "node.resync": { code: nodeCode.toUpperCase(), planned_moves: 31, without_target: 0, dry_run: false },
      };
      const nodeAction = action.startsWith("node.");
      const providerAction = action.startsWith("provider_quota.");
      const paymentAction = action === "payment.reconcile";
      const promoAction = action.startsWith("promo.");
      const referralAction = action === "referral.process";
      const broadcastAction = action === "broadcast.send";
      const revenueAction = paymentAction || promoAction || referralAction;
      const l3Action = broadcastAction || action === "node.disable" || action === "user.block" || action === "user.regenerate_token" || action === "user.migration_code" || action === "user.safe_delete" || action === "provider_quota.delete" || action === "promo.delete";
      const challenge = action === "node.disable"
        ? nodeCode.toUpperCase()
        : action === "provider_quota.delete"
          ? nodeCode.toUpperCase()
        : action === "promo.delete"
          ? targetId.toUpperCase()
        : broadcastAction || action === "ticket.reply" || action === "user.message"
          ? "ОТПРАВИТЬ"
          : l3Action
            ? targetId
            : "ПОДТВЕРДИТЬ";
      const genericBefore = targetType === "ticket" ? { ticket_id: Number(targetId), status: "open" } : { tg_id: Number(targetId), status: "active" };
      const genericAfter = targetType === "ticket" ? { ticket_id: Number(targetId), status: action === "ticket.status" ? String((body.payload as Record<string, unknown> | undefined)?.status || "open") : "open" } : { tg_id: Number(targetId), status: action === "user.block" ? "blocked" : "active" };
      const providerBefore = { node_code: nodeCode.toUpperCase(), configured: true, node_status: "active", included_gb: 100, used_gb: 84.25, reset_day: 1, timezone: "UTC", warning_ratio: 0.8, critical_ratio: 0.95, enabled: true, notes_present: false, projected_exhaustion_at: "2026-07-18T12:00:00Z", updated_at: "2026-07-15T09:55:00Z" };
      const providerAfter = action === "provider_quota.delete" ? { ...providerBefore, configured: false, included_gb: null, reset_day: null, timezone: null, warning_ratio: null, critical_ratio: null, enabled: false, projected_exhaustion_at: null, updated_at: null } : { ...providerBefore, included_gb: Number((body.payload as Record<string, unknown> | undefined)?.included_gb || 100) };
      const revenuePayload = body.payload && typeof body.payload === "object" && !Array.isArray(body.payload) ? body.payload as Record<string, unknown> : {};
      const paymentBefore = { order_id: "order-review-901", provider: "freekassa", status: "manual_review", amount: 99, currency: "RUB", callback_events: 2, callback_state: "requires_review" };
      const paymentAfter = { ...paymentBefore, status: String(revenuePayload.status || "manual_review"), operator_note_length: String(revenuePayload.note || "").length };
      const promoBefore = { promo_code: targetId.toUpperCase(), promo_type: "discount", value: 20, uses_left: 90, used_count: 10, expires_at: "2026-09-15T00:00:00Z", exists: action !== "promo.create" };
      const promoAfter = action === "promo.delete" ? { ...promoBefore, exists: false } : { ...promoBefore, promo_code: String(revenuePayload.new_code || revenuePayload.code || targetId).toUpperCase(), promo_type: String(revenuePayload.promo_type || promoBefore.promo_type), value: Number(revenuePayload.value ?? promoBefore.value), uses_left: Number(revenuePayload.uses_left ?? promoBefore.uses_left), expires_at: revenuePayload.expires_at ?? promoBefore.expires_at, exists: true };
      const referralBefore = { selection_count: 2, queue_id: 301, order_id: "ref-order-301", referrer_tg_id: 1101, referred_tg_id: 2101, decision_basis: "reward_ready" };
      const referralAfter = { ...referralBefore, status: "process" };
      const broadcastPayload = body.payload && typeof body.payload === "object" && !Array.isArray(body.payload) ? body.payload as Record<string, unknown> : {};
      const broadcastBefore = { recipient_count: 12, recipient_hash: "9".repeat(64) };
      const broadcastAfter = { segment: String(broadcastPayload.segment || "all_active"), limit: Number(broadcastPayload.limit || 500), message_sha256: "8".repeat(64), message_length: String(broadcastPayload.text || "").length };
      const revenueBefore = paymentAction ? paymentBefore : promoAction ? promoBefore : referralBefore;
      const revenueAfter = paymentAction ? paymentAfter : promoAction ? promoAfter : referralAfter;
      await fulfillJson(route, {
        ok: true,
        intent_id: "00000000-0000-4000-8000-000000000713",
        action,
        target: { type: targetType, id: nodeAction || providerAction ? nodeCode : targetId },
        risk_level: l3Action ? "L3" : "L2",
        preview: {
          title: broadcastAction ? "Защищённая рассылка" : revenueAction ? paymentAction ? "Сверка платёжного заказа" : promoAction ? "Изменение промокода" : "Обработка реферальной очереди" : providerAction ? `Квота провайдера ${nodeCode.toUpperCase()}` : nodeAction ? action === "node.disable" ? `Отключение ноды ${nodeCode.toUpperCase()}` : `Команда для ноды ${nodeCode.toUpperCase()}` : targetType === "ticket" ? `Действие с тикетом ${targetId}` : `Действие с пользователем ${targetId}`,
          summary: broadcastAction ? "Сервер зафиксировал точных получателей и SHA-256 сообщения." : revenueAction ? paymentAction ? "Сервер зафиксировал provider, order, status и callback version." : promoAction ? "Сервер показал точные before/after и срок промокода." : "Сервер зафиксировал очередь и основание решения." : providerAction ? "Сервер пересчитал конфигурацию и прогноз исчерпания." : nodeAction ? action === "node.disable" ? `Будет отключена нода ${nodeCode.toUpperCase()}` : `Будет изменена нода ${nodeCode.toUpperCase()}` : "Сервер проверил текущее состояние и подготовил изменение.",
          before: broadcastAction ? broadcastBefore : revenueAction ? revenueBefore : providerAction ? providerBefore : nodeAction ? { code: nodeCode.toUpperCase(), ...lifecycle, mapped_users: 31 } : genericBefore,
          after: broadcastAction ? broadcastAfter : revenueAction ? revenueAfter : providerAction ? providerAfter : nodeAction ? { code: nodeCode.toUpperCase(), ...afterByAction[action], mapped_users: 31 } : genericAfter,
          warnings: broadcastAction ? ["Получатели зафиксированы. Автоматического повтора нет."] : revenueAction ? paymentAction ? ["Callback evidence не изменяется."] : referralAction ? ["Новый платёж не создаётся."] : [] : action === "node.disable" ? ["Принудительное отключение может оборвать активные подключения."] : providerAction ? ["Прогноз рассчитан сервером."] : [],
          ...(referralAction ? { selection: { selection_count: 2, selection_hash: "4".repeat(64) } } : {}),
        },
        payload_hash: "1".repeat(64),
        snapshot_hash: "2".repeat(64),
        entity_version_hash: "3".repeat(64),
        confirmation_challenge: challenge,
        confirmation_challenge_kind: broadcastAction ? "exact_phrase" : action === "promo.delete" ? "exact_promo_code" : action === "node.disable" || action === "provider_quota.delete" ? "exact_node_code" : l3Action ? "exact_tg_id" : "exact_phrase",
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

    if (method !== "GET" && isProviderQuotaMutationPath(url.pathname)) {
      if (!requestHeaders["x-admin-intent-id"] || !requestHeaders["x-admin-idempotency-key"] || !requestHeaders["x-admin-confirmation-sha256"]) {
        await fulfillJson(route, { detail: { code: "intent_required", message: "Нужно защищённое намерение" } }, 428);
        return;
      }
      await fulfillJson(route, {
        ok: true,
        status: "completed",
        action_intent_id: requestHeaders["x-admin-intent-id"],
        audit_id: 716,
        quota: networkQuotaConfig,
      });
      return;
    }

    if (method !== "GET" && isRevenueMutationPath(url.pathname)) {
      if (!requestHeaders["x-admin-intent-id"] || !requestHeaders["x-admin-idempotency-key"] || !requestHeaders["x-admin-confirmation-sha256"]) {
        await fulfillJson(route, { detail: { code: "intent_required", message: "Нужно защищённое намерение" } }, 428);
        return;
      }
      await fulfillJson(route, {
        ok: true,
        status: "completed",
        action_intent_id: requestHeaders["x-admin-intent-id"],
        audit_id: 717,
        processed: url.pathname === "/api/admin/referrals/process" ? 2 : undefined,
        rewarded: url.pathname === "/api/admin/referrals/process" ? 1 : undefined,
      });
      return;
    }

    if (isAlertActionPath(url.pathname)) {
      const alertId = Number(url.pathname.split("/").at(-2));
      const alert = networkAlerts.find((row) => row.id === alertId) || networkAlerts[0];
      await fulfillJson(route, { ok: true, alert: { ...alert, acknowledged_at: generatedAt } });
      return;
    }

    if (isUserActionPath(url.pathname) || isTicketActionPath(url.pathname)) {
      if (!requestHeaders["x-admin-intent-id"] || !requestHeaders["x-admin-idempotency-key"] || !requestHeaders["x-admin-confirmation-sha256"]) {
        await fulfillJson(route, { detail: { code: "intent_required", message: "Нужно защищённое намерение" } }, 428);
        return;
      }
      let status: "completed" | "failed" | "uncertain" = "completed";
      if (url.pathname.endsWith("/reply")) {
        const configured = options.ticketReplyOutcomes || [];
        status = configured[Math.min(ticketReplyRequestCount, Math.max(0, configured.length - 1))] || "completed";
        ticketReplyRequestCount += 1;
      }
      await fulfillJson(route, {
        ok: status === "completed",
        status,
        action_intent_id: requestHeaders["x-admin-intent-id"],
        audit_id: status === "uncertain" ? null : 714,
        result_code: status === "failed" ? "fixture_known_failure" : status === "uncertain" ? "fixture_uncertain" : "completed",
      });
      return;
    }

    if (options.failAllLegacyRequests && method === "GET" && LEGACY_GET_PATHS.has(url.pathname)) {
      await fulfillJson(route, { detail: "Legacy request failed", code: "legacy_test_failure" }, 500);
      if (url.pathname === "/api/admin/ops/overview") overviewResponses.push(500);
      return;
    }

    if (isUserInvestigationPath(url.pathname)) {
      const tgId = Number(url.pathname.split("/").at(-2));
      await fulfillJson(route, { ...clientInvestigation, tg_id: tgId });
      return;
    }

    if (isUserDetailPath(url.pathname)) {
      const tgId = Number(url.pathname.split("/").at(-1));
      await fulfillJson(route, clientUserDetail(tgId));
      return;
    }

    if (isTicketDetailPath(url.pathname)) {
      await fulfillJson(route, { ticket: clientTicketDetail });
      return;
    }

    if (url.pathname === "/api/admin/users") {
      const query = (url.searchParams.get("q") || "").trim().toLowerCase();
      const status = (url.searchParams.get("status") || "").trim().toLowerCase();
      const rows = clientUserRows.filter((row) => {
        if (status && status !== "all") {
          if (status === "manual" && row.status !== "manual_test") return false;
          if (status !== "manual" && row.status !== status) return false;
        }
        if (!query) return true;
        return [row.tg_id, row.username, row.display_name, row.app_install_id].filter((value) => value !== null).join(" ").toLowerCase().includes(query);
      });
      await fulfillJson(route, { page: 1, page_size: 80, total: rows.length, sort: url.searchParams.get("sort") || "created_desc", users: rows });
      return;
    }

    if (url.pathname === "/api/admin/online/users") {
      const only = (url.searchParams.get("only") || "").trim().toLowerCase();
      const rows = only ? clientOnlinePayload.rows.filter((row) => row.nodes_online.includes(only)) : clientOnlinePayload.rows;
      await fulfillJson(route, { ...clientOnlinePayload, total: rows.length, rows });
      return;
    }

    if (url.pathname === "/api/admin/tickets") {
      const status = (url.searchParams.get("status") || "").trim().toLowerCase();
      const rows = status && clientTicketList.status !== status ? [] : [clientTicketList];
      await fulfillJson(route, { tickets: rows });
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
      const overviewAlerts = options.overviewAlerts || [];
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
        metrics: {
          status: "fresh",
          age_seconds: 42,
          last_sample_at: "2026-07-15T09:59:18Z",
          stale_after_seconds: 180,
          alerts: {},
          nodes: []
        },
        capacity: {
          nodes: [
            {
              code: "de",
              name: "Germany",
              enabled: true,
              accepting_new_clients: true,
              capacity_state: "available",
              capacity_score: 91,
              cpu_percent: 42,
              online_connections_hint: 118,
              last_health_at: "2026-07-15T09:59:18Z"
            },
            {
              code: "nl",
              name: "Netherlands",
              enabled: true,
              accepting_new_clients: true,
              capacity_state: "available",
              capacity_score: 88,
              cpu_percent: 31,
              online_connections_hint: 96,
              last_health_at: "2026-07-15T09:59:16Z"
            }
          ]
        },
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
        alerts: {
          active: overviewAlerts,
          active_count: overviewAlerts.length,
          critical_count: overviewAlerts.filter((alert) => alert.severity === "critical").length,
          warning_count: overviewAlerts.filter((alert) => alert.severity === "warning").length
        }
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
      const period = url.searchParams.get("period") || "7d";
      const multiplier = period === "today" ? 1 : period === "30d" ? 8 : 3;
      await fulfillJson(route, {
        ok: true,
        period: { key: period, from: generatedAt, to: generatedAt },
        revenue: options.revenueScenario === "populated" ? { currency: "RUB", paid_count: 4 * multiplier, amount: 1295 * multiplier, by_currency: [{ currency: "RUB", paid_count: 4 * multiplier, revenue: 1295 * multiplier }] } : { currency: "RUB", paid_count: 0, amount: 0, by_currency: [] },
        status_counts: options.revenueScenario === "populated" ? { paid: 4 * multiplier, pending: 1, manual_review: 1, failed: 1 } : { paid: 0, pending: 0, manual_review: 0, failed: 0 },
        attention: options.revenueScenario === "populated" ? { pending_count: 1, manual_review_count: 1, failed_count: 1, problem_count: 3 } : { pending_count: 0, manual_review_count: 0, failed_count: 0, problem_count: 0 },
        abandoned: {
          buy_clicks: options.revenueScenario === "populated" ? 12 * multiplier : 0,
          checkout_started: options.revenueScenario === "populated" ? 8 * multiplier : 0,
          paid: options.revenueScenario === "populated" ? 4 * multiplier : 0,
          buy_click_not_paid: options.revenueScenario === "populated" ? 8 * multiplier : 0,
          checkout_not_paid: options.revenueScenario === "populated" ? 4 * multiplier : 0
        },
        problem_orders: options.revenueScenario === "populated" ? [revenueOrders[0]] : []
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
      await fulfillJson(route, options.networkScenario === "populated" ? { ok: true, from: "2026-07-13", to: "2026-07-15", rows: networkTrafficRows } : { rows: [] });
      return;
    }

    if (options.networkScenario === "populated" && url.pathname === "/api/admin/alerts") {
      const wanted = url.searchParams.get("status") || "active";
      const rows = wanted === "resolved" ? [] : networkAlerts;
      await fulfillJson(route, { ok: true, generated_at: generatedAt, alerts: rows });
      return;
    }

    if (options.networkScenario === "populated" && url.pathname === "/api/admin/provider-quotas") {
      await fulfillJson(route, { ok: true, quotas: [networkQuotaConfig] });
      return;
    }

    if (options.networkScenario === "populated" && url.pathname === "/api/admin/provider-quotas/status") {
      await fulfillJson(route, { ok: true, generated_at: generatedAt, nodes: networkQuotaStatuses });
      return;
    }

    if (options.networkScenario === "populated" && url.pathname === "/api/admin/free-tier/summary") {
      await fulfillJson(route, { ok: true, summary: networkFreeSummary, facts: networkFreeFacts });
      return;
    }

    if (options.networkScenario === "populated" && url.pathname === "/api/admin/free-tier/users") {
      const query = (url.searchParams.get("q") || "").toLowerCase();
      const rows = networkFreeUsers.filter((row) => !query || `${row.tg_id} ${row.username} ${row.display_name}`.toLowerCase().includes(query));
      await fulfillJson(route, { ok: true, generated_at: generatedAt, total: rows.length, facts: networkFreeFacts, users: rows });
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

    if (url.pathname === "/api/admin/payments/orders") {
      if (options.paymentOrdersStatus && options.paymentOrdersStatus !== 200) {
        await fulfillJson(route, { detail: "Реестр заказов временно недоступен", code: "payment_orders_unavailable" }, options.paymentOrdersStatus);
        return;
      }
      const wantedStatus = url.searchParams.get("status") || "";
      const q = (url.searchParams.get("q") || "").toLowerCase();
      const rows = (options.revenueScenario === "populated" ? revenueOrders : []).filter((row) => (!wantedStatus || row.status === wantedStatus) && (!q || `${row.order_id} ${row.tg_id}`.toLowerCase().includes(q)));
      await fulfillJson(route, { orders: rows, total: rows.length, limit: 80, offset: 0 });
      return;
    }

    if (isPaymentDetailPath(url.pathname)) {
      const parts = url.pathname.split("/");
      const orderId = decodeURIComponent(parts.at(-1) || "");
      const provider = decodeURIComponent(parts.at(-2) || "");
      const order = revenueOrders.find((row) => row.order_id === orderId && row.provider === provider);
      await fulfillJson(route, order ? { order } : { detail: "Order not found" }, order ? 200 : 404);
      return;
    }

    if (url.pathname === "/api/admin/funnel/summary") {
      if (options.funnelStatus && options.funnelStatus !== 200) {
        await fulfillJson(route, { detail: "Воронка временно недоступна", code: "funnel_unavailable" }, options.funnelStatus);
        return;
      }
      await fulfillJson(route, options.revenueScenario === "populated" ? revenueFunnel : { period: { from: null, to: null }, acquisition: { cohort: "first_touch_in_period", totals: {}, stages: [], drop_reasons: [], by_source: [] }, product: { cohort: "known_user_open_in_period", totals: {}, stages: [], drop_reasons: [] }, notes: [] });
      return;
    }

    if (url.pathname === "/api/admin/promos") {
      if (options.promosStatus && options.promosStatus !== 200) {
        await fulfillJson(route, { detail: "Промокоды временно недоступны", code: "promos_unavailable" }, options.promosStatus);
        return;
      }
      await fulfillJson(route, { promos: options.promoRows ?? (options.revenueScenario === "populated" ? revenuePromos : []) });
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

    if (url.pathname === "/api/admin/referrals/pending") {
      const wanted = url.searchParams.get("status") || "";
      const rows = (options.revenueScenario === "populated" ? revenueReferrals : []).filter((row) => !wanted || row.status === wanted);
      await fulfillJson(route, { rows });
      return;
    }

    const minimalPayloads: Record<string, unknown> = {
      "/api/admin/alerts": { alerts: [] },
      "/api/admin/free-tier/users": { users: [] },
      "/api/admin/free-tier/summary": { summary: { generated_at: generatedAt, free_users: null, sampled_users: null, limit_gb_per_user: null, cycle_days: null, used_gb: null, limit_gb_total: null, remaining_gb: null, used_pct: null, near_cap_users: null, over_cap_users: null, burn_rate_gb_per_day: null, source: null }, facts: { node_pool: null, traffic_limit_gb: null, cycle_days: null, speed_limit_mbps: null, device_limit: null, monthly_reset: null, source: null } },
      "/api/admin/nodes/timeseries": { rows: [] },
      "/api/admin/provider-quotas": { quotas: [] },
      "/api/admin/provider-quotas/status": { generated_at: generatedAt, nodes: [] },
      "/api/admin/emergency-network/status": {
        generated_at: generatedAt,
        worker: {
          enabled: false,
          configuration_state: "disabled",
          interval_seconds: null,
          probe_concurrency: null
        },
        snapshot_counts: {},
        active: null,
        distribution: null,
        probe_summary: {
          snapshot_id: null,
          pending: 0,
          healthy: 0,
          unavailable: 0,
          total: 0
        },
        rollback_candidates: [],
        snapshots: []
      },
      "/api/admin/nodes/health": { nodes: options.ruScenario ? nodeRows : [] },
      "/api/admin/nodes/runtime": { ok: true, nodes: [] },
      "/api/admin/online/users": { ok: true, generated_at: generatedAt, rows: [] },
      "/api/admin/payments/orders": { orders: [] },
      "/api/admin/keys/pressure": { rows: [] },
      "/api/admin/tickets": { tickets: [] },
      "/api/admin/live-updates": { updates: [] },
      "/api/admin/funnel/summary": { period: { from: null, to: null }, acquisition: { cohort: "first_touch_in_period", totals: {}, stages: [], drop_reasons: [], by_source: [] }, product: { cohort: "known_user_open_in_period", totals: {}, stages: [], drop_reasons: [] }, notes: [] },
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
