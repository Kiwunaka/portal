"use client";

import { Clock3, Download, KeyRound, RefreshCw, ShieldAlert, ShieldCheck, UserCog } from "lucide-react";
import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, EmptyState, MetricCell, MetricStrip, SectionTitle } from "@/components/ui";
import { WindowedTable } from "@/components/ui/windowed-table";
import type { ActionIntentRequest } from "@/lib/admin-api/actions";
import { AdminApiError } from "@/lib/admin-api/client";
import {
  exportGovernanceAudit,
  fetchGovernanceOperator,
  fetchGovernanceOverview,
  type GovernanceOperator,
  type GovernanceOperatorDetail,
  type GovernanceRole,
} from "@/lib/admin-api/governance";
import { useRouteResource } from "@/lib/use-route-resource";

type Tab = "operators" | "audit" | "sensitive" | "privacy";
type GrantKind = "standing" | "jit" | "break_glass";

const inputClass = "min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]";

function dateTime(value: string | null | undefined): string {
  if (!value || !Number.isFinite(Date.parse(value))) return "—";
  return new Date(value).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}

function shortId(value: string | null | undefined): string {
  return value ? value.slice(0, 8) : "—";
}

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

function roleTone(role: GovernanceRole): "success" | "warning" | "danger" | "neutral" {
  if (!role.active) return "neutral";
  if (role.grant_kind === "break_glass") return "danger";
  if (role.grant_kind === "jit") return "warning";
  return "success";
}

function statusTone(status: string): "success" | "danger" | "warning" | "neutral" {
  if (status === "active" || status === "success" || status === "completed") return "success";
  if (status === "suspended" || status === "failed" || status === "denied") return "danger";
  if (status === "pending_review") return "warning";
  return "neutral";
}

