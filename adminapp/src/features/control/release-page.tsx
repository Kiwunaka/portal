"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import {
  Activity,
  Boxes,
  Clock3,
  Copy,
  Gauge,
  PauseCircle,
  RefreshCw,
  RotateCcw,
  ShieldCheck,
  Smartphone,
  TriangleAlert,
} from "lucide-react";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { MissingData } from "@/components/ops/missing-data";
import { RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  MetricCell,
  MetricStrip,
  SectionTitle,
  type Tone,
} from "@/components/ui";
import type { ActionIntentRequest } from "@/lib/admin-api/actions";
import { AdminApiError } from "@/lib/admin-api/client";
import {
  fetchReleaseCandidates,
  fetchReleaseCockpit,
  type ReleaseCandidateSummary,
  type ReleaseEvidenceCheck,
  type ReleaseEvidenceStatus,
  type ReleaseOriginReadiness,
} from "@/lib/admin-api/control";
import { useRouteResource } from "@/lib/use-route-resource";
import { readUrlState, replaceUrlState, subscribeToUrlState, urlCodecs } from "@/lib/url-state";

type ReleaseUrlState = { candidate: string | null };
type ReleaseAction =
  | "release.rollout.start"
  | "release.rollout.change"
  | "release.rollout.pause"
  | "release.rollout.rollback"
  | "release.min_supported.set"
  | "release.observation.close";

const RELEASE_URL_CODECS = { candidate: urlCodecs.optionalString() };
const ORIGIN_LABELS: Record<string, string> = {
  current: "current-origin",
  brain: "brain-origin",
  ru: "RU-origin",
};
const ACTION_LABELS: Record<ReleaseAction, string> = {
  "release.rollout.start": "Начать rollout",
  "release.rollout.change": "Изменить процент",
  "release.rollout.pause": "Поставить на паузу",
  "release.rollout.rollback": "Запросить rollback",
  "release.min_supported.set": "Изменить min supported",
  "release.observation.close": "Закрыть окно наблюдения",
};

function statusTone(status: ReleaseEvidenceStatus): Tone {
  if (status === "PASS") return "success";
  if (status === "FAIL" || status === "BLOCKED_BY_ACCESS") return "danger";
  if (
    status === "MISSING" ||
    status.startsWith("SKIPPED") ||
    status === "MANUAL_OWNER_TEST" ||
    status === "OPERATOR_ATTESTED"
  ) return "warning";
  return "neutral";
}

function statusText(status: ReleaseEvidenceStatus): string {
  const labels: Record<string, string> = {
    PASS: "Подтверждено · PASS",
    FAIL: "Сбой · FAIL",
    MANUAL_OWNER_TEST: "Ручная проверка · MANUAL_OWNER_TEST",
    OPERATOR_ATTESTED: "Заверено · OPERATOR_ATTESTED",
    SKIPPED_BY_OWNER: "Пропущено владельцем · SKIPPED_BY_OWNER",
    SKIPPED_BY_OPERATOR: "Пропущено оператором · SKIPPED_BY_OPERATOR",
    BLOCKED_BY_ACCESS: "Нет доступа · BLOCKED_BY_ACCESS",
    NOT_REQUESTED: "Не запрашивалось · NOT_REQUESTED",
    MISSING: "Нет данных · MISSING",
  };
  return labels[status] || status || "Нет данных · MISSING";
}

function dateText(value: string | null | undefined): string {
  if (!value || Number.isNaN(Date.parse(value))) return "— · Нет данных";
  return new Date(value).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}

function ageText(seconds: number | null): string {
  if (seconds === null || !Number.isFinite(seconds)) return "— · Нет данных";
  if (seconds < 60) return `${Math.max(0, Math.round(seconds))} сек.`;
  if (seconds < 3600) return `${Math.round(seconds / 60)} мин.`;
  if (seconds < 86400) return `${Math.round(seconds / 3600)} ч.`;
  return `${Math.round(seconds / 86400)} дн.`;
}

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

