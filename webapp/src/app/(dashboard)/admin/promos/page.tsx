"use client";

import {
  AdminConfirmDialog,
  AdminBadge,
  AdminMetricStrip,
  AdminPanelHeader,
  adminButtonClass,
  adminFieldClass,
  adminInsetPanelClass,
  adminPanelClass,
  adminTableShellClass,
} from "@/components/admin/admin-shell";
import {
  adminAccessKeysIssue,
  adminPromoSlots,
  adminPromoSlotsUpdate,
  fetchAccessKeyStatus,
  type AccessKeyStatusPayload,
  type PromoSlotAssignmentPayload,
  type PromoSlotCatalogContent,
  type PromoSlotCatalogSlot,
} from "@/lib/api";
import { getAccessMatrix, getPromoSlotsCatalog, getTariffPlans } from "@/lib/portal";
import { useEffect, useMemo, useState } from "react";
import { fmtRuDate } from "../nav";

const ACCESS_MATRIX = getAccessMatrix();
const PROMO_CATALOG = getPromoSlotsCatalog();
const DEFAULT_PROMO_SLOTS: PromoSlotCatalogSlot[] = PROMO_CATALOG.slots.map((slot) => ({
  id: slot.id,
  surface: slot.surface,
  contexts: [...slot.contexts],
  allowed_content_ids: [...slot.allowed_content_ids],
}));
const DEFAULT_PROMO_CONTENT: PromoSlotCatalogContent[] = PROMO_CATALOG.content_catalog.map((item) => ({
  id: item.id,
  kind: item.kind,
  goal: item.goal,
  default_enabled: Boolean(item.default_enabled),
}));
const SHARED_PLANS = getTariffPlans()
  .slice()
  .filter((plan) => Boolean(plan.is_active) && Number(plan.amount_rub || 0) > 0)
  .sort((left, right) => Number(left.sort_order || 0) - Number(right.sort_order || 0))
  .map((plan) => ({
    code: plan.code,
    label: plan.label,
    badge: plan.badge || undefined,
    amountRub: Number(plan.amount_rub || 0),
    days: Number(plan.duration_days || 0),
    deviceLimit: Number(plan.device_limit || 1),
    note: plan.cabinet_note || plan.marketing_note || plan.label,
  }));

type ConfirmState = { kind: "issue" | "slots"; reason: string } | null;

function normalizeKey(value: string): string {
  return String(value || "").trim().toUpperCase();
}

function createAssignmentState(assignments: PromoSlotAssignmentPayload[], slots: PromoSlotCatalogSlot[], contentCatalog: PromoSlotCatalogContent[]): PromoSlotAssignmentPayload[] {
  const assignmentMap = new Map(assignments.map((item) => [item.slot_id, item]));
  const contentMap = new Map(contentCatalog.map((item) => [item.id, item]));

  return slots.map((slot, index) => {
    const existing = assignmentMap.get(slot.id);
    const fallbackContent = slot.allowed_content_ids.find((contentId) => contentMap.has(contentId)) || slot.allowed_content_ids[0] || "";
    const nextContentId = existing && slot.allowed_content_ids.includes(existing.content_id) ? existing.content_id : fallbackContent;
    return {
      slot_id: slot.id,
      content_id: nextContentId,
      enabled: existing?.enabled ?? Boolean(contentMap.get(nextContentId)?.default_enabled),
      title: existing?.title ?? "",
      body: existing?.body ?? "",
      cta_label: existing?.cta_label ?? "",
      cta_href: existing?.cta_href ?? "",
      contexts: existing?.contexts?.length ? [...existing.contexts] : [...slot.contexts],
      sort_order: existing?.sort_order ?? index + 1,
    };
  });
}

