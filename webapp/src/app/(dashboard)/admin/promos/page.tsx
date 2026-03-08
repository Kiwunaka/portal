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
import { Check, CreditCard, Gift, Package, PencilLine, Plus, RefreshCw, Tag, Trash2, X } from "lucide-react";
import { useEffect, useState } from "react";
import { fmtRuDate } from "../nav";

type PromoDialog =
  | { kind: "createPromo"; code: string; promoType: "discount" | "days"; value: string; usesLeft: string }
  | { kind: "editPromo"; code: string; promoType: "discount" | "days"; value: string; usesLeft: string }
  | { kind: "deletePromo"; code: string }
  | { kind: "createGift"; cardType: "mini" | "standard" | "premium" }
  | { kind: "createPlan"; code: string; label: string; amountRub: string; amountStars: string; days: string; deviceLimit: string }
  | { kind: "deletePlan"; code: string; label: string }
  | {
      kind: "createCampaign";
      name: string;
      campaignType: "promo" | "gift";
      targetValue: string;
      segment: string;
      startsAt: string;
      endsAt: string;
      maxActivations: string;
      isActive: boolean;
    }
  | {
      kind: "editCampaign";
      id: number;
      name: string;
      campaignType: "promo" | "gift";
      targetValue: string;
      segment: string;
      startsAt: string;
      endsAt: string;
      maxActivations: string;
      isActive: boolean;
    }
  | { kind: "deleteCampaign"; id: number; name: string }
  | null;

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

function parseIntSafe(value: string, fallback = 0): number {
  const num = Number(value);
  if (!Number.isFinite(num)) return fallback;
  return Math.floor(num);
}

function normalizeIsoInput(value?: string | null): string {
  const text = String(value || "").trim();
  return text ? text.slice(0, 16) : "";
}

function StatusMessage({ tone, text }: { tone: "success" | "error"; text: string }) {
  const isSuccess = tone === "success";
  return (
    <div className="stat-card p-4 flex items-center gap-3">
      <div className={`stat-icon ${isSuccess ? "stat-icon-emerald" : "stat-icon-rose"}`}>
        {isSuccess ? <Check size={18} /> : <X size={18} />}
      </div>
      <p className={`text-sm font-medium ${isSuccess ? "text-emerald-600 dark:text-emerald-300" : "text-rose-500"}`}>{text}</p>
    </div>
  );
}

