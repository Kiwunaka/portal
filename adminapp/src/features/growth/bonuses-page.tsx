"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Dices, RefreshCw, Save, ShieldCheck, TimerReset } from "lucide-react";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, Progress, SectionTitle } from "@/components/ui";
import type { ActionIntentRequest } from "@/lib/admin-api/actions";
import { AdminApiError } from "@/lib/admin-api/client";
import { fetchBonusConfiguration, type LoyaltyTier, type WheelOutcome } from "@/lib/admin-api/money";
import { useRouteResource } from "@/lib/use-route-resource";

function weightsText(rows: WheelOutcome[]): string {
  return rows.map((row) => `${row.kind}:${row.value}:${row.weight}`).join("\n");
}

function tiersText(rows: LoyaltyTier[]): string {
  return rows.map((row) => `${row.days}:${row.bonus_days}:${row.perk}`).join("\n");
}

function parseWeights(input: string): WheelOutcome[] {
  const rows = input.split(/\r?\n/).map((row) => row.trim()).filter(Boolean).map((row) => {
    const [kindRaw, valueRaw, weightRaw, ...extra] = row.split(":");
    const kind = String(kindRaw || "").trim().toLowerCase();
    const value = Number(valueRaw);
    const weight = Number(weightRaw);
    if (extra.length || !["days", "discount"].includes(kind) || !Number.isInteger(value) || value < 1 || value > 365 || !Number.isInteger(weight) || weight < 1 || weight > 10_000) throw new Error(`Некорректный сектор: ${row}`);
    return { kind, value, weight };
  });
  if (!rows.length || rows.length > 20) throw new Error("Нужно от 1 до 20 секторов.");
  if (new Set(rows.map((row) => `${row.kind}:${row.value}`)).size !== rows.length) throw new Error("Секторы должны быть уникальны.");
  return rows;
}

function parseTiers(input: string): LoyaltyTier[] {
  const rows = input.split(/\r?\n/).map((row) => row.trim()).filter(Boolean).map((row) => {
    const [daysRaw, bonusRaw, ...perkRaw] = row.split(":");
    const days = Number(daysRaw);
    const bonusDays = Number(bonusRaw);
    const perk = perkRaw.join(":").trim();
    if (!Number.isInteger(days) || days < 1 || !Number.isInteger(bonusDays) || bonusDays < 0 || !perk) throw new Error(`Некорректный уровень: ${row}`);
    return { days, bonus_days: bonusDays, perk };
  });
  if (!rows.length) throw new Error("Добавьте хотя бы один уровень лояльности.");
  return rows;
}

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

