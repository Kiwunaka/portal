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
  { value: "all_active", label: "All active" },
  { value: "free", label: "Free" },
  { value: "paid", label: "Paid" },
  { value: "expired", label: "Expired" },
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
      setError("Message text and operator reason are required.");
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
      });
      setResult(`Sent ${out?.sent ?? 0}, failed ${out?.failed ?? 0}, attempted ${out?.attempted ?? 0}.`);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not send broadcast."));
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
      setError("Operator reason is required.");
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
        setResult("Live update created.");
      } else if (liveDialog.kind === "edit") {
        await adminLiveUpdateUpdate(liveDialog.id, {
          title: liveDialog.title.trim(),
          summary: liveDialog.summary.trim(),
          link: liveDialog.link.trim(),
          is_active: liveDialog.isActive,
        });
        setResult(`Live update #${liveDialog.id} updated.`);
      } else {
        await adminLiveUpdateDelete(liveDialog.id);
        setResult(`Live update #${liveDialog.id} deleted.`);
      }
      await loadLiveUpdates();
      setLiveDialog(null);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not save live update."));
    } finally {
      setBusy(false);
    }
  };

  const submitTemplateDialog = async (): Promise<void> => {
    if (!templateDialog || !templateDialog.text.trim()) {
      setError("Template text is required.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      if (templateDialog.mode === "create") {
        await adminTemplateCreate({ key: templateDialog.key, text: templateDialog.text.trim() });
        setResult(`Template ${templateDialog.title} created.`);
      } else {
        await adminTemplateUpdate(templateDialog.key, { text: templateDialog.text.trim() });
        setResult(`Template ${templateDialog.title} updated.`);
      }
      await loadTemplates();
      setTemplateDialog(null);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not save template."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-4">
      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader
          eyebrow="messaging"
          title="Broadcasts and message templates"
          description="No fake realtime chat here: broadcasts are deliberate sends with preview, segment, limit, and operator reason."
          actions={
            <button className={adminButtonClass("secondary", "sm")} type="button" onClick={() => { void loadLiveUpdates(); void loadTemplates(); }}>
              Reload
            </button>
          }
        />
        <div className="flex flex-wrap gap-2">
          <AdminBadge tone="warning">reason required</AdminBadge>
          <AdminBadge>preview before send</AdminBadge>
          <AdminBadge tone="accent">{templates.length} templates</AdminBadge>
        </div>
      </article>

      {result ? <div className={adminPanelClass("success")}>{result}</div> : null}
      {error ? <div className={adminPanelClass("danger")}>{error}</div> : null}

      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader eyebrow="broadcast" title="Send broadcast" />
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <label className="text-xs text-slate-400">
            Segment
            <select value={segment} onChange={(event) => setSegment(event.target.value)} className={`mt-1 ${adminFieldClass}`}>
              {SEGMENT_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
          <label className="text-xs text-slate-400">
            Limit
            <input type="number" value={limit} onChange={(event) => setLimit(Number(event.target.value || 0))} className={`mt-1 ${adminFieldClass}`} />
          </label>
          <label className="text-xs text-slate-400 xl:col-span-2">
            Telegram IDs override
            <input value={tgIdsRaw} onChange={(event) => setTgIdsRaw(event.target.value)} className={`mt-1 ${adminFieldClass}`} placeholder="123456789, 987654321" />
          </label>
        </div>
        <div className="mt-3 grid gap-4 lg:grid-cols-[minmax(0,1fr),minmax(260px,0.42fr)]">
          <label className="block text-xs text-slate-400">
            Message text
            <textarea value={text} onChange={(event) => setText(event.target.value)} rows={7} placeholder="Broadcast text" className={`mt-1 ${adminTextAreaClass}`} />
          </label>
          <div className={adminInsetPanelClass}>
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">preview</p>
            <div className="mt-3 min-h-[132px] whitespace-pre-line rounded-[0.85rem] border border-[#c6e6db] bg-[#ffffff] p-3 text-sm text-slate-300">
              {text.trim() || <span className="text-slate-500">Message preview appears here.</span>}
            </div>
          </div>
        </div>
        <div className="mt-3 flex flex-col gap-3 lg:flex-row lg:items-end">
          <label className="flex-1 text-xs text-slate-400">
            Operator reason
            <input value={confirmReason} onChange={(event) => setConfirmReason(event.target.value)} className={`mt-1 ${adminFieldClass}`} placeholder="Why this broadcast is being sent" />
          </label>
          <button className={adminButtonClass("primary")} type="button" onClick={() => void submit()} disabled={busy || !text.trim() || !confirmReason.trim()}>
            Send broadcast
          </button>
        </div>
      </article>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr),minmax(360px,0.8fr)]">
        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader
            eyebrow="retention"
            title="Templates"
            actions={<AdminBadge>{templates.length} stored</AdminBadge>}
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
                    <AdminBadge tone={existing ? "success" : "warning"}>{existing ? "set" : "missing"}</AdminBadge>
                  </div>
                  <p className="mt-3 line-clamp-4 rounded-[0.85rem] border border-[#c6e6db] bg-[#ffffff] p-3 text-xs leading-5 text-slate-400">
                    {existing?.text || "Template is not configured yet."}
                  </p>
                  <button className={`${adminButtonClass("secondary", "xs")} mt-3`} type="button" onClick={() => openTemplateDialog(item.key)} disabled={busy}>
                    {existing ? "Edit" : "Create"}
                  </button>
                </article>
              );
            })}
          </div>
        </article>

        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader
            eyebrow="live updates"
            title="News cards"
            actions={
              <button className={adminButtonClass("primary", "sm")} type="button" onClick={() => setLiveDialog({ kind: "create", title: "New update", summary: "", link: "", sortOrder: "100", reason: "" })}>
                New update
              </button>
            }
          />
          <div className="space-y-3">
            {liveUpdates.map((row) => (
              <div key={row.id} className={adminInsetPanelClass}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-50">{row.title}</p>
                    <p className="mt-1 line-clamp-2 text-xs text-slate-500">{row.summary || "No summary"}</p>
                    {row.link ? <p className="mt-1 truncate text-xs text-emerald-300">{row.link}</p> : null}
                  </div>
                  <AdminBadge tone={row.is_active ? "success" : "warning"}>{row.is_active ? "active" : "hidden"}</AdminBadge>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button className={adminButtonClass("secondary", "xs")} type="button" onClick={() => setLiveDialog({ kind: "edit", id: row.id, title: row.title || "", summary: row.summary || "", link: row.link || "", isActive: Boolean(row.is_active), reason: "" })}>
                    Edit
                  </button>
                  <button className={adminButtonClass("danger", "xs")} type="button" onClick={() => setLiveDialog({ kind: "delete", id: row.id, reason: "" })}>
                    Delete
                  </button>
                </div>
              </div>
            ))}
            {!liveUpdates.length ? <p className="text-xs text-slate-500">No live updates yet.</p> : null}
          </div>
        </article>
      </div>

      {liveDialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/70 p-4">
          <div className={`${adminPanelClass("neutral")} w-full max-w-xl`}>
            {liveDialog.kind === "delete" ? (
              <>
                <h3 className="text-xl font-semibold">Delete live update #{liveDialog.id}</h3>
                <input value={liveDialog.reason} onChange={(event) => setLiveDialog({ ...liveDialog, reason: event.target.value })} className={`mt-4 ${adminFieldClass}`} placeholder="Operator reason" />
              </>
            ) : (
              <>
                <h3 className="text-xl font-semibold">{liveDialog.kind === "create" ? "New live update" : `Live update #${liveDialog.id}`}</h3>
                <input value={liveDialog.title} onChange={(event) => setLiveDialog({ ...liveDialog, title: event.target.value })} className={`mt-4 ${adminFieldClass}`} placeholder="Title" />
                <textarea value={liveDialog.summary} onChange={(event) => setLiveDialog({ ...liveDialog, summary: event.target.value })} rows={4} className={`mt-3 ${adminTextAreaClass}`} placeholder="Summary" />
                <input value={liveDialog.link} onChange={(event) => setLiveDialog({ ...liveDialog, link: event.target.value })} className={`mt-3 ${adminFieldClass}`} placeholder="Link" />
                {liveDialog.kind === "create" ? (
                  <input value={liveDialog.sortOrder} onChange={(event) => setLiveDialog({ ...liveDialog, sortOrder: event.target.value })} type="number" className={`mt-3 ${adminFieldClass}`} placeholder="Sort order" />
                ) : (
                  <label className="mt-3 inline-flex items-center gap-2 text-sm text-slate-400">
                    <input type="checkbox" checked={liveDialog.isActive} onChange={(event) => setLiveDialog({ ...liveDialog, isActive: event.target.checked })} />
                    Active
                  </label>
                )}
                <input value={liveDialog.reason} onChange={(event) => setLiveDialog({ ...liveDialog, reason: event.target.value })} className={`mt-3 ${adminFieldClass}`} placeholder="Operator reason" />
              </>
            )}
            <div className="mt-4 flex justify-end gap-2">
              <button className={adminButtonClass("secondary")} type="button" onClick={() => setLiveDialog(null)}>Cancel</button>
              <button className={adminButtonClass(liveDialog.kind === "delete" ? "danger" : "primary")} type="button" disabled={busy || !liveDialog.reason.trim()} onClick={() => void submitLiveDialog()}>
                {liveDialog.kind === "delete" ? "Delete" : "Save"}
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
            <textarea value={templateDialog.text} onChange={(event) => setTemplateDialog({ ...templateDialog, text: event.target.value })} rows={12} className={`mt-4 ${adminTextAreaClass}`} placeholder="Template text" />
            <div className="mt-4 flex justify-end gap-2">
              <button className={adminButtonClass("secondary")} type="button" onClick={() => setTemplateDialog(null)}>Cancel</button>
              <button className={adminButtonClass("primary")} type="button" disabled={busy || !templateDialog.text.trim()} onClick={() => void submitTemplateDialog()}>
                {templateDialog.mode === "create" ? "Create" : "Save"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
