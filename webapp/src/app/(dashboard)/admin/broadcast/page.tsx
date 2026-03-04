"use client";

import {
  adminBroadcast,
  adminLiveUpdateCreate,
  adminLiveUpdateDelete,
  adminLiveUpdateUpdate,
  adminLiveUpdates,
  type LiveUpdateRow,
} from "@/lib/api";
import { useEffect, useState } from "react";

function parseTgIds(input: string): number[] {
  return input
    .split(/[\s,;]+/)
    .map((token) => Number(token.trim()))
    .filter((value) => Number.isFinite(value) && value > 0)
    .map((value) => Math.floor(value));
}

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
    const link = window.prompt("Ссылка:", "https://t.me/net4ebur_bot") || "";
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
    <section className="space-y-4">
      <article className="glass-card p-5 space-y-4">
        <h2 className="font-display text-2xl font-semibold">Broadcast</h2>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <select
            value={segment}
            onChange={(event) => setSegment(event.target.value)}
            className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          >
            <option value="all_active">all_active</option>
            <option value="free">free</option>
            <option value="paid">paid</option>
            <option value="expired">expired</option>
          </select>
          <input
            type="number"
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value || 0))}
            className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            placeholder="Лимит"
          />
          <input
            value={tgIdsRaw}
            onChange={(event) => setTgIdsRaw(event.target.value)}
            className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            placeholder="tg_ids: 123,456"
          />
          <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em]" type="button" onClick={() => void submit()} disabled={busy || !text.trim()}>
            {busy ? "Отправка..." : "Отправить"}
          </button>
        </div>
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          rows={7}
          placeholder="Текст рассылки..."
          className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
        />
      </article>

      <article className="glass-card p-5">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h3 className="font-display text-xl font-semibold">Live updates</h3>
          <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void createLiveUpdate()} disabled={busy}>
            + Добавить
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="px-2 py-2">ID</th>
                <th className="px-2 py-2">Title</th>
                <th className="px-2 py-2">Link</th>
                <th className="px-2 py-2">State</th>
                <th className="px-2 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {liveUpdates.map((row) => (
                <tr key={row.id} className="border-t border-white/30 dark:border-white/10">
                  <td className="px-2 py-2">{row.id}</td>
                  <td className="px-2 py-2">{row.title}</td>
                  <td className="px-2 py-2">
                    <a href={row.link} target="_blank" className="text-violet-600 underline dark:text-violet-300">
                      открыть
                    </a>
                  </td>
                  <td className="px-2 py-2">{row.is_active ? "active" : "inactive"}</td>
                  <td className="px-2 py-2">
                    <div className="flex gap-2">
                      <button className="outline-btn rounded-xl px-2 py-1 text-xs font-semibold" type="button" onClick={() => void editLiveUpdate(row)} disabled={busy}>
                        edit
                      </button>
                      <button className="outline-btn rounded-xl px-2 py-1 text-xs font-semibold" type="button" onClick={() => void removeLiveUpdate(row.id)} disabled={busy}>
                        delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>

      {result ? <p className="text-sm text-emerald-500">{result}</p> : null}
      {error ? <p className="text-sm text-rose-500">{error}</p> : null}
    </section>
  );
}
