import { Badge, Button, Card } from "@/components/ui";
import { EmptyState } from "@/components/ui/states";
import type {
  RuHistoryRange,
  RuLatest,
  RuNodeStatus,
  RuRunHistory,
  RuRunSummary,
  RuStageResult,
  RuStageStatus
} from "@/lib/admin-api/nodes";
import { formatSourceAge } from "@/lib/ops-status/presentation";

import { opsStatusFromSource, reasonText, sourceStatusText } from "./node-source-summary";

const RANGE_OPTIONS: Array<{ value: RuHistoryRange; label: string }> = [
  { value: "24h", label: "24 часа" },
  { value: "7d", label: "7 дней" },
  { value: "30d", label: "30 дней" },
  { value: "180d", label: "180 дней" }
];

const STAGE_LABELS = {
  dns: "DNS",
  tcp: "TCP",
  tls: "TLS",
  http_large_body: "Большой HTTPS-ответ",
  transport_handshake: "Рукопожатие транспорта"
} as const;

const STAGE_STATUS_TEXT: Record<RuStageStatus, string> = {
  pass: "Пройдено",
  fail: "Сбой",
  not_run: "Не выполнялась",
  not_applicable: "Не требуется"
};

function formatDate(value: string | null): string {
  if (!value) return "Нет данных";
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) return "Нет данных";
  return new Date(timestamp).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}

function runTone(run: RuRunSummary): "success" | "warning" | "danger" | "neutral" {
  if (run.release_verdict === "pass" && run.current_eligible) return "success";
  if (run.release_verdict === "fail") return "danger";
  if (run.release_verdict === "incomplete" || run.release_verdict === "superseded_manifest") return "warning";
  return "neutral";
}

function runLabel(run: RuRunSummary): string {
  if (run.release_verdict === "pass" && run.current_eligible) return "Пригоден";
  if (run.release_verdict === "fail") return "Сбой";
  if (run.release_verdict === "incomplete") return "Неполный";
  if (run.release_verdict === "superseded_manifest") return "Старая конфигурация";
  if (run.release_verdict === "blocked_by_access") return "Доступ заблокирован";
  return "Без текущего вердикта";
}

function latestNotice(latest: RuLatest, nodeStatus: RuNodeStatus): { title: string; detail: string } {
  const attempt = latest.latest_received_attempt;
  const ineligibleReason = String(attempt?.ineligible_reason || attempt?.server_reason || latest.reason_code || "");
  if (!attempt) {
    return { title: "Пригодный запуск ещё не получен", detail: "Нет ни полученной попытки, ни пригодного результата для текущей конфигурации." };
  }
  if (ineligibleReason === "superseded_manifest" || latest.reason_code === "superseded_manifest") {
    return { title: "Последняя попытка выполнена по прежней конфигурации", detail: "Она сохранена в истории, но не подтверждает текущие цели ноды." };
  }
  if (attempt.environment_verdict === "unavailable" || latest.environment_verdict === "unavailable") {
    return { title: "Среда проверки из РФ недоступна", detail: "Google не подтвердил рабочую среду" };
  }
  if (attempt.release_verdict === "incomplete" || ineligibleReason === "required_target_incomplete" || attempt.execution_status === "partial") {
    return { title: "Последняя попытка не завершила обязательные проверки", detail: "Последний пригодный результат показан отдельно и сохраняет исходный возраст." };
  }
  if (nodeStatus.status === "stale") {
    return { title: "Последний пригодный результат старше 7 часов", detail: "Нужен новый независимый запуск из РФ; частое обновление UI не меняет этот порог." };
  }
  return { title: reasonText(nodeStatus.reason_code), detail: "Текущий статус вычислен сервером по обязательным стадиям и действующей конфигурации целей." };
}

function nodeTone(status: RuNodeStatus["status"]): "success" | "warning" | "danger" | "neutral" {
  const normalized = opsStatusFromSource(status);
  if (normalized === "ok") return "success";
  if (normalized === "failed" || normalized === "BLOCKED_BY_ACCESS") return "danger";
  if (normalized === "degraded" || normalized === "stale") return "warning";
  return "neutral";
}

function AttemptSummary({ title, run }: { title: string; run: RuRunSummary | null }) {
  return (
    <article className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-xs font-semibold text-[color:var(--atlas-text-soft)]">{title}</h4>
        {run ? <Badge tone={runTone(run)}>{runLabel(run)}</Badge> : <Badge tone="neutral">Нет данных</Badge>}
      </div>
      <p className="mt-2 text-sm font-semibold">{run ? formatDate(run.finished_at) : "Нет данных"}</p>
      {run?.finished_at ? <p className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">{formatSourceAge(run.finished_at)}</p> : null}
      {run ? (
        <details className="mt-2 text-xs text-[color:var(--atlas-text-soft)]">
          <summary className="cursor-pointer select-none font-semibold text-[color:var(--atlas-text)]">Техническая идентификация попытки</summary>
          <dl className="mt-2 grid gap-1 font-mono text-[11px]">
            <div><dt className="inline text-[color:var(--atlas-text-muted)]">run_id: </dt><dd className="inline">{run.run_id}</dd></div>
            <div><dt className="inline text-[color:var(--atlas-text-muted)]">manifest: </dt><dd className="inline break-all">{run.manifest_revision}</dd></div>
            <div><dt className="inline text-[color:var(--atlas-text-muted)]">execution: </dt><dd className="inline">{run.execution_status}</dd></div>
            <div><dt className="inline text-[color:var(--atlas-text-muted)]">reason: </dt><dd className="inline">{run.ineligible_reason || run.server_reason || "—"}</dd></div>
          </dl>
        </details>
      ) : null}
    </article>
  );
}

function StageCell({ stage }: { stage: RuStageResult }) {
  const tone = stage.status === "pass" ? "success" : stage.status === "fail" ? "danger" : stage.status === "not_run" ? "warning" : "neutral";
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge tone={tone}>{STAGE_STATUS_TEXT[stage.status]}</Badge>
      <span className="tabular-nums text-[color:var(--atlas-text-soft)]">{stage.latency_ms === null ? "—" : `${stage.latency_ms} мс`}</span>
    </div>
  );
}

