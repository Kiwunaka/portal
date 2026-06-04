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
  | { kind: "extend"; days: string }
  | { kind: "create"; displayName: string; days: string }
  | { kind: "deleteConfirm"; tgId: number; displayName: string }
  | { kind: "bulkConfirm" }
  | { kind: "token"; subscriptionUrl: string; syncOk: boolean }
  | null;

function errorMessage(err: unknown, fallback: string): string {
  return String((err as { message?: string })?.message || err || fallback);
}

const BULK_CONFIRMATION_PHRASE = "ПРИМЕНИТЬ";

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
    (page: number) => {
      syncQueryState({ ...queryState, page: Math.max(1, page) });
    },
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
      if (!options?.preserveNotice) {
        setOkMessage("");
      }

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
          if (nextId) {
            await loadCardDetails(nextId);
          }
        }
      } catch (err) {
        setError(errorMessage(err, "Не удалось загрузить пользователей."));
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
    if (!selectedTgId) return;
    await loadCardDetails(selectedTgId);
  }, [loadCardDetails, selectedTgId]);

  const copyText = useCallback(async (text: string): Promise<void> => {
    if (!text.trim()) return;
    try {
      await navigator.clipboard.writeText(text.trim());
      setOkMessage("Скопировано в буфер.");
    } catch {
      setError("Не удалось скопировать значение.");
    }
  }, []);

  const actionMessage = useCallback((): void => {
    if (!selectedTgId) return;
    setDialog({ kind: "message", text: "" });
  }, [selectedTgId]);

  const submitMessageDialog = useCallback(async (): Promise<void> => {
    if (!selectedTgId || !dialog || dialog.kind !== "message" || !dialog.text.trim()) return;
    setBusy(true);
    try {
      await adminUserMessage(selectedTgId, dialog.text.trim());
      setOkMessage("Сообщение отправлено.");
      setDialog(null);
      await reloadSelected();
    } catch (err) {
      setError(errorMessage(err, "Не удалось отправить сообщение."));
    } finally {
      setBusy(false);
    }
  }, [dialog, reloadSelected, selectedTgId]);

  const actionExtend = useCallback((): void => {
    if (!selectedTgId) return;
    setDialog({ kind: "extend", days: "30" });
  }, [selectedTgId]);

  const submitExtendDialog = useCallback(async (): Promise<void> => {
    if (!selectedTgId || !dialog || dialog.kind !== "extend") return;
    const days = Number(dialog.days || 0);
    if (!Number.isFinite(days) || days === 0) {
      setError("Укажите корректное число дней.");
      return;
    }

    setBusy(true);
    try {
      await adminManualExtend(selectedTgId, days);
      setOkMessage(`Доступ продлён на ${days} дн.`);
      setDialog(null);
      await reloadSelected();
      await loadUsers({ preserveNotice: true });
    } catch (err) {
      setError(errorMessage(err, "Не удалось продлить доступ."));
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
      setOkMessage(blocked ? "Пользователь заблокирован." : "Пользователь разблокирован.");
      await reloadSelected();
      await loadUsers({ preserveNotice: true });
    } catch (err) {
      setError(errorMessage(err, "Не удалось изменить блокировку."));
    } finally {
      setBusy(false);
    }
  }, [loadUsers, reloadSelected, selected?.user.is_active, selectedTgId]);

  const actionRegenerateToken = useCallback(async (): Promise<void> => {
    if (!selectedTgId) return;
    setBusy(true);
    try {
      const out = await adminManualRegenerateToken(selectedTgId);
      setOkMessage(`Токен обновлён (${out.sync_ok ? "панель синхронизирована" : "синхронизация панели ожидается"}).`);
      setDialog({ kind: "token", subscriptionUrl: out.subscription_url, syncOk: Boolean(out.sync_ok) });
      await reloadSelected();
    } catch (err) {
      setError(errorMessage(err, "Не удалось обновить токен."));
    } finally {
      setBusy(false);
    }
  }, [reloadSelected, selectedTgId]);

  const actionDeleteTestUser = useCallback((): void => {
    if (!selectedTgId || !selectedCanDelete) return;
    const displayName = String(selected?.user.display_name || selected?.user.username || `#${selectedTgId}`);
    setDialog({ kind: "deleteConfirm", tgId: selectedTgId, displayName });
  }, [selected?.user.display_name, selected?.user.username, selectedCanDelete, selectedTgId]);

  const submitDeleteTestUserDialog = useCallback(async (): Promise<void> => {
    if (!dialog || dialog.kind !== "deleteConfirm") return;
    const targetTgId = Number(dialog.tgId || 0);
    if (!targetTgId) return;

    setBusy(true);
    try {
      await adminDeleteTestUser(targetTgId);
      setOkMessage("Manual/test пользователь удалён.");
      setDialog(null);
      selectedIdRef.current = 0;
      setSelected(null);
      await loadUsers({ preserveNotice: true });
    } catch (err) {
      setError(errorMessage(err, "Не удалось удалить manual/test пользователя."));
    } finally {
      setBusy(false);
    }
  }, [dialog, loadUsers]);

  const actionCreateManual = useCallback((): void => {
    setDialog({ kind: "create", displayName: "Тестовый аккаунт", days: "30" });
  }, []);

  const submitCreateManualDialog = useCallback(async (): Promise<void> => {
    if (!dialog || dialog.kind !== "create") return;
    const displayName = dialog.displayName.trim();
    const days = Number(dialog.days || 0);
    if (!displayName || !Number.isFinite(days) || days <= 0) {
      setError("Укажите имя и положительное число дней.");
      return;
    }

    setBusy(true);
    try {
      await adminManualCreate({ display_name: displayName, days });
      setOkMessage("Manual/test пользователь создан.");
      setDialog(null);
      await loadUsers({ preserveNotice: true });
    } catch (err) {
      setError(errorMessage(err, "Не удалось создать manual/test пользователя."));
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
        if (action === "toggle") {
          await adminUserKeyToggle(selectedTgId, key.node_code, !Boolean(key.enabled));
        } else if (action === "reset") {
          await adminUserKeyResetTraffic(selectedTgId, key.node_code);
        } else {
          await adminUserKeyResyncSubId(selectedTgId, key.node_code);
        }
        const actionText =
          action === "toggle"
            ? key.enabled
              ? "Ключ отключён"
              : "Ключ включён"
            : action === "reset"
              ? "Трафик сброшен"
              : "Sub ID синхронизирован";
        setOkMessage(`${actionText} для ноды ${key.node_code}.`);
        await reloadSelected();
      } catch (err) {
        setError(errorMessage(err, "Не удалось выполнить действие с ключом."));
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
        setOkMessage(`Пресет ${preset} выполнен (${result.changed ?? 0} изменений, ${result.failed ?? 0} ошибок).`);
        if (result.subscription_url) {
          setDialog({ kind: "token", subscriptionUrl: result.subscription_url, syncOk: true });
        }
        await reloadSelected();
      } catch (err) {
        setError(errorMessage(err, "Не удалось выполнить пресет."));
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
        setOkMessage(`Политика для ${nodeCode} обновлена.`);
        await reloadSelected();
      } catch (err) {
        setError(errorMessage(err, "Не удалось сохранить политику."));
      } finally {
        setPolicyBusy("");
      }
    },
    [policyDrafts, reloadSelected, selectedTgId],
  );

  const runBulkAction = useCallback(
    async (confirmed = false): Promise<void> => {
      if (!selectedTgId) return;
      setBusy(true);
      setError("");
      setOkMessage("");
      try {
        if (!bulkAction.dryRun && !confirmed) {
          setDialog({ kind: "bulkConfirm" });
          return;
        }

        if (!bulkAction.dryRun) {
          const phrase = window.prompt(`Для подтверждения массового действия введите ${BULK_CONFIRMATION_PHRASE}`);
          if (phrase !== BULK_CONFIRMATION_PHRASE) {
            setError(`Массовое действие не запущено: требуется точная фраза ${BULK_CONFIRMATION_PHRASE}.`);
            return;
          }
        }

        const nodeCodes = bulkAction.nodeCodes
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean);
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
        setBulkResult(
          `Bulk ${out.action || bulkAction.action}: matched ${out.matched ?? 0}, changed ${out.changed ?? 0}, failed ${out.failed ?? 0}${out.dry_run ? " (dry-run)" : ""}.`,
        );
        if (!bulkAction.dryRun) {
          await reloadSelected();
        }
      } catch (err) {
        setError(errorMessage(err, "Не удалось запустить массовое действие."));
      } finally {
        setBusy(false);
      }
    },
    [bulkAction, reloadSelected, selectedTgId],
  );

  const grantLoyaltyTier = useCallback(
    async (tierDays: number): Promise<void> => {
      if (!selectedTgId) return;
      setBusy(true);
      try {
        const out = await adminUserLoyaltyGrant(selectedTgId, tierDays);
        setOkMessage(`Loyalty-награда ${tierDays} дн. выдана${out.sync_ok ? "" : " (синхронизация панели может занять время)"}.`);
        await reloadSelected();
      } catch (err) {
        setError(errorMessage(err, "Не удалось выдать loyalty-награду."));
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
        setError(errorMessage(err, "Не удалось открыть карточку пользователя."));
      } finally {
        setBusy(false);
      }
    },
    [loadCardDetails],
  );

  const onQueryChange = useCallback(
    (value: string) => {
      updateFilters({ q: value });
    },
    [updateFilters],
  );

  const onStatusChange = useCallback(
    (value: string) => {
      updateFilters({ status: value });
    },
    [updateFilters],
  );

  const onOriginChange = useCallback(
    (value: string) => {
      updateFilters({ origin: value });
    },
    [updateFilters],
  );

  const onObserverChange = useCallback(
    (value: string) => {
      updateFilters({ observerState: value });
    },
    [updateFilters],
  );

  const onSortChange = useCallback(
    (value: string) => {
      updateFilters({ sort: value });
    },
    [updateFilters],
  );

  const onPrevPage = useCallback(() => {
    updatePage(Math.max(1, queryState.page - 1));
  }, [queryState.page, updatePage]);

  const onNextPage = useCallback(() => {
    updatePage(Math.min(totalPages, queryState.page + 1));
  }, [queryState.page, totalPages, updatePage]);

  const onRefresh = useCallback(() => {
    void loadUsers();
  }, [loadUsers]);

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
        onQueryChange={onQueryChange}
        onStatusChange={onStatusChange}
        onOriginChange={onOriginChange}
        onObserverChange={onObserverChange}
        onSortChange={onSortChange}
        onRefresh={onRefresh}
        onCreateManual={actionCreateManual}
        onPrevPage={onPrevPage}
        onNextPage={onNextPage}
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
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/65 p-4">
          <div className={`${adminPanelClass("neutral")} max-h-[min(92vh,720px)] w-full max-w-lg overflow-auto`}>
            {dialog.kind === "message" ? (
              <>
                <h3 className="font-display text-xl font-semibold">Сообщение пользователю</h3>
                <p className="mt-1 text-xs text-slate-500">Это отправит прямое сообщение оператором в Telegram.</p>
                <textarea
                  value={dialog.text}
                  onChange={(event) => setDialog({ kind: "message", text: event.target.value })}
                  rows={5}
                  className={`mt-4 ${adminTextAreaClass}`}
                  placeholder="Введите текст сообщения"
                />
                <div className="mt-4 flex justify-end gap-2">
                  <button className={adminButtonClass("secondary")} type="button" onClick={() => setDialog(null)}>
                    Отмена
                  </button>
                  <button className={adminButtonClass("primary")} type="button" disabled={busy || !dialog.text.trim()} onClick={() => void submitMessageDialog()}>
                    Отправить
                  </button>
                </div>
              </>
            ) : null}

            {dialog.kind === "extend" ? (
              <>
                <h3 className="font-display text-xl font-semibold">Продлить доступ</h3>
                <p className="mt-1 text-xs text-slate-500">Добавьте оплаченные дни к текущей подписке пользователя.</p>
                <input
                  value={dialog.days}
                  onChange={(event) => setDialog({ kind: "extend", days: event.target.value })}
                  type="number"
                  min={1}
                  className={`mt-4 ${adminFieldClass}`}
                  placeholder="Дней"
                />
                <div className="mt-4 flex justify-end gap-2">
                  <button className={adminButtonClass("secondary")} type="button" onClick={() => setDialog(null)}>
                    Отмена
                  </button>
                  <button className={adminButtonClass("primary")} type="button" disabled={busy} onClick={() => void submitExtendDialog()}>
                    Применить
                  </button>
                </div>
              </>
            ) : null}

            {dialog.kind === "create" ? (
              <>
                <h3 className="font-display text-xl font-semibold">Создать manual/test пользователя</h3>
                <p className="mt-1 text-xs text-slate-500">Manual-аккаунты допустимы только для админских и тестовых задач.</p>
                <input
                  value={dialog.displayName}
                  onChange={(event) => setDialog({ kind: "create", displayName: event.target.value, days: dialog.days })}
                  className={`mt-4 ${adminFieldClass}`}
                  placeholder="Имя пользователя"
                />
                <input
                  value={dialog.days}
                  onChange={(event) => setDialog({ kind: "create", displayName: dialog.displayName, days: event.target.value })}
                  type="number"
                  min={1}
                  className={`mt-3 ${adminFieldClass}`}
                  placeholder="Дней доступа"
                />
                <div className="mt-4 flex justify-end gap-2">
                  <button className={adminButtonClass("secondary")} type="button" onClick={() => setDialog(null)}>
                    Отмена
                  </button>
                  <button className={adminButtonClass("primary")} type="button" disabled={busy} onClick={() => void submitCreateManualDialog()}>
                    Создать
                  </button>
                </div>
              </>
            ) : null}

            {dialog.kind === "deleteConfirm" ? (
              <>
                <h3 className="font-display text-xl font-semibold">Удалить manual/test пользователя</h3>
                <p className="mt-2 text-sm text-slate-500">
                  Вы собираетесь удалить <strong>{dialog.displayName}</strong> ({dialog.tgId}). Это действие необратимо и доступно только для явных manual/test аккаунтов.
                </p>
                <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:justify-end">
                  <button className={adminButtonClass("secondary")} type="button" onClick={() => setDialog(null)}>
                    Отмена
                  </button>
                  <button className={adminButtonClass("danger")} type="button" disabled={busy} onClick={() => void submitDeleteTestUserDialog()}>
                    Удалить пользователя
                  </button>
                </div>
              </>
            ) : null}

            {dialog.kind === "bulkConfirm" ? (
              <>
                <h3 className="font-display text-xl font-semibold">Подтвердить массовое действие</h3>
                <p className="mt-2 text-sm text-slate-500">
                  Вы собираетесь запустить <strong>{bulkAction.action}</strong> для сегмента <strong>{bulkAction.segment}</strong>.
                </p>
                <p className="mt-2 text-xs text-slate-500">
                  Поиск: {bulkAction.q.trim() || "нет"} | Лимит: {bulkAction.limit} | Ноды: {bulkAction.nodeCodes.trim() || "все"}
                </p>
                <p className="mt-2 text-xs text-amber-700">
                  После нажатия кнопки браузер запросит фразу <strong>{BULK_CONFIRMATION_PHRASE}</strong>. Это защищает действие от случайного клика и clickjacking.
                </p>
                <div className="mt-4 flex justify-end gap-2">
                  <button className={adminButtonClass("secondary")} type="button" onClick={() => setDialog(null)}>
                    Отмена
                  </button>
                  <button className={adminButtonClass("primary")} type="button" disabled={busy} onClick={() => void runBulkAction(true)}>
                    Запустить действие
                  </button>
                </div>
              </>
            ) : null}

            {dialog.kind === "token" ? (
              <>
                <h3 className="font-display text-xl font-semibold">Новая подписочная ссылка</h3>
                <p className="mt-1 text-xs text-slate-500">
                  Синхронизация панели: {dialog.syncOk ? "успешна" : "в ожидании или с ошибкой"}.
                </p>
                <input
                  value={dialog.subscriptionUrl}
                  readOnly
                  className={`mt-4 ${adminFieldClass} text-xs`}
                />
                <div className="mt-4 flex justify-end gap-2">
                  <button className={adminButtonClass("secondary")} type="button" onClick={() => void copyText(dialog.subscriptionUrl)}>
                    Скопировать
                  </button>
                  <button className={adminButtonClass("primary")} type="button" onClick={() => setDialog(null)}>
                    Закрыть
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
