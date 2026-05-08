"use client";

import { adminButtonClass, adminPanelClass } from "@/components/admin/admin-shell";
import {
  adminAccessKeysIssue,
  adminGiftCodeCreate,
  adminGiftCodes,
  adminPromoSlots,
  adminPromoSlotsUpdate,
  fetchAccessKeyStatus,
  type AdminGiftCodeRow,
  type AccessKeyStatusPayload,
  type PromoSlotAssignmentPayload,
  type PromoSlotCatalogContent,
  type PromoSlotCatalogSlot,
} from "@/lib/api";
import { getAccessMatrix, getPromoSlotsCatalog, getTariffPlans } from "@/lib/portal";
import { Check, Copy, Gift, KeyRound, LayoutTemplate, RefreshCw, Save, Search, ShieldCheck } from "lucide-react";
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
const LEGACY_GIFT_TYPES: Array<{ value: "mini" | "standard" | "premium"; label: string }> = [
  { value: "mini", label: "Mini - 7 дн." },
  { value: "standard", label: "Standard - 30 дн." },
  { value: "premium", label: "Premium - 90 дн." },
];

function normalizeKey(value: string): string {
  return String(value || "")
    .trim()
    .replace(/[\u2010\u2011\u2012\u2013\u2014\u2212_]+/g, "-")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-+|-+$/g, "")
    .toUpperCase();
}

