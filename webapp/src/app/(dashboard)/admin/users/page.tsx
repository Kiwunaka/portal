"use client";

import {
  adminAuditLog,
  adminBulkKeyAction,
  adminManualBlock,
  adminManualCreate,
  adminManualExtend,
  adminManualRegenerateToken,
  adminUserCard,
  adminUserKeyHistory,
  adminUserKeyLimitUpdate,
  adminUserKeyResetTraffic,
  adminUserKeyResyncSubId,
  adminUserKeyToggle,
  adminUserLoyaltyGrant,
  adminUserMessage,
  adminUserPresetRun,
  adminUsers,
  type AdminAuditRow,
  type AdminUserCard,
  type AdminUserKey,
  type AdminUserKeyHistoryRow,
  type AdminUserRow,
} from "@/lib/api";
import { useCallback, useEffect, useMemo, useState } from "react";
import { fmtRuDate } from "../nav";

function fmtTraffic(bytes: number): string {
  const gb = Number(bytes || 0) / (1024 ** 3);
  return `${gb.toFixed(2)} GB`;
}

function fmtOnline(value: boolean | null | undefined): string {
  if (value === true) return "online";
  if (value === false) return "offline";
  return "unknown";
}

function parseNullableNumber(input: string): number | null {
  const raw = input.trim();
  if (!raw) return null;
  const value = Number(raw);
  if (!Number.isFinite(value)) return null;
  return value;
}

function historyBadgeClass(action: string): string {
  const value = String(action || "").toLowerCase();
  if (value.includes("regen") || value.includes("rotate")) return "badge-warning";
  if (value.includes("disable") || value.includes("block")) return "badge-danger";
  if (value.includes("resync") || value.includes("move") || value.includes("node")) return "badge-info";
  if (value.includes("enable") || value.includes("create")) return "badge-success";
  return "badge-violet";
}

type DetailTab = "overview" | "keys" | "history" | "audit";

type KeyPolicyDraft = {
  burst_mbps: string;
  soft_cap_gb: string;
  hard_cap_gb: string;
  notify_soft: boolean;
  notify_hard: boolean;
  auto_disable_on_hard: boolean;
  apply_now: boolean;
};

function emptyPolicyDraft(): KeyPolicyDraft {
  return {
    burst_mbps: "",
    soft_cap_gb: "",
    hard_cap_gb: "",
    notify_soft: true,
    notify_hard: true,
    auto_disable_on_hard: true,
    apply_now: true,
  };
}