export default function AdminPromosPage() {
  const [promos, setPromos] = useState<AdminPromoRow[]>([]);
  const [giftCodes, setGiftCodes] = useState<AdminGiftCodeRow[]>([]);
  const [plans, setPlans] = useState<PlanCatalogRow[]>([]);
  const [campaigns, setCampaigns] = useState<AdminIncentiveCampaign[]>([]);
  const [error, setError] = useState("");
  const [result, setResult] = useState("");
  const [busy, setBusy] = useState(false);
  const [dialog, setDialog] = useState<PromoDialog>(null);

  const load = async (): Promise<void> => {
    setError("");
    try {
      const [promoRows, giftRows, planRows, campaignRows] = await Promise.all([
        adminPromos(120),
        adminGiftCodes(80),
        adminPlans(true),
        adminCampaigns(120),
      ]);
      setPromos(promoRows);
      setGiftCodes(giftRows);
      setPlans(planRows);
      setCampaigns(campaignRows);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось загрузить промо, подарки, тарифы и кампании"));
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const copyText = async (text: string): Promise<void> => {
    try {
      await navigator.clipboard.writeText(text);
      setResult("Скопировано в буфер.");
    } catch {
      setError("Не удалось скопировать код в буфер.");
    }
  };

  const submitDialog = async (): Promise<void> => {
    if (!dialog) return;
    setBusy(true);
    setError("");
    setResult("");
    try {
      if (dialog.kind === "createPromo") {
        if (!dialog.code.trim()) {
          setError("Укажите код промокода.");
          setBusy(false);
          return;
        }
        await adminPromoCreate({
          code: dialog.code.trim().toUpperCase(),
          promo_type: dialog.promoType,
          value: Math.max(1, parseIntSafe(dialog.value, 1)),
          uses_left: Math.max(1, parseIntSafe(dialog.usesLeft, 1)),
        });
        setResult(`Промокод ${dialog.code.trim().toUpperCase()} создан.`);
      } else if (dialog.kind === "editPromo") {
        await adminPromoUpdate(dialog.code, {
          promo_type: dialog.promoType,
          value: Math.max(1, parseIntSafe(dialog.value, 1)),
          uses_left: Math.max(0, parseIntSafe(dialog.usesLeft, 0)),
        });
        setResult(`Промокод ${dialog.code} обновлён.`);
      } else if (dialog.kind === "deletePromo") {
        await adminPromoDelete(dialog.code);
        setResult(`Промокод ${dialog.code} удалён.`);
      } else if (dialog.kind === "createGift") {
        await adminGiftCodeCreate(dialog.cardType);
        setResult(`Gift-код типа ${dialog.cardType} создан.`);
      } else if (dialog.kind === "createPlan") {
        if (!dialog.code.trim() || !dialog.label.trim()) {
          setError("Укажите код и название тарифа.");
          setBusy(false);
          return;
        }
        await adminPlanCreate({
          code: dialog.code.trim(),
          label: dialog.label.trim(),
          amount_rub: Math.max(1, parseIntSafe(dialog.amountRub, 1)),
          amount_stars: Math.max(0, parseIntSafe(dialog.amountStars, 0)),
          days: Math.max(1, parseIntSafe(dialog.days, 1)),
          device_limit: Math.max(1, parseIntSafe(dialog.deviceLimit, 1)),
          is_active: true,
        });
        setResult(`Тариф ${dialog.code.trim()} создан.`);
      } else if (dialog.kind === "deletePlan") {
        await adminPlanDelete(dialog.code);
        setResult(`Тариф ${dialog.code} удалён.`);
      } else if (dialog.kind === "createCampaign") {
        if (!dialog.name.trim() || !dialog.targetValue.trim()) {
          setError("Укажите название и target value кампании.");
          setBusy(false);
          return;
        }
        await adminCampaignCreate({
          name: dialog.name.trim(),
          campaign_type: dialog.campaignType,
          target_value: dialog.targetValue.trim(),
          segment: dialog.segment.trim() || "all",
          starts_at: dialog.startsAt.trim() || null,
          ends_at: dialog.endsAt.trim() || null,
          max_activations: Math.max(0, parseIntSafe(dialog.maxActivations, 0)),
          auto_disable: true,
          is_active: dialog.isActive,
        });
        setResult(`Кампания ${dialog.name.trim()} создана.`);
      } else if (dialog.kind === "editCampaign") {
        if (!dialog.name.trim() || !dialog.targetValue.trim()) {
          setError("Укажите название и target value кампании.");
          setBusy(false);
          return;
        }
        await adminCampaignUpdate(dialog.id, {
          name: dialog.name.trim(),
          segment: dialog.segment.trim() || "all",
          starts_at: dialog.startsAt.trim() || null,
          ends_at: dialog.endsAt.trim() || null,
          max_activations: Math.max(0, parseIntSafe(dialog.maxActivations, 0)),
          is_active: dialog.isActive,
        });
        setResult(`Кампания #${dialog.id} обновлена.`);
      } else if (dialog.kind === "deleteCampaign") {
        await adminCampaignDelete(dialog.id);
        setResult(`Кампания ${dialog.name} удалена.`);
      }
      setDialog(null);
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось выполнить выбранное действие"));
    } finally {
      setBusy(false);
    }
  };

  const togglePlan = async (code: string, current: boolean): Promise<void> => {
    setBusy(true);
    setError("");
    setResult("");
    try {
      await adminPlanUpdate(code, { is_active: !current });
      setResult(`Тариф ${code} ${current ? "отключён" : "включён"}.`);
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось обновить тариф"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-5">
      <article className="glass-card p-4">
        <h2 className="font-display text-xl font-bold">Промо и тарифы без лишней путаницы</h2>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Этот раздел нужен для акций и коммерческих сценариев: промокоды, подарочные коды, тарифы и кампании. Если создаёте новую акцию, обычно путь такой: сначала код или подарок, потом кампания, и только после этого публикация ссылки.
        </p>
      </article>

      <div className="glass-card p-4 flex flex-wrap items-center gap-3">
        <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => setDialog({ kind: "createPromo", code: "WELCOME14", promoType: "days", value: "14", usesLeft: "100" })} disabled={busy}>
          <Plus size={14} /> Промокод
        </button>
        <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => setDialog({ kind: "createGift", cardType: "standard" })} disabled={busy}>
          <Gift size={14} /> Gift-код
        </button>
        <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => setDialog({ kind: "createPlan", code: "new_plan", label: "Новый тариф", amountRub: "299", amountStars: "299", days: "30", deviceLimit: "5" })} disabled={busy}>
          <CreditCard size={14} /> Тариф
        </button>
        <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => setDialog({ kind: "createCampaign", name: "Весеннее промо", campaignType: "promo", targetValue: "WELCOME14", segment: "all", startsAt: "", endsAt: "", maxActivations: "0", isActive: true })} disabled={busy}>
          <Package size={14} /> Кампания
        </button>
        <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5 ml-auto" type="button" onClick={() => void load()} disabled={busy}>
          <RefreshCw size={14} /> Обновить
        </button>
      </div>

      {result ? <StatusMessage tone="success" text={result} /> : null}
      {error ? <StatusMessage tone="error" text={error} /> : null}

      <div className="grid gap-5 xl:grid-cols-2">
        <article className="glass-card p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="stat-icon stat-icon-violet"><Tag size={20} /></div>
            <h2 className="font-display text-xl font-bold">Промокоды</h2>
          </div>
          <p className="mb-4 text-xs text-slate-500">Промокод даёт скидку или бонусные дни. Здесь видно, сколько раз код ещё можно использовать.</p>
          <div className="space-y-2">
            {promos.length === 0 ? <div className="empty-state"><Tag size={24} /><p className="text-xs">Нет промокодов</p></div> : null}
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
                  <button className="outline-btn rounded-lg px-2 py-1 text-[10px] font-semibold inline-flex items-center gap-1" type="button" onClick={() => setDialog({ kind: "editPromo", code: promo.code, promoType: promo.promo_type === "discount" ? "discount" : "days", value: String(promo.value || 0), usesLeft: String(promo.uses_left || 0) })} disabled={busy}>
                    <PencilLine size={10} />
                  </button>
                  <button className="outline-btn rounded-lg px-2 py-1 text-[10px] font-semibold inline-flex items-center gap-1 text-rose-500" type="button" onClick={() => setDialog({ kind: "deletePromo", code: promo.code })} disabled={busy}>
                    <Trash2 size={10} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="glass-card p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="stat-icon stat-icon-amber"><Gift size={20} /></div>
            <h2 className="font-display text-xl font-bold">Gift-коды</h2>
          </div>
          <p className="mb-4 text-xs text-slate-500">Подарочные коды удобно использовать для партнёров, ручных бонусов и акций в канале.</p>
          <div className="space-y-2">
            {giftCodes.length === 0 ? <div className="empty-state"><Gift size={24} /><p className="text-xs">Нет gift-кодов</p></div> : null}
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
                <span className={`badge ${gift.redeemed_at ? "badge-success" : "badge-danger"}`}>{gift.redeemed_at ? fmtRuDate(gift.redeemed_at) : "не использован"}</span>
              </div>
            ))}
          </div>
        </article>
      </div>

      <article className="glass-card p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="stat-icon stat-icon-blue"><Package size={20} /></div>
          <h2 className="font-display text-xl font-bold">Кампании</h2>
        </div>
        <p className="mb-4 text-xs text-slate-500">Кампания связывает код или подарок с сегментом пользователей, сроками и лимитом активаций.</p>
        <div className="space-y-2">
          {campaigns.length === 0 ? <div className="empty-state"><Package size={24} /><p className="text-xs">Нет кампаний</p></div> : null}
          {campaigns.map((row) => (
            <div key={row.id} className="node-card flex items-center justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="badge badge-violet">#{row.id}</span>
                  <strong className="text-sm">{row.name}</strong>
                  <span className={`badge ${row.is_active ? "badge-success" : "badge-danger"}`}>{row.is_active ? "активна" : "выкл"}</span>
                  <span className="badge badge-info">{campaignTypeLabel(row.campaign_type)}</span>
                </div>
                <p className="mt-1 text-xs text-slate-500">цель: <strong>{row.target_value}</strong> • сегмент: <strong>{row.segment}</strong> • активации: <strong>{row.activations_count}/{row.max_activations || "∞"}</strong></p>
                <p className="text-[10px] text-slate-400">период: {fmtRuDate(row.starts_at)} → {fmtRuDate(row.ends_at)}</p>
              </div>
              <div className="flex gap-1.5 flex-shrink-0">
                <button className="outline-btn rounded-lg px-2 py-1 text-[10px] font-semibold inline-flex items-center gap-1" type="button" onClick={() => setDialog({ kind: "editCampaign", id: row.id, name: row.name || "", campaignType: row.campaign_type === "gift" ? "gift" : "promo", targetValue: row.target_value || "", segment: row.segment || "all", startsAt: normalizeIsoInput(row.starts_at), endsAt: normalizeIsoInput(row.ends_at), maxActivations: String(row.max_activations || 0), isActive: Boolean(row.is_active) })} disabled={busy}>
                  <PencilLine size={10} />
                </button>
                <button className="outline-btn rounded-lg px-2 py-1 text-[10px] font-semibold inline-flex items-center gap-1 text-rose-500" type="button" onClick={() => setDialog({ kind: "deleteCampaign", id: row.id, name: row.name || `#${row.id}` })} disabled={busy}>
                  <Trash2 size={10} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </article>

      <article className="glass-card p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="stat-icon stat-icon-emerald"><Package size={20} /></div>
          <h2 className="font-display text-xl font-bold">Тарифы</h2>
        </div>
        <p className="mb-4 text-xs text-slate-500">Здесь лежит каталог тарифов, который видят пользователи при выборе плана.</p>
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
                <div className="rounded-lg bg-white/50 p-1.5 dark:bg-white/5"><p className="text-slate-400">RUB</p><p className="font-bold">{plan.amount_rub}</p></div>
                <div className="rounded-lg bg-white/50 p-1.5 dark:bg-white/5"><p className="text-slate-400">Stars</p><p className="font-bold">{plan.amount_stars}</p></div>
                <div className="rounded-lg bg-white/50 p-1.5 dark:bg-white/5"><p className="text-slate-400">Дней</p><p className="font-bold">{plan.days}</p></div>
              </div>
              <div className="mt-3 flex justify-end">
                <button className="outline-btn rounded-lg px-2.5 py-1 text-[10px] font-semibold inline-flex items-center gap-1 text-rose-500" type="button" onClick={() => setDialog({ kind: "deletePlan", code: plan.code, label: plan.label })} disabled={busy}>
                  <Trash2 size={10} /> Удалить
                </button>
              </div>
            </div>
          ))}
          {plans.length === 0 ? <div className="empty-state col-span-full"><Package size={28} /><p className="text-xs">Нет планов</p></div> : null}
        </div>
      </article>

      {dialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/65 p-4">
          <div className="glass-card w-full max-w-2xl p-5">
            {(dialog.kind === "createPromo" || dialog.kind === "editPromo") ? (
              <>
                <h3 className="font-display text-xl font-semibold">{dialog.kind === "createPromo" ? "Новый промокод" : `Редактирование промокода ${dialog.code}`}</h3>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <input value={dialog.code} onChange={(event) => setDialog((prev) => prev && (prev.kind === "createPromo" || prev.kind === "editPromo") ? { ...prev, code: event.target.value.toUpperCase() } : prev)} readOnly={dialog.kind === "editPromo"} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Код" />
                  <select value={dialog.promoType} onChange={(event) => setDialog((prev) => prev && (prev.kind === "createPromo" || prev.kind === "editPromo") ? { ...prev, promoType: event.target.value as "discount" | "days" } : prev)} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70">
                    <option value="days">Дни</option>
                    <option value="discount">Скидка</option>
                  </select>
                  <input value={dialog.value} onChange={(event) => setDialog((prev) => prev && (prev.kind === "createPromo" || prev.kind === "editPromo") ? { ...prev, value: event.target.value } : prev)} type="number" min={1} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Значение" />
                  <input value={dialog.usesLeft} onChange={(event) => setDialog((prev) => prev && (prev.kind === "createPromo" || prev.kind === "editPromo") ? { ...prev, usesLeft: event.target.value } : prev)} type="number" min={0} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Лимит использований" />
                </div>
              </>
            ) : null}

            {dialog.kind === "createGift" ? (
              <>
                <h3 className="font-display text-xl font-semibold">Новый gift-код</h3>
                <div className="mt-4">
                  <select value={dialog.cardType} onChange={(event) => setDialog({ kind: "createGift", cardType: event.target.value as "mini" | "standard" | "premium" })} className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70">
                    <option value="mini">mini</option>
                    <option value="standard">standard</option>
                    <option value="premium">premium</option>
                  </select>
                </div>
              </>
            ) : null}

            {dialog.kind === "createPlan" ? (
              <>
                <h3 className="font-display text-xl font-semibold">Новый тариф</h3>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <input value={dialog.code} onChange={(event) => setDialog({ ...dialog, code: event.target.value })} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Код" />
                  <input value={dialog.label} onChange={(event) => setDialog({ ...dialog, label: event.target.value })} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Название" />
                  <input value={dialog.amountRub} onChange={(event) => setDialog({ ...dialog, amountRub: event.target.value })} type="number" min={1} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="RUB" />
                  <input value={dialog.amountStars} onChange={(event) => setDialog({ ...dialog, amountStars: event.target.value })} type="number" min={0} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Stars" />
                  <input value={dialog.days} onChange={(event) => setDialog({ ...dialog, days: event.target.value })} type="number" min={1} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Дней" />
                  <input value={dialog.deviceLimit} onChange={(event) => setDialog({ ...dialog, deviceLimit: event.target.value })} type="number" min={1} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Лимит устройств" />
                </div>
              </>
            ) : null}

            {(dialog.kind === "createCampaign" || dialog.kind === "editCampaign") ? (
              <>
                <h3 className="font-display text-xl font-semibold">{dialog.kind === "createCampaign" ? "Новая кампания" : `Редактирование кампании #${dialog.id}`}</h3>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <input value={dialog.name} onChange={(event) => setDialog({ ...dialog, name: event.target.value })} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Название" />
                  <select value={dialog.campaignType} onChange={(event) => setDialog({ ...dialog, campaignType: event.target.value as "promo" | "gift" })} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70">
                    <option value="promo">promo</option>
                    <option value="gift">gift</option>
                  </select>
                  <input value={dialog.targetValue} onChange={(event) => setDialog({ ...dialog, targetValue: event.target.value })} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Target value" />
                  <input value={dialog.segment} onChange={(event) => setDialog({ ...dialog, segment: event.target.value })} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Сегмент" />
                  <input value={dialog.startsAt} onChange={(event) => setDialog({ ...dialog, startsAt: event.target.value })} type="datetime-local" className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" />
                  <input value={dialog.endsAt} onChange={(event) => setDialog({ ...dialog, endsAt: event.target.value })} type="datetime-local" className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" />
                  <input value={dialog.maxActivations} onChange={(event) => setDialog({ ...dialog, maxActivations: event.target.value })} type="number" min={0} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Лимит активаций" />
                  <label className="inline-flex items-center gap-2 rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm text-slate-600 dark:border-violet-500/30 dark:bg-slate-900/70 dark:text-slate-300">
                    <input type="checkbox" checked={dialog.isActive} onChange={(event) => setDialog({ ...dialog, isActive: event.target.checked })} />
                    Активна
                  </label>
                </div>
              </>
            ) : null}

            {dialog.kind === "deletePromo" ? <>
              <h3 className="font-display text-xl font-semibold">Удалить промокод {dialog.code}?</h3>
              <p className="mt-2 text-sm text-slate-500">Код перестанет работать в новых checkout-сценариях.</p>
            </> : null}
            {dialog.kind === "deletePlan" ? <>
              <h3 className="font-display text-xl font-semibold">Удалить тариф {dialog.code}?</h3>
              <p className="mt-2 text-sm text-slate-500">{dialog.label}</p>
            </> : null}
            {dialog.kind === "deleteCampaign" ? <>
              <h3 className="font-display text-xl font-semibold">Удалить кампанию {dialog.name}?</h3>
              <p className="mt-2 text-sm text-slate-500">Это отключит использование кампании в новых сценариях.</p>
            </> : null}

            <div className="mt-5 flex justify-end gap-2">
              <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setDialog(null)} disabled={busy}>
                Отмена
              </button>
              <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void submitDialog()} disabled={busy}>
                {dialog.kind.startsWith("delete") ? "Удалить" : "Сохранить"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
