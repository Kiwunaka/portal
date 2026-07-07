"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import {
  AlertTriangle,
  BellOff,
  Check,
  Loader2,
  RefreshCw,
  Save,
  Trash2
} from "lucide-react";
import {
  Area,
  AreaChart,
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
  fetchAdminModule,
  fetchFreeUsers,
  fetchNodeTimeseries,
  fetchOpsOverview,
  fetchProviderQuotas,
  fetchTrafficSummary,
  hasAdminAuthMaterial,
  saveAdminInitData,
  saveAdminSessionToken,
  saveProviderQuota,
  sendBroadcast,
  silenceAlert,
  type AdminModulePayload,
  type FreeTierUser,
  type NodeTimeseriesRow,
  type OpsAlert,
  type OpsOverview,
  type ProviderQuotaConfig,
  type ProviderQuotaStatus,
  type TrafficSummaryRow
} from "@/lib/api";
import { formatGb, formatInt, formatPct, shortDateTime } from "@/lib/format";

type OpsDashboardSection =
  | "dashboard"
  | "nodes"
  | "traffic"
  | "free-tier"
  | "provider-caps"
  | "alerts"
  | "users"
  | "tickets"
  | "payments"
  | "promos"
  | "referrals"
  | "release"
  | "broadcast"
  | "funnel";

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

const moduleSections = new Set(["users", "tickets", "payments", "promos", "referrals", "release", "funnel"]);

function toneForState(value?: string | null): Tone {
  const v = String(value || "").toLowerCase();
  if (["critical", "danger", "over_cap", "hard_reject", "error", "failed"].includes(v)) return "danger";
  if (["warning", "near_cap", "stale", "degraded", "pending"].includes(v)) return "warning";
  if (["ok", "healthy", "active", "paid", "success"].includes(v)) return "success";
  if (["silenced", "info"].includes(v)) return "info";
  return "neutral";
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
        <Badge tone={tone}>{tone}</Badge>
      </div>
    </Card>
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
        if (!options?.silent) setError(errorMessage(err, "Admin session exchange failed"));
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
        <SectionTitle title="Admin auth" description="Сначала пробуем текущую web session из кабинета. Если браузер ее не прислал, вставь Telegram WebApp initData один раз." />
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
          <Button
            tone="secondary"
            disabled={busy || !value.trim()}
            onClick={() => void startSession(value)}
          >
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
            Clear
          </Button>
        </div>
        {error ? <div className="mt-3"><Badge tone="danger">{error}</Badge></div> : null}
      </Card>
    </div>
  );
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
    .slice(-160)
    .map((row) => ({
      t: shortDateTime(row.sampled_at),
      node: row.node_code,
      cpu: Number(row.cpu_percent || 0),
      net: Number(row.network_total_mbps || 0),
      score: Number(row.capacity_score || row.score || 0)
    }));
}

function compactValue(value: unknown): string {
  if (value == null) return "";
  if (typeof value === "boolean") return value ? "yes" : "no";
  if (typeof value === "number") return Number.isInteger(value) ? formatInt(value) : value.toFixed(2);
  if (typeof value === "object") return JSON.stringify(value).slice(0, 120);
  return String(value);
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

function ActionField({
  label,
  value,
  onChange,
  placeholder = "",
  multiline = false
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  multiline?: boolean;
}) {
  const className =
    "mt-1 w-full rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm text-[color:var(--atlas-text)] outline-none focus:border-[color:var(--atlas-focus)]";
  return (
    <label className="block text-xs font-semibold text-[color:var(--atlas-text-soft)]">
      {label}
      {multiline ? (
        <textarea value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} className={`${className} min-h-24 py-2`} />
      ) : (
        <input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} className={`${className} h-9`} />
      )}
    </label>
  );
}