export default function AdminUsersPage() {
  const [query, setQuery] = useState("");
  const [rows, setRows] = useState<AdminUserRow[]>([]);
  const [selected, setSelected] = useState<AdminUserCard | null>(null);
  const [keyHistoryRows, setKeyHistoryRows] = useState<AdminUserKeyHistoryRow[]>([]);
  const [auditRows, setAuditRows] = useState<AdminAuditRow[]>([]);
  const [policyDrafts, setPolicyDrafts] = useState<Record<string, KeyPolicyDraft>>({});
  const [detailTab, setDetailTab] = useState<DetailTab>("overview");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [keyBusy, setKeyBusy] = useState("");
  const [policyBusy, setPolicyBusy] = useState("");
  const [error, setError] = useState("");
  const [okMessage, setOkMessage] = useState("");
  const [bulkResult, setBulkResult] = useState("");
  const [bulkAction, setBulkAction] = useState({
    action: "disable" as "disable" | "enable" | "reset" | "resync",
    segment: "all",
    q: "",
    nodeCodes: "",
    limit: 50,
    dryRun: true,
    force: false,
  });

  const loadCardDetails = useCallback(async (tgId: number): Promise<void> => {
    const [card, history, audit] = await Promise.all([
      adminUserCard(tgId),
      adminUserKeyHistory(tgId, 150),
      adminAuditLog({ target_tg_id: tgId, limit: 120, offset: 0 }),
    ]);
    setSelected(card);
    setKeyHistoryRows(history);
    setAuditRows(audit);
  }, []);

  const loadUsers = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError("");
    setOkMessage("");
    try {
      const users = await adminUsers(query, 80, 0);
      setRows(users);
      if (!users.length) {
        setSelected(null);
        setKeyHistoryRows([]);
        setAuditRows([]);
      } else {
        const nextId =
          selected?.user.tg_id && users.some((item) => item.tg_id === selected.user.tg_id)
            ? selected.user.tg_id
            : users[0]?.tg_id;
        if (nextId) {
          await loadCardDetails(nextId);
        }
      }
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка загрузки"));
    } finally {
      setLoading(false);
    }
  }, [loadCardDetails, query, selected?.user.tg_id]);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  useEffect(() => {
    const next: Record<string, KeyPolicyDraft> = {};
    for (const key of selected?.keys || []) {
      const policy = key.policy || selected?.key_policies?.find((row) => row.node_code === key.node_code) || null;
      next[key.node_code] = {
        burst_mbps: policy?.burst_mbps == null ? "" : String(policy.burst_mbps),
        soft_cap_gb: policy?.soft_cap_gb == null ? "" : String(policy.soft_cap_gb),
        hard_cap_gb: policy?.hard_cap_gb == null ? "" : String(policy.hard_cap_gb),
        notify_soft: policy?.notify_soft ?? true,
        notify_hard: policy?.notify_hard ?? true,
        auto_disable_on_hard: policy?.auto_disable_on_hard ?? true,
        apply_now: true,
      };
    }
    setPolicyDrafts(next);
  }, [selected]);

  const pickUser = async (tgId: number): Promise<void> => {
    setBusy(true);
    setError("");
    setOkMessage("");
    try {
      await loadCardDetails(tgId);
      setDetailTab("overview");
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось открыть карточку"));
    } finally {
      setBusy(false);
    }
  };

  const selectedTgId = Number(selected?.user.tg_id || 0);

  const reloadSelected = async (): Promise<void> => {
    if (!selectedTgId) return;
    await pickUser(selectedTgId);
  };

  const copyText = async (text: string): Promise<void> => {
    if (!text.trim()) return;
    try {
      await navigator.clipboard.writeText(text.trim());
      setOkMessage("Скопировано в буфер.");
    } catch {
      window.alert("Не удалось скопировать");
    }
  };

  const actionMessage = async (): Promise<void> => {
    if (!selectedTgId) return;
    const text = window.prompt("Текст сообщения пользователю:");
    if (!text?.trim()) return;
    setBusy(true);
    try {
      await adminUserMessage(selectedTgId, text.trim());
      setOkMessage("Сообщение отправлено.");
      await reloadSelected();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка отправки"));
    } finally {
      setBusy(false);
    }
  };

  const actionExtend = async (): Promise<void> => {
    if (!selectedTgId) return;
    const raw = window.prompt("Продлить на сколько дней?", "30");
    const days = Number(raw || 0);
    if (!Number.isFinite(days) || days === 0) return;
    setBusy(true);
    try {
      await adminManualExtend(selectedTgId, days);
      setOkMessage(`Подписка продлена на ${days} дн.`);
      await reloadSelected();
      await loadUsers();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка продления"));
    } finally {
      setBusy(false);
    }
  };

  const actionToggleBlock = async (): Promise<void> => {
    if (!selectedTgId) return;
    const blocked = Boolean(selected?.user.is_active);
    setBusy(true);
    try {
      await adminManualBlock(selectedTgId, blocked);
      setOkMessage(blocked ? "Пользователь заблокирован." : "Пользователь разблокирован.");
      await reloadSelected();
      await loadUsers();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка блокировки"));
    } finally {
      setBusy(false);
    }
  };

  const actionRegenerateToken = async (): Promise<void> => {
    if (!selectedTgId) return;
    setBusy(true);
    try {
      const out = await adminManualRegenerateToken(selectedTgId);
      setOkMessage(`Новый токен создан (sync: ${out.sync_ok ? "ok" : "warn"}).`);
      window.alert(`Новая ссылка:\n${out.subscription_url}\n\nSync: ${out.sync_ok ? "OK" : "WARN"}`);
      await reloadSelected();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка ротации токена"));
    } finally {
      setBusy(false);
    }
  };

  const actionCreateManual = async (): Promise<void> => {
    const displayName = window.prompt("Имя для manual пользователя:", "Offline user");
    const daysRaw = window.prompt("Срок доступа (дни):", "30");
    const days = Number(daysRaw || 0);
    if (!displayName?.trim() || !Number.isFinite(days) || days <= 0) return;
    setBusy(true);
    try {
      await adminManualCreate({ display_name: displayName.trim(), days });
      setOkMessage("Manual пользователь создан.");
      await loadUsers();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка создания manual пользователя"));
    } finally {
      setBusy(false);
    }
  };

  const runKeyAction = async (key: AdminUserKey, action: "toggle" | "reset" | "resync"): Promise<void> => {
    if (!selectedTgId) return;
    const op = `${key.node_code}:${action}`;
    setKeyBusy(op);
    setError("");
    setOkMessage("");
    try {
      if (action === "toggle") {
        await adminUserKeyToggle(selectedTgId, key.node_code, !Boolean(key.enabled));
      } else if (action === "reset") {
        await adminUserKeyResetTraffic(selectedTgId, key.node_code);
      } else {
        await adminUserKeyResyncSubId(selectedTgId, key.node_code);
      }
      setOkMessage(`Операция ${action} выполнена для ${key.node_code}.`);
      await reloadSelected();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка управления ключом"));
    } finally {
      setKeyBusy("");
    }
  };

  const runPreset = async (preset: "reset_key" | "rotate_link" | "extend_1d" | "send_guide"): Promise<void> => {
    if (!selectedTgId) return;
    setBusy(true);
    setError("");
    setOkMessage("");
    try {
      const result = await adminUserPresetRun(selectedTgId, preset);
      setOkMessage(`Preset ${result.preset} выполнен.`);
      await reloadSelected();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось выполнить preset"));
    } finally {
      setBusy(false);
    }
  };

  const savePolicy = async (nodeCode: string): Promise<void> => {
    if (!selectedTgId) return;
    const draft = policyDrafts[nodeCode] || emptyPolicyDraft();
    setPolicyBusy(nodeCode);
    setError("");
    setOkMessage("");
    try {
      await adminUserKeyLimitUpdate(selectedTgId, nodeCode, {
        burst_mbps: parseNullableNumber(draft.burst_mbps),
        soft_cap_gb: parseNullableNumber(draft.soft_cap_gb),
        hard_cap_gb: parseNullableNumber(draft.hard_cap_gb),
        notify_soft: draft.notify_soft,
        notify_hard: draft.notify_hard,
        auto_disable_on_hard: draft.auto_disable_on_hard,
        apply_now: draft.apply_now,
      });
      setOkMessage(`Лимиты для ${nodeCode} сохранены.`);
      await reloadSelected();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось сохранить лимиты"));
    } finally {
      setPolicyBusy("");
    }
  };

  const runBulkAction = async (): Promise<void> => {
    setBusy(true);
    setError("");
    setBulkResult("");
    setOkMessage("");
    try {
      if (!bulkAction.dryRun) {
        const confirmText = window.prompt("Для подтверждения массовой операции введите APPLY");
        if ((confirmText || "").trim().toUpperCase() !== "APPLY") {
          setBusy(false);
          return;
        }
      }
      const nodeCodes = bulkAction.nodeCodes.split(",").map((item) => item.trim()).filter(Boolean);
      const out = await adminBulkKeyAction({
        action: bulkAction.action,
        segment: bulkAction.segment,
        node_codes: nodeCodes.length ? nodeCodes : undefined,
        q: bulkAction.q.trim() || undefined,
        limit: Math.max(1, Math.min(500, Number(bulkAction.limit || 50))),
        dry_run: bulkAction.dryRun,
        force: bulkAction.force,
      });
      const affected = Number(out?.affected || 0);
      const failed = Number(out?.failed || 0);
      const mode = out?.dry_run ? "dry-run" : "apply";
      setBulkResult(`Bulk ${mode}: affected ${affected}, failed ${failed}`);
      if (!bulkAction.dryRun) {
        await loadUsers();
      }
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка массовой операции"));
    } finally {
      setBusy(false);
    }
  };

  const grantLoyaltyTier = async (tierDays: number): Promise<void> => {
    if (!selectedTgId) return;
    setBusy(true);
    setError("");
    setOkMessage("");
    try {
      const out = await adminUserLoyaltyGrant(selectedTgId, tierDays);
      setOkMessage(`Loyalty-награда ${out.tier_days} дней выдана.`);
      await reloadSelected();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось выдать loyalty-награду"));
    } finally {
      setBusy(false);
    }
  };

  const keys = selected?.keys || [];
  const summary = selected?.summary;
  const risk = selected?.risk;
  const loyalty = selected?.loyalty;

  const riskClass = useMemo(() => {
    const level = String(risk?.level || "").toLowerCase();
    if (level === "critical") return "badge-danger";
    if (level === "high") return "badge-warning";
    if (level === "medium") return "badge-info";
    return "badge-success";
  }, [risk?.level]);

  const tabButtonClass = (tab: DetailTab): string =>
    `rounded-xl px-3 py-2 text-xs font-semibold uppercase tracking-[0.08em] transition ${
      detailTab === tab ? "bg-violet-600 text-white shadow-lg shadow-violet-600/25" : "outline-btn"
    }`;

  return (
    <section className="grid gap-4 xl:grid-cols-[1fr,1fr]">
      <article className="glass-card p-4">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Поиск по username или tg_id"
            className="flex-1 rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          />
          <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void loadUsers()}>
            Найти
          </button>
          <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void actionCreateManual()} disabled={busy}>
            + Manual
          </button>
        </div>

        <div className="mb-3 rounded-xl border border-violet-200/40 bg-white/70 p-3 dark:border-violet-500/20 dark:bg-white/5">
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">Безопасные массовые действия по ключам</p>
          <div className="grid gap-2 sm:grid-cols-2">
            <select
              value={bulkAction.action}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, action: event.target.value as "disable" | "enable" | "reset" | "resync" }))}
              className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            >
              <option value="disable">disable keys</option>
              <option value="enable">enable keys</option>
              <option value="reset">reset traffic</option>
              <option value="resync">resync subId</option>
            </select>
            <select
              value={bulkAction.segment}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, segment: event.target.value }))}
              className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            >
              <option value="all">segment: all</option>
              <option value="paid">segment: paid</option>
              <option value="free">segment: free</option>
              <option value="manual">segment: manual</option>
              <option value="active">segment: active</option>
              <option value="inactive">segment: inactive</option>
            </select>
            <input
              value={bulkAction.q}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, q: event.target.value }))}
              placeholder="Доп. фильтр (username/tg_id)"
              className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            />
            <input
              value={bulkAction.nodeCodes}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, nodeCodes: event.target.value }))}
              placeholder="Ноды через запятую (опц.)"
              className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            />
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <label className="text-xs text-slate-600 dark:text-slate-300">
              limit:
              <input
                type="number"
                min={1}
                max={500}
                value={bulkAction.limit}
                onChange={(event) => setBulkAction((prev) => ({ ...prev, limit: Number(event.target.value || 50) }))}
                className="ml-1 w-20 rounded-lg border border-violet-200/50 bg-white/80 px-2 py-1 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
              />
            </label>
            <label className="inline-flex items-center gap-1 text-xs text-slate-600 dark:text-slate-300">
              <input type="checkbox" checked={bulkAction.dryRun} onChange={(event) => setBulkAction((prev) => ({ ...prev, dryRun: event.target.checked }))} />
              dry-run
            </label>
            <label className="inline-flex items-center gap-1 text-xs text-slate-600 dark:text-slate-300">
              <input type="checkbox" checked={bulkAction.force} onChange={(event) => setBulkAction((prev) => ({ ...prev, force: event.target.checked }))} />
              force
            </label>
            <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={() => void runBulkAction()} disabled={busy}>
              Выполнить
            </button>
          </div>
          {bulkResult ? <p className="mt-2 text-xs text-emerald-500">{bulkResult}</p> : null}
        </div>

        {loading ? <p className="text-sm text-slate-500">Загрузка пользователей...</p> : null}
        {error ? <p className="mb-2 text-sm text-rose-500">{error}</p> : null}
        {okMessage ? <p className="mb-2 text-sm text-emerald-500">{okMessage}</p> : null}

        <div className="max-h-[58vh] overflow-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="px-2 py-2">ID</th>
                <th className="px-2 py-2">Пользователь</th>
                <th className="px-2 py-2">План</th>
                <th className="px-2 py-2">Статус</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={row.tg_id}
                  className={`cursor-pointer border-t border-white/30 dark:border-white/10 ${
                    row.tg_id === selectedTgId ? "bg-violet-500/10" : ""
                  }`}
                  onClick={() => void pickUser(row.tg_id)}
                >
                  <td className="px-2 py-2 font-mono text-xs">{row.tg_id}</td>
                  <td className="px-2 py-2">{row.display_name || row.username || "—"}</td>
                  <td className="px-2 py-2">{row.sub_type || "—"}</td>
                  <td className="px-2 py-2">
                    <span className={`rounded-full px-2 py-1 text-xs ${row.is_active ? "bg-emerald-500/20 text-emerald-600" : "bg-rose-500/20 text-rose-500"}`}>
                      {row.is_active ? "active" : "blocked"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>

      <article className="glass-card p-4">
        {!selected ? (
          <p className="text-sm text-slate-500">Выберите пользователя слева.</p>
        ) : (
          <>
            <div className="mb-3">
              <h2 className="font-display text-2xl font-semibold">Карточка #{selected.user.tg_id}</h2>
              <p className="text-xs text-slate-500">Создан: {fmtRuDate(selected.user.created_at)}</p>
              <p className="text-xs text-slate-500">Истекает: {fmtRuDate(selected.user.expiry_at)}</p>
            </div>

            <div className="mb-3 grid gap-2 sm:grid-cols-2">
              <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void actionMessage()} disabled={busy}>
                Сообщение
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void actionExtend()} disabled={busy}>
                Продлить
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void actionRegenerateToken()} disabled={busy}>
                Новый токен
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void actionToggleBlock()} disabled={busy}>
                {selected.user.is_active ? "Блокировать" : "Разблокировать"}
              </button>
            </div>

            <div className="mb-3 grid gap-2 sm:grid-cols-2">
              <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void runPreset("reset_key")} disabled={busy}>
                Preset: reset key
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void runPreset("rotate_link")} disabled={busy}>
                Preset: rotate link
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void runPreset("extend_1d")} disabled={busy}>
                Preset: extend 1 day
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void runPreset("send_guide")} disabled={busy}>
                Preset: send guide
              </button>
            </div>

            <div className="mb-3 grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                <p>План: <strong>{selected.user.sub_type}</strong></p>
                <p>Stars paid: <strong>{selected.user.stars_paid}</strong></p>
                <p>Referrals: <strong>{selected.user.referral_count}</strong></p>
                <p>Loyalty streak: <strong>{loyalty?.streak_days ?? 0} дн.</strong></p>
              </div>
              <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                <div className="mb-1 flex items-center gap-2">
                  <span className={`badge ${riskClass}`}>risk {Math.round(risk?.score || 0)}</span>
                  <span className="text-xs text-slate-500">{risk?.level || "low"}</span>
                </div>
                <p className="text-xs">Regen: <strong>{risk?.signals?.regen_count ?? 0}</strong></p>
                <p className="text-xs">Admin key ops: <strong>{risk?.signals?.admin_key_ops ?? 0}</strong></p>
                <p className="text-xs">Unique IP: <strong>{risk?.signals?.unique_ips ?? 0}</strong></p>
                <p className="text-xs">Traffic: <strong>{Number(risk?.signals?.traffic_gb || 0).toFixed(2)} GB</strong></p>
              </div>
            </div>

            <div className="mt-3 rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
              <p className="mb-1 font-semibold">Подписка</p>
              <div className="flex items-start gap-2">
                <input
                  value={String(selected.user.subscription_url || "")}
                  readOnly
                  className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                />
                <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void copyText(String(selected.user.subscription_url || ""))}>
                  Copy URL
                </button>
              </div>
              <div className="mt-2 flex items-start gap-2">
                <input
                  value={String(selected.user.subscription_token || "")}
                  readOnly
                  className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                />
                <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void copyText(String(selected.user.subscription_token || ""))}>
                  Copy token
                </button>
              </div>
            </div>

            {loyalty?.tiers?.length ? (
              <div className="mb-3 rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                <p className="mb-2 font-semibold">Loyalty tiers (30/90/180)</p>
                <div className="grid gap-2 sm:grid-cols-3">
                  {loyalty.tiers.map((tier) => (
                    <div key={tier.reward_key} className="rounded-xl border border-white/30 bg-white/70 p-2 text-xs dark:border-white/10 dark:bg-white/5">
                      <p className="font-semibold">{tier.days} дн.</p>
                      <p>Бонус: {tier.bonus_days} дн.</p>
                      <p>Perk: {tier.perk}</p>
                      <p className="mt-1">Статус: {tier.claimed ? "claimed" : tier.unlocked ? "unlocked" : "locked"}</p>
                      {!tier.claimed && tier.unlocked ? (
                        <button className="mt-2 outline-btn rounded-lg px-2 py-1 text-[11px] font-semibold" type="button" disabled={busy} onClick={() => void grantLoyaltyTier(tier.days)}>
                          Выдать tier
                        </button>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="mb-3 flex flex-wrap gap-2">
              <button className={tabButtonClass("overview")} type="button" onClick={() => setDetailTab("overview")}>overview</button>
              <button className={tabButtonClass("keys")} type="button" onClick={() => setDetailTab("keys")}>keys</button>
              <button className={tabButtonClass("history")} type="button" onClick={() => setDetailTab("history")}>история ключей</button>
              <button className={tabButtonClass("audit")} type="button" onClick={() => setDetailTab("audit")}>журнал админа</button>
            </div>

            {detailTab === "overview" ? (
              <>
                <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                  <p className="mb-2 font-semibold">Сводка ключей</p>
                  {summary ? (
                    <div className="grid gap-2 text-xs sm:grid-cols-2">
                      <p>Нод с ключом: <strong>{summary.nodes_with_client}/{summary.nodes_total}</strong></p>
                      <p>Online нод: <strong>{summary.nodes_online}</strong></p>
                      <p>Enabled нод: <strong>{summary.nodes_enabled}</strong></p>
                      <p>SubId mismatch: <strong>{summary.subid_mismatch_count}</strong></p>
                      <p>Трафик всего: <strong>{fmtTraffic(summary.traffic_total_bytes)}</strong></p>
                      <p>Panel state: <strong>{summary.panel_state || "unknown"}</strong></p>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500">Сводка недоступна.</p>
                  )}
                </div>
                <h3 className="mt-4 font-display text-xl font-semibold">Последние тикеты</h3>
                <div className="mt-2 space-y-2">
                  {(selected.tickets || []).map((ticket) => (
                    <div key={ticket.id} className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                      <p className="font-medium">#{ticket.id} • {ticket.status_title}</p>
                      <p className="text-xs text-slate-500">{ticket.last_message_preview || "Без сообщений"}</p>
                    </div>
                  ))}
                  {!selected.tickets?.length ? <p className="text-xs text-slate-500">Тикетов нет.</p> : null}
                </div>
              </>
            ) : null}

            {detailTab === "keys" ? (
              <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <p className="font-semibold">Ключи, лимиты и управление</p>
                  <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={() => void reloadSelected()} disabled={busy || !!keyBusy || !!policyBusy}>
                    Обновить
                  </button>
                </div>
                <div className="space-y-2">
                  {keys.length === 0 ? <p className="text-xs text-slate-500">Ключи не найдены для текущего плана.</p> : null}
                  {keys.map((key) => {
                    const toggleOp = `${key.node_code}:toggle`;
                    const resetOp = `${key.node_code}:reset`;
                    const resyncOp = `${key.node_code}:resync`;
                    const busyToggle = keyBusy === toggleOp;
                    const busyReset = keyBusy === resetOp;
                    const busyResync = keyBusy === resyncOp;
                    const draft = policyDrafts[key.node_code] || emptyPolicyDraft();
                    return (
                      <div key={key.node_code} className="rounded-xl border border-white/35 bg-white/70 p-3 text-xs dark:border-white/10 dark:bg-white/5">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <p className="font-semibold">{key.node_code} • {key.node_name || "Node"}</p>
                          <span className={`rounded-full px-2 py-0.5 ${key.exists ? "bg-emerald-500/20 text-emerald-600" : "bg-slate-300/40 text-slate-500"}`}>
                            {key.exists ? "key exists" : "no key"}
                          </span>
                        </div>
                        <p className="mt-1">Online: <strong>{fmtOnline(key.online)}</strong> • Enabled: <strong>{key.enabled ? "yes" : "no"}</strong></p>
                        <p>SubId: <strong>{key.sub_id || "—"}</strong></p>
                        <p>Expected: <strong>{key.expected_sub_id || "—"}</strong> • Match: <strong>{key.sub_id_match ? "yes" : "no"}</strong></p>
                        <p>Traffic: <strong>{fmtTraffic(key.total_bytes)}</strong> ({key.up_bytes}↑ / {key.down_bytes}↓)</p>
                        <p>Last online: <strong>{fmtRuDate(key.last_online_at)}</strong></p>

                        <div className="mt-2 flex flex-wrap gap-2">
                          <button className="outline-btn rounded-xl px-2.5 py-1 text-[11px] font-semibold" type="button" disabled={busy || !key.exists || !!keyBusy} onClick={() => void runKeyAction(key, "toggle")}>
                            {busyToggle ? "..." : key.enabled ? "Disable" : "Enable"}
                          </button>
                          <button className="outline-btn rounded-xl px-2.5 py-1 text-[11px] font-semibold" type="button" disabled={busy || !key.exists || !!keyBusy} onClick={() => void runKeyAction(key, "reset")}>
                            {busyReset ? "..." : "Reset traffic"}
                          </button>
                          <button className="outline-btn rounded-xl px-2.5 py-1 text-[11px] font-semibold" type="button" disabled={busy || !key.exists || !!keyBusy} onClick={() => void runKeyAction(key, "resync")}>
                            {busyResync ? "..." : "Resync subId"}
                          </button>
                          <button className="outline-btn rounded-xl px-2.5 py-1 text-[11px] font-semibold" type="button" disabled={!String(key.vless_link || "").trim()} onClick={() => void copyText(String(key.vless_link || ""))}>
                            Copy key
                          </button>
                        </div>

                        <div className="mt-3 rounded-xl border border-violet-200/40 bg-white/80 p-2 dark:border-violet-500/20 dark:bg-slate-900/60">
                          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Per-key лимиты и автонотификации</p>
                          <div className="grid gap-2 sm:grid-cols-3">
                            <input
                              value={draft.burst_mbps}
                              onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, burst_mbps: event.target.value } }))}
                              placeholder="burst Mbps"
                              className="rounded-lg border border-violet-200/50 bg-white px-2 py-1 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                            />
                            <input
                              value={draft.soft_cap_gb}
                              onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, soft_cap_gb: event.target.value } }))}
                              placeholder="soft cap GB"
                              className="rounded-lg border border-violet-200/50 bg-white px-2 py-1 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                            />
                            <input
                              value={draft.hard_cap_gb}
                              onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, hard_cap_gb: event.target.value } }))}
                              placeholder="hard cap GB"
                              className="rounded-lg border border-violet-200/50 bg-white px-2 py-1 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                            />
                          </div>
                          <div className="mt-2 flex flex-wrap items-center gap-3">
                            <label className="inline-flex items-center gap-1 text-[11px]">
                              <input type="checkbox" checked={draft.notify_soft} onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, notify_soft: event.target.checked } }))} />
                              notify soft
                            </label>
                            <label className="inline-flex items-center gap-1 text-[11px]">
                              <input type="checkbox" checked={draft.notify_hard} onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, notify_hard: event.target.checked } }))} />
                              notify hard
                            </label>
                            <label className="inline-flex items-center gap-1 text-[11px]">
                              <input type="checkbox" checked={draft.auto_disable_on_hard} onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, auto_disable_on_hard: event.target.checked } }))} />
                              auto disable
                            </label>
                            <label className="inline-flex items-center gap-1 text-[11px]">
                              <input type="checkbox" checked={draft.apply_now} onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, apply_now: event.target.checked } }))} />
                              apply now
                            </label>
                            <button className="outline-btn rounded-lg px-2 py-1 text-[11px] font-semibold" type="button" onClick={() => void savePolicy(key.node_code)} disabled={policyBusy === key.node_code}>
                              {policyBusy === key.node_code ? "Saving..." : "Сохранить лимиты"}
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : null}

            {detailTab === "history" ? (
              <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <p className="font-semibold">История ключей (регены / блокировки / переносы)</p>
                  <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={() => void reloadSelected()} disabled={busy}>
                    Обновить
                  </button>
                </div>
                <div className="max-h-[44vh] overflow-auto">
                  <table className="min-w-full text-xs">
                    <thead>
                      <tr className="text-left text-slate-500">
                        <th className="px-2 py-2">Дата</th>
                        <th className="px-2 py-2">Action</th>
                        <th className="px-2 py-2">Node</th>
                        <th className="px-2 py-2">Actor</th>
                        <th className="px-2 py-2">Meta</th>
                      </tr>
                    </thead>
                    <tbody>
                      {keyHistoryRows.map((row) => (
                        <tr key={row.id} className="border-t border-white/30 dark:border-white/10">
                          <td className="px-2 py-2 whitespace-nowrap">{fmtRuDate(row.created_at)}</td>
                          <td className="px-2 py-2"><span className={`badge ${historyBadgeClass(row.action)}`}>{row.action}</span></td>
                          <td className="px-2 py-2">{row.node_code || "—"}</td>
                          <td className="px-2 py-2">{row.actor_tg_id || "—"}</td>
                          <td className="px-2 py-2 max-w-[260px] truncate">{row.meta ? JSON.stringify(row.meta) : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {!keyHistoryRows.length ? <p className="px-2 py-3 text-xs text-slate-500">История пуста.</p> : null}
                </div>
              </div>
            ) : null}

            {detailTab === "audit" ? (
              <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <p className="font-semibold">Журнал действий админа</p>
                  <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={() => void reloadSelected()} disabled={busy}>
                    Обновить
                  </button>
                </div>
                <div className="max-h-[44vh] overflow-auto">
                  <table className="min-w-full text-xs">
                    <thead>
                      <tr className="text-left text-slate-500">
                        <th className="px-2 py-2">Дата</th>
                        <th className="px-2 py-2">Actor</th>
                        <th className="px-2 py-2">Action</th>
                        <th className="px-2 py-2">Meta</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditRows.map((row) => (
                        <tr key={row.id} className="border-t border-white/30 dark:border-white/10">
                          <td className="px-2 py-2 whitespace-nowrap">{fmtRuDate(row.created_at)}</td>
                          <td className="px-2 py-2">{row.actor_tg_id}</td>
                          <td className="px-2 py-2"><span className="badge badge-violet">{row.action}</span></td>
                          <td className="px-2 py-2 max-w-[280px] truncate">{row.meta ? JSON.stringify(row.meta) : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {!auditRows.length ? <p className="px-2 py-3 text-xs text-slate-500">Действий пока нет.</p> : null}
                </div>
              </div>
            ) : null}
          </>
        )}
      </article>
    </section>
  );
}
