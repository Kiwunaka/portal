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
  if (value === true) return "������";
  if (value === false) return "������";
  return "����������";
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

function actionLabel(action: string): string {
  const value = String(action || "").toLowerCase();
  if (!value) return "�";
  if (value.includes("regen") || value.includes("rotate")) return "������� �����";
  if (value.includes("reset")) return "����� �������";
  if (value.includes("resync")) return "������������� ID ��������";
  if (value.includes("move") || value.includes("node")) return "������� ����� ������";
  if (value.includes("disable") || value.includes("block")) return "����������/����������";
  if (value.includes("enable") || value.includes("unblock")) return "���������/�������������";
  if (value.includes("create")) return "��������";
  if (value.includes("delete") || value.includes("remove")) return "��������";
  if (value.includes("extend")) return "���������";
  return action;
}

function riskLevelLabel(level: string): string {
  const value = String(level || "").toLowerCase();
  if (["low", "������"].includes(value)) return "������";
  if (["medium", "med", "�������"].includes(value)) return "�������";
  if (["high", "�������"].includes(value)) return "�������";
  if (["critical", "crit", "�����������"].includes(value)) return "�����������";
  return value || "������";
}

function panelStateLabel(state: string): string {
  const value = String(state || "").toLowerCase();
  if (["ok", "healthy", "fresh"].includes(value)) return "�����";
  if (["degraded", "stale", "warn", "warning"].includes(value)) return "��������������";
  if (["error", "down", "offline", "fail"].includes(value)) return "������";
  return value || "����������";
}

