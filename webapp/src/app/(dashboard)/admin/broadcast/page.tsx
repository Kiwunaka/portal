"use client";

import {
  adminBroadcast,
  adminLiveUpdateCreate,
  adminLiveUpdateDelete,
  adminLiveUpdateUpdate,
  adminLiveUpdates,
  adminTemplateCreate,
  adminTemplates,
  adminTemplateUpdate,
  type AdminTemplateRow,
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
  { value: "all_active", label: " ", icon: "??" },
  { value: "free", label: "", icon: "??" },
  { value: "paid", label: "", icon: "??" },
  { value: "expired", label: "", icon: "?" },
];

const RETENTION_TEMPLATE_GROUPS = [
  { key: "retention_welcome_a", label: "Welcome A", flow: "Welcome", hint: "������ ������� ����� �����������" },
  { key: "retention_welcome_b", label: "Welcome B", flow: "Welcome", hint: "�������������� welcome-�������" },
  { key: "retention_t3_a", label: "T-3 A", flow: "���������", hint: "�� 3 ��� �� ��������� �������" },
  { key: "retention_t3_b", label: "T-3 B", flow: "���������", hint: "������ ������� ��� T-3" },
  { key: "retention_t1_a", label: "T-1 A", flow: "���������", hint: "�� ����� �� ��������� �������" },
  { key: "retention_t1_b", label: "T-1 B", flow: "���������", hint: "������ ������� ��� T-1" },
  { key: "retention_t0_a", label: "T0 A", flow: "���������", hint: "��������� ������� � ���� ���������" },
  { key: "retention_t0_b", label: "T0 B", flow: "���������", hint: "������ ������� ��� T0" },
  { key: "retention_reactivation_a", label: "Reactivation A", flow: "�������", hint: "������� ����� ������" },
  { key: "retention_reactivation_b", label: "Reactivation B", flow: "�������", hint: "�������������� reactivation-�������" },
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

  const loadLiveUpdates = async (): Promise<void> => {
    try {
      const rows = await adminLiveUpdates(true);
      setLiveUpdates(rows);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "    "));
    }
  };

  const loadTemplates = async (): Promise<void> => {
    try {
      const rows = await adminTemplates(200);
      setTemplates(rows);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "    "));
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
      setResult(` :  ${out?.sent ?? 0},  ${out?.failed ?? 0},  ${out?.attempted ?? 0}.`);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "   "));
    } finally {
      setBusy(false);
    }
  };

  const createLiveUpdate = async (): Promise<void> => {
    setLiveDialog({
      kind: "create",
      title: "���������� �������",
      summary: "����� ��������� ������������ � ��������",
      link: "https://t.me/pokrov_vpnbot",
      sortOrder: "100",
    });
  };

  const editLiveUpdate = async (row: LiveUpdateRow): Promise<void> => {
    setLiveDialog({
      kind: "edit",
      id: row.id,
      title: row.title || "",
      summary: row.summary || "",
      link: row.link || "",
      isActive: Boolean(row.is_active),
    });
  };

  const removeLiveUpdate = async (id: number): Promise<void> => {
    setLiveDialog({ kind: "delete", id });
  };

  const openTemplateDialog = (templateKey: string): void => {
    const meta = RETENTION_TEMPLATE_GROUPS.find((row) => row.key === templateKey);
    if (!meta) return;
    const existing = templates.find((row) => row.key === templateKey);
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
          setError("������� ��������� �������.");
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
        setResult("������� ���������.");
      } else if (liveDialog.kind === "edit") {
        if (!liveDialog.title.trim()) {
          setError("������� ��������� �������.");
          setBusy(false);
          return;
        }
        await adminLiveUpdateUpdate(liveDialog.id, {
          title: liveDialog.title.trim(),
          summary: liveDialog.summary.trim(),
          link: liveDialog.link.trim(),
          is_active: liveDialog.isActive,
        });
        setResult(`������� #${liveDialog.id} ���������.`);
      } else if (liveDialog.kind === "delete") {
        await adminLiveUpdateDelete(liveDialog.id);
        setResult(`������� #${liveDialog.id} �������.`);
      }
      await loadLiveUpdates();
      setLiveDialog(null);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "     "));
    } finally {
      setBusy(false);
    }
  };

  const submitTemplateDialog = async (): Promise<void> => {
    if (!templateDialog) return;
    const textValue = templateDialog.text.trim();
    if (!textValue) {
      setError("������ �� ����� ���� ������.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      if (templateDialog.mode === "create") {
        await adminTemplateCreate({ key: templateDialog.key, text: textValue });
        setResult(`������ ${templateDialog.title} ������.`);
      } else {
        await adminTemplateUpdate(templateDialog.key, { text: textValue });
        setResult(`������ ${templateDialog.title} �������.`);
      }
      await loadTemplates();
      setTemplateDialog(null);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "    "));
    } finally {
      setBusy(false);
    }
  };

  const templatesByKey = new Map(templates.map((row) => [row.key, row]));

  return (
    <section className="space-y-5">
      {/* -- Broadcast composer --------------------------- */}
      <article className="stat-card p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="stat-icon stat-icon-rose">
            <Megaphone size={20} />
          </div>
          <div>
            <h2 className="font-display text-xl font-bold">��������</h2>
            <p className="text-xs text-slate-500">�������� �������� ��������� �� ���������� �������� �������������</p>
          </div>
        </div>
        <div className="rounded-xl bg-white/60 p-3 text-xs text-slate-500 dark:bg-white/5 dark:text-slate-400">
          ����������� �������� ��� ��������, ����������� � ������ ����������. ���� ��������� ���������, ������� ��������� ��� �� ��������� ������� � ������ ����� �� ��� ����.
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <div>
            <label className="block text-[10px] uppercase tracking-[0.1em] text-slate-500 mb-1">�������</label>
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
            <label className="block text-[10px] uppercase tracking-[0.1em] text-slate-500 mb-1">�����</label>
            <input
              type="number"
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value || 0))}
              className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            />
          </div>
          <div className="xl:col-span-2">
            <label className="block text-[10px] uppercase tracking-[0.1em] text-slate-500 mb-1">Telegram ID (�������������)</label>
            <input
              value={tgIdsRaw}
              onChange={(event) => setTgIdsRaw(event.target.value)}
              className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
              placeholder="���� �����, ������� ���������� Telegram ID ����� �������"
            />
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[1fr,0.4fr]">
          <div>
            <label className="block text-[10px] uppercase tracking-[0.1em] text-slate-500 mb-1">����� ��������</label>
            <textarea
              value={text}
              onChange={(event) => setText(event.target.value)}
              rows={6}
              placeholder="�������� ����� �������� �������� �������"
              className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70 resize-none"
            />
          </div>
          {/* Preview */}
          <div>
            <label className="block text-[10px] uppercase tracking-[0.1em] text-slate-500 mb-1 flex items-center gap-1"><Eye size={10} /> ������</label>
            <div className="rounded-xl bg-white/50 p-3 dark:bg-white/5 min-h-[120px] text-sm whitespace-pre-line text-slate-600 dark:text-slate-300">
              {text.trim() || <span className="text-slate-400 italic">������� �����</span>}
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
          {busy ? "..." : ""}
        </button>
      </article>

      <article className="glass-card p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="stat-icon stat-icon-violet">
              <PencilLine size={20} />
            </div>
            <div>
              <h3 className="font-display text-xl font-bold">Retention-�������</h3>
              <p className="text-xs text-slate-500">������� ������� ��� �����������, ����������� � ��������� � �������� �������������</p>
            </div>
          </div>
          <span className="badge badge-info">{templates.length} ��������</span>
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
                  <span className={`badge ${existing ? "badge-success" : "badge-warning"}`}>
                    {existing ? "" : ""}
                  </span>
                </div>
                <p className="mt-2 text-xs text-slate-500">{item.hint}</p>
                <div className="mt-3 rounded-xl bg-white/50 p-3 text-xs leading-relaxed text-slate-600 dark:bg-white/5 dark:text-slate-300">
                  {(existing?.text || "   .     .").slice(0, 240)}
                  {existing?.text && existing.text.length > 240 ? "" : ""}
                </div>
                <div className="mt-3 flex justify-end">
                  <button
                    className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold inline-flex items-center gap-1.5"
                    type="button"
                    onClick={() => openTemplateDialog(item.key)}
                    disabled={busy}
                  >
                    <PencilLine size={12} />
                    {existing ? "" : ""}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      </article>

      {/* -- Live updates --------------------------------- */}
      <article className="glass-card p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="stat-icon stat-icon-blue">
              <Newspaper size={20} />
            </div>
            <div>
              <h3 className="font-display text-xl font-bold">������� � ����������</h3>
              <p className="text-xs text-slate-500">�������� ��������, ������� ������������ ����� ����� � ��������</p>
            </div>
          </div>
          <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => void createLiveUpdate()} disabled={busy}>
            <Plus size={14} /> ��������
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
                  <p className="mt-1 text-xs text-slate-500 line-clamp-2">{row.summary || "�"}</p>
                </div>
                <span className={`badge ${row.is_active ? "badge-success" : "badge-danger"}`}>
                  {row.is_active ? "" : ""}
                </span>
              </div>
              <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                {row.link ? (
                  <a href={row.link} target="_blank" className="inline-flex items-center gap-1 text-xs text-violet-600 dark:text-violet-300 hover:underline">
                    <ExternalLink size={10} /> �������
                  </a>
                ) : <span />}
                <div className="flex gap-1.5">
                  <button className="outline-btn rounded-lg px-2.5 py-1 text-[10px] font-semibold inline-flex items-center gap-1" type="button" onClick={() => void editLiveUpdate(row)} disabled={busy}>
                    <PencilLine size={10} /> ��������
                  </button>
                  <button className="outline-btn rounded-lg px-2.5 py-1 text-[10px] font-semibold inline-flex items-center gap-1 text-rose-500" type="button" onClick={() => void removeLiveUpdate(row.id)} disabled={busy}>
                    <Trash2 size={10} /> �������
                  </button>
                </div>
              </div>
            </div>
          ))}
          {liveUpdates.length === 0 ? (
            <div className="empty-state col-span-full">
              <Newspaper size={28} />
              <p className="text-xs">�������� ���� ���</p>
            </div>
          ) : null}
        </div>
      </article>

      {/* -- Result / error ------------------------------- */}
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

      {liveDialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/65 p-4">
          <div className="glass-card w-full max-w-xl p-5">
            {liveDialog.kind === "create" || liveDialog.kind === "edit" ? (
              <>
                <h3 className="font-display text-xl font-semibold">
                  {liveDialog.kind === "create" ? " " : `  #${liveDialog.id}`}
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
                    placeholder="���������"
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
                    placeholder="������� ��������"
                  />
                  <input
                    value={liveDialog.link}
                    onChange={(event) =>
                      setLiveDialog((prev) =>
                        prev && (prev.kind === "create" || prev.kind === "edit") ? { ...prev, link: event.target.value } : prev,
                      )
                    }
                    className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                    placeholder="������"
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
                      placeholder="sort_order"
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
                      �������
                    </label>
                  )}
                </div>
                <div className="mt-4 flex justify-end gap-2">
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setLiveDialog(null)}>
                    ������
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void submitLiveDialog()}>
                    ���������
                  </button>
                </div>
              </>
            ) : null}

            {liveDialog.kind === "delete" ? (
              <>
                <h3 className="font-display text-xl font-semibold">  #{liveDialog.id}?</h3>
                <p className="mt-2 text-sm text-slate-500">�������� ������ �������� �� ����� ����������.</p>
                <div className="mt-4 flex justify-end gap-2">
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setLiveDialog(null)}>
                    ������
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void submitLiveDialog()}>
                    �������
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
              onChange={(event) =>
                setTemplateDialog((prev) => (prev ? { ...prev, text: event.target.value } : prev))
              }
              rows={12}
              className="mt-4 w-full rounded-2xl border border-violet-200/50 bg-white/80 px-3 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
              placeholder="����� �������. ����� ������������ ���������� ����� {expiry_date}, {channel}, {discount_pct}."
            />
            <div className="mt-4 flex justify-end gap-2">
              <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setTemplateDialog(null)}>
                ������
              </button>
              <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void submitTemplateDialog()}>
                {templateDialog.mode === "create" ? "" : ""}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
