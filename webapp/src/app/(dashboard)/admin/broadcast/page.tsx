"use client";

import {
  adminBroadcast,
  adminLiveUpdateCreate,
  adminLiveUpdateDelete,
  adminLiveUpdateUpdate,
  adminLiveUpdates,
  type LiveUpdateRow,
} from "@/lib/api";
import { Check, ExternalLink, Eye, Loader2, Megaphone, Newspaper, PencilLine, Plus, Send, Trash2, X } from "lucide-react";
import { useEffect, useState } from "react";

function parseTgIds(input: string): number[] {
  return input
    .split(/[\s,;]+/)
    .map((token) => Number(token.trim()))
    .filter((value) => Number.isFinite(value) && value > 0)
    .map((value) => Math.floor(value));
}

const SEGMENT_OPTIONS = [
  { value: "all_active", label: "Все активные", icon: "🌐" },
  { value: "free", label: "Free", icon: "🆓" },
  { value: "paid", label: "Paid", icon: "💎" },
  { value: "expired", label: "Expired", icon: "⏰" },
];

export default function AdminBroadcastPage() {
  const [segment, setSegment] = useState("all_active");
  const [limit, setLimit] = useState(200);
  const [tgIdsRaw, setTgIdsRaw] = useState("");
  const [text, setText] = useState("");
  const [liveUpdates, setLiveUpdates] = useState<LiveUpdateRow[]>([]);
  const [result, setResult] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const loadLiveUpdates = async (): Promise<void> => {
    try {
      const rows = await adminLiveUpdates(true);
      setLiveUpdates(rows);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка загрузки live-updates"));
    }
  };

  useEffect(() => {
    void loadLiveUpdates();
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
      setResult(`Отправлено: ${out?.sent ?? 0}, ошибок: ${out?.failed ?? 0}, попыток: ${out?.attempted ?? 0}`);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка рассылки"));
    } finally {
      setBusy(false);
    }
  };

  const createLiveUpdate = async (): Promise<void> => {
    const title = window.prompt("Заголовок новости:", "Обновление сервиса");
    if (!title?.trim()) return;
    const summary = window.prompt("Краткое описание:", "Новые улучшения стабильности и скорости") || "";
    const link = window.prompt("Ссылка:", "https://t.me/portal_privacy_bot") || "";
    const sortOrder = Number(window.prompt("Порядок (sort_order):", "100") || 100);
    setBusy(true);
    setError("");
    try {
      await adminLiveUpdateCreate({
        title: title.trim(),
        summary: summary.trim(),
        link: link.trim(),
        is_active: true,
        sort_order: Number.isFinite(sortOrder) ? Math.max(0, Math.floor(sortOrder)) : 100,
      });
      await loadLiveUpdates();
      setResult("Live-update добавлен.");
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось создать live-update"));
    } finally {
      setBusy(false);
    }
  };

  const editLiveUpdate = async (row: LiveUpdateRow): Promise<void> => {
    const title = window.prompt("Заголовок:", row.title || "");
    if (!title?.trim()) return;
    const summary = window.prompt("Описание:", row.summary || "") || "";
    const link = window.prompt("Ссылка:", row.link || "") || "";
    const activeRaw = window.prompt("Активно? (yes/no)", row.is_active ? "yes" : "no") || "yes";
    setBusy(true);
    setError("");
    try {
      await adminLiveUpdateUpdate(row.id, {
        title: title.trim(),
        summary: summary.trim(),
        link: link.trim(),
        is_active: activeRaw.trim().toLowerCase() !== "no",
      });
      await loadLiveUpdates();
      setResult(`Live-update #${row.id} обновлен.`);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось обновить live-update"));
    } finally {
      setBusy(false);
    }
  };

  const removeLiveUpdate = async (id: number): Promise<void> => {
    if (!window.confirm(`Удалить live-update #${id}?`)) return;
    setBusy(true);
    setError("");
    try {
      await adminLiveUpdateDelete(id);
      await loadLiveUpdates();
      setResult(`Live-update #${id} удален.`);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось удалить live-update"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-5">
      {/* ── Broadcast composer ─────────────────────────── */}
      <article className="stat-card p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="stat-icon stat-icon-rose">
            <Megaphone size={20} />
          </div>
          <div>
            <h2 className="font-display text-xl font-bold">Broadcast</h2>
            <p className="text-xs text-slate-500">Массовая рассылка пользователям</p>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <div>
            <label className="block text-[10px] uppercase tracking-[0.1em] text-slate-500 mb-1">Сегмент</label>
            <select
              value={segment}
              onChange={(event) => setSegment(event.target.value)}
              className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            >
              {SEGMENT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.icon} {opt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-[10px] uppercase tracking-[0.1em] text-slate-500 mb-1">Лимит</label>
            <input
              type="number"
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value || 0))}
              className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            />
          </div>
          <div className="xl:col-span-2">
            <label className="block text-[10px] uppercase tracking-[0.1em] text-slate-500 mb-1">tg_ids (опционально)</label>
            <input
              value={tgIdsRaw}
              onChange={(event) => setTgIdsRaw(event.target.value)}
              className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
              placeholder="123, 456, 789"
            />
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[1fr,0.4fr]">
          <div>
            <label className="block text-[10px] uppercase tracking-[0.1em] text-slate-500 mb-1">Текст рассылки</label>
            <textarea
              value={text}
              onChange={(event) => setText(event.target.value)}
              rows={6}
              placeholder="Текст рассылки..."
              className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70 resize-none"
            />
          </div>
          {/* Preview */}
          <div>
            <label className="block text-[10px] uppercase tracking-[0.1em] text-slate-500 mb-1 flex items-center gap-1"><Eye size={10} /> Превью</label>
            <div className="rounded-xl bg-white/50 p-3 dark:bg-white/5 min-h-[120px] text-sm whitespace-pre-line text-slate-600 dark:text-slate-300">
              {text.trim() || <span className="text-slate-400 italic">Введите текст…</span>}
            </div>
          </div>
        </div>

        <button
          className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em] inline-flex items-center gap-2"
          type="button"
          onClick={() => void submit()}
          disabled={busy || !text.trim()}
        >
          {busy ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
          {busy ? "Отправка..." : "Отправить"}
        </button>
      </article>

      {/* ── Live updates ───────────────────────────────── */}
      <article className="glass-card p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="stat-icon stat-icon-blue">
              <Newspaper size={20} />
            </div>
            <div>
              <h3 className="font-display text-xl font-bold">Live updates</h3>
              <p className="text-xs text-slate-500">Новости в личном кабинете пользователей</p>
            </div>
          </div>
          <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => void createLiveUpdate()} disabled={busy}>
            <Plus size={14} /> Добавить
          </button>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          {liveUpdates.map((row) => (
            <div key={row.id} className="node-card">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`status-dot ${row.is_active ? "status-dot-online" : "status-dot-stale"}`} />
                    <p className="text-sm font-bold">{row.title}</p>
                  </div>
                  <p className="mt-1 text-xs text-slate-500 line-clamp-2">{row.summary || "—"}</p>
                </div>
                <span className={`badge ${row.is_active ? "badge-success" : "badge-danger"}`}>
                  {row.is_active ? "active" : "off"}
                </span>
              </div>
              <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                {row.link ? (
                  <a href={row.link} target="_blank" className="inline-flex items-center gap-1 text-xs text-violet-600 dark:text-violet-300 hover:underline">
                    <ExternalLink size={10} /> Открыть
                  </a>
                ) : <span />}
                <div className="flex gap-1.5">
                  <button className="outline-btn rounded-lg px-2.5 py-1 text-[10px] font-semibold inline-flex items-center gap-1" type="button" onClick={() => void editLiveUpdate(row)} disabled={busy}>
                    <PencilLine size={10} /> edit
                  </button>
                  <button className="outline-btn rounded-lg px-2.5 py-1 text-[10px] font-semibold inline-flex items-center gap-1 text-rose-500" type="button" onClick={() => void removeLiveUpdate(row.id)} disabled={busy}>
                    <Trash2 size={10} /> del
                  </button>
                </div>
              </div>
            </div>
          ))}
          {liveUpdates.length === 0 ? (
            <div className="empty-state col-span-full">
              <Newspaper size={28} />
              <p className="text-xs">Нет live-updates</p>
            </div>
          ) : null}
        </div>
      </article>

      {/* ── Result / error ─────────────────────────────── */}
      {result ? (
        <div className="stat-card p-4 flex items-center gap-3">
          <div className="stat-icon stat-icon-emerald"><Check size={18} /></div>
          <p className="text-sm text-emerald-600 dark:text-emerald-300 font-medium">{result}</p>
        </div>
      ) : null}
      {error ? (
        <div className="stat-card p-4 flex items-center gap-3">
          <div className="stat-icon stat-icon-rose"><X size={18} /></div>
          <p className="text-sm text-rose-500 font-medium">{error}</p>
        </div>
      ) : null}
    </section>
  );
}