export function BonusesPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const load = useCallback((signal: AbortSignal) => fetchBonusConfiguration({ signal }), []);
  const resource = useRouteResource("growth-bonuses", load, { enabled: true, pollMs: 60_000 });
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [preset, setPreset] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState<string | null>(null);
  const [weights, setWeights] = useState<string | null>(null);
  const [loyaltyEnabled, setLoyaltyEnabled] = useState<boolean | null>(null);
  const [tiers, setTiers] = useState<string | null>(null);
  const [grantUser, setGrantUser] = useState("");
  const [grantTier, setGrantTier] = useState("");
  const [formError, setFormError] = useState("");

  const effectivePreset = preset ?? resource.data?.wheel.preset ?? "";
  const effectiveCooldown = cooldown ?? String(resource.data?.wheel.cooldown_hours ?? 336);
  const effectiveWeights = weights ?? weightsText(resource.data?.wheel.weights ?? []);
  const effectiveLoyaltyEnabled = loyaltyEnabled ?? resource.data?.loyalty.enabled ?? true;
  const effectiveTiers = tiers ?? tiersText(resource.data?.loyalty.tiers ?? []);
  const effectiveGrantTier = grantTier || String(resource.data?.loyalty.tiers[0]?.days || "");

  useEffect(() => {
    onShellStatus?.({
      api: resource.error ? resource.data ? "degraded" : "failed" : resource.loading ? "missing" : "ok",
      session: isAccessDenied(resource.error) ? "failed" : resource.data ? "ok" : resource.error ? "unavailable" : "missing",
      oldestRequiredSourceAt: resource.updatedAt,
    });
  }, [onShellStatus, resource.data, resource.error, resource.loading, resource.updatedAt]);

  const distribution = useMemo(() => {
    try {
      const parsed = parseWeights(effectiveWeights);
      const sum = parsed.reduce((value, row) => value + row.weight, 0);
      return parsed.map((row) => ({ ...row, percent: sum ? row.weight / sum * 100 : 0 }));
    } catch {
      return [];
    }
  }, [effectiveWeights]);

  function openWheelUpdate() {
    try {
      const parsed = parseWeights(effectiveWeights);
      const hours = Number(effectiveCooldown);
      if (!effectivePreset.trim() || !Number.isInteger(hours) || hours < 1 || hours > 2160) throw new Error("Пресет или cooldown указаны неверно.");
      setFormError("");
      setRequest({ action: "wheel_config.update", target: { type: "config", id: "wheel" }, payload: { preset: effectivePreset.trim(), cooldown_hours: hours, weights: parsed }, endpoint: "/api/admin/wheel-config", method: "PUT", workspace: "growth" });
      setDialogOpen(true);
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Конфигурация колеса некорректна.");
    }
  }

  function openLoyaltyUpdate() {
    try {
      const parsed = parseTiers(effectiveTiers);
      setFormError("");
      setRequest({ action: "loyalty_config.update", target: { type: "config", id: "loyalty" }, payload: { enabled: effectiveLoyaltyEnabled, tiers: parsed }, endpoint: "/api/admin/loyalty-config", method: "PUT", workspace: "growth" });
      setDialogOpen(true);
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Конфигурация лояльности некорректна.");
    }
  }

  function openGrant() {
    const tgId = Number(grantUser);
    const tierDays = Number(effectiveGrantTier);
    if (!Number.isInteger(tgId) || tgId < 1 || !Number.isInteger(tierDays) || tierDays < 1) {
      setFormError("Укажите Telegram ID и существующий уровень лояльности.");
      return;
    }
    setFormError("");
    setRequest({ action: "user.loyalty_grant", target: { type: "user", id: String(tgId) }, payload: { tier_days: tierDays }, endpoint: `/api/admin/users/${tgId}/loyalty/grant`, workspace: "growth" });
    setDialogOpen(true);
  }

  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar"><div className="flex flex-wrap gap-2 text-xs text-[color:var(--atlas-text-soft)]"><Badge tone={resource.error ? "warning" : "info"}>Allowlisted config</Badge><span>Предпросмотр привязан к текущей версии AppSetting; слепая запись заблокирована.</span></div><Button tone="secondary" disabled={resource.loading || resource.refreshing} onClick={() => { setPreset(null); setCooldown(null); setWeights(null); setLoyaltyEnabled(null); setTiers(null); resource.reload(); }}><RefreshCw size={15} className={resource.refreshing ? "animate-spin" : ""} /> Обновить</Button></div>
      <RouteBoundary loading={resource.loading} refreshing={resource.refreshing} error={resource.error} hasData={resource.data !== null} retryLabel="Повторить загрузку бонусов" onRetry={resource.reload}>
        {resource.data ? <div className="grid gap-3 xl:grid-cols-2">
          <Card className="space-y-4">
            <SectionTitle title="Колесо бонусов" description="Формат сектора: kind:value:weight. Допустимые kind — days и discount." />
            <div className="grid gap-3 sm:grid-cols-2"><label className="text-xs font-semibold">Пресет<input aria-label="Пресет колеса" value={effectivePreset} onChange={(event) => setPreset(event.target.value)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3" /></label><label className="text-xs font-semibold">Cooldown, часы<input aria-label="Cooldown колеса" type="number" min={1} max={2160} value={effectiveCooldown} onChange={(event) => setCooldown(event.target.value)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3" /></label></div>
            <label className="block text-xs font-semibold">Секторы<textarea aria-label="Секторы колеса" rows={7} value={effectiveWeights} onChange={(event) => setWeights(event.target.value)} className="mt-1 w-full rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 font-mono text-xs" placeholder={"days:1:50\ndays:3:30\ndiscount:10:20"} /></label>
            <Button tone="primary" onClick={openWheelUpdate}><Save size={15} /> Проверить и сохранить</Button>
            <div className="space-y-3 border-t border-[color:var(--atlas-border)] pt-4"><p className="flex items-center gap-2 text-xs font-semibold"><Dices size={15} /> Распределение веса</p>{distribution.map((row) => <div key={`${row.kind}:${row.value}`}><div className="mb-1 flex justify-between text-xs"><span>{row.kind} · {row.value}</span><strong>{row.percent.toFixed(1)}%</strong></div><Progress value={row.percent} tone="info" /></div>)}</div>
          </Card>

          <div className="space-y-3">
            <Card className="space-y-4"><SectionTitle title="Уровни лояльности" description="Формат: days:bonus_days:perk. Изменение проходит через L2 ActionIntent." /><label className="flex items-center gap-2 text-xs font-semibold"><input type="checkbox" checked={effectiveLoyaltyEnabled} onChange={(event) => setLoyaltyEnabled(event.target.checked)} /> Программа включена</label><textarea aria-label="Уровни лояльности" rows={6} value={effectiveTiers} onChange={(event) => setTiers(event.target.value)} className="w-full rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 font-mono text-xs" placeholder={"30:1:priority_support\n90:3:fast_resync"} /><Button tone="primary" onClick={openLoyaltyUpdate}><TimerReset size={15} /> Проверить и сохранить</Button></Card>
            <Card className="space-y-4"><SectionTitle title="Ручная выдача уровня" description="Сервер перечитает пользователя и проверит существование уровня перед командой." /><div className="grid gap-3 sm:grid-cols-2"><label className="text-xs font-semibold">Telegram ID<input aria-label="Telegram ID для лояльности" inputMode="numeric" value={grantUser} onChange={(event) => setGrantUser(event.target.value)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3" /></label><label className="text-xs font-semibold">Уровень<select aria-label="Уровень лояльности" value={effectiveGrantTier} onChange={(event) => setGrantTier(event.target.value)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3">{resource.data.loyalty.tiers.map((row) => <option key={row.days} value={row.days}>{row.days} дней · +{row.bonus_days}</option>)}</select></label></div><Button tone="danger" onClick={openGrant}><ShieldCheck size={15} /> Подготовить выдачу</Button></Card>
          </div>
          {formError ? <p role="alert" className="xl:col-span-2 text-xs text-[color:var(--atlas-status-danger-text)]">{formError}</p> : null}
        </div> : null}
      </RouteBoundary>
      <ActionIntentDialog open={dialogOpen} request={request} onOpenChange={(open) => { setDialogOpen(open); if (!open) setRequest(null); }} onKnownOutcome={() => { setPreset(null); setCooldown(null); setWeights(null); setLoyaltyEnabled(null); setTiers(null); resource.reload(); }} onCheckState={resource.reload} />
    </div>
  );
}
