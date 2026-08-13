"use client";

import { useMemo, useState } from "react";
import { ImageIcon, Megaphone, RefreshCw, Save, X } from "lucide-react";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { Badge, Button, Card, EmptyState, SectionTitle } from "@/components/ui";
import type { ActionIntentRequest } from "@/lib/admin-api/actions";
import {
  fetchPromoSlots,
  type PromoSlotAssignment,
  type PromoSlotsPayload,
} from "@/lib/admin-api/revenue";
import { useRouteResource } from "@/lib/use-route-resource";

const inputClass = "mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm";

const contextLabels: Record<string, string> = {
  anonymous: "Без входа",
  session: "С авторизацией",
  ticketed: "После обращения",
  trial_premium: "Триал",
  bonus_premium: "Бонусный премиум",
  paid_unlimited: "Оплаченный премиум",
  expired_or_blocked: "Доступ закончился",
};

function surfaceLabel(value: string): string {
  if (value === "app") return "Приложение";
  if (value === "webapp") return "Личный кабинет";
  if (value === "marketing") return "Сайт";
  return value || "Поверхность";
}

function contentLabel(value: string): string {
  const labels: Record<string, string> = {
    partner_promo: "Рекламная кампания",
    redeem_key: "Активация ключа",
    support_recovery: "Поддержка",
    telegram_bonus: "Telegram-бонус",
  };
  return labels[value] || value;
}

