"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { Gift, KeyRound, RefreshCw, ShieldCheck, Workflow } from "lucide-react";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { MissingData } from "@/components/ops/missing-data";
import { RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, DataTable, EmptyState, MetricCell, MetricStrip, SectionTitle } from "@/components/ui";
import type { ActionIntentRequest } from "@/lib/admin-api/actions";
import { AdminApiError } from "@/lib/admin-api/client";
import { fetchMoneyAccess, type EntitlementGrantRow, type GiftCodeRow } from "@/lib/admin-api/money";
import { useRouteResource } from "@/lib/use-route-resource";

function total(values: Record<string, number> | undefined): number | null {
  if (!values) return null;
  return Object.values(values).reduce((sum, value) => sum + (Number.isFinite(value) ? value : 0), 0);
}

function dateText(value: string | null): string {
  if (!value || Number.isNaN(Date.parse(value))) return "—";
  return new Date(value).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

export function AccessPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const load = useCallback((signal: AbortSignal) => fetchMoneyAccess({ signal }), []);
  const resource = useRouteResource("money-access", load, { enabled: true, pollMs: 60_000 });
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [planCode, setPlanCode] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [giftType, setGiftType] = useState("mini");
  const [formError, setFormError] = useState("");

  useEffect(() => {
    onShellStatus?.({
      api: resource.error ? resource.data ? "degraded" : "failed" : resource.loading ? "missing" : "ok",
      session: isAccessDenied(resource.error) ? "failed" : resource.data ? "ok" : resource.error ? "unavailable" : "missing",
      oldestRequiredSourceAt: resource.data?.generated_at || null,
    });
  }, [onShellStatus, resource.data, resource.error, resource.loading]);

  const grantColumns = useMemo<ColumnDef<EntitlementGrantRow>[]>(() => [
    { header: "Grant", cell: ({ row }) => <span className="font-mono text-[11px]">{row.original.grant_ref}</span> },
    { header: "Источник", cell: ({ row }) => <span>{row.original.source || <MissingData inline />}</span> },
    { header: "Доступ", cell: ({ row }) => <div><strong>{row.original.plan_code || row.original.grant_kind}</strong><span className="block text-[11px] text-[color:var(--atlas-text-muted)]">{row.original.grant_kind}</span></div> },
    { header: "Состояние", cell: ({ row }) => <Badge tone={row.original.status === "active" || row.original.status === "applied" ? "success" : row.original.status === "reversed" ? "danger" : "warning"}>{row.original.status}</Badge> },
    { header: "Создан", cell: ({ row }) => dateText(row.original.created_at) },
  ], []);

  const giftColumns = useMemo<ColumnDef<GiftCodeRow>[]>(() => [
    { header: "Код", cell: ({ row }) => <span className="font-mono">{row.original.code_hint}</span> },
    { header: "Тип", accessorKey: "card_type" },
    { header: "Состояние", cell: ({ row }) => <Badge tone={row.original.redeemed ? "neutral" : "success"}>{row.original.redeemed ? "Погашен" : "Выдан"}</Badge> },
    { header: "Создан", cell: ({ row }) => dateText(row.original.created_at) },
  ], []);

  function issueKeys() {
    const selectedPlanCode = planCode || resource.data?.plans[0]?.code || "";
    const normalizedQuantity = Number(quantity);
    if (!selectedPlanCode || !Number.isInteger(normalizedQuantity) || normalizedQuantity < 1 || normalizedQuantity > 200) {
      setFormError("Выберите план и укажите количество от 1 до 200.");
      return;
    }
    setFormError("");
    setRequest({
      action: "access_key.issue",
      target: { type: "access_key_batch", id: selectedPlanCode },
      payload: { plan_code: selectedPlanCode, quantity: normalizedQuantity },
      endpoint: "/api/admin/access-keys/issue",
      workspace: "money",
    });
    setDialogOpen(true);
  }

  function issueGift() {
    setFormError("");
    setRequest({
      action: "gift_code.create",
      target: { type: "gift_code", id: giftType },
      payload: { card_type: giftType },
      endpoint: "/api/admin/gift-codes",
      workspace: "money",
    });
    setDialogOpen(true);
  }

  const outbox = resource.data?.outbox || {};
  const pendingOutbox = typeof outbox.pending === "number" ? outbox.pending : null;
  const deadLetters = typeof outbox.dead_letter === "number" ? outbox.dead_letter : null;

  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone={resource.error ? "warning" : resource.data ? "success" : "neutral"}>Entitlement authority</Badge>
          <span>Телеметрия не подтверждает оплату; доступ определяется grant и outbox.</span>
        </div>
        <Button tone="secondary" disabled={resource.loading || resource.refreshing} onClick={resource.reload}><RefreshCw size={15} className={resource.refreshing ? "animate-spin" : ""} /> Обновить</Button>
      </div>

      <RouteBoundary loading={resource.loading} refreshing={resource.refreshing} error={resource.error} hasData={resource.data !== null} retryLabel="Повторить загрузку доступа" onRetry={resource.reload}>
        {resource.data ? <div className="space-y-3">
          <MetricStrip label="Контур доступа">
            <MetricCell icon={<ShieldCheck size={17} />} label="Claims" value={total(resource.data.claim_counts) ?? <MissingData />} detail="Платёжные требования" tone="info" />
            <MetricCell icon={<KeyRound size={17} />} label="Grants" value={total(resource.data.grant_counts) ?? <MissingData />} detail="Авторитет доступа" tone="success" />
            <MetricCell icon={<Workflow size={17} />} label="Outbox pending" value={pendingOutbox ?? <MissingData />} detail="Ожидают проекции" tone={Number(pendingOutbox || 0) > 0 ? "warning" : "success"} />
            <MetricCell icon={<Gift size={17} />} label="Dead letter" value={deadLetters ?? <MissingData />} detail="Требуют разбирательства" tone={Number(deadLetters || 0) > 0 ? "danger" : "success"} />
          </MetricStrip>

          <div className="grid gap-3 xl:grid-cols-2">
            <Card>
              <SectionTitle title="Выдать пакет ключей" description="L3: сервер фиксирует план, количество и состояние каталога перед генерацией." />
              <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_8rem_auto] sm:items-end">
                <label className="text-xs font-semibold">План<select aria-label="План ключей" value={planCode || resource.data.plans[0]?.code || ""} onChange={(event) => setPlanCode(event.target.value)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3">{resource.data.plans.map((plan) => <option key={plan.code} value={plan.code}>{plan.label} · {plan.duration_days} дн.</option>)}</select></label>
                <label className="text-xs font-semibold">Количество<input aria-label="Количество ключей" type="number" min={1} max={200} value={quantity} onChange={(event) => setQuantity(event.target.value)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3" /></label>
                <Button tone="danger" onClick={issueKeys}><KeyRound size={15} /> Подготовить</Button>
              </div>
            </Card>
            <Card>
              <SectionTitle title="Создать подарочный код" description="L3: полный код возвращается только результатом подтверждённой команды и не хранится в read model." />
              <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
                <label className="text-xs font-semibold">Тип<select aria-label="Тип подарочного кода" value={giftType} onChange={(event) => setGiftType(event.target.value)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="mini">Mini · 7 дней</option><option value="standard">Standard · 30 дней</option><option value="premium">Premium · 90 дней</option></select></label>
                <Button tone="danger" onClick={issueGift}><Gift size={15} /> Подготовить</Button>
              </div>
            </Card>
          </div>
          {formError ? <p role="alert" className="text-xs text-[color:var(--atlas-status-danger-text)]">{formError}</p> : null}

          <Card><SectionTitle title="Последние entitlement grants" description="Аккаунты и внешние заказы показаны только как непрозрачные ссылки." />{resource.data.recent_grants.length ? <DataTable data={resource.data.recent_grants} columns={grantColumns} empty="Нет grants" /> : <EmptyState description="Entitlement grants ещё не созданы." />}</Card>
          <Card><SectionTitle title="Реестр подарочных кодов" description="Read model не раскрывает полный код; только безопасную подсказку и SHA-256." />{resource.data.gift_codes.length ? <DataTable data={resource.data.gift_codes} columns={giftColumns} empty="Нет подарочных кодов" /> : <EmptyState description="Подарочные коды ещё не выпускались." />}</Card>
        </div> : null}
      </RouteBoundary>

      <ActionIntentDialog open={dialogOpen} request={request} onOpenChange={(open) => { setDialogOpen(open); if (!open) setRequest(null); }} onKnownOutcome={resource.reload} onCheckState={resource.reload} />
    </div>
  );
}
