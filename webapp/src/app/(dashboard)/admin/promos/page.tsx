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
  | { kind: "createPlan"; code: string; label: string; amountRub: string; days: string; deviceLimit: string }
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
  if (String(value).toLowerCase() === "discount") return "СЃРєРёРґРєР°";
  if (String(value).toLowerCase() === "days") return "РґРЅРё";
  return value;
}

function campaignTypeLabel(value: string): string {
  if (String(value).toLowerCase() === "promo") return "РїСЂРѕРјРѕ";
  if (String(value).toLowerCase() === "gift") return "РїРѕРґР°СЂРѕРє";
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
      setError(String((err as { message?: string })?.message || err || "РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РіСЂСѓР·РёС‚СЊ РїСЂРѕРјРѕ, РїРѕРґР°СЂРєРё, С‚Р°СЂРёС„С‹ Рё РєР°РјРїР°РЅРёРё"));
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const copyText = async (text: string): Promise<void> => {
    try {
      await navigator.clipboard.writeText(text);
      setResult("РЎРєРѕРїРёСЂРѕРІР°РЅРѕ РІ Р±СѓС„РµСЂ.");
    } catch {
      setError("РќРµ СѓРґР°Р»РѕСЃСЊ СЃРєРѕРїРёСЂРѕРІР°С‚СЊ РєРѕРґ РІ Р±СѓС„РµСЂ.");
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
          setError("РЈРєР°Р¶РёС‚Рµ РєРѕРґ РїСЂРѕРјРѕРєРѕРґР°.");
          setBusy(false);
          return;
        }
        await adminPromoCreate({
          code: dialog.code.trim().toUpperCase(),
          promo_type: dialog.promoType,
          value: Math.max(1, parseIntSafe(dialog.value, 1)),
          uses_left: Math.max(1, parseIntSafe(dialog.usesLeft, 1)),
        });
        setResult(`РџСЂРѕРјРѕРєРѕРґ ${dialog.code.trim().toUpperCase()} СЃРѕР·РґР°РЅ.`);
      } else if (dialog.kind === "editPromo") {
        await adminPromoUpdate(dialog.code, {
          promo_type: dialog.promoType,
          value: Math.max(1, parseIntSafe(dialog.value, 1)),
          uses_left: Math.max(0, parseIntSafe(dialog.usesLeft, 0)),
        });
        setResult(`РџСЂРѕРјРѕРєРѕРґ ${dialog.code} РѕР±РЅРѕРІР»С‘РЅ.`);
      } else if (dialog.kind === "deletePromo") {
        await adminPromoDelete(dialog.code);
        setResult(`РџСЂРѕРјРѕРєРѕРґ ${dialog.code} СѓРґР°Р»С‘РЅ.`);
      } else if (dialog.kind === "createGift") {
        await adminGiftCodeCreate(dialog.cardType);
        setResult(`Gift-РєРѕРґ С‚РёРїР° ${dialog.cardType} СЃРѕР·РґР°РЅ.`);
      } else if (dialog.kind === "createPlan") {
        if (!dialog.code.trim() || !dialog.label.trim()) {
          setError("РЈРєР°Р¶РёС‚Рµ РєРѕРґ Рё РЅР°Р·РІР°РЅРёРµ С‚Р°СЂРёС„Р°.");
          setBusy(false);
          return;
        }
        await adminPlanCreate({
          code: dialog.code.trim(),
          label: dialog.label.trim(),
          amount_rub: Math.max(1, parseIntSafe(dialog.amountRub, 1)),
          amount_stars: Math.max(0, parseIntSafe(dialog.amountRub, 1)),
          days: Math.max(1, parseIntSafe(dialog.days, 1)),
          device_limit: Math.max(1, parseIntSafe(dialog.deviceLimit, 1)),
          is_active: true,
        });
        setResult(`РўР°СЂРёС„ ${dialog.code.trim()} СЃРѕР·РґР°РЅ.`);
      } else if (dialog.kind === "deletePlan") {
        await adminPlanDelete(dialog.code);
        setResult(`РўР°СЂРёС„ ${dialog.code} СѓРґР°Р»С‘РЅ.`);
      } else if (dialog.kind === "createCampaign") {
        if (!dialog.name.trim() || !dialog.targetValue.trim()) {
          setError("РЈРєР°Р¶РёС‚Рµ РЅР°Р·РІР°РЅРёРµ Рё target value РєР°РјРїР°РЅРёРё.");
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
        setResult(`РљР°РјРїР°РЅРёСЏ ${dialog.name.trim()} СЃРѕР·РґР°РЅР°.`);
      } else if (dialog.kind === "editCampaign") {
        if (!dialog.name.trim() || !dialog.targetValue.trim()) {
          setError("РЈРєР°Р¶РёС‚Рµ РЅР°Р·РІР°РЅРёРµ Рё target value РєР°РјРїР°РЅРёРё.");
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
        setResult(`РљР°РјРїР°РЅРёСЏ #${dialog.id} РѕР±РЅРѕРІР»РµРЅР°.`);
      } else if (dialog.kind === "deleteCampaign") {
        await adminCampaignDelete(dialog.id);
        setResult(`РљР°РјРїР°РЅРёСЏ ${dialog.name} СѓРґР°Р»РµРЅР°.`);
      }
      setDialog(null);
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "РќРµ СѓРґР°Р»РѕСЃСЊ РІС‹РїРѕР»РЅРёС‚СЊ РІС‹Р±СЂР°РЅРЅРѕРµ РґРµР№СЃС‚РІРёРµ"));
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
      setResult(`РўР°СЂРёС„ ${code} ${current ? "РѕС‚РєР»СЋС‡С‘РЅ" : "РІРєР»СЋС‡С‘РЅ"}.`);
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "РќРµ СѓРґР°Р»РѕСЃСЊ РѕР±РЅРѕРІРёС‚СЊ С‚Р°СЂРёС„"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-5">
      <article className="glass-card p-4">
        <h2 className="font-display text-xl font-bold">РџСЂРѕРјРѕ Рё С‚Р°СЂРёС„С‹ Р±РµР· Р»РёС€РЅРµР№ РїСѓС‚Р°РЅРёС†С‹</h2>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Р­С‚РѕС‚ СЂР°Р·РґРµР» РЅСѓР¶РµРЅ РґР»СЏ Р°РєС†РёР№ Рё РєРѕРјРјРµСЂС‡РµСЃРєРёС… СЃС†РµРЅР°СЂРёРµРІ: РїСЂРѕРјРѕРєРѕРґС‹, РїРѕРґР°СЂРѕС‡РЅС‹Рµ РєРѕРґС‹, С‚Р°СЂРёС„С‹ Рё РєР°РјРїР°РЅРёРё. Р•СЃР»Рё СЃРѕР·РґР°С‘С‚Рµ РЅРѕРІСѓСЋ Р°РєС†РёСЋ, РѕР±С‹С‡РЅРѕ РїСѓС‚СЊ С‚Р°РєРѕР№: СЃРЅР°С‡Р°Р»Р° РєРѕРґ РёР»Рё РїРѕРґР°СЂРѕРє, РїРѕС‚РѕРј РєР°РјРїР°РЅРёСЏ, Рё С‚РѕР»СЊРєРѕ РїРѕСЃР»Рµ СЌС‚РѕРіРѕ РїСѓР±Р»РёРєР°С†РёСЏ СЃСЃС‹Р»РєРё.
        </p>
      </article>

      <div className="glass-card p-4 flex flex-wrap items-center gap-3">
        <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => setDialog({ kind: "createPromo", code: "WELCOME14", promoType: "days", value: "14", usesLeft: "100" })} disabled={busy}>
          <Plus size={14} /> РџСЂРѕРјРѕРєРѕРґ
        </button>
        <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => setDialog({ kind: "createGift", cardType: "standard" })} disabled={busy}>
          <Gift size={14} /> Gift-РєРѕРґ
        </button>
        <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => setDialog({ kind: "createPlan", code: "new_plan", label: "РќРѕРІС‹Р№ С‚Р°СЂРёС„", amountRub: "299", days: "30", deviceLimit: "5" })} disabled={busy}>
          <CreditCard size={14} /> РўР°СЂРёС„
        </button>
        <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => setDialog({ kind: "createCampaign", name: "Р’РµСЃРµРЅРЅРµРµ РїСЂРѕРјРѕ", campaignType: "promo", targetValue: "WELCOME14", segment: "all", startsAt: "", endsAt: "", maxActivations: "0", isActive: true })} disabled={busy}>
          <Package size={14} /> РљР°РјРїР°РЅРёСЏ
        </button>
        <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5 ml-auto" type="button" onClick={() => void load()} disabled={busy}>
          <RefreshCw size={14} /> РћР±РЅРѕРІРёС‚СЊ
        </button>
      </div>

      {result ? <StatusMessage tone="success" text={result} /> : null}
      {error ? <StatusMessage tone="error" text={error} /> : null}

      <div className="grid gap-5 xl:grid-cols-2">
        <article className="glass-card p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="stat-icon stat-icon-violet"><Tag size={20} /></div>
            <h2 className="font-display text-xl font-bold">РџСЂРѕРјРѕРєРѕРґС‹</h2>
          </div>
          <p className="mb-4 text-xs text-slate-500">РџСЂРѕРјРѕРєРѕРґ РґР°С‘С‚ СЃРєРёРґРєСѓ РёР»Рё Р±РѕРЅСѓСЃРЅС‹Рµ РґРЅРё. Р—РґРµСЃСЊ РІРёРґРЅРѕ, СЃРєРѕР»СЊРєРѕ СЂР°Р· РєРѕРґ РµС‰С‘ РјРѕР¶РЅРѕ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ.</p>
          <div className="space-y-2">
            {promos.length === 0 ? <div className="empty-state"><Tag size={24} /><p className="text-xs">РќРµС‚ РїСЂРѕРјРѕРєРѕРґРѕРІ</p></div> : null}
            {promos.map((promo) => (
              <div key={promo.code} className="node-card flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <button type="button" className="haptic-tap" onClick={() => void copyText(promo.code)} title="РљРѕРїРёСЂРѕРІР°С‚СЊ">
                    <span className="badge badge-violet font-mono">{promo.code}</span>
                  </button>
                  <div>
                    <span className={`badge ${promo.promo_type === "discount" ? "badge-warning" : "badge-info"}`}>{promoTypeLabel(promo.promo_type)}</span>
                    <span className="ml-2 text-xs text-slate-500">Р·РЅР°С‡РµРЅРёРµ: <strong>{promo.value}</strong> вЂў РёСЃРїРѕР»СЊР·РѕРІР°РЅРёР№: <strong>{promo.uses_left}</strong></span>
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
            <h2 className="font-display text-xl font-bold">Gift-РєРѕРґС‹</h2>
          </div>
          <p className="mb-4 text-xs text-slate-500">РџРѕРґР°СЂРѕС‡РЅС‹Рµ РєРѕРґС‹ СѓРґРѕР±РЅРѕ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ РґР»СЏ РїР°СЂС‚РЅС‘СЂРѕРІ, СЂСѓС‡РЅС‹С… Р±РѕРЅСѓСЃРѕРІ Рё Р°РєС†РёР№ РІ РєР°РЅР°Р»Рµ.</p>
          <div className="space-y-2">
            {giftCodes.length === 0 ? <div className="empty-state"><Gift size={24} /><p className="text-xs">РќРµС‚ gift-РєРѕРґРѕРІ</p></div> : null}
            {giftCodes.map((gift) => (
              <div key={gift.code} className="node-card flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <button type="button" className="haptic-tap" onClick={() => void copyText(gift.code)} title="РљРѕРїРёСЂРѕРІР°С‚СЊ">
                    <span className="badge badge-violet font-mono">{gift.code}</span>
                  </button>
                  <div className="text-xs text-slate-500">
                    <span className={`badge ${gift.card_type === "premium" ? "badge-warning" : gift.card_type === "standard" ? "badge-info" : "badge-success"}`}>{gift.card_type}</span>
                    <span className="ml-2">{gift.days}d</span>
                  </div>
                </div>
                <span className={`badge ${gift.redeemed_at ? "badge-success" : "badge-danger"}`}>{gift.redeemed_at ? fmtRuDate(gift.redeemed_at) : "РЅРµ РёСЃРїРѕР»СЊР·РѕРІР°РЅ"}</span>
              </div>
            ))}
          </div>
        </article>
      </div>

      <article className="glass-card p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="stat-icon stat-icon-blue"><Package size={20} /></div>
          <h2 className="font-display text-xl font-bold">РљР°РјРїР°РЅРёРё</h2>
        </div>
        <p className="mb-4 text-xs text-slate-500">РљР°РјРїР°РЅРёСЏ СЃРІСЏР·С‹РІР°РµС‚ РєРѕРґ РёР»Рё РїРѕРґР°СЂРѕРє СЃ СЃРµРіРјРµРЅС‚РѕРј РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№, СЃСЂРѕРєР°РјРё Рё Р»РёРјРёС‚РѕРј Р°РєС‚РёРІР°С†РёР№.</p>
        <div className="space-y-2">
          {campaigns.length === 0 ? <div className="empty-state"><Package size={24} /><p className="text-xs">РќРµС‚ РєР°РјРїР°РЅРёР№</p></div> : null}
          {campaigns.map((row) => (
            <div key={row.id} className="node-card flex items-center justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="badge badge-violet">#{row.id}</span>
                  <strong className="text-sm">{row.name}</strong>
                  <span className={`badge ${row.is_active ? "badge-success" : "badge-danger"}`}>{row.is_active ? "Р°РєС‚РёРІРЅР°" : "РІС‹РєР»"}</span>
                  <span className="badge badge-info">{campaignTypeLabel(row.campaign_type)}</span>
                </div>
                <p className="mt-1 text-xs text-slate-500">С†РµР»СЊ: <strong>{row.target_value}</strong> вЂў СЃРµРіРјРµРЅС‚: <strong>{row.segment}</strong> вЂў Р°РєС‚РёРІР°С†РёРё: <strong>{row.activations_count}/{row.max_activations || "в€ћ"}</strong></p>
                <p className="text-[10px] text-slate-400">РїРµСЂРёРѕРґ: {fmtRuDate(row.starts_at)} в†’ {fmtRuDate(row.ends_at)}</p>
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
          <h2 className="font-display text-xl font-bold">РўР°СЂРёС„С‹</h2>
        </div>
        <p className="mb-4 text-xs text-slate-500">Р—РґРµСЃСЊ Р»РµР¶РёС‚ РєР°С‚Р°Р»РѕРі С‚Р°СЂРёС„РѕРІ, РєРѕС‚РѕСЂС‹Р№ РІРёРґСЏС‚ РїРѕР»СЊР·РѕРІР°С‚РµР»Рё РїСЂРё РІС‹Р±РѕСЂРµ РїР»Р°РЅР°.</p>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {plans.map((plan) => (
            <div key={plan.code} className="stat-card p-4">
              <div className="flex items-center justify-between gap-2 mb-3">
                <span className="badge badge-violet font-mono">{plan.code}</span>
                <button type="button" className={`badge haptic-tap ${plan.is_active ? "badge-success" : "badge-danger"}`} onClick={() => void togglePlan(plan.code, plan.is_active)} disabled={busy}>
                  {plan.is_active ? "Р°РєС‚РёРІРµРЅ" : "РІС‹РєР»СЋС‡РµРЅ"}
                </button>
              </div>
              <p className="text-lg font-bold">{plan.label}</p>
              <div className="mt-2 grid grid-cols-3 gap-2 text-center text-xs">
                <div className="rounded-lg bg-white/50 p-1.5 dark:bg-white/5"><p className="text-slate-400">RUB</p><p className="font-bold">{plan.amount_rub}</p></div>
                <div className="rounded-lg bg-white/50 p-1.5 dark:bg-white/5"><p className="text-slate-400">Устр.</p><p className="font-bold">{plan.device_limit}</p></div>
                <div className="rounded-lg bg-white/50 p-1.5 dark:bg-white/5"><p className="text-slate-400">Р”РЅРµР№</p><p className="font-bold">{plan.days}</p></div>
              </div>
              <div className="mt-3 flex justify-end">
                <button className="outline-btn rounded-lg px-2.5 py-1 text-[10px] font-semibold inline-flex items-center gap-1 text-rose-500" type="button" onClick={() => setDialog({ kind: "deletePlan", code: plan.code, label: plan.label })} disabled={busy}>
                  <Trash2 size={10} /> РЈРґР°Р»РёС‚СЊ
                </button>
              </div>
            </div>
          ))}
          {plans.length === 0 ? <div className="empty-state col-span-full"><Package size={28} /><p className="text-xs">РќРµС‚ РїР»Р°РЅРѕРІ</p></div> : null}
        </div>
      </article>

      {dialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/65 p-4">
          <div className="glass-card w-full max-w-2xl p-5">
            {(dialog.kind === "createPromo" || dialog.kind === "editPromo") ? (
              <>
                <h3 className="font-display text-xl font-semibold">{dialog.kind === "createPromo" ? "РќРѕРІС‹Р№ РїСЂРѕРјРѕРєРѕРґ" : `Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ РїСЂРѕРјРѕРєРѕРґР° ${dialog.code}`}</h3>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <input value={dialog.code} onChange={(event) => setDialog((prev) => prev && (prev.kind === "createPromo" || prev.kind === "editPromo") ? { ...prev, code: event.target.value.toUpperCase() } : prev)} readOnly={dialog.kind === "editPromo"} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="РљРѕРґ" />
                  <select value={dialog.promoType} onChange={(event) => setDialog((prev) => prev && (prev.kind === "createPromo" || prev.kind === "editPromo") ? { ...prev, promoType: event.target.value as "discount" | "days" } : prev)} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70">
                    <option value="days">Р”РЅРё</option>
                    <option value="discount">РЎРєРёРґРєР°</option>
                  </select>
                  <input value={dialog.value} onChange={(event) => setDialog((prev) => prev && (prev.kind === "createPromo" || prev.kind === "editPromo") ? { ...prev, value: event.target.value } : prev)} type="number" min={1} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Р—РЅР°С‡РµРЅРёРµ" />
                  <input value={dialog.usesLeft} onChange={(event) => setDialog((prev) => prev && (prev.kind === "createPromo" || prev.kind === "editPromo") ? { ...prev, usesLeft: event.target.value } : prev)} type="number" min={0} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Р›РёРјРёС‚ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёР№" />
                </div>
              </>
            ) : null}

            {dialog.kind === "createGift" ? (
              <>
                <h3 className="font-display text-xl font-semibold">РќРѕРІС‹Р№ gift-РєРѕРґ</h3>
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
                <h3 className="font-display text-xl font-semibold">РќРѕРІС‹Р№ С‚Р°СЂРёС„</h3>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <input value={dialog.code} onChange={(event) => setDialog({ ...dialog, code: event.target.value })} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="РљРѕРґ" />
                  <input value={dialog.label} onChange={(event) => setDialog({ ...dialog, label: event.target.value })} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="РќР°Р·РІР°РЅРёРµ" />
                  <input value={dialog.amountRub} onChange={(event) => setDialog({ ...dialog, amountRub: event.target.value })} type="number" min={1} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="RUB" />
                  <input value={dialog.days} onChange={(event) => setDialog({ ...dialog, days: event.target.value })} type="number" min={1} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Р”РЅРµР№" />
                  <input value={dialog.deviceLimit} onChange={(event) => setDialog({ ...dialog, deviceLimit: event.target.value })} type="number" min={1} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Р›РёРјРёС‚ СѓСЃС‚СЂРѕР№СЃС‚РІ" />
                </div>
              </>
            ) : null}

            {(dialog.kind === "createCampaign" || dialog.kind === "editCampaign") ? (
              <>
                <h3 className="font-display text-xl font-semibold">{dialog.kind === "createCampaign" ? "РќРѕРІР°СЏ РєР°РјРїР°РЅРёСЏ" : `Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ РєР°РјРїР°РЅРёРё #${dialog.id}`}</h3>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <input value={dialog.name} onChange={(event) => setDialog({ ...dialog, name: event.target.value })} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="РќР°Р·РІР°РЅРёРµ" />
                  <select value={dialog.campaignType} onChange={(event) => setDialog({ ...dialog, campaignType: event.target.value as "promo" | "gift" })} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70">
                    <option value="promo">promo</option>
                    <option value="gift">gift</option>
                  </select>
                  <input value={dialog.targetValue} onChange={(event) => setDialog({ ...dialog, targetValue: event.target.value })} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Target value" />
                  <input value={dialog.segment} onChange={(event) => setDialog({ ...dialog, segment: event.target.value })} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="РЎРµРіРјРµРЅС‚" />
                  <input value={dialog.startsAt} onChange={(event) => setDialog({ ...dialog, startsAt: event.target.value })} type="datetime-local" className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" />
                  <input value={dialog.endsAt} onChange={(event) => setDialog({ ...dialog, endsAt: event.target.value })} type="datetime-local" className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" />
                  <input value={dialog.maxActivations} onChange={(event) => setDialog({ ...dialog, maxActivations: event.target.value })} type="number" min={0} className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Р›РёРјРёС‚ Р°РєС‚РёРІР°С†РёР№" />
                  <label className="inline-flex items-center gap-2 rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm text-slate-600 dark:border-violet-500/30 dark:bg-slate-900/70 dark:text-slate-300">
                    <input type="checkbox" checked={dialog.isActive} onChange={(event) => setDialog({ ...dialog, isActive: event.target.checked })} />
                    РђРєС‚РёРІРЅР°
                  </label>
                </div>
              </>
            ) : null}

            {dialog.kind === "deletePromo" ? <>
              <h3 className="font-display text-xl font-semibold">РЈРґР°Р»РёС‚СЊ РїСЂРѕРјРѕРєРѕРґ {dialog.code}?</h3>
              <p className="mt-2 text-sm text-slate-500">РљРѕРґ РїРµСЂРµСЃС‚Р°РЅРµС‚ СЂР°Р±РѕС‚Р°С‚СЊ РІ РЅРѕРІС‹С… checkout-СЃС†РµРЅР°СЂРёСЏС….</p>
            </> : null}
            {dialog.kind === "deletePlan" ? <>
              <h3 className="font-display text-xl font-semibold">РЈРґР°Р»РёС‚СЊ С‚Р°СЂРёС„ {dialog.code}?</h3>
              <p className="mt-2 text-sm text-slate-500">{dialog.label}</p>
            </> : null}
            {dialog.kind === "deleteCampaign" ? <>
              <h3 className="font-display text-xl font-semibold">РЈРґР°Р»РёС‚СЊ РєР°РјРїР°РЅРёСЋ {dialog.name}?</h3>
              <p className="mt-2 text-sm text-slate-500">Р­С‚Рѕ РѕС‚РєР»СЋС‡РёС‚ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ РєР°РјРїР°РЅРёРё РІ РЅРѕРІС‹С… СЃС†РµРЅР°СЂРёСЏС….</p>
            </> : null}

            <div className="mt-5 flex justify-end gap-2">
              <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setDialog(null)} disabled={busy}>
                РћС‚РјРµРЅР°
              </button>
              <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void submitDialog()} disabled={busy}>
                {dialog.kind.startsWith("delete") ? "РЈРґР°Р»РёС‚СЊ" : "РЎРѕС…СЂР°РЅРёС‚СЊ"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}

