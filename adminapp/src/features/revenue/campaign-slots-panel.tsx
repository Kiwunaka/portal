"use client";

import { useEffect, useMemo, useState } from "react";
import { Clock3, ImageIcon, Megaphone, RefreshCw, Save, Upload, X } from "lucide-react";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { Badge, Button, Card, EmptyState, SectionTitle } from "@/components/ui";
import type { ActionIntentRequest } from "@/lib/admin-api/actions";
import {
  fetchPromoSlots,
  type PromoSlotAssignment,
  type PromoSlotsPayload,
  uploadPromoMedia,
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
    release_update: "Обновление приложения",
    incident_notice: "Сервисное сообщение",
  };
  return labels[value] || value;
}

function contentDescription(value: string): string {
  const descriptions: Record<string, string> = {
    partner_promo: "Обычная акция или партнёрское предложение с вашей кнопкой и ссылкой.",
    redeem_key: "Ведёт пользователя к вводу купленного ключа или к продлению доступа.",
    support_recovery: "Помогает восстановить доступ или открыть поддержку в текущей поверхности.",
    telegram_bonus: "Предлагает привязать Telegram и получить доступный бонус.",
    release_update: "Сообщает о новой версии и ведёт к безопасному обновлению клиента.",
    incident_notice: "Показывает предупреждение о работах, сбое или временном ограничении.",
  };
  return descriptions[value] || "Сценарий определяет назначение блока и допустимое действие кнопки.";
}

