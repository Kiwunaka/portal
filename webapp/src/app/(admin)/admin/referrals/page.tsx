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
import { fmtRuDate } from "@/lib/date-format";
import { Copy, ExternalLink, Link2, Loader2, PencilLine, Plus, RefreshCw, Search, Sparkles, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

type StartLinkDialog =
  | { kind: "create"; code: string; description: string; targetAction: string }
  | { kind: "edit"; id: number; code: string; description: string; targetAction: string; isActive: boolean }
  | { kind: "delete"; id: number }
  | null;

function queueStatusLabel(value: string): string {
  const normalized = String(value || "").toLowerCase();
  if (normalized === "pending") return "В ожидании";
  if (normalized === "rewarded") return "Награждён";
  if (normalized === "rejected") return "Отклонён";
  if (normalized === "waiting_activity") return "Ждёт активности";
  return value || "Неизвестно";
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
      setError(String((err as { message?: string })?.message || err || "Не удалось загрузить реферальные данные."));
    }
  }, [queueStatus]);

  useEffect(() => {
    void load();
  }, [load]);

  const createLink = (): void => {
    setLinkDialog({
      kind: "create",
      code: "launch14",
      description: "Стартовая ссылка для кампании.",
      targetAction: "campaign",
    });
  };

  const editLink = (row: AdminStartLinkRow): void => {
    setLinkDialog({
      kind: "edit",
      id: row.id,
      code: row.code || "",
      description: row.description || "",
      targetAction: row.target_action || "campaign",
      isActive: Boolean(row.is_active),
    });
  };

  const deactivateLink = (id: number): void => {
    setLinkDialog({ kind: "delete", id });
  };

  const submitLinkDialog = async (): Promise<void> => {
    if (!linkDialog) return;
    setBusy(true);
    setError("");
    try {
      if (linkDialog.kind === "create") {
        if (!linkDialog.code.trim()) {
          setError("Укажите код стартовой ссылки.");
          setBusy(false);
          return;
        }
        await adminStartLinkCreate({
          code: linkDialog.code.trim(),
          description: linkDialog.description.trim(),
          target_action: linkDialog.targetAction.trim(),
          is_active: true,
        });
        setResult("Стартовая ссылка создана.");
      } else if (linkDialog.kind === "edit") {
        if (!linkDialog.code.trim()) {
          setError("Укажите код стартовой ссылки.");
          setBusy(false);
          return;
        }
        await adminStartLinkUpdate(linkDialog.id, {
          code: linkDialog.code.trim(),
          description: linkDialog.description.trim(),
          target_action: linkDialog.targetAction.trim(),
          is_active: linkDialog.isActive,
        });
        setResult(`Стартовая ссылка #${linkDialog.id} обновлена.`);
      } else if (linkDialog.kind === "delete") {
        await adminStartLinkDelete(linkDialog.id);
        setResult(`Стартовая ссылка #${linkDialog.id} удалена.`);
      }
      setLinkDialog(null);
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось сохранить стартовую ссылку."));
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
      setError(String((err as { message?: string })?.message || err || "Не удалось собрать ссылки."));
    } finally {
      setBusy(false);
    }
  };

  const copyText = async (text: string): Promise<void> => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // noop
    }
  };

  const processQueue = async (forceWithoutActivity = false): Promise<void> => {
    setBusy(true);
    setError("");
    setResult("");
    try {
      const out = await adminReferralProcess({ limit: 120, force_without_activity: forceWithoutActivity });
      setResult(`Очередь обработана: награждено ${out.rewarded}, ожидание ${out.waiting}, отклонено ${out.rejected}, всего ${out.processed}.`);
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось обработать очередь."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-5">
      <article className="glass-card p-4">
        <h2 className="font-display text-xl font-bold">Стартовые ссылки и welcome-цепочки</h2>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Здесь создаются start-ссылки для welcome и campaign-входов, а также обрабатывается реферальная очередь.
        </p>
      </article>

      <article className="glass-card p-5">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="stat-icon stat-icon-violet">
              <Link2 size={20} />
            </div>
            <div className="min-w-0">
              <h2 className="font-display text-xl font-bold">Стартовые ссылки</h2>
              <p className="text-xs text-slate-500">Используются для welcome, промо и других входов.</p>
            </div>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <button className="btn-primary inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => createLink()} disabled={busy}>
              <Plus size={14} /> Новая ссылка
            </button>
            <button className="outline-btn inline-flex items-center gap-1 rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void load()}>
              <RefreshCw size={13} />
            </button>
          </div>
        </div>
        {error ? <p className="mb-3 text-sm text-rose-500">{error}</p> : null}

        <div className="space-y-2">
          {links.length === 0 ? (
            <div className="empty-state">
              <Link2 size={28} />
              <p className="text-xs">Стартовых ссылок пока нет</p>
            </div>
          ) : null}
          {links.map((link) => (
            <div key={link.id} className="node-card flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex min-w-0 flex-1 items-center gap-3">
                <span className={`status-dot ${link.is_active ? "status-dot-online" : "status-dot-stale"}`} />
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="badge badge-violet font-mono">{link.code}</span>
                    <span className="text-xs text-slate-500">{link.description || "Без описания"}</span>
                  </div>
                  <p className="mt-0.5 text-[10px] text-slate-400">Обновлено: {fmtRuDate(link.updated_at)}</p>
                </div>
              </div>
              <div className="flex shrink-0 flex-wrap items-center gap-2">
                <a href={link.bot_start_link} target="_blank" className="outline-btn inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[10px] font-semibold">
                  <ExternalLink size={10} /> Открыть
                </a>
                <button className="outline-btn inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[10px] font-semibold" type="button" onClick={() => editLink(link)} disabled={busy}>
                  <PencilLine size={10} /> Править
                </button>
                {link.is_active ? (
                  <button className="outline-btn inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[10px] font-semibold text-rose-500" type="button" onClick={() => deactivateLink(link.id)} disabled={busy}>
                    <X size={10} /> Выключить
                  </button>
                ) : (
                  <span className="badge badge-danger">Неактивна</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </article>

      <article className="stat-card p-5 sm:p-6 space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="stat-icon stat-icon-emerald">
              <Sparkles size={20} />
            </div>
            <div className="min-w-0">
              <h2 className="font-display text-xl font-bold">Сборщик ссылок для кампаний</h2>
              <p className="text-xs text-slate-500">Генерирует bot, checkout и webapp ссылки по promo, campaign или plan параметрам.</p>
            </div>
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          <div>
            <label className="mb-1 block text-[10px] uppercase tracking-[0.1em] text-slate-500">Промокод</label>
            <input value={promoCode} onChange={(event) => setPromoCode(event.target.value)} placeholder="WELCOME14" className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" />
          </div>
          <div>
            <label className="mb-1 block text-[10px] uppercase tracking-[0.1em] text-slate-500">Ключ кампании</label>
            <input value={campaignKey} onChange={(event) => setCampaignKey(event.target.value)} placeholder="launch14" className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" />
          </div>
          <div>
            <label className="mb-1 block text-[10px] uppercase tracking-[0.1em] text-slate-500">Код тарифа</label>
            <input value={planCode} onChange={(event) => setPlanCode(event.target.value)} placeholder="1_month" className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" />
          </div>
        </div>
        <button className="btn-primary inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em] w-full sm:w-auto" type="button" onClick={() => void buildLinks()} disabled={busy}>
          {busy ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
          Собрать ссылки
        </button>
        {built ? (
          <div className="grid gap-2 text-sm">
            {built.checkout_mode === "bot_fallback" ? (
              <div className="rounded-xl border border-amber-400/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
                Платёжный checkout недоступен, поэтому система собрала ссылку через бот. Проверьте связку перед запуском кампании.
              </div>
            ) : null}
            {[
              { label: "Bot", value: built.bot_start_link },
              { label: "Checkout", value: built.checkout_link },
              { label: "Webapp", value: built.webapp_link },
            ].map((item) => (
              <div key={item.label} className="node-card flex items-center justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">{item.label}</p>
                  <p className="truncate font-mono text-xs">{item.value}</p>
                </div>
                <button className="outline-btn inline-flex shrink-0 items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-semibold" type="button" onClick={() => void copyText(item.value)}>
                  <Copy size={11} /> Копировать
                </button>
              </div>
            ))}
          </div>
        ) : null}
      </article>

      <article className="glass-card p-5">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="stat-icon stat-icon-amber">
              <Search size={20} />
            </div>
            <div className="min-w-0">
              <h2 className="font-display text-xl font-bold">Очередь реферальной проверки</h2>
              <p className="text-xs text-slate-500">Показывает заявки, которые ждут ручной или автоматической обработки.</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={queueStatus}
              onChange={(event) => setQueueStatus(event.target.value)}
              className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            >
              <option value="">Все статусы</option>
              <option value="pending">В ожидании</option>
              <option value="rewarded">Награждён</option>
              <option value="rejected">Отклонён</option>
              <option value="waiting_activity">Ждёт активности</option>
            </select>
            <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void processQueue(false)} disabled={busy}>
              Обработать
            </button>
            <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void processQueue(true)} disabled={busy}>
              Без активности
            </button>
          </div>
        </div>
        {error ? <p className="mb-2 text-sm text-rose-500">{error}</p> : null}
        {result ? <p className="mb-2 text-sm text-emerald-500">{result}</p> : null}
        <div className="max-h-[40vh] overflow-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="px-2 py-2">Заказ</th>
                <th className="px-2 py-2">Реферер</th>
                <th className="px-2 py-2">Приглашённый</th>
                <th className="px-2 py-2">Готово</th>
                <th className="px-2 py-2">Статус</th>
              </tr>
            </thead>
            <tbody>
              {queueRows.map((row) => (
                <tr key={row.id} className="border-t border-white/30 dark:border-white/10">
                  <td className="px-2 py-2 font-mono">{row.order_id}</td>
                  <td className="px-2 py-2">{row.referrer_tg_id}</td>
                  <td className="px-2 py-2">{row.referred_tg_id}</td>
                  <td className="px-2 py-2">{fmtRuDate(row.ready_at)}</td>
                  <td className="px-2 py-2">
                    <span className="badge badge-violet">{queueStatusLabel(row.status)}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {queueRows.length === 0 ? <p className="py-3 text-xs text-slate-500">Очередь пуста.</p> : null}
        </div>
      </article>

      {linkDialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/65 p-4">
          <div className="glass-card w-full max-w-xl p-5">
            {linkDialog.kind === "create" || linkDialog.kind === "edit" ? (
              <>
                <h3 className="font-display text-xl font-semibold">{linkDialog.kind === "create" ? "Новая стартовая ссылка" : `Стартовая ссылка #${linkDialog.id}`}</h3>
                <div className="mt-4 space-y-3">
                  <input
                    value={linkDialog.code}
                    onChange={(event) =>
                      setLinkDialog((prev) => (prev && (prev.kind === "create" || prev.kind === "edit") ? { ...prev, code: event.target.value } : prev))
                    }
                    className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                    placeholder="Код ссылки"
                  />
                  <input
                    value={linkDialog.description}
                    onChange={(event) =>
                      setLinkDialog((prev) => (prev && (prev.kind === "create" || prev.kind === "edit") ? { ...prev, description: event.target.value } : prev))
                    }
                    className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                    placeholder="Описание"
                  />
                  <input
                    value={linkDialog.targetAction}
                    onChange={(event) =>
                      setLinkDialog((prev) => (prev && (prev.kind === "create" || prev.kind === "edit") ? { ...prev, targetAction: event.target.value } : prev))
                    }
                    className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                    placeholder="Целевое действие"
                  />
                  {linkDialog.kind === "edit" ? (
                    <label className="inline-flex items-center gap-2 text-sm text-slate-500">
                      <input
                        type="checkbox"
                        checked={linkDialog.isActive}
                        onChange={(event) => setLinkDialog((prev) => (prev && prev.kind === "edit" ? { ...prev, isActive: event.target.checked } : prev))}
                      />
                      Активна
                    </label>
                  ) : null}
                </div>
                <div className="mt-4 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setLinkDialog(null)}>
                    Отмена
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void submitLinkDialog()}>
                    Сохранить
                  </button>
                </div>
              </>
            ) : null}

            {linkDialog.kind === "delete" ? (
              <>
                <h3 className="font-display text-xl font-semibold">Удалить start-ссылку #{linkDialog.id}?</h3>
                <p className="mt-2 text-sm text-slate-500">Сценарии welcome и campaign больше не смогут использовать эту ссылку.</p>
                <div className="mt-4 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setLinkDialog(null)}>
                    Отмена
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void submitLinkDialog()}>
                    Удалить
                  </button>
                </div>
              </>
            ) : null}
          </div>
        </div>
      ) : null}
    </section>
  );
}
