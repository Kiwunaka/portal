"use client";

import { apiFetch, type ApiRequestInit } from "./client";

export type PaymentPeriod = "today" | "7d" | "30d";
export type FunnelRange = "7d" | "30d" | "90d";

export type PaymentEventState = {
  id: number;
  provider: string;
  event_type: string;
  external_id: string;
  order_id: string | null;
  signature_ok: boolean;
  processed_ok: boolean | null;
  created_at: string | null;
};

export type PaymentOrder = {
  id: number;
  order_id: string;
  provider: string;
  tg_id: number | null;
  user: { tg_id: number; username: string | null; display_name: string | null; status: string } | null;
  plan_code: string | null;
  amount: number | null;
  currency: string | null;
  status: string | null;
  source: string | null;
  campaign: string | null;
  promo_code: string | null;
  created_at: string | null;
  paid_at: string | null;
  event_count: number | null;
  last_event: PaymentEventState | null;
};

export type PaymentSummary = {
  period: { key: PaymentPeriod; from: string | null; to: string | null };
  revenue: { currency: string | null; paid_count: number | null; amount: number | null; by_currency: Array<{ currency: string; paid_count: number | null; revenue: number | null }> };
  status_counts: Record<string, number | null>;
  attention: { pending_count: number | null; manual_review_count: number | null; failed_count: number | null; problem_count: number | null };
  abandoned: { buy_clicks: number | null; checkout_started: number | null; paid: number | null; buy_click_not_paid: number | null; checkout_not_paid: number | null; note: string | null };
  problem_orders: PaymentOrder[];
};

export type PaymentOrdersPayload = { orders: PaymentOrder[]; total: number | null; limit: number | null; offset: number | null };

export type FunnelStage = { key: string; label: string; entered: number | null; reached_next: number | null; dropped: number | null; conversion_pct: number | null };
export type FunnelSource = { source: string; sessions: number | null; entry_intents: number | null; resolved_entries: number | null; checkouts: number | null; paid: number | null; connected: number | null };
export type FunnelDiagnosticRow = { key: string; count: number | null; latest_at: string | null };
export type FunnelVersionRow = { platform: string; app_version: string; events: number | null; users: number | null; latest_at: string | null };
export type FunnelProductObservability = {
  summary: { events: number | null; successes: number | null; failures: number | null; retryable_failures: number | null; active_users_7d: number | null; clock_skewed: number | null; latest_event_at: string | null };
  errors: FunnelDiagnosticRow[];
  error_categories: FunnelDiagnosticRow[];
  stages: FunnelDiagnosticRow[];
  subsystems: FunnelDiagnosticRow[];
  network_classes: FunnelDiagnosticRow[];
  versions: FunnelVersionRow[];
};
export type FunnelPayload = {
  period: { from: string | null; to: string | null };
  acquisition: {
    cohort: string;
    totals: { sessions: number | null; entry_intents: number | null; resolved_entries: number | null; checkouts: number | null; paid: number | null; connected: number | null };
    stages: FunnelStage[];
    drop_reasons: Array<{ reason: string; count: number | null }>;
    by_source: FunnelSource[];
  };
  product: {
    cohort: string;
    totals: { opened: number | null; checkouts: number | null; paid: number | null; connected: number | null };
    stages: FunnelStage[];
    drop_reasons: Array<{ reason: string; count: number | null }>;
    observability: FunnelProductObservability;
  };
  notes: string[];
};

export type PromoRow = {
  code: string;
  promo_type: "discount" | "days" | null;
  value: number | null;
  uses_left: number | null;
  used_count: number | null;
  expires_at: string | null;
  created_at: string | null;
};

export type PromoSlotAssignment = {
  slot_id: string;
  content_id: string;
  enabled: boolean;
  title?: string | null;
  body?: string | null;
  badge_label?: string | null;
  image_url?: string | null;
  image_layout?: "logo" | "banner" | string | null;
  media_type?: "image" | "animated_image" | "video" | string | null;
  media_url?: string | null;
  poster_url?: string | null;
  fallback_image_url?: string | null;
  media_mime?: string | null;
  media_width?: number | null;
  media_height?: number | null;
  media_bytes?: number | null;
  media_duration_seconds?: number | null;
  autoplay?: boolean;
  loop?: boolean;
  cta_label?: string | null;
  cta_href?: string | null;
  accent_color?: string | null;
  background_color?: string | null;
  text_color?: string | null;
  button_color?: string | null;
  button_text_color?: string | null;
  placement?: string | null;
  dismissible?: boolean;
  whole_card_clickable?: boolean;
  starts_at?: string | null;
  ends_at?: string | null;
  countdown_mode?: "none" | "ends_at" | string | null;
  countdown_label?: string | null;
  contexts: string[];
  sort_order: number;
};

