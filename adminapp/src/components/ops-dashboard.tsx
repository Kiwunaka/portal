"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import {
  BellOff,
  Check,
  Eye,
  Loader2,
  Power,
  PowerOff,
  RefreshCw,
  RotateCw,
  Save,
  Search,
  Send,
  ShieldAlert,
  Trash2
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { DataTable } from "@/components/data-table";
import { Badge, Button, Card, Progress, SectionTitle, type Tone } from "@/components/ui";
import {
  ackAlert,
  adminCommand,
  clearAdminInitData,
  clearAdminSessionToken,
  createAdminSession,
  deleteProviderQuota,
  fetchAlerts,
  fetchAdminModule,
  fetchAdminUserCard,
  fetchAdminUsers,
  fetchFreeUsers,
  fetchKeyPressure,
  fetchNodeTimeseries,
  fetchNodesHealth,
  fetchNodesRuntime,
  fetchOnlineUsers,
  fetchOpsOverview,
  fetchPaymentOrders,
  fetchPaymentsSummary,
  fetchProviderQuotas,
  fetchTrafficSummary,
  hasAdminAuthMaterial,
  nodeLifecycleAction,
  nodeResync,
  saveAdminInitData,
  saveAdminSessionToken,
  saveProviderQuota,
  sendBroadcast,
  silenceAlert,
  type AdminModulePayload,
  type AdminUserCardPayload,
  type AdminUserRow,
  type AdminUsersPayload,
  type FreeTierUser,
  type NodeHealthRow,
  type NodeTimeseriesRow,
  type OnlineUsersPayload,
  type OpsAlert,
  type OpsOverview,
  type PaymentsSummaryPayload,
  type ProviderQuotaConfig,
  type ProviderQuotaStatus,
  type TrafficSummaryRow
} from "@/lib/api";
import { formatGb, formatInt, formatPct, shortDateTime } from "@/lib/format";

type OpsDashboardSection =
  | "dashboard"
  | "users"
  | "online"
  | "nodes"
  | "payments"
  | "funnel"
  | "tickets"
  | "alerts"
  | "traffic"
  | "free-tier"
  | "provider-caps"
  | "promos"
  | "referrals"
  | "release"
  | "broadcast";

type AnyRow = Record<string, unknown>;

type QuotaFormState = {
  node_code: string;
  included_gb: string;
  reset_day: string;
  timezone: string;
  warning_ratio: string;
  critical_ratio: string;
  enabled: boolean;
  notes: string;
};

type NodePendingAction = {
  action: "drain" | "enable" | "undrain" | "disable" | "resync";
  code: string;
  confirm: string;
  force: boolean;
  limit: string;
};

const moduleSections = new Set<OpsDashboardSection>(["promos", "referrals"]);

function asRecord(value: unknown): AnyRow {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as AnyRow) : {};
}

function asRows(value: unknown): AnyRow[] {
  return Array.isArray(value) ? value.map(asRecord) : [];
}

function text(value: unknown, fallback = "n/a"): string {
  if (value === null || value === undefined) return fallback;
  const raw = String(value).trim();
  return raw || fallback;
}

function numberValue(value: unknown): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function boolText(value: unknown): string {
  if (value === true) return "да";
  if (value === false) return "нет";
  return "n/a";
}

