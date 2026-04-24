"use client";

import {
  adminBulkKeyAction,
  adminDeleteTestUser,
  adminManualBlock,
  adminManualCreate,
  adminManualExtend,
  adminManualRegenerateToken,
  adminUserCard,
  adminUserKeyLimitUpdate,
  adminUserKeyResetTraffic,
  adminUserKeyResyncSubId,
  adminUserKeyToggle,
  adminUserLoyaltyGrant,
  adminUserMessage,
  adminUserPresetRun,
  adminUsers,
  type AdminUserCard,
  type AdminUserKey,
  type AdminUserRow,
} from "@/lib/api";
import { adminButtonClass, adminFieldClass, adminPanelClass, adminTextAreaClass } from "@/components/admin/admin-shell";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AdminUsersQueryPanel } from "@/components/admin/users/admin-users-query-panel";
import { AdminUsersResultsTable } from "@/components/admin/users/admin-users-results-table";
import { AdminUserSidePanel } from "@/components/admin/users/admin-user-side-panel";
import {
  ADMIN_USERS_PAGE_SIZE,
  createDefaultBulkActionState,
  readAdminUsersQueryState,
  serializeAdminUsersQueryState,
  type AdminUsersBulkActionState,
  type AdminUsersQueryState,
} from "@/components/admin/users/admin-users-query-state";
import { emptyPolicyDraft, isManualTestUserLike, parseNullableNumber, type KeyPolicyDraft } from "@/components/admin/users/admin-users-format";

type DetailTab = "overview" | "keys" | "history" | "audit";

type AdminActionDialog =
  | { kind: "message"; text: string }
  | { kind: "extend"; days: string; reason: string }
  | { kind: "create"; displayName: string; days: string; reason: string }
  | { kind: "deleteConfirm"; tgId: number; displayName: string; reason: string }
  | { kind: "bulkConfirm"; reason: string }
  | { kind: "token"; subscriptionUrl: string; syncOk: boolean }
  | null;

function errorMessage(err: unknown, fallback: string): string {
  return String((err as { message?: string })?.message || err || fallback);
}

