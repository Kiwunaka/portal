"use client";

import { useMemo, useState } from "react";
import { Activity, CircleDollarSign, RefreshCw, ShieldAlert, UsersRound } from "lucide-react";

import { RouteBoundary } from "@/components/ops/route-boundary";
import { Badge, Button, Card, MetricCell, MetricStrip, SectionTitle, type Tone } from "@/components/ui";
import {
  fetchCommercialCampaigns,
  fetchWinbackPilotDecision,
  type CommercialCampaignRow,
} from "@/lib/admin-api/revenue";
import { useRouteResource } from "@/lib/use-route-resource";

const RECOMMENDATION_LABELS: Record<string, string> = {
  stop: "Остановить",
  continue_collecting: "Собирать данные",
  keep: "Оставить",
  change_copy: "Сменить текст",
  change_audience: "Сменить аудиторию",
  change_benefit: "Сменить выгоду",
  disable: "Выключить",
  owner_review_scale_50: "Владелец решает масштаб до 50",
};

function recommendationTone(value: string): Tone {
  if (value === "stop" || value === "disable") return "danger";
  if (value === "owner_review_scale_50" || value === "keep") return "success";
  return "warning";
}

function formatNumber(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value)
    ? new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 }).format(value)
    : "—";
}

function campaignLabel(row: CommercialCampaignRow): string {
  return `${row.name} · ${row.lifecycle_status} · ${row.public_id || row.id}`;
}