function HistoryRun({ run }: { run: RuRunSummary }) {
  const target = run.targets?.[0] || null;
  return (
    <details className="border-b border-[color:var(--atlas-border)] last:border-b-0">
      <summary className="cursor-pointer list-none px-3 py-3 marker:hidden">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="text-sm font-semibold">Запуск {formatDate(run.finished_at)}</div>
            <div className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">{run.finished_at ? formatSourceAge(run.finished_at) : "Время не получено"}</div>
          </div>
          <Badge tone={runTone(run)}>{runLabel(run)}</Badge>
        </div>
      </summary>
      <div className="px-3 pb-3">
        {target ? (
          <div className="ops-scrollbar overflow-x-auto rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)]">
            <table className="w-full min-w-[560px] border-collapse text-xs">
              <thead className="bg-[color:var(--pokrov-table-header-bg)] text-left text-[11px] text-[color:var(--atlas-text-soft)]">
                <tr><th className="px-3 py-2">Стадия</th><th className="px-3 py-2">Результат</th></tr>
              </thead>
              <tbody>
                {(Object.keys(STAGE_LABELS) as Array<keyof typeof STAGE_LABELS>).map((key) => (
                  <tr key={key} className="border-t border-[color:var(--atlas-border)]">
                    <th scope="row" className="px-3 py-2 text-left font-semibold">{STAGE_LABELS[key]}</th>
                    <td className="px-3 py-2"><StageCell stage={target.stages[key]} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p className="text-xs text-[color:var(--atlas-text-soft)]">Для этой ноды стадии в кратком ответе отсутствуют.</p>}
        <details className="mt-2 text-xs text-[color:var(--atlas-text-soft)]">
          <summary className="cursor-pointer select-none font-semibold text-[color:var(--atlas-text)]">Технические коды запуска</summary>
          <div className="mt-2 font-mono text-[11px]">run_id: {run.run_id}<br />reason: {target?.reason_code || run.server_reason || run.ineligible_reason || "—"}</div>
        </details>
      </div>
    </details>
  );
}

export function RuHistory({
  latest,
  nodeStatus,
  history,
  range,
  onRangeChange,
  loadingMore,
  loadMoreError,
  onLoadMore
}: {
  latest: RuLatest | null;
  nodeStatus: RuNodeStatus | null;
  history: RuRunHistory | null;
  range: RuHistoryRange;
  onRangeChange: (range: RuHistoryRange) => void;
  loadingMore: boolean;
  loadMoreError: string | null;
  onLoadMore: () => void;
}) {
  const notice = latest && nodeStatus ? latestNotice(latest, nodeStatus) : null;
  return (
    <div className="space-y-3">
      {latest && nodeStatus && notice ? (
        <>
          <Card className="min-h-0">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-sm font-semibold">Текущий RU-origin</h3>
              <Badge tone={nodeTone(nodeStatus.status)}>{nodeStatus.status === "ok" ? "Пригоден" : sourceStatusText(nodeStatus.status)}</Badge>
            </div>
            <p className="mt-3 text-sm font-semibold">{notice.title}</p>
            <p className="mt-1 text-xs leading-5 text-[color:var(--atlas-text-soft)]">{notice.detail}</p>
          </Card>

          <div className="grid gap-3 md:grid-cols-2">
            <AttemptSummary title="Последняя полученная попытка" run={latest.latest_received_attempt} />
            <AttemptSummary title="Последний пригодный результат" run={latest.latest_eligible_run} />
          </div>
        </>
      ) : null}

      {history ? <section aria-label="История проверок из РФ" className="overflow-hidden rounded-[var(--pokrov-radius-panel)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] shadow-[var(--atlas-shadow-soft)]">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[color:var(--atlas-border)] px-3 py-3">
          <div>
            <h3 className="text-sm font-semibold">История проверок из РФ</h3>
            <p className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">Только запуски выбранной ноды; пропущенные стадии не считаются успешными.</p>
          </div>
          <div className="flex flex-wrap gap-1" aria-label="Диапазон истории">
            {RANGE_OPTIONS.map((option) => (
              <Button
                key={option.value}
                tone={range === option.value ? "primary" : "ghost"}
                aria-pressed={range === option.value}
                onClick={() => onRangeChange(option.value)}
              >
                {option.label}
              </Button>
            ))}
          </div>
        </div>
        {history.items.length ? history.items.map((run) => <HistoryRun key={run.run_id} run={run} />) : (
          <div className="p-3"><EmptyState description="В выбранном диапазоне нет сохранённых запусков этой ноды." className="min-h-24" /></div>
        )}
        {history.next_cursor || loadMoreError ? (
          <div className="border-t border-[color:var(--atlas-border)] p-3">
            {loadMoreError ? <p className="mb-2 text-xs text-[color:var(--command-status-danger-text)]">{loadMoreError}</p> : null}
            <Button tone="secondary" disabled={loadingMore} onClick={onLoadMore}>{loadingMore ? "Загружаем…" : "Показать ещё"}</Button>
          </div>
        ) : null}
      </section> : null}
    </div>
  );
}