function CopyValue({ label, value }: { label: string; value: string | null }) {
  const [copied, setCopied] = useState(false);
  if (!value) return <MissingData />;
  return (
    <div className="min-w-0 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[10px] font-semibold uppercase tracking-wide text-[color:var(--atlas-text-muted)]">{label}</span>
        <button
          type="button"
          aria-label={`Копировать ${label}`}
          className="inline-flex min-h-7 items-center gap-1 rounded px-2 text-[11px] text-[color:var(--atlas-text-soft)] hover:bg-[color:var(--atlas-status-neutral-bg)]"
          onClick={() => {
            void navigator.clipboard.writeText(value).then(() => {
              setCopied(true);
              window.setTimeout(() => setCopied(false), 1200);
            });
          }}
        >
          <Copy size={12} /> {copied ? "Скопировано" : "Копировать"}
        </button>
      </div>
      <code className="mt-1 block break-all text-[11px] text-[color:var(--atlas-text-soft)]">{value}</code>
    </div>
  );
}

function CandidateButton({ candidate, selected }: { candidate: ReleaseCandidateSummary; selected: boolean }) {
  return (
    <button
      type="button"
      aria-label={`Открыть релиз ${candidate.component} ${candidate.version}`}
      aria-current={selected ? "true" : undefined}
      onClick={() => replaceUrlState<ReleaseUrlState>({ candidate: candidate.candidate_id }, RELEASE_URL_CODECS)}
      className={`w-full rounded-[var(--pokrov-radius-card)] border p-3 text-left outline-none transition focus-visible:ring-2 focus-visible:ring-[color:var(--atlas-focus)] ${selected ? "border-[color:var(--atlas-primary)] bg-[color:var(--atlas-status-info-bg)]" : "border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] hover:border-[color:var(--atlas-border-strong)]"}`}
    >
      <span className="font-semibold">{candidate.component || "—"} · {candidate.version || "—"}</span>
      <span className="mt-1 block text-[11px] text-[color:var(--atlas-text-soft)]">Возраст: {ageText(candidate.age_seconds)}</span>
      <span className="mt-1 block truncate font-mono text-[10px] text-[color:var(--atlas-text-muted)]">{candidate.candidate_id}</span>
    </button>
  );
}

function EvidenceCheck({ check }: { check: ReleaseEvidenceCheck }) {
  return (
    <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-xs font-semibold">{check.check_name || "Проверка без названия"}</p>
          <p className="mt-1 text-[11px] text-[color:var(--atlas-text-soft)]">
            {check.required ? "Обязательная" : "Диагностическая"} · {check.reason || "причина не указана"}
          </p>
        </div>
        <Badge tone={statusTone(check.status)}>{statusText(check.status)}</Badge>
      </div>
      <p className="mt-2 text-[11px] text-[color:var(--atlas-text-muted)]">Наблюдалось: {dateText(check.observed_at)}</p>
    </div>
  );
}

function OriginBlock({ origin }: { origin: ReleaseOriginReadiness }) {
  const checks = [...origin.checks, ...origin.diagnostics];
  return (
    <section aria-label={ORIGIN_LABELS[origin.origin] || origin.origin} className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold">{ORIGIN_LABELS[origin.origin] || origin.origin}</h3>
        <Badge tone={statusTone(origin.status)}>{statusText(origin.status)}</Badge>
      </div>
      <div className="mt-3 grid gap-2">
        {checks.length ? checks.map((check) => <EvidenceCheck key={`${check.check_name}:${check.evidence_ref || "missing"}`} check={check} />) : <MissingData />}
      </div>
    </section>
  );
}

