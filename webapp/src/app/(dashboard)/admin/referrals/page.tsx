"use client";

import {
  adminBuildCampaignLinks,
  adminStartLinkCreate,
  adminStartLinkDelete,
  adminStartLinkUpdate,
  adminStartLinks,
  type AdminStartLinkRow,
  type CampaignLinksBuildResult,
} from "@/lib/api";
import { useEffect, useState } from "react";
import { fmtRuDate } from "../nav";

export default function AdminReferralsPage() {
  const [links, setLinks] = useState<AdminStartLinkRow[]>([]);
  const [built, setBuilt] = useState<CampaignLinksBuildResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [promoCode, setPromoCode] = useState("");
  const [campaignKey, setCampaignKey] = useState("");
  const [planCode, setPlanCode] = useState("");

  const load = async (): Promise<void> => {
    setError("");
    try {
      const rows = await adminStartLinks(true);
      setLinks(rows);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка загрузки ссылок"));
    }
  };

  useEffect(() => {
    void load();
  }, []);

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
    } finally {
      setBusy(false);
    }
  };

  const editLink = async (row: AdminStartLinkRow): Promise<void> => {
    const code = window.prompt("Код:", row.code || "");
    if (!code?.trim()) return;
    const description = window.prompt("Описание:", row.description || "") || "";
    const targetAction = window.prompt("target_action:", row.target_action || "campaign") || "campaign";
    const activeRaw = window.prompt("Активна? (yes/no)", row.is_active ? "yes" : "no") || "yes";
    setBusy(true);
    try {
      await adminStartLinkUpdate(row.id, {
        code: code.trim(),
        description: description.trim(),
        target_action: targetAction.trim(),
        is_active: activeRaw.trim().toLowerCase() !== "no",
      });
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось обновить ссылку"));
    } finally {
      setBusy(false);
    }
  };

  const deactivateLink = async (id: number): Promise<void> => {
    setBusy(true);
    try {
      await adminStartLinkDelete(id);
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось деактивировать ссылку"));
    } finally {
      setBusy(false);
    }
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
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-4">
      <article className="glass-card p-4">
        <div className="mb-3 flex flex-wrap gap-2">
          <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void createLink()} disabled={busy}>
            + Start link
          </button>
          <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void load()}>
            Обновить
          </button>
        </div>
        {error ? <p className="mb-2 text-sm text-rose-500">{error}</p> : null}
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="px-2 py-2">Code</th>
                <th className="px-2 py-2">Описание</th>
                <th className="px-2 py-2">Bot link</th>
                <th className="px-2 py-2">Обновлено</th>
                <th className="px-2 py-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {links.map((link) => (
                <tr key={link.id} className="border-t border-white/30 dark:border-white/10">
                  <td className="px-2 py-2 font-mono text-xs">{link.code}</td>
                  <td className="px-2 py-2">{link.description || "—"}</td>
                  <td className="px-2 py-2">
                    <a href={link.bot_start_link} target="_blank" className="text-violet-600 underline dark:text-violet-300">
                      открыть
                    </a>
                  </td>
                  <td className="px-2 py-2">{fmtRuDate(link.updated_at)}</td>
                  <td className="px-2 py-2">
                    <div className="flex gap-2">
                      <button className="outline-btn rounded-xl px-2 py-1 text-xs font-semibold" type="button" onClick={() => void editLink(link)} disabled={busy}>
                        edit
                      </button>
                      {link.is_active ? (
                        <button className="outline-btn rounded-xl px-2 py-1 text-xs font-semibold" type="button" onClick={() => void deactivateLink(link.id)} disabled={busy}>
                          disable
                        </button>
                      ) : (
                        <span className="text-xs text-slate-500">inactive</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>

      <article className="glass-card p-4 space-y-3">
        <h2 className="font-display text-2xl font-semibold">Campaign / Welcome links builder</h2>
        <div className="grid gap-3 md:grid-cols-3">
          <input
            value={promoCode}
            onChange={(event) => setPromoCode(event.target.value)}
            placeholder="Promo code"
            className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          />
          <input
            value={campaignKey}
            onChange={(event) => setCampaignKey(event.target.value)}
            placeholder="Campaign key"
            className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          />
          <input
            value={planCode}
            onChange={(event) => setPlanCode(event.target.value)}
            placeholder="Plan code"
            className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          />
        </div>
        <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em]" type="button" onClick={() => void buildLinks()} disabled={busy}>
          Собрать ссылки
        </button>
        {built ? (
          <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
            <p><strong>Bot:</strong> {built.bot_start_link}</p>
            <p><strong>Checkout:</strong> {built.checkout_link}</p>
            <p><strong>WebApp:</strong> {built.webapp_link}</p>
          </div>
        ) : null}
      </article>
    </section>
  );
}
