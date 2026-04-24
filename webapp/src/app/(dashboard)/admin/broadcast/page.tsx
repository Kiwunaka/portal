"use client";

import {
  adminBroadcast,
  adminLiveUpdateCreate,
  adminLiveUpdateDelete,
  adminLiveUpdateUpdate,
  adminLiveUpdates,
  adminTemplateCreate,
  adminTemplateUpdate,
  adminTemplates,
  type AdminTemplateRow,
  type LiveUpdateRow,
} from "@/lib/api";
import {
  AdminConfirmDialog,
  AdminBadge,
  AdminPanelHeader,
  adminButtonClass,
  adminFieldClass,
  adminInsetPanelClass,
  adminPanelClass,
  adminTextAreaClass,
} from "@/components/admin/admin-shell";
import { useEffect, useMemo, useState } from "react";

function parseTgIds(input: string): number[] {
  return input
    .split(/[\s,;]+/)
    .map((token) => Number(token.trim()))
    .filter((value) => Number.isFinite(value) && value > 0)
    .map((value) => Math.floor(value));
}

const SEGMENT_OPTIONS = [
  { value: "all_active", label: "Все активные" },
  { value: "free", label: "Бесплатные" },
  { value: "paid", label: "Оплаченные" },
  { value: "expired", label: "Истекшие" },
];

const TEMPLATE_GROUPS = [
  { key: "retention_welcome_a", label: "Welcome A", flow: "Welcome" },
  { key: "retention_welcome_b", label: "Welcome B", flow: "Welcome" },
  { key: "retention_t3_a", label: "T-3 A", flow: "Retention" },
  { key: "retention_t3_b", label: "T-3 B", flow: "Retention" },
  { key: "retention_t1_a", label: "T-1 A", flow: "Retention" },
  { key: "retention_t1_b", label: "T-1 B", flow: "Retention" },
  { key: "retention_t0_a", label: "T0 A", flow: "Retention" },
  { key: "retention_t0_b", label: "T0 B", flow: "Retention" },
  { key: "retention_reactivation_a", label: "Reactivation A", flow: "Reactivation" },
  { key: "retention_reactivation_b", label: "Reactivation B", flow: "Reactivation" },
];

type LiveUpdateDialog =
  | { kind: "create"; title: string; summary: string; link: string; sortOrder: string; reason: string }
  | { kind: "edit"; id: number; title: string; summary: string; link: string; isActive: boolean; reason: string }
  | { kind: "delete"; id: number; reason: string }
  | null;

type TemplateDialog = { key: string; text: string; mode: "create" | "edit"; title: string } | null;