export type PromoMediaAsset = {
  id: string;
  url: string;
  media_type: "image" | "animated_image" | "video";
  mime: string;
  bytes: number;
  width: number | null;
  height: number | null;
  sha256: string;
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

export type PromoSlotsPayload = {
  version: string;
  mode: string;
  remote_available: boolean;
  fallback_behavior: string;
  assignments: PromoSlotAssignment[];
  catalog: {
    version: string;
    mode: string;
    fallback_behavior: string;
    slots: PromoSlotCatalogSlot[];
    content_catalog: PromoSlotCatalogContent[];
  };
};

export type ReferralRow = {
  id: number;
  order_id: string;
  referrer_tg_id: number;
  referred_tg_id: number;
  queued_at: string | null;
  ready_at: string | null;
  status: string | null;
  processed_at: string | null;
  basis: string | null;
  meta_present: boolean;
  meta_sha256: string;
};

function finite(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function text(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function stateText(value: unknown): string | null {
  const normalized = text(value);
  return normalized?.toLowerCase() === "unknown" ? null : normalized;
}

function paymentOrder(value: unknown): PaymentOrder | null {
  if (!value || typeof value !== "object") return null;
  const row = value as Record<string, unknown>;
  if (typeof row.id !== "number" || typeof row.order_id !== "string" || typeof row.provider !== "string") return null;
  const rawUser = row.user && typeof row.user === "object" ? row.user as Record<string, unknown> : null;
  const rawEvent = row.last_event && typeof row.last_event === "object" ? row.last_event as Record<string, unknown> : null;
  return {
    id: row.id,
    order_id: row.order_id,
    provider: row.provider,
    tg_id: finite(row.tg_id),
    user: rawUser && typeof rawUser.tg_id === "number" ? {
      tg_id: rawUser.tg_id,
      username: text(rawUser.username),
      display_name: text(rawUser.display_name),
      status: text(rawUser.status) || "unknown",
    } : null,
    plan_code: text(row.plan_code),
    amount: finite(row.amount),
    currency: text(row.currency),
    status: stateText(row.status),
    source: text(row.source),
    campaign: text(row.campaign),
    promo_code: text(row.promo_code),
    created_at: text(row.created_at),
    paid_at: text(row.paid_at),
    event_count: finite(row.event_count),
    last_event: rawEvent && typeof rawEvent.id === "number" ? {
      id: rawEvent.id,
      provider: text(rawEvent.provider) || "",
      event_type: text(rawEvent.event_type) || "",
      external_id: text(rawEvent.external_id) || "",
      order_id: text(rawEvent.order_id),
      signature_ok: rawEvent.signature_ok === true,
      processed_ok: typeof rawEvent.processed_ok === "boolean" ? rawEvent.processed_ok : null,
      created_at: text(rawEvent.created_at),
    } : null,
  };
}

export async function fetchPaymentSummary(period: PaymentPeriod, init?: ApiRequestInit): Promise<PaymentSummary> {
  const data = await apiFetch<Record<string, unknown>>(`/api/admin/payments/summary?period=${period}`, init);
  const revenue = data.revenue && typeof data.revenue === "object" ? data.revenue as Record<string, unknown> : {};
  const attention = data.attention && typeof data.attention === "object" ? data.attention as Record<string, unknown> : {};
  const abandoned = data.abandoned && typeof data.abandoned === "object" ? data.abandoned as Record<string, unknown> : {};
  const rawPeriod = data.period && typeof data.period === "object" ? data.period as Record<string, unknown> : {};
  const statusCounts = data.status_counts && typeof data.status_counts === "object" ? data.status_counts as Record<string, unknown> : {};
  return {
    period: { key: (text(rawPeriod.key) as PaymentPeriod) || period, from: text(rawPeriod.from), to: text(rawPeriod.to) },
    revenue: {
      currency: text(revenue.currency),
      paid_count: finite(revenue.paid_count),
      amount: finite(revenue.amount),
      by_currency: Array.isArray(revenue.by_currency) ? revenue.by_currency.flatMap((item) => {
        if (!item || typeof item !== "object") return [];
        const row = item as Record<string, unknown>;
        const currency = text(row.currency);
        return currency ? [{ currency, paid_count: finite(row.paid_count), revenue: finite(row.revenue) }] : [];
      }) : [],
    },
    status_counts: Object.fromEntries(Object.entries(statusCounts).map(([key, value]) => [key, finite(value)])),
    attention: { pending_count: finite(attention.pending_count), manual_review_count: finite(attention.manual_review_count), failed_count: finite(attention.failed_count), problem_count: finite(attention.problem_count) },
    abandoned: { buy_clicks: finite(abandoned.buy_clicks), checkout_started: finite(abandoned.checkout_started), paid: finite(abandoned.paid), buy_click_not_paid: finite(abandoned.buy_click_not_paid), checkout_not_paid: finite(abandoned.checkout_not_paid), note: text(abandoned.note) },
    problem_orders: Array.isArray(data.problem_orders) ? data.problem_orders.map(paymentOrder).filter((row): row is PaymentOrder => row !== null) : [],
  };
}

export async function fetchPaymentOrders(filters: { status?: string; q?: string; provider?: string }, init?: ApiRequestInit): Promise<PaymentOrdersPayload> {
  const query = new URLSearchParams({ limit: "80" });
  if (filters.status?.trim()) query.set("status", filters.status.trim());
  if (filters.q?.trim()) query.set("q", filters.q.trim());
  if (filters.provider?.trim()) query.set("provider", filters.provider.trim());
  const data = await apiFetch<Record<string, unknown>>(`/api/admin/payments/orders?${query.toString()}`, init);
  return { orders: Array.isArray(data.orders) ? data.orders.map(paymentOrder).filter((row): row is PaymentOrder => row !== null) : [], total: finite(data.total), limit: finite(data.limit), offset: finite(data.offset) };
}

export async function fetchPaymentOrder(provider: string, orderId: string, init?: ApiRequestInit): Promise<PaymentOrder> {
  const data = await apiFetch<{ order?: unknown }>(`/api/admin/payments/orders/${encodeURIComponent(provider)}/${encodeURIComponent(orderId)}`, init);
  const order = paymentOrder(data.order);
  if (!order) throw new Error("Сервер вернул неполную карточку заказа.");
  return order;
}

function rangeBounds(range: FunnelRange): { from: string; to: string } {
  const days = range === "7d" ? 7 : range === "90d" ? 90 : 30;
  const to = new Date();
  const from = new Date(to);
  from.setUTCDate(from.getUTCDate() - days + 1);
  return { from: from.toISOString(), to: to.toISOString() };
}

export async function fetchFunnel(range: FunnelRange, init?: ApiRequestInit): Promise<FunnelPayload> {
  const query = new URLSearchParams(rangeBounds(range));
  const data = await apiFetch<Record<string, unknown>>(`/api/admin/funnel/summary?${query.toString()}`, init);
  const period = data.period && typeof data.period === "object" ? data.period as Record<string, unknown> : {};
  const acquisition = data.acquisition && typeof data.acquisition === "object" ? data.acquisition as Record<string, unknown> : {};
  const product = data.product && typeof data.product === "object" ? data.product as Record<string, unknown> : {};
  const acquisitionTotals = acquisition.totals && typeof acquisition.totals === "object" ? acquisition.totals as Record<string, unknown> : {};
  const productTotals = product.totals && typeof product.totals === "object" ? product.totals as Record<string, unknown> : {};
  const observability = product.observability && typeof product.observability === "object" ? product.observability as Record<string, unknown> : {};
  const observabilitySummary = observability.summary && typeof observability.summary === "object" ? observability.summary as Record<string, unknown> : {};
  const rows = (value: unknown): Record<string, unknown>[] => Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => Boolean(item && typeof item === "object")) : [];
  const stages = (value: unknown): FunnelStage[] => rows(value).map((row) => ({ key: text(row.key) || "unknown", label: text(row.label) || "Без названия", entered: finite(row.entered), reached_next: finite(row.reached_next), dropped: finite(row.dropped), conversion_pct: finite(row.conversion_pct) }));
  const drops = (value: unknown): Array<{ reason: string; count: number | null }> => rows(value).map((row) => ({ reason: text(row.reason) || "Без причины", count: finite(row.count) }));
  const diagnostics = (value: unknown): FunnelDiagnosticRow[] => rows(value).map((row) => ({ key: text(row.key) || "unknown", count: finite(row.count), latest_at: text(row.latest_at) }));
  return {
    period: { from: text(period.from), to: text(period.to) },
    acquisition: {
      cohort: text(acquisition.cohort) || "first_touch_in_period",
      totals: { sessions: finite(acquisitionTotals.sessions), entry_intents: finite(acquisitionTotals.entry_intents), resolved_entries: finite(acquisitionTotals.resolved_entries), checkouts: finite(acquisitionTotals.checkouts), paid: finite(acquisitionTotals.paid), connected: finite(acquisitionTotals.connected) },
      stages: stages(acquisition.stages),
      drop_reasons: drops(acquisition.drop_reasons),
      by_source: rows(acquisition.by_source).map((row) => ({ source: text(row.source) || "unknown", sessions: finite(row.sessions), entry_intents: finite(row.entry_intents), resolved_entries: finite(row.resolved_entries), checkouts: finite(row.checkouts), paid: finite(row.paid), connected: finite(row.connected) })),
    },
    product: {
      cohort: text(product.cohort) || "known_user_open_in_period",
      totals: { opened: finite(productTotals.opened), checkouts: finite(productTotals.checkouts), paid: finite(productTotals.paid), connected: finite(productTotals.connected) },
      stages: stages(product.stages),
      drop_reasons: drops(product.drop_reasons),
      observability: {
        summary: {
          events: finite(observabilitySummary.events),
          successes: finite(observabilitySummary.successes),
          failures: finite(observabilitySummary.failures),
          retryable_failures: finite(observabilitySummary.retryable_failures),
          active_users_7d: finite(observabilitySummary.active_users_7d),
          clock_skewed: finite(observabilitySummary.clock_skewed),
          latest_event_at: text(observabilitySummary.latest_event_at),
        },
        errors: diagnostics(observability.errors),
        error_categories: diagnostics(observability.error_categories),
        stages: diagnostics(observability.stages),
        subsystems: diagnostics(observability.subsystems),
        network_classes: diagnostics(observability.network_classes),
        versions: rows(observability.versions).map((row) => ({ platform: text(row.platform) || "unknown", app_version: text(row.app_version) || "unknown", events: finite(row.events), users: finite(row.users), latest_at: text(row.latest_at) })),
      },
    },
    notes: Array.isArray(data.notes) ? data.notes.filter((item): item is string => typeof item === "string") : [],
  };
}

export async function fetchPromos(init?: ApiRequestInit): Promise<PromoRow[]> {
  const data = await apiFetch<{ promos?: unknown[] }>("/api/admin/promos?limit=100", init);
  return Array.isArray(data.promos) ? data.promos.flatMap((item) => {
    if (!item || typeof item !== "object") return [];
    const row = item as Record<string, unknown>;
    const code = text(row.code);
    const promoType = text(row.promo_type);
    return code ? [{ code, promo_type: promoType === "discount" || promoType === "days" ? promoType : null, value: finite(row.value), uses_left: finite(row.uses_left), used_count: finite(row.used_count), expires_at: text(row.expires_at), created_at: text(row.created_at) }] : [];
  }) : [];
}

export async function fetchPromoSlots(init?: ApiRequestInit): Promise<PromoSlotsPayload> {
  const data = await apiFetch<{ promo_slots: PromoSlotsPayload }>("/api/admin/promo-slots", init);
  return data.promo_slots;
}

export async function uploadPromoMedia(file: File, init?: ApiRequestInit): Promise<PromoMediaAsset> {
  const data = await apiFetch<{ asset: PromoMediaAsset }>("/api/admin/promo-media", {
    ...init,
    method: "POST",
    body: file,
    headers: {
      ...(init?.headers || {}),
      "Content-Type": file.type || "application/octet-stream",
      "X-Upload-Filename": file.name,
    },
    timeoutMs: 60_000,
  });
  return data.asset;
}

export async function fetchReferrals(status: string, init?: ApiRequestInit): Promise<ReferralRow[]> {
  const query = new URLSearchParams({ limit: "100", status });
  const data = await apiFetch<{ rows?: unknown[] }>(`/api/admin/referrals/pending?${query.toString()}`, init);
  return Array.isArray(data.rows) ? data.rows.flatMap((item) => {
    if (!item || typeof item !== "object") return [];
    const row = item as Record<string, unknown>;
    if (typeof row.id !== "number" || typeof row.order_id !== "string" || typeof row.referrer_tg_id !== "number" || typeof row.referred_tg_id !== "number") return [];
    return [{ id: row.id, order_id: row.order_id, referrer_tg_id: row.referrer_tg_id, referred_tg_id: row.referred_tg_id, queued_at: text(row.queued_at), ready_at: text(row.ready_at), status: stateText(row.status), processed_at: text(row.processed_at), basis: stateText(row.basis), meta_present: row.meta_present === true, meta_sha256: text(row.meta_sha256) || "" }];
  }) : [];
}