function ModuleActionPanel({ section, onDone }: { section: OpsDashboardSection; onDone: () => Promise<void> }) {
  const [values, setValues] = useState<Record<string, string>>({
    tg_id: "",
    days: "30",
    text: "",
    ticket_id: "",
    status: "in_progress",
    provider: "lavatop",
    order_id: "",
    note: "Manual operator reconciliation",
    code: "",
    promo_type: "discount",
    value: "15",
    uses_left: "-1",
    title: "",
    summary: "",
    link: "",
    limit: "50"
  });
  const [busy, setBusy] = useState("");
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const setField = (key: string, value: string) => setValues((prev) => ({ ...prev, [key]: value }));
  const run = async (label: string, path: string, method: "POST" | "PATCH" | "DELETE", payload?: Record<string, unknown>) => {
    setBusy(label);
    setError("");
    setResult("");
    try {
      const output = await adminCommand(path, method, payload);
      setResult(JSON.stringify(output).slice(0, 500));
      await onDone();
    } catch (err) {
      setError(errorMessage(err, `${label} failed`));
    } finally {
      setBusy("");
    }
  };
  const tgId = Number(values.tg_id || 0);
  const ticketId = Number(values.ticket_id || 0);

  if (section === "users") {
    return (
      <Card>
        <SectionTitle title="User actions" description="Manual account, message, extension, block, token regeneration and safe test-user deletion." />
        <div className="grid gap-3 lg:grid-cols-4">
          <ActionField label="tg_id" value={values.tg_id} onChange={(v) => setField("tg_id", v)} />
          <ActionField label="days" value={values.days} onChange={(v) => setField("days", v)} />
          <ActionField label="message" value={values.text} onChange={(v) => setField("text", v)} placeholder="Operator DM" multiline />
          <div className="flex flex-wrap content-end gap-2">
            <Button disabled={!tgId || !values.text.trim() || Boolean(busy)} onClick={() => void run("message", `/api/admin/users/${tgId}/message`, "POST", { text: values.text })}>Message</Button>
            <Button disabled={!tgId || Boolean(busy)} onClick={() => void run("extend", `/api/admin/users/${tgId}/manual/extend`, "POST", { days: Number(values.days || 30) })}>Extend</Button>
            <Button tone="danger" disabled={!tgId || Boolean(busy)} onClick={() => void run("block", `/api/admin/users/${tgId}/manual/block`, "POST", { blocked: true })}>Block</Button>
            <Button disabled={!tgId || Boolean(busy)} onClick={() => void run("regen", `/api/admin/users/${tgId}/manual/regenerate-token`, "POST")}>Regenerate</Button>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">{busy ? <Badge tone="info">running {busy}</Badge> : null}{error ? <Badge tone="danger">{error}</Badge> : null}{result ? <Badge tone="success">{result}</Badge> : null}</div>
      </Card>
    );
  }

  if (section === "tickets") {
    return (
      <Card>
        <SectionTitle title="Ticket actions" description="Reply and status transition for support tickets." />
        <div className="grid gap-3 lg:grid-cols-[160px_160px_1fr_auto]">
          <ActionField label="ticket_id" value={values.ticket_id} onChange={(v) => setField("ticket_id", v)} />
          <ActionField label="status" value={values.status} onChange={(v) => setField("status", v)} placeholder="open | in_progress | closed" />
          <ActionField label="reply" value={values.text} onChange={(v) => setField("text", v)} multiline />
          <div className="flex flex-wrap content-end gap-2">
            <Button disabled={!ticketId || !values.text.trim() || Boolean(busy)} onClick={() => void run("reply", `/api/admin/tickets/${ticketId}/reply`, "POST", { body: values.text })}>Reply</Button>
            <Button disabled={!ticketId || Boolean(busy)} onClick={() => void run("status", `/api/admin/tickets/${ticketId}/status`, "POST", { status: values.status })}>Set status</Button>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">{busy ? <Badge tone="info">running {busy}</Badge> : null}{error ? <Badge tone="danger">{error}</Badge> : null}{result ? <Badge tone="success">{result}</Badge> : null}</div>
      </Card>
    );
  }

  if (section === "payments") {
    return (
      <Card>
        <SectionTitle title="Payment reconciliation" description="Manual reconciliation uses the existing guarded payment order endpoint." />
        <div className="grid gap-3 lg:grid-cols-[140px_220px_160px_1fr_auto]">
          <ActionField label="provider" value={values.provider} onChange={(v) => setField("provider", v)} />
          <ActionField label="order_id" value={values.order_id} onChange={(v) => setField("order_id", v)} />
          <ActionField label="status" value={values.status} onChange={(v) => setField("status", v)} />
          <ActionField label="note" value={values.note} onChange={(v) => setField("note", v)} />
          <Button disabled={!values.provider || !values.order_id || values.note.length < 8 || Boolean(busy)} onClick={() => void run("reconcile", `/api/admin/payments/orders/${encodeURIComponent(values.provider)}/${encodeURIComponent(values.order_id)}/reconcile`, "POST", { status: values.status, note: values.note })}>Reconcile</Button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">{busy ? <Badge tone="info">running {busy}</Badge> : null}{error ? <Badge tone="danger">{error}</Badge> : null}{result ? <Badge tone="success">{result}</Badge> : null}</div>
      </Card>
    );
  }

  if (section === "promos") {
    return (
      <Card>
        <SectionTitle title="Promo actions" description="Create, update or delete promo codes." />
        <div className="grid gap-3 lg:grid-cols-[160px_140px_120px_120px_auto]">
          <ActionField label="code" value={values.code} onChange={(v) => setField("code", v)} />
          <ActionField label="promo_type" value={values.promo_type} onChange={(v) => setField("promo_type", v)} />
          <ActionField label="value" value={values.value} onChange={(v) => setField("value", v)} />
          <ActionField label="uses_left" value={values.uses_left} onChange={(v) => setField("uses_left", v)} />
          <div className="flex flex-wrap content-end gap-2">
            <Button disabled={!values.code || Boolean(busy)} onClick={() => void run("create", "/api/admin/promos", "POST", { code: values.code, promo_type: values.promo_type, value: Number(values.value || 1), uses_left: Number(values.uses_left || -1) })}>Create</Button>
            <Button disabled={!values.code || Boolean(busy)} onClick={() => void run("update", `/api/admin/promos/${encodeURIComponent(values.code)}`, "PATCH", { promo_type: values.promo_type, value: Number(values.value || 1), uses_left: Number(values.uses_left || -1) })}>Update</Button>
            <Button tone="danger" disabled={!values.code || Boolean(busy)} onClick={() => void run("delete", `/api/admin/promos/${encodeURIComponent(values.code)}`, "DELETE")}>Delete</Button>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">{busy ? <Badge tone="info">running {busy}</Badge> : null}{error ? <Badge tone="danger">{error}</Badge> : null}{result ? <Badge tone="success">{result}</Badge> : null}</div>
      </Card>
    );
  }

  if (section === "referrals") {
    return (
      <Card>
        <SectionTitle title="Referral processing" description="Process pending referral queue with the existing backend anti-fraud checks." />
        <div className="flex flex-wrap gap-2">
          <ActionField label="limit" value={values.limit} onChange={(v) => setField("limit", v)} />
          <Button disabled={Boolean(busy)} onClick={() => void run("process", "/api/admin/referrals/process", "POST", { limit: Number(values.limit || 50), force_without_activity: false })}>Process queue</Button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">{busy ? <Badge tone="info">running {busy}</Badge> : null}{error ? <Badge tone="danger">{error}</Badge> : null}{result ? <Badge tone="success">{result}</Badge> : null}</div>
      </Card>
    );
  }

  if (section === "release") {
    return (
      <Card>
        <SectionTitle title="Release/live update" description="Create a backend-owned live update surfaced to clients." />
        <div className="grid gap-3 lg:grid-cols-[1fr_1fr_1fr_auto]">
          <ActionField label="title" value={values.title} onChange={(v) => setField("title", v)} />
          <ActionField label="summary" value={values.summary} onChange={(v) => setField("summary", v)} />
          <ActionField label="link" value={values.link} onChange={(v) => setField("link", v)} />
          <Button disabled={!values.title || !values.summary || Boolean(busy)} onClick={() => void run("live update", "/api/admin/live-updates", "POST", { title: values.title, summary: values.summary, link: values.link || null, is_active: true })}>Create update</Button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">{busy ? <Badge tone="info">running {busy}</Badge> : null}{error ? <Badge tone="danger">{error}</Badge> : null}{result ? <Badge tone="success">{result}</Badge> : null}</div>
      </Card>
    );
  }

  return null;
}