function compactValue(value: unknown): string {
  if (value == null) return "n/a";
  if (typeof value === "boolean") return boolText(value);
  if (typeof value === "number") return Number.isInteger(value) ? formatInt(value) : value.toFixed(2);
  if (Array.isArray(value)) return value.map((item) => text(item, "")).filter(Boolean).join(", ") || "n/a";
  if (typeof value === "object") return "есть данные";
  return String(value);
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

function toneForState(value?: unknown): Tone {
  const v = String(value || "").toLowerCase();
  if (["critical", "danger", "over_cap", "hard_reject", "error", "failed", "blocked", "suspicious", "manual_review"].includes(v)) return "danger";
  if (["warning", "near_cap", "stale", "degraded", "pending", "created", "watch", "draining", "not_accepting_new_clients"].includes(v)) return "warning";
  if (["ok", "healthy", "active", "paid", "success", "fresh", "enabled"].includes(v)) return "success";
  if (["silenced", "info", "trial", "free", "manual"].includes(v)) return "info";
  return "neutral";
}

function nodeRiskTone(node: NodeHealthRow): Tone {
  if (!node.enabled || node.capacity_state === "hard_reject" || node.is_healthy === false) return "danger";
  if (node.is_draining || node.accepting_new_clients === false || node.freshness_status === "stale" || node.observer_is_stale) return "warning";
  if (node.dataplane_ok === false || numberValue(node.panel_error_rate) > 0) return "warning";
  return "success";
}

function formatMoney(amount: unknown, currency: unknown): string {
  const n = numberValue(amount);
  const c = text(currency, "RUB").toUpperCase();
  return `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 }).format(n)} ${c}`;
}

function listText(value: unknown, max = 4): string {
  const items = Array.isArray(value) ? value.map((item) => text(item, "")).filter(Boolean) : [];
  if (!items.length) return "n/a";
  const visible = items.slice(0, max).join(", ");
  return items.length > max ? `${visible} +${items.length - max}` : visible;
}

function settledValue<T>(result: PromiseSettledResult<T>, fallback: T): T {
  return result.status === "fulfilled" ? result.value : fallback;
}

function settledError(result: PromiseSettledResult<unknown>): string {
  return result.status === "rejected" ? errorMessage(result.reason, "request failed") : "";
}

function buildTrafficChart(rows: TrafficSummaryRow[]) {
  const buckets = new Map<string, { date: string; free: number; premium: number; total: number }>();
  for (const row of rows) {
    const bucket = buckets.get(row.date) || { date: row.date, free: 0, premium: 0, total: 0 };
    const isFree = row.pool_code.toLowerCase().includes("free") || row.node_code.toLowerCase().includes("free");
    if (isFree) bucket.free += row.traffic_gb;
    else bucket.premium += row.traffic_gb;
    bucket.total += row.traffic_gb;
    buckets.set(row.date, bucket);
  }
  return Array.from(buckets.values()).sort((a, b) => a.date.localeCompare(b.date));
}

function buildNodeChart(rows: NodeTimeseriesRow[]) {
  return rows
    .filter((row) => row.sampled_at)
    .slice(-140)
    .map((row) => ({
      t: shortDateTime(row.sampled_at),
      node: row.node_code,
      cpu: Number(row.cpu_percent || 0),
      net: Number(row.network_total_mbps || 0),
      score: Number(row.capacity_score || row.score || 0)
    }));
}

function stateLabel(value: unknown): string {
  const v = String(value || "").toLowerCase();
  const labels: Record<string, string> = {
    active: "активен",
    expired: "истек",
    blocked: "заблокирован",
    paid: "оплачено",
    pending: "ждет",
    created: "создан",
    failed: "ошибка",
    manual_review: "ручная проверка",
    ok: "ок",
    healthy: "здорово",
    stale: "устарело",
    hard_reject: "не выдавать",
    degraded: "просадка",
    warning: "внимание",
    critical: "критично"
  };
  return labels[v] || text(value);
}

function MetricTile({ label, value, detail, tone = "neutral" }: { label: string; value: string; detail?: string; tone?: Tone }) {
  return (
    <Card className="min-h-[108px]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[11px] uppercase tracking-[0.08em] text-[color:var(--atlas-text-muted)]">{label}</div>
          <div className="mt-2 text-2xl font-semibold leading-none text-[color:var(--atlas-text)]">{value}</div>
          {detail ? <div className="mt-2 text-xs leading-5 text-[color:var(--atlas-text-soft)]">{detail}</div> : null}
        </div>
        <Badge tone={tone}>{stateLabel(tone)}</Badge>
      </div>
    </Card>
  );
}

function EmptyState({ text: label }: { text: string }) {
  return (
    <div className="rounded-[var(--pokrov-radius-card)] border border-dashed border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-4 py-6 text-sm text-[color:var(--atlas-text-soft)]">
      {label}
    </div>
  );
}

function Field({ label, value, tone }: { label: string; value: unknown; tone?: Tone }) {
  return (
    <div className="min-w-0 rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 py-2">
      <div className="text-[11px] uppercase tracking-[0.08em] text-[color:var(--atlas-text-muted)]">{label}</div>
      <div className="mt-1 truncate text-sm font-semibold text-[color:var(--atlas-text)]">
        {tone ? <Badge tone={tone}>{compactValue(value)}</Badge> : compactValue(value)}
      </div>
    </div>
  );
}

function AuthGate({ onReady }: { onReady: () => void }) {
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const autoTriedRef = useRef(false);

  const startSession = useCallback(
    async (initData?: string, options?: { silent?: boolean }) => {
      setBusy(true);
      if (!options?.silent) setError("");
      try {
        const clean = String(initData || "").trim();
        if (clean) saveAdminInitData(clean);
        const session = await createAdminSession();
        saveAdminSessionToken(session.token);
        clearAdminInitData();
        onReady();
      } catch (err) {
        if (!options?.silent) setError(errorMessage(err, "Не удалось открыть admin session"));
      } finally {
        setBusy(false);
      }
    },
    [onReady]
  );

  useEffect(() => {
    if (autoTriedRef.current) return;
    autoTriedRef.current = true;
    void startSession("", { silent: true });
  }, [startSession]);

  return (
    <div className="grid min-h-[62vh] place-items-center">
      <Card className="w-full max-w-xl">
        <SectionTitle title="Вход в админку" description="Сначала пробуем текущую web session. Если она не пришла, вставь Telegram WebApp initData один раз." />
        <textarea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder="query_id=...&user=...&auth_date=...&hash=..."
          className="min-h-28 w-full rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 text-xs outline-none focus:border-[color:var(--atlas-focus)]"
        />
        <div className="mt-3 flex flex-wrap gap-2">
          <Button tone="primary" disabled={busy} onClick={() => void startSession()}>
            {busy ? <Loader2 className="animate-spin" size={15} /> : <Check size={15} />} Войти через текущую сессию
          </Button>
          <Button tone="secondary" disabled={busy || !value.trim()} onClick={() => void startSession(value)}>
            {busy ? <Loader2 className="animate-spin" size={15} /> : <Check size={15} />} Войти по initData
          </Button>
          <Button
            tone="ghost"
            onClick={() => {
              clearAdminInitData();
              clearAdminSessionToken();
              setValue("");
            }}
          >
            Сбросить
          </Button>
        </div>
        {error ? <div className="mt-3"><Badge tone="danger">{error}</Badge></div> : null}
      </Card>
    </div>
  );
}

function ModuleActionPanel({ section, onDone }: { section: OpsDashboardSection; onDone: () => Promise<void> }) {
  const [values, setValues] = useState<Record<string, string>>({
    promo_code: "",
    promo_type: "days",
    promo_value: "7",
    promo_uses: "1",
    gift_card_type: "standard",
    referral_id: "",
    referral_decision: "approve"
  });
  const [busy, setBusy] = useState("");
  const [result, setResult] = useState("");
  const [error, setError] = useState("");

  const run = async (key: string) => {
    setBusy(key);
    setResult("");
    setError("");
    try {
      let path = "";
      const method: "POST" | "PATCH" | "DELETE" = "POST";
      let payload: AnyRow | undefined;
      if (key === "promo_create") {
        path = "/api/admin/promos";
        payload = {
          code: values.promo_code.trim(),
          promo_type: values.promo_type.trim(),
          value: Number(values.promo_value || 0),
          uses_left: Number(values.promo_uses || 1)
        };
      } else if (key === "gift_create") {
        path = "/api/admin/gift-codes";
        payload = { card_type: values.gift_card_type.trim() };
      } else if (key === "referral_decide") {
        path = `/api/admin/referrals/${encodeURIComponent(values.referral_id.trim())}/decision`;
        payload = { decision: values.referral_decision.trim() };
      }
      if (!path) return;
      const output = await adminCommand(path, method, payload);
      setResult(`ok: ${compactValue(output.ok ?? true)}`);
      await onDone();
    } catch (err) {
      setError(errorMessage(err, "Action failed"));
    } finally {
      setBusy("");
    }
  };

  if (section === "promos") {
    return (
      <Card>
        <SectionTitle title="Промо и gift-коды" description="Создание без сырого JSON: код, тип, номинал и лимит активаций." />
        <div className="grid gap-3 md:grid-cols-5">
          {[
            ["promo_code", "код"],
            ["promo_type", "тип"],
            ["promo_value", "значение"],
            ["promo_uses", "активаций"],
            ["gift_card_type", "gift тип"]
          ].map(([key, label]) => (
            <label key={key} className="text-xs font-semibold text-[color:var(--atlas-text-soft)]">
              {label}
              <input
                value={values[key] || ""}
                onChange={(event) => setValues({ ...values, [key]: event.target.value })}
                className="mt-1 h-9 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]"
              />
            </label>
          ))}
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Button tone="primary" disabled={busy === "promo_create" || !values.promo_code.trim()} onClick={() => void run("promo_create")}>
            {busy === "promo_create" ? <Loader2 className="animate-spin" size={15} /> : <Save size={15} />} Создать промо
          </Button>
          <Button tone="secondary" disabled={busy === "gift_create"} onClick={() => void run("gift_create")}>
            {busy === "gift_create" ? <Loader2 className="animate-spin" size={15} /> : <Save size={15} />} Создать gift
          </Button>
          {error ? <Badge tone="danger">{error}</Badge> : null}
          {result ? <Badge tone="success">{result}</Badge> : null}
        </div>
      </Card>
    );
  }

  if (section === "referrals") {
    return (
      <Card>
        <SectionTitle title="Рефералы" description="Очередь решений: approve или reject по referral id." />
        <div className="grid gap-3 md:grid-cols-[1fr_220px_auto] md:items-end">
          <label className="text-xs font-semibold text-[color:var(--atlas-text-soft)]">
            referral id
            <input
              value={values.referral_id || ""}
              onChange={(event) => setValues({ ...values, referral_id: event.target.value })}
              className="mt-1 h-9 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]"
            />
          </label>
          <label className="text-xs font-semibold text-[color:var(--atlas-text-soft)]">
            решение
            <select
              value={values.referral_decision}
              onChange={(event) => setValues({ ...values, referral_decision: event.target.value })}
              className="mt-1 h-9 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]"
            >
              <option value="approve">approve</option>
              <option value="reject">reject</option>
            </select>
          </label>
          <Button tone="primary" disabled={busy === "referral_decide" || !values.referral_id.trim()} onClick={() => void run("referral_decide")}>
            {busy === "referral_decide" ? <Loader2 className="animate-spin" size={15} /> : <Check size={15} />} Применить
          </Button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {error ? <Badge tone="danger">{error}</Badge> : null}
          {result ? <Badge tone="success">{result}</Badge> : null}
        </div>
      </Card>
    );
  }

  return null;
}

function UserCard({
  card,
  loading,
  error
}: {
  card: AdminUserCardPayload | null;
  loading: boolean;
  error: string;
}) {
  if (loading) {
    return (
      <Card>
        <SectionTitle title="Карточка пользователя" />
        <div className="flex items-center gap-2 text-sm text-[color:var(--atlas-text-soft)]">
          <Loader2 className="animate-spin" size={16} /> Загружаю карточку
        </div>
      </Card>
    );
  }
  if (error) {
    return (
      <Card>
        <SectionTitle title="Карточка пользователя" />
        <Badge tone="danger">{error}</Badge>
      </Card>
    );
  }
  if (!card) {
    return (
      <Card>
        <SectionTitle title="Карточка пользователя" />
        <EmptyState text="Выбери пользователя в таблице." />
      </Card>
    );
  }

  const user = asRecord(card.user);
  const summary = asRecord(card.summary || card.keys_state?.summary);
  const keys = asRows(card.keys || card.keys_state?.keys);
  const observer = asRecord(card.observer);
  const risk = asRecord(card.risk);
  const recentIps = asRows(observer.recent_ips);
  const tickets = asRows(card.tickets);
  const payments = asRows(card.payment_orders);
  const history = asRows(card.key_history);
  const adminActions = asRows(card.admin_actions);

  const keyColumns: ColumnDef<AnyRow>[] = [
    { header: "Нода", cell: ({ row }) => text(row.original.node_code) },
    { header: "Есть", cell: ({ row }) => <Badge tone={row.original.exists ? "success" : "neutral"}>{boolText(row.original.exists)}</Badge> },
    { header: "Вкл", cell: ({ row }) => <Badge tone={row.original.enabled ? "success" : "warning"}>{boolText(row.original.enabled)}</Badge> },
    { header: "Онлайн", cell: ({ row }) => <Badge tone={row.original.online ? "success" : "neutral"}>{boolText(row.original.online)}</Badge> },
    { header: "IP/conn", cell: ({ row }) => formatInt(numberValue(row.original.current_connections)) },
    { header: "Трафик", cell: ({ row }) => formatGb(numberValue(row.original.total_gb)) },
    { header: "subId", cell: ({ row }) => <Badge tone={row.original.sub_id_match ? "success" : "danger"}>{row.original.sub_id_match ? "match" : "mismatch"}</Badge> }
  ];
  const paymentColumns: ColumnDef<AnyRow>[] = [
    { header: "Заказ", cell: ({ row }) => text(row.original.order_id || row.original.id) },
    { header: "Провайдер", cell: ({ row }) => text(row.original.provider) },
    { header: "Статус", cell: ({ row }) => <Badge tone={toneForState(row.original.status)}>{stateLabel(row.original.status)}</Badge> },
    { header: "Сумма", cell: ({ row }) => formatMoney(row.original.amount, row.original.currency) },
    { header: "Создан", cell: ({ row }) => shortDateTime(text(row.original.created_at, "")) }
  ];
  const ticketColumns: ColumnDef<AnyRow>[] = [
    { header: "ID", cell: ({ row }) => text(row.original.id) },
    { header: "Статус", cell: ({ row }) => <Badge tone={toneForState(row.original.status)}>{stateLabel(row.original.status)}</Badge> },
    { header: "Тема", cell: ({ row }) => text(row.original.subject || row.original.title || row.original.last_message) },
    { header: "Обновлен", cell: ({ row }) => shortDateTime(text(row.original.updated_at || row.original.created_at, "")) }
  ];
  const ipColumns: ColumnDef<AnyRow>[] = [
    { header: "IP", cell: ({ row }) => text(row.original.source_ip_raw) },
    { header: "Нода", cell: ({ row }) => text(row.original.node_code) },
    { header: "Подозр.", cell: ({ row }) => <Badge tone={row.original.counts_for_suspicion ? "warning" : "neutral"}>{boolText(row.original.counts_for_suspicion)}</Badge> },
    { header: "Последний раз", cell: ({ row }) => shortDateTime(text(row.original.last_seen_at, "")) }
  ];
  const historyColumns: ColumnDef<AnyRow>[] = [
    { header: "Время", cell: ({ row }) => shortDateTime(text(row.original.created_at, "")) },
    { header: "Действие", cell: ({ row }) => text(row.original.action) },
    { header: "Нода", cell: ({ row }) => text(row.original.node_code) },
    { header: "Оператор", cell: ({ row }) => text(row.original.actor_tg_id) }
  ];

  return (
    <div className="space-y-3">
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <SectionTitle title={`Пользователь ${text(user.tg_id)}`} description={text(user.display_name || user.username || user.app_install_id, "без имени")} />
          <div className="flex flex-wrap gap-2">
            <Badge tone={toneForState(user.status)}>{stateLabel(user.status)}</Badge>
            <Badge tone={toneForState(user.sub_type)}>{text(user.sub_type)}</Badge>
            <Badge tone={toneForState(observer.state)}>{stateLabel(observer.state || "ok")}</Badge>
          </div>
        </div>
        <div className="grid gap-2 md:grid-cols-3 xl:grid-cols-6">
          <Field label="доступ до" value={shortDateTime(text(user.expiry_at, ""))} />
          <Field label="онлайн нод" value={summary.nodes_online ?? summary.online_keys_now ?? 0} tone={numberValue(summary.online_keys_now) > 0 ? "success" : "neutral"} />
          <Field label="соединений" value={summary.online_connections_now ?? 0} />
          <Field label="IP 24ч" value={observer.observed_ip_count_24h ?? summary.active_users_estimate ?? 0} tone={numberValue(observer.observed_ip_count_24h) > 1 ? "warning" : "neutral"} />
          <Field label="subId mismatch" value={summary.subid_mismatch_count ?? 0} tone={numberValue(summary.subid_mismatch_count) > 0 ? "danger" : "success"} />
          <Field label="risk" value={risk.state || risk.level || observer.state || "ok"} tone={toneForState(risk.state || risk.level || observer.state || "ok")} />
        </div>
      </Card>

      <Card>
        <SectionTitle title="Ноды и ключи" description="Ключи и IP спрятаны внутри карточки, а не в общем списке." />
        <DataTable data={keys} columns={keyColumns} empty="Ключи не найдены или panel недоступна" />
      </Card>

      <Card>
        <SectionTitle title="IP-наблюдения" description="Raw IP показываем только здесь, для конкретного пользователя." />
        <DataTable data={recentIps} columns={ipColumns} empty="Нет свежих IP-наблюдений" />
      </Card>

      <div className="grid gap-3 xl:grid-cols-2">
        <Card>
          <SectionTitle title="Платежи пользователя" />
          <DataTable data={payments} columns={paymentColumns} empty="Платежей нет" />
        </Card>
        <Card>
          <SectionTitle title="Тикеты пользователя" />
          <DataTable data={tickets} columns={ticketColumns} empty="Тикетов нет" />
        </Card>
      </div>

      <div className="grid gap-3 xl:grid-cols-2">
        <Card>
          <SectionTitle title="История ключей" />
          <DataTable data={history} columns={historyColumns} empty="Истории нет" />
        </Card>
        <Card>
          <SectionTitle title="История действий админки" />
          <DataTable data={adminActions} columns={historyColumns} empty="Действий нет" />
        </Card>
      </div>
    </div>
  );
}

export function OpsDashboard({ section }: { section: OpsDashboardSection }) {
  const [authReady, setAuthReady] = useState(false);
  const [overview, setOverview] = useState<OpsOverview | null>(null);
  const [alerts, setAlerts] = useState<OpsAlert[]>([]);
  const [freeUsers, setFreeUsers] = useState<FreeTierUser[]>([]);
  const [trafficRows, setTrafficRows] = useState<TrafficSummaryRow[]>([]);
  const [timeseriesRows, setTimeseriesRows] = useState<NodeTimeseriesRow[]>([]);
  const [quotas, setQuotas] = useState<ProviderQuotaConfig[]>([]);
  const [nodes, setNodes] = useState<NodeHealthRow[]>([]);
  const [runtimePayload, setRuntimePayload] = useState<AnyRow>({});
  const [onlinePayload, setOnlinePayload] = useState<OnlineUsersPayload | null>(null);
  const [paymentsToday, setPaymentsToday] = useState<PaymentsSummaryPayload | null>(null);
  const [payments7d, setPayments7d] = useState<PaymentsSummaryPayload | null>(null);
  const [payments30d, setPayments30d] = useState<PaymentsSummaryPayload | null>(null);
  const [paymentOrders, setPaymentOrders] = useState<AnyRow[]>([]);
  const [keyPressure, setKeyPressure] = useState<AnyRow[]>([]);
  const [ticketsRows, setTicketsRows] = useState<AnyRow[]>([]);
  const [releaseRows, setReleaseRows] = useState<AnyRow[]>([]);
  const [funnelPayload, setFunnelPayload] = useState<AnyRow>({});
  const [modulePayload, setModulePayload] = useState<AdminModulePayload | null>(null);
  const [usersPayload, setUsersPayload] = useState<AdminUsersPayload | null>(null);
  const [userSearch, setUserSearch] = useState("");
  const [userStatus, setUserStatus] = useState("");
  const [selectedTgId, setSelectedTgId] = useState<number | null>(null);
  const [userCard, setUserCard] = useState<AdminUserCardPayload | null>(null);
  const [userCardLoading, setUserCardLoading] = useState(false);
  const [userCardError, setUserCardError] = useState("");
  const [selectedNodeCode, setSelectedNodeCode] = useState("");
  const [pendingNodeAction, setPendingNodeAction] = useState<NodePendingAction | null>(null);
  const [nodeActionBusy, setNodeActionBusy] = useState(false);
  const [nodeActionResult, setNodeActionResult] = useState("");
  const [nodeActionError, setNodeActionError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastLoadedAt, setLastLoadedAt] = useState("");
  const [quotaForm, setQuotaForm] = useState<QuotaFormState | null>(null);
  const [savingQuota, setSavingQuota] = useState(false);
  const [deletingQuota, setDeletingQuota] = useState(false);
  const [quotaError, setQuotaError] = useState("");
  const [alertActionId, setAlertActionId] = useState<number | null>(null);
  const [broadcastText, setBroadcastText] = useState("");
  const [broadcastSegment, setBroadcastSegment] = useState("all_active");
  const [broadcastLimit, setBroadcastLimit] = useState("100");
  const [broadcastTgIds, setBroadcastTgIds] = useState("");
  const [broadcastConfirm, setBroadcastConfirm] = useState("");
  const [broadcastPreview, setBroadcastPreview] = useState<AnyRow | null>(null);
  const [broadcastResult, setBroadcastResult] = useState<AnyRow | null>(null);
  const [broadcastSending, setBroadcastSending] = useState(false);
  const [broadcastError, setBroadcastError] = useState("");

  useEffect(() => {
    const applySearch = (q: string) => {
      setUserSearch(q);
      setSelectedTgId(/^-?\d+$/.test(q.trim()) ? Number(q.trim()) : null);
    };
    if (typeof window !== "undefined" && section === "users") {
      const q = new URLSearchParams(window.location.search).get("q") || "";
      if (q) applySearch(q);
    }
    const handler = (event: Event) => {
      const detail = (event as CustomEvent<{ q?: string }>).detail;
      if (detail?.q) applySearch(String(detail.q));
    };
    window.addEventListener("pokrov-admin-global-search", handler);
    return () => window.removeEventListener("pokrov-admin-global-search", handler);
  }, [section]);

  const load = useCallback(async () => {
    if (!hasAdminAuthMaterial()) {
      setLoading(false);
      setAuthReady(false);
      return;
    }
    setAuthReady(true);
    setLoading(true);
    setError("");
    const modulePromise = moduleSections.has(section) ? fetchAdminModule(section) : Promise.resolve(null);
    const [
      overviewResult,
      alertsResult,
      freeResult,
      trafficResult,
      timeseriesResult,
      quotasResult,
      nodesResult,
      runtimeResult,
      onlineResult,
      todayResult,
      weekResult,
      monthResult,
      ordersResult,
      pressureResult,
      ticketsResult,
      releaseResult,
      funnelResult,
      usersResult,
      moduleResult
    ] = await Promise.allSettled([
      fetchOpsOverview(),
      fetchAlerts("active"),
      fetchFreeUsers(),
      fetchTrafficSummary(),
      fetchNodeTimeseries(),
      fetchProviderQuotas(),
      fetchNodesHealth(),
      fetchNodesRuntime(),
      fetchOnlineUsers({ limit: 200 }),
      fetchPaymentsSummary("today"),
      fetchPaymentsSummary("7d"),
      fetchPaymentsSummary("30d"),
      fetchPaymentOrders(80),
      fetchKeyPressure(),
      fetchAdminModule("tickets"),
      fetchAdminModule("release"),
      fetchAdminModule("funnel"),
      fetchAdminUsers({ q: userSearch, status: userStatus, limit: 80, sort: "created_desc" }),
      modulePromise
    ]);

    setOverview(settledValue(overviewResult, null));
    setAlerts(settledValue(alertsResult, []));
    setFreeUsers(settledValue(freeResult, []));
    setTrafficRows(settledValue(trafficResult, []));
    setTimeseriesRows(settledValue(timeseriesResult, []));
    setQuotas(settledValue(quotasResult, []));
    setNodes(settledValue(nodesResult, []));
    setRuntimePayload(asRecord(settledValue(runtimeResult, { ok: false, nodes: [] })));
    setOnlinePayload(settledValue(onlineResult, null));
    setPaymentsToday(settledValue(todayResult, null));
    setPayments7d(settledValue(weekResult, null));
    setPayments30d(settledValue(monthResult, null));
    setPaymentOrders(settledValue(ordersResult, []));
    setKeyPressure(settledValue(pressureResult, []));
    setTicketsRows(settledValue(ticketsResult, { section: "tickets", rows: [], payload: {} }).rows || []);
    setReleaseRows(settledValue(releaseResult, { section: "release", rows: [], payload: {} }).rows || []);
    setFunnelPayload(settledValue(funnelResult, { section: "funnel", rows: [], payload: {} }).payload || {});
    setUsersPayload(settledValue(usersResult, null));
    setModulePayload(settledValue(moduleResult, null));
    setLastLoadedAt(new Date().toISOString());

    const errors = [
      settledError(overviewResult),
      settledError(alertsResult),
      settledError(nodesResult),
      settledError(onlineResult),
      settledError(todayResult),
      settledError(usersResult)
    ].filter(Boolean);
    setError(errors.length ? errors.slice(0, 2).join(" | ") : "");
    setLoading(false);
  }, [section, userSearch, userStatus]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const firstUserTgId = useMemo(() => {
    const value = usersPayload?.users?.[0]?.tg_id;
    return value === undefined || value === null ? null : Number(value);
  }, [usersPayload]);
  const activeSelectedTgId = selectedTgId ?? firstUserTgId;

  const defaultSelectedNodeCode = useMemo(() => {
    if (!nodes.length) return "";
    const firstProblem = [...nodes].sort((a, b) => {
      const rank = (node: NodeHealthRow) => (nodeRiskTone(node) === "danger" ? 0 : nodeRiskTone(node) === "warning" ? 1 : 2);
      return rank(a) - rank(b);
    })[0];
    return String(firstProblem?.code || nodes[0]?.code || "");
  }, [nodes]);
  const activeSelectedNodeCode = selectedNodeCode || defaultSelectedNodeCode;

  useEffect(() => {
    let cancelled = false;
    if (!activeSelectedTgId || !authReady) {
      const timer = window.setTimeout(() => {
        if (!cancelled) {
          setUserCard(null);
          setUserCardLoading(false);
          setUserCardError("");
        }
      }, 0);
      return () => {
        cancelled = true;
        window.clearTimeout(timer);
      };
    }

    const timer = window.setTimeout(() => {
      setUserCardLoading(true);
      setUserCardError("");
      fetchAdminUserCard(activeSelectedTgId)
        .then((payload) => {
          if (!cancelled) setUserCard(payload);
        })
        .catch((err) => {
          if (!cancelled) {
            setUserCard(null);
            setUserCardError(errorMessage(err, "Карточка пользователя не загрузилась"));
          }
        })
        .finally(() => {
          if (!cancelled) setUserCardLoading(false);
        });
    }, 0);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [activeSelectedTgId, authReady]);

  const configuredByNode = useMemo(() => new Set(quotas.map((q) => q.node_code.toLowerCase())), [quotas]);
  const providerStatus = overview?.provider_quotas || [];
  const trafficChart = useMemo(() => buildTrafficChart(trafficRows), [trafficRows]);
  const nodeChart = useMemo(() => buildNodeChart(timeseriesRows), [timeseriesRows]);
  const selectedNode = useMemo(() => nodes.find((node) => String(node.code).toLowerCase() === activeSelectedNodeCode.toLowerCase()) || nodes[0] || null, [activeSelectedNodeCode, nodes]);
  const onlineRows = useMemo(() => onlinePayload?.rows || [], [onlinePayload]);
  const problemNodes = useMemo(() => nodes.filter((node) => nodeRiskTone(node) !== "success"), [nodes]);
  const problemOrders = useMemo(() => payments7d?.problem_orders || paymentsToday?.problem_orders || [], [payments7d, paymentsToday]);
  const activeTicketRows = useMemo(() => ticketsRows.filter((row) => !["closed", "resolved"].includes(String(row.status || "").toLowerCase())), [ticketsRows]);
  const pressureProblemRows = useMemo(() => keyPressure.filter((row) => String(row.state || "ok") !== "ok" || Boolean(row.manual_review_required)), [keyPressure]);

  const actionItems = useMemo(() => {
    const items: Array<{ kind: string; title: string; detail: string; tone: Tone; action: OpsDashboardSection }> = [];
    for (const alert of alerts.slice(0, 5)) {
      items.push({
        kind: "alert",
        title: alert.title,
        detail: `${stateLabel(alert.severity)} · ${text(alert.node_code || alert.source)}`,
        tone: toneForState(alert.severity),
        action: "alerts"
      });
    }
    for (const node of problemNodes.slice(0, 5)) {
      items.push({
        kind: "node",
        title: `Нода ${node.code}`,
        detail: `${stateLabel(node.capacity_state || (node.is_healthy ? "ok" : "critical"))} · panel ${compactValue(node.panel_latency_ms)} ms · dataplane ${boolText(node.dataplane_ok)}`,
        tone: nodeRiskTone(node),
        action: "nodes"
      });
    }
    for (const order of problemOrders.slice(0, 5)) {
      items.push({
        kind: "payment",
        title: `Оплата ${text(order.order_id || order.id)}`,
        detail: `${stateLabel(order.status)} · ${formatMoney(order.amount, order.currency)} · tg ${text(order.tg_id)}`,
        tone: toneForState(order.status),
        action: "payments"
      });
    }
    for (const row of pressureProblemRows.slice(0, 4)) {
      items.push({
        kind: "key",
        title: `Ключ ${text(row.key_id)} требует внимания`,
        detail: `tg ${text(row.tg_id)} · ${text(row.node_code)} · score ${compactValue(row.pressure_score)}`,
        tone: Boolean(row.manual_review_required) ? "danger" : toneForState(row.state),
        action: "online"
      });
    }
    for (const row of activeTicketRows.slice(0, 4)) {
      items.push({
        kind: "ticket",
        title: `Тикет ${text(row.id)}`,
        detail: `${stateLabel(row.status)} · tg ${text(row.user_tg_id || row.tg_id)}`,
        tone: toneForState(row.status || "warning"),
        action: "tickets"
      });
    }
    return items.slice(0, 14);
  }, [activeTicketRows, alerts, problemNodes, problemOrders, pressureProblemRows]);

  const alertColumns: ColumnDef<OpsAlert>[] = useMemo(() => [
    { header: "Срочность", cell: ({ row }) => <Badge tone={toneForState(row.original.severity)}>{stateLabel(row.original.severity)}</Badge> },
    { header: "Что случилось", cell: ({ row }) => <div className="min-w-[220px]"><div className="font-semibold">{row.original.title}</div><div className="text-[color:var(--atlas-text-soft)]">{row.original.body || row.original.fingerprint}</div></div> },
    { header: "Нода/источник", cell: ({ row }) => text(row.original.node_code || row.original.source) },
    { header: "Последний раз", cell: ({ row }) => shortDateTime(row.original.last_seen_at) },
    {
      header: "Действие",
      cell: ({ row }) => (
        <div className="flex gap-2">
          <Button
            tone="secondary"
            disabled={alertActionId === row.original.id}
            onClick={async () => {
              setAlertActionId(row.original.id);
              try {
                await ackAlert(row.original.id);
                await load();
              } finally {
                setAlertActionId(null);
              }
            }}
          >
            <Check size={14} /> Ack
          </Button>
          <Button
            tone="ghost"
            disabled={alertActionId === row.original.id}
            onClick={async () => {
              setAlertActionId(row.original.id);
              try {
                await silenceAlert(row.original.id, 60);
                await load();
              } finally {
                setAlertActionId(null);
              }
            }}
          >
            <BellOff size={14} /> 1ч
          </Button>
        </div>
      )
    }
  ], [alertActionId, load]);

  const userColumns: ColumnDef<AdminUserRow>[] = useMemo(() => [
    {
      header: "Пользователь",
      cell: ({ row }) => (
        <button
          className="text-left font-semibold text-[color:var(--atlas-text)] hover:underline"
          onClick={() => setSelectedTgId(Number(row.original.tg_id))}
        >
          {text(row.original.display_name || row.original.username || row.original.tg_id)}
          <span className="block text-[11px] font-normal text-[color:var(--atlas-text-muted)]">tg {row.original.tg_id}</span>
        </button>
      )
    },
    { header: "Доступ", cell: ({ row }) => <Badge tone={toneForState(row.original.status)}>{stateLabel(row.original.status)}</Badge> },
    { header: "Тип", cell: ({ row }) => <Badge tone={toneForState(row.original.sub_type)}>{text(row.original.sub_type)}</Badge> },
    { header: "Истекает", cell: ({ row }) => shortDateTime(row.original.expiry_at) },
    { header: "Observer", cell: ({ row }) => <Badge tone={toneForState(row.original.observer_state || "ok")}>{stateLabel(row.original.observer_state || "ok")}</Badge> },
    { header: "Install", cell: ({ row }) => text(row.original.app_install_id) }
  ], []);

  const onlineColumns: ColumnDef<OnlineUsersPayload["rows"][number]>[] = useMemo(() => [
    {
      header: "Кто",
      cell: ({ row }) => (
        <button
          className="text-left font-semibold hover:underline disabled:no-underline disabled:opacity-60"
          disabled={!row.original.tg_id}
          onClick={() => row.original.tg_id ? setSelectedTgId(Number(row.original.tg_id)) : undefined}
        >
          {text(row.original.display_name || row.original.username || row.original.panel_email || row.original.identity)}
          <span className="block text-[11px] font-normal text-[color:var(--atlas-text-muted)]">{row.original.tg_id ? `tg ${row.original.tg_id}` : "не сопоставлен"}</span>
        </button>
      )
    },
    { header: "Доступ", cell: ({ row }) => <Badge tone={toneForState(row.original.status)}>{stateLabel(row.original.status)}</Badge> },
    { header: "Ноды", cell: ({ row }) => listText(row.original.nodes_online) },
    { header: "Ключи", cell: ({ row }) => formatInt(row.original.online_keys_now) },
    { header: "Соед.", cell: ({ row }) => formatInt(row.original.online_connections_now) },
    { header: "IP count", cell: ({ row }) => <Badge tone={numberValue(row.original.ip_count) > 1 ? "warning" : "neutral"}>{formatInt(row.original.ip_count)}</Badge> },
    { header: "Риск", cell: ({ row }) => listText(row.original.risk_flags) },
    { header: "Последний", cell: ({ row }) => shortDateTime(row.original.last_online_at) }
  ], []);

  const nodeColumns: ColumnDef<NodeHealthRow>[] = useMemo(() => [
    {
      header: "Нода",
      cell: ({ row }) => (
        <button className="text-left font-semibold hover:underline" onClick={() => setSelectedNodeCode(row.original.code)}>
          {row.original.code}
          <span className="block text-[11px] font-normal text-[color:var(--atlas-text-muted)]">{text(row.original.name)}</span>
        </button>
      )
    },
    { header: "Health", cell: ({ row }) => <Badge tone={nodeRiskTone(row.original)}>{stateLabel(row.original.capacity_state || (row.original.is_healthy ? "ok" : "critical"))}</Badge> },
    { header: "Panel", cell: ({ row }) => `${compactValue(row.original.panel_latency_ms)} ms / err ${compactValue(row.original.panel_error_rate)}` },
    { header: "Dataplane", cell: ({ row }) => <Badge tone={row.original.dataplane_ok === false ? "danger" : row.original.dataplane_ok === true ? "success" : "neutral"}>{boolText(row.original.dataplane_ok)} · {compactValue(row.original.dataplane_rtt_ms)} ms</Badge> },
    { header: "Fresh", cell: ({ row }) => <Badge tone={toneForState(row.original.freshness_status)}>{stateLabel(row.original.freshness_status)}</Badge> },
    { header: "Online", cell: ({ row }) => `${formatInt(row.original.online_keys_now)} ключ / ${formatInt(row.original.online_connections_now)} соед.` },
    { header: "IPv4/IPv6", cell: ({ row }) => `${text(row.original.ipv4_health)} / ${text(row.original.ipv6_health)}` },
    { header: "Cap", cell: ({ row }) => `${compactValue(row.original.capacity_score)} · ${text(row.original.capacity_reject_reason, "")}` }
  ], []);

  const orderColumns: ColumnDef<AnyRow>[] = useMemo(() => [
    { header: "Заказ", cell: ({ row }) => text(row.original.order_id || row.original.id) },
    { header: "tg", cell: ({ row }) => text(row.original.tg_id) },
    { header: "Провайдер", cell: ({ row }) => text(row.original.provider) },
    { header: "Статус", cell: ({ row }) => <Badge tone={toneForState(row.original.status)}>{stateLabel(row.original.status)}</Badge> },
    { header: "Сумма", cell: ({ row }) => formatMoney(row.original.amount, row.original.currency) },
    { header: "План", cell: ({ row }) => text(row.original.plan_code) },
    { header: "Создан", cell: ({ row }) => shortDateTime(text(row.original.created_at, "")) }
  ], []);

  const ticketColumns: ColumnDef<AnyRow>[] = useMemo(() => [
    { header: "ID", cell: ({ row }) => text(row.original.id) },
    { header: "Пользователь", cell: ({ row }) => text(row.original.user_tg_id || row.original.tg_id) },
    { header: "Статус", cell: ({ row }) => <Badge tone={toneForState(row.original.status)}>{stateLabel(row.original.status)}</Badge> },
    { header: "Тема", cell: ({ row }) => text(row.original.subject || row.original.title || row.original.last_message) },
    { header: "Обновлен", cell: ({ row }) => shortDateTime(text(row.original.updated_at || row.original.created_at, "")) }
  ], []);

  const releaseColumns: ColumnDef<AnyRow>[] = useMemo(() => [
    { header: "Версия/пост", cell: ({ row }) => <div><div className="font-semibold">{text(row.original.title || row.original.version || row.original.id)}</div><div className="text-[color:var(--atlas-text-soft)]">{text(row.original.summary || row.original.channel_username || row.original.link, "")}</div></div> },
    { header: "Активно", cell: ({ row }) => <Badge tone={row.original.is_active ? "success" : "neutral"}>{boolText(row.original.is_active)}</Badge> },
    { header: "Опубликовано", cell: ({ row }) => shortDateTime(text(row.original.published_at || row.original.created_at, "")) },
    { header: "Sort", cell: ({ row }) => compactValue(row.original.sort_order) }
  ], []);

  const genericColumns: ColumnDef<AnyRow>[] = useMemo(() => [
    { header: "ID", cell: ({ row }) => text(row.original.id || row.original.code || row.original.key || row.original.order_id) },
    { header: "Статус", cell: ({ row }) => <Badge tone={toneForState(row.original.status || row.original.state || row.original.is_active)}>{stateLabel(row.original.status || row.original.state || (row.original.is_active ? "active" : ""))}</Badge> },
    { header: "Название", cell: ({ row }) => text(row.original.title || row.original.name || row.original.code || row.original.target_value || row.original.email) },
    { header: "Детали", cell: ({ row }) => text(row.original.summary || row.original.type || row.original.promo_type || row.original.segment || row.original.reason) },
    { header: "Дата", cell: ({ row }) => shortDateTime(text(row.original.updated_at || row.original.created_at || row.original.created, "")) }
  ], []);

  const freeColumns: ColumnDef<FreeTierUser>[] = useMemo(() => [
    { header: "Пользователь", cell: ({ row }) => `${text(row.original.display_name || row.original.username || row.original.tg_id)} · tg ${row.original.tg_id}` },
    { header: "Состояние", cell: ({ row }) => <Badge tone={toneForState(row.original.state)}>{stateLabel(row.original.state)}</Badge> },
    { header: "Использовано", cell: ({ row }) => formatGb(row.original.used_gb) },
    { header: "Осталось", cell: ({ row }) => formatGb(row.original.remaining_gb) },
    { header: "Лимит", cell: ({ row }) => <div className="min-w-28"><div className="mb-1">{formatPct(row.original.used_pct)}</div><Progress value={row.original.used_pct} tone={toneForState(row.original.state)} /></div> },
    { header: "Reset", cell: ({ row }) => shortDateTime(row.original.cycle_end) }
  ], []);

  const providerColumns: ColumnDef<ProviderQuotaStatus>[] = useMemo(() => [
    {
      header: "Нода",
      cell: ({ row }) => (
        <button
          className="text-left font-semibold hover:underline"
          onClick={() =>
            setQuotaForm({
              node_code: row.original.node_code,
              included_gb: String(row.original.included_gb || 0),
              reset_day: String(row.original.reset_day || 1),
              timezone: row.original.timezone || "UTC",
              warning_ratio: String(row.original.warning_ratio || 0.8),
              critical_ratio: String(row.original.critical_ratio || 0.95),
              enabled: row.original.enabled,
              notes: ""
            })
          }
        >
          {row.original.node_code}
          <span className="block text-[11px] font-normal text-[color:var(--atlas-text-muted)]">{row.original.node_name || row.original.source}</span>
        </button>
      )
    },
    { header: "Состояние", cell: ({ row }) => <Badge tone={toneForState(row.original.state)}>{stateLabel(row.original.state)}</Badge> },
    { header: "Использовано", cell: ({ row }) => `${formatGb(row.original.used_gb)} / ${formatGb(row.original.included_gb)}` },
    { header: "Осталось", cell: ({ row }) => formatGb(row.original.remaining_gb) },
    { header: "Прогресс", cell: ({ row }) => <div className="min-w-28"><div className="mb-1">{formatPct(row.original.used_pct)}</div><Progress value={row.original.used_pct} tone={toneForState(row.original.state)} /></div> },
    { header: "Reset", cell: ({ row }) => shortDateTime(row.original.cycle_end) }
  ], []);

  const trafficColumns: ColumnDef<TrafficSummaryRow>[] = useMemo(() => [
    { header: "Дата", cell: ({ row }) => row.original.date },
    { header: "Нода", cell: ({ row }) => row.original.node_code },
    { header: "Pool", cell: ({ row }) => row.original.pool_code },
    { header: "Трафик", cell: ({ row }) => formatGb(row.original.traffic_gb) },
    { header: "Samples", cell: ({ row }) => formatInt(row.original.samples) }
  ], []);

  if (!authReady && !loading) {
    return <AuthGate onReady={() => void load()} />;
  }

  const renderTopBar = (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
        <Badge tone={error ? "warning" : "success"}>{error ? "частично" : "данные свежие"}</Badge>
        <span>обновлено: {lastLoadedAt ? shortDateTime(lastLoadedAt) : "n/a"}</span>
        {onlinePayload?.generated_at ? <span>online: {shortDateTime(onlinePayload.generated_at)}</span> : null}
      </div>
      <Button tone="secondary" onClick={() => void load()} disabled={loading}>
        {loading ? <Loader2 className="animate-spin" size={15} /> : <RefreshCw size={15} />} Обновить
      </Button>
    </div>
  );

  const renderActionFeed = (
    <Card>
      <SectionTitle title="Требует действий" description="Сначала самое срочное: ноды, оплаты, лимиты, подозрительные ключи и свежие тикеты." />
      {actionItems.length ? (
        <div className="divide-y divide-[color:var(--atlas-border)]">
          {actionItems.map((item, index) => (
            <div key={`${item.kind}-${index}`} className="grid gap-2 py-3 md:grid-cols-[120px_1fr_auto] md:items-center">
              <Badge tone={item.tone}>{item.kind}</Badge>
              <div className="min-w-0">
                <div className="truncate text-sm font-semibold">{item.title}</div>
                <div className="truncate text-xs text-[color:var(--atlas-text-soft)]">{item.detail}</div>
              </div>
              <span className="text-xs text-[color:var(--atlas-text-muted)]">{item.action}</span>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState text="Срочных действий нет." />
      )}
    </Card>
  );

  const renderSummaryTiles = (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      <MetricTile label="Выручка сегодня" value={formatMoney(paymentsToday?.revenue.amount || 0, paymentsToday?.revenue.currency || "RUB")} detail={`${formatInt(paymentsToday?.revenue.paid_count)} оплат · проблем ${formatInt(paymentsToday?.attention.problem_count)}`} tone={paymentsToday?.attention.problem_count ? "warning" : "success"} />
      <MetricTile label="Выручка 7 дней" value={formatMoney(payments7d?.revenue.amount || 0, payments7d?.revenue.currency || "RUB")} detail={`${formatInt(payments7d?.revenue.paid_count)} оплат · checkout не оплатили ${formatInt(payments7d?.abandoned.checkout_not_paid as number)}`} tone="info" />
      <MetricTile label="Онлайн сейчас" value={formatInt(onlinePayload?.summary?.online_connections_now as number)} detail={`${formatInt(onlinePayload?.summary?.known_users_online as number)} пользователей · ${formatInt(onlinePayload?.summary?.online_keys_now as number)} ключей`} tone="success" />
      <MetricTile label="Здоровье нод" value={`${formatInt(nodes.length - problemNodes.length)} / ${formatInt(nodes.length)}`} detail={`проблем: ${formatInt(problemNodes.length)} · panel errors: ${formatInt(onlinePayload?.summary?.nodes_with_panel_errors as number)}`} tone={problemNodes.length ? "warning" : "success"} />
    </div>
  );

  const renderDashboard = (
    <div className="space-y-3">
      {renderActionFeed}
      {renderSummaryTiles}
      <div className="grid gap-3 xl:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <SectionTitle title="Воронка" description="site entry, buy click, checkout start, paid, connected без сырого JSON." />
          <div className="space-y-3">
            {asRows(funnelPayload.stages).map((row) => (
              <div key={text(row.key)} className="grid gap-2 md:grid-cols-[190px_1fr_80px] md:items-center">
                <div className="text-sm font-semibold">{text(row.label)}</div>
                <Progress value={numberValue(row.conversion_pct)} tone={numberValue(row.conversion_pct) < 35 ? "warning" : "success"} />
                <div className="text-right text-xs text-[color:var(--atlas-text-soft)]">{formatPct(numberValue(row.conversion_pct))}</div>
              </div>
            ))}
            {!asRows(funnelPayload.stages).length ? <EmptyState text="Нет funnel событий." /> : null}
          </div>
        </Card>
        <Card>
          <SectionTitle title="Трафик" description="Premium / free по дням." />
          <div className="h-[230px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trafficChart}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--atlas-border)" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="premium" stackId="a" fill="var(--atlas-primary)" />
                <Bar dataKey="free" stackId="a" fill="var(--atlas-status-info-text)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );

  const renderUsers = (
    <div className="grid gap-3 xl:grid-cols-[minmax(520px,0.95fr)_minmax(520px,1.05fr)]">
      <div className="space-y-3">
        <Card>
          <SectionTitle title="Поиск пользователей" description="TG ID, username, имя, install ID, order ID, нода, ключ/email." />
          <form
            className="grid gap-2 md:grid-cols-[1fr_170px_auto]"
            onSubmit={(event: FormEvent) => {
              event.preventDefault();
              const q = userSearch.trim();
              setSelectedTgId(/^-?\d+$/.test(q) ? Number(q) : null);
              void load();
            }}
          >
            <label className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[color:var(--atlas-text-muted)]" size={15} />
              <input
                value={userSearch}
                onChange={(event) => setUserSearch(event.target.value)}
                placeholder="tg_id, username, install_id, order_id, key/email"
                className="h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] pl-9 pr-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]"
              />
            </label>
            <select
              value={userStatus}
              onChange={(event) => setUserStatus(event.target.value)}
              className="h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]"
            >
              <option value="">любой статус</option>
              <option value="active">active</option>
              <option value="expired">expired</option>
              <option value="blocked">blocked</option>
              <option value="paid">paid</option>
              <option value="free">free</option>
            </select>
            <Button tone="primary" type="submit"><Search size={15} /> Найти</Button>
          </form>
        </Card>
        <Card>
          <SectionTitle title="Пользователи" description={`${formatInt(usersPayload?.total || 0)} найдено`} />
          <DataTable data={usersPayload?.users || []} columns={userColumns} empty="Пользователи не найдены" />
        </Card>
      </div>
      <UserCard card={userCard} loading={userCardLoading} error={userCardError} />
    </div>
  );

  const runNodeAction = async (dryRun = false) => {
    if (!pendingNodeAction || !selectedNode) return;
    if (pendingNodeAction.confirm.trim().toLowerCase() !== pendingNodeAction.code.toLowerCase()) {
      setNodeActionError("Введи node_code точно, например " + pendingNodeAction.code);
      return;
    }
    setNodeActionBusy(true);
    setNodeActionError("");
    setNodeActionResult("");
    try {
      const output =
        pendingNodeAction.action === "resync"
          ? await nodeResync(pendingNodeAction.code, { limit: Number(pendingNodeAction.limit || 100), dry_run: dryRun })
          : await nodeLifecycleAction(pendingNodeAction.code, pendingNodeAction.action, { force: pendingNodeAction.force });
      setNodeActionResult(`${pendingNodeAction.action}: ok ${compactValue(output.ok)} · dry_run ${compactValue(output.dry_run)}`);
      if (!dryRun) {
        setPendingNodeAction(null);
        await load();
      }
    } catch (err) {
      setNodeActionError(errorMessage(err, "Node action failed"));
    } finally {
      setNodeActionBusy(false);
    }
  };

  const renderNodeDetail = selectedNode ? (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <SectionTitle title={`Нода ${selectedNode.code}`} description={text(selectedNode.name)} />
        <div className="flex flex-wrap gap-2">
          <Badge tone={nodeRiskTone(selectedNode)}>{stateLabel(selectedNode.capacity_state || (selectedNode.is_healthy ? "ok" : "critical"))}</Badge>
          <Badge tone={selectedNode.enabled ? "success" : "danger"}>{selectedNode.enabled ? "enabled" : "disabled"}</Badge>
          <Badge tone={selectedNode.is_draining ? "warning" : "success"}>{selectedNode.is_draining ? "drain" : "accept"}</Badge>
        </div>
      </div>
      <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-4">
        <Field label="panel latency" value={`${compactValue(selectedNode.panel_latency_ms)} ms`} />
        <Field label="dataplane" value={`${boolText(selectedNode.dataplane_ok)} · ${compactValue(selectedNode.dataplane_rtt_ms)} ms`} tone={selectedNode.dataplane_ok === false ? "danger" : selectedNode.dataplane_ok === true ? "success" : "neutral"} />
        <Field label="freshness" value={`${stateLabel(selectedNode.freshness_status)} · ${compactValue(selectedNode.freshness_age_seconds)} сек`} tone={toneForState(selectedNode.freshness_status)} />
        <Field label="capacity" value={`${stateLabel(selectedNode.capacity_state)} · ${compactValue(selectedNode.capacity_score)}`} tone={toneForState(selectedNode.capacity_state)} />
        <Field label="observer" value={selectedNode.observer_is_stale ? "stale" : "ok"} tone={selectedNode.observer_is_stale ? "warning" : "success"} />
        <Field label="IPv4 / IPv6" value={`${text(selectedNode.ipv4_health)} / ${text(selectedNode.ipv6_health)}`} />
        <Field label="online" value={`${formatInt(selectedNode.online_keys_now)} ключ / ${formatInt(selectedNode.online_connections_now)} соед.`} />
        <Field label="mapped users" value={selectedNode.mapped_users ?? 0} />
      </div>
      <div className="mt-4 grid gap-2 sm:grid-cols-5">
        {(["drain", "enable", "undrain", "disable", "resync"] as const).map((action) => (
          <Button
            key={action}
            tone={action === "disable" ? "danger" : "secondary"}
            onClick={() => {
              setPendingNodeAction({ action, code: selectedNode.code, confirm: "", force: false, limit: "100" });
              setNodeActionError("");
              setNodeActionResult("");
            }}
          >
            {action === "enable" || action === "undrain" ? <Power size={15} /> : action === "disable" ? <PowerOff size={15} /> : action === "resync" ? <RotateCw size={15} /> : <ShieldAlert size={15} />}
            {action}
          </Button>
        ))}
      </div>
      {pendingNodeAction ? (
        <div className="mt-4 rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
          <div className="mb-3 text-sm font-semibold">Подтверждение: {pendingNodeAction.action} для {pendingNodeAction.code}</div>
          <div className="grid gap-2 md:grid-cols-[1fr_120px_auto_auto] md:items-end">
            <label className="text-xs font-semibold text-[color:var(--atlas-text-soft)]">
              введи node_code
              <input
                value={pendingNodeAction.confirm}
                onChange={(event) => setPendingNodeAction({ ...pendingNodeAction, confirm: event.target.value })}
                className="mt-1 h-9 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] px-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]"
              />
            </label>
            {pendingNodeAction.action === "resync" ? (
              <label className="text-xs font-semibold text-[color:var(--atlas-text-soft)]">
                limit
                <input
                  value={pendingNodeAction.limit}
                  onChange={(event) => setPendingNodeAction({ ...pendingNodeAction, limit: event.target.value })}
                  className="mt-1 h-9 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] px-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]"
                />
              </label>
            ) : (
              <label className="flex h-9 items-center gap-2 text-sm text-[color:var(--atlas-text-soft)]">
                <input type="checkbox" checked={pendingNodeAction.force} onChange={(event) => setPendingNodeAction({ ...pendingNodeAction, force: event.target.checked })} />
                force
              </label>
            )}
            {pendingNodeAction.action === "resync" ? <Button disabled={nodeActionBusy} onClick={() => void runNodeAction(true)}><Eye size={15} /> Dry-run</Button> : null}
            <Button tone={pendingNodeAction.action === "disable" ? "danger" : "primary"} disabled={nodeActionBusy} onClick={() => void runNodeAction(false)}>
              {nodeActionBusy ? <Loader2 className="animate-spin" size={15} /> : <Check size={15} />} Выполнить
            </Button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {nodeActionError ? <Badge tone="danger">{nodeActionError}</Badge> : null}
            {nodeActionResult ? <Badge tone="success">{nodeActionResult}</Badge> : null}
          </div>
        </div>
      ) : null}
    </Card>
  ) : null;

  const renderNodes = (
    <div className="space-y-3">
      <div className="grid gap-3 xl:grid-cols-[1fr_360px]">
        <Card>
          <SectionTitle title="Health-first ноды" description="Panel, dataplane, probe, TLS/transport, freshness, observer, IPv4/IPv6 и capacity в одном списке." />
          <DataTable data={nodes} columns={nodeColumns} empty="Ноды не загружены" />
        </Card>
        <Card>
          <SectionTitle title="Live runtime" description="Read-only snapshot из панели, Postgres truth не перетирает." />
          <div className="space-y-2 text-sm">
            <Field label="runtime updated" value={shortDateTime(text(runtimePayload.updated_at, ""))} />
            <Field label="nodes in snapshot" value={asRows(runtimePayload.nodes).length} />
            <Field label="panel errors" value={formatInt(onlinePayload?.summary?.nodes_with_panel_errors as number)} tone={numberValue(onlinePayload?.summary?.nodes_with_panel_errors) > 0 ? "warning" : "success"} />
          </div>
        </Card>
      </div>
      {renderNodeDetail}
      <Card>
        <SectionTitle title="Node trend" description="CPU, network и score по последним samples." />
        <div className="h-[260px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={nodeChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--atlas-border)" />
              <XAxis dataKey="t" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line type="monotone" dataKey="cpu" stroke="var(--atlas-status-warning-text)" dot={false} />
              <Line type="monotone" dataKey="net" stroke="var(--atlas-primary)" dot={false} />
              <Line type="monotone" dataKey="score" stroke="var(--atlas-status-success-text)" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );

  const renderOnline = (
    <div className="space-y-3">
      <div className="grid gap-3 md:grid-cols-4">
        <MetricTile label="Пользователей онлайн" value={formatInt(onlinePayload?.summary?.known_users_online as number)} detail={`unknown keys ${formatInt(onlinePayload?.summary?.unknown_online_keys as number)}`} tone="success" />
        <MetricTile label="Соединений сейчас" value={formatInt(onlinePayload?.summary?.online_connections_now as number)} detail={`${formatInt(onlinePayload?.summary?.online_keys_now as number)} online keys`} tone="info" />
        <MetricTile label="Риск ключей" value={formatInt(pressureProblemRows.length)} detail="manual_review/watch/suspicious" tone={pressureProblemRows.length ? "warning" : "success"} />
        <MetricTile label="Raw IP в списке" value={onlinePayload?.summary?.raw_ip_exposed ? "да" : "нет"} detail="IP только в карточке пользователя" tone={onlinePayload?.summary?.raw_ip_exposed ? "danger" : "success"} />
      </div>
      <Card>
        <SectionTitle title="Сейчас онлайн" description="Live panel state без raw IP в общем списке." />
        <DataTable data={onlineRows} columns={onlineColumns} empty="Сейчас никто не онлайн или panel недоступна" />
      </Card>
      <Card>
        <SectionTitle title="Подозрительные ключи" description="Pressure score, multi-IP, manual review." />
        <DataTable data={keyPressure} columns={genericColumns} empty="Key pressure пустой" />
      </Card>
    </div>
  );

  const paymentSummaryTiles = (
    <div className="grid gap-3 md:grid-cols-3">
      {[
        ["Сегодня", paymentsToday],
        ["7 дней", payments7d],
        ["30 дней", payments30d]
      ].map(([label, payload]) => {
        const item = payload as PaymentsSummaryPayload | null;
        return (
          <MetricTile
            key={String(label)}
            label={String(label)}
            value={formatMoney(item?.revenue.amount || 0, item?.revenue.currency || "RUB")}
            detail={`${formatInt(item?.revenue.paid_count || 0)} paid · pending ${formatInt(item?.attention.pending_count || 0)} · manual ${formatInt(item?.attention.manual_review_count || 0)}`}
            tone={item?.attention.problem_count ? "warning" : "success"}
          />
        );
      })}
    </div>
  );

  const renderPayments = (
    <div className="space-y-3">
      {paymentSummaryTiles}
      <div className="grid gap-3 xl:grid-cols-[360px_1fr]">
        <Card>
          <SectionTitle title="Кликнул, но не оплатил" description="Диагностика воронки, не бухгалтерская правда." />
          <div className="space-y-2">
            <Field label="buy click" value={payments7d?.abandoned.buy_clicks ?? 0} />
            <Field label="checkout start" value={payments7d?.abandoned.checkout_started ?? 0} />
            <Field label="buy click not paid" value={payments7d?.abandoned.buy_click_not_paid ?? 0} tone={numberValue(payments7d?.abandoned.buy_click_not_paid) > 0 ? "warning" : "success"} />
            <Field label="checkout not paid" value={payments7d?.abandoned.checkout_not_paid ?? 0} tone={numberValue(payments7d?.abandoned.checkout_not_paid) > 0 ? "warning" : "success"} />
          </div>
        </Card>
        <Card>
          <SectionTitle title="Проблемные оплаты" description="Pending, manual review и failed сверху." />
          <DataTable data={problemOrders} columns={orderColumns} empty="Проблемных оплат нет" />
        </Card>
      </div>
      <Card>
        <SectionTitle title="Заказы" />
        <DataTable data={paymentOrders} columns={orderColumns} empty="Заказов нет" />
      </Card>
    </div>
  );

  const renderFunnel = (
    <div className="space-y-3">
      <div className="grid gap-3 md:grid-cols-5">
        {Object.entries(asRecord(funnelPayload.totals)).map(([key, value]) => (
          <MetricTile key={key} label={key} value={formatInt(numberValue(value))} tone={key === "paid" || key === "connected" ? "success" : "info"} />
        ))}
      </div>
      <Card>
        <SectionTitle title="Stages" description="site entry, app/bot open, checkout, paid, connected." />
        <DataTable data={asRows(funnelPayload.stages)} columns={[
          { header: "Stage", cell: ({ row }) => text(row.original.label) },
          { header: "Entered", cell: ({ row }) => formatInt(numberValue(row.original.entered)) },
          { header: "Next", cell: ({ row }) => formatInt(numberValue(row.original.reached_next)) },
          { header: "Drop", cell: ({ row }) => formatInt(numberValue(row.original.dropped)) },
          { header: "Conversion", cell: ({ row }) => <div className="min-w-32"><div className="mb-1">{formatPct(numberValue(row.original.conversion_pct))}</div><Progress value={numberValue(row.original.conversion_pct)} tone={numberValue(row.original.conversion_pct) < 35 ? "warning" : "success"} /></div> }
        ]} empty="Нет stages" />
      </Card>
      <div className="grid gap-3 xl:grid-cols-2">
        <Card>
          <SectionTitle title="Source breakdown" />
          <DataTable data={asRows(funnelPayload.by_source)} columns={[
            { header: "Source", cell: ({ row }) => text(row.original.source) },
            { header: "Visitors", cell: ({ row }) => formatInt(numberValue(row.original.visitors)) },
            { header: "App opens", cell: ({ row }) => formatInt(numberValue(row.original.app_opens)) },
            { header: "Checkout", cell: ({ row }) => formatInt(numberValue(row.original.checkouts)) },
            { header: "Paid", cell: ({ row }) => formatInt(numberValue(row.original.paid)) },
            { header: "Connected", cell: ({ row }) => formatInt(numberValue(row.original.connected)) }
          ]} empty="Нет source данных" />
        </Card>
        <Card>
          <SectionTitle title="Drop reasons" />
          <DataTable data={asRows(funnelPayload.drop_reasons)} columns={[
            { header: "Причина", cell: ({ row }) => text(row.original.reason) },
            { header: "Count", cell: ({ row }) => formatInt(numberValue(row.original.count)) }
          ]} empty="Нет drop reasons" />
        </Card>
      </div>
      <Card>
        <SectionTitle title="Recent events" />
        <DataTable data={asRows(funnelPayload.recent)} columns={[
          { header: "Время", cell: ({ row }) => shortDateTime(text(row.original.created_at, "")) },
          { header: "Kind", cell: ({ row }) => text(row.original.kind) },
          { header: "Stage/event", cell: ({ row }) => text(row.original.stage || row.original.event_name) },
          { header: "Source", cell: ({ row }) => text(row.original.source) },
          { header: "tg/session", cell: ({ row }) => text(row.original.tg_id || row.original.session_id) }
        ]} empty="Нет recent событий" />
      </Card>
    </div>
  );

  const renderProviderCaps = (
    <div className="grid gap-3 xl:grid-cols-[1fr_360px]">
      <Card>
        <SectionTitle title="Лимиты провайдеров" description="Hoster/provider caps по нодам, reset window и остаток." />
        <DataTable data={providerStatus} columns={providerColumns} empty="Нет нод или квот" />
      </Card>
      <Card>
        <SectionTitle title="Quota config" description="Ручная конфигурация лимита по node_code." />
        {quotaForm ? (
          <form
            className="space-y-3"
            onSubmit={async (event) => {
              event.preventDefault();
              const warningRatio = Number(quotaForm.warning_ratio || 0.8);
              const criticalRatio = Number(quotaForm.critical_ratio || 0.95);
              if (warningRatio >= criticalRatio) {
                setQuotaError("warning_ratio должен быть меньше critical_ratio");
                return;
              }
              setSavingQuota(true);
              setQuotaError("");
              try {
                const configured = configuredByNode.has(quotaForm.node_code.toLowerCase());
                await saveProviderQuota(
                  quotaForm.node_code,
                  {
                    included_gb: Number(quotaForm.included_gb || 0),
                    reset_day: Number(quotaForm.reset_day || 1),
                    timezone: quotaForm.timezone || "UTC",
                    warning_ratio: warningRatio,
                    critical_ratio: criticalRatio,
                    enabled: quotaForm.enabled,
                    notes: quotaForm.notes
                  },
                  configured
                );
                await load();
              } catch (err) {
                setQuotaError(errorMessage(err, "Provider quota save failed"));
              } finally {
                setSavingQuota(false);
              }
            }}
          >
            {quotaError ? <Badge tone="danger">{quotaError}</Badge> : null}
            {(["node_code", "included_gb", "reset_day", "timezone", "warning_ratio", "critical_ratio"] as const).map((key) => (
              <label key={key} className="block text-xs font-semibold text-[color:var(--atlas-text-soft)]">
                {key}
                <input
                  value={String(quotaForm[key])}
                  onChange={(event) => setQuotaForm({ ...quotaForm, [key]: event.target.value })}
                  className="mt-1 h-9 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]"
                />
              </label>
            ))}
            <label className="flex items-center gap-2 text-sm text-[color:var(--atlas-text-soft)]">
              <input type="checkbox" checked={quotaForm.enabled} onChange={(event) => setQuotaForm({ ...quotaForm, enabled: event.target.checked })} />
              enabled
            </label>
            <label className="block text-xs font-semibold text-[color:var(--atlas-text-soft)]">
              notes
              <textarea
                value={quotaForm.notes}
                onChange={(event) => setQuotaForm({ ...quotaForm, notes: event.target.value })}
                className="mt-1 min-h-20 w-full rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 py-2 text-sm outline-none focus:border-[color:var(--atlas-focus)]"
              />
            </label>
            <div className="flex gap-2">
              <Button tone="primary" type="submit" disabled={savingQuota}>
                {savingQuota ? <Loader2 className="animate-spin" size={15} /> : <Save size={15} />} Сохранить
              </Button>
              <Button
                tone="danger"
                type="button"
                disabled={savingQuota || deletingQuota}
                onClick={async () => {
                  setDeletingQuota(true);
                  setQuotaError("");
                  try {
                    await deleteProviderQuota(quotaForm.node_code);
                    setQuotaForm(null);
                    await load();
                  } catch (err) {
                    setQuotaError(errorMessage(err, "Provider quota delete failed"));
                  } finally {
                    setDeletingQuota(false);
                  }
                }}
              >
                {deletingQuota ? <Loader2 className="animate-spin" size={15} /> : <Trash2 size={15} />} Удалить
              </Button>
            </div>
          </form>
        ) : (
          <EmptyState text="Выбери ноду в таблице." />
        )}
      </Card>
    </div>
  );

  const renderFreeTier = (
    <div className="grid gap-3 xl:grid-cols-[320px_1fr]">
      <Card>
        <SectionTitle title="Free tier" description="Dedicated NL-free, лимит и soft-mode." />
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <Field label="Free users" value={formatInt(overview?.free_tier.free_users)} tone="info" />
            <Field label="Sampled" value={formatInt(overview?.free_tier.sampled_users)} tone="neutral" />
          </div>
          <div>
            <div className="mb-2 flex justify-between text-xs text-[color:var(--atlas-text-soft)]">
              <span>{formatGb(overview?.free_tier.used_gb)}</span>
              <span>{formatPct(overview?.free_tier.used_pct)}</span>
            </div>
            <Progress value={overview?.free_tier.used_pct || 0} tone={overview?.free_tier.over_cap_users ? "danger" : overview?.free_tier.near_cap_users ? "warning" : "success"} />
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <Badge tone="warning">{formatInt(overview?.free_tier.near_cap_users)} near</Badge>
            <Badge tone="danger">{formatInt(overview?.free_tier.over_cap_users)} over</Badge>
          </div>
        </div>
      </Card>
      <Card>
        <SectionTitle title="Free users" description="Расход, остаток и reset window по бесплатным пользователям." />
        <DataTable data={freeUsers} columns={freeColumns} empty="Нет free пользователей" />
      </Card>
    </div>
  );

  const renderBroadcast = (
    <Card className="max-w-4xl">
      <SectionTitle title="Рассылка" description="Preview/dry-run обязателен перед отправкой. Для реальной отправки введи SEND." />
      <div className="grid gap-3 md:grid-cols-[1fr_160px_120px]">
        <label className="text-xs font-semibold text-[color:var(--atlas-text-soft)]">
          segment
          <select
            value={broadcastSegment}
            onChange={(event) => setBroadcastSegment(event.target.value)}
            className="mt-1 h-9 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]"
          >
            <option value="all_active">all_active</option>
            <option value="paid">paid</option>
            <option value="free">free</option>
            <option value="expired">expired</option>
            <option value="custom">custom tg_ids</option>
          </select>
        </label>
        <label className="text-xs font-semibold text-[color:var(--atlas-text-soft)]">
          limit
          <input
            value={broadcastLimit}
            onChange={(event) => setBroadcastLimit(event.target.value)}
            className="mt-1 h-9 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]"
          />
        </label>
        <label className="text-xs font-semibold text-[color:var(--atlas-text-soft)]">
          confirm
          <input
            value={broadcastConfirm}
            onChange={(event) => setBroadcastConfirm(event.target.value)}
            placeholder="SEND"
            className="mt-1 h-9 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]"
          />
        </label>
      </div>
      {broadcastSegment === "custom" ? (
        <label className="mt-3 block text-xs font-semibold text-[color:var(--atlas-text-soft)]">
          tg_ids через запятую
          <input
            value={broadcastTgIds}
            onChange={(event) => setBroadcastTgIds(event.target.value)}
            className="mt-1 h-9 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]"
          />
        </label>
      ) : null}
      <textarea
        value={broadcastText}
        onChange={(event) => setBroadcastText(event.target.value)}
        className="mt-3 min-h-36 w-full rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]"
        placeholder="Текст рассылки"
      />
      <div className="mt-3 rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 text-sm">
        <div className="mb-2 text-xs font-semibold uppercase tracking-[0.08em] text-[color:var(--atlas-text-muted)]">Preview</div>
        <div className="whitespace-pre-wrap leading-6">{broadcastText || "Текст появится здесь."}</div>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Button
          tone="secondary"
          disabled={!broadcastText.trim() || broadcastSending}
          onClick={async () => {
            setBroadcastSending(true);
            setBroadcastError("");
            setBroadcastPreview(null);
            setBroadcastResult(null);
            try {
              const tgIds = broadcastSegment === "custom" ? broadcastTgIds.split(/[,\s]+/).map((x) => Number(x)).filter((x) => Number.isFinite(x)) : undefined;
              const result = await sendBroadcast({ text: broadcastText, segment: broadcastSegment, limit: Number(broadcastLimit || 100), tg_ids: tgIds, dry_run: true });
              setBroadcastPreview(result);
            } catch (err) {
              setBroadcastError(errorMessage(err, "Broadcast preview failed"));
            } finally {
              setBroadcastSending(false);
            }
          }}
        >
          {broadcastSending ? <Loader2 className="animate-spin" size={15} /> : <Eye size={15} />} Dry-run
        </Button>
        <Button
          tone="primary"
          disabled={!broadcastText.trim() || broadcastConfirm !== "SEND" || !broadcastPreview || broadcastSending}
          onClick={async () => {
            setBroadcastSending(true);
            setBroadcastError("");
            setBroadcastResult(null);
            try {
              const tgIds = broadcastSegment === "custom" ? broadcastTgIds.split(/[,\s]+/).map((x) => Number(x)).filter((x) => Number.isFinite(x)) : undefined;
              const result = await sendBroadcast({ text: broadcastText, segment: broadcastSegment, limit: Number(broadcastLimit || 100), tg_ids: tgIds, dry_run: false });
              setBroadcastResult(result);
            } catch (err) {
              setBroadcastError(errorMessage(err, "Broadcast send failed"));
            } finally {
              setBroadcastSending(false);
            }
          }}
        >
          {broadcastSending ? <Loader2 className="animate-spin" size={15} /> : <Send size={15} />} Отправить
        </Button>
        {broadcastError ? <Badge tone="danger">{broadcastError}</Badge> : null}
        {broadcastPreview ? <Badge tone="info">dry-run: {formatInt(numberValue(broadcastPreview.attempted))} получателей</Badge> : null}
        {broadcastResult ? <Badge tone="success">sent {formatInt(numberValue(broadcastResult.sent))} / failed {formatInt(numberValue(broadcastResult.failed))}</Badge> : null}
      </div>
    </Card>
  );

  const renderRelease = (
    <div className="space-y-3">
      <div className="grid gap-3 md:grid-cols-4">
        <MetricTile label="Live updates" value={formatInt(releaseRows.length)} detail="backend-owned JSON surface" tone="info" />
        <MetricTile label="APK/EXE delivery" value="GitHub Releases" detail="не first-party download domain" tone="success" />
        <MetricTile label="Update model" value="prompt" detail="проверка на launch/resume" tone="info" />
        <MetricTile label="Manual gates" value="отдельно" detail="install/connect/signing/store/RU" tone="warning" />
      </div>
      <Card>
        <SectionTitle title="Release readiness" description="Версии, публичные посты и ручные gates без unsupported stable/store claims." />
        <DataTable data={releaseRows} columns={releaseColumns} empty="Live updates не найдены" />
      </Card>
      <Card>
        <SectionTitle title="Manual gates" />
        <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-4">
          <Field label="Android owner install/connect" value="MANUAL_OWNER_TEST" tone="warning" />
          <Field label="Windows trusted signing" value="separate gate" tone="warning" />
          <Field label="Store availability" value="not claimed" tone="success" />
          <Field label="RU-origin readiness" value="separate probe" tone="warning" />
        </div>
      </Card>
    </div>
  );

  return (
    <div className="space-y-4">
      {renderTopBar}
      {error ? <Badge tone="warning">{error}</Badge> : null}
      {loading && !overview ? (
        <Card>
          <div className="flex items-center gap-2 text-sm text-[color:var(--atlas-text-soft)]">
            <Loader2 className="animate-spin" size={16} /> Загружаю ops snapshot
          </div>
        </Card>
      ) : null}

      {section === "dashboard" ? renderDashboard : null}
      {section === "users" ? renderUsers : null}
      {section === "online" ? renderOnline : null}
      {section === "nodes" ? renderNodes : null}
      {section === "payments" ? renderPayments : null}
      {section === "funnel" ? renderFunnel : null}
      {section === "tickets" ? (
        <Card>
          <SectionTitle title="Тикеты" description="Очередь проблем: кто, статус, тема, когда обновлялось." />
          <DataTable data={ticketsRows} columns={ticketColumns} empty="Тикетов нет" />
        </Card>
      ) : null}
      {section === "alerts" ? (
        <Card>
          <SectionTitle title="Алерты" description="Спокойные алерты: без звука и мигания, с ack/silence." />
          <DataTable data={alerts} columns={alertColumns} empty="Нет активных алертов" />
        </Card>
      ) : null}
      {section === "traffic" ? (
        <div className="space-y-3">
          <Card>
            <SectionTitle title="Traffic breakdown" description="Pool / node / day breakdown from usage rollups." />
            <DataTable data={trafficRows} columns={trafficColumns} empty="Нет traffic rollups" />
          </Card>
        </div>
      ) : null}
      {section === "free-tier" ? renderFreeTier : null}
      {section === "provider-caps" ? renderProviderCaps : null}
      {moduleSections.has(section) ? (
        <div className="space-y-3">
          <ModuleActionPanel section={section} onDone={load} />
          <Card>
            <SectionTitle title={section === "promos" ? "Промо" : "Рефералы"} description="Нормальная таблица поверх существующего admin API, без сырого JSON." />
            <DataTable data={modulePayload?.rows || []} columns={genericColumns} empty="Нет строк" />
          </Card>
        </div>
      ) : null}
      {section === "release" ? renderRelease : null}
      {section === "broadcast" ? renderBroadcast : null}
    </div>
  );
}
