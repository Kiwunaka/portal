"use client";

import {
  adminBuildCampaignLinks,
  adminReferralProcess,
  adminReferralQueue,
  adminStartLinkCreate,
  adminStartLinkDelete,
  adminStartLinkUpdate,
  adminStartLinks,
  type AdminReferralQueueRow,
  type AdminStartLinkRow,
  type CampaignLinksBuildResult,
} from "@/lib/api";
import {
  AdminBadge,
  AdminPanelHeader,
  adminButtonClass,
  adminFieldClass,
  adminInsetPanelClass,
  adminPanelClass,
  adminTableShellClass,
  adminTextAreaClass,
} from "@/components/admin/admin-shell";
import { useCallback, useEffect, useState } from "react";
import { fmtRuDate } from "../nav";

type StartLinkDialog =
  | { kind: "create"; code: string; description: string; targetAction: string; reason: string }
  | { kind: "edit"; id: number; code: string; description: string; targetAction: string; isActive: boolean; reason: string }
  | { kind: "delete"; id: number; reason: string }
  | null;

function queueStatusLabel(value: string): string {
  const normalized = String(value || "").toLowerCase();
  if (normalized === "pending") return "pending";
  if (normalized === "rewarded") return "rewarded";
  if (normalized === "rejected") return "rejected";
  if (normalized === "waiting_activity") return "waiting activity";
  return value || "unknown";
}

function queueTone(value: string): "success" | "warning" | "danger" | "neutral" {
  const normalized = String(value || "").toLowerCase();
  if (normalized === "rewarded") return "success";
  if (normalized === "rejected") return "danger";
  if (normalized === "pending" || normalized === "waiting_activity") return "warning";
  return "neutral";
}