export function OpsDashboard({ section }: { section: OpsDashboardSection }) {
  const mountedRef = useRef(true);
  const loadAbortRef = useRef<AbortController | null>(null);
  const loadSeqRef = useRef(0);
  const [authReady, setAuthReady] = useState(false);
  const [overview, setOverview] = useState<OpsOverview | null>(null);
  const [alerts, setAlerts] = useState<OpsAlert[]>([]);
  const [freeUsers, setFreeUsers] = useState<FreeTierUser[]>([]);
  const [trafficRows, setTrafficRows] = useState<TrafficSummaryRow[]>([]);
  const [timeseriesRows, setTimeseriesRows] = useState<NodeTimeseriesRow[]>([]);
  const [quotas, setQuotas] = useState<ProviderQuotaConfig[]>([]);
  const [modulePayload, setModulePayload] = useState<AdminModulePayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [quotaForm, setQuotaForm] = useState<QuotaFormState | null>(null);
  const [savingQuota, setSavingQuota] = useState(false);
  const [deletingQuota, setDeletingQuota] = useState(false);
  const [quotaError, setQuotaError] = useState("");
  const [alertActionId, setAlertActionId] = useState<number | null>(null);
  const [broadcastText, setBroadcastText] = useState("");
  const [broadcastResult, setBroadcastResult] = useState("");
  const [broadcastSending, setBroadcastSending] = useState(false);
  const [broadcastError, setBroadcastError] = useState("");

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      loadAbortRef.current?.abort();
    };
  }, []);

  const load = useCallback(async () => {
    loadSeqRef.current += 1;
    const seq = loadSeqRef.current;
    loadAbortRef.current?.abort();
    const controller = new AbortController();
    loadAbortRef.current = controller;

    if (!hasAdminAuthMaterial()) {
      if (loadAbortRef.current === controller) loadAbortRef.current = null;
      setLoading(false);
      setAuthReady(false);
      return;
    }
    setAuthReady(true);
    setLoading(true);
    setError("");
    try {
      const [overviewData, freeData, trafficData, timeseriesData, quotaData, moduleData] = await Promise.all([
        fetchOpsOverview({ signal: controller.signal }),
        fetchFreeUsers({ signal: controller.signal }).catch(() => []),
        fetchTrafficSummary({ signal: controller.signal }).catch(() => []),
        fetchNodeTimeseries("", { signal: controller.signal }).catch(() => []),
        fetchProviderQuotas({ signal: controller.signal }).catch(() => []),
        moduleSections.has(section) ? fetchAdminModule(section, { signal: controller.signal }).catch(() => null) : Promise.resolve(null)
      ]);
      if (!mountedRef.current || controller.signal.aborted || loadSeqRef.current !== seq) return;
      setOverview(overviewData);
      setAlerts(overviewData.alerts?.active || []);
      setFreeUsers(freeData);
      setTrafficRows(trafficData);
      setTimeseriesRows(timeseriesData);
      setQuotas(quotaData);
      setModulePayload(moduleData);
    } catch (err) {
      if (!mountedRef.current || controller.signal.aborted || loadSeqRef.current !== seq) return;
      setError(err instanceof Error ? err.message : "Admin API error");
      if (String(err).includes("401") || String(err).includes("403")) setAuthReady(false);
    } finally {
      if (loadAbortRef.current === controller) loadAbortRef.current = null;
      if (mountedRef.current && loadSeqRef.current === seq) setLoading(false);
    }
  }, [section]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const providerStatus = useMemo(() => overview?.provider_quotas || [], [overview?.provider_quotas]);
  const configuredByNode = useMemo(() => new Map(quotas.map((quota) => [quota.node_code.toLowerCase(), quota])), [quotas]);
  const trafficChart = useMemo(() => buildTrafficChart(trafficRows), [trafficRows]);
  const nodeChart = useMemo(() => buildNodeChart(timeseriesRows), [timeseriesRows]);

  useEffect(() => {
    if (section !== "provider-caps" || quotaForm?.node_code) return;
    const first = providerStatus.find((row) => row.node_code) || null;
    if (!first) return;
    const configured = configuredByNode.get(first.node_code.toLowerCase());
    const timer = window.setTimeout(
      () =>
        setQuotaForm({
          node_code: first.node_code,
          included_gb: String(configured?.included_gb || first.included_gb || 1024),
          reset_day: String(configured?.reset_day || 1),
          timezone: configured?.timezone || "UTC",
          warning_ratio: String(configured?.warning_ratio || 0.8),
          critical_ratio: String(configured?.critical_ratio || 0.95),
          enabled: configured?.enabled ?? true,
          notes: configured?.notes || ""
        }),
      0
    );
    return () => window.clearTimeout(timer);
  }, [configuredByNode, providerStatus, quotaForm?.node_code, section]);

  const alertColumns = useMemo<ColumnDef<OpsAlert>[]>(
    () => [
      { header: "Severity", cell: ({ row }) => <Badge tone={toneForState(row.original.severity)}>{row.original.severity}</Badge> },
      { header: "Source", accessorKey: "source" },
      {
        header: "Alert",
        cell: ({ row }) => (
          <div className="max-w-[420px]">
            <div className="font-semibold">{row.original.title}</div>
            <div className="truncate text-[color:var(--atlas-text-soft)]">{row.original.body || row.original.fingerprint}</div>
          </div>
        )
      },
      { header: "Node", cell: ({ row }) => row.original.node_code || "system" },
      { header: "Last", cell: ({ row }) => shortDateTime(row.original.last_seen_at) },
      {
        header: "Actions",
        cell: ({ row }) => (
          <div className="flex gap-2">
            <Button
              tone="secondary"
              disabled={alertActionId === row.original.id}
              onClick={async () => {
                setAlertActionId(row.original.id);
                setError("");
                try {
                  await ackAlert(row.original.id);
                  await load();
                } catch (err) {
                  setError(errorMessage(err, "Alert ack failed"));
                } finally {
                  setAlertActionId(null);
                }
              }}
            >
              {alertActionId === row.original.id ? <Loader2 className="animate-spin" size={14} /> : <Check size={14} />} Ack
            </Button>
            <Button
              tone="ghost"
              disabled={alertActionId === row.original.id}
              onClick={async () => {
                setAlertActionId(row.original.id);
                setError("");
                try {
                  await silenceAlert(row.original.id, 120);
                  await load();
                } catch (err) {
                  setError(errorMessage(err, "Alert silence failed"));
                } finally {
                  setAlertActionId(null);
                }
              }}
            >
              {alertActionId === row.original.id ? <Loader2 className="animate-spin" size={14} /> : <BellOff size={14} />} 2h
            </Button>
          </div>
        )
      }
    ],
    [alertActionId, load]
  );

  const providerColumns = useMemo<ColumnDef<ProviderQuotaStatus>[]>(
    () => [
      { header: "Node", cell: ({ row }) => <span className="font-semibold">{row.original.node_code}</span> },
      { header: "State", cell: ({ row }) => <Badge tone={toneForState(row.original.state)}>{row.original.state}</Badge> },
      {
        header: "Used",
        cell: ({ row }) => (
          <div className="min-w-[180px]">
            <div className="mb-1 flex justify-between gap-2 text-[11px] text-[color:var(--atlas-text-soft)]">
              <span>{formatGb(row.original.used_gb)}</span>
              <span>{formatPct(row.original.used_pct)}</span>
            </div>
            <Progress value={row.original.used_pct} tone={toneForState(row.original.state)} />
          </div>
        )
      },
      { header: "Included", cell: ({ row }) => formatGb(row.original.included_gb) },
      { header: "Remaining", cell: ({ row }) => formatGb(row.original.remaining_gb) },
      { header: "Reset", cell: ({ row }) => shortDateTime(row.original.cycle_end) },
      {
        header: "Edit",
        cell: ({ row }) => (
          <Button
            tone="secondary"
            onClick={() => {
              const configured = configuredByNode.get(row.original.node_code.toLowerCase());
              setQuotaError("");
              setQuotaForm({
                node_code: row.original.node_code,
                included_gb: String(configured?.included_gb || row.original.included_gb || 1024),
                reset_day: String(configured?.reset_day || row.original.reset_day || 1),
                timezone: configured?.timezone || row.original.timezone || "UTC",
                warning_ratio: String(configured?.warning_ratio || row.original.warning_ratio || 0.8),
                critical_ratio: String(configured?.critical_ratio || row.original.critical_ratio || 0.95),
                enabled: configured?.enabled ?? row.original.enabled,
                notes: configured?.notes || ""
              });
            }}
          >
            Edit
          </Button>
        )
      }
    ],
    [configuredByNode]
  );

  const freeColumns = useMemo<ColumnDef<FreeTierUser>[]>(
    () => [
      { header: "User", cell: ({ row }) => <span className="font-semibold">{row.original.username || row.original.display_name || row.original.tg_id}</span> },
      { header: "State", cell: ({ row }) => <Badge tone={toneForState(row.original.state)}>{row.original.state}</Badge> },
      {
        header: "Traffic",
        cell: ({ row }) => (
          <div className="min-w-[180px]">
            <div className="mb-1 flex justify-between gap-2 text-[11px] text-[color:var(--atlas-text-soft)]">
              <span>{formatGb(row.original.used_gb)}</span>
              <span>{formatPct(row.original.used_pct)}</span>
            </div>
            <Progress value={row.original.used_pct} tone={toneForState(row.original.state)} />
          </div>
        )
      },
      { header: "Left", cell: ({ row }) => formatGb(row.original.remaining_gb) },
      { header: "Reset", cell: ({ row }) => shortDateTime(row.original.cycle_end) },
      { header: "Active", cell: ({ row }) => (row.original.is_active ? "yes" : "no") }
    ],
    []
  );

  const trafficColumns = useMemo<ColumnDef<TrafficSummaryRow>[]>(
    () => [
      { header: "Date", accessorKey: "date" },
      { header: "Node", accessorKey: "node_code" },
      { header: "Pool", accessorKey: "pool_code" },
      { header: "Traffic", cell: ({ row }) => formatGb(row.original.traffic_gb) },
      { header: "Samples", cell: ({ row }) => formatInt(row.original.samples) }
    ],
    []
  );

  const moduleColumns = useMemo<ColumnDef<Record<string, unknown>>[]>(() => {
    const sample = modulePayload?.rows?.[0] || {};
    const keys = Object.keys(sample).slice(0, 8);
    return keys.map((key) => ({
      header: key,
      cell: ({ row }) => <span className="line-clamp-2 max-w-[240px]">{compactValue(row.original[key])}</span>
    }));
  }, [modulePayload]);

  if (!authReady && !loading) {
    return <AuthGate onReady={() => void load()} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          {overview?.metrics?.status ? <Badge tone={toneForState(overview.metrics.status)}>{overview.metrics.status}</Badge> : null}
          {overview?.generated_at ? <span className="text-xs text-[color:var(--atlas-text-muted)]">Updated {shortDateTime(overview.generated_at)}</span> : null}
          {error ? <Badge tone="danger">{error}</Badge> : null}
        </div>
        <Button tone="secondary" onClick={() => void load()} disabled={loading}>
          {loading ? <Loader2 className="animate-spin" size={15} /> : <RefreshCw size={15} />} Refresh
        </Button>
      </div>

      {loading && !overview ? (
        <Card className="grid min-h-[320px] place-items-center text-sm text-[color:var(--atlas-text-soft)]">
          <Loader2 className="mb-2 animate-spin" size={22} /> Loading admin surface
        </Card>
      ) : null}

      {overview ? (
        <>
          {(section === "dashboard" || section === "alerts") && (
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <MetricTile label="Active alerts" value={formatInt(overview.alerts.active_count)} detail={`${overview.alerts.critical_count} critical, ${overview.alerts.warning_count} warning`} tone={overview.alerts.critical_count ? "danger" : overview.alerts.warning_count ? "warning" : "success"} />
              <MetricTile label="Users active" value={formatInt(overview.summary.users.active)} detail={`${formatInt(overview.summary.users.free)} free / ${formatInt(overview.summary.users.paid)} paid`} tone="info" />
              <MetricTile label="Nodes healthy" value={`${overview.summary.nodes.healthy}/${overview.summary.nodes.total}`} detail={`metrics age ${formatInt(overview.metrics.age_seconds || 0)}s`} tone={overview.summary.nodes.healthy === overview.summary.nodes.total ? "success" : "warning"} />
              <MetricTile label="Free tier burn" value={formatGb(overview.free_tier.used_gb)} detail={`${overview.free_tier.over_cap_users} over cap, ${overview.free_tier.near_cap_users} near`} tone={overview.free_tier.over_cap_users ? "danger" : overview.free_tier.near_cap_users ? "warning" : "success"} />
            </div>
          )}

          {(section === "dashboard" || section === "traffic" || section === "nodes") && (
            <div className="grid gap-3 xl:grid-cols-[1.2fr_0.8fr]">
              <Card className="min-h-[320px]">
                <SectionTitle title="Traffic by pool" description="Сводка из KeyUsageRollup: free/premium по дням." />
                <div className="h-[240px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={trafficChart}>
                      <CartesianGrid stroke="rgba(17,24,20,0.08)" vertical={false} />
                      <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Area type="monotone" dataKey="premium" stackId="1" stroke="#12805a" fill="#12805a" fillOpacity={0.22} />
                      <Area type="monotone" dataKey="free" stackId="1" stroke="#315c70" fill="#315c70" fillOpacity={0.2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </Card>
              <Card className="min-h-[320px]">
                <SectionTitle title="Node pressure" description="CPU, network и capacity score по последним sample points." />
                <div className="h-[240px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={nodeChart}>
                      <CartesianGrid stroke="rgba(17,24,20,0.08)" vertical={false} />
                      <XAxis dataKey="t" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Line type="monotone" dataKey="cpu" stroke="#8d352e" dot={false} strokeWidth={2} />
                      <Line type="monotone" dataKey="net" stroke="#315c70" dot={false} strokeWidth={2} />
                      <Line type="monotone" dataKey="score" stroke="#12805a" dot={false} strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </div>
          )}

          {(section === "dashboard" || section === "alerts") && (
            <Card>
              <SectionTitle title="Durable alerts" description="Active alerts are persisted, ackable, silenceable and refresh from current ops snapshots." />
              <DataTable data={alerts} columns={alertColumns} empty="Нет активных алертов" />
            </Card>
          )}

          {(section === "dashboard" || section === "provider-caps") && (
            <div className="grid gap-3 xl:grid-cols-[1fr_360px]">
              <Card>
                <SectionTitle title="Provider caps" description="Ручные hoster/provider лимиты по нодам, reset window и остаток до капа." />
                <DataTable data={providerStatus} columns={providerColumns} empty="Нет нод или квот" />
              </Card>
              <Card>
                <SectionTitle title="Quota config" description="CRUD v1: ручная конфигурация лимита трафика по node_code." />
                {quotaForm ? (
                  <form
                    className="space-y-3"
                    onSubmit={async (event) => {
                      event.preventDefault();
                      const warningRatio = Number(quotaForm.warning_ratio || 0.8);
                      const criticalRatio = Number(quotaForm.critical_ratio || 0.95);
                      if (warningRatio >= criticalRatio) {
                        setQuotaError("warning_ratio must be lower than critical_ratio");
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
                          className="mt-1 h-9 w-full rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm text-[color:var(--atlas-text)] outline-none focus:border-[color:var(--atlas-focus)]"
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
                        {savingQuota ? <Loader2 className="animate-spin" size={15} /> : <Save size={15} />} Save
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
                        {deletingQuota ? <Loader2 className="animate-spin" size={15} /> : <Trash2 size={15} />} Delete
                      </Button>
                    </div>
                  </form>
                ) : (
                  <div className="text-sm text-[color:var(--atlas-text-soft)]">Выбери ноду в таблице.</div>
                )}
              </Card>
            </div>
          )}

          {(section === "dashboard" || section === "free-tier") && (
            <div className="grid gap-3 xl:grid-cols-[320px_1fr]">
              <Card>
                <SectionTitle title="Free tier" description="Dedicated NL-free, 5 GB / 30 days, 50 Mbps/IP, 1 device." />
                <div className="space-y-4">
                  <MetricTile label="Free users" value={formatInt(overview.free_tier.free_users)} detail={`${overview.free_tier.sampled_users} sampled`} tone="info" />
                  <div>
                    <div className="mb-2 flex justify-between text-xs text-[color:var(--atlas-text-soft)]">
                      <span>{formatGb(overview.free_tier.used_gb)}</span>
                      <span>{formatPct(overview.free_tier.used_pct)}</span>
                    </div>
                    <Progress value={overview.free_tier.used_pct} tone={overview.free_tier.over_cap_users ? "danger" : overview.free_tier.near_cap_users ? "warning" : "success"} />
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <Badge tone="warning">{overview.free_tier.near_cap_users} near</Badge>
                    <Badge tone="danger">{overview.free_tier.over_cap_users} over</Badge>
                  </div>
                </div>
              </Card>
              <Card>
                <SectionTitle title="Free users" description="Расход, остаток и reset window по бесплатным пользователям." />
                <DataTable data={freeUsers} columns={freeColumns} empty="Нет free пользователей" />
              </Card>
            </div>
          )}

          {section === "traffic" && (
            <Card>
              <SectionTitle title="Traffic breakdown" description="Pool / node / day breakdown from usage rollups." />
              <DataTable data={trafficRows} columns={trafficColumns} empty="Нет traffic rollups" />
            </Card>
          )}

          {section === "nodes" && (
            <Card>
              <SectionTitle title="Node status" description="Capacity rows from ops overview." />
              <DataTable
                data={(overview.capacity.nodes || []) as Array<Record<string, unknown>>}
                columns={[
                  { header: "Node", cell: ({ row }) => compactValue(row.original.code || row.original.node_code) },
                  { header: "State", cell: ({ row }) => <Badge tone={toneForState(compactValue(row.original.capacity_state))}>{compactValue(row.original.capacity_state)}</Badge> },
                  { header: "Score", cell: ({ row }) => compactValue(row.original.capacity_score) },
                  { header: "TX ratio", cell: ({ row }) => compactValue(row.original.tx_ratio) },
                  { header: "CPU", cell: ({ row }) => compactValue(row.original.cpu_percent) },
                  { header: "Reason", cell: ({ row }) => compactValue(row.original.reject_reason) }
                ]}
                empty="Нет capacity данных"
              />
            </Card>
          )}

          {moduleSections.has(section) && section !== "funnel" && (
            <ModuleActionPanel section={section} onDone={load} />
          )}

          {moduleSections.has(section) && section !== "funnel" && (
            <Card>
              <SectionTitle title={`Module: ${section}`} description="Read-side parity surface over existing POKROV admin API. Destructive flows stay guarded by existing backend auth." />
              <DataTable data={modulePayload?.rows || []} columns={moduleColumns} empty="Нет строк" />
            </Card>
          )}

          {section === "funnel" && (
            <Card>
              <SectionTitle title="Funnel" description="Existing /api/admin/funnel/summary payload for operator diagnosis." />
              <pre className="ops-scrollbar max-h-[560px] overflow-auto rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 text-xs">
                {JSON.stringify(modulePayload?.payload || {}, null, 2)}
              </pre>
            </Card>
          )}

          {section === "broadcast" && (
            <Card className="max-w-2xl">
              <SectionTitle title="Broadcast" description="Отправка через существующий /api/admin/broadcast. По умолчанию segment=active, limit=100." />
              <textarea
                value={broadcastText}
                onChange={(event) => setBroadcastText(event.target.value)}
                className="min-h-36 w-full rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]"
                placeholder="Текст рассылки"
              />
              <div className="mt-3 flex items-center gap-2">
                <Button
                  tone="primary"
                  disabled={!broadcastText.trim() || broadcastSending}
                  onClick={async () => {
                    setBroadcastSending(true);
                    setBroadcastError("");
                    setBroadcastResult("");
                    try {
                      const result = await sendBroadcast({ text: broadcastText, segment: "active", limit: 100 });
                      setBroadcastResult(JSON.stringify(result));
                    } catch (err) {
                      setBroadcastError(errorMessage(err, "Broadcast failed"));
                    } finally {
                      setBroadcastSending(false);
                    }
                  }}
                >
                  {broadcastSending ? <Loader2 className="animate-spin" size={15} /> : <AlertTriangle size={15} />} Send active 100
                </Button>
                {broadcastError ? <Badge tone="danger">{broadcastError}</Badge> : null}
                {broadcastResult ? <span className="text-xs text-[color:var(--atlas-text-soft)]">{broadcastResult}</span> : null}
              </div>
            </Card>
          )}
        </>
      ) : null}
    </div>
  );
}