function dateInput(value: string | null | undefined): string {
  if (!value || Number.isNaN(Date.parse(value))) return "";
  const date = new Date(value);
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

function createAssignments(payload: PromoSlotsPayload): PromoSlotAssignment[] {
  const existing = new Map(payload.assignments.map((item) => [item.slot_id, item]));
  const content = new Map(payload.catalog.content_catalog.map((item) => [item.id, item]));
  return payload.catalog.slots.map((slot, index) => {
    const current = existing.get(slot.id);
    const fallbackContent = slot.allowed_content_ids.find((id) => content.has(id)) || slot.allowed_content_ids[0] || "";
    const contentId = current && slot.allowed_content_ids.includes(current.content_id) ? current.content_id : fallbackContent;
    return {
      slot_id: slot.id,
      content_id: contentId,
      enabled: current?.enabled ?? Boolean(content.get(contentId)?.default_enabled),
      title: current?.title || "",
      body: current?.body || "",
      badge_label: current?.badge_label || "",
      image_url: current?.image_url || "",
      image_layout: current?.image_layout || "logo",
      cta_label: current?.cta_label || "",
      cta_href: current?.cta_href || "",
      accent_color: current?.accent_color || "",
      background_color: current?.background_color || "",
      text_color: current?.text_color || "",
      button_color: current?.button_color || "",
      button_text_color: current?.button_text_color || "",
      placement: current?.placement || "",
      dismissible: current?.dismissible ?? true,
      whole_card_clickable: current?.whole_card_clickable ?? true,
      starts_at: dateInput(current?.starts_at),
      ends_at: dateInput(current?.ends_at),
      contexts: current?.contexts?.length ? [...current.contexts] : [...slot.contexts],
      sort_order: current?.sort_order ?? index + 1,
    };
  });
}

function sanitizeAssignments(assignments: PromoSlotAssignment[]): PromoSlotAssignment[] {
  return assignments.map((item) => ({
    ...item,
    title: item.title?.trim() || null,
    body: item.body?.trim() || null,
    badge_label: item.badge_label?.trim() || null,
    image_url: item.image_url?.trim() || null,
    cta_label: item.cta_label?.trim() || null,
    cta_href: item.cta_href?.trim() || null,
    accent_color: item.accent_color?.trim() || null,
    background_color: item.background_color?.trim() || null,
    text_color: item.text_color?.trim() || null,
    button_color: item.button_color?.trim() || null,
    button_text_color: item.button_text_color?.trim() || null,
    placement: item.placement?.trim() || null,
    starts_at: item.starts_at?.trim() || null,
    ends_at: item.ends_at?.trim() || null,
  }));
}

function ColorField({ label, value, fallback, onChange }: { label: string; value: string; fallback: string; onChange: (value: string) => void }) {
  return (
    <label className="text-xs font-semibold">
      {label}
      <span className="mt-1 flex items-center gap-2">
        <input aria-label={label} type="color" value={value || fallback} onChange={(event) => onChange(event.target.value)} className="h-10 w-12 rounded-lg border border-[color:var(--atlas-border)] bg-transparent p-1" />
        <input aria-label={`${label}, HEX`} value={value} onChange={(event) => onChange(event.target.value)} placeholder="по умолчанию" className="min-h-10 min-w-0 flex-1 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-2 font-mono text-xs" />
        {value ? <button type="button" aria-label={`Сбросить ${label.toLowerCase()}`} onClick={() => onChange("")} className="rounded-lg p-2 text-[color:var(--atlas-text-soft)] hover:bg-[color:var(--atlas-surface-muted)]"><X size={14} /></button> : null}
      </span>
    </label>
  );
}

export function CampaignSlotsPanel() {
  const load = useMemo(() => (signal: AbortSignal) => fetchPromoSlots({ signal }), []);
  const resource = useRouteResource("promo-slots", load, { enabled: true, pollMs: 0 });
  const [draftAssignments, setDraftAssignments] = useState<PromoSlotAssignment[] | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const serverAssignments = useMemo(() => resource.data ? createAssignments(resource.data) : [], [resource.data]);
  const assignments = draftAssignments || serverAssignments;
  const dirty = draftAssignments !== null;
  const slotById = useMemo(() => new Map((resource.data?.catalog.slots || []).map((slot) => [slot.id, slot])), [resource.data]);
  const effectiveSelectedId = selectedId && assignments.some((item) => item.slot_id === selectedId) ? selectedId : assignments[0]?.slot_id || "";
  const selected = assignments.find((item) => item.slot_id === effectiveSelectedId) || null;
  const selectedSlot = selected ? slotById.get(selected.slot_id) || null : null;

  function update(patch: Partial<PromoSlotAssignment>) {
    if (!selected) return;
    setDraftAssignments((current) => (current || serverAssignments).map((item) => item.slot_id === selected.slot_id ? { ...item, ...patch } : item));
  }

  function toggleContext(context: string) {
    if (!selected) return;
    const values = selected.contexts.includes(context)
      ? selected.contexts.filter((item) => item !== context)
      : [...selected.contexts, context];
    update({ contexts: values });
  }

  function save() {
    const payload = { assignments: sanitizeAssignments(assignments) };
    setRequest({ action: "promo_slots.update", target: { type: "config", id: "promo-slots" }, payload, endpoint: "/api/admin/promo-slots", method: "PUT" });
    setDialogOpen(true);
  }

  function reload() {
    setDraftAssignments(null);
    resource.reload();
  }

  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <SectionTitle title="Реклама без обновления приложения" description="Кампания, аудитория, картинка, кнопка и расписание приходят с сервера. Сначала настройте один слот и проверьте предпросмотр." />
        <div className="flex gap-2">
          <Button tone="secondary" disabled={resource.loading || resource.refreshing} onClick={reload}><RefreshCw size={15} className={resource.refreshing ? "animate-spin" : ""} /> Обновить</Button>
          <Button tone="primary" disabled={!dirty || !assignments.length} onClick={save}><Save size={15} /> Проверить и сохранить</Button>
        </div>
      </div>

      {resource.error ? <p role="alert" className="mt-3 text-xs text-[color:var(--atlas-status-danger-text)]">Не удалось загрузить рекламные слоты: {resource.error.message}</p> : null}
      {dirty ? <div className="mt-3"><Badge tone="warning">Есть несохранённые изменения</Badge></div> : null}

      {!selected || !selectedSlot ? (
        <div className="mt-4"><EmptyState title="Слоты ещё не загружены" description="Проверьте API и повторите загрузку." /></div>
      ) : (
        <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(19rem,0.85fr)]">
          <div className="space-y-4">
            <div className="grid gap-3 md:grid-cols-[1fr,1fr]">
              <label className="text-xs font-semibold">Место показа
                <select value={effectiveSelectedId} onChange={(event) => setSelectedId(event.target.value)} className={inputClass}>
                  {assignments.map((item) => {
                    const slot = slotById.get(item.slot_id);
                    return <option key={item.slot_id} value={item.slot_id}>{surfaceLabel(slot?.surface || "")} · {item.slot_id}</option>;
                  })}
                </select>
              </label>
              <label className="text-xs font-semibold">Тип блока
                <select value={selected.content_id} onChange={(event) => update({ content_id: event.target.value })} className={inputClass}>
                  {selectedSlot.allowed_content_ids.map((id) => <option key={id} value={id}>{contentLabel(id)}</option>)}
                </select>
              </label>
            </div>

            <div>
              <p className="text-xs font-semibold">Кому показывать</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {selectedSlot.contexts.map((context) => (
                  <button key={context} type="button" aria-pressed={selected.contexts.includes(context)} onClick={() => toggleContext(context)} className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${selected.contexts.includes(context) ? "border-[color:var(--atlas-status-success-border)] bg-[color:var(--atlas-status-success-bg)] text-[color:var(--atlas-status-success-text)]" : "border-[color:var(--atlas-border)] text-[color:var(--atlas-text-soft)]"}`}>{contextLabels[context] || context}</button>
                ))}
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <label className="text-xs font-semibold">Метка<input value={selected.badge_label || ""} onChange={(event) => update({ badge_label: event.target.value })} placeholder="Предложение" className={inputClass} /></label>
              <label className="text-xs font-semibold">Заголовок<input value={selected.title || ""} onChange={(event) => update({ title: event.target.value })} placeholder="Коротко и по делу" className={inputClass} /></label>
            </div>
            <label className="block text-xs font-semibold">Текст<textarea value={selected.body || ""} onChange={(event) => update({ body: event.target.value })} rows={2} placeholder="Одна короткая причина нажать" className={`${inputClass} py-2`} /></label>

            <div className="grid gap-3 md:grid-cols-[1fr,11rem]">
              <label className="text-xs font-semibold">Картинка или логотип (HTTPS)<input value={selected.image_url || ""} onChange={(event) => update({ image_url: event.target.value })} placeholder="https://cdn.example/banner.webp" className={inputClass} /></label>
              <label className="text-xs font-semibold">Вид изображения<select value={selected.image_layout || "logo"} onChange={(event) => update({ image_layout: event.target.value })} className={inputClass}><option value="logo">Логотип</option><option value="banner">Баннер</option></select></label>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <label className="text-xs font-semibold">Текст кнопки<input value={selected.cta_label || ""} onChange={(event) => update({ cta_label: event.target.value })} placeholder="Подробнее" className={inputClass} /></label>
              <label className="text-xs font-semibold">Ссылка<input value={selected.cta_href || ""} onChange={(event) => update({ cta_href: event.target.value })} placeholder="https://… или tg://…" className={inputClass} /></label>
            </div>

            <details className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] p-3">
              <summary className="cursor-pointer text-sm font-semibold">Расписание, цвета и поведение</summary>
              <div className="mt-4 space-y-4">
                <div className="grid gap-3 md:grid-cols-2">
                  <label className="text-xs font-semibold">Начало<input type="datetime-local" value={selected.starts_at || ""} onChange={(event) => update({ starts_at: event.target.value })} className={inputClass} /></label>
                  <label className="text-xs font-semibold">Окончание<input type="datetime-local" value={selected.ends_at || ""} onChange={(event) => update({ ends_at: event.target.value })} className={inputClass} /></label>
                </div>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  <ColorField label="Акцент" value={selected.accent_color || ""} fallback="#0B6B53" onChange={(value) => update({ accent_color: value })} />
                  <ColorField label="Фон" value={selected.background_color || ""} fallback="#F4F0E8" onChange={(value) => update({ background_color: value })} />
                  <ColorField label="Текст" value={selected.text_color || ""} fallback="#151A17" onChange={(value) => update({ text_color: value })} />
                  <ColorField label="Кнопка" value={selected.button_color || ""} fallback="#0B6B53" onChange={(value) => update({ button_color: value })} />
                  <ColorField label="Текст кнопки" value={selected.button_text_color || ""} fallback="#FFFFFF" onChange={(value) => update({ button_text_color: value })} />
                </div>
                <div className="flex flex-wrap gap-5 text-xs font-semibold">
                  <label className="inline-flex items-center gap-2"><input type="checkbox" checked={selected.enabled} onChange={(event) => update({ enabled: event.target.checked })} /> Показывать</label>
                  <label className="inline-flex items-center gap-2"><input type="checkbox" checked={selected.dismissible !== false} onChange={(event) => update({ dismissible: event.target.checked })} /> Крестик закрытия</label>
                  <label className="inline-flex items-center gap-2"><input type="checkbox" checked={selected.whole_card_clickable !== false} onChange={(event) => update({ whole_card_clickable: event.target.checked })} /> Весь блок — ссылка</label>
                </div>
              </div>
            </details>
          </div>

          <aside>
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.12em] text-[color:var(--atlas-text-soft)]">Предпросмотр</p>
            <div className="overflow-hidden rounded-[1.4rem] border" style={{ backgroundColor: selected.background_color || "#f4f0e8", borderColor: selected.accent_color || "#d6ddd7", color: selected.text_color || "#151a17" }}>
              {selected.image_url && selected.image_layout === "banner" ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={selected.image_url} alt="" className="h-36 w-full object-cover" />
              ) : null}
              <div className="flex items-center gap-3 p-4">
                {selected.image_url && selected.image_layout !== "banner" ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={selected.image_url} alt="" className="h-14 w-14 rounded-2xl object-contain" />
                ) : <span className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-black/5"><ImageIcon size={22} /></span>}
                <div className="min-w-0 flex-1">
                  {selected.badge_label ? <p className="text-[10px] font-bold uppercase tracking-[0.14em] opacity-65">{selected.badge_label}</p> : null}
                  <p className="font-semibold">{selected.title || "Заголовок кампании"}</p>
                  <p className="mt-1 text-xs opacity-70">{selected.body || "Короткий текст без рекламного полотна."}</p>
                </div>
                {selected.cta_label ? <span className="rounded-xl px-3 py-2 text-xs font-bold" style={{ backgroundColor: selected.button_color || selected.accent_color || "#0b6b53", color: selected.button_text_color || "#ffffff" }}>{selected.cta_label}</span> : null}
              </div>
            </div>
            <div className="mt-3 flex items-start gap-2 rounded-xl bg-[color:var(--atlas-surface-muted)] p-3 text-xs text-[color:var(--atlas-text-soft)]"><Megaphone size={15} className="mt-0.5 shrink-0" /> После подтверждения клиент получит изменения при следующем обновлении данных. Выпуск нового APK не нужен.</div>
          </aside>
        </div>
      )}

      <ActionIntentDialog open={dialogOpen} request={request} onOpenChange={(open) => { setDialogOpen(open); if (!open) setRequest(null); }} onKnownOutcome={reload} onCheckState={resource.reload} />
    </Card>
  );
}