export function WinbackPilotDecisionPanel() {
  const campaignsLoad = useMemo(() => (signal: AbortSignal) => fetchCommercialCampaigns({ signal }), []);
  const campaigns = useRouteResource("commercial-campaigns", campaignsLoad, { enabled: true, pollMs: 60_000 });
  const winbackCampaigns = useMemo(
    () => (campaigns.data?.campaigns || []).filter((row) => row.objective === "winback"),
    [campaigns.data],
  );
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const effectiveId = winbackCampaigns.some((row) => row.id === selectedId)
    ? selectedId
    : winbackCampaigns[0]?.id || null;

  const decisionLoad = useMemo(
    () => (signal: AbortSignal) => fetchWinbackPilotDecision(Number(effectiveId), { signal }),
    [effectiveId],
  );
  const decision = useRouteResource(`winback-pilot-decision:${effectiveId || "none"}`, decisionLoad, {
    enabled: effectiveId !== null,
    pollMs: 60_000,
  });
  const selected = winbackCampaigns.find((row) => row.id === effectiveId) || null;
  const pack = decision.data?.decision || null;
  const guardrails = pack?.guardrails;
  const primary = pack?.primary_metric;
  const quota = guardrails?.quota;

  function reload() {
    campaigns.reload();
    decision.reload();
  }

  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <SectionTitle
          title="Пилот возврата: решение и стоп-краны"
          description="Источник истины — зрелая 30-дневная выручка на единицу ёмкости. Показы и клики остаются диагностикой и не выбирают победителя."
        />
        <Button tone="secondary" disabled={campaigns.loading || decision.loading || decision.refreshing} onClick={reload}>
          <RefreshCw size={15} className={campaigns.refreshing || decision.refreshing ? "animate-spin" : ""} /> Обновить
        </Button>
      </div>

      {winbackCampaigns.length > 1 ? (
        <label className="mb-4 block text-xs font-semibold">
          Кампания
          <select
            aria-label="Пилот возврата"
            value={effectiveId || ""}
            onChange={(event) => setSelectedId(Number(event.target.value))}
            className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"
          >
            {winbackCampaigns.map((row) => <option key={row.id} value={row.id}>{campaignLabel(row)}</option>)}
          </select>
        </label>
      ) : null}

      <RouteBoundary
        loading={campaigns.loading || decision.loading}
        refreshing={campaigns.refreshing || decision.refreshing}
        error={campaigns.error || decision.error}
        hasData={Boolean(selected && pack)}
        retryLabel="Повторить решение пилота"
        onRetry={reload}
      >
        {!winbackCampaigns.length && campaigns.data ? (
          <p className="text-sm text-[color:var(--atlas-text-soft)]">Winback-кампания ещё не создана. Внешний запуск не разрешён.</p>
        ) : selected && pack ? (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone={recommendationTone(pack.recommendation)}>{RECOMMENDATION_LABELS[pack.recommendation] || pack.recommendation}</Badge>
              <Badge tone={selected.policy.activation_allowed ? "success" : "danger"}>{selected.policy.activation_allowed ? "Политика разрешает" : "Политика блокирует"}</Badge>
              <Badge tone={pack.observation_complete ? "success" : "warning"}>{pack.observation_complete ? "Окно закрыто" : "Наблюдение не завершено"}</Badge>
              <span className="font-mono text-[11px] text-[color:var(--atlas-text-muted)]">rev {selected.revision} · {pack.pilot.revision}</span>
            </div>

            <MetricStrip label="Решение пилота">
              <MetricCell icon={<CircleDollarSign size={17} />} label="₽30 / единица ёмкости" value={formatNumber(primary?.value)} detail={primary?.state === "ready" ? "Зрелая серверная проекция" : "Недостаточно зрелых данных"} tone={primary?.state === "ready" ? "success" : "warning"} />
              <MetricCell icon={<UsersRound size={17} />} label="Оплачено / лимит" value={`${quota?.paid_conversions ?? "—"} / ${quota?.paid_cap ?? "—"}`} detail={`Осталось: ${quota?.remaining ?? "—"}`} tone={Number(quota?.remaining || 0) > 0 ? "info" : "danger"} />
              <MetricCell icon={<Activity size={17} />} label="Payment errors" value={guardrails?.payment_errors?.count ?? "—"} detail={`Заказов: ${guardrails?.payment_errors?.order_count ?? "—"}`} tone={Number(guardrails?.payment_errors?.count || 0) > 0 ? "danger" : "success"} />
              <MetricCell icon={<ShieldAlert size={17} />} label="Инциденты / P0–P1" value={`${guardrails?.incidents?.count ?? "—"} / ${guardrails?.support?.p0_p1_count ?? "—"}`} detail="Пересечение окна пилота" tone={Number(guardrails?.incidents?.count || 0) + Number(guardrails?.support?.p0_p1_count || 0) > 0 ? "danger" : "success"} />
            </MetricStrip>

            <div className="grid gap-3 lg:grid-cols-2">
              <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
                <p className="text-xs font-semibold text-[color:var(--atlas-text)]">Стоп-причины</p>
                {pack.automatic_stop_reasons.length ? (
                  <ul className="mt-2 space-y-1 text-xs text-[color:var(--atlas-status-danger-text)]">
                    {pack.automatic_stop_reasons.map((reason) => <li key={reason} className="font-mono">{reason}</li>)}
                  </ul>
                ) : <p className="mt-2 text-xs text-[color:var(--atlas-text-soft)]">Автоматических стоп-причин нет.</p>}
              </div>
              <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
                <p className="text-xs font-semibold text-[color:var(--atlas-text)]">Победитель и масштаб</p>
                {pack.winner ? <p className="mt-2 text-sm">Вариант <strong>{pack.winner.variant}</strong> · {formatNumber(pack.winner.value)}</p> : <p className="mt-2 text-xs text-[color:var(--atlas-text-soft)]">Победитель не выбран: нужны зрелая метрика, holdout и закрытое окно.</p>}
                <p className="mt-2 text-xs text-[color:var(--atlas-text-muted)]">Автомасштаб: запрещён. Максимум после решения владельца: {pack.maximum_owner_review_paid_cap} оплат.</p>
              </div>
            </div>

            <div className="text-xs text-[color:var(--atlas-text-muted)]">
              Holdout: <span className="font-mono">{pack.holdout.state || "insufficient_data"}</span> · action intents: {pack.action_intents.length} · decision SHA: <span className="font-mono">{decision.data?.postmortem.decision_pack_sha256.slice(0, 12)}</span>
            </div>
          </div>
        ) : null}
      </RouteBoundary>
    </Card>
  );
}
