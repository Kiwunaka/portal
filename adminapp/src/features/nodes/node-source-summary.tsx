"use client";

import { useId, type ReactNode } from "react";

import { StatusBadge } from "@/components/ui/status-badge";
import { OpsTooltip } from "@/components/ui/tooltip";
import type { NodeObservability, RuSourceStatus } from "@/lib/admin-api/nodes";
import { formatSourceAge } from "@/lib/ops-status/presentation";
import type { OpsStatusCode } from "@/lib/ops-status/types";

const REASON_TEXT: Record<string, string> = {
  brain_metrics_fresh: "Метрики Brain свежие и обязательная проверка пройдена",
  brain_metrics_stale: "Метрики Brain старше серверного окна свежести",
  brain_metrics_missing: "Brain ещё не прислал пригодные метрики",
  brain_probe_failed: "Проверка Brain завершилась явным сбоем",
  runtime_fresh: "Текущее состояние панели получено вовремя",
  runtime_stale: "Снимок текущего состояния устарел",
  runtime_missing: "Текущее состояние панели ещё не получено",
  observer_fresh: "Наблюдатель недавно прислал обработанный пакет",
  observer_stale: "Наблюдатель давно не присылал новый пакет",
  observer_missing: "Данных наблюдателя пока нет",
  current_ru_run: "Текущий пригодный запуск из РФ",
  target_pass: "Обязательные стадии для ноды пройдены",
  target_failed: "Одна или несколько обязательных стадий завершились сбоем",
  target_incomplete: "Не все обязательные стадии были выполнены",
  eligible_run_stale: "Последний пригодный результат старше 7 часов",
  eligible_run_missing: "Пригодный запуск ещё не получен",
  target_missing: "В пригодном запуске нет результата этой ноды",
  current_target_missing: "В запуске отсутствует обязательная текущая цель",
  ru_target_missing: "Для ноды ещё нет результата проверки из РФ",
  google_unavailable: "Google не подтвердил рабочую среду",
  superseded_manifest: "Проверка выполнена по прежней конфигурации целей",
  required_target_incomplete: "Последняя попытка не завершила обязательные проверки",
  required_target_failed: "Обязательная цель завершилась сбоем",
  release_incomplete: "Проверка завершилась не полностью",
  release_failed: "Проверка завершилась сбоем",
  not_in_scope: "Нода сейчас не входит в обязательный RU-контур",
  blocked_by_access: "Есть подписанное доказательство отсутствия доступа"
};

export function reasonText(reasonCode: string | null | undefined): string {
  const code = String(reasonCode || "").trim();
  return REASON_TEXT[code] || "Причина не расшифрована; откройте технические детали";
}

export function opsStatusFromSource(status: RuSourceStatus | string | null | undefined): OpsStatusCode {
  const normalized = String(status || "").toLowerCase();
  if (normalized === "ok" || normalized === "pass" || normalized === "fresh") return "ok";
  if (normalized === "failed" || normalized === "fail" || normalized === "critical") return "failed";
  if (normalized === "degraded" || normalized === "warning" || normalized === "incomplete") return "degraded";
  if (normalized === "stale") return "stale";
  if (normalized === "unavailable" || normalized === "unavailable_probe_host") return "unavailable";
  if (normalized === "blocked_by_access") return "BLOCKED_BY_ACCESS";
  return "missing";
}

export function formatThreshold(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || !Number.isFinite(seconds)) return "Порог не получен от сервера";
  if (seconds % 3600 === 0) return `Порог свежести: ${seconds / 3600} ч`;
  if (seconds % 60 === 0) return `Порог свежести: ${seconds / 60} мин`;
  return `Порог свежести: ${seconds} сек`;
}

function NodeSourceRow({ source, status, sampledAt, reason, threshold, action }: {
  source: string;
  status: OpsStatusCode;
  sampledAt: string | null;
  reason: ReactNode;
  threshold: string;
  action: ReactNode;
}) {
  const id = useId();
  const safeReason = status === "missing" ? "Нет данных" : status === "unavailable" ? "Недоступно" : reason;
  return (
    <div className="grid min-h-14 grid-cols-[minmax(0,1fr)_auto] items-center gap-3 border-b border-[color:var(--atlas-border)] px-3 py-2 last:border-b-0">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="truncate text-xs font-semibold text-[color:var(--atlas-text)]">{source}</span>
          <StatusBadge status={status} />
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-[color:var(--atlas-text-muted)]">
          <span className="text-[color:var(--atlas-text-soft)]">{safeReason}</span>
          {sampledAt ? <time dateTime={sampledAt}>{formatSourceAge(sampledAt)}</time> : <span>Нет данных</span>}
        </div>
      </div>
      <OpsTooltip id={`${id}-source`} content={reason} source={`Проверка: ${source}`} sampledAt={sampledAt} threshold={threshold} action={action} />
    </div>
  );
}

export function NodeSourceSummary({ data }: { data: NodeObservability }) {
  const current = data.sources.runtime;
  const brain = data.sources.brain_metrics;
  const ru = data.sources.ru_origin;

  return (
    <section aria-labelledby="node-sources-title" className="overflow-hidden rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)]">
      <h3 id="node-sources-title" className="border-b border-[color:var(--atlas-border)] px-3 py-2 text-sm font-semibold">
        Источники состояния
      </h3>
      <NodeSourceRow
        source="Текущий контур"
        status={opsStatusFromSource(current.status)}
        sampledAt={current.sampled_at}
        reason={reasonText(current.reason_code)}
        threshold={formatThreshold(current.threshold_seconds)}
        action="При отклонении сравните панель, dataplane и Observer."
      />
      <NodeSourceRow
        source="Brain-origin"
        status={opsStatusFromSource(brain.status)}
        sampledAt={brain.sampled_at}
        reason={reasonText(brain.reason_code)}
        threshold={formatThreshold(brain.threshold_seconds)}
        action="Проверьте свежесть метрик Brain и последнюю стадию проверки."
      />
      <NodeSourceRow
        source="RU-origin"
        status={opsStatusFromSource(ru.status)}
        sampledAt={ru.sampled_at}
        reason={reasonText(ru.reason_code)}
        threshold={formatThreshold(ru.threshold_seconds)}
        action="Откройте вкладку «Проверки из РФ» и сравните попытку со стадиями."
      />
      <details className="border-t border-[color:var(--atlas-border)] px-3 py-2 text-xs text-[color:var(--atlas-text-soft)]">
        <summary className="cursor-pointer select-none font-semibold text-[color:var(--atlas-text)]">Технические коды источников</summary>
        <dl className="mt-2 grid gap-1 font-mono text-[11px]">
          <div><dt className="inline text-[color:var(--atlas-text-muted)]">current: </dt><dd className="inline">{current.reason_code}</dd></div>
          <div><dt className="inline text-[color:var(--atlas-text-muted)]">brain: </dt><dd className="inline">{brain.reason_code}</dd></div>
          <div><dt className="inline text-[color:var(--atlas-text-muted)]">ru: </dt><dd className="inline">{ru.reason_code}</dd></div>
        </dl>
      </details>
    </section>
  );
}