export default function AdminBroadcastPage() {
  const [segment, setSegment] = useState("all_active");
  const [limit, setLimit] = useState(200);
  const [tgIdsRaw, setTgIdsRaw] = useState("");
  const [text, setText] = useState("");
  const [confirmReason, setConfirmReason] = useState("");
  const [confirmBroadcast, setConfirmBroadcast] = useState(false);
  const [liveUpdates, setLiveUpdates] = useState<LiveUpdateRow[]>([]);
  const [templates, setTemplates] = useState<AdminTemplateRow[]>([]);
  const [result, setResult] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [liveDialog, setLiveDialog] = useState<LiveUpdateDialog>(null);
  const [templateDialog, setTemplateDialog] = useState<TemplateDialog>(null);

  const templatesByKey = useMemo(() => new Map(templates.map((row) => [row.key, row])), [templates]);

  const loadLiveUpdates = async (): Promise<void> => {
    try {
      setLiveUpdates(await adminLiveUpdates(true));
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not load live updates."));
    }
  };

  const loadTemplates = async (): Promise<void> => {
    try {
      setTemplates(await adminTemplates(200));
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not load templates."));
    }
  };

  useEffect(() => {
    void loadLiveUpdates();
    void loadTemplates();
  }, []);

  const submit = async (): Promise<void> => {
    if (!text.trim() || !confirmReason.trim()) {
      setError("Укажите текст сообщения и причину действия.");
      return;
    }
    setBusy(true);
    setError("");
    setResult("");
    try {
      const tgIds = parseTgIds(tgIdsRaw);
      const out = await adminBroadcast({
        text: text.trim(),
        segment,
        limit: Math.max(1, Math.min(1000, Number(limit) || 1)),
        tg_ids: tgIds.length ? tgIds : undefined,
        operator_reason: confirmReason.trim(),
      });
      setResult(`Отправлено: ${out?.sent ?? 0}, ошибок: ${out?.failed ?? 0}, попыток: ${out?.attempted ?? 0}.`);
      setConfirmBroadcast(false);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось отправить рассылку."));
    } finally {
      setBusy(false);
    }
  };

  const openTemplateDialog = (templateKey: string): void => {
    const meta = TEMPLATE_GROUPS.find((row) => row.key === templateKey);
    if (!meta) return;
    const existing = templatesByKey.get(templateKey);
    setTemplateDialog({ key: templateKey, text: existing?.text || "", mode: existing ? "edit" : "create", title: meta.label });
  };

  const submitLiveDialog = async (): Promise<void> => {
    if (!liveDialog) return;
    if ("reason" in liveDialog && !liveDialog.reason.trim()) {
      setError("Укажите причину действия оператора.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      if (liveDialog.kind === "create") {
        await adminLiveUpdateCreate({
          title: liveDialog.title.trim(),
          summary: liveDialog.summary.trim(),
          link: liveDialog.link.trim(),
          is_active: true,
          sort_order: Math.max(0, Number(liveDialog.sortOrder || 100)),
        });
        setResult("Новость создана.");
      } else if (liveDialog.kind === "edit") {
        await adminLiveUpdateUpdate(liveDialog.id, {
          title: liveDialog.title.trim(),
          summary: liveDialog.summary.trim(),
          link: liveDialog.link.trim(),
          is_active: liveDialog.isActive,
        });
        setResult(`Новость #${liveDialog.id} обновлена.`);
      } else {
        await adminLiveUpdateDelete(liveDialog.id);
        setResult(`Новость #${liveDialog.id} удалена.`);
      }
      await loadLiveUpdates();
      setLiveDialog(null);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось сохранить новость."));
    } finally {
      setBusy(false);
    }
  };

  const submitTemplateDialog = async (): Promise<void> => {
    if (!templateDialog || !templateDialog.text.trim()) {
      setError("Укажите текст шаблона.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      if (templateDialog.mode === "create") {
        await adminTemplateCreate({ key: templateDialog.key, text: templateDialog.text.trim() });
        setResult(`Шаблон ${templateDialog.title} создан.`);
      } else {
        await adminTemplateUpdate(templateDialog.key, { text: templateDialog.text.trim() });
        setResult(`Шаблон ${templateDialog.title} обновлен.`);
      }
      await loadTemplates();
      setTemplateDialog(null);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось сохранить шаблон."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-4">
      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader
          eyebrow="сообщения"
          title="Рассылки и шаблоны"
          description="Плотная операторская панель: сегмент, лимит, предпросмотр и обязательная причина перед live-отправкой."
          actions={
            <button className={adminButtonClass("secondary", "sm")} type="button" onClick={() => { void loadLiveUpdates(); void loadTemplates(); }}>
              Обновить
            </button>
          }
        />
        <div className="flex flex-wrap gap-2">
          <AdminBadge tone="warning">нужна причина</AdminBadge>
          <AdminBadge>предпросмотр</AdminBadge>
          <AdminBadge tone="accent">{templates.length} шаблонов</AdminBadge>
        </div>
      </article>

      {result ? <div className={adminPanelClass("success")}>{result}</div> : null}
      {error ? <div className={adminPanelClass("danger")}>{error}</div> : null}

      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader eyebrow="рассылка" title="Отправка рассылки" />
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <label className="text-xs text-slate-400">
            Сегмент
            <select value={segment} onChange={(event) => setSegment(event.target.value)} className={`mt-1 ${adminFieldClass}`}>
              {SEGMENT_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
          <label className="text-xs text-slate-400">
            Лимит
            <input type="number" value={limit} onChange={(event) => setLimit(Number(event.target.value || 0))} className={`mt-1 ${adminFieldClass}`} />
          </label>
          <label className="text-xs text-slate-400 xl:col-span-2">
            Telegram ID вручную
            <input value={tgIdsRaw} onChange={(event) => setTgIdsRaw(event.target.value)} className={`mt-1 ${adminFieldClass}`} placeholder="123456789, 987654321" />
          </label>
        </div>
        <div className="mt-3 grid gap-4 lg:grid-cols-[minmax(0,1fr),minmax(260px,0.42fr)]">
          <label className="block text-xs text-slate-400">
            Текст сообщения
            <textarea value={text} onChange={(event) => setText(event.target.value)} rows={7} placeholder="Текст рассылки" className={`mt-1 ${adminTextAreaClass}`} />
          </label>
          <div className={adminInsetPanelClass}>
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">предпросмотр</p>
            <div className="mt-3 min-h-[132px] whitespace-pre-line rounded-[0.85rem] border border-[#c6e6db] bg-[#ffffff] p-3 text-sm text-slate-300">
              {text.trim() || <span className="text-slate-500">Предпросмотр сообщения появится здесь.</span>}
            </div>
          </div>
        </div>
        <div className="mt-3 flex justify-end">
          <button className={adminButtonClass("primary")} type="button" onClick={() => setConfirmBroadcast(true)} disabled={busy || !text.trim()}>
            Отправить рассылку
          </button>
        </div>
      </article>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr),minmax(360px,0.8fr)]">
        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader
            eyebrow="удержание"
            title="Шаблоны"
            actions={<AdminBadge>{templates.length} сохранено</AdminBadge>}
          />
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {TEMPLATE_GROUPS.map((item) => {
              const existing = templatesByKey.get(item.key);
              return (
                <article key={item.key} className={adminInsetPanelClass}>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500">{item.flow}</p>
                      <h4 className="mt-1 text-sm font-semibold text-slate-50">{item.label}</h4>
                    </div>
                    <AdminBadge tone={existing ? "success" : "warning"}>{existing ? "задан" : "пусто"}</AdminBadge>
                  </div>
                  <p className="mt-3 line-clamp-4 rounded-[0.85rem] border border-[#c6e6db] bg-[#ffffff] p-3 text-xs leading-5 text-slate-400">
                    {existing?.text || "Шаблон еще не настроен."}
                  </p>
                  <button className={`${adminButtonClass("secondary", "xs")} mt-3`} type="button" onClick={() => openTemplateDialog(item.key)} disabled={busy}>
                    {existing ? "Изменить" : "Создать"}
                  </button>
                </article>
              );
            })}
          </div>
        </article>

        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader
            eyebrow="новости"
            title="Карточки новостей"
            actions={
              <button className={adminButtonClass("primary", "sm")} type="button" onClick={() => setLiveDialog({ kind: "create", title: "", summary: "", link: "", sortOrder: "100", reason: "" })}>
                Новая карточка
              </button>
            }
          />
          <div className="space-y-3">
            {liveUpdates.map((row) => (
              <div key={row.id} className={adminInsetPanelClass}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-50">{row.title}</p>
                    <p className="mt-1 line-clamp-2 text-xs text-slate-500">{row.summary || "Без описания"}</p>
                    {row.link ? <p className="mt-1 truncate text-xs text-emerald-300">{row.link}</p> : null}
                  </div>
                  <AdminBadge tone={row.is_active ? "success" : "warning"}>{row.is_active ? "активна" : "скрыта"}</AdminBadge>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button className={adminButtonClass("secondary", "xs")} type="button" onClick={() => setLiveDialog({ kind: "edit", id: row.id, title: row.title || "", summary: row.summary || "", link: row.link || "", isActive: Boolean(row.is_active), reason: "" })}>
                    Изменить
                  </button>
                  <button className={adminButtonClass("danger", "xs")} type="button" onClick={() => setLiveDialog({ kind: "delete", id: row.id, reason: "" })}>
                    Удалить
                  </button>
                </div>
              </div>
            ))}
            {!liveUpdates.length ? <p className="text-xs text-slate-500">Новостей пока нет.</p> : null}
          </div>
        </article>
      </div>

      {liveDialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/70 p-4">
          <div className={`${adminPanelClass("neutral")} w-full max-w-xl`}>
            {liveDialog.kind === "delete" ? (
              <>
                <h3 className="text-xl font-semibold">Удалить новость #{liveDialog.id}</h3>
                <input value={liveDialog.reason} onChange={(event) => setLiveDialog({ ...liveDialog, reason: event.target.value })} className={`mt-4 ${adminFieldClass}`} placeholder="Причина действия" />
              </>
            ) : (
              <>
                <h3 className="text-xl font-semibold">{liveDialog.kind === "create" ? "Новая новость" : `Новость #${liveDialog.id}`}</h3>
                <input value={liveDialog.title} onChange={(event) => setLiveDialog({ ...liveDialog, title: event.target.value })} className={`mt-4 ${adminFieldClass}`} placeholder="Заголовок" />
                <textarea value={liveDialog.summary} onChange={(event) => setLiveDialog({ ...liveDialog, summary: event.target.value })} rows={4} className={`mt-3 ${adminTextAreaClass}`} placeholder="Описание" />
                <input value={liveDialog.link} onChange={(event) => setLiveDialog({ ...liveDialog, link: event.target.value })} className={`mt-3 ${adminFieldClass}`} placeholder="Ссылка" />
                {liveDialog.kind === "create" ? (
                  <input value={liveDialog.sortOrder} onChange={(event) => setLiveDialog({ ...liveDialog, sortOrder: event.target.value })} type="number" className={`mt-3 ${adminFieldClass}`} placeholder="Порядок" />
                ) : (
                  <label className="mt-3 inline-flex items-center gap-2 text-sm text-slate-400">
                    <input type="checkbox" checked={liveDialog.isActive} onChange={(event) => setLiveDialog({ ...liveDialog, isActive: event.target.checked })} />
                    Активна
                  </label>
                )}
                <input value={liveDialog.reason} onChange={(event) => setLiveDialog({ ...liveDialog, reason: event.target.value })} className={`mt-3 ${adminFieldClass}`} placeholder="Причина действия" />
              </>
            )}
            <div className="mt-4 flex justify-end gap-2">
              <button className={adminButtonClass("secondary")} type="button" onClick={() => setLiveDialog(null)}>Отмена</button>
              <button className={adminButtonClass(liveDialog.kind === "delete" ? "danger" : "primary")} type="button" disabled={busy || !liveDialog.reason.trim()} onClick={() => void submitLiveDialog()}>
                {liveDialog.kind === "delete" ? "Удалить" : "Сохранить"}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {templateDialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/70 p-4">
          <div className={`${adminPanelClass("neutral")} w-full max-w-2xl`}>
            <h3 className="text-xl font-semibold">{templateDialog.title}</h3>
            <p className="mt-1 text-xs uppercase tracking-[0.12em] text-slate-500">{templateDialog.key}</p>
            <textarea value={templateDialog.text} onChange={(event) => setTemplateDialog({ ...templateDialog, text: event.target.value })} rows={12} className={`mt-4 ${adminTextAreaClass}`} placeholder="Текст шаблона" />
            <div className="mt-4 flex justify-end gap-2">
              <button className={adminButtonClass("secondary")} type="button" onClick={() => setTemplateDialog(null)}>Отмена</button>
              <button className={adminButtonClass("primary")} type="button" disabled={busy || !templateDialog.text.trim()} onClick={() => void submitTemplateDialog()}>
                {templateDialog.mode === "create" ? "Создать" : "Сохранить"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
      <AdminConfirmDialog
        open={confirmBroadcast}
        title="Подтвердить отправку рассылки"
        description="Сообщение будет отправлено выбранному сегменту или указанным Telegram ID. Укажите причину для аудита."
        reason={confirmReason}
        onReasonChange={setConfirmReason}
        onCancel={() => setConfirmBroadcast(false)}
        onConfirm={() => void submit()}
        confirmLabel="Отправить"
        busy={busy}
      />
    </section>
  );
}