function createAssignmentState(
  assignments: PromoSlotAssignmentPayload[],
  slots: PromoSlotCatalogSlot[],
  contentCatalog: PromoSlotCatalogContent[],
): PromoSlotAssignmentPayload[] {
  const assignmentMap = new Map(assignments.map((item) => [item.slot_id, item]));
  const contentMap = new Map(contentCatalog.map((item) => [item.id, item]));

  return slots.map((slot, index) => {
    const existing = assignmentMap.get(slot.id);
    const fallbackContent = slot.allowed_content_ids.find((contentId) => contentMap.has(contentId)) || slot.allowed_content_ids[0] || "";
    const nextContentId =
      existing && slot.allowed_content_ids.includes(existing.content_id) ? existing.content_id : fallbackContent;

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

function formatContexts(values: string[]): string {
  return values.join(" • ");
}

function formatPlanMeta(days: number, deviceLimit: number): string {
  return `${days} дн. • до ${deviceLimit} устройств`;
}

function formatGiftType(value: string): string {
  return LEGACY_GIFT_TYPES.find((item) => item.value === value)?.label || value;
}

function StatusBanner({ tone, text }: { tone: "success" | "error"; text: string }) {
  const success = tone === "success";
  return (
    <div className={`${adminPanelClass(success ? "success" : "danger")} flex items-center gap-3`}>
      <div className={`stat-icon ${success ? "stat-icon-emerald" : "stat-icon-rose"}`}>
        {success ? <Check size={18} /> : <ShieldCheck size={18} />}
      </div>
      <p className={`text-sm font-medium ${success ? "text-emerald-600 dark:text-emerald-300" : "text-rose-500"}`}>
        {text}
      </p>
    </div>
  );
}

export default function AdminPromosPage() {
  const [selectedPlan, setSelectedPlan] = useState(SHARED_PLANS[0]?.code || "1_month");
  const [quantity, setQuantity] = useState("5");
  const [giftType, setGiftType] = useState<"mini" | "standard" | "premium">("standard");
  const [giftCodes, setGiftCodes] = useState<AdminGiftCodeRow[]>([]);
  const [issuedKeys, setIssuedKeys] = useState<
    Array<{
      key: string;
      planLabel: string;
      issuedAt?: string | null;
    }>
  >([]);
  const [lookupKey, setLookupKey] = useState("");
  const [lookupResult, setLookupResult] = useState<AccessKeyStatusPayload | null>(null);
  const [slotCatalog, setSlotCatalog] = useState<PromoSlotCatalogSlot[]>(DEFAULT_PROMO_SLOTS);
  const [contentCatalog, setContentCatalog] = useState<PromoSlotCatalogContent[]>(DEFAULT_PROMO_CONTENT);
  const [assignments, setAssignments] = useState<PromoSlotAssignmentPayload[]>(
    createAssignmentState([], DEFAULT_PROMO_SLOTS, DEFAULT_PROMO_CONTENT),
  );
  const [remoteVersion, setRemoteVersion] = useState(PROMO_CATALOG.version);
  const [remoteMode, setRemoteMode] = useState(PROMO_CATALOG.mode);
  const [remoteAvailable, setRemoteAvailable] = useState(false);
  const [fallbackBehavior, setFallbackBehavior] = useState(PROMO_CATALOG.fallback_behavior);
  const [loading, setLoading] = useState(false);
  const [issuing, setIssuing] = useState(false);
  const [giftLoading, setGiftLoading] = useState(false);
  const [giftCreating, setGiftCreating] = useState(false);
  const [lookupBusy, setLookupBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [error, setError] = useState("");

  const contentById = useMemo(
    () => new Map(contentCatalog.map((item) => [item.id, item])),
    [contentCatalog],
  );

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
      setStatusText("Конфиг промо-слотов загружен с сервера.");
    } catch (nextError) {
      setSlotCatalog(DEFAULT_PROMO_SLOTS);
      setContentCatalog(DEFAULT_PROMO_CONTENT);
      setAssignments(createAssignmentState([], DEFAULT_PROMO_SLOTS, DEFAULT_PROMO_CONTENT));
      setError(String((nextError as { message?: string })?.message || nextError || "Не удалось загрузить промо-слоты."));
    } finally {
      setLoading(false);
    }
  };

  const loadGiftCodes = async (): Promise<void> => {
    setGiftLoading(true);
    setError("");
    try {
      setGiftCodes(await adminGiftCodes(50));
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || "Не удалось загрузить подарочные карты."));
    } finally {
      setGiftLoading(false);
    }
  };

  useEffect(() => {
    void loadPromoSlots();
    void loadGiftCodes();
  }, []);

  const issueKeys = async (): Promise<void> => {
    const nextQuantity = Math.max(1, Math.min(50, Number(quantity || 1)));
    setIssuing(true);
    setError("");
    setStatusText("");
    try {
      const payload = await adminAccessKeysIssue({
        plan_code: selectedPlan,
        quantity: nextQuantity,
      });
      setIssuedKeys(
        (payload.issued || []).map((item) => ({
          key: item.key,
          planLabel: item.plan?.label || payload.plan?.label || selectedPlan,
          issuedAt: item.issued_at,
        })),
      );
      setStatusText(`Выпущено ${payload.issued?.length || 0} ключей доступа для плана ${payload.plan?.label || selectedPlan}.`);
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || "Не удалось выпустить ключи."));
    } finally {
      setIssuing(false);
    }
  };

  const createLegacyGiftCard = async (): Promise<void> => {
    setGiftCreating(true);
    setError("");
    setStatusText("");
    try {
      const payload = await adminGiftCodeCreate(giftType);
      const created = payload.gift_code;
      const row: AdminGiftCodeRow = {
        code: created.code,
        card_type: created.card_type,
        days: created.days,
        stars: created.stars,
        created_by: 0,
        created_at: new Date().toISOString(),
        redeemed_by: null,
        redeemed_at: null,
      };
      setGiftCodes((current) => [row, ...current.filter((item) => item.code !== row.code)]);
      setStatusText(`Подарочная карта ${row.code} создана.`);
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || "Не удалось создать подарочную карту."));
    } finally {
      setGiftCreating(false);
    }
  };

  const lookupAccessKey = async (): Promise<void> => {
    const key = normalizeKey(lookupKey);
    if (!key) {
      setError("Введите ключ доступа для проверки.");
      return;
    }
    setLookupBusy(true);
    setError("");
    setStatusText("");
    try {
      const payload = await fetchAccessKeyStatus(key);
      setLookupResult(payload);
      setStatusText(payload.exists ? "Статус ключа загружен." : "Ключ не найден.");
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || "Не удалось получить статус ключа."));
    } finally {
      setLookupBusy(false);
    }
  };

  const savePromoSlots = async (): Promise<void> => {
    setSaving(true);
    setError("");
    setStatusText("");
    try {
      const payload = await adminPromoSlotsUpdate({ assignments });
      setAssignments(createAssignmentState(payload.promo_slots.assignments || [], slotCatalog, contentCatalog));
      setRemoteMode(String(payload.promo_slots.mode || remoteMode));
      setRemoteAvailable(Boolean(payload.promo_slots.remote_available));
      setFallbackBehavior(String(payload.promo_slots.fallback_behavior || fallbackBehavior));
      setStatusText("Конфиг промо-слотов сохранён.");
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || "Не удалось сохранить промо-слоты."));
    } finally {
      setSaving(false);
    }
  };

  const updateAssignment = (slotId: string, patch: Partial<PromoSlotAssignmentPayload>) => {
    setAssignments((current) =>
      current.map((item) => (item.slot_id === slotId ? { ...item, ...patch } : item)),
    );
  };

  const copyText = async (text: string): Promise<void> => {
    try {
      await navigator.clipboard.writeText(text);
      setStatusText("Скопировано в буфер.");
      setError("");
    } catch {
      setError("Не удалось скопировать значение.");
    }
  };

  return (
    <section className="space-y-5">
      <article className={adminPanelClass("neutral")}>
        <h2 className="font-display text-xl font-bold">Ключи доступа и промо-слоты</h2>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Эта панель больше не живёт в старой логике подарков и промокодов. Здесь оператор выпускает ключи доступа,
          проверяет кейсы восстановления, держит единый каталог тарифов перед глазами и управляет только собственными
          промо-слотами из утверждённого списка.
        </p>
      </article>

      {statusText ? <StatusBanner tone="success" text={statusText} /> : null}
      {error ? <StatusBanner tone="error" text={error} /> : null}

      <div className="grid gap-5 md:grid-cols-3">
        <article className={adminPanelClass("neutral")}>
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500">публичный контур</p>
          <h3 className="mt-2 font-display text-2xl font-semibold">Android + Windows</h3>
          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            Публичное обещание этой волны держим только на этих платформах. Apple-сборки остаются
            инженерным контуром и не входят в релизную приёмку.
          </p>
        </article>

        <article className={adminPanelClass("neutral")}>
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500">бесплатная база</p>
          <h3 className="mt-2 font-display text-2xl font-semibold">
            {ACCESS_MATRIX.free_tier.location_code} • {ACCESS_MATRIX.free_tier.traffic_limit_gb} GB
          </h3>
          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            Ежемесячный сброс, {ACCESS_MATRIX.free_tier.speed_limit_mbps} Мбит/с на IP, до{" "}
            {ACCESS_MATRIX.free_tier.device_limit} устройства. После пробного периода сюда уходит базовое понижение.
          </p>
        </article>

        <article className={adminPanelClass("neutral")}>
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500">скрытый порядок транспорта</p>
          <h3 className="mt-2 font-display text-2xl font-semibold">VLESS → VMess → Trojan → XHTTP</h3>
          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            Операторская видимость сохраняется, но массовый UI видит одну логическую локацию. XHTTP допускается
            только при готовой CDN/static-предпосылке.
          </p>
        </article>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.05fr,0.95fr]">
        <article className={adminPanelClass("neutral")}>
          <div className="mb-4 flex items-center gap-3">
            <div className="stat-icon stat-icon-emerald">
              <KeyRound size={20} />
            </div>
            <h2 className="font-display text-xl font-bold">Выпуск ключей доступа</h2>
          </div>
          <p className="mb-4 text-sm text-slate-600 dark:text-slate-300">
            Маршрут с ключами начинается здесь: оператор выпускает ключи по каноническим кодам тарифов, а не через
            старые типы подарочных кодов.
          </p>

          <div className="grid gap-3 md:grid-cols-[1fr,120px,auto]">
            <select
              value={selectedPlan}
              onChange={(event) => setSelectedPlan(event.target.value)}
              className="rounded-xl border border-white/45 bg-white/65 px-3 py-3 text-sm outline-none dark:border-white/10 dark:bg-white/5"
            >
              {SHARED_PLANS.map((plan) => (
                <option key={plan.code} value={plan.code}>
                  {plan.label} • {plan.amountRub} ₽
                </option>
              ))}
            </select>
            <input
              value={quantity}
              onChange={(event) => setQuantity(event.target.value)}
              type="number"
              min={1}
              max={50}
              className="rounded-xl border border-white/45 bg-white/65 px-3 py-3 text-sm outline-none dark:border-white/10 dark:bg-white/5"
            />
            <button
              type="button"
              onClick={() => void issueKeys()}
              disabled={issuing}
                    className={adminButtonClass("primary")}
            >
              {issuing ? "Выпускаем..." : "Выпустить"}
            </button>
          </div>

          <div className="mt-5 space-y-2">
            {issuedKeys.length ? (
              issuedKeys.map((item) => (
                <div key={item.key} className="node-card flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <p className="badge badge-violet font-mono">{item.key}</p>
                    <p className="mt-2 text-xs text-slate-500">
                      {item.planLabel} • {fmtRuDate(item.issuedAt)}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => void copyText(item.key)}
                    className={adminButtonClass("secondary", "xs")}
                  >
                    <Copy size={14} />
                    Скопировать
                  </button>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <KeyRound size={24} />
                <p className="text-xs">Новые ключи доступа появятся здесь после выпуска.</p>
              </div>
            )}
          </div>
        </article>

        <article className="glass-card p-5">
          <div className="mb-4 flex items-center gap-3">
            <div className="stat-icon stat-icon-blue">
              <Search size={20} />
            </div>
            <h2 className="font-display text-xl font-bold">Проверка восстановления</h2>
          </div>
          <p className="mb-4 text-sm text-slate-600 dark:text-slate-300">
            Для ручных кейсов восстановления оператор может проверить статус конкретного ключа без показа сырой ссылки подключения.
          </p>

          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              value={lookupKey}
              onChange={(event) => setLookupKey(normalizeKey(event.target.value))}
              placeholder="POKROV-XXXX-XXXX"
              className="w-full rounded-xl border border-white/45 bg-white/65 px-3 py-3 text-sm outline-none dark:border-white/10 dark:bg-white/5"
            />
            <button
              type="button"
              onClick={() => void lookupAccessKey()}
              disabled={lookupBusy}
                    className={adminButtonClass("secondary")}
            >
              {lookupBusy ? "Проверяем..." : "Проверить"}
            </button>
          </div>

          {lookupResult ? (
            <div className="mt-5 space-y-2 rounded-2xl border border-white/40 bg-white/55 p-4 text-sm text-slate-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-200">
              <p>Ключ: <strong>{lookupResult.key}</strong></p>
              <p>Найден: <strong>{lookupResult.exists ? "да" : "нет"}</strong></p>
              <p>Погашен: <strong>{lookupResult.redeemed ? "да" : "нет"}</strong></p>
              <p>План: <strong>{lookupResult.plan?.label || lookupResult.kind || "—"}</strong></p>
              <p>Лимит устройств: <strong>{lookupResult.device_limit}</strong></p>
              <p>Выдан: <strong>{fmtRuDate(lookupResult.issued_at)}</strong></p>
              <p>Погашен: <strong>{fmtRuDate(lookupResult.redeemed_at)}</strong></p>
            </div>
          ) : null}
        </article>
      </div>

      <article className={adminPanelClass("neutral")}>
        <div className="mb-4 flex items-center gap-3">
          <div className="stat-icon stat-icon-amber">
            <Gift size={20} />
          </div>
          <div>
            <h2 className="font-display text-xl font-bold">Старые подарочные карты</h2>
            <p className="text-xs text-slate-500">
              Совместимость для уже знакомого bot/API gift-flow. Основной новый путь остается через ключи доступа.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void loadGiftCodes()}
            disabled={giftLoading}
            className={`${adminButtonClass("secondary", "xs")} ml-auto`}
          >
            <RefreshCw size={14} />
            {giftLoading ? "Обновляем..." : "Обновить"}
          </button>
        </div>

        <div className="grid gap-3 md:grid-cols-[1fr,auto]">
          <label className="text-sm">
            <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">Тип подарочной карты</span>
            <select
              aria-label="Тип подарочной карты"
              value={giftType}
              onChange={(event) => setGiftType(event.target.value as "mini" | "standard" | "premium")}
              className="w-full rounded-xl border border-white/45 bg-white/65 px-3 py-3 text-sm outline-none dark:border-white/10 dark:bg-white/5"
            >
              {LEGACY_GIFT_TYPES.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={() => void createLegacyGiftCard()}
            disabled={giftCreating}
            className={`${adminButtonClass("primary")} self-end`}
          >
            {giftCreating ? "Создаем..." : "Создать gift-карту"}
          </button>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {giftCodes.length ? (
            giftCodes.map((item) => (
              <div key={item.code} className="stat-card p-4">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <span className="badge badge-violet font-mono">{item.code}</span>
                  <span className={item.redeemed_by ? "badge badge-warning" : "badge badge-success"}>
                    {item.redeemed_by ? "использована" : "готова"}
                  </span>
                </div>
                <p className="text-sm font-semibold">{formatGiftType(item.card_type)}</p>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                  {item.days} дн. · {item.stars} Stars
                </p>
                <p className="mt-1 text-xs text-slate-500">Создана: {fmtRuDate(item.created_at)}</p>
                {item.redeemed_at ? <p className="mt-1 text-xs text-slate-500">Погашена: {fmtRuDate(item.redeemed_at)}</p> : null}
                <button
                  type="button"
                  onClick={() => void copyText(item.code)}
                  className={`${adminButtonClass("secondary", "xs")} mt-3`}
                >
                  <Copy size={14} />
                  Скопировать
                </button>
              </div>
            ))
          ) : (
            <div className="empty-state md:col-span-2 xl:col-span-3">
              <Gift size={24} />
              <p className="text-xs">Подарочных карт пока нет. Создайте карту только если нужен legacy gift-flow.</p>
            </div>
          )}
        </div>
      </article>

      <article className={adminPanelClass("neutral")}>
        <div className="mb-4 flex items-center gap-3">
          <div className="stat-icon stat-icon-amber">
            <ShieldCheck size={20} />
          </div>
          <h2 className="font-display text-xl font-bold">Каталог тарифов</h2>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {SHARED_PLANS.map((plan) => (
            <div key={plan.code} className="stat-card p-4">
              <div className="mb-3 flex items-center justify-between gap-2">
                <span className="badge badge-violet font-mono">{plan.code}</span>
                <span className="badge badge-success">{plan.badge || "активен"}</span>
              </div>
              <p className="text-lg font-bold">{plan.label}</p>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{plan.amountRub} ₽</p>
              <p className="mt-1 text-xs text-slate-500">{formatPlanMeta(plan.days, plan.deviceLimit)}</p>
              <p className="mt-3 text-xs leading-6 text-slate-500">{plan.note}</p>
            </div>
          ))}
        </div>
      </article>

      <article className="glass-card p-5">
        <div className="mb-4 flex items-center gap-3">
          <div className="stat-icon stat-icon-violet">
            <LayoutTemplate size={20} />
          </div>
          <div>
            <h2 className="font-display text-xl font-bold">Расписание промо-слотов</h2>
            <p className="text-xs text-slate-500">
              версия {remoteVersion} • режим {remoteMode} • источник {remoteAvailable ? "доступен" : "резерв"}
            </p>
          </div>
          <div className="ml-auto flex gap-2">
            <button
              type="button"
              onClick={() => void loadPromoSlots()}
              disabled={loading}
                    className={adminButtonClass("secondary", "xs")}
            >
              <RefreshCw size={14} />
              Обновить
            </button>
            <button
              type="button"
              onClick={() => void savePromoSlots()}
              disabled={saving}
                    className={adminButtonClass("primary", "xs")}
            >
              <Save size={14} />
              {saving ? "Сохраняем..." : "Сохранить"}
            </button>
          </div>
        </div>

        <p className="mb-4 text-sm text-slate-600 dark:text-slate-300">
          Разрешены только слоты из утверждённого списка и собственный промо-контент. Если удалённый конфиг недоступен,
          поверхность переходит в <strong>{fallbackBehavior}</strong>.
        </p>

        <div className="space-y-4">
          {assignments.map((assignment) => {
            const slot = slotCatalog.find((item) => item.id === assignment.slot_id);
            const allowedContentIds = slot?.allowed_content_ids || [];

            return (
              <div key={assignment.slot_id} className="node-card space-y-4 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="badge badge-violet font-mono">{assignment.slot_id}</span>
                  <span className="badge badge-info">{slot?.surface || "surface"}</span>
                  <span className="text-xs text-slate-500">{formatContexts(slot?.contexts || assignment.contexts || [])}</span>
                </div>

                <div className="grid gap-3 lg:grid-cols-[1fr,1fr,120px]">
                  <label className="text-sm">
                    <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">контент</span>
                    <select
                      value={assignment.content_id}
                      onChange={(event) => updateAssignment(assignment.slot_id, { content_id: event.target.value })}
                      className="w-full rounded-xl border border-white/45 bg-white/65 px-3 py-3 text-sm outline-none dark:border-white/10 dark:bg-white/5"
                    >
                      {allowedContentIds.map((contentId) => {
                        const content = contentById.get(contentId);
                        return (
                          <option key={contentId} value={contentId}>
                            {content?.goal || contentId}
                          </option>
                        );
                      })}
                    </select>
                  </label>

                  <label className="text-sm">
                    <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">контексты</span>
                    <input
                      value={(assignment.contexts || []).join(", ")}
                      onChange={(event) =>
                        updateAssignment(assignment.slot_id, {
                          contexts: event.target.value
                            .split(",")
                            .map((item) => item.trim())
                            .filter(Boolean),
                        })
                      }
                      className="w-full rounded-xl border border-white/45 bg-white/65 px-3 py-3 text-sm outline-none dark:border-white/10 dark:bg-white/5"
                    />
                  </label>

                  <label className="text-sm">
                    <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">порядок</span>
                    <input
                      value={assignment.sort_order}
                      onChange={(event) => updateAssignment(assignment.slot_id, { sort_order: Math.max(0, Number(event.target.value || 0)) })}
                      type="number"
                      min={0}
                      className="w-full rounded-xl border border-white/45 bg-white/65 px-3 py-3 text-sm outline-none dark:border-white/10 dark:bg-white/5"
                    />
                  </label>
                </div>

                <div className="grid gap-3 lg:grid-cols-2">
                  <label className="text-sm">
                    <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">замена заголовка</span>
                    <input
                      value={assignment.title || ""}
                      onChange={(event) => updateAssignment(assignment.slot_id, { title: event.target.value })}
                      className="w-full rounded-xl border border-white/45 bg-white/65 px-3 py-3 text-sm outline-none dark:border-white/10 dark:bg-white/5"
                    />
                  </label>

                  <label className="text-sm">
                    <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">замена текста</span>
                    <input
                      value={assignment.body || ""}
                      onChange={(event) => updateAssignment(assignment.slot_id, { body: event.target.value })}
                      className="w-full rounded-xl border border-white/45 bg-white/65 px-3 py-3 text-sm outline-none dark:border-white/10 dark:bg-white/5"
                    />
                  </label>

                  <label className="text-sm">
                    <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">текст кнопки</span>
                    <input
                      value={assignment.cta_label || ""}
                      onChange={(event) => updateAssignment(assignment.slot_id, { cta_label: event.target.value })}
                      className="w-full rounded-xl border border-white/45 bg-white/65 px-3 py-3 text-sm outline-none dark:border-white/10 dark:bg-white/5"
                    />
                  </label>

                  <label className="text-sm">
                    <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">ссылка кнопки</span>
                    <input
                      value={assignment.cta_href || ""}
                      onChange={(event) => updateAssignment(assignment.slot_id, { cta_href: event.target.value })}
                      className="w-full rounded-xl border border-white/45 bg-white/65 px-3 py-3 text-sm outline-none dark:border-white/10 dark:bg-white/5"
                    />
                  </label>
                </div>

                <label className="inline-flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                  <input
                    type="checkbox"
                    checked={assignment.enabled}
                    onChange={(event) => updateAssignment(assignment.slot_id, { enabled: event.target.checked })}
                  />
                  Слот включён
                </label>
              </div>
            );
          })}
        </div>
      </article>
    </section>
  );
}
