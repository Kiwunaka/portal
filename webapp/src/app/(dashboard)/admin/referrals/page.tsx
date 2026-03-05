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
import { Copy, ExternalLink, Link2, Loader2, PencilLine, Plus, RefreshCw, Search, Sparkles, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { fmtRuDate } from "../nav";

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

  const load = useCallback(async (): Promise<void> => {
    setError("");
    setResult("");
    try {
      const [rows, queue] = await Promise.all([adminStartLinks(true), adminReferralQueue(120, queueStatus)]);
      setLinks(rows);
      setQueueRows(queue);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка загрузки ссылок"));
    }
  }, [queueStatus]);

  useEffect(() => {
    void load();
  }, [load]);

  const createLink = async (): Promise<void> => {
    const code = window.prompt("Код start-ссылки:", "launch14");
    if (!code?.trim()) return;
    const description = window.prompt("Описание:", "Campaign link") || "";
    const targetAction = window.prompt("target_action:", "campaign") || "campaign";
    setBusy(true);
    try {
      await adminStartLinkCreate({ code: code.trim(), description, target_action: targetAction.trim(), is_active: true });
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось создать ссылку"));
    } finally { setBusy(false); }
  };

  const editLink = async (row: AdminStartLinkRow): Promise<void> => {
    const code = window.prompt("Код:", row.code || "");
    if (!code?.trim()) return;
    const description = window.prompt("Описание:", row.description || "") || "";
    const targetAction = window.prompt("target_action:", row.target_action || "campaign") || "campaign";
    const activeRaw = window.prompt("Активна? (yes/no)", row.is_active ? "yes" : "no") || "yes";
    setBusy(true);
    try {
      await adminStartLinkUpdate(row.id, { code: code.trim(), description: description.trim(), target_action: targetAction.trim(), is_active: activeRaw.trim().toLowerCase() !== "no" });
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось обновить ссылку"));
    } finally { setBusy(false); }
  };

  const deactivateLink = async (id: number): Promise<void> => {
    setBusy(true);
    try { await adminStartLinkDelete(id); await load(); } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось деактивировать ссылку"));
    } finally { setBusy(false); }
  };

  const buildLinks = async (): Promise<void> => {
    setBusy(true);
    setError("");
    try {
      const out = await adminBuildCampaignLinks({
        promo_code: promoCode.trim() || undefined,
        campaign_key: campaignKey.trim() || undefined,
        plan_code: planCode.trim() || undefined,
        source: "bot",
      });
      setBuilt(out);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось собрать кампейн-ссылки"));
    } finally { setBusy(false); }
  };

  const copyText = async (text: string): Promise<void> => {
    try { await navigator.clipboard.writeText(text); } catch { /* noop */ }
  };

  const processQueue = async (forceWithoutActivity = false): Promise<void> => {
    setBusy(true);
    setError("");
    setResult("");
    try {
      const out = await adminReferralProcess({ limit: 120, force_without_activity: forceWithoutActivity });
      setResult(`Processed: ${out.processed}, rewarded: ${out.rewarded}, waiting: ${out.waiting}, rejected: ${out.rejected}`);
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось обработать anti-fraud очередь"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-5">
      {/* ── Start links ────────────────────────────────── */}
      <article className="glass-card p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="stat-icon stat-icon-violet"><Link2 size={20} /></div>
            <div>
              <h2 className="font-display text-xl font-bold">Start links</h2>
              <p className="text-xs text-slate-500">Welcome / campaign ссылки для бота</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => void createLink()} disabled={busy}>
              <Plus size={14} /> Start link
            </button>
            <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold inline-flex items-center gap-1" type="button" onClick={() => void load()}>
              <RefreshCw size={13} />
            </button>
          </div>
        </div>
        {error ? <p className="mb-3 text-sm text-rose-500">{error}</p> : null}

        <div className="space-y-2">
          {links.length === 0 ? (
            <div className="empty-state"><Link2 size={28} /><p className="text-xs">Нет start-ссылок</p></div>
          ) : null}
          {links.map((link) => (
            <div key={link.id} className="node-card flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <span className={`status-dot ${link.is_active ? "status-dot-online" : "status-dot-stale"}`} />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="badge badge-violet font-mono">{link.code}</span>
                    <span className="text-xs text-slate-500">{link.description || "—"}</span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-0.5">Обновлено: {fmtRuDate(link.updated_at)}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <a href={link.bot_start_link} target="_blank" className="outline-btn rounded-lg px-2 py-1 text-[10px] font-semibold inline-flex items-center gap-1">
                  <ExternalLink size={10} /> Open
                </a>
                <button className="outline-btn rounded-lg px-2 py-1 text-[10px] font-semibold inline-flex items-center gap-1" type="button" onClick={() => void editLink(link)} disabled={busy}>
                  <PencilLine size={10} />
                </button>
                {link.is_active ? (
                  <button className="outline-btn rounded-lg px-2 py-1 text-[10px] font-semibold inline-flex items-center gap-1 text-rose-500" type="button" onClick={() => void deactivateLink(link.id)} disabled={busy}>
                    <X size={10} />
                  </button>
                ) : (
                  <span className="badge badge-danger">off</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </article>

      {/* ── Campaign links builder ─────────────────────── */}
      <article className="stat-card p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="stat-icon stat-icon-emerald"><Sparkles size={20} /></div>
          <div>
            <h2 className="font-display text-xl font-bold">Campaign / Welcome links builder</h2>
            <p className="text-xs text-slate-500">Генерация ссылок для маркетинговых кампаний</p>
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          <div>
            <label className="block text-[10px] uppercase tracking-[0.1em] text-slate-500 mb-1">Promo code</label>
            <input value={promoCode} onChange={(event) => setPromoCode(event.target.value)} placeholder="WELCOME14" className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" />
          </div>
          <div>
            <label className="block text-[10px] uppercase tracking-[0.1em] text-slate-500 mb-1">Campaign key</label>
            <input value={campaignKey} onChange={(event) => setCampaignKey(event.target.value)} placeholder="launch14" className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" />
          </div>
          <div>
            <label className="block text-[10px] uppercase tracking-[0.1em] text-slate-500 mb-1">Plan code</label>
            <input value={planCode} onChange={(event) => setPlanCode(event.target.value)} placeholder="1_month" className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" />
          </div>
        </div>
        <button className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em] inline-flex items-center gap-2" type="button" onClick={() => void buildLinks()} disabled={busy}>
          {busy ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
          Собрать ссылки
        </button>
        {built ? (
          <div className="grid gap-2 text-sm">
            {[
              { label: "Bot", value: built.bot_start_link },
              { label: "Checkout", value: built.checkout_link },
              { label: "WebApp", value: built.webapp_link },
            ].map((item) => (
              <div key={item.label} className="node-card flex items-center justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">{item.label}</p>
                  <p className="text-xs font-mono truncate">{item.value}</p>
                </div>
                <button className="outline-btn rounded-lg px-2.5 py-1.5 inline-flex items-center gap-1 text-xs font-semibold flex-shrink-0" type="button" onClick={() => void copyText(item.value)}>
                  <Copy size={11} /> Copy
                </button>
              </div>
            ))}
          </div>
        ) : null}
      </article>

      {/* ── Referral anti-fraud queue ─────────────────── */}
      <article className="glass-card p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="stat-icon stat-icon-amber"><Search size={20} /></div>
            <div>
              <h2 className="font-display text-xl font-bold">Referral anti-fraud queue</h2>
              <p className="text-xs text-slate-500">Подтверждение бонуса после окна активного использования</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={queueStatus}
              onChange={(event) => setQueueStatus(event.target.value)}
              className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            >
              <option value="">all statuses</option>
              <option value="pending">pending</option>
              <option value="rewarded">rewarded</option>
              <option value="rejected">rejected</option>
              <option value="waiting_activity">waiting_activity</option>
            </select>
            <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void processQueue(false)} disabled={busy}>
              Process
            </button>
            <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void processQueue(true)} disabled={busy}>
              Force
            </button>
          </div>
        </div>
        {error ? <p className="mb-2 text-sm text-rose-500">{error}</p> : null}
        {result ? <p className="mb-2 text-sm text-emerald-500">{result}</p> : null}
        <div className="max-h-[40vh] overflow-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="px-2 py-2">Order</th>
                <th className="px-2 py-2">Referrer</th>
                <th className="px-2 py-2">Referred</th>
                <th className="px-2 py-2">Ready at</th>
                <th className="px-2 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {queueRows.map((row) => (
                <tr key={row.id} className="border-t border-white/30 dark:border-white/10">
                  <td className="px-2 py-2 font-mono">{row.order_id}</td>
                  <td className="px-2 py-2">{row.referrer_tg_id}</td>
                  <td className="px-2 py-2">{row.referred_tg_id}</td>
                  <td className="px-2 py-2">{fmtRuDate(row.ready_at)}</td>
                  <td className="px-2 py-2"><span className="badge badge-violet">{row.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
          {queueRows.length === 0 ? <p className="py-3 text-xs text-slate-500">Очередь пуста.</p> : null}
        </div>
      </article>
    </section>
  );
}
