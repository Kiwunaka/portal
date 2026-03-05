"use client";

import {
  adminCampaignCreate,
  adminCampaignDelete,
  adminCampaignUpdate,
  adminCampaigns,
  adminGiftCodeCreate,
  adminGiftCodes,
  adminPlanCreate,
  adminPlanDelete,
  adminPlanUpdate,
  adminPlans,
  adminPromoCreate,
  adminPromoDelete,
  adminPromoUpdate,
  adminPromos,
  type AdminIncentiveCampaign,
  type AdminGiftCodeRow,
  type AdminPromoRow,
  type PlanCatalogRow,
} from "@/lib/api";
import { CreditCard, Gift, Package, PencilLine, Plus, RefreshCw, Tag, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { fmtRuDate } from "../nav";

function parsePromptBool(raw: string, fallback: boolean): boolean {
  const value = String(raw || "").trim().toLowerCase();
  if (!value) return fallback;
  if (["no", "n", "нет", "не", "0", "false", "off"].includes(value)) return false;
  if (["yes", "y", "да", "1", "true", "on"].includes(value)) return true;
  return fallback;
}

function promoTypeLabel(value: string): string {
  if (String(value).toLowerCase() === "discount") return "скидка";
  if (String(value).toLowerCase() === "days") return "дни";
  return value;
}

function campaignTypeLabel(value: string): string {
  if (String(value).toLowerCase() === "promo") return "промо";
  if (String(value).toLowerCase() === "gift") return "подарок";
  return value;
}

export default function AdminPromosPage() {
  const [promos, setPromos] = useState<AdminPromoRow[]>([]);
  const [giftCodes, setGiftCodes] = useState<AdminGiftCodeRow[]>([]);
  const [plans, setPlans] = useState<PlanCatalogRow[]>([]);
  const [campaigns, setCampaigns] = useState<AdminIncentiveCampaign[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async (): Promise<void> => {
    setError("");
    try {
      const [promoRows, giftRows, planRows, campaignRows] = await Promise.all([adminPromos(120), adminGiftCodes(80), adminPlans(true), adminCampaigns(120)]);
      setPromos(promoRows);
      setGiftCodes(giftRows);
      setPlans(planRows);
      setCampaigns(campaignRows);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка загрузки"));
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const createPromo = async (): Promise<void> => {
    const code = window.prompt("Код промо:", "WELCOME14");
    if (!code?.trim()) return;
    const promoType = window.prompt("Тип (discount/days):", "days");
    const value = Number(window.prompt("Значение:", "14") || 0);
    const uses = Number(window.prompt("Лимит использований:", "100") || 0);
    if (!promoType || !Number.isFinite(value) || !Number.isFinite(uses)) return;
    setBusy(true);
    try {
      await adminPromoCreate({ code: code.trim().toUpperCase(), promo_type: promoType.trim().toLowerCase() === "discount" ? "discount" : "days", value: Math.max(1, Math.floor(value)), uses_left: Math.max(1, Math.floor(uses)) });
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось создать промо"));
    } finally { setBusy(false); }
  };

  const editPromo = async (row: AdminPromoRow): Promise<void> => {
    const value = Number(window.prompt("Новое значение:", String(row.value || 0)) || row.value || 0);
    const uses = Number(window.prompt("Новый лимит:", String(row.uses_left || 0)) || row.uses_left || 0);
    if (!Number.isFinite(value) || !Number.isFinite(uses)) return;
    setBusy(true);
    try {
      await adminPromoUpdate(row.code, { value: Math.max(1, Math.floor(value)), uses_left: Math.max(0, Math.floor(uses)) });
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось обновить промо"));
    } finally { setBusy(false); }
  };

  const deletePromo = async (code: string): Promise<void> => {
    if (!window.confirm(`Удалить промокод ${code}?`)) return;
    setBusy(true);
    try { await adminPromoDelete(code); await load(); } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось удалить промо"));
    } finally { setBusy(false); }
  };

  const createGiftCode = async (): Promise<void> => {
    const cardType = window.prompt("Тип gift-кода (mini/standard/premium):", "standard");
    if (!cardType?.trim()) return;
    setBusy(true);
    try {
      await adminGiftCodeCreate(cardType.trim().toLowerCase() as "mini" | "standard" | "premium");
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось создать gift-код"));
    } finally { setBusy(false); }
  };

  const createPlan = async (): Promise<void> => {
    const code = window.prompt("Код тарифа:", "new_plan");
    if (!code?.trim()) return;
    const label = window.prompt("Название тарифа:", "Новый тариф") || "Новый тариф";
    const amountRub = Number(window.prompt("Цена (RUB):", "299") || 299);
    const amountStars = Number(window.prompt("Цена (Stars):", "299") || 299);
    const days = Number(window.prompt("Дней доступа:", "30") || 30);
    const deviceLimit = Number(window.prompt("Лимит устройств:", "5") || 5);
    setBusy(true);
    try {
      await adminPlanCreate({ code: code.trim(), label: label.trim(), amount_rub: Math.max(1, Math.floor(amountRub || 1)), amount_stars: Math.max(0, Math.floor(amountStars || 0)), days: Math.max(1, Math.floor(days || 1)), device_limit: Math.max(1, Math.floor(deviceLimit || 1)), is_active: true });
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось создать план"));
    } finally { setBusy(false); }
  };

  const createCampaign = async (): Promise<void> => {
    const name = window.prompt("Название кампании:", "Весеннее промо");
    if (!name?.trim()) return;
    const campaignType = window.prompt("Тип (promo/gift):", "promo") || "promo";
    const targetValue = window.prompt("Target value (код promo или card_type gift):", "WELCOME14");
    if (!targetValue?.trim()) return;
    const segment = window.prompt("Сегмент (all/free/paid/manual/active/inactive):", "all") || "all";
    const startsAt = window.prompt("starts_at (ISO, optional):", "") || null;
    const endsAt = window.prompt("ends_at (ISO, optional):", "") || null;
    const maxActivations = Number(window.prompt("Лимит активаций (0 = без лимита):", "0") || 0);
    setBusy(true);
    try {
      await adminCampaignCreate({
        name: name.trim(),
        campaign_type: campaignType.trim().toLowerCase() === "gift" ? "gift" : "promo",
        target_value: targetValue.trim(),
        segment: segment.trim() || "all",
        starts_at: startsAt || null,
        ends_at: endsAt || null,
        max_activations: Math.max(0, Math.floor(maxActivations || 0)),
        auto_disable: true,
        is_active: true,
      });
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось создать кампанию"));
    } finally { setBusy(false); }
  };

  const editCampaign = async (row: AdminIncentiveCampaign): Promise<void> => {
    const name = window.prompt("Название:", row.name || "");
    if (!name?.trim()) return;
    const segment = window.prompt("Сегмент:", row.segment || "all") || "all";
    const startsAt = window.prompt("starts_at (ISO|empty):", row.starts_at || "") || null;
    const endsAt = window.prompt("ends_at (ISO|empty):", row.ends_at || "") || null;
    const maxActivations = Number(window.prompt("max activations:", String(row.max_activations || 0)) || row.max_activations || 0);
    const activeRaw = window.prompt("Активна? (да/нет):", row.is_active ? "да" : "нет") || "";
    setBusy(true);
    try {
      await adminCampaignUpdate(row.id, {
        name: name.trim(),
        segment: segment.trim() || "all",
        starts_at: startsAt || null,
        ends_at: endsAt || null,
        max_activations: Math.max(0, Math.floor(maxActivations || 0)),
        is_active: parsePromptBool(activeRaw, Boolean(row.is_active)),
      });
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось обновить кампанию"));
    } finally { setBusy(false); }
  };

  const deleteCampaign = async (row: AdminIncentiveCampaign): Promise<void> => {
    if (!window.confirm(`Удалить кампанию ${row.name}?`)) return;
    setBusy(true);
    try { await adminCampaignDelete(row.id); await load(); } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось удалить кампанию"));
    } finally { setBusy(false); }
  };

  const togglePlan = async (code: string, current: boolean): Promise<void> => {
    setBusy(true);
    try { await adminPlanUpdate(code, { is_active: !current }); await load(); } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось обновить план"));
    } finally { setBusy(false); }
  };

  const deletePlan = async (code: string): Promise<void> => {
    if (!window.confirm(`Удалить план ${code}?`)) return;
    setBusy(true);
    try { await adminPlanDelete(code); await load(); } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось удалить план"));
    } finally { setBusy(false); }
  };

  const copyText = async (text: string): Promise<void> => {
    try { await navigator.clipboard.writeText(text); } catch { /* noop */ }
  };

  return (
    <section className="space-y-5">
      {/* ── Actions bar ────────────────────────────────── */}
      <div className="glass-card p-4 flex flex-wrap items-center gap-3">
        <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => void createPromo()} disabled={busy}>
          <Plus size={14} /> Промокод
        </button>
        <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => void createGiftCode()} disabled={busy}>
          <Gift size={14} /> Gift-код
        </button>
        <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => void createPlan()} disabled={busy}>
          <CreditCard size={14} /> Тариф
        </button>
        <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => void createCampaign()} disabled={busy}>
          <Package size={14} /> Кампания
        </button>
        <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5 ml-auto" type="button" onClick={() => void load()}>
          <RefreshCw size={14} /> Обновить
        </button>
        {error ? <p className="w-full text-sm text-rose-500">{error}</p> : null}
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        {/* ── Promo codes ──────────────────────────────── */}
        <article className="glass-card p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="stat-icon stat-icon-violet"><Tag size={20} /></div>
          <h2 className="font-display text-xl font-bold">Промокоды</h2>
          </div>
          <div className="space-y-2">
            {promos.length === 0 ? (
              <div className="empty-state"><Tag size={24} /><p className="text-xs">Нет промокодов</p></div>
            ) : null}
            {promos.map((promo) => (
              <div key={promo.code} className="node-card flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <button type="button" className="haptic-tap" onClick={() => void copyText(promo.code)} title="Копировать">
                    <span className="badge badge-violet font-mono">{promo.code}</span>
                  </button>
                  <div>
                    <span className={`badge ${promo.promo_type === "discount" ? "badge-warning" : "badge-info"}`}>{promoTypeLabel(promo.promo_type)}</span>
                    <span className="ml-2 text-xs text-slate-500">значение: <strong>{promo.value}</strong> • использований: <strong>{promo.uses_left}</strong></span>
                  </div>
                </div>
                <div className="flex gap-1.5 flex-shrink-0">
                  <button className="outline-btn rounded-lg px-2 py-1 text-[10px] font-semibold inline-flex items-center gap-1" type="button" onClick={() => void editPromo(promo)} disabled={busy}><PencilLine size={10} /></button>
                  <button className="outline-btn rounded-lg px-2 py-1 text-[10px] font-semibold inline-flex items-center gap-1 text-rose-500" type="button" onClick={() => void deletePromo(promo.code)} disabled={busy}><Trash2 size={10} /></button>
                </div>
              </div>
            ))}
          </div>
        </article>

        {/* ── Gift codes ───────────────────────────────── */}
        <article className="glass-card p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="stat-icon stat-icon-amber"><Gift size={20} /></div>
          <h2 className="font-display text-xl font-bold">Gift-коды</h2>
          </div>
          <div className="space-y-2">
            {giftCodes.length === 0 ? (
              <div className="empty-state"><Gift size={24} /><p className="text-xs">Нет gift-кодов</p></div>
            ) : null}
            {giftCodes.map((gift) => (
              <div key={gift.code} className="node-card flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <button type="button" className="haptic-tap" onClick={() => void copyText(gift.code)} title="Копировать">
                    <span className="badge badge-violet font-mono">{gift.code}</span>
                  </button>
                  <div className="text-xs text-slate-500">
                    <span className={`badge ${gift.card_type === "premium" ? "badge-warning" : gift.card_type === "standard" ? "badge-info" : "badge-success"}`}>{gift.card_type}</span>
                    <span className="ml-2">{gift.days}d</span>
                  </div>
                </div>
                <span className={`badge ${gift.redeemed_at ? "badge-success" : "badge-danger"}`}>
                  {gift.redeemed_at ? fmtRuDate(gift.redeemed_at) : "не использован"}
                </span>
              </div>
            ))}
          </div>
        </article>
      </div>

      {/* ── Campaigns ─────────────────────────────────── */}
      <article className="glass-card p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="stat-icon stat-icon-blue"><Package size={20} /></div>
          <h2 className="font-display text-xl font-bold">Кампании</h2>
        </div>
        <div className="space-y-2">
          {campaigns.length === 0 ? (
            <div className="empty-state"><Package size={24} /><p className="text-xs">Нет кампаний</p></div>
          ) : null}
          {campaigns.map((row) => (
            <div key={row.id} className="node-card flex items-center justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="badge badge-violet">#{row.id}</span>
                  <strong className="text-sm">{row.name}</strong>
                  <span className={`badge ${row.is_active ? "badge-success" : "badge-danger"}`}>{row.is_active ? "активна" : "выкл"}</span>
                  <span className="badge badge-info">{campaignTypeLabel(row.campaign_type)}</span>
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  цель: <strong>{row.target_value}</strong> • сегмент: <strong>{row.segment}</strong> • активации: <strong>{row.activations_count}/{row.max_activations || "∞"}</strong>
                </p>
                <p className="text-[10px] text-slate-400">период: {fmtRuDate(row.starts_at)} → {fmtRuDate(row.ends_at)}</p>
              </div>
              <div className="flex gap-1.5 flex-shrink-0">
                <button className="outline-btn rounded-lg px-2 py-1 text-[10px] font-semibold inline-flex items-center gap-1" type="button" onClick={() => void editCampaign(row)} disabled={busy}><PencilLine size={10} /></button>
                <button className="outline-btn rounded-lg px-2 py-1 text-[10px] font-semibold inline-flex items-center gap-1 text-rose-500" type="button" onClick={() => void deleteCampaign(row)} disabled={busy}><Trash2 size={10} /></button>
              </div>
            </div>
          ))}
        </div>
      </article>

      {/* ── Plans ──────────────────────────────────────── */}
      <article className="glass-card p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="stat-icon stat-icon-emerald"><Package size={20} /></div>
          <h2 className="font-display text-xl font-bold">Тарифы</h2>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {plans.map((plan) => (
            <div key={plan.code} className="stat-card p-4">
              <div className="flex items-center justify-between gap-2 mb-3">
                <span className="badge badge-violet font-mono">{plan.code}</span>
                <button type="button" className={`badge haptic-tap ${plan.is_active ? "badge-success" : "badge-danger"}`} onClick={() => void togglePlan(plan.code, plan.is_active)} disabled={busy}>
                  {plan.is_active ? "активен" : "выключен"}
                </button>
              </div>
              <p className="text-lg font-bold">{plan.label}</p>
              <div className="mt-2 grid grid-cols-3 gap-2 text-center text-xs">
                <div className="rounded-lg bg-white/50 p-1.5 dark:bg-white/5">
                  <p className="text-slate-400">RUB</p>
                  <p className="font-bold">{plan.amount_rub}</p>
                </div>
                <div className="rounded-lg bg-white/50 p-1.5 dark:bg-white/5">
                  <p className="text-slate-400">Stars</p>
                  <p className="font-bold">{plan.amount_stars}</p>
                </div>
                <div className="rounded-lg bg-white/50 p-1.5 dark:bg-white/5">
                  <p className="text-slate-400">Дней</p>
                  <p className="font-bold">{plan.days}</p>
                </div>
              </div>
              <div className="mt-3 flex justify-end">
                <button className="outline-btn rounded-lg px-2.5 py-1 text-[10px] font-semibold inline-flex items-center gap-1 text-rose-500" type="button" onClick={() => void deletePlan(plan.code)} disabled={busy}>
                  <Trash2 size={10} /> Удалить
                </button>
              </div>
            </div>
          ))}
          {plans.length === 0 ? (
            <div className="empty-state col-span-full"><Package size={28} /><p className="text-xs">Нет планов</p></div>
          ) : null}
        </div>
      </article>
    </section>
  );
}