export function GovernancePage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const load = useCallback((signal: AbortSignal) => fetchGovernanceOverview({ signal }), []);
  const resource = useRouteResource("governance:overview", load, { enabled: true, pollMs: 60_000 });
  const operators = useMemo(() => resource.data?.operators.items || [], [resource.data?.operators.items]);
  const [tab, setTab] = useState<Tab>("operators");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const effectiveSelectedId = selectedId || operators[0]?.id || null;
  const loadDetail = useCallback(
    (signal: AbortSignal) => effectiveSelectedId ? fetchGovernanceOperator(effectiveSelectedId, { signal }) : Promise.reject(new Error("operator_not_selected")),
    [effectiveSelectedId],
  );
  const detail = useRouteResource<GovernanceOperatorDetail>(`governance:operator:${effectiveSelectedId || "none"}`, loadDetail, { enabled: Boolean(effectiveSelectedId) });
  const [roleCode, setRoleCode] = useState("readonly");
  const [grantKind, setGrantKind] = useState<GrantKind>("standing");
  const [minutes, setMinutes] = useState(30);
  const [reason, setReason] = useState("Операционная необходимость подтверждена владельцем смены");
  const [formError, setFormError] = useState("");
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [exporting, setExporting] = useState(false);

  const selectedSummary = useMemo(
    () => operators.find((operator) => operator.id === effectiveSelectedId) || null,
    [effectiveSelectedId, operators],
  );

  useEffect(() => {
    onShellStatus?.({
      api: resource.error ? resource.data ? "degraded" : "failed" : resource.loading ? "missing" : "ok",
      session: isAccessDenied(resource.error) ? "failed" : resource.data ? "ok" : resource.error ? "unavailable" : "missing",
      oldestRequiredSourceAt: resource.data?.privacy.generated_at || resource.updatedAt,
    });
  }, [onShellStatus, resource.data, resource.error, resource.loading, resource.updatedAt]);

  function reload() {
    resource.reload();
    if (effectiveSelectedId) detail.reload();
  }

  function openAction(action: string, target: { type: string; id: string }, payload: Record<string, unknown>) {
    setRequest({
      action,
      target,
      payload,
      endpoint: "/api/admin/v2/governance/action-intents",
      method: "POST",
      workspace: "governance",
    });
    setDialogOpen(true);
  }

  function submitGrant(event: FormEvent) {
    event.preventDefault();
    if (!effectiveSelectedId) return;
    const normalizedReason = reason.trim();
    if (normalizedReason.length < 8) {
      setFormError("Причина должна содержать минимум 8 символов.");
      return;
    }
    const limits = resource.data?.catalog.temporal_limits_minutes[grantKind];
    if (limits && (minutes < limits.min || minutes > limits.max)) {
      setFormError(`Для ${grantKind} срок должен быть ${limits.min}–${limits.max} минут.`);
      return;
    }
    setFormError("");
    openAction("operator.role.grant", { type: "operator", id: effectiveSelectedId }, {
      role_code: roleCode,
      grant_kind: grantKind,
      ...(grantKind === "standing" ? {} : { expires_at: new Date(Date.now() + minutes * 60_000).toISOString() }),
      reason: normalizedReason,
    });
  }

  function operatorStatusAction(operator: GovernanceOperator) {
    const action = operator.status === "active" ? "operator.suspend" : "operator.activate";
    openAction(action, { type: "operator", id: operator.id }, { reason: reason.trim() });
  }

  async function downloadAudit() {
    setExporting(true);
    try {
      const blob = await exportGovernanceAudit();
      const href = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = href;
      anchor.download = "pokrov-operator-audit.csv";
      anchor.click();
      URL.revokeObjectURL(href);
    } finally {
      setExporting(false);
    }
  }

  const pendingReviews = operators.reduce((total, operator) => total + operator.pending_reviews, 0);
  const activeSessions = operators.reduce((total, operator) => total + operator.active_sessions, 0);
  const auditFailures = (resource.data?.audit.items || []).filter((row) => row.result !== "success" && row.result !== "completed").length;

  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone={pendingReviews ? "warning" : "success"}>{pendingReviews ? `Непроверенных выдач: ${pendingReviews}` : "Временный доступ разобран"}</Badge>
          <span>Любое изменение доступа проходит step-up, preview, точное подтверждение и единый action-intent.</span>
        </div>
        <Button tone="secondary" disabled={resource.loading || resource.refreshing} onClick={reload}>
          <RefreshCw aria-hidden="true" size={15} className={resource.refreshing ? "animate-spin" : ""} /> Обновить
        </Button>
      </div>

      <MetricStrip label="Контроль доступа">
        <MetricCell icon={<UserCog size={17} />} label="Операторы" value={resource.data?.operators.count ?? "—"} detail={resource.data?.operators.environment || "environment неизвестен"} tone="info" />
        <MetricCell icon={<KeyRound size={17} />} label="Активные сессии" value={resource.data ? activeSessions : "—"} detail="Без токенов и CSRF в read model" tone="success" />
        <MetricCell icon={<Clock3 size={17} />} label="Ожидают ревью" value={resource.data ? pendingReviews : "—"} detail="JIT и break-glass" tone={pendingReviews ? "warning" : "success"} />
        <MetricCell icon={<ShieldAlert size={17} />} label="Ошибки аудита" value={resource.data ? auditFailures : "—"} detail="В последних 100 событиях" tone={auditFailures ? "danger" : "neutral"} />
      </MetricStrip>

      <div role="tablist" aria-label="Разделы управления системой" className="flex gap-1 overflow-x-auto rounded-[var(--pokrov-radius-panel)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-1">
        {([
          ["operators", "Операторы"],
          ["audit", "Аудит и команды"],
          ["sensitive", "Чувствительный доступ"],
          ["privacy", "Privacy и retention"],
        ] as const).map(([id, label]) => (
          <button key={id} type="button" role="tab" aria-selected={tab === id} onClick={() => setTab(id)} className={`min-h-10 shrink-0 rounded-[var(--pokrov-radius-control)] px-3 text-xs font-semibold transition ${tab === id ? "bg-[color:var(--atlas-primary)] text-[color:var(--atlas-primary-text)]" : "text-[color:var(--atlas-text-soft)] hover:bg-[color:var(--command-surface-raised)]"}`}>
            {label}
          </button>
        ))}
      </div>

      <RouteBoundary loading={resource.loading} refreshing={resource.refreshing} error={resource.error} hasData={resource.data !== null} retryLabel="Повторить governance" onRetry={resource.reload}>
        {tab === "operators" ? <OperatorsTab
          operators={operators}
          selectedId={effectiveSelectedId}
          selectedSummary={selectedSummary}
          detail={detail}
          roleCodes={(resource.data?.catalog.roles || []).map((role) => role.code)}
          roleCode={roleCode}
          grantKind={grantKind}
          minutes={minutes}
          reason={reason}
          formError={formError}
          onSelect={setSelectedId}
          onRoleCode={setRoleCode}
          onGrantKind={setGrantKind}
          onMinutes={setMinutes}
          onReason={setReason}
          onGrant={submitGrant}
          onStatus={operatorStatusAction}
          onAction={openAction}
        /> : null}

        {tab === "audit" ? (
          <Card>
            <div className="flex flex-wrap items-start justify-between gap-3"><SectionTitle title="Audit explorer" description="Кто, с какой role/permission snapshot, что сделал, над каким ресурсом и через какой action-intent." /><Button tone="secondary" disabled={exporting} onClick={downloadAudit}><Download size={15} /> {exporting ? "Экспорт…" : "CSV до 1000 строк"}</Button></div>
            <WindowedTable label="Аудит операторских действий" columnCount={7} tableClassName="w-full min-w-[70rem] border-collapse text-left text-xs" header={<thead><tr className="border-b border-[color:var(--atlas-border)] text-[color:var(--atlas-text-muted)]"><th className="p-2">Время</th><th className="p-2">Оператор</th><th className="p-2">Роль</th><th className="p-2">Действие</th><th className="p-2">Ресурс</th><th className="p-2">Результат</th><th className="p-2">Command</th></tr></thead>} rows={(resource.data?.audit.items || []).map((row) => <tr key={row.id} className="border-b border-[color:var(--atlas-border)] align-top"><td className="p-2 whitespace-nowrap">{dateTime(row.created_at)}</td><td className="p-2"><strong>{row.operator_name || shortId(row.operator_id)}</strong><span className="mt-0.5 block font-mono text-[10px] text-[color:var(--atlas-text-muted)]">session {shortId(row.session_id)}</span></td><td className="p-2">{row.roles.join(", ") || "—"}</td><td className="p-2 font-mono">{row.action}</td><td className="p-2 font-mono">{row.resource ? `${row.resource.type}:${shortId(row.resource.id)}` : "—"}</td><td className="p-2"><Badge tone={statusTone(row.result)}>{row.result}</Badge>{row.reason_code ? <span className="mt-1 block text-[color:var(--atlas-text-muted)]">{row.reason_code}</span> : null}</td><td className="p-2 font-mono">{shortId(row.command_intent_id)}</td></tr>)} />
            {!resource.data?.audit.items.length ? <EmptyState title="Событий нет" description="Authentication и command события появятся после первого действия." /> : null}
          </Card>
        ) : null}

        {tab === "sensitive" ? (
          <Card>
            <SectionTitle title="Sensitive-access log" description="Выдача и использование доступа к diagnostic bundles. Содержимое bundle и hash токена здесь запрещены." />
            <div className="grid gap-2 lg:grid-cols-2">{(resource.data?.sensitive.items || []).map((row) => <article key={row.grant_id} className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] p-3 text-xs"><div className="flex items-center justify-between gap-2"><span className="font-semibold">Тикет #{row.ticket_id}</span><Badge tone={row.retention_hold ? "warning" : "neutral"}>{row.retention_hold ? "retention hold" : row.action}</Badge></div><dl className="mt-3 grid grid-cols-2 gap-2"><div><dt className="text-[color:var(--atlas-text-muted)]">Оператор</dt><dd>{row.actor_tg_id} · {row.actor_role}</dd></div><div><dt className="text-[color:var(--atlas-text-muted)]">Причина</dt><dd>{row.reason_code}</dd></div><div><dt className="text-[color:var(--atlas-text-muted)]">Выдано</dt><dd>{dateTime(row.created_at)}</dd></div><div><dt className="text-[color:var(--atlas-text-muted)]">Использовано</dt><dd>{dateTime(row.used_at)}</dd></div></dl><p className="mt-2 font-mono text-[10px] text-[color:var(--atlas-text-muted)]">grant {shortId(row.grant_id)} · upload {shortId(row.upload_id)}</p></article>)}</div>
            {!resource.data?.sensitive.items.length ? <EmptyState title="Доступов не было" description="Журнал пуст; это не считается ошибкой источника." /> : null}
          </Card>
        ) : null}

        {tab === "privacy" ? <PrivacyTab data={resource.data?.privacy || null} /> : null}
      </RouteBoundary>

      <ActionIntentDialog open={dialogOpen} request={request} onOpenChange={(open) => { setDialogOpen(open); if (!open) setRequest(null); }} onKnownOutcome={reload} onCheckState={reload} />
    </div>
  );
}