export default function AdminUsersPage() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryState = useMemo(() => readAdminUsersQueryState(searchParams), [searchParams]);

  const [rows, setRows] = useState<AdminUserRow[]>([]);
  const [totalRows, setTotalRows] = useState(0);
  const [selected, setSelected] = useState<AdminUserCard | null>(null);
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
  const [bulkAction, setBulkAction] = useState<AdminUsersBulkActionState>(createDefaultBulkActionState());
  const selectedIdRef = useRef<number>(0);

  const syncQueryState = useCallback(
    (next: AdminUsersQueryState) => {
      const nextQuery = serializeAdminUsersQueryState(next);
      router.replace(nextQuery ? `${pathname}?${nextQuery}` : pathname, { scroll: false });
    },
    [pathname, router],
  );

  const updateFilters = useCallback(
    (patch: Partial<Omit<AdminUsersQueryState, "page">>) => {
      syncQueryState({ ...queryState, ...patch, page: 1 });
    },
    [queryState, syncQueryState],
  );

  const updatePage = useCallback(
    (page: number) => syncQueryState({ ...queryState, page: Math.max(1, page) }),
    [queryState, syncQueryState],
  );

  const loadCardDetails = useCallback(async (tgId: number): Promise<void> => {
    const card = await adminUserCard(tgId);
    setSelected(card);
  }, []);

  const loadUsers = useCallback(
    async (options?: { preserveNotice?: boolean }): Promise<void> => {
      setLoading(true);
      setError("");
      if (!options?.preserveNotice) setOkMessage("");

      try {
        const result = await adminUsers({
          q: queryState.q.trim() || undefined,
          status: queryState.status !== "all" ? queryState.status : undefined,
          origin: queryState.origin !== "all" ? queryState.origin : undefined,
          observer_state: queryState.observerState !== "all" ? queryState.observerState : undefined,
          sort: queryState.sort,
          page: queryState.page,
          page_size: ADMIN_USERS_PAGE_SIZE,
        });

        setRows(result.users);
        setTotalRows(result.total);

        if (!result.users.length) {
          setSelected(null);
        } else {
          const nextId =
            selectedIdRef.current && result.users.some((item) => item.tg_id === selectedIdRef.current)
              ? selectedIdRef.current
              : result.users[0]?.tg_id;
          if (nextId) await loadCardDetails(nextId);
        }
      } catch (err) {
        setError(errorMessage(err, "Could not load users."));
      } finally {
        setLoading(false);
      }
    },
    [loadCardDetails, queryState],
  );

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  useEffect(() => {
    selectedIdRef.current = Number(selected?.user.tg_id || 0);
  }, [selected?.user.tg_id]);

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

  const selectedTgId = Number(selected?.user.tg_id || 0);
  const selectedCanDelete = isManualTestUserLike(selected?.user);
  const totalPages = Math.max(1, Math.ceil(totalRows / ADMIN_USERS_PAGE_SIZE));
  const pageStart = rows.length ? (queryState.page - 1) * ADMIN_USERS_PAGE_SIZE + 1 : 0;
  const pageEnd = rows.length ? pageStart + rows.length - 1 : 0;

  const reloadSelected = useCallback(async (): Promise<void> => {
    if (selectedTgId) await loadCardDetails(selectedTgId);
  }, [loadCardDetails, selectedTgId]);

  const copyText = useCallback(async (text: string): Promise<void> => {
    if (!text.trim()) return;
    try {
      await navigator.clipboard.writeText(text.trim());
      setOkMessage("Copied to clipboard.");
    } catch {
      setError("Clipboard copy failed.");
    }
  }, []);

  const actionMessage = useCallback(() => selectedTgId && setDialog({ kind: "message", text: "" }), [selectedTgId]);
  const actionExtend = useCallback(() => selectedTgId && setDialog({ kind: "extend", days: "30", reason: "" }), [selectedTgId]);
  const actionCreateManual = useCallback(() => setDialog({ kind: "create", displayName: "Manual test account", days: "30", reason: "" }), []);

  const submitMessageDialog = useCallback(async (): Promise<void> => {
    if (!selectedTgId || !dialog || dialog.kind !== "message" || !dialog.text.trim()) return;
    setBusy(true);
    try {
      await adminUserMessage(selectedTgId, dialog.text.trim());
      setOkMessage("Message sent.");
      setDialog(null);
      await reloadSelected();
    } catch (err) {
      setError(errorMessage(err, "Could not send message."));
    } finally {
      setBusy(false);
    }
  }, [dialog, reloadSelected, selectedTgId]);

  const submitExtendDialog = useCallback(async (): Promise<void> => {
    if (!selectedTgId || !dialog || dialog.kind !== "extend") return;
    const days = Number(dialog.days || 0);
    if (!Number.isFinite(days) || days === 0) {
      setError("Enter a valid number of days.");
      return;
    }
    setBusy(true);
    try {
      await adminManualExtend(selectedTgId, days);
      setOkMessage(`Access extended by ${days} days.`);
      setDialog(null);
      await reloadSelected();
      await loadUsers({ preserveNotice: true });
    } catch (err) {
      setError(errorMessage(err, "Could not extend access."));
    } finally {
      setBusy(false);
    }
  }, [dialog, loadUsers, reloadSelected, selectedTgId]);

  const actionToggleBlock = useCallback(async (): Promise<void> => {
    if (!selectedTgId) return;
    const blocked = Boolean(selected?.user.is_active);
    setBusy(true);
    try {
      await adminManualBlock(selectedTgId, blocked);
      setOkMessage(blocked ? "User blocked." : "User unblocked.");
      await reloadSelected();
      await loadUsers({ preserveNotice: true });
    } catch (err) {
      setError(errorMessage(err, "Could not change block state."));
    } finally {
      setBusy(false);
    }
  }, [loadUsers, reloadSelected, selected?.user.is_active, selectedTgId]);

  const actionRegenerateToken = useCallback(async (): Promise<void> => {
    if (!selectedTgId) return;
    setBusy(true);
    try {
      const out = await adminManualRegenerateToken(selectedTgId);
      setOkMessage(`Token rotated (${out.sync_ok ? "panel synced" : "panel sync pending"}).`);
      setDialog({ kind: "token", subscriptionUrl: out.subscription_url, syncOk: Boolean(out.sync_ok) });
      await reloadSelected();
    } catch (err) {
      setError(errorMessage(err, "Could not rotate token."));
    } finally {
      setBusy(false);
    }
  }, [reloadSelected, selectedTgId]);

  const actionDeleteTestUser = useCallback((): void => {
    if (!selectedTgId || !selectedCanDelete) return;
    const displayName = String(selected?.user.display_name || selected?.user.username || `#${selectedTgId}`);
    setDialog({ kind: "deleteConfirm", tgId: selectedTgId, displayName, reason: "" });
  }, [selected?.user.display_name, selected?.user.username, selectedCanDelete, selectedTgId]);

  const submitDeleteTestUserDialog = useCallback(async (): Promise<void> => {
    if (!dialog || dialog.kind !== "deleteConfirm") return;
    const targetTgId = Number(dialog.tgId || 0);
    if (!targetTgId) {
      setError("Delete target is missing.");
      return;
    }
    setBusy(true);
    try {
      await adminDeleteTestUser(targetTgId);
      setOkMessage("Manual/test пользователь удалён.");
      setDialog(null);
      selectedIdRef.current = 0;
      setSelected(null);
      await loadUsers({ preserveNotice: true });
    } catch (err) {
      setError(errorMessage(err, "Could not delete manual/test user."));
    } finally {
      setBusy(false);
    }
  }, [dialog, loadUsers]);

  const submitCreateManualDialog = useCallback(async (): Promise<void> => {
    if (!dialog || dialog.kind !== "create") return;
    const displayName = dialog.displayName.trim();
    const days = Number(dialog.days || 0);
    if (!displayName || !Number.isFinite(days) || days <= 0 || !dialog.reason.trim()) {
      setError("Enter name, positive days, and an operator reason.");
      return;
    }
    setBusy(true);
    try {
      await adminManualCreate({ display_name: displayName, days });
      setOkMessage("Manual/test user created.");
      setDialog(null);
      await loadUsers({ preserveNotice: true });
    } catch (err) {
      setError(errorMessage(err, "Could not create manual/test user."));
    } finally {
      setBusy(false);
    }
  }, [dialog, loadUsers]);

  const runKeyAction = useCallback(
    async (key: AdminUserKey, action: "toggle" | "reset" | "resync"): Promise<void> => {
      if (!selectedTgId) return;
      const op = `${key.node_code}:${action}`;
      setKeyBusy(op);
      setError("");
      setOkMessage("");
      try {
        if (action === "toggle") await adminUserKeyToggle(selectedTgId, key.node_code, !Boolean(key.enabled));
        else if (action === "reset") await adminUserKeyResetTraffic(selectedTgId, key.node_code);
        else await adminUserKeyResyncSubId(selectedTgId, key.node_code);
        setOkMessage(`Key action ${action} completed for ${key.node_code}.`);
        await reloadSelected();
      } catch (err) {
        setError(errorMessage(err, "Could not run key action."));
      } finally {
        setKeyBusy("");
      }
    },
    [reloadSelected, selectedTgId],
  );

  const runPreset = useCallback(
    async (preset: "reset_key" | "rotate_link" | "extend_1d" | "send_guide"): Promise<void> => {
      if (!selectedTgId) return;
      setBusy(true);
      setError("");
      setOkMessage("");
      try {
        const result = await adminUserPresetRun(selectedTgId, preset);
        setOkMessage(`Preset ${preset} completed (${result.changed ?? 0} changed, ${result.failed ?? 0} failed).`);
        if (result.subscription_url) setDialog({ kind: "token", subscriptionUrl: result.subscription_url, syncOk: true });
        await reloadSelected();
      } catch (err) {
        setError(errorMessage(err, "Could not run preset."));
      } finally {
        setBusy(false);
      }
    },
    [reloadSelected, selectedTgId],
  );

  const savePolicy = useCallback(
    async (nodeCode: string): Promise<void> => {
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
        setOkMessage(`Policy updated for ${nodeCode}.`);
        await reloadSelected();
      } catch (err) {
        setError(errorMessage(err, "Could not save policy."));
      } finally {
        setPolicyBusy("");
      }
    },
    [policyDrafts, reloadSelected, selectedTgId],
  );

  const runBulkAction = useCallback(
    async (confirmed = false): Promise<void> => {
      setError("");
      setOkMessage("");
      if (!bulkAction.dryRun && !confirmed) {
        setDialog({ kind: "bulkConfirm", reason: "" });
        return;
      }
      if (!bulkAction.dryRun && confirmed && dialog?.kind === "bulkConfirm" && !dialog.reason.trim()) {
        setError("Add an operator reason before running a live bulk action.");
        return;
      }
      setBusy(true);
      try {
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
        setDialog(null);
        setBulkResult(`Bulk ${out.action || bulkAction.action}: matched ${out.matched ?? 0}, changed ${out.changed ?? 0}, failed ${out.failed ?? 0}${out.dry_run ? " (dry run)" : ""}.`);
        if (!bulkAction.dryRun) await reloadSelected();
      } catch (err) {
        setError(errorMessage(err, "Could not run bulk action."));
      } finally {
        setBusy(false);
      }
    },
    [bulkAction, dialog, reloadSelected],
  );

  const grantLoyaltyTier = useCallback(
    async (tierDays: number): Promise<void> => {
      if (!selectedTgId) return;
      setBusy(true);
      try {
        const out = await adminUserLoyaltyGrant(selectedTgId, tierDays);
        setOkMessage(`Loyalty reward ${tierDays} days granted${out.sync_ok ? "" : " (panel sync may take time)"}.`);
        await reloadSelected();
      } catch (err) {
        setError(errorMessage(err, "Could not grant loyalty reward."));
      } finally {
        setBusy(false);
      }
    },
    [reloadSelected, selectedTgId],
  );

  const handleSelectUser = useCallback(
    async (tgId: number): Promise<void> => {
      setBusy(true);
      setError("");
      setOkMessage("");
      try {
        await loadCardDetails(tgId);
        setDetailTab("overview");
      } catch (err) {
        setError(errorMessage(err, "Could not open user card."));
      } finally {
        setBusy(false);
      }
    },
    [loadCardDetails],
  );

  return (
    <section className="space-y-4">
      <AdminUsersQueryPanel
        filters={queryState}
        bulkAction={bulkAction}
        busy={busy}
        loading={loading}
        okMessage={okMessage}
        bulkResult={bulkResult}
        pageStart={pageStart}
        pageEnd={pageEnd}
        totalRows={totalRows}
        page={queryState.page}
        totalPages={totalPages}
        onQueryChange={(value) => updateFilters({ q: value })}
        onStatusChange={(value) => updateFilters({ status: value })}
        onOriginChange={(value) => updateFilters({ origin: value })}
        onObserverChange={(value) => updateFilters({ observerState: value })}
        onSortChange={(value) => updateFilters({ sort: value })}
        onRefresh={() => void loadUsers()}
        onCreateManual={actionCreateManual}
        onPrevPage={() => updatePage(Math.max(1, queryState.page - 1))}
        onNextPage={() => updatePage(Math.min(totalPages, queryState.page + 1))}
        onRunBulkAction={() => void runBulkAction()}
        setBulkAction={setBulkAction}
      />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.08fr),minmax(360px,0.92fr)]">
        <AdminUsersResultsTable
          rows={rows}
          loading={loading}
          error={error}
          selectedTgId={selectedTgId}
          page={queryState.page}
          totalPages={totalPages}
          totalRows={totalRows}
          pageStart={pageStart}
          pageEnd={pageEnd}
          onSelect={(tgId) => void handleSelectUser(tgId)}
        />

        <div className="xl:sticky xl:top-4 xl:self-start">
          <AdminUserSidePanel
            selected={selected}
            detailTab={detailTab}
            busy={busy}
            keyBusy={keyBusy}
            policyBusy={policyBusy}
            policyDrafts={policyDrafts}
            selectedCanDelete={selectedCanDelete}
            onReload={() => void reloadSelected()}
            onMessage={actionMessage}
            onExtend={actionExtend}
            onToggleBlock={() => void actionToggleBlock()}
            onRegenerateToken={() => void actionRegenerateToken()}
            onDeleteTestUser={actionDeleteTestUser}
            onRunPreset={(preset) => void runPreset(preset)}
            onGrantLoyalty={(tierDays) => void grantLoyaltyTier(tierDays)}
            onRunKeyAction={(key, action) => void runKeyAction(key, action)}
            onSavePolicy={(nodeCode) => void savePolicy(nodeCode)}
            onCopyText={(text) => void copyText(text)}
            setDetailTab={setDetailTab}
            setPolicyDrafts={setPolicyDrafts}
          />
        </div>
      </div>

      {dialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/70 p-4">
          <div className={`${adminPanelClass("neutral")} max-h-[min(92vh,720px)] w-full max-w-lg overflow-auto`}>
            {dialog.kind === "message" ? (
              <>
                <h3 className="text-xl font-semibold">Message user</h3>
                <p className="mt-1 text-xs text-slate-500">Sends an operator message through the existing Telegram path.</p>
                <textarea value={dialog.text} onChange={(event) => setDialog({ kind: "message", text: event.target.value })} rows={5} className={`mt-4 ${adminTextAreaClass}`} placeholder="Message text" />
                <DialogActions busy={busy} confirmDisabled={!dialog.text.trim()} confirmLabel="Send" onCancel={() => setDialog(null)} onConfirm={() => void submitMessageDialog()} />
              </>
            ) : null}

            {dialog.kind === "extend" ? (
              <>
                <h3 className="text-xl font-semibold">Extend access</h3>
                <p className="mt-1 text-xs text-slate-500">Adds days to the selected subscription. Reason is required for operator discipline; current API stores the access change.</p>
                <input value={dialog.days} onChange={(event) => setDialog({ ...dialog, days: event.target.value })} type="number" min={1} className={`mt-4 ${adminFieldClass}`} placeholder="Days" />
                <input value={dialog.reason} onChange={(event) => setDialog({ ...dialog, reason: event.target.value })} className={`mt-3 ${adminFieldClass}`} placeholder="Operator reason" />
                <DialogActions busy={busy} confirmDisabled={!dialog.reason.trim()} confirmLabel="Apply" onCancel={() => setDialog(null)} onConfirm={() => void submitExtendDialog()} />
              </>
            ) : null}

            {dialog.kind === "create" ? (
              <>
                <h3 className="text-xl font-semibold">Create manual/test user</h3>
                <p className="mt-1 text-xs text-slate-500">Manual accounts are for admin and test scenarios only.</p>
                <input value={dialog.displayName} onChange={(event) => setDialog({ ...dialog, displayName: event.target.value })} className={`mt-4 ${adminFieldClass}`} placeholder="Display name" />
                <input value={dialog.days} onChange={(event) => setDialog({ ...dialog, days: event.target.value })} type="number" min={1} className={`mt-3 ${adminFieldClass}`} placeholder="Access days" />
                <input value={dialog.reason} onChange={(event) => setDialog({ ...dialog, reason: event.target.value })} className={`mt-3 ${adminFieldClass}`} placeholder="Operator reason" />
                <DialogActions busy={busy} confirmDisabled={!dialog.reason.trim()} confirmLabel="Create" onCancel={() => setDialog(null)} onConfirm={() => void submitCreateManualDialog()} />
              </>
            ) : null}

            {dialog.kind === "deleteConfirm" ? (
              <>
                <h3 className="text-xl font-semibold">Удалить manual/test пользователя</h3>
                <p className="mt-2 text-sm text-slate-400">
                  You are deleting <strong>{dialog.displayName}</strong> ({dialog.tgId}). This action is irreversible and available only for explicit manual/test accounts.
                </p>
                <input value={dialog.reason} onChange={(event) => setDialog({ ...dialog, reason: event.target.value })} className={`mt-4 ${adminFieldClass}`} placeholder="Operator reason, optional" />
                <DialogActions busy={busy} confirmLabel="Удалить пользователя" danger onCancel={() => setDialog(null)} onConfirm={() => void submitDeleteTestUserDialog()} />
              </>
            ) : null}

            {dialog.kind === "bulkConfirm" ? (
              <>
                <h3 className="text-xl font-semibold">Confirm live bulk action</h3>
                <p className="mt-2 text-sm text-slate-400">
                  Action <strong>{bulkAction.action}</strong> will run for segment <strong>{bulkAction.segment}</strong>. Dry run is off.
                </p>
                <p className="mt-2 text-xs text-slate-500">
                  Filter: {bulkAction.q.trim() || "none"} | Limit: {bulkAction.limit} | Nodes: {bulkAction.nodeCodes.trim() || "all"}
                </p>
                <input value={dialog.reason} onChange={(event) => setDialog({ ...dialog, reason: event.target.value })} className={`mt-4 ${adminFieldClass}`} placeholder="Operator reason, required" />
                <DialogActions busy={busy} confirmDisabled={!dialog.reason.trim()} confirmLabel="Run live action" danger onCancel={() => setDialog(null)} onConfirm={() => void runBulkAction(true)} />
              </>
            ) : null}

            {dialog.kind === "token" ? (
              <>
                <h3 className="text-xl font-semibold">Новая recovery-ссылка подключения</h3>
                <p className="mt-1 text-xs text-slate-500">Panel sync: {dialog.syncOk ? "ok" : "pending or failed"}.</p>
                <input value={dialog.subscriptionUrl} readOnly className={`mt-4 ${adminFieldClass} text-xs`} />
                <div className="mt-4 flex justify-end gap-2">
                  <button className={adminButtonClass("secondary")} type="button" onClick={() => void copyText(dialog.subscriptionUrl)}>Copy</button>
                  <button className={adminButtonClass("primary")} type="button" onClick={() => setDialog(null)}>Close</button>
                </div>
              </>
            ) : null}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function DialogActions({
  busy,
  confirmDisabled,
  confirmLabel,
  danger,
  onCancel,
  onConfirm,
}: {
  busy: boolean;
  confirmDisabled?: boolean;
  confirmLabel: string;
  danger?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="mt-4 flex justify-end gap-2">
      <button className={adminButtonClass("secondary")} type="button" onClick={onCancel}>Отмена</button>
      <button className={adminButtonClass(danger ? "danger" : "primary")} type="button" disabled={busy || confirmDisabled} onClick={onConfirm}>
        {confirmLabel}
      </button>
    </div>
  );
}
