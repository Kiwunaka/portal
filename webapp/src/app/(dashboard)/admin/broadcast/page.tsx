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
import { Check, ExternalLink, Eye, Loader2, Megaphone, Newspaper, PencilLine, Plus, Send, Trash2, X } from "lucide-react";
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
  { value: "paid", label: "Платные" },
  { value: "expired", label: "Истекшие" },
];

const RETENTION_TEMPLATE_GROUPS = [
  { key: "retention_welcome_a", label: "Welcome A", flow: "Welcome", hint: "Первый вариант приветствия для новых пользователей." },
  { key: "retention_welcome_b", label: "Welcome B", flow: "Welcome", hint: "Второй вариант приветствия с альтернативным тоном." },
  { key: "retention_t3_a", label: "За 3 дня (A)", flow: "Retention", hint: "Шаблон для напоминания за три дня до окончания подписки." },
  { key: "retention_t3_b", label: "За 3 дня (B)", flow: "Retention", hint: "Альтернатива для T-3." },
  { key: "retention_t1_a", label: "За 1 день (A)", flow: "Retention", hint: "Шаблон для мягкого напоминания за день до конца." },
  { key: "retention_t1_b", label: "За 1 день (B)", flow: "Retention", hint: "Альтернатива для T-1." },
  { key: "retention_t0_a", label: "В день окончания (A)", flow: "Retention", hint: "Сообщение на день, когда подписка уже закончилась." },
  { key: "retention_t0_b", label: "В день окончания (B)", flow: "Retention", hint: "Альтернативный вариант сообщения для T0." },
  { key: "retention_reactivation_a", label: "Реактивация A", flow: "Reactivation", hint: "Шаблон для возврата ушедших пользователей." },
  { key: "retention_reactivation_b", label: "Реактивация B", flow: "Reactivation", hint: "Альтернативный вариант для реактивационной цепочки." },
];

type LiveUpdateDialog =
  | { kind: "create"; title: string; summary: string; link: string; sortOrder: string }
  | { kind: "edit"; id: number; title: string; summary: string; link: string; isActive: boolean }
  | { kind: "delete"; id: number }
  | null;

type TemplateDialog =
  | { key: string; text: string; mode: "create" | "edit"; title: string; hint: string }
  | null;