type DetailResource = ReturnType<typeof useRouteResource<GovernanceOperatorDetail>>;

function OperatorsTab({ operators, selectedId, selectedSummary, detail, roleCodes, roleCode, grantKind, minutes, reason, formError, onSelect, onRoleCode, onGrantKind, onMinutes, onReason, onGrant, onStatus, onAction }: {
  operators: GovernanceOperator[];
  selectedId: string | null;
  selectedSummary: GovernanceOperator | null;
  detail: DetailResource;
  roleCodes: string[];
  roleCode: string;
  grantKind: GrantKind;
  minutes: number;
  reason: string;
  formError: string;
  onSelect: (id: string) => void;
  onRoleCode: (value: string) => void;
  onGrantKind: (value: GrantKind) => void;
  onMinutes: (value: number) => void;
  onReason: (value: string) => void;
  onGrant: (event: FormEvent) => void;
  onStatus: (operator: GovernanceOperator) => void;
  onAction: (action: string, target: { type: string; id: string }, payload: Record<string, unknown>) => void;
}) {
  return <section className="ops-workspace xl:grid-cols-[minmax(18rem,0.7fr)_minmax(0,1.3fr)]">
    <Card>
      <SectionTitle title="Операторы" description="Identity source, состояние, активные роли, сессии и незакрытые временные выдачи." />
      <div className="space-y-2">{operators.map((operator) => <button key={operator.id} type="button" onClick={() => onSelect(operator.id)} className={`w-full rounded-[var(--pokrov-radius-control)] border p-3 text-left transition ${selectedId === operator.id ? "border-[color:var(--atlas-accent)] bg-[color:var(--atlas-accent-soft)]" : "border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] hover:border-[color:var(--atlas-border-strong)]"}`}><span className="flex items-start justify-between gap-2"><span><span className="block text-sm font-semibold">{operator.display_name || shortId(operator.id)}</span><span className="mt-0.5 block font-mono text-[10px] text-[color:var(--atlas-text-muted)]">{shortId(operator.id)} · {operator.identity_source}</span></span><Badge tone={statusTone(operator.status)}>{operator.status}</Badge></span><span className="mt-2 flex flex-wrap gap-1">{operator.active_roles.map((role) => <Badge key={role.id} tone={roleTone(role)}>{role.role_code}{role.grant_kind !== "standing" ? ` · ${role.grant_kind}` : ""}</Badge>)}</span><span className="mt-2 block text-[11px] text-[color:var(--atlas-text-soft)]">Сессий: {operator.active_sessions} · последний вход {dateTime(operator.last_seen_at)}</span></button>)}</div>
      {!operators.length ? <EmptyState title="Операторов нет" description="Bootstrap ещё не создал ни одной operator identity." /> : null}
    </Card>
    <div className="space-y-3">
      <Card>
        <SectionTitle title={selectedSummary?.display_name || "Карточка оператора"} description={selectedSummary ? `${selectedSummary.identity_source} · ${selectedSummary.id}` : "Выберите оператора слева."} />
        {!selectedSummary ? <EmptyState description="Карточка появится после выбора." /> : <div className="space-y-4"><div className="flex flex-wrap items-center gap-2"><Badge tone={statusTone(selectedSummary.status)}>{selectedSummary.status}</Badge><span className="text-xs text-[color:var(--atlas-text-soft)]">Telegram ID: {selectedSummary.legacy_actor_tg_id ?? "не связан"}</span><Button tone={selectedSummary.status === "active" ? "danger" : "secondary"} onClick={() => onStatus(selectedSummary)}>{selectedSummary.status === "active" ? "Заблокировать" : "Активировать"}</Button></div><form onSubmit={onGrant} className="grid gap-3 rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] p-3 md:grid-cols-2"><label className="text-xs font-semibold">Роль<select value={roleCode} onChange={(event) => onRoleCode(event.target.value)} className={`${inputClass} mt-1`}>{roleCodes.map((code) => <option key={code} value={code}>{code}</option>)}</select></label><label className="text-xs font-semibold">Тип выдачи<select value={grantKind} onChange={(event) => onGrantKind(event.target.value as GrantKind)} className={`${inputClass} mt-1`}><option value="standing">standing</option><option value="jit">JIT</option><option value="break_glass">break-glass</option></select></label>{grantKind !== "standing" ? <label className="text-xs font-semibold">Срок, минут<input type="number" value={minutes} min={5} max={1440} onChange={(event) => onMinutes(Number(event.target.value))} className={`${inputClass} mt-1`} /></label> : null}<label className={`text-xs font-semibold ${grantKind === "standing" ? "md:col-span-2" : ""}`}>Причина / тикет<input value={reason} maxLength={240} onChange={(event) => onReason(event.target.value)} className={`${inputClass} mt-1`} /></label>{formError ? <p role="alert" className="text-xs text-[color:var(--atlas-status-danger-text)] md:col-span-2">{formError}</p> : null}<div className="md:col-span-2"><Button type="submit" tone={grantKind === "break_glass" ? "danger" : "primary"}>Подготовить выдачу</Button></div></form></div>}
      </Card>
      {selectedId ? <RouteBoundary loading={detail.loading} refreshing={detail.refreshing} error={detail.error} hasData={detail.data !== null} retryLabel="Повторить карточку" onRetry={detail.reload}><div className="grid gap-3 lg:grid-cols-2"><Card><SectionTitle title="Роли и ревью" description="История не стирается: отозванные и истёкшие выдачи остаются в карточке." /><div className="space-y-2">{(detail.data?.roles || []).map((role) => <article key={role.id} className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] p-3 text-xs"><div className="flex flex-wrap items-center justify-between gap-2"><strong>{role.role_code}</strong><div className="flex gap-1"><Badge tone={roleTone(role)}>{role.grant_kind}</Badge><Badge tone={statusTone(role.review_status)}>{role.review_status}</Badge></div></div><p className="mt-2 text-[color:var(--atlas-text-soft)]">Выдана {dateTime(role.granted_at)}{role.expires_at ? ` · до ${dateTime(role.expires_at)}` : " · бессрочно"}</p><p className="mt-1 text-[color:var(--atlas-text-muted)]">{role.grant_reason || role.revoke_reason || "Причина не сохранена"}</p><div className="mt-2 flex flex-wrap gap-2">{role.active ? <Button size="compact" tone="danger" onClick={() => onAction("operator.role.revoke", { type: "operator", id: selectedId }, { role_code: role.role_code, reason: reason.trim() })}>Отозвать</Button> : null}{role.review_status === "pending_review" ? <Button size="compact" tone="secondary" onClick={() => onAction("operator.access.review", { type: "operator_role", id: role.id }, { note: reason.trim() })}>Закрыть ревью</Button> : null}</div></article>)}</div></Card><Card><SectionTitle title="Сессии" description="Только временные метки и состояние. Session token, hash и CSRF не возвращаются API." /><div className="space-y-2">{(detail.data?.sessions || []).map((session) => <article key={session.id} className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] p-3 text-xs"><div className="flex items-center justify-between gap-2"><span className="font-mono">{shortId(session.id)}</span><Badge tone={session.active ? "success" : "neutral"}>{session.active ? "active" : "closed"}</Badge></div><p className="mt-2 text-[color:var(--atlas-text-soft)]">Последняя активность {dateTime(session.last_seen_at)} · step-up {dateTime(session.step_up_at)}</p>{session.active ? <Button className="mt-2" size="compact" tone="danger" onClick={() => onAction("operator.session.revoke", { type: "operator_session", id: session.id }, { reason: reason.trim() })}>Отозвать сессию</Button> : null}</article>)}{!detail.data?.sessions.length ? <EmptyState description="Сессий у оператора ещё нет." /> : null}</div></Card></div></RouteBoundary> : null}
    </div>
  </section>;
}

