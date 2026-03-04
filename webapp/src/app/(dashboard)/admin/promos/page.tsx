"use client";

import {
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
  type AdminGiftCodeRow,
  type AdminPromoRow,
  type PlanCatalogRow,
} from "@/lib/api";
import { useEffect, useState } from "react";
import { fmtRuDate } from "../nav";

export default function AdminPromosPage() {
  const [promos, setPromos] = useState<AdminPromoRow[]>([]);
  const [giftCodes, setGiftCodes] = useState<AdminGiftCodeRow[]>([]);
  const [plans, setPlans] = useState<PlanCatalogRow[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async (): Promise<void> => {
    setError("");
    try {
      const [promoRows, giftRows, planRows] = await Promise.all([adminPromos(120), adminGiftCodes(80), adminPlans(true)]);
      setPromos(promoRows);
      setGiftCodes(giftRows);
      setPlans(planRows);
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
      await adminPromoCreate({
        code: code.trim().toUpperCase(),
        promo_type: promoType.trim().toLowerCase() === "discount" ? "discount" : "days",
        value: Math.max(1, Math.floor(value)),
        uses_left: Math.max(1, Math.floor(uses)),
      });
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось создать промо"));
    } finally {
      setBusy(false);
    }
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
    } finally {
      setBusy(false);
    }
  };

  const deletePromo = async (code: string): Promise<void> => {
    if (!window.confirm(`Удалить промокод ${code}?`)) return;
    setBusy(true);
    try {
      await adminPromoDelete(code);
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось удалить промо"));
    } finally {
      setBusy(false);
    }
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
    } finally {
      setBusy(false);
    }
  };

  const createPlan = async (): Promise<void> => {
    const code = window.prompt("Plan code:", "new_plan");
    if (!code?.trim()) return;
    const label = window.prompt("Label:", "Новый тариф") || "Новый тариф";
    const amountRub = Number(window.prompt("RUB:", "299") || 299);
    const amountStars = Number(window.prompt("Stars:", "299") || 299);
    const days = Number(window.prompt("Days:", "30") || 30);
    const deviceLimit = Number(window.prompt("Device limit:", "5") || 5);
    setBusy(true);
    try {
      await adminPlanCreate({
        code: code.trim(),
        label: label.trim(),
        amount_rub: Math.max(1, Math.floor(amountRub || 1)),
        amount_stars: Math.max(0, Math.floor(amountStars || 0)),
        days: Math.max(1, Math.floor(days || 1)),
        device_limit: Math.max(1, Math.floor(deviceLimit || 1)),
        is_active: true,
      });
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось создать план"));
    } finally {
      setBusy(false);
    }
  };

  const togglePlan = async (code: string, current: boolean): Promise<void> => {
    setBusy(true);
    try {
      await adminPlanUpdate(code, { is_active: !current });
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось обновить план"));
    } finally {
      setBusy(false);
    }
  };

  const deletePlan = async (code: string): Promise<void> => {
    if (!window.confirm(`Удалить план ${code}?`)) return;
    setBusy(true);
    try {
      await adminPlanDelete(code);
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось удалить план"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-4">
      <div className="glass-card p-4">
        <div className="flex flex-wrap gap-2">
          <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void createPromo()} disabled={busy}>
            + Promo
          </button>
          <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void createGiftCode()} disabled={busy}>
            + Gift code
          </button>
          <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void createPlan()} disabled={busy}>
            + Plan
          </button>
          <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void load()}>
            Обновить
          </button>
        </div>
        {error ? <p className="mt-2 text-sm text-rose-500">{error}</p> : null}
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <article className="glass-card p-4 overflow-x-auto">
          <h2 className="mb-2 font-display text-2xl font-semibold">Promo codes</h2>
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="px-2 py-2">Code</th>
                <th className="px-2 py-2">Type</th>
                <th className="px-2 py-2">Value</th>
                <th className="px-2 py-2">Uses</th>
                <th className="px-2 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {promos.map((promo) => (
                <tr key={promo.code} className="border-t border-white/30 dark:border-white/10">
                  <td className="px-2 py-2 font-mono text-xs">{promo.code}</td>
                  <td className="px-2 py-2">{promo.promo_type}</td>
                  <td className="px-2 py-2">{promo.value}</td>
                  <td className="px-2 py-2">{promo.uses_left}</td>
                  <td className="px-2 py-2">
                    <div className="flex gap-2">
                      <button className="outline-btn rounded-xl px-2 py-1 text-xs font-semibold" type="button" onClick={() => void editPromo(promo)} disabled={busy}>
                        edit
                      </button>
                      <button className="outline-btn rounded-xl px-2 py-1 text-xs font-semibold" type="button" onClick={() => void deletePromo(promo.code)} disabled={busy}>
                        delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>

        <article className="glass-card p-4 overflow-x-auto">
          <h2 className="mb-2 font-display text-2xl font-semibold">Gift codes</h2>
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="px-2 py-2">Code</th>
                <th className="px-2 py-2">Type</th>
                <th className="px-2 py-2">Days</th>
                <th className="px-2 py-2">Redeemed</th>
              </tr>
            </thead>
            <tbody>
              {giftCodes.map((gift) => (
                <tr key={gift.code} className="border-t border-white/30 dark:border-white/10">
                  <td className="px-2 py-2 font-mono text-xs">{gift.code}</td>
                  <td className="px-2 py-2">{gift.card_type}</td>
                  <td className="px-2 py-2">{gift.days}</td>
                  <td className="px-2 py-2">{gift.redeemed_at ? fmtRuDate(gift.redeemed_at) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>
      </div>

      <article className="glass-card p-4 overflow-x-auto">
        <h2 className="mb-2 font-display text-2xl font-semibold">Plans</h2>
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="px-2 py-2">Code</th>
              <th className="px-2 py-2">Label</th>
              <th className="px-2 py-2">RUB</th>
              <th className="px-2 py-2">Stars</th>
              <th className="px-2 py-2">Days</th>
              <th className="px-2 py-2">State</th>
              <th className="px-2 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {plans.map((plan) => (
              <tr key={plan.code} className="border-t border-white/30 dark:border-white/10">
                <td className="px-2 py-2 font-mono text-xs">{plan.code}</td>
                <td className="px-2 py-2">{plan.label}</td>
                <td className="px-2 py-2">{plan.amount_rub}</td>
                <td className="px-2 py-2">{plan.amount_stars}</td>
                <td className="px-2 py-2">{plan.days}</td>
                <td className="px-2 py-2">
                  <button
                    className={`rounded-full px-2 py-1 text-xs ${plan.is_active ? "bg-emerald-500/20 text-emerald-600" : "bg-slate-500/20 text-slate-500"}`}
                    type="button"
                    onClick={() => void togglePlan(plan.code, plan.is_active)}
                    disabled={busy}
                  >
                    {plan.is_active ? "active" : "disabled"}
                  </button>
                </td>
                <td className="px-2 py-2">
                  <button className="outline-btn rounded-xl px-2 py-1 text-xs font-semibold" type="button" onClick={() => void deletePlan(plan.code)} disabled={busy}>
                    delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>
    </section>
  );
}