export default function AdminPromosPage() {
  const [selectedPlan, setSelectedPlan] = useState(SHARED_PLANS[0]?.code || "1_month");
  const [quantity, setQuantity] = useState("5");
  const [issuedKeys, setIssuedKeys] = useState<Array<{ key: string; planLabel: string; issuedAt?: string | null }>>([]);
  const [lookupKey, setLookupKey] = useState("");
  const [lookupResult, setLookupResult] = useState<AccessKeyStatusPayload | null>(null);
  const [slotCatalog, setSlotCatalog] = useState<PromoSlotCatalogSlot[]>(DEFAULT_PROMO_SLOTS);
  const [contentCatalog, setContentCatalog] = useState<PromoSlotCatalogContent[]>(DEFAULT_PROMO_CONTENT);
  const [assignments, setAssignments] = useState<PromoSlotAssignmentPayload[]>(createAssignmentState([], DEFAULT_PROMO_SLOTS, DEFAULT_PROMO_CONTENT));
  const [remoteVersion, setRemoteVersion] = useState(PROMO_CATALOG.version);
  const [remoteMode, setRemoteMode] = useState(PROMO_CATALOG.mode);
  const [remoteAvailable, setRemoteAvailable] = useState(false);
  const [fallbackBehavior, setFallbackBehavior] = useState(PROMO_CATALOG.fallback_behavior);
  const [loading, setLoading] = useState(false);
  const [issuing, setIssuing] = useState(false);
  const [lookupBusy, setLookupBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [error, setError] = useState("");
  const [confirm, setConfirm] = useState<ConfirmState>(null);

  const contentById = useMemo(() => new Map(contentCatalog.map((item) => [item.id, item])), [contentCatalog]);

  const loadPromoSlots = async (): Promise<void> => {
    setLoading(true);
    setError("");
    try {
      const payload = await adminPromoSlots();
      const remote = payload.promo_slots;
      const remoteCatalog = remote.catalog;
      const nextSlots = remoteCatalog?.slots?.length ? remoteCatalog.slots : DEFAULT_PROMO_SLOTS;
      const nextContent = remoteCatalog?.content_catalog?.length ? remoteCatalog.content_catalog : DEFAULT_PROMO_CONTENT;
      setSlotCatalog(nextSlots);
      setContentCatalog(nextContent);
      setAssignments(createAssignmentState(remote.assignments || [], nextSlots, nextContent));
      setRemoteVersion(String(remote.version || remoteCatalog?.version || PROMO_CATALOG.version));
      setRemoteMode(String(remote.mode || remoteCatalog?.mode || PROMO_CATALOG.mode));
      setRemoteAvailable(Boolean(remote.remote_available));
      setFallbackBehavior(String(remote.fallback_behavior || remoteCatalog?.fallback_behavior || PROMO_CATALOG.fallback_behavior));
      setStatusText("Promo-slot config loaded.");
    } catch (nextError) {
      setSlotCatalog(DEFAULT_PROMO_SLOTS);
      setContentCatalog(DEFAULT_PROMO_CONTENT);
      setAssignments(createAssignmentState([], DEFAULT_PROMO_SLOTS, DEFAULT_PROMO_CONTENT));
      setError(String((nextError as { message?: string })?.message || nextError || "Could not load promo slots."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadPromoSlots();
  }, []);

  const issueKeys = async (operatorReason: string): Promise<void> => {
    const nextQuantity = Math.max(1, Math.min(50, Number(quantity || 1)));
    setIssuing(true);
    setError("");
    setStatusText("");
    try {
      const payload = await adminAccessKeysIssue({ plan_code: selectedPlan, quantity: nextQuantity, operator_reason: operatorReason.trim() });
      setIssuedKeys((payload.issued || []).map((item) => ({
        key: item.key,
        planLabel: item.plan?.label || payload.plan?.label || selectedPlan,
        issuedAt: item.issued_at,
      })));
      setStatusText(`Выдано ключей: ${payload.issued?.length || 0}. Причина: ${operatorReason.trim()}`);
      setConfirm(null);
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || "Could not issue access keys."));
    } finally {
      setIssuing(false);
    }
  };

  const lookupAccessKey = async (): Promise<void> => {
    const key = normalizeKey(lookupKey);
    if (!key) {
      setError("Enter an access key to look up.");
      return;
    }
    setLookupBusy(true);
    setError("");
    setStatusText("");
    try {
      const payload = await fetchAccessKeyStatus(key);
      setLookupResult(payload);
      setStatusText(payload.exists ? "Access key status loaded." : "Access key not found.");
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || "Could not load access key status."));
    } finally {
      setLookupBusy(false);
    }
  };

  const savePromoSlots = async (operatorReason: string): Promise<void> => {
    setSaving(true);
    setError("");
    setStatusText("");
    try {
      const payload = await adminPromoSlotsUpdate({ assignments, operator_reason: operatorReason.trim() });
      setAssignments(createAssignmentState(payload.promo_slots.assignments || [], slotCatalog, contentCatalog));
      setRemoteMode(String(payload.promo_slots.mode || remoteMode));
      setRemoteAvailable(Boolean(payload.promo_slots.remote_available));
      setFallbackBehavior(String(payload.promo_slots.fallback_behavior || fallbackBehavior));
      setStatusText(`Слоты сохранены. Причина: ${operatorReason.trim()}`);
      setConfirm(null);
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || "Could not save promo slots."));
    } finally {
      setSaving(false);
    }
  };

  const updateAssignment = (slotId: string, patch: Partial<PromoSlotAssignmentPayload>) => {
    setAssignments((current) => current.map((item) => (item.slot_id === slotId ? { ...item, ...patch } : item)));
  };

  const copyText = async (text: string): Promise<void> => {
    try {
      await navigator.clipboard.writeText(text);
      setStatusText("Скопировано.");
      setError("");
    } catch {
      setError("Не удалось скопировать в буфер.");
    }
  };

  return (
    <section className="space-y-4">
      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader
          eyebrow="платежи"
          title="Ключи доступа и promo-слоты"
          description="Выдача платных ключей, recovery-проверки и управление whitelisted promo-слотами без раскрытия публичных цен."
          actions={
            <button className={adminButtonClass("secondary", "sm")} type="button" onClick={() => void loadPromoSlots()} disabled={loading}>
              Обновить слоты
            </button>
          }
        />
        <div className="flex flex-wrap gap-2">
          <AdminBadge tone="accent">remote {remoteAvailable ? "доступен" : "локальный каталог"}</AdminBadge>
          <AdminBadge>version {remoteVersion}</AdminBadge>
          <AdminBadge>mode {remoteMode}</AdminBadge>
          <AdminBadge tone="warning">empty-state: {fallbackBehavior}</AdminBadge>
        </div>
      </article>

      <AdminMetricStrip
        items={[
          { label: "тарифы", value: SHARED_PLANS.length, hint: "Активные платные тарифы." },
          { label: "слоты", value: assignments.length, hint: "Назначения whitelisted promo-слотов.", tone: "accent" },
          { label: "free baseline", value: `${ACCESS_MATRIX.free_tier.location_code} · ${ACCESS_MATRIX.free_tier.traffic_limit_gb} GB`, hint: `${ACCESS_MATRIX.free_tier.speed_limit_mbps} Mbps, ${ACCESS_MATRIX.free_tier.device_limit} device(s).` },
          { label: "выдано сейчас", value: issuedKeys.length, hint: "Ключи, выданные в этой сессии.", tone: issuedKeys.length ? "success" : "neutral" },
        ]}
      />

      {statusText ? <div className={adminPanelClass("success")}>{statusText}</div> : null}
      {error ? <div className={adminPanelClass("danger")}>{error}</div> : null}

      <div className="grid gap-4 xl:grid-cols-[1fr,0.9fr]">
        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader eyebrow="ключи" title="Выдача ключей доступа" />
          <div className="grid gap-3 md:grid-cols-[1fr,120px,auto]">
            <select value={selectedPlan} onChange={(event) => setSelectedPlan(event.target.value)} className={adminFieldClass}>
              {SHARED_PLANS.map((plan) => (
                <option key={plan.code} value={plan.code}>{plan.label} · {plan.amountRub} RUB</option>
              ))}
            </select>
            <input value={quantity} onChange={(event) => setQuantity(event.target.value)} type="number" min={1} max={50} className={adminFieldClass} />
            <button type="button" onClick={() => setConfirm({ kind: "issue", reason: "" })} disabled={issuing} className={adminButtonClass("primary")}>
              {issuing ? "Выдаем..." : "Выдать ключи"}
            </button>
          </div>
          <div className="mt-4 space-y-2">
            {issuedKeys.map((item) => (
              <div key={item.key} className={adminInsetPanelClass}>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-mono text-sm font-semibold text-slate-100">{item.key}</p>
                    <p className="mt-1 text-xs text-slate-500">{item.planLabel} · {fmtRuDate(item.issuedAt)}</p>
                  </div>
                  <button type="button" onClick={() => void copyText(item.key)} className={adminButtonClass("secondary", "xs")}>Копировать</button>
                </div>
              </div>
            ))}
            {!issuedKeys.length ? <p className="text-xs text-slate-500">Выданные ключи появятся здесь.</p> : null}
          </div>
        </article>

        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader eyebrow="recovery" title="Проверка ключа доступа" description="Для проверок восстановления и fraud-проверок без раскрытия исходных ссылок подключения." />
          <div className="flex flex-col gap-3 sm:flex-row">
            <input value={lookupKey} onChange={(event) => setLookupKey(normalizeKey(event.target.value))} placeholder="POKROV-XXXX-XXXX" className={adminFieldClass} />
            <button type="button" onClick={() => void lookupAccessKey()} disabled={lookupBusy} className={adminButtonClass("secondary")}>
              {lookupBusy ? "Проверяем..." : "Проверить"}
            </button>
          </div>
          {lookupResult ? (
            <div className={`${adminInsetPanelClass} mt-4 space-y-1 text-sm text-slate-300`}>
              <p>Ключ: <strong>{lookupResult.key}</strong></p>
              <p>Существует: <strong>{lookupResult.exists ? "да" : "нет"}</strong></p>
              <p>Погашен: <strong>{lookupResult.redeemed ? "да" : "нет"}</strong></p>
              <p>Тариф: <strong>{lookupResult.plan?.label || lookupResult.kind || "-"}</strong></p>
              <p>Лимит устройств: <strong>{lookupResult.device_limit}</strong></p>
              <p>Выдан: <strong>{fmtRuDate(lookupResult.issued_at)}</strong></p>
              <p>Погашен в: <strong>{fmtRuDate(lookupResult.redeemed_at)}</strong></p>
            </div>
          ) : null}
        </article>
      </div>

      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader eyebrow="тарифы" title="Каталог совместимости тарифов" description="Только операторский справочник; публичный pricing-роут остается compatibility-поверхностью." />
        <div className={adminTableShellClass}>
          <div className="overflow-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-[#c6e6db] bg-[#f8fffc] text-left text-[11px] uppercase tracking-[0.14em] text-slate-500">
                  <th className="px-3 py-3">Code</th>
                  <th className="px-3 py-3">Тариф</th>
                  <th className="px-3 py-3">Цена</th>
                  <th className="px-3 py-3">Дни</th>
                  <th className="px-3 py-3">Устройства</th>
                  <th className="px-3 py-3">Примечание</th>
                </tr>
              </thead>
              <tbody>
                {SHARED_PLANS.map((plan) => (
                  <tr key={plan.code} className="border-t border-[#c6e6db]">
                    <td className="px-3 py-3 font-mono text-xs">{plan.code}</td>
                    <td className="px-3 py-3">{plan.label}</td>
                    <td className="px-3 py-3">{plan.amountRub} RUB</td>
                    <td className="px-3 py-3">{plan.days}</td>
                    <td className="px-3 py-3">{plan.deviceLimit}</td>
                    <td className="px-3 py-3 text-xs text-slate-400">{plan.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </article>

      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader
          eyebrow="promo slots"
          title="Slot assignments"
          description="Only whitelisted slots and first-party content IDs can be saved."
          actions={<button type="button" onClick={() => setConfirm({ kind: "slots", reason: "" })} disabled={saving} className={adminButtonClass("primary", "sm")}>{saving ? "Сохраняем..." : "Сохранить слоты"}</button>}
        />
        <div className="space-y-3">
          {assignments.map((assignment) => {
            const slot = slotCatalog.find((item) => item.id === assignment.slot_id);
            const allowedContentIds = slot?.allowed_content_ids || [];
            return (
              <div key={assignment.slot_id} className={adminInsetPanelClass}>
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <AdminBadge tone={assignment.enabled ? "success" : "warning"}>{assignment.enabled ? "enabled" : "disabled"}</AdminBadge>
                  <span className="font-mono text-sm font-semibold text-slate-100">{assignment.slot_id}</span>
                  <span className="text-xs text-slate-500">{slot?.surface || "surface"} · {(slot?.contexts || assignment.contexts || []).join(", ")}</span>
                </div>
                <div className="grid gap-3 lg:grid-cols-[1fr,1fr,120px]">
                  <select value={assignment.content_id} onChange={(event) => updateAssignment(assignment.slot_id, { content_id: event.target.value })} className={adminFieldClass}>
                    {allowedContentIds.map((contentId) => {
                      const content = contentById.get(contentId);
                      return <option key={contentId} value={contentId}>{content?.goal || contentId}</option>;
                    })}
                  </select>
                  <input value={(assignment.contexts || []).join(", ")} onChange={(event) => updateAssignment(assignment.slot_id, { contexts: event.target.value.split(",").map((item) => item.trim()).filter(Boolean) })} className={adminFieldClass} placeholder="Contexts" />
                  <input value={assignment.sort_order} onChange={(event) => updateAssignment(assignment.slot_id, { sort_order: Math.max(0, Number(event.target.value || 0)) })} type="number" className={adminFieldClass} />
                </div>
                <div className="mt-3 grid gap-3 lg:grid-cols-2">
                  <input value={assignment.title || ""} onChange={(event) => updateAssignment(assignment.slot_id, { title: event.target.value })} className={adminFieldClass} placeholder="Title override" />
                  <input value={assignment.body || ""} onChange={(event) => updateAssignment(assignment.slot_id, { body: event.target.value })} className={adminFieldClass} placeholder="Body override" />
                  <input value={assignment.cta_label || ""} onChange={(event) => updateAssignment(assignment.slot_id, { cta_label: event.target.value })} className={adminFieldClass} placeholder="CTA label" />
                  <input value={assignment.cta_href || ""} onChange={(event) => updateAssignment(assignment.slot_id, { cta_href: event.target.value })} className={adminFieldClass} placeholder="CTA href" />
                </div>
                <label className="mt-3 inline-flex items-center gap-2 text-sm text-slate-400">
                  <input type="checkbox" checked={assignment.enabled} onChange={(event) => updateAssignment(assignment.slot_id, { enabled: event.target.checked })} />
                  Slot enabled
                </label>
              </div>
            );
          })}
        </div>
      </article>

      <AdminConfirmDialog
        open={Boolean(confirm)}
        title={confirm?.kind === "issue" ? "Подтвердить выпуск ключей" : "Подтвердить сохранение слотов"}
        description={
          confirm?.kind === "issue"
            ? "Ключи дают платный доступ. Укажите понятную причину для журнала аудита."
            : "Сохранение меняет промо-разметку. Укажите причину для журнала аудита."
        }
        reason={confirm?.reason || ""}
        onReasonChange={(reason) => setConfirm((current) => (current ? { ...current, reason } : current))}
        onCancel={() => setConfirm(null)}
        onConfirm={() => {
          if (!confirm) return;
          if (confirm.kind === "issue") void issueKeys(confirm.reason);
          else void savePromoSlots(confirm.reason);
        }}
        busy={issuing || saving}
      />
    </section>
  );
}