function PrivacyTab({ data }: { data: Awaited<ReturnType<typeof fetchGovernanceOverview>>["privacy"] | null }) {
  if (!data) return null;
  const antiabuseBacklog = Object.values(data.deletion_anonymization.backlog).reduce(
    (total, value) => total + value,
    0,
  );
  const bundleBacklog =
    data.diagnostic_bundles.expired_unheld_backlog +
    data.diagnostic_bundles.access_audit_unheld_backlog;
  return (
    <div className="space-y-3">
      <Card>
        <SectionTitle title="Retention control" description="Фактические сроки из environment и backlog старше cutoff. Ноль backlog — проверяемый результат worker policy, а не обещание UI." />
        <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
          {data.retention.map((row) => (
            <article key={row.code} className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] p-3 text-xs">
              <div className="flex items-center justify-between gap-2"><strong>{row.code}</strong><Badge tone={row.expired_backlog ? "danger" : "success"}>{row.expired_backlog ? `backlog ${row.expired_backlog}` : "cutoff чист"}</Badge></div>
              <p className="mt-2 text-2xl font-semibold">{row.raw_retention_days} дней</p>
              <p className="mt-1 text-[color:var(--atlas-text-muted)]">{row.rows} строк · oldest {dateTime(row.oldest_at)}</p>
              <p className="mt-1 font-mono text-[10px]">{row.policy_source} · {row.disposition}</p>
            </article>
          ))}
        </div>
      </Card>
      <div className="grid gap-3 xl:grid-cols-2">
        <Card>
          <SectionTitle title="Deletion / anonymization" description="Raw IP и purpose-bound HMAC поля обнуляются по разным cutoff; audit rows не удаляются этим контуром." />
          <div className="flex items-center justify-between gap-2"><span className="text-sm text-[color:var(--atlas-text-soft)]">Просроченных полей</span><Badge tone={antiabuseBacklog ? "danger" : "success"}>{antiabuseBacklog}</Badge></div>
          <dl className="mt-3 grid grid-cols-3 gap-3 text-sm">
            <div><dt className="text-[color:var(--atlas-text-muted)]">Raw IP</dt><dd className="text-xl font-semibold">{data.deletion_anonymization.policy.raw_ip_hours} ч</dd></div>
            <div><dt className="text-[color:var(--atlas-text-muted)]">Full HMAC</dt><dd className="text-xl font-semibold">{data.deletion_anonymization.policy.full_ip_hmac_days} д</dd></div>
            <div><dt className="text-[color:var(--atlas-text-muted)]">Prefix HMAC</dt><dd className="text-xl font-semibold">{data.deletion_anonymization.policy.prefix_ip_hmac_days} д</dd></div>
          </dl>
          <p className="mt-3 font-mono text-[10px] text-[color:var(--atlas-text-muted)]">{data.deletion_anonymization.policy.disposition}</p>
        </Card>
        <Card>
          <SectionTitle title="Diagnostic bundle TTL" description="Accepted, quarantine, incomplete и access-audit окна учитываются отдельно; held и cleanup backlog не смешиваются." />
          <div className="flex items-center justify-between gap-2"><span className="text-sm text-[color:var(--atlas-text-soft)]">Cleanup backlog</span><Badge tone={bundleBacklog ? "danger" : "success"}>{bundleBacklog}</Badge></div>
          <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div><dt className="text-[color:var(--atlas-text-muted)]">Accepted</dt><dd className="text-xl font-semibold">{data.diagnostic_bundles.accepted_retention_days} дней</dd></div>
            <div><dt className="text-[color:var(--atlas-text-muted)]">Quarantine</dt><dd className="text-xl font-semibold">{data.diagnostic_bundles.quarantine_retention_days} дней</dd></div>
            <div><dt className="text-[color:var(--atlas-text-muted)]">Incomplete grace</dt><dd className="text-xl font-semibold">{data.diagnostic_bundles.incomplete_grace_days} дней</dd></div>
            <div><dt className="text-[color:var(--atlas-text-muted)]">Access audit</dt><dd className="text-xl font-semibold">{data.diagnostic_bundles.access_audit_retention_days} дней</dd></div>
            <div><dt className="text-[color:var(--atlas-text-muted)]">Held bundles</dt><dd className="text-xl font-semibold">{data.diagnostic_bundles.expired_held}</dd></div>
            <div><dt className="text-[color:var(--atlas-text-muted)]">Held audits</dt><dd className="text-xl font-semibold">{data.diagnostic_bundles.access_audit_held}</dd></div>
          </dl>
        </Card>
      </div>
      <Card>
        <SectionTitle title="Field inventory" description="Allowlist возвращаемых полей и явный список того, что governance API не раскрывает." />
        <div className="grid gap-2 xl:grid-cols-2">
          {data.field_inventory.map((family) => (
            <article key={family.family} className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] p-3 text-xs">
              <div className="flex items-center justify-between gap-2"><strong>{family.family}</strong><Badge tone={family.classification === "sensitive" || family.classification === "restricted" ? "warning" : "neutral"}>{family.classification}</Badge></div>
              <p className="mt-2 text-[color:var(--atlas-text-soft)]">{family.fields.join(" · ")}</p>
              {family.excluded?.length ? <p className="mt-1 text-[color:var(--atlas-status-danger-text)]">Не выдаём: {family.excluded.join(" · ")}</p> : null}
            </article>
          ))}
        </div>
      </Card>
      <Card><div className="flex items-start gap-3 text-sm leading-6 text-[color:var(--atlas-text-soft)]"><ShieldCheck aria-hidden="true" className="mt-1 shrink-0 text-[color:var(--atlas-primary)]" size={18} /><p>Raw default — {data.raw_policy.default_days} дней. Более длинные окна остаются только у purpose-bound payment, security, release и access-audit записей; очистка принадлежит <code>{data.raw_policy.cleanup_authority}</code>.</p></div></Card>
    </div>
  );
}