function dateInput(value: string | null | undefined): string {
  if (!value || Number.isNaN(Date.parse(value))) return "";
  const date = new Date(value);
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

function countdownText(endsAt: string | null | undefined, now: number): string {
  const end = Date.parse(String(endsAt || ""));
  if (!Number.isFinite(end)) return "Нужно указать окончание";
  const total = Math.max(0, Math.floor((end - now) / 1000));
  const days = Math.floor(total / 86_400);
  const hours = Math.floor((total % 86_400) / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;
  const clock = [hours + days * 24, minutes, seconds].map((value) => String(value).padStart(2, "0")).join(":");
  return total > 0 ? clock : "00:00:00";
}

function isFirstPartyMediaUrl(value: string | null | undefined): boolean {
  if (!value?.trim()) return true;
  try {
    const url = new URL(value.trim());
    const host = url.hostname.toLowerCase().replace(/\.$/, "");
    return url.protocol === "https:" && (host === "pokrov.space" || host.endsWith(".pokrov.space"));
  } catch {
    return false;
  }
}

function promoValidationMessage(item: PromoSlotAssignment): string {
  if (!item.enabled) return "";
  const mediaUrl = item.media_url?.trim() || item.image_url?.trim() || "";
  for (const [label, value] of [
    ["медиа", mediaUrl],
    ["poster", item.poster_url || ""],
    ["fallback", item.fallback_image_url || ""],
  ] as const) {
    if (!isFirstPartyMediaUrl(value)) return `${label}: используйте загрузку в POKROV, внешние медиа запрещены.`;
  }
  if (item.image_layout === "media_only" && !mediaUrl) return "Для композиции «Только медиа» загрузите файл.";
  if (item.media_type && !mediaUrl) return "Выбран тип медиа, но файл не загружен.";
  if (item.media_type === "video" && (!item.poster_url?.trim() || !item.fallback_image_url?.trim())) {
    return "Для видео обязательны poster и статичный fallback.";
  }
  if (!item.title?.trim() && !item.body?.trim() && !item.badge_label?.trim() && !mediaUrl) {
    return "Включённая кампания должна содержать текст или медиа.";
  }
  if (item.countdown_mode === "ends_at" && !item.ends_at?.trim()) return "Для таймера укажите окончание акции.";
  const startsAt = Date.parse(item.starts_at || "");
  const endsAt = Date.parse(item.ends_at || "");
  if (Number.isFinite(startsAt) && Number.isFinite(endsAt) && startsAt >= endsAt) {
    return "Окончание акции должно быть позже начала.";
  }
  return "";
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
      enabled: current?.enabled ?? false,
      title: current?.title || "",
      body: current?.body || "",
      badge_label: current?.badge_label || "",
      image_url: current?.image_url || "",
      image_layout: current?.image_layout || "logo",
      media_type: current?.media_type || (current?.image_url ? "image" : "image"),
      media_url: current?.media_url || current?.image_url || "",
      poster_url: current?.poster_url || "",
      fallback_image_url: current?.fallback_image_url || "",
      media_mime: current?.media_mime || "",
      media_width: current?.media_width ?? null,
      media_height: current?.media_height ?? null,
      media_bytes: current?.media_bytes ?? null,
      media_duration_seconds: current?.media_duration_seconds ?? null,
      autoplay: current?.autoplay ?? false,
      loop: current?.loop ?? true,
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
      countdown_mode: current?.countdown_mode || "none",
      countdown_label: current?.countdown_label || "",
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
    media_url: item.media_url?.trim() || null,
    poster_url: item.poster_url?.trim() || null,
    fallback_image_url: item.fallback_image_url?.trim() || null,
    media_mime: item.media_mime?.trim() || null,
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
    countdown_label: item.countdown_label?.trim() || null,
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
  const [uploading, setUploading] = useState<"primary" | "poster" | "fallback" | null>(null);
  const [uploadError, setUploadError] = useState("");
  const [now, setNow] = useState(() => Date.now());
  const serverAssignments = useMemo(() => resource.data ? createAssignments(resource.data) : [], [resource.data]);
  const assignments = draftAssignments || serverAssignments;
  const dirty = draftAssignments !== null;
  const slotById = useMemo(() => new Map((resource.data?.catalog.slots || []).map((slot) => [slot.id, slot])), [resource.data]);
  const effectiveSelectedId = selectedId && assignments.some((item) => item.slot_id === selectedId) ? selectedId : assignments[0]?.slot_id || "";
  const selected = assignments.find((item) => item.slot_id === effectiveSelectedId) || null;
  const selectedSlot = selected ? slotById.get(selected.slot_id) || null : null;
  const previewMediaUrl = selected?.media_url || selected?.image_url || "";
  const previewMediaOnly = selected?.image_layout === "media_only" && Boolean(previewMediaUrl);

  useEffect(() => {
    if (selected?.countdown_mode !== "ends_at") return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [selected?.countdown_mode]);

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
    for (const item of assignments) {
      const message = promoValidationMessage(item);
      if (message) {
        setSelectedId(item.slot_id);
        setUploadError(message);
        return;
      }
    }
    setUploadError("");
    const payload = { assignments: sanitizeAssignments(assignments) };
    setRequest({ action: "promo_slots.update", target: { type: "config", id: "promo-slots" }, payload, endpoint: "/api/admin/promo-slots", method: "PUT" });
    setDialogOpen(true);
  }

  function reload() {
    setDraftAssignments(null);
    resource.reload();
  }

  async function uploadAsset(file: File | undefined, target: "primary" | "poster" | "fallback") {
    if (!file || !selected) return;
    setUploadError("");
    setUploading(target);
    try {
      const asset = await uploadPromoMedia(file);
      if (target !== "primary" && asset.media_type === "video") {
        throw new Error("Для poster и fallback нужна картинка, не видео.");
      }
      if (target === "primary") {
        update({
          media_type: asset.media_type,
          media_url: asset.url,
          image_url: asset.media_type === "video" ? selected.fallback_image_url || selected.poster_url || "" : asset.url,
          media_mime: asset.mime,
          media_width: asset.width,
          media_height: asset.height,
          media_bytes: asset.bytes,
        });
      } else if (target === "poster") {
        update({ poster_url: asset.url });
      } else {
        update({ fallback_image_url: asset.url, image_url: selected.media_type === "video" ? asset.url : selected.image_url });
      }
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Не удалось загрузить файл.");
    } finally {
      setUploading(null);
    }
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
              <label className="text-xs font-semibold">Сценарий блока
                <select value={selected.content_id} onChange={(event) => update({ content_id: event.target.value })} className={inputClass}>
                  {selectedSlot.allowed_content_ids.map((id) => <option key={id} value={id}>{contentLabel(id)}</option>)}
                </select>
                <span className="mt-1 block font-normal leading-5 text-[color:var(--atlas-text-muted)]">{contentDescription(selected.content_id)}</span>
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

            <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-xs font-semibold">Медиа</p>
                  <p className="mt-0.5 text-xs text-[color:var(--atlas-text-soft)]">PNG, JPEG, WebP, GIF, MP4 или WebM · до 24 МБ · хранение только в POKROV</p>
                </div>
                <label className="inline-flex min-h-10 cursor-pointer items-center gap-2 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] px-3 text-xs font-semibold">
                  <Upload size={15} /> {uploading === "primary" ? "Загружаем…" : "Загрузить файл"}
                  <input className="sr-only" type="file" accept="image/png,image/jpeg,image/webp,image/gif,video/mp4,video/webm" disabled={uploading !== null} onChange={(event) => void uploadAsset(event.target.files?.[0], "primary")} />
                </label>
              </div>
              {uploadError ? <p role="alert" className="mt-2 text-xs text-[color:var(--atlas-status-danger-text)]">{uploadError}</p> : null}
              <div className="mt-3 grid gap-3 md:grid-cols-[10rem,1fr,11rem]">
                <label className="text-xs font-semibold">Тип<select value={selected.media_type || "image"} onChange={(event) => update({ media_type: event.target.value })} className={inputClass}><option value="image">Картинка</option><option value="animated_image">GIF / анимация</option><option value="video">Видео</option></select></label>
                <label className="text-xs font-semibold">POKROV URL медиа<input value={selected.media_url || ""} onChange={(event) => update({ media_url: event.target.value, image_url: event.target.value })} placeholder="https://api.pokrov.space/…" className={inputClass} /></label>
                <label className="text-xs font-semibold">Композиция<select value={selected.image_layout || "logo"} onChange={(event) => update({ image_layout: event.target.value })} className={inputClass}><option value="logo">Логотип слева</option><option value="banner">Баннер сверху</option><option value="media_only">Только медиа</option></select></label>
              </div>
              {selected.media_type === "video" ? (
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <div className="text-xs font-semibold">Poster
                    <div className="flex gap-2"><input aria-label="URL poster" value={selected.poster_url || ""} onChange={(event) => update({ poster_url: event.target.value })} placeholder="Картинка до запуска" className={inputClass} /><span className="mt-1"><label className="grid h-10 w-10 cursor-pointer place-items-center rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)]" title="Загрузить poster"><Upload size={14} /><input className="sr-only" type="file" accept="image/png,image/jpeg,image/webp,image/gif" disabled={uploading !== null} onChange={(event) => void uploadAsset(event.target.files?.[0], "poster")} /></label></span></div>
                  </div>
                  <div className="text-xs font-semibold">Статичный fallback
                    <div className="flex gap-2"><input aria-label="URL статичного fallback" value={selected.fallback_image_url || ""} onChange={(event) => update({ fallback_image_url: event.target.value, image_url: event.target.value })} placeholder="Для экономии трафика / ошибки" className={inputClass} /><span className="mt-1"><label className="grid h-10 w-10 cursor-pointer place-items-center rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)]" title="Загрузить fallback"><Upload size={14} /><input className="sr-only" type="file" accept="image/png,image/jpeg,image/webp,image/gif" disabled={uploading !== null} onChange={(event) => void uploadAsset(event.target.files?.[0], "fallback")} /></label></span></div>
                  </div>
                </div>
              ) : null}
              <div className="mt-3 flex flex-wrap gap-5 text-xs font-semibold">
                <label className="inline-flex items-center gap-2"><input type="checkbox" checked={selected.autoplay === true} onChange={(event) => update({ autoplay: event.target.checked })} /> Автозапуск без звука</label>
                <label className="inline-flex items-center gap-2"><input type="checkbox" checked={selected.loop !== false} onChange={(event) => update({ loop: event.target.checked })} /> Повторять</label>
              </div>
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
                <div className="grid gap-3 md:grid-cols-[11rem,1fr,9rem]">
                  <label className="text-xs font-semibold">Таймер<select value={selected.countdown_mode || "none"} onChange={(event) => update({ countdown_mode: event.target.value })} className={inputClass}><option value="none">Без таймера</option><option value="ends_at">До окончания</option></select></label>
                  <label className="text-xs font-semibold">Подпись таймера<input value={selected.countdown_label || ""} onChange={(event) => update({ countdown_label: event.target.value })} placeholder="−70% · осталось" className={inputClass} /></label>
                  <label className="text-xs font-semibold">Приоритет<input type="number" min={0} max={10000} value={selected.sort_order} onChange={(event) => update({ sort_order: Number(event.target.value) || 0 })} className={inputClass} /></label>
                </div>
                {selected.countdown_mode === "ends_at" ? <div className="inline-flex items-center gap-2 rounded-full bg-[color:var(--atlas-surface-muted)] px-3 py-2 text-xs font-semibold tabular-nums"><Clock3 size={14} /> {selected.countdown_label || "Осталось"} {countdownText(selected.ends_at, now)}</div> : null}
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
            <div className="mb-2 flex items-center justify-between gap-2"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-[color:var(--atlas-text-soft)]">Телефон · 390 px</p><Badge tone={selected.dismissible === false ? "warning" : "neutral"}>{selected.dismissible === false ? "Обязательный" : "Можно закрыть"}</Badge></div>
            <div className="relative mx-auto w-full max-w-[390px] overflow-hidden rounded-[1.4rem] border" style={{ backgroundColor: selected.background_color || "#f4f0e8", borderColor: selected.accent_color || "#d6ddd7", color: selected.text_color || "#151a17" }}>
              {previewMediaUrl && (selected.image_layout === "banner" || previewMediaOnly) ? (
                selected.media_type === "video" ? <video src={previewMediaUrl} poster={selected.poster_url || selected.fallback_image_url || undefined} muted playsInline controls autoPlay={selected.autoplay === true} loop={selected.loop !== false} className={`${previewMediaOnly ? "aspect-[16/9]" : "h-36"} w-full bg-black/5 object-cover`} /> : (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={previewMediaUrl} alt="" className={`${previewMediaOnly ? "h-auto max-h-[28rem]" : "h-36"} w-full object-cover`} />
                )
              ) : null}
              {!previewMediaOnly ? <div className={`grid gap-3 p-4 ${selected.dismissible !== false ? "pr-14" : ""}`}>
                <div className="flex min-w-0 items-start gap-3">
                  {previewMediaUrl && selected.image_layout === "logo" ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={selected.media_type === "video" ? selected.poster_url || selected.fallback_image_url || previewMediaUrl : previewMediaUrl} alt="" className="h-14 w-14 shrink-0 rounded-2xl object-contain" />
                  ) : selected.image_layout === "logo" ? <span className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-black/5"><ImageIcon size={22} /></span> : null}
                  <div className="min-w-0 flex-1">
                    {selected.badge_label ? <p className="text-[10px] font-bold uppercase tracking-[0.14em] opacity-65">{selected.badge_label}</p> : null}
                    {selected.title ? <p className="font-semibold leading-tight">{selected.title}</p> : null}
                    {selected.body ? <p className="mt-1 text-xs leading-relaxed opacity-70">{selected.body}</p> : null}
                    {selected.countdown_mode === "ends_at" ? <p className="mt-2 inline-flex items-center gap-1.5 text-xs font-bold tabular-nums"><Clock3 size={13} /> {selected.countdown_label || "Осталось"} {countdownText(selected.ends_at, now)}</p> : null}
                  </div>
                </div>
                {selected.cta_label ? <span className="min-h-11 w-full rounded-xl px-4 py-3 text-center text-sm font-bold" style={{ backgroundColor: selected.button_color || selected.accent_color || "#0b6b53", color: selected.button_text_color || "#ffffff" }}>{selected.cta_label}</span> : null}
              </div> : null}
              {selected.dismissible !== false ? <button type="button" aria-label="Закрыть" className="absolute right-2 top-2 grid h-11 w-11 place-items-center rounded-full bg-white/85 text-black shadow-sm backdrop-blur"><X size={18} /></button> : null}
            </div>
            <div className="mt-3 flex items-start gap-2 rounded-xl bg-[color:var(--atlas-surface-muted)] p-3 text-xs text-[color:var(--atlas-text-soft)]"><Megaphone size={15} className="mt-0.5 shrink-0" /> После подтверждения клиент получит изменения при следующем обновлении данных. Выпуск нового APK не нужен.</div>
          </aside>
        </div>
      )}

      <ActionIntentDialog open={dialogOpen} request={request} onOpenChange={(open) => { setDialogOpen(open); if (!open) setRequest(null); }} onKnownOutcome={reload} onCheckState={resource.reload} />
    </Card>
  );
}