export function ReleasePage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [urlState, setUrlState] = useState<ReleaseUrlState>(() => readUrlState(RELEASE_URL_CODECS));
  const [action, setAction] = useState<ReleaseAction>("release.rollout.start");
  const [platform, setPlatform] = useState("android");
  const [percent, setPercent] = useState("10");
  const [minVersion, setMinVersion] = useState("1.1.0");
  const [observationHours, setObservationHours] = useState("24");
  const [rollbackCandidate, setRollbackCandidate] = useState("");
  const [formError, setFormError] = useState("");
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => subscribeToUrlState<ReleaseUrlState>(RELEASE_URL_CODECS, setUrlState), []);

  const loadCandidates = useCallback((signal: AbortSignal) => fetchReleaseCandidates({ signal }), []);
  const candidates = useRouteResource("release-candidates-v2", loadCandidates, { enabled: true, pollMs: 60_000 });
  const selectedCandidate = useMemo(
    () => candidates.data?.items.find((item) => item.candidate_id === urlState.candidate) || null,
    [candidates.data, urlState.candidate],
  );

  useEffect(() => {
    if (!candidates.data?.items.length || selectedCandidate) return;
    replaceUrlState<ReleaseUrlState>({ candidate: candidates.data.items[0].candidate_id }, RELEASE_URL_CODECS);
  }, [candidates.data, selectedCandidate]);

  const loadCockpit = useCallback(
    (signal: AbortSignal) => {
      if (!urlState.candidate) throw new Error("Кандидат релиза не выбран.");
      return fetchReleaseCockpit(urlState.candidate, { signal });
    },
    [urlState.candidate],
  );
  const cockpit = useRouteResource(
    `release-cockpit:${urlState.candidate || "none"}`,
    loadCockpit,
    { enabled: Boolean(urlState.candidate), pollMs: 60_000 },
  );

  useEffect(() => {
    const errors = [candidates.error, cockpit.error].filter(Boolean);
    const hasData = Boolean(candidates.data || cockpit.data);
    const observed = cockpit.data?.readiness.origins
      .flatMap((origin) => origin.checks.map((check) => check.observed_at).filter((value): value is string => Boolean(value)))
      .sort() || [];
    onShellStatus?.({
      api: errors.length ? hasData ? "degraded" : "failed" : candidates.loading || cockpit.loading ? "missing" : "ok",
      session: errors.some((error) => isAccessDenied(error)) ? "failed" : hasData ? "ok" : errors.length ? "unavailable" : "missing",
      oldestRequiredSourceAt: observed[0] || null,
    });
  }, [candidates.data, candidates.error, candidates.loading, cockpit.data, cockpit.error, cockpit.loading, onShellStatus]);

  const candidate = cockpit.data?.candidate || selectedCandidate;
  const origins = cockpit.data?.readiness.origins || [];
  const rollout = cockpit.data?.rollout.states.find((item) => item.platform === platform) || null;
  const adoption = cockpit.data?.adoption.cohorts.find(
    (item) => item.platform === platform && item.app_version === candidate?.version,
  );

  function submitAction(event: FormEvent) {
    event.preventDefault();
    if (!candidate) return;
    const payload: Record<string, unknown> = { platform };
    const numericPercent = Number(percent);
    if (action === "release.rollout.start" || action === "release.rollout.change") {
      if (!Number.isInteger(numericPercent) || numericPercent < 1 || numericPercent > 100) {
        setFormError("Процент rollout должен быть целым числом от 1 до 100.");
        return;
      }
      payload.rollout_percent = numericPercent;
    }
    if (action === "release.rollout.start" || action === "release.min_supported.set") {
      if (!/^[0-9A-Za-z][0-9A-Za-z._+-]{0,63}$/.test(minVersion.trim())) {
        setFormError("Укажите корректную минимальную версию.");
        return;
      }
      payload.min_supported_version = minVersion.trim();
    }
    if (action === "release.rollout.start") {
      const hours = Number(observationHours);
      if (!Number.isInteger(hours) || hours < 1 || hours > 168) {
        setFormError("Окно наблюдения должно быть от 1 до 168 часов.");
        return;
      }
      payload.observation_hours = hours;
      payload.thresholds = { crash_failures: 0, connect_failures: 0, update_failures: 0 };
    }
    if (action === "release.rollout.rollback") {
      if (!/^[0-9a-f]{64}$/.test(rollbackCandidate.trim())) {
        setFormError("Для rollback нужен точный candidate ID из 64 hex-символов.");
        return;
      }
      payload.rollback_candidate_id = rollbackCandidate.trim();
    }
    setFormError("");
    setRequest({
      action,
      target: { type: "release_candidate", id: candidate.candidate_id },
      payload,
      endpoint: "/api/admin/v2/releases/action-intents",
      method: "POST",
      workspace: "releases",
    });
    setDialogOpen(true);
  }

  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone={cockpit.data ? statusTone(cockpit.data.gate_matrix.status) : cockpit.error ? "warning" : "neutral"}>
            {cockpit.data ? `Release gates: ${statusText(cockpit.data.gate_matrix.status)}` : cockpit.error ? "Release cockpit недоступен" : "Кандидат не выбран"}
          </Badge>
          <span>Rollout и health считаются backend; браузер их не выводит сам.</span>
        </div>
        <Button tone="secondary" disabled={candidates.refreshing || cockpit.refreshing} onClick={() => { candidates.reload(); cockpit.reload(); }}>
          <RefreshCw size={15} className={candidates.refreshing || cockpit.refreshing ? "animate-spin" : ""} /> Обновить
        </Button>
      </div>

      <MetricStrip label="Release cockpit">
        <MetricCell icon={<Boxes size={17} />} label="Компоненты" value={cockpit.data?.components.length ?? <MissingData />} detail="Точные revisions одной версии" tone="info" />
        <MetricCell icon={<ShieldCheck size={17} />} label="Release gates" value={cockpit.data ? statusText(cockpit.data.gate_matrix.status) : <MissingData />} detail="Origins + client/core/backend/admin proofs" tone={cockpit.data ? statusTone(cockpit.data.gate_matrix.status) : "neutral"} />
        <MetricCell icon={<Gauge size={17} />} label={`Rollout · ${platform}`} value={rollout ? `${rollout.rollout_percent}%` : <MissingData />} detail={rollout?.status || "Состояние не создано"} tone={rollout?.paused ? "warning" : rollout ? "success" : "neutral"} />
        <MetricCell icon={<Activity size={17} />} label="Health gate" value={cockpit.data ? statusText(cockpit.data.health_gate.status) : <MissingData />} detail={cockpit.data?.health_gate.reason || "Нет среза"} tone={cockpit.data ? statusTone(cockpit.data.health_gate.status) : "neutral"} />
      </MetricStrip>

      <div className="ops-workspace xl:grid-cols-[minmax(18rem,0.34fr)_minmax(0,0.66fr)]">
        <Card>
          <SectionTitle title="Кандидаты" description="Импортированный server-owned список. Выбор хранится в URL." />
          <RouteBoundary loading={candidates.loading} refreshing={candidates.refreshing} error={candidates.error} hasData={candidates.data !== null} retryLabel="Повторить список" onRetry={candidates.reload}>
            <div className="grid gap-2">
              {candidates.data?.items.length ? candidates.data.items.map((item) => (
                <CandidateButton key={item.candidate_id} candidate={item} selected={item.candidate_id === urlState.candidate} />
              )) : candidates.data ? <EmptyState title="Кандидатов нет" description="Отсутствие кандидата не считается готовностью." /> : null}
            </div>
          </RouteBoundary>
        </Card>

        <Card>
          <SectionTitle title={candidate ? `${candidate.component} · ${candidate.version}` : "Кандидат"} description="Exact commits, artifacts и release evidence без подмены пропусков PASS-статусом." />
          <RouteBoundary loading={cockpit.loading} refreshing={cockpit.refreshing} error={cockpit.error} hasData={cockpit.data !== null} retryLabel="Повторить cockpit" onRetry={cockpit.reload}>
            {cockpit.data && candidate ? (
              <div className="space-y-4">
                <div className="grid gap-2 lg:grid-cols-2">
                  <CopyValue label="candidate ID" value={candidate.candidate_id} />
                  <CopyValue label="selected artifact SHA-256" value={candidate.artifact_sha256} />
                </div>
                <div className="overflow-x-auto rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)]">
                  <table className="min-w-full text-left text-xs">
                    <thead className="bg-[color:var(--atlas-canvas-alt)] text-[color:var(--atlas-text-muted)]"><tr><th className="p-2">Компонент</th><th className="p-2">Revision</th><th className="p-2">Artifact SHA-256</th></tr></thead>
                    <tbody>{cockpit.data.components.map((item) => <tr key={item.candidate_id} className="border-t border-[color:var(--atlas-border)]"><td className="p-2 font-semibold">{item.component}</td><td className="max-w-48 truncate p-2 font-mono" title={item.revision}>{item.revision}</td><td className="max-w-48 truncate p-2 font-mono" title={item.artifact_sha256}>{item.artifact_sha256}</td></tr>)}</tbody>
                  </table>
                </div>
                <p className="text-[11px] text-[color:var(--atlas-text-muted)]">Срез: {dateText(cockpit.data.generated_at)} · Матрица evidence: {cockpit.data.readiness.required_check_matrix_version}</p>
              </div>
            ) : null}
          </RouteBoundary>
        </Card>
      </div>

      <div className="ops-workspace xl:grid-cols-[minmax(0,0.58fr)_minmax(22rem,0.42fr)]">
        <Card>
          <SectionTitle title="Rollout и rollback" description="Каждая команда создаёт preview, требует подтверждение и исполняется один раз. Rollback блокирует новый артефакт, но не изображает внешнее переключение завершённым." />
          <form className="mt-3 space-y-3" onSubmit={submitAction}>
            {formError ? <p role="alert" className="text-xs text-[color:var(--atlas-status-danger-text)]">{formError}</p> : null}
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-xs font-semibold">Команда<select value={action} onChange={(event) => setAction(event.target.value as ReleaseAction)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3">{(Object.keys(ACTION_LABELS) as ReleaseAction[]).map((value) => <option key={value} value={value}>{ACTION_LABELS[value]}</option>)}</select></label>
              <label className="text-xs font-semibold">Платформа<select value={platform} onChange={(event) => setPlatform(event.target.value)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="android">Android</option><option value="windows">Windows</option></select></label>
            </div>
            {action === "release.rollout.start" || action === "release.rollout.change" ? <label className="block text-xs font-semibold">Rollout, %<input value={percent} inputMode="numeric" onChange={(event) => setPercent(event.target.value)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3" /></label> : null}
            {action === "release.rollout.start" || action === "release.min_supported.set" ? <label className="block text-xs font-semibold">Минимальная поддерживаемая версия<input value={minVersion} onChange={(event) => setMinVersion(event.target.value)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 font-mono" /></label> : null}
            {action === "release.rollout.start" ? <label className="block text-xs font-semibold">Окно наблюдения, часов<input value={observationHours} inputMode="numeric" onChange={(event) => setObservationHours(event.target.value)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3" /><span className="mt-1 block font-normal text-[color:var(--atlas-text-muted)]">Порог новых crash/connect/update failures: 0. При неполном evidence старт будет отклонён backend.</span></label> : null}
            {action === "release.rollout.rollback" ? <label className="block text-xs font-semibold">Rollback candidate ID<input value={rollbackCandidate} onChange={(event) => setRollbackCandidate(event.target.value)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 font-mono" /></label> : null}
            <Button tone={action === "release.rollout.rollback" || action === "release.rollout.pause" ? "danger" : "primary"} type="submit" disabled={!candidate}>
              {action === "release.rollout.rollback" ? <RotateCcw size={15} /> : action === "release.rollout.pause" ? <PauseCircle size={15} /> : <ShieldCheck size={15} />} {ACTION_LABELS[action]}
            </Button>
          </form>
        </Card>

        <Card>
          <SectionTitle title="Текущее состояние" description="Registry связан с реальным /api/client/apps. При mismatch или pause выдача update policy закрывается." />
          {rollout ? <dl className="mt-3 grid grid-cols-2 gap-3 text-xs"><dt className="text-[color:var(--atlas-text-muted)]">Статус</dt><dd className="font-semibold">{rollout.status}</dd><dt className="text-[color:var(--atlas-text-muted)]">Rollout</dt><dd className="font-semibold">{rollout.rollout_percent}%</dd><dt className="text-[color:var(--atlas-text-muted)]">Min supported</dt><dd className="font-mono">{rollout.min_supported_version || "—"}</dd><dt className="text-[color:var(--atlas-text-muted)]">Observation ends</dt><dd>{dateText(rollout.observation_ends_at)}</dd><dt className="text-[color:var(--atlas-text-muted)]">Paused</dt><dd>{rollout.paused ? "Да" : "Нет"}</dd></dl> : <EmptyState title="Rollout не создан" description="Начать rollout можно только после PASS всех release gates." />}
          <div className="mt-4 border-t border-[color:var(--atlas-border)] pt-4">
            <p className="text-xs font-semibold">Adoption выбранной версии</p>
            <p className="mt-2 text-2xl font-bold tabular-nums">{adoption ? `${adoption.share_percent}%` : "—"}</p>
            <p className="text-[11px] text-[color:var(--atlas-text-muted)]">{adoption ? `${adoption.observed_installations} активных установок · ${platform}` : "Нет version-bound наблюдений"}</p>
          </div>
        </Card>
      </div>

      <MetricStrip label="Регрессии и поддержка">
        <MetricCell icon={<Smartphone size={17} />} label="Version cohort" value={adoption?.observed_installations ?? <MissingData />} detail={`${platform} · ${candidate?.version || "версия не выбрана"}`} tone="info" />
        <MetricCell icon={<TriangleAlert size={17} />} label="Health groups" value={cockpit.data?.health_gate.groups.length ?? <MissingData />} detail={cockpit.data?.health_gate.reason || "Нет данных"} tone={cockpit.data ? statusTone(cockpit.data.health_gate.status) : "neutral"} />
        <MetricCell icon={<Clock3 size={17} />} label="Support delta" value={cockpit.data ? `${cockpit.data.support_delta.delta >= 0 ? "+" : ""}${cockpit.data.support_delta.delta}` : <MissingData />} detail={cockpit.data ? `${cockpit.data.support_delta.window_hours} ч. · version-bound bundles` : "Нет данных"} tone={cockpit.data && cockpit.data.support_delta.delta > 0 ? "warning" : cockpit.data ? "success" : "neutral"} />
        <MetricCell icon={<TriangleAlert size={17} />} label="Known issues" value={cockpit.data?.known_issues.length ?? <MissingData />} detail="Только выбранная версия" tone={cockpit.data?.known_issues.length ? "warning" : cockpit.data ? "success" : "neutral"} />
      </MetricStrip>

      <Card>
        <SectionTitle title="Evidence по origins" description="current-origin, brain-origin и RU-origin остаются раздельными; skip, attestation и missing не превращаются в PASS." />
        <div className="mt-3 grid gap-3 xl:grid-cols-3">
          {origins.map((origin) => <OriginBlock key={origin.origin} origin={origin} />)}
        </div>
      </Card>

      <ActionIntentDialog
        open={dialogOpen}
        request={request}
        onOpenChange={(open) => { setDialogOpen(open); if (!open) setRequest(null); }}
        onKnownOutcome={() => { cockpit.reload(); candidates.reload(); }}
        onCheckState={cockpit.reload}
      />
    </div>
  );
}