export default function AdminReferralsPage() {
  const [links, setLinks] = useState<AdminStartLinkRow[]>([]);
  const [queueRows, setQueueRows] = useState<AdminReferralQueueRow[]>([]);
  const [built, setBuilt] = useState<CampaignLinksBuildResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState("");
  const [promoCode, setPromoCode] = useState("");
  const [campaignKey, setCampaignKey] = useState("");
  const [planCode, setPlanCode] = useState("");
  const [queueStatus, setQueueStatus] = useState("");
  const [linkDialog, setLinkDialog] = useState<StartLinkDialog>(null);

  const load = useCallback(async (): Promise<void> => {
    setError("");
    setResult("");
    try {
      const [rows, queue] = await Promise.all([adminStartLinks(true), adminReferralQueue(120, queueStatus)]);
      setLinks(rows);
      setQueueRows(queue);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not load referral data."));
    }
  }, [queueStatus]);

  useEffect(() => {
    void load();
  }, [load]);

  const submitLinkDialog = async (): Promise<void> => {
    if (!linkDialog) return;
    if (!linkDialog.reason.trim()) {
      setError("Operator reason is required.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      if (linkDialog.kind === "create") {
        await adminStartLinkCreate({
          code: linkDialog.code.trim(),
          description: linkDialog.description.trim(),
          target_action: linkDialog.targetAction.trim(),
          is_active: true,
        });
        setResult("Start link created.");
      } else if (linkDialog.kind === "edit") {
        await adminStartLinkUpdate(linkDialog.id, {
          code: linkDialog.code.trim(),
          description: linkDialog.description.trim(),
          target_action: linkDialog.targetAction.trim(),
          is_active: linkDialog.isActive,
        });
        setResult(`Start link #${linkDialog.id} updated.`);
      } else {
        await adminStartLinkDelete(linkDialog.id);
        setResult(`Start link #${linkDialog.id} deleted.`);
      }
      setLinkDialog(null);
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not save start link."));
    } finally {
      setBusy(false);
    }
  };

  const buildLinks = async (): Promise<void> => {
    setBusy(true);
    setError("");
    setResult("");
    try {
      setBuilt(await adminBuildCampaignLinks({
        promo_code: promoCode.trim() || undefined,
        campaign_key: campaignKey.trim() || undefined,
        plan_code: planCode.trim() || undefined,
        source: "bot",
      }));
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not build campaign links."));
    } finally {
      setBusy(false);
    }
  };

  const copyText = async (text: string): Promise<void> => {
    try {
      await navigator.clipboard.writeText(text);
      setResult("Copied.");
    } catch {
      setError("Clipboard copy failed.");
    }
  };

  const processQueue = async (forceWithoutActivity = false): Promise<void> => {
    setBusy(true);
    setError("");
    setResult("");
    try {
      const out = await adminReferralProcess({ limit: 120, force_without_activity: forceWithoutActivity });
      setResult(`Queue processed: rewarded ${out.rewarded}, waiting ${out.waiting}, rejected ${out.rejected}, total ${out.processed}.`);
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not process queue."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-4">
      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader
          eyebrow="access"
          title="Referrals and campaign links"
          description="Manage start links, build campaign URLs, and process the referral reward queue from one operator surface."
          actions={
            <>
              <button className={adminButtonClass("secondary", "sm")} type="button" onClick={() => void load()} disabled={busy}>
                Reload
              </button>
              <button className={adminButtonClass("primary", "sm")} type="button" onClick={() => setLinkDialog({ kind: "create", code: "launch14", description: "Campaign start link", targetAction: "campaign", reason: "" })} disabled={busy}>
                New start link
              </button>
            </>
          }
        />
        <div className="flex flex-wrap gap-2">
          <AdminBadge tone="accent">{links.length} start links</AdminBadge>
          <AdminBadge tone="accent">{queueRows.length} queue rows</AdminBadge>
          <AdminBadge tone="warning">delete requires reason</AdminBadge>
        </div>
      </article>

      {result ? <div className={adminPanelClass("success")}>{result}</div> : null}
      {error ? <div className={adminPanelClass("danger")}>{error}</div> : null}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr),minmax(360px,0.75fr)]">
        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader eyebrow="start links" title="Entry links" />
          <div className="space-y-3">
            {links.map((link) => (
              <div key={link.id} className={adminInsetPanelClass}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <AdminBadge tone={link.is_active ? "success" : "warning"}>{link.is_active ? "active" : "inactive"}</AdminBadge>
                      <span className="font-mono text-sm font-semibold text-slate-100">{link.code}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{link.description || "No description"}</p>
                    <p className="mt-1 text-[11px] text-slate-500">Updated: {fmtRuDate(link.updated_at)}</p>
                    <p className="mt-1 truncate text-xs text-emerald-300">{link.bot_start_link}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button className={adminButtonClass("secondary", "xs")} type="button" onClick={() => void copyText(link.bot_start_link)}>Copy</button>
                    <button className={adminButtonClass("secondary", "xs")} type="button" onClick={() => setLinkDialog({ kind: "edit", id: link.id, code: link.code || "", description: link.description || "", targetAction: link.target_action || "campaign", isActive: Boolean(link.is_active), reason: "" })}>Edit</button>
                    {link.is_active ? (
                      <button className={adminButtonClass("danger", "xs")} type="button" onClick={() => setLinkDialog({ kind: "delete", id: link.id, reason: "" })}>Delete</button>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
            {!links.length ? <p className="text-xs text-slate-500">No start links yet.</p> : null}
          </div>
        </article>

        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader eyebrow="campaign builder" title="Build links" description="Generate bot, checkout, and webapp links for a campaign tuple." />
          <div className="grid gap-3">
            <input value={promoCode} onChange={(event) => setPromoCode(event.target.value)} placeholder="Promo code, optional" className={adminFieldClass} />
            <input value={campaignKey} onChange={(event) => setCampaignKey(event.target.value)} placeholder="Campaign key, optional" className={adminFieldClass} />
            <input value={planCode} onChange={(event) => setPlanCode(event.target.value)} placeholder="Plan code, optional" className={adminFieldClass} />
            <button className={adminButtonClass("primary")} type="button" onClick={() => void buildLinks()} disabled={busy}>
              Build links
            </button>
          </div>
          {built ? (
            <div className="mt-4 space-y-2">
              {built.checkout_mode === "bot_fallback" ? <AdminBadge tone="warning">checkout uses bot reserve path</AdminBadge> : null}
              {[
                { label: "Bot", value: built.bot_start_link },
                { label: "Checkout", value: built.checkout_link },
                { label: "Webapp", value: built.webapp_link },
              ].map((item) => (
                <div key={item.label} className={adminInsetPanelClass}>
                  <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500">{item.label}</p>
                  <p className="mt-1 truncate font-mono text-xs text-slate-300">{item.value}</p>
                  <button className={`${adminButtonClass("secondary", "xs")} mt-2`} type="button" onClick={() => void copyText(item.value)}>
                    Copy
                  </button>
                </div>
              ))}
            </div>
          ) : null}
        </article>
      </div>

      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader
          eyebrow="queue"
          title="Referral processing queue"
          actions={
            <div className="flex flex-wrap gap-2">
              <select value={queueStatus} onChange={(event) => setQueueStatus(event.target.value)} className={adminFieldClass}>
                <option value="">All statuses</option>
                <option value="pending">Pending</option>
                <option value="rewarded">Rewarded</option>
                <option value="rejected">Rejected</option>
                <option value="waiting_activity">Waiting activity</option>
              </select>
              <button className={adminButtonClass("secondary", "sm")} type="button" onClick={() => void processQueue(false)} disabled={busy}>Process</button>
              <button className={adminButtonClass("danger", "sm")} type="button" onClick={() => void processQueue(true)} disabled={busy}>Force process</button>
            </div>
          }
        />
        <div className={adminTableShellClass}>
          <div className="max-h-[42vh] overflow-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="border-b border-[#c6e6db] bg-[#f8fffc] text-left text-[11px] uppercase tracking-[0.14em] text-slate-500">
                  <th className="px-3 py-3">Order</th>
                  <th className="px-3 py-3">Referrer</th>
                  <th className="px-3 py-3">Referred</th>
                  <th className="px-3 py-3">Ready</th>
                  <th className="px-3 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {queueRows.map((row) => (
                  <tr key={row.id} className="border-t border-[#c6e6db]">
                    <td className="px-3 py-3 font-mono">{row.order_id}</td>
                    <td className="px-3 py-3">{row.referrer_tg_id}</td>
                    <td className="px-3 py-3">{row.referred_tg_id}</td>
                    <td className="px-3 py-3">{fmtRuDate(row.ready_at)}</td>
                    <td className="px-3 py-3"><AdminBadge tone={queueTone(row.status)}>{queueStatusLabel(row.status)}</AdminBadge></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!queueRows.length ? <p className="px-3 py-4 text-xs text-slate-500">Queue is empty.</p> : null}
          </div>
        </div>
      </article>

      {linkDialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/70 p-4">
          <div className={`${adminPanelClass("neutral")} w-full max-w-xl`}>
            {linkDialog.kind === "delete" ? (
              <>
                <h3 className="text-xl font-semibold">Delete start link #{linkDialog.id}</h3>
                <p className="mt-2 text-sm text-slate-400">Campaign and welcome scenarios will no longer use this link.</p>
              </>
            ) : (
              <>
                <h3 className="text-xl font-semibold">{linkDialog.kind === "create" ? "New start link" : `Start link #${linkDialog.id}`}</h3>
                <input value={linkDialog.code} onChange={(event) => setLinkDialog({ ...linkDialog, code: event.target.value })} className={`mt-4 ${adminFieldClass}`} placeholder="Code" />
                <textarea value={linkDialog.description} onChange={(event) => setLinkDialog({ ...linkDialog, description: event.target.value })} rows={3} className={`mt-3 ${adminTextAreaClass}`} placeholder="Description" />
                <input value={linkDialog.targetAction} onChange={(event) => setLinkDialog({ ...linkDialog, targetAction: event.target.value })} className={`mt-3 ${adminFieldClass}`} placeholder="Target action" />
                {linkDialog.kind === "edit" ? (
                  <label className="mt-3 inline-flex items-center gap-2 text-sm text-slate-400">
                    <input type="checkbox" checked={linkDialog.isActive} onChange={(event) => setLinkDialog({ ...linkDialog, isActive: event.target.checked })} />
                    Active
                  </label>
                ) : null}
              </>
            )}
            <input value={linkDialog.reason} onChange={(event) => setLinkDialog({ ...linkDialog, reason: event.target.value })} className={`mt-4 ${adminFieldClass}`} placeholder="Operator reason" />
            <div className="mt-4 flex justify-end gap-2">
              <button className={adminButtonClass("secondary")} type="button" onClick={() => setLinkDialog(null)}>Cancel</button>
              <button className={adminButtonClass(linkDialog.kind === "delete" ? "danger" : "primary")} type="button" disabled={busy || !linkDialog.reason.trim()} onClick={() => void submitLinkDialog()}>
                {linkDialog.kind === "delete" ? "Delete" : "Save"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
