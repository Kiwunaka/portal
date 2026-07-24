"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Boxes, Clock3, Copy, RefreshCw, ShieldCheck, TriangleAlert } from "lucide-react";

import { MissingData } from "@/components/ops/missing-data";
import { RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, EmptyState, MetricCell, MetricStrip, SectionTitle, type Tone } from "@/components/ui";
import { AdminApiError } from "@/lib/admin-api/client";
import {
  fetchReleaseCandidates,
  fetchReleaseReadiness,
  type ReleaseCandidateSummary,
  type ReleaseEvidenceCheck,
  type ReleaseEvidenceStatus,
  type ReleaseOriginReadiness,
} from "@/lib/admin-api/control";
import { useRouteResource } from "@/lib/use-route-resource";
import { readUrlState, replaceUrlState, subscribeToUrlState, urlCodecs } from "@/lib/url-state";

type ReleaseUrlState = { candidate: string | null };
const RELEASE_URL_CODECS = { candidate: urlCodecs.optionalString() };

const ORIGIN_LABELS: Record<string, string> = {
  current: "current-origin",
  brain: "brain-origin",
  ru: "RU-origin",
};

function statusTone(status: ReleaseEvidenceStatus): Tone {
  if (status === "PASS") return "success";
  if (status === "FAIL" || status === "BLOCKED_BY_ACCESS") return "danger";
  if (status === "MISSING" || status.startsWith("SKIPPED") || status === "MANUAL_OWNER_TEST" || status === "OPERATOR_ATTESTED") return "warning";
  return "neutral";
}

function statusText(status: ReleaseEvidenceStatus): string {
  const labels: Record<string, string> = {
    PASS: "Подтверждено · PASS",
    FAIL: "Сбой · FAIL",
    MANUAL_OWNER_TEST: "Ручная проверка владельца · MANUAL_OWNER_TEST",
    OPERATOR_ATTESTED: "Заверено оператором · OPERATOR_ATTESTED",
    SKIPPED_BY_OWNER: "Пропущено владельцем · SKIPPED_BY_OWNER",
    SKIPPED_BY_OPERATOR: "Пропущено оператором · SKIPPED_BY_OPERATOR",
    BLOCKED_BY_ACCESS: "Доступ заблокирован · BLOCKED_BY_ACCESS",
    NOT_REQUESTED: "Не запрашивалось · NOT_REQUESTED",
    MISSING: "Нет данных · MISSING",
  };
  return labels[status] || status || "Нет данных · MISSING";
}