export default function AdminBroadcastPage() {
  const [segment, setSegment] = useState("all_active");
  const [limit, setLimit] = useState(200);
  const [tgIdsRaw, setTgIdsRaw] = useState("");
  const [text, setText] = useState("");
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
      const rows = await adminLiveUpdates(true);
      setLiveUpdates(rows);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось загрузить новости."));
    }
  };

  const loadTemplates = async (): Promise<void> => {
    try {
      const rows = await adminTemplates(200);
      setTemplates(rows);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось загрузить шаблоны."));
    }
  };

  useEffect(() => {
    void loadLiveUpdates();
    void loadTemplates();
  }, []);

  const submit = async (): Promise<void> => {
    if (!text.trim()) return;
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
      });
      setResult(`Отправлено: ${out?.sent ?? 0}, ошибок: ${out?.failed ?? 0}, адресатов: ${out?.attempted ?? 0}.`);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось отправить рассылку."));
    } finally {
      setBusy(false);
    }
  };

  const createLiveUpdate = (): void => {
    setLiveDialog({
      kind: "create",
      title: "Новая новость",
      summary: "Короткий анонс для главной ленты.",
      link: "https://t.me/pokrov_vpnbot",
      sortOrder: "100",
    });
  };

  const editLiveUpdate = (row: LiveUpdateRow): void => {
    setLiveDialog({
      kind: "edit",
      id: row.id,
      title: row.title || "",
      summary: row.summary || "",
      link: row.link || "",
      isActive: Boolean(row.is_active),
    });
  };

  const removeLiveUpdate = (id: number): void => {
    setLiveDialog({ kind: "delete", id });
  };

  const openTemplateDialog = (templateKey: string): void => {
    const meta = RETENTION_TEMPLATE_GROUPS.find((row) => row.key === templateKey);
    if (!meta) return;
    const existing = templatesByKey.get(templateKey);
    setTemplateDialog({
      key: templateKey,
      text: existing?.text || "",
      mode: existing ? "edit" : "create",
      title: meta.label,
      hint: meta.hint,
    });
  };

  const submitLiveDialog = async (): Promise<void> => {
    if (!liveDialog) return;
    setBusy(true);
    setError("");
    try {
      if (liveDialog.kind === "create") {
        if (!liveDialog.title.trim()) {
          setError("У новости должен быть заголовок.");
          setBusy(false);
          return;
        }
        const sortOrder = Number(liveDialog.sortOrder || 100);
        await adminLiveUpdateCreate({
          title: liveDialog.title.trim(),
          summary: liveDialog.summary.trim(),
          link: liveDialog.link.trim(),
          is_active: true,
          sort_order: Number.isFinite(sortOrder) ? Math.max(0, Math.floor(sortOrder)) : 100,
        });
        setResult("Новость создана.");
      } else if (liveDialog.kind === "edit") {
        if (!liveDialog.title.trim()) {
          setError("У новости должен быть заголовок.");
          setBusy(false);
          return;
        }
        await adminLiveUpdateUpdate(liveDialog.id, {
          title: liveDialog.title.trim(),
          summary: liveDialog.summary.trim(),
          link: liveDialog.link.trim(),
          is_active: liveDialog.isActive,
        });
        setResult(`Новость #${liveDialog.id} обновлена.`);
      } else if (liveDialog.kind === "delete") {
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
    if (!templateDialog) return;
    const textValue = templateDialog.text.trim();
    if (!textValue) {
      setError("Шаблон не может быть пустым.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      if (templateDialog.mode === "create") {
        await adminTemplateCreate({ key: templateDialog.key, text: textValue });
        setResult(`Шаблон ${templateDialog.title} создан.`);
      } else {
        await adminTemplateUpdate(templateDialog.key, { text: textValue });
        setResult(`Шаблон ${templateDialog.title} обновлён.`);
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
    <section className="space-y-5">
      <article className="stat-card p-5 sm:p-6 space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
          <div className="stat-icon stat-icon-rose">
            <Megaphone size={20} />
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="font-display text-xl font-bold">Рассылки</h2>
            <p className="text-xs text-slate-500">
              Отсюда отправляются массовые сообщения и управляются новости на главной. Перед запуском проверьте сегмент, лимит и текст.
            </p>
          </div>
        </div>
        <div className="rounded-xl bg-white/60 p-3 text-xs leading-relaxed text-slate-500 dark:bg-white/5 dark:text-slate-400">
          Для Telegram ID можно указать список через пробел, запятую или точку с запятой. Если список пустой, рассылка пойдёт по выбранному сегменту.
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <div>
            <label className="mb-1 block text-[10px] uppercase tracking-[0.1em] text-slate-500">Сегмент</label>
            <select
              value={segment}
              onChange={(event) => setSegment(event.target.value)}
              className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            >
              {SEGMENT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-[10px] uppercase tracking-[0.1em] text-slate-500">Лимит</label>
            <input
              type="number"
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value || 0))}
              className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            />
          </div>
          <div className="xl:col-span-2">
            <label className="mb-1 block text-[10px] uppercase tracking-[0.1em] text-slate-500">Telegram ID</label>
            <input
              value={tgIdsRaw}
              onChange={(event) => setTgIdsRaw(event.target.value)}
              className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
              placeholder="Например: 123456789, 987654321"
            />
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr),minmax(260px,0.4fr)]">
          <div>
            <label className="mb-1 block text-[10px] uppercase tracking-[0.1em] text-slate-500">Текст рассылки</label>
            <textarea
              value={text}
              onChange={(event) => setText(event.target.value)}
              rows={6}
              placeholder="Введите текст сообщения для отправки."
              className="w-full resize-none rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            />
          </div>
          <div>
            <label className="mb-1 flex items-center gap-1 text-[10px] uppercase tracking-[0.1em] text-slate-500">
              <Eye size={10} /> Превью
            </label>
            <div className="min-h-[120px] rounded-xl bg-white/50 p-3 text-sm whitespace-pre-line text-slate-600 dark:bg-white/5 dark:text-slate-300">
              {text.trim() || <span className="text-slate-400 italic">Здесь появится текст сообщения</span>}
            </div>
          </div>
        </div>

        <button
          className="btn-primary inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em] w-full sm:w-auto"
          type="button"
          onClick={() => void submit()}
          disabled={busy || !text.trim()}
        >
          {busy ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
          {busy ? "Отправляем..." : "Отправить"}
        </button>
      </article>

      <article className="glass-card p-5">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="stat-icon stat-icon-violet">
              <PencilLine size={20} />
            </div>
            <div className="min-w-0">
              <h3 className="font-display text-xl font-bold">Retention-шаблоны</h3>
              <p className="text-xs text-slate-500">
                Здесь редактируются цепочки приветствия, удержания и реактивации. Шаблоны используются в автоматических сообщениях.
              </p>
            </div>
          </div>
          <span className="badge badge-info self-start sm:self-auto">{templates.length} шаблонов</span>
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {RETENTION_TEMPLATE_GROUPS.map((item) => {
            const existing = templatesByKey.get(item.key);
            return (
              <article key={item.key} className="node-card">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">{item.flow}</p>
                    <h4 className="mt-1 text-sm font-bold">{item.label}</h4>
                  </div>
                  <span className={`badge ${existing ? "badge-success" : "badge-warning"}`}>{existing ? "Есть" : "Нет"}</span>
                </div>
                <p className="mt-2 text-xs text-slate-500">{item.hint}</p>
                <div className="mt-3 rounded-xl bg-white/50 p-3 text-xs leading-relaxed text-slate-600 dark:bg-white/5 dark:text-slate-300">
                  {(existing?.text || "Шаблон пока не задан.").slice(0, 240)}
                </div>
                <div className="mt-3 flex justify-end">
                  <button
                    className="outline-btn inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold"
                    type="button"
                    onClick={() => openTemplateDialog(item.key)}
                    disabled={busy}
                  >
                    <PencilLine size={12} />
                    {existing ? "Редактировать" : "Создать"}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      </article>

      <article className="glass-card p-5">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="stat-icon stat-icon-blue">
              <Newspaper size={20} />
            </div>
            <div className="min-w-0">
              <h3 className="font-display text-xl font-bold">Новости и анонсы</h3>
              <p className="text-xs text-slate-500">
                Управляйте короткими карточками на главной и связанными ссылками.
              </p>
            </div>
          </div>
          <button className="btn-primary inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => createLiveUpdate()} disabled={busy}>
            <Plus size={14} /> Новая новость
          </button>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          {liveUpdates.map((row) => (
            <div key={row.id} className="node-card">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`status-dot ${row.is_active ? "status-dot-online" : "status-dot-stale"}`} />
                    <p className="text-sm font-bold">{row.title}</p>
                  </div>
                  <p className="mt-1 line-clamp-2 text-xs text-slate-500">{row.summary || "Без описания"}</p>
                </div>
                <span className={`badge ${row.is_active ? "badge-success" : "badge-danger"}`}>{row.is_active ? "Активна" : "Скрыта"}</span>
              </div>
              <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                {row.link ? (
                  <a href={row.link} target="_blank" className="inline-flex items-center gap-1 text-xs text-violet-600 hover:underline dark:text-violet-300">
                    <ExternalLink size={10} /> Открыть
                  </a>
                ) : (
                  <span />
                )}
                <div className="flex gap-1.5">
                  <button className="outline-btn inline-flex items-center gap-1 rounded-lg px-2.5 py-1 text-[10px] font-semibold" type="button" onClick={() => editLiveUpdate(row)} disabled={busy}>
                    <PencilLine size={10} /> Править
                  </button>
                  <button className="outline-btn inline-flex items-center gap-1 rounded-lg px-2.5 py-1 text-[10px] font-semibold text-rose-500" type="button" onClick={() => removeLiveUpdate(row.id)} disabled={busy}>
                    <Trash2 size={10} /> Удалить
                  </button>
                </div>
              </div>
            </div>
          ))}
          {liveUpdates.length === 0 ? (
            <div className="empty-state col-span-full">
              <Newspaper size={28} />
              <p className="text-xs">Пока нет опубликованных новостей</p>
            </div>
          ) : null}
        </div>
      </article>

      {result ? (
        <div className="stat-card flex items-center gap-3 p-4">
          <div className="stat-icon stat-icon-emerald">
            <Check size={18} />
          </div>
          <p className="text-sm font-medium text-emerald-600 dark:text-emerald-300">{result}</p>
        </div>
      ) : null}
      {error ? (
        <div className="stat-card flex items-center gap-3 p-4">
          <div className="stat-icon stat-icon-rose">
            <X size={18} />
          </div>
          <p className="text-sm font-medium text-rose-500">{error}</p>
        </div>
      ) : null}

      {liveDialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/65 p-4">
          <div className="glass-card w-full max-w-xl p-5">
            {liveDialog.kind === "create" || liveDialog.kind === "edit" ? (
              <>
                <h3 className="font-display text-xl font-semibold">
                  {liveDialog.kind === "create" ? "Новая новость" : `Новость #${liveDialog.id}`}
                </h3>
                <div className="mt-4 space-y-3">
                  <input
                    value={liveDialog.title}
                    onChange={(event) =>
                      setLiveDialog((prev) =>
                        prev && (prev.kind === "create" || prev.kind === "edit") ? { ...prev, title: event.target.value } : prev,
                      )
                    }
                    className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                    placeholder="Заголовок"
                  />
                  <textarea
                    value={liveDialog.summary}
                    onChange={(event) =>
                      setLiveDialog((prev) =>
                        prev && (prev.kind === "create" || prev.kind === "edit") ? { ...prev, summary: event.target.value } : prev,
                      )
                    }
                    rows={4}
                    className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                    placeholder="Короткое описание"
                  />
                  <input
                    value={liveDialog.link}
                    onChange={(event) =>
                      setLiveDialog((prev) =>
                        prev && (prev.kind === "create" || prev.kind === "edit") ? { ...prev, link: event.target.value } : prev,
                      )
                    }
                    className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                    placeholder="Ссылка"
                  />
                  {liveDialog.kind === "create" ? (
                    <input
                      value={liveDialog.sortOrder}
                      onChange={(event) =>
                        setLiveDialog((prev) => (prev && prev.kind === "create" ? { ...prev, sortOrder: event.target.value } : prev))
                      }
                      type="number"
                      min={0}
                      className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                      placeholder="Порядок сортировки"
                    />
                  ) : (
                    <label className="inline-flex items-center gap-2 text-sm text-slate-500">
                      <input
                        type="checkbox"
                        checked={liveDialog.isActive}
                        onChange={(event) =>
                          setLiveDialog((prev) => (prev && prev.kind === "edit" ? { ...prev, isActive: event.target.checked } : prev))
                        }
                      />
                      Публиковать карточку
                    </label>
                  )}
                </div>
                <div className="mt-4 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setLiveDialog(null)}>
                    Отмена
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void submitLiveDialog()}>
                    Сохранить
                  </button>
                </div>
              </>
            ) : null}

            {liveDialog.kind === "delete" ? (
              <>
                <h3 className="font-display text-xl font-semibold">Удалить новость #{liveDialog.id}?</h3>
                <p className="mt-2 text-sm text-slate-500">Карточка исчезнет из ленты и перестанет показываться пользователям.</p>
                <div className="mt-4 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setLiveDialog(null)}>
                    Отмена
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void submitLiveDialog()}>
                    Удалить
                  </button>
                </div>
              </>
            ) : null}
          </div>
        </div>
      ) : null}

      {templateDialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/65 p-4">
          <div className="glass-card w-full max-w-2xl p-5">
            <h3 className="font-display text-xl font-semibold">{templateDialog.title}</h3>
            <p className="mt-2 text-sm text-slate-500">{templateDialog.hint}</p>
            <p className="mt-1 text-xs uppercase tracking-[0.1em] text-slate-500">{templateDialog.key}</p>
            <textarea
              value={templateDialog.text}
              onChange={(event) => setTemplateDialog((prev) => (prev ? { ...prev, text: event.target.value } : prev))}
              rows={12}
              className="mt-4 w-full rounded-2xl border border-violet-200/50 bg-white/80 px-3 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
              placeholder="Текст шаблона. Доступны переменные {expiry_date}, {channel}, {discount_pct}."
            />
            <div className="mt-4 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setTemplateDialog(null)}>
                Отмена
              </button>
              <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void submitTemplateDialog()}>
                {templateDialog.mode === "create" ? "Создать" : "Сохранить"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