function ticketStatusLabel(status: string): string {
  const value = String(status || "").toLowerCase().replace(/\s+/g, "_");
  if (value === "open") return "������";
  if (value === "in_progress") return "� ������";
  if (value === "closed") return "������";
  return status || "�";
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

type AdminActionDialog =
  | { kind: "message"; text: string }
  | { kind: "extend"; days: string }
  | { kind: "create"; displayName: string; days: string }
  | { kind: "bulkConfirm" }
  | { kind: "token"; subscriptionUrl: string; syncOk: boolean }
  | null;

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
  const [dialog, setDialog] = useState<AdminActionDialog>(null);
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
      setError(String((err as { message?: string })?.message || err || "    "));
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
      setError(String((err as { message?: string })?.message || err || "    "));
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
      setOkMessage("����������� � �����.");
    } catch {
      setError("�� ������� ����������� ������ ��� ����.");
    }
  };

  const actionMessage = async (): Promise<void> => {
    if (!selectedTgId) return;
    setDialog({ kind: "message", text: "" });
  };

  const submitMessageDialog = async (): Promise<void> => {
    if (!selectedTgId || !dialog || dialog.kind !== "message" || !dialog.text.trim()) return;
    setBusy(true);
    try {
      await adminUserMessage(selectedTgId, dialog.text.trim());
      setOkMessage("��������� ����������.");
      setDialog(null);
      await reloadSelected();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "   "));
    } finally {
      setBusy(false);
    }
  };

  const actionExtend = async (): Promise<void> => {
    if (!selectedTgId) return;
    setDialog({ kind: "extend", days: "30" });
  };

  const submitExtendDialog = async (): Promise<void> => {
    if (!selectedTgId || !dialog || dialog.kind !== "extend") return;
    const days = Number(dialog.days || 0);
    if (!Number.isFinite(days) || days === 0) {
      setError("������� ���������� ���������� ����.");
      return;
    }
    setBusy(true);
    try {
      await adminManualExtend(selectedTgId, days);
      setOkMessage(`�������� �������� �� ${days} ��.`);
      setDialog(null);
      await reloadSelected();
      await loadUsers();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "   "));
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
      setOkMessage(blocked ? " ." : " .");
      await reloadSelected();
      await loadUsers();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "    "));
    } finally {
      setBusy(false);
    }
  };

  const actionRegenerateToken = async (): Promise<void> => {
    if (!selectedTgId) return;
    setBusy(true);
    try {
      const out = await adminManualRegenerateToken(selectedTgId);
      setOkMessage(`   (${out.sync_ok ? " " : "  "}).`);
      setDialog({ kind: "token", subscriptionUrl: out.subscription_url, syncOk: Boolean(out.sync_ok) });
      await reloadSelected();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "   "));
    } finally {
      setBusy(false);
    }
  };

  const actionCreateManual = async (): Promise<void> => {
    setDialog({ kind: "create", displayName: "������� ������������", days: "30" });
  };

  const submitCreateManualDialog = async (): Promise<void> => {
    if (!dialog || dialog.kind !== "create") return;
    const displayName = dialog.displayName.trim();
    const days = Number(dialog.days || 0);
    if (!displayName || !Number.isFinite(days) || days <= 0) {
      setError("��������� ��� � ���� ������� ��� ������� ������������.");
      return;
    }
    setBusy(true);
    try {
      await adminManualCreate({ display_name: displayName, days });
      setOkMessage("������ ������������ ������.");
      setDialog(null);
      await loadUsers();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "    "));
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
      setOkMessage(`�������� ${action} ��������� ��� ${key.node_code}.`);
      await reloadSelected();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "     "));
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
      setOkMessage(`�������� ${result.preset} ��������.`);
      await reloadSelected();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "    "));
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
      setOkMessage(`������ ��� ${nodeCode} ���������.`);
      await reloadSelected();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "   "));
    } finally {
      setPolicyBusy("");
    }
  };

  const runBulkAction = async (confirmed = false): Promise<void> => {
    setBusy(true);
    setError("");
    setBulkResult("");
    setOkMessage("");
    try {
      if (!bulkAction.dryRun && !confirmed) {
        setBusy(false);
        setDialog({ kind: "bulkConfirm" });
        return;
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
      const mode = out?.dry_run ? "" : "";
      setBulkResult(`�������� �������� (${mode}): ���������� ${affected}, ������ ${failed}`);
      if (!out?.dry_run) {
        setDialog(null);
      }
      if (!bulkAction.dryRun) {
        await loadUsers();
      }
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "    "));
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
      setOkMessage(`   ${out.tier_days}   (${out.sync_ok ? " " : "  "}).`);
      await reloadSelected();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "    "));
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
            placeholder="����� �� username, Telegram ID ��� ����� �����"
            className="flex-1 rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          />
          <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void loadUsers()}>
            �����
          </button>
          <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void actionCreateManual()} disabled={busy}>
            + ������ ������������
          </button>
        </div>

        <div className="mb-3 rounded-xl border border-violet-200/40 bg-white/70 p-3 dark:border-violet-500/20 dark:bg-white/5">
          <p className="mb-1 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">�������� �������� �� ������</p>
          <p className="mb-2 text-xs text-slate-500">
            ����������� ���� ����, ���� ����� ����� ���������� ������ �������������. ������� ����� ��������� ������������, � ��� ����� ��������� ���������.
          </p>
          <div className="grid gap-2 sm:grid-cols-2">
            <select
              value={bulkAction.action}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, action: event.target.value as "disable" | "enable" | "reset" | "resync" }))}
              className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            >
              <option value="disable">��������� �����</option>
              <option value="enable">�������� �����</option>
              <option value="reset">�������� ������</option>
              <option value="resync">�������������������� subId</option>
            </select>
            <select
              value={bulkAction.segment}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, segment: event.target.value }))}
              className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            >
              <option value="all">�������: ���</option>
              <option value="paid">�������: �������</option>
              <option value="free">�������: ����������</option>
              <option value="manual">�������: ������</option>
              <option value="active">�������: ��������</option>
              <option value="inactive">�������: ����������</option>
            </select>
            <input
              value={bulkAction.q}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, q: event.target.value }))}
              placeholder="�������������� ������: username ��� Telegram ID"
              className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            />
            <input
              value={bulkAction.nodeCodes}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, nodeCodes: event.target.value }))}
              placeholder="���� ����� ������� (���.)"
              className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            />
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <label className="text-xs text-slate-600 dark:text-slate-300">
              �����:
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
              ������������
            </label>
            <label className="inline-flex items-center gap-1 text-xs text-slate-600 dark:text-slate-300">
              <input type="checkbox" checked={bulkAction.force} onChange={(event) => setBulkAction((prev) => ({ ...prev, force: event.target.checked }))} />
              �������������
            </label>
              <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={() => void runBulkAction()} disabled={busy}>
                ��������� ��������
              </button>
          </div>
          {bulkResult ? <p className="mt-2 text-xs text-emerald-500">{bulkResult}</p> : null}
        </div>

        {loading ? <p className="text-sm text-slate-500"> ...</p> : null}
        {error ? <p className="mb-2 text-sm text-rose-500">{error}</p> : null}
        {okMessage ? <p className="mb-2 text-sm text-emerald-500">{okMessage}</p> : null}

        <div className="max-h-[58vh] overflow-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="px-2 py-2">ID</th>
                <th className="px-2 py-2">������������</th>
                <th className="px-2 py-2">����</th>
                <th className="px-2 py-2">������</th>
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
                  <td className="px-2 py-2">{row.display_name || row.username || "�"}</td>
                  <td className="px-2 py-2">{row.sub_type || "�"}</td>
                  <td className="px-2 py-2">
                    <span className={`rounded-full px-2 py-1 text-xs ${row.is_active ? "bg-emerald-500/20 text-emerald-600" : "bg-rose-500/20 text-rose-500"}`}>
                      {row.is_active ? "" : ""}
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
          <p className="text-sm text-slate-500">�������� ������������ �����.</p>
        ) : (
          <>
            <div className="mb-3">
              <h2 className="font-display text-2xl font-semibold">�������� #{selected.user.tg_id}</h2>
              <p className="text-xs text-slate-500">������: {fmtRuDate(selected.user.created_at)}</p>
              <p className="text-xs text-slate-500">��������: {fmtRuDate(selected.user.expiry_at)}</p>
            </div>

            <div className="mb-3 grid gap-2 sm:grid-cols-2">
              <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void actionMessage()} disabled={busy}>
                ���������
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void actionExtend()} disabled={busy}>
                ��������
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void actionRegenerateToken()} disabled={busy}>
                ����� �����
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void actionToggleBlock()} disabled={busy}>
                {selected.user.is_active ? "" : ""}
              </button>
            </div>

            <div className="mb-3 grid gap-2 sm:grid-cols-2">
              <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void runPreset("reset_key")} disabled={busy}>
                ��������: ����� �����
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void runPreset("rotate_link")} disabled={busy}>
                ��������: ������� ������
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void runPreset("extend_1d")} disabled={busy}>
                ��������: +1 ����
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void runPreset("send_guide")} disabled={busy}>
                ��������: ��������� ����������
              </button>
            </div>

            <div className="mb-3 grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                <p>����: <strong>{selected.user.sub_type}</strong></p>
                <p>�������� �������� �������: <strong>{selected.user.stars_paid}</strong></p>
                <p>���������: <strong>{selected.user.referral_count}</strong></p>
                <p> : <strong>{loyalty?.streak_days ?? 0} .</strong></p>
              </div>
              <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                <div className="mb-1 flex items-center gap-2">
                  <span className={`badge ${riskClass}`}> {Math.round(risk?.score || 0)}</span>
                  <span className="text-xs text-slate-500">{riskLevelLabel(String(risk?.level || ""))}</span>
                </div>
                <p className="text-xs">: <strong>{risk?.signals?.regen_count ?? 0}</strong></p>
                <p className="text-xs">-  : <strong>{risk?.signals?.admin_key_ops ?? 0}</strong></p>
                <p className="text-xs"> IP: <strong>{risk?.signals?.unique_ips ?? 0}</strong></p>
                <p className="text-xs">: <strong>{Number(risk?.signals?.traffic_gb || 0).toFixed(2)} GB</strong></p>
              </div>
            </div>

            <div className="mt-3 rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
              <p className="mb-1 font-semibold">��������</p>
              <div className="flex items-start gap-2">
                <input
                  value={String(selected.user.subscription_url || "")}
                  readOnly
                  className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                />
                <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void copyText(String(selected.user.subscription_url || ""))}>
                  ���������� URL
                </button>
              </div>
              <div className="mt-2 flex items-start gap-2">
                <input
                  value={String(selected.user.subscription_token || "")}
                  readOnly
                  className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                />
                <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void copyText(String(selected.user.subscription_token || ""))}>
                  ���������� �����
                </button>
              </div>
            </div>

            {loyalty?.tiers?.length ? (
              <div className="mb-3 rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                <p className="mb-2 font-semibold">������ ���������� (30/90/180)</p>
                <div className="grid gap-2 sm:grid-cols-3">
                  {loyalty.tiers.map((tier) => (
                    <div key={tier.reward_key} className="rounded-xl border border-white/30 bg-white/70 p-2 text-xs dark:border-white/10 dark:bg-white/5">
                      <p className="font-semibold">{tier.days} ��.</p>
                      <p>�����: {tier.bonus_days} ��.</p>
                      <p>����������: {tier.perk}</p>
                      <p className="mt-1">: {tier.claimed ? "" : tier.unlocked ? "" : ""}</p>
                      {!tier.claimed && tier.unlocked ? (
                        <button className="mt-2 outline-btn rounded-lg px-2 py-1 text-[11px] font-semibold" type="button" disabled={busy} onClick={() => void grantLoyaltyTier(tier.days)}>
                          ������ �������
                        </button>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="mb-3 flex flex-wrap gap-2">
              <button className={tabButtonClass("overview")} type="button" onClick={() => setDetailTab("overview")}>�����</button>
              <button className={tabButtonClass("keys")} type="button" onClick={() => setDetailTab("keys")}>����� � ������</button>
              <button className={tabButtonClass("history")} type="button" onClick={() => setDetailTab("history")}>������� ���������</button>
              <button className={tabButtonClass("audit")} type="button" onClick={() => setDetailTab("audit")}>�������� ������</button>
            </div>

            {detailTab === "overview" ? (
              <>
                <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                  <p className="mb-2 font-semibold">������ ������</p>
                  <p className="mb-2 text-xs text-slate-500">
                    ����� �����, �� �������� ����� � ������������ ���� ����, ������� ������� ��� ������ � ���� �� ���������� ����� POKROV � �������.
                  </p>
                  {summary ? (
                    <div className="grid gap-2 text-xs sm:grid-cols-2">
                      <p>��� � ������: <strong>{summary.nodes_with_client}/{summary.nodes_total}</strong></p>
                      <p>������ ���: <strong>{summary.nodes_online}</strong></p>
                      <p>���������� ���: <strong>{summary.nodes_enabled}</strong></p>
                      <p>����������� �� ID ��������: <strong>{summary.subid_mismatch_count}</strong></p>
                      <p>������ �����: <strong>{fmtTraffic(summary.traffic_total_bytes)}</strong></p>
                      <p>��������� ������: <strong>{panelStateLabel(String(summary.panel_state || ""))}</strong></p>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500">������ ����������.</p>
                  )}
                </div>
                <h3 className="mt-4 font-display text-xl font-semibold">��������� ������</h3>
                <div className="mt-2 space-y-2">
                  {(selected.tickets || []).map((ticket) => (
                    <div key={ticket.id} className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                      <p className="font-medium">#{ticket.id} � {ticketStatusLabel(ticket.status_title)}</p>
                      <p className="text-xs text-slate-500">{ticket.last_message_preview || "��� ���������"}</p>
                    </div>
                  ))}
                  {!selected.tickets?.length ? <p className="text-xs text-slate-500"> .</p> : null}
                </div>
              </>
            ) : null}

            {detailTab === "keys" ? (
              <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <p className="font-semibold">�����, ������ � ����������</p>
                  <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={() => void reloadSelected()} disabled={busy || !!keyBusy || !!policyBusy}>
                    ��������
                  </button>
                </div>
                <p className="mb-3 text-xs text-slate-500">
                  � ���� ������� ����� �������� � ��������� �����, ���������� ������, �������������������� ������ � ���������� ������ �� ������ ���� ��������.
                </p>
                <div className="space-y-2">
                  {keys.length === 0 ? <p className="text-xs text-slate-500">     .</p> : null}
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
                          <p className="font-semibold">{key.node_code} � {key.node_name || "����"}</p>
                          <span className={`rounded-full px-2 py-0.5 ${key.exists ? "bg-emerald-500/20 text-emerald-600" : "bg-slate-300/40 text-slate-500"}`}>
                            {key.exists ? " " : " "}
                          </span>
                        </div>
                        <p className="mt-1">: <strong>{fmtOnline(key.online)}</strong>  : <strong>{key.enabled ? "" : ""}</strong></p>
                        <p>ID �������� � ������: <strong>{key.sub_id || "�"}</strong></p>
                        <p> ID: <strong>{key.expected_sub_id || ""}</strong>  : <strong>{key.sub_id_match ? "" : ""}</strong></p>
                        <p>������: <strong>{fmtTraffic(key.total_bytes)}</strong> ({key.up_bytes}^ / {key.down_bytes}v)</p>
                        <p>��������� ������: <strong>{fmtRuDate(key.last_online_at)}</strong></p>

                        <div className="mt-2 flex flex-wrap gap-2">
                          <button className="outline-btn rounded-xl px-2.5 py-1 text-[11px] font-semibold" type="button" disabled={busy || !key.exists || !!keyBusy} onClick={() => void runKeyAction(key, "toggle")}>
                            {busyToggle ? "..." : key.enabled ? "" : ""}
                          </button>
                          <button className="outline-btn rounded-xl px-2.5 py-1 text-[11px] font-semibold" type="button" disabled={busy || !key.exists || !!keyBusy} onClick={() => void runKeyAction(key, "reset")}>
                            {busyReset ? "..." : " "}
                          </button>
                          <button className="outline-btn rounded-xl px-2.5 py-1 text-[11px] font-semibold" type="button" disabled={busy || !key.exists || !!keyBusy} onClick={() => void runKeyAction(key, "resync")}>
                            {busyResync ? "..." : " ID "}
                          </button>
                          <button className="outline-btn rounded-xl px-2.5 py-1 text-[11px] font-semibold" type="button" disabled={!String(key.vless_link || "").trim()} onClick={() => void copyText(String(key.vless_link || ""))}>
                            ���������� ����
                          </button>
                        </div>

                        <div className="mt-3 rounded-xl border border-violet-200/40 bg-white/80 p-2 dark:border-violet-500/20 dark:bg-slate-900/60">
                          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">������ �� ���� � ���������������</p>
                          <div className="grid gap-2 sm:grid-cols-3">
                            <input
                              value={draft.burst_mbps}
                              onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, burst_mbps: event.target.value } }))}
                              placeholder="������� �������� (Mbps)"
                              className="rounded-lg border border-violet-200/50 bg-white px-2 py-1 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                            />
                            <input
                              value={draft.soft_cap_gb}
                              onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, soft_cap_gb: event.target.value } }))}
                              placeholder="soft-����� (GB)"
                              className="rounded-lg border border-violet-200/50 bg-white px-2 py-1 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                            />
                            <input
                              value={draft.hard_cap_gb}
                              onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, hard_cap_gb: event.target.value } }))}
                              placeholder="hard-����� (GB)"
                              className="rounded-lg border border-violet-200/50 bg-white px-2 py-1 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                            />
                          </div>
                          <div className="mt-2 flex flex-wrap items-center gap-3">
                            <label className="inline-flex items-center gap-1 text-[11px]">
                              <input type="checkbox" checked={draft.notify_soft} onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, notify_soft: event.target.checked } }))} />
                              ���������� � soft-������
                            </label>
                            <label className="inline-flex items-center gap-1 text-[11px]">
                              <input type="checkbox" checked={draft.notify_hard} onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, notify_hard: event.target.checked } }))} />
                              ���������� � hard-������
                            </label>
                            <label className="inline-flex items-center gap-1 text-[11px]">
                              <input type="checkbox" checked={draft.auto_disable_on_hard} onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, auto_disable_on_hard: event.target.checked } }))} />
                              �������������� ��� hard-������
                            </label>
                            <label className="inline-flex items-center gap-1 text-[11px]">
                              <input type="checkbox" checked={draft.apply_now} onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, apply_now: event.target.checked } }))} />
                              ��������� �����
                            </label>
                            <button className="outline-btn rounded-lg px-2 py-1 text-[11px] font-semibold" type="button" onClick={() => void savePolicy(key.node_code)} disabled={policyBusy === key.node_code}>
                              {policyBusy === key.node_code ? "..." : " "}
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
                  <p className="font-semibold">������� ������ (������ / ���������� / ��������)</p>
                  <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={() => void reloadSelected()} disabled={busy}>
                    ��������
                  </button>
                </div>
                <p className="mb-3 text-xs text-slate-500">
                  ������ �������� ������, ��� ������ ����������� � ������� ������������: ���������, �������, ��������, ���������� � ������ ��������.
                </p>
                <div className="max-h-[44vh] overflow-auto">
                  <table className="min-w-full text-xs">
                    <thead>
                      <tr className="text-left text-slate-500">
                        <th className="px-2 py-2">����</th>
                        <th className="px-2 py-2">��������</th>
                        <th className="px-2 py-2">����</th>
                        <th className="px-2 py-2">��������</th>
                        <th className="px-2 py-2">����������</th>
                      </tr>
                    </thead>
                    <tbody>
                      {keyHistoryRows.map((row) => (
                        <tr key={row.id} className="border-t border-white/30 dark:border-white/10">
                          <td className="px-2 py-2 whitespace-nowrap">{fmtRuDate(row.created_at)}</td>
                          <td className="px-2 py-2"><span className={`badge ${historyBadgeClass(row.action)}`}>{actionLabel(row.action)}</span></td>
                          <td className="px-2 py-2">{row.node_code || "�"}</td>
                          <td className="px-2 py-2">{row.actor_tg_id || "�"}</td>
                          <td className="px-2 py-2 max-w-[260px] truncate">{row.meta ? JSON.stringify(row.meta) : ""}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {!keyHistoryRows.length ? <p className="px-2 py-3 text-xs text-slate-500"> .</p> : null}
                </div>
              </div>
            ) : null}

            {detailTab === "audit" ? (
              <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <p className="font-semibold">������ �������� ������</p>
                  <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={() => void reloadSelected()} disabled={busy}>
                    ��������
                  </button>
                </div>
                <p className="mb-3 text-xs text-slate-500">
                  ����� �����, ��� �� ���������� ��� ����� � �������� ������������ � ����� ��� ���������.
                </p>
                <div className="max-h-[44vh] overflow-auto">
                  <table className="min-w-full text-xs">
                    <thead>
                      <tr className="text-left text-slate-500">
                        <th className="px-2 py-2">����</th>
                        <th className="px-2 py-2">��������</th>
                        <th className="px-2 py-2">��������</th>
                        <th className="px-2 py-2">����������</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditRows.map((row) => (
                        <tr key={row.id} className="border-t border-white/30 dark:border-white/10">
                          <td className="px-2 py-2 whitespace-nowrap">{fmtRuDate(row.created_at)}</td>
                          <td className="px-2 py-2">{row.actor_tg_id}</td>
                          <td className="px-2 py-2"><span className="badge badge-violet">{actionLabel(row.action)}</span></td>
                          <td className="px-2 py-2 max-w-[280px] truncate">{row.meta ? JSON.stringify(row.meta) : ""}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {!auditRows.length ? <p className="px-2 py-3 text-xs text-slate-500">  .</p> : null}
                </div>
              </div>
            ) : null}
          </>
        )}
      </article>

      {dialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/65 p-4">
          <div className="glass-card w-full max-w-lg p-5">
            {dialog.kind === "message" ? (
              <>
                <h3 className="font-display text-xl font-semibold">��������� ������������</h3>
                <p className="mt-1 text-xs text-slate-500">��������� ���� ����� � Telegram.</p>
                <textarea
                  value={dialog.text}
                  onChange={(event) => setDialog({ kind: "message", text: event.target.value })}
                  rows={5}
                  className="mt-4 w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                  placeholder="����� ���������"
                />
                <div className="mt-4 flex justify-end gap-2">
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setDialog(null)}>
                    ������
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy || !dialog.text.trim()} onClick={() => void submitMessageDialog()}>
                    ���������
                  </button>
                </div>
              </>
            ) : null}

            {dialog.kind === "extend" ? (
              <>
                <h3 className="font-display text-xl font-semibold">�������� ������</h3>
                <p className="mt-1 text-xs text-slate-500">��������� ����� ���� � ������� � ����� ������������.</p>
                <input
                  value={dialog.days}
                  onChange={(event) => setDialog({ kind: "extend", days: event.target.value })}
                  type="number"
                  min={1}
                  className="mt-4 w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                  placeholder="����"
                />
                <div className="mt-4 flex justify-end gap-2">
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setDialog(null)}>
                    ������
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void submitExtendDialog()}>
                    ���������
                  </button>
                </div>
              </>
            ) : null}

            {dialog.kind === "create" ? (
              <>
                <h3 className="font-display text-xl font-semibold">������ ������������</h3>
                <p className="mt-1 text-xs text-slate-500">��� ������-������ � ������������� ������.</p>
                <input
                  value={dialog.displayName}
                  onChange={(event) => setDialog({ kind: "create", displayName: event.target.value, days: dialog.days })}
                  className="mt-4 w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                  placeholder="��� ������������"
                />
                <input
                  value={dialog.days}
                  onChange={(event) => setDialog({ kind: "create", displayName: dialog.displayName, days: event.target.value })}
                  type="number"
                  min={1}
                  className="mt-3 w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                  placeholder="���� ������� � ����"
                />
                <div className="mt-4 flex justify-end gap-2">
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setDialog(null)}>
                    ������
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void submitCreateManualDialog()}>
                    �������
                  </button>
                </div>
              </>
            ) : null}

            {dialog.kind === "bulkConfirm" ? (
              <>
                <h3 className="font-display text-xl font-semibold">����������� �������� ��������</h3>
                <p className="mt-2 text-sm text-slate-500">
                  ����� ��������� �������� <strong>{bulkAction.action}</strong> ��� �������� <strong>{bulkAction.segment}</strong>.
                </p>
                <p className="mt-2 text-xs text-slate-500">
                  ������: {bulkAction.q.trim() || "��� �������"} � �����: {bulkAction.limit} � ����: {bulkAction.nodeCodes.trim() || "���"}
                </p>
                <div className="mt-4 flex justify-end gap-2">
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setDialog(null)}>
                    ������
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void runBulkAction(true)}>
                    ���������
                  </button>
                </div>
              </>
            ) : null}

            {dialog.kind === "token" ? (
              <>
                <h3 className="font-display text-xl font-semibold">����� ������ ������</h3>
                <p className="mt-1 text-xs text-slate-500">
                   : {dialog.syncOk ? " " : "  "}.
                </p>
                <input
                  value={dialog.subscriptionUrl}
                  readOnly
                  className="mt-4 w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-3 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                />
                <div className="mt-4 flex justify-end gap-2">
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void copyText(dialog.subscriptionUrl)}>
                    ����������
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setDialog(null)}>
                    �������
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