function dateText(value: string | null): string {
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
      <span className="font-semibold">{candidate.component || "— · Нет данных"} · {candidate.version || "— · Нет данных"}</span>
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
          <p className="mt-1 text-[11px] text-[color:var(--atlas-text-soft)]">{check.required ? "Обязательная проверка" : "Диагностическая проверка"} · {check.reason || "причина не указана"}</p>
        </div>
        <Badge tone={statusTone(check.status)}>{statusText(check.status)}</Badge>
      </div>
      <dl className="mt-3 grid gap-2 text-[11px] sm:grid-cols-2">
        <div><dt className="text-[color:var(--atlas-text-muted)]">Наблюдалось</dt><dd className="mt-0.5 font-semibold">{dateText(check.observed_at)}</dd></div>
        <div><dt className="text-[color:var(--atlas-text-muted)]">RU run ID</dt><dd className="mt-0.5 break-all font-mono">{check.ru_probe_run_id || "— · Нет данных"}</dd></div>
      </dl>
      <div className="mt-2"><CopyValue label="evidence ref" value={check.evidence_ref} /></div>
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
  useEffect(() => subscribeToUrlState<ReleaseUrlState>(RELEASE_URL_CODECS, setUrlState), []);

  const loadCandidates = useCallback((signal: AbortSignal) => fetchReleaseCandidates({ signal }), []);
  const candidates = useRouteResource("release-candidates", loadCandidates, { enabled: true, pollMs: 60_000 });
  const selectedCandidate = useMemo(
    () => candidates.data?.items.find((item) => item.candidate_id === urlState.candidate) || null,
    [candidates.data, urlState.candidate],
  );

  useEffect(() => {
    if (!candidates.data?.items.length) return;
    if (selectedCandidate) return;
    replaceUrlState<ReleaseUrlState>({ candidate: candidates.data.items[0].candidate_id }, RELEASE_URL_CODECS);
  }, [candidates.data, selectedCandidate]);

  const loadReadiness = useCallback(
    (signal: AbortSignal) => {
      if (!urlState.candidate) throw new Error("Кандидат релиза не выбран.");
      return fetchReleaseReadiness(urlState.candidate, { signal });
    },
    [urlState.candidate],
  );
  const readiness = useRouteResource(
    `release-readiness:${urlState.candidate || "none"}`,
    loadReadiness,
    { enabled: Boolean(urlState.candidate), pollMs: 60_000 },
  );

  useEffect(() => {
    const errors = [candidates.error, readiness.error].filter(Boolean);
    const hasData = Boolean(candidates.data || readiness.data);
    const observed = readiness.data?.origins.flatMap((origin) => origin.checks.map((check) => check.observed_at).filter((value): value is string => Boolean(value))).sort() || [];
    onShellStatus?.({
      api: errors.length ? hasData ? "degraded" : "failed" : candidates.loading || readiness.loading ? "missing" : "ok",
      session: errors.some((error) => isAccessDenied(error)) ? "failed" : hasData ? "ok" : errors.length ? "unavailable" : "missing",
      oldestRequiredSourceAt: observed[0] || null,
    });
  }, [candidates.data, candidates.error, candidates.loading, onShellStatus, readiness.data, readiness.error, readiness.loading]);

  const candidate = readiness.data?.candidate || selectedCandidate;
  const origins = readiness.data?.origins || [];
  const requiredAttention = origins
    .flatMap((origin) => origin.checks)
    .filter((check) => check.required && check.status !== "PASS").length;
  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone={candidates.error || readiness.error ? "warning" : readiness.data ? statusTone(readiness.data.status) : "neutral"}>
            {readiness.data ? `Итог backend: ${statusText(readiness.data.status)}` : candidates.error || readiness.error ? "Источник релизов недоступен" : "Релиз ещё не выбран"}
          </Badge>
          <span>Итог не вычисляется в браузере.</span>
        </div>
        <Button tone="secondary" disabled={candidates.refreshing || readiness.refreshing} onClick={() => { candidates.reload(); readiness.reload(); }}>
          <RefreshCw size={15} className={candidates.refreshing || readiness.refreshing ? "animate-spin" : ""} /> Обновить
        </Button>
      </div>

      <MetricStrip label="Сводка готовности релиза">
        <MetricCell icon={<Boxes aria-hidden="true" size={17} />} label="Кандидаты" value={candidates.data ? candidates.data.items.length : <MissingData />} detail="Импортированные backend" tone="info" />
        <MetricCell icon={<ShieldCheck aria-hidden="true" size={17} />} label="Origins PASS" value={readiness.data ? `${origins.filter((origin) => origin.status === "PASS").length} / ${origins.length}` : <MissingData />} detail="current, brain и RU отдельно" tone={readiness.data && origins.length > 0 && origins.every((origin) => origin.status === "PASS") ? "success" : readiness.data ? "warning" : "neutral"} />
        <MetricCell icon={<TriangleAlert aria-hidden="true" size={17} />} label="Требуют доказательств" value={readiness.data ? requiredAttention : <MissingData />} detail="Обязательные проверки не PASS" tone={requiredAttention ? "warning" : readiness.data ? "success" : "neutral"} />
        <MetricCell icon={<Clock3 aria-hidden="true" size={17} />} label="Возраст кандидата" value={candidate ? ageText(candidate.age_seconds) : <MissingData />} detail={candidate?.component || "Кандидат не выбран"} tone="neutral" />
      </MetricStrip>

      <div className="ops-workspace xl:grid-cols-[minmax(19rem,0.4fr)_minmax(0,1fr)]">
        <Card>
          <SectionTitle title="Кандидаты релиза" description="Точная версия, revision, artifact hash и возраст импорта. Выбор сохраняется в URL." />
          <RouteBoundary loading={candidates.loading} refreshing={candidates.refreshing} error={candidates.error} hasData={candidates.data !== null} retryLabel="Повторить список" onRetry={candidates.reload}>
            <div className="grid gap-2">
              {candidates.data?.items.length ? candidates.data.items.map((item) => <CandidateButton key={item.candidate_id} candidate={item} selected={item.candidate_id === urlState.candidate} />) : candidates.data ? <EmptyState title="Кандидатов нет" description="Backend не вернул ни одного импортированного кандидата. Это не успешная готовность." /> : null}
            </div>
          </RouteBoundary>
        </Card>

        <Card>
          <SectionTitle title={candidate ? `${candidate.component} · ${candidate.version}` : "Готовность кандидата"} description="current-origin, brain-origin и RU-origin показаны независимо. Пропуск, attestation, блокировка доступа и отсутствие данных не окрашиваются как успех." />
          <RouteBoundary loading={readiness.loading} refreshing={readiness.refreshing} error={readiness.error} hasData={readiness.data !== null} retryLabel="Повторить готовность" onRetry={readiness.reload}>
            {readiness.data && candidate ? (
              <div className="space-y-4">
                <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
                  <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] p-3"><p className="text-[11px] text-[color:var(--atlas-text-muted)]">Компонент</p><p className="mt-1 font-semibold">{candidate.component || "— · Нет данных"}</p></div>
                  <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] p-3"><p className="text-[11px] text-[color:var(--atlas-text-muted)]">Версия</p><p className="mt-1 font-semibold">{candidate.version || "— · Нет данных"}</p></div>
                  <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] p-3"><p className="text-[11px] text-[color:var(--atlas-text-muted)]">Возраст</p><p className="mt-1 font-semibold">{ageText(candidate.age_seconds)}</p></div>
                  <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] p-3"><p className="text-[11px] text-[color:var(--atlas-text-muted)]">Итог backend</p><div className="mt-1"><Badge tone={statusTone(readiness.data.status)}>{statusText(readiness.data.status)}</Badge></div></div>
                </div>
                <div className="grid gap-2 lg:grid-cols-2">
                  <CopyValue label="candidate ID" value={readiness.data.candidate_id} />
                  <CopyValue label="artifact SHA-256" value={candidate.artifact_sha256} />
                  <CopyValue label="revision" value={candidate.revision} />
                  <CopyValue label="descriptor SHA-256" value={candidate.descriptor_sha256} />
                </div>
                <p className="text-[11px] text-[color:var(--atlas-text-muted)]">Матрица: {readiness.data.required_check_matrix_version || "— · Нет данных"} · Срез: {dateText(readiness.data.generated_at)}</p>
                <div className="grid gap-3">
                  {readiness.data.origins.map((origin) => <OriginBlock key={origin.origin} origin={origin} />)}
                </div>
              </div>
            ) : urlState.candidate ? null : <EmptyState title="Выберите кандидата" description="Откройте запись слева, чтобы загрузить readiness именно для неё." />}
          </RouteBoundary>
        </Card>
      </div>
    </div>
  );
}
