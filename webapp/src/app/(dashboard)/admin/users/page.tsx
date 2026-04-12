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
  type AdminAuditRow,
  type AdminObserverState,
  type AdminUserCard,
  type AdminUserKey,
  type AdminUserKeyHistoryRow,
  type AdminUserRow,
} from "@/lib/api";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fmtRuDate } from "../nav";

function fmtTraffic(bytes: number): string {
  const gb = Number(bytes || 0) / (1024 ** 3);
  return `${gb.toFixed(2)} GB`;
}

function fmtOnline(value: boolean | null | undefined): string {
  if (value === true) return "В сети";
  if (value === false) return "Не в сети";
  return "Неизвестно";
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
  if (!value) return "-";
  if (value.includes("regen") || value.includes("rotate")) return "Ротация токена";
  if (value.includes("reset")) return "Сброс трафика";
  if (value.includes("resync")) return "Синхронизация sub ID";
  if (value.includes("move") || value.includes("node")) return "Перенос ноды";
  if (value.includes("disable") || value.includes("block")) return "Блокировка";
  if (value.includes("enable") || value.includes("unblock")) return "Разблокировка";
  if (value.includes("create")) return "Создание";
  if (value.includes("delete") || value.includes("remove")) return "Удаление";
  if (value.includes("extend")) return "Продление";
  return action;
}

function riskLevelLabel(level: string): string {
  const value = String(level || "").toLowerCase();
  if (value === "low") return "Низкий";
  if (value === "medium" || value === "med") return "Средний";
  if (value === "high") return "Высокий";
  if (value === "critical" || value === "crit") return "Критичный";
  return value || "Неизвестно";
}

function panelStateLabel(state: string): string {
  const value = String(state || "").toLowerCase();
  if (["ok", "healthy", "fresh"].includes(value)) return "Норма";
  if (["degraded", "stale", "warn", "warning"].includes(value)) return "Деградация";
  if (["error", "down", "offline", "fail"].includes(value)) return "Ошибка";
  return value || "Неизвестно";
}

function ticketStatusLabel(status: string): string {
  const value = String(status || "").toLowerCase().replace(/\s+/g, "_");
  if (value === "open") return "Открыт";
  if (value === "in_progress") return "В работе";
  if (value === "closed") return "Закрыт";
  return status || "-";
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
  | { kind: "deleteConfirm"; tgId: number; displayName: string }
  | { kind: "bulkConfirm" }
  | { kind: "token"; subscriptionUrl: string; syncOk: boolean }
  | null;

function userStatusLabel(status: string): string {
  const value = String(status || "").toLowerCase();
  if (value === "active") return "Активен";
  if (value === "blocked") return "Заблокирован";
  if (value === "manual_test") return "Manual/Test";
  return "Истёк";
}

function userStatusBadgeClass(status: string): string {
  const value = String(status || "").toLowerCase();
  if (value === "active") return "bg-emerald-500/20 text-emerald-600";
  if (value === "blocked") return "bg-amber-500/20 text-amber-600";
  if (value === "manual_test") return "bg-violet-500/20 text-violet-600";
  return "bg-rose-500/20 text-rose-500";
}

function originLabel(origin: string): string {
  const value = String(origin || "").toLowerCase();
  if (value === "app") return "Приложение";
  if (value === "hybrid") return "Приложение + Telegram";
  if (value === "manual_test") return "Manual/Test";
  return "Telegram";
}

function observerStateLabel(state: AdminObserverState | string): string {
  const value = String(state || "").toLowerCase();
  if (value === "watch") return "watch";
  if (value === "suspicious") return "suspicious";
  return "ok";
}

function observerStateBadgeClass(state: AdminObserverState | string): string {
  const value = String(state || "").toLowerCase();
  if (value === "suspicious") return "badge-danger";
  if (value === "watch") return "badge-warning";
  return "badge-success";
}

function isManualTestUserLike(user: {
  tg_id?: number | null;
  origin?: string | null;
  status?: string | null;
  is_manual?: boolean | null;
} | null | undefined): boolean {
  if (!user) return false;
  return Boolean(
    user.is_manual ||
      String(user.origin || "").toLowerCase() === "manual_test" ||
      String(user.status || "").toLowerCase() === "manual_test" ||
      Number(user.tg_id || 0) < 0,
  );
}

function observerHasData(observer: AdminUserCard["observer"] | null | undefined): boolean {
  if (!observer) return false;
  return Boolean(
    observer.observed_ip_count_24h ||
      observer.observed_ip_count_7d ||
      observer.observed_ip_count_30d ||
      observer.observed_node_count_24h ||
      observer.observed_node_count_7d ||
      observer.observed_node_count_30d ||
      observer.overlap_count_24h ||
      observer.reasons?.length ||
      observer.recent_ips?.length ||
      observer.recent_nodes?.length,
  );
}

export default function AdminUsersPage() {
  const [query, setQuery] = useState("");
  const [rows, setRows] = useState<AdminUserRow[]>([]);
  const [totalRows, setTotalRows] = useState(0);
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
  const [statusFilter, setStatusFilter] = useState("all");
  const [originFilter, setOriginFilter] = useState("all");
  const [observerFilter, setObserverFilter] = useState("all");
  const [sortOrder, setSortOrder] = useState("created_desc");
  const [page, setPage] = useState(1);
  const pageSize = 80;
  const selectedIdRef = useRef<number>(0);
  const [bulkAction, setBulkAction] = useState({
    action: "disable" as "disable" | "enable" | "reset" | "resync",
    segment: "active",
    q: "",
    nodeCodes: "",
    limit: 50,
    dryRun: true,
    force: false,
  });

  const loadCardDetails = useCallback(async (tgId: number): Promise<void> => {
    const card = await adminUserCard(tgId);
    setSelected(card);
    setKeyHistoryRows(card.key_history || []);
    setAuditRows(card.admin_actions || []);
  }, []);

  const loadUsers = useCallback(async (options?: { preserveNotice?: boolean }): Promise<void> => {
    setLoading(true);
    setError("");
    if (!options?.preserveNotice) {
      setOkMessage("");
    }
    try {
      const result = await adminUsers({
        q: query.trim() || undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
        origin: originFilter !== "all" ? originFilter : undefined,
        observer_state: observerFilter !== "all" ? observerFilter : undefined,
        sort: sortOrder,
        page,
        page_size: pageSize,
      });
      setRows(result.users);
      setTotalRows(result.total);
      if (!result.users.length) {
        setSelected(null);
        setKeyHistoryRows([]);
        setAuditRows([]);
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
      setError(String((err as { message?: string })?.message || err || "    "));
    } finally {
      setLoading(false);
    }
  }, [loadCardDetails, observerFilter, originFilter, page, query, sortOrder, statusFilter]);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  useEffect(() => {
    setPage(1);
  }, [observerFilter, originFilter, query, sortOrder, statusFilter]);

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
      setOkMessage("Скопировано в буфер.");
    } catch {
      setError("Не удалось скопировать значение.");
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
      setOkMessage("Сообщение отправлено.");
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
      setOkMessage(blocked ? "Пользователь заблокирован." : "Пользователь разблокирован.");
      await reloadSelected();
      await loadUsers({ preserveNotice: true });
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
      setOkMessage(`Токен обновлён (${out.sync_ok ? "панель синхронизирована" : "синхронизация панели ожидается"}).`);
      setDialog({ kind: "token", subscriptionUrl: out.subscription_url, syncOk: Boolean(out.sync_ok) });
      await reloadSelected();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "   "));
    } finally {
      setBusy(false);
    }
  };

  const actionDeleteTestUser = async (): Promise<void> => {
    if (!selectedTgId || !isManualTestUserLike(selected?.user)) return;
    const displayName = String(selected?.user.display_name || selected?.user.username || `#${selectedTgId}`);
    setDialog({ kind: "deleteConfirm", tgId: selectedTgId, displayName });
  };

  const submitDeleteTestUserDialog = async (): Promise<void> => {
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
      setKeyHistoryRows([]);
      setAuditRows([]);
      await loadUsers({ preserveNotice: true });
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "    "));
    } finally {
      setBusy(false);
    }
  };

  const actionCreateManual = async (): Promise<void> => {
    setDialog({ kind: "create", displayName: "Тестовый аккаунт", days: "30" });
  };

  const submitCreateManualDialog = async (): Promise<void> => {
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
      const presetLabels: Record<string, string> = {
        reset_key: "Пресет «сбросить ключ» выполнен.",
        rotate_link: "Пресет «обновить ссылку» выполнен.",
        extend_1d: "Пресет «+1 день» выполнен.",
        send_guide: "Пресет «отправить инструкцию» выполнен.",
      };
      setOkMessage(presetLabels[result.preset] || `Пресет ${result.preset} выполнен.`);
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
      setOkMessage(`Лимиты и политика сохранены для ноды ${nodeCode}.`);
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
      const affected = Number(out?.users || out?.affected || 0);
      const failed = Number(out?.failed || 0);
      const changed = Number(out?.changed || 0);
      const mode = out?.dry_run ? "Предпросмотр" : "Применение";
      setBulkResult(`${mode}: найдено ${affected}, изменено ${changed}, ошибок ${failed}.`);
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
      setOkMessage(`Награда loyalty за ${out.tier_days} дн. выдана (${out.sync_ok ? "панель синхронизирована" : "синхронизация панели ожидается"}).`);
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
  const observer = selected?.observer;
  const selectedCanDelete = isManualTestUserLike(selected?.user);
  const pageStart = rows.length ? (page - 1) * pageSize + 1 : 0;
  const pageEnd = rows.length ? pageStart + rows.length - 1 : 0;
  const totalPages = Math.max(1, Math.ceil(totalRows / pageSize));

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
    <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr),minmax(0,1fr)]">
      <article className="glass-card min-w-0 p-4">
        <div className="mb-3 grid gap-2 sm:grid-cols-2 2xl:grid-cols-[minmax(0,1.6fr),repeat(4,minmax(0,0.9fr)),auto,auto]">
          <input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(1);
            }}
            placeholder="Поиск по username, Telegram ID, имени или app install ID"
            className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          />
          <select
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value);
              setPage(1);
            }}
            className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          >
            <option value="all">Все статусы</option>
            <option value="active">Активные</option>
            <option value="expired">Истёкшие</option>
            <option value="blocked">Заблокированные</option>
            <option value="manual_test">Manual/Test</option>
          </select>
          <select
            value={originFilter}
            onChange={(event) => {
              setOriginFilter(event.target.value);
              setPage(1);
            }}
            className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          >
            <option value="all">Все источники</option>
            <option value="telegram">Telegram</option>
            <option value="app">Приложение</option>
            <option value="hybrid">Приложение + Telegram</option>
            <option value="manual_test">Manual/Test</option>
          </select>
          <select
            value={observerFilter}
            onChange={(event) => {
              setObserverFilter(event.target.value);
              setPage(1);
            }}
            className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          >
            <option value="all">Observer: all</option>
            <option value="ok">Observer: ok</option>
            <option value="watch">Observer: watch</option>
            <option value="suspicious">Observer: suspicious</option>
          </select>
          <select
            value={sortOrder}
            onChange={(event) => {
              setSortOrder(event.target.value);
              setPage(1);
            }}
            className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          >
            <option value="created_desc">Сначала новые</option>
            <option value="created_asc">Сначала старые</option>
            <option value="expiry_asc">Скоро истекают</option>
            <option value="expiry_desc">Истекают позже</option>
            <option value="name_asc">Имя А-Я</option>
          </select>
          <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void loadUsers()}>
            Обновить
          </button>
          <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void actionCreateManual()} disabled={busy}>
            + Создать manual/test пользователя
          </button>
        </div>

        <div className="mb-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-violet-200/40 bg-white/70 px-3 py-2 text-xs text-slate-500 dark:border-violet-500/20 dark:bg-white/5">
          <div>
            Показаны {pageStart}-{pageEnd || 0} из {totalRows} пользователей. Эффективный статус общий для web и bot admin.
          </div>
          <div className="flex items-center gap-2">
            <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" disabled={page <= 1 || loading} onClick={() => setPage((prev) => Math.max(1, prev - 1))}>
              Предыдущая
            </button>
            <span>
              Страница {page} / {totalPages}
            </span>
            <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" disabled={page >= totalPages || loading} onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}>
              Следующая
            </button>
          </div>
        </div>

        <div className="mb-3 rounded-xl border border-violet-200/40 bg-white/70 p-3 dark:border-violet-500/20 dark:bg-white/5">
          <p className="mb-1 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">Массовое действие с ключами</p>
          <p className="mb-2 text-xs text-slate-500">Используйте сегменты, выровненные с backend, и начинайте с dry run, если затрагиваете много пользователей.</p>
          <div className="grid gap-2 sm:grid-cols-2">
            <select
              value={bulkAction.action}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, action: event.target.value as "disable" | "enable" | "reset" | "resync" }))}
              className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            >
              <option value="disable">Отключить ключи</option>
              <option value="enable">Включить ключи</option>
              <option value="reset">Сбросить трафик</option>
              <option value="resync">Синхронизировать subId</option>
            </select>
            <select
              value={bulkAction.segment}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, segment: event.target.value }))}
              className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            >
              <option value="all">Все пользователи</option>
              <option value="active">Активные</option>
              <option value="inactive">Неактивные</option>
              <option value="expired">Истёкшие</option>
              <option value="blocked">Заблокированные</option>
              <option value="paid">Платные</option>
              <option value="free">Бесплатные</option>
              <option value="manual_test">Manual/Test</option>
            </select>
            <input
              value={bulkAction.q}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, q: event.target.value }))}
              placeholder="Необязательный поиск внутри сегмента"
              className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            />
            <input
              value={bulkAction.nodeCodes}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, nodeCodes: event.target.value }))}
              placeholder="Необязательные коды нод через запятую"
              className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            />
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <label className="text-xs text-slate-600 dark:text-slate-300">
              Лимит:
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
              Предпросмотр
            </label>
            <label className="inline-flex items-center gap-1 text-xs text-slate-600 dark:text-slate-300">
              <input type="checkbox" checked={bulkAction.force} onChange={(event) => setBulkAction((prev) => ({ ...prev, force: event.target.checked }))} />
              Принудительно
            </label>
            <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={() => void runBulkAction()} disabled={busy}>
              Запустить массовое действие
            </button>
          </div>
          {bulkResult ? <p className="mt-2 text-xs text-emerald-500">{bulkResult}</p> : null}
        </div>

        {loading ? <p className="text-sm text-slate-500"> ...</p> : null}
        {error ? <p className="mb-2 text-sm text-rose-500">{error}</p> : null}
        {okMessage ? <p className="mb-2 text-sm text-emerald-500">{okMessage}</p> : null}

        <div className="mb-3 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
          <span>{rows.length ? `Показаны ${pageStart}-${pageEnd} из ${totalRows} пользователей.` : "По текущим фильтрам пользователей нет."}</span>
          <span>Безопасное удаление доступно только для явных manual/test пользователей.</span>
        </div>

        <div className="max-h-[58vh] overflow-x-auto overflow-y-auto rounded-xl border border-white/20">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="px-2 py-2">ID</th>
                <th className="px-2 py-2">Observer</th>
                <th className="px-2 py-2">Пользователь</th>
                <th className="px-2 py-2">Статус</th>
                <th className="px-2 py-2">Источник</th>
                <th className="px-2 py-2">Тариф</th>
                <th className="px-2 py-2">Истекает</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={`summary-${row.tg_id}`}
                  className={`cursor-pointer border-t border-white/30 dark:border-white/10 ${
                    row.tg_id === selectedTgId ? "bg-violet-500/10" : isManualTestUserLike(row) ? "bg-violet-500/5" : ""
                  }`}
                  onClick={() => void pickUser(row.tg_id)}
                >
                  <td className="px-2 py-2 font-mono text-xs">{row.tg_id}</td>
                  <td className="px-2 py-2">
                    <span className={`badge ${observerStateBadgeClass(row.observer_state)}`}>{observerStateLabel(row.observer_state)}</span>
                  </td>
                  <td className="px-2 py-2">
                    <div className="font-medium">{row.display_name || row.username || "Без имени"}</div>
                    <div className="text-xs text-slate-500">
                      {row.username ? `@${row.username}` : "без username"}
                      {row.linked_telegram_username ? ` | linked @${row.linked_telegram_username}` : ""}
                      {row.app_install_id ? ` | app ${row.app_install_id}` : ""}
                    </div>
                  </td>
                  <td className="px-2 py-2">
                    <span className={`rounded-full px-2 py-1 text-xs ${userStatusBadgeClass(row.status)}`}>{userStatusLabel(row.status)}</span>
                  </td>
                  <td className="px-2 py-2">
                    <span className="rounded-full bg-slate-500/10 px-2 py-1 text-xs font-semibold text-slate-600 dark:text-slate-200">
                      {originLabel(row.origin)}
                    </span>
                  </td>
                  <td className="px-2 py-2">{row.sub_type || "-"}</td>
                  <td className="px-2 py-2 text-xs text-slate-600 dark:text-slate-300">{fmtRuDate(row.expiry_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs text-slate-500">
            Страница {page} из {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" disabled={page <= 1 || loading} onClick={() => setPage((prev) => Math.max(1, prev - 1))}>
              Предыдущая
            </button>
            <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" disabled={page >= totalPages || loading} onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}>
              Следующая
            </button>
          </div>
        </div>
      </article>

      <article className="glass-card min-w-0 p-4">
        {!selected ? (
          <p className="text-sm text-slate-500">Выберите пользователя в таблице, чтобы открыть детали.</p>
        ) : (
          <>
            <div className="mb-3 rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="font-display text-2xl font-semibold">{selected.user.display_name || selected.user.username || `Пользователь #${selected.user.tg_id}`}</h2>
                  <p className="text-xs text-slate-500">tg_id: {selected.user.tg_id}</p>
                  <p className="text-xs text-slate-500">Создан: {fmtRuDate(selected.user.created_at)}</p>
                  <p className="text-xs text-slate-500">Истекает: {fmtRuDate(selected.user.expiry_at)}</p>
                </div>
                <div className="space-y-2 text-right">
                  <div className="flex flex-wrap items-center justify-end gap-2">
                    <span className={`rounded-full px-2 py-1 text-xs ${userStatusBadgeClass(selected.user.status)}`}>{userStatusLabel(selected.user.status)}</span>
                    <span className={`badge ${observerStateBadgeClass(selected.user.observer_state)}`}>Observer {observerStateLabel(selected.user.observer_state)}</span>
                    <span className="badge badge-violet">{originLabel(selected.user.origin)}</span>
                  </div>
                  <p className="text-xs text-slate-500">
                    Связанный Telegram: {selected.user.linked_telegram_username ? `@${selected.user.linked_telegram_username}` : selected.user.linked_telegram_id || "нет"}
                  </p>
                  <p className="text-xs text-slate-500">ID установки app: {selected.user.app_install_id || "нет"}</p>
                </div>
              </div>
            </div>

            <div className="mb-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
              <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void actionMessage()} disabled={busy}>
                Написать пользователю
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void actionExtend()} disabled={busy}>
                Продлить доступ
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void actionRegenerateToken()} disabled={busy}>
                Обновить токен
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void actionToggleBlock()} disabled={busy}>
                {selected.user.status === "blocked" ? "Разблокировать пользователя" : "Заблокировать пользователя"}
              </button>
              {selectedCanDelete ? (
                <button className="rounded-xl bg-rose-500/15 px-3 py-2 text-sm font-semibold text-rose-500" type="button" onClick={() => void actionDeleteTestUser()} disabled={busy}>
                  Удалить manual/test пользователя
                </button>
              ) : null}
            </div>

            {selectedCanDelete ? (
              <div className="mb-3 rounded-xl border border-rose-200/60 bg-rose-50/70 p-3 dark:border-rose-500/20 dark:bg-rose-500/10">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold text-rose-600">Очистка manual/test</p>
                    <p className="text-xs text-slate-500">Из админки можно удалять только явных manual/test пользователей.</p>
                  </div>
                  <button className="rounded-xl bg-rose-500 px-3 py-2 text-xs font-semibold text-white disabled:opacity-60" type="button" onClick={() => void actionDeleteTestUser()} disabled={busy}>
                    Удалить manual/test пользователя
                  </button>
                </div>
              </div>
            ) : null}
            <div className="mb-3 grid gap-2 sm:grid-cols-2">
              <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void runPreset("reset_key")} disabled={busy}>
                Пресет: сбросить ключ
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void runPreset("rotate_link")} disabled={busy}>
                Пресет: обновить ссылку
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void runPreset("extend_1d")} disabled={busy}>
                Пресет: +1 день
              </button>
              <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void runPreset("send_guide")} disabled={busy}>
                Пресет: отправить инструкцию
              </button>
            </div>

            <div className="mb-3 grid gap-3 xl:grid-cols-3">
              <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                <p>Тариф: <strong>{selected.user.sub_type || "-"}</strong></p>
                <p>Оплачено stars: <strong>{selected.user.stars_paid}</strong></p>
                <p>Рефералы: <strong>{selected.user.referral_count}</strong></p>
                <p>Серия: <strong>{loyalty?.streak_days ?? 0} дн.</strong></p>
              </div>
              <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                <div className="mb-1 flex items-center gap-2">
                  <span className={`badge ${riskClass}`}>Риск {Math.round(risk?.score || 0)}</span>
                  <span className="text-xs text-slate-500">{riskLevelLabel(String(risk?.level || ""))}</span>
                </div>
                <p className="text-xs">Ротации: <strong>{risk?.signals?.regen_count ?? 0}</strong></p>
                <p className="text-xs">Операции админа с ключами: <strong>{risk?.signals?.admin_key_ops ?? 0}</strong></p>
                <p className="text-xs">Уникальные IP: <strong>{risk?.signals?.unique_ips ?? 0}</strong></p>
                <p className="text-xs">Трафик: <strong>{Number(risk?.signals?.traffic_gb || 0).toFixed(2)} GB</strong></p>
              </div>
            </div>

            <div className="mb-3 rounded-xl border border-white/30 bg-white/70 p-3 text-xs text-slate-500 dark:border-white/10 dark:bg-white/10">
              <p>Расшифровка рисков:</p>
              <p>Ротации = ротации ссылки/ключа за 30 дней.</p>
              <p>Операции админа с ключами = ручные admin-действия за 30 дней.</p>
              <p>Уникальные IP = адреса из event log за 30 дней, а не runtime panel IP.</p>
            </div>

            <div className="mb-3 rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
              <div className="mb-1 flex items-center gap-2">
                <span className={`badge ${observerStateBadgeClass(observer?.state || selected.user.observer_state)}`}>
                  Observer {observerStateLabel(observer?.state || selected.user.observer_state)}
                </span>
                <span className="text-xs text-slate-500">
                  {observer?.updated_at ? `updated ${fmtRuDate(observer.updated_at)}` : "updated: n/a"}
                </span>
              </div>
              {!observerHasData(observer) ? (
                <p className="text-xs text-slate-500">Observer пока не прислал наблюдений.</p>
              ) : (
                <>
                  <p className="text-xs">IP 24h: <strong>{observer?.observed_ip_count_24h ?? 0}</strong></p>
                  <p className="text-xs">Nodes 24h: <strong>{observer?.observed_node_count_24h ?? 0}</strong></p>
                  <p className="text-xs">Overlap 24h: <strong>{observer?.overlap_count_24h ?? 0}</strong></p>
                  <p className="text-xs">Reasons: <strong>{observer?.reasons?.length ? observer.reasons.join(", ") : "none"}</strong></p>
                </>
              )}
            </div>

            <div className="mt-3 rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
              <p className="mb-1 font-semibold">Подписочный доступ</p>
              <div className="flex items-start gap-2">
                <input
                  value={String(selected.user.subscription_url || "")}
                  readOnly
                  className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                />
                <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void copyText(String(selected.user.subscription_url || ""))}>
                  Скопировать URL
                </button>
              </div>
              <div className="mt-2 flex items-start gap-2">
                <input
                  value={String(selected.user.subscription_token || "")}
                  readOnly
                  className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                />
                <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => void copyText(String(selected.user.subscription_token || ""))}>
                  Скопировать токен
                </button>
              </div>
            </div>

            {loyalty?.tiers?.length ? (
              <div className="mb-3 rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                <p className="mb-2 font-semibold">Loyalty-награды (30/90/180)</p>
                <div className="grid gap-2 sm:grid-cols-3">
                  {loyalty.tiers.map((tier) => (
                    <div key={tier.reward_key} className="rounded-xl border border-white/30 bg-white/70 p-2 text-xs dark:border-white/10 dark:bg-white/5">
                      <p className="font-semibold">{tier.days} дн.</p>
                      <p>Бонус: {tier.bonus_days} дн.</p>
                      <p>Перк: {tier.perk}</p>
                      <p className="mt-1">Статус: {tier.claimed ? "выдано" : tier.unlocked ? "готово к выдаче" : "заблокировано"}</p>
                      {!tier.claimed && tier.unlocked ? (
                        <button className="mt-2 outline-btn rounded-lg px-2 py-1 text-[11px] font-semibold" type="button" disabled={busy} onClick={() => void grantLoyaltyTier(tier.days)}>
                          Выдать награду
                        </button>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="mb-3 flex flex-wrap gap-2">
              <button className={tabButtonClass("overview")} type="button" onClick={() => setDetailTab("overview")}>Обзор</button>
              <button className={tabButtonClass("keys")} type="button" onClick={() => setDetailTab("keys")}>Ключи и лимиты</button>
              <button className={tabButtonClass("history")} type="button" onClick={() => setDetailTab("history")}>История ключей</button>
              <button className={tabButtonClass("audit")} type="button" onClick={() => setDetailTab("audit")}>Аудит</button>
            </div>

            {detailTab === "overview" ? (
              <>
                <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                  <p className="mb-2 font-semibold">Сводка по подключению</p>
                  <p className="mb-2 text-xs text-slate-500">
                    Единое окно контроля профиля: мониторинг состояния серверов, биллинга и коннекта пользователя.
                  </p>
                  {summary ? (
                    <div className="grid gap-2 text-xs sm:grid-cols-2">
                      <p>Нод с клиентом: <strong>{summary.nodes_with_client}/{summary.nodes_total}</strong></p>
                      <p>Нод в сети: <strong>{summary.nodes_online}</strong></p>
                      <p>Ключей online сейчас: <strong>{summary.online_keys_now}</strong></p>
                      <p>Подключений сейчас: <strong>{summary.online_connections_now}</strong></p>
                      <p>Нод в выдаче: <strong>{summary.nodes_enabled}</strong></p>
                      <p>Расхождения sub ID: <strong>{summary.subid_mismatch_count}</strong></p>
                      <p>Общий трафик: <strong>{fmtTraffic(summary.traffic_total_bytes)}</strong></p>
                      <p>Состояние панели: <strong>{panelStateLabel(String(summary.panel_state || ""))}</strong></p>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500">Сводка по этому пользователю пока недоступна.</p>
                  )}
                  {summary?.online_node_codes_now?.length ? (
                    <p className="mt-2 text-xs text-slate-500">
                      Сейчас online на нодах: <strong>{summary.online_node_codes_now.map((code) => String(code || "").toUpperCase()).join(", ")}</strong>
                    </p>
                  ) : (
                    <p className="mt-2 text-xs text-slate-500">Сейчас online ноды не видны: ключ либо офлайн, либо runtime ещё не обновился.</p>
                  )}
                </div>
                <h3 className="mt-4 font-display text-xl font-semibold">Обращения поддержки</h3>
                <div className="mt-4 rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <p className="font-semibold">Observer-lite</p>
                    <span className={`badge ${observerStateBadgeClass(observer?.state || selected.user.observer_state)}`}>
                      {observerStateLabel(observer?.state || selected.user.observer_state)}
                    </span>
                  </div>
                  {!observerHasData(observer) ? (
                    <p className="text-xs text-slate-500">Данных наблюдения пока нет.</p>
                  ) : (
                    <div className="grid gap-3 lg:grid-cols-2">
                      <div className="space-y-1 text-xs">
                        <p>IPs: <strong>{observer?.observed_ip_count_24h ?? 0}</strong> / 24h, <strong>{observer?.observed_ip_count_7d ?? 0}</strong> / 7d, <strong>{observer?.observed_ip_count_30d ?? 0}</strong> / 30d</p>
                        <p>Nodes: <strong>{observer?.observed_node_count_24h ?? 0}</strong> / 24h, <strong>{observer?.observed_node_count_7d ?? 0}</strong> / 7d, <strong>{observer?.observed_node_count_30d ?? 0}</strong> / 30d</p>
                        <p>Overlap 24h: <strong>{observer?.overlap_count_24h ?? 0}</strong></p>
                        <p>Last observed: <strong>{fmtRuDate(observer?.last_observed_at)}</strong></p>
                        <p>Reasons: <strong>{observer?.reasons?.length ? observer.reasons.join(", ") : "none"}</strong></p>
                      </div>
                      <div className="grid gap-3 lg:grid-cols-2">
                        <div>
                          <p className="mb-1 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">Recent IPs</p>
                          <div className="space-y-1">
                            {(observer?.recent_ips || []).map((row) => (
                              <div key={`${row.node_code}:${row.source_ip_raw}:${row.last_seen_at}`} className="rounded-lg border border-white/20 bg-white/60 px-2 py-1 text-xs dark:border-white/10 dark:bg-white/5">
                                <div className="flex items-center justify-between gap-2">
                                  <span className="font-mono">{row.source_ip_raw}</span>
                                  <span className="badge badge-info">{String(row.node_code || "").toUpperCase()}</span>
                                </div>
                                <div className="mt-1 text-slate-500">{fmtRuDate(row.last_seen_at)}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                        <div>
                          <p className="mb-1 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">Recent nodes</p>
                          <div className="space-y-1">
                            {(observer?.recent_nodes || []).map((row) => (
                              <div key={`${row.node_id}:${row.last_seen_at}`} className="rounded-lg border border-white/20 bg-white/60 px-2 py-1 text-xs dark:border-white/10 dark:bg-white/5">
                                <div className="flex items-center justify-between gap-2">
                                  <span>{String(row.node_code || "").toUpperCase()}</span>
                                  <span>{row.score_ip_count} IP</span>
                                </div>
                                <div className="mt-1 text-slate-500">{fmtRuDate(row.last_seen_at)}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                  <p className="mt-3 text-[11px] text-slate-500">Эта телеметрия показывает, где ключ видели недавно. Статус &quot;сейчас online&quot; берётся отдельно из live runtime панели.</p>
                </div>
                <div className="mt-2 space-y-2">
                  {(selected.tickets || []).map((ticket) => (
                    <div key={ticket.id} className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                      <p className="font-medium">#{ticket.id} - {ticketStatusLabel(ticket.status_title)}</p>
                      <p className="text-xs text-slate-500">{ticket.last_message_preview || "Превью сообщения пока нет"}</p>
                    </div>
                  ))}
                  {!selected.tickets?.length ? <p className="text-xs text-slate-500">Обращениеов пока нет.</p> : null}
                </div>
              </>
            ) : null}

            {detailTab === "keys" ? (
              <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <p className="font-semibold">Ключи, состояние нод и лимиты</p>
                  <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={() => void reloadSelected()} disabled={busy || !!keyBusy || !!policyBusy}>
                    Обновить
                  </button>
                </div>
                <p className="mb-3 text-xs text-slate-500">
                  Здесь можно проверить существование ключа, включён ли он, совпадает ли sub ID, какой трафик уже накоплен и какие node-level лимиты сейчас применяются.
                </p>
                <div className="space-y-2">
                  {keys.length === 0 ? <p className="text-xs text-slate-500">Для этого пользователя ключи не найдены.</p> : null}
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
                          <p className="font-semibold">{key.node_code} - {key.node_name || "Нода без названия"}</p>
                          <span className={`rounded-full px-2 py-0.5 ${key.exists ? "bg-emerald-500/20 text-emerald-600" : "bg-slate-300/40 text-slate-500"}`}>
                            {key.exists ? "Есть ключ" : "Ключ отсутствует"}
                          </span>
                        </div>
                        <p className="mt-1">В сети: <strong>{fmtOnline(key.online)}</strong> | Включён: <strong>{key.enabled ? "да" : "нет"}</strong></p>
                        <p>Подключений сейчас: <strong>{key.current_connections}</strong></p>
                        <p>Текущий sub ID: <strong>{key.sub_id || "-"}</strong></p>
                        <p>Ожидаемый sub ID: <strong>{key.expected_sub_id || "-"}</strong> | Совпадает: <strong>{key.sub_id_match ? "да" : "нет"}</strong></p>
                        <p>Трафик: <strong>{fmtTraffic(key.total_bytes)}</strong> ({key.up_bytes} up / {key.down_bytes} down)</p>
                        <p>Последний online: <strong>{fmtRuDate(key.last_online_at)}</strong></p>

                        <div className="mt-2 flex flex-wrap gap-2">
                          <button className="outline-btn rounded-xl px-2.5 py-1 text-[11px] font-semibold" type="button" disabled={busy || !key.exists || !!keyBusy} onClick={() => void runKeyAction(key, "toggle")}>
                            {busyToggle ? "..." : key.enabled ? "Отключить ключ" : "Включить ключ"}
                          </button>
                          <button className="outline-btn rounded-xl px-2.5 py-1 text-[11px] font-semibold" type="button" disabled={busy || !key.exists || !!keyBusy} onClick={() => void runKeyAction(key, "reset")}>
                            {busyReset ? "..." : "Сбросить трафик"}
                          </button>
                          <button className="outline-btn rounded-xl px-2.5 py-1 text-[11px] font-semibold" type="button" disabled={busy || !key.exists || !!keyBusy} onClick={() => void runKeyAction(key, "resync")}>
                            {busyResync ? "..." : "Синхронизировать sub ID"}
                          </button>
                          <button className="outline-btn rounded-xl px-2.5 py-1 text-[11px] font-semibold" type="button" disabled={!String(key.vless_link || "").trim()} onClick={() => void copyText(String(key.vless_link || ""))}>
                            Скопировать ссылку
                          </button>
                        </div>

                        <div className="mt-3 rounded-xl border border-violet-200/40 bg-white/80 p-2 dark:border-violet-500/20 dark:bg-slate-900/60">
                          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Политика ноды и лимиты трафика</p>
                          <div className="grid gap-2 sm:grid-cols-3">
                            <input
                              value={draft.burst_mbps}
                              onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, burst_mbps: event.target.value } }))}
                              placeholder="Burst-лимит (Mbps)"
                              className="rounded-lg border border-violet-200/50 bg-white px-2 py-1 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                            />
                            <input
                              value={draft.soft_cap_gb}
                              onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, soft_cap_gb: event.target.value } }))}
                              placeholder="Soft cap (ГБ)"
                              className="rounded-lg border border-violet-200/50 bg-white px-2 py-1 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                            />
                            <input
                              value={draft.hard_cap_gb}
                              onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, hard_cap_gb: event.target.value } }))}
                              placeholder="Hard cap (ГБ)"
                              className="rounded-lg border border-violet-200/50 bg-white px-2 py-1 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                            />
                          </div>
                          <div className="mt-2 flex flex-wrap items-center gap-3">
                            <label className="inline-flex items-center gap-1 text-[11px]">
                              <input type="checkbox" checked={draft.notify_soft} onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, notify_soft: event.target.checked } }))} />
                              Уведомлять на soft cap
                            </label>
                            <label className="inline-flex items-center gap-1 text-[11px]">
                              <input type="checkbox" checked={draft.notify_hard} onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, notify_hard: event.target.checked } }))} />
                              Уведомлять на hard cap
                            </label>
                            <label className="inline-flex items-center gap-1 text-[11px]">
                              <input type="checkbox" checked={draft.auto_disable_on_hard} onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, auto_disable_on_hard: event.target.checked } }))} />
                              Автоотключение на hard cap
                            </label>
                            <label className="inline-flex items-center gap-1 text-[11px]">
                              <input type="checkbox" checked={draft.apply_now} onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, apply_now: event.target.checked } }))} />
                              Применить сразу
                            </label>
                            <button className="outline-btn rounded-lg px-2 py-1 text-[11px] font-semibold" type="button" onClick={() => void savePolicy(key.node_code)} disabled={policyBusy === key.node_code}>
                              {policyBusy === key.node_code ? "..." : "Сохранить политику"}
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
                  <p className="font-semibold">История ключей (сбросы / ротации / ресинк)</p>
                  <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={() => void reloadSelected()} disabled={busy}>
                    Обновить
                  </button>
                </div>
                <p className="mb-3 text-xs text-slate-500">
                  Здесь видны низкоуровневые операции с ключами, чтобы быстро понять, когда доступ ротировали, сбрасывали, синхронизировали или переносили между нодами.
                </p>
                <div className="max-h-[44vh] overflow-auto">
                  <table className="min-w-full text-xs">
                    <thead>
                      <tr className="text-left text-slate-500">
                        <th className="px-2 py-2">Дата</th>
                        <th className="px-2 py-2">Действие</th>
                        <th className="px-2 py-2">Нода</th>
                        <th className="px-2 py-2">Актор</th>
                        <th className="px-2 py-2">Метаданные</th>
                      </tr>
                    </thead>
                    <tbody>
                      {keyHistoryRows.map((row) => (
                        <tr key={row.id} className="border-t border-white/30 dark:border-white/10">
                          <td className="px-2 py-2 whitespace-nowrap">{fmtRuDate(row.created_at)}</td>
                          <td className="px-2 py-2"><span className={`badge ${historyBadgeClass(row.action)}`}>{actionLabel(row.action)}</span></td>
                          <td className="px-2 py-2">{row.node_code || "-"}</td>
                          <td className="px-2 py-2">{row.actor_tg_id || "-"}</td>
                          <td className="px-2 py-2 max-w-[260px] truncate">{row.meta ? JSON.stringify(row.meta) : ""}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {!keyHistoryRows.length ? <p className="px-2 py-3 text-xs text-slate-500">История ключей пока пуста.</p> : null}
                </div>
              </div>
            ) : null}

            {detailTab === "audit" ? (
              <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <p className="font-semibold">Админ-аудит</p>
                  <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={() => void reloadSelected()} disabled={busy}>
                    Обновить
                  </button>
                </div>
                <p className="mb-3 text-xs text-slate-500">
                  В этой таблице записаны более высокоуровневые действия оператора над пользователем из admin-поверхностей.
                </p>
                <div className="max-h-[44vh] overflow-auto">
                  <table className="min-w-full text-xs">
                    <thead>
                      <tr className="text-left text-slate-500">
                        <th className="px-2 py-2">Дата</th>
                        <th className="px-2 py-2">Актор</th>
                        <th className="px-2 py-2">Действие</th>
                        <th className="px-2 py-2">Метаданные</th>
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
                  {!auditRows.length ? <p className="px-2 py-3 text-xs text-slate-500">Записей аудита пока нет.</p> : null}
                </div>
              </div>
            ) : null}
          </>
        )}
      </article>

      {dialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/65 p-4">
          <div className="glass-card max-h-[min(92vh,720px)] w-full max-w-lg overflow-auto p-5">
            {dialog.kind === "message" ? (
              <>
                <h3 className="font-display text-xl font-semibold">Сообщение пользователю</h3>
                <p className="mt-1 text-xs text-slate-500">Это отправит прямое сообщение оператором в Telegram.</p>
                <textarea
                  value={dialog.text}
                  onChange={(event) => setDialog({ kind: "message", text: event.target.value })}
                  rows={5}
                  className="mt-4 w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                  placeholder="Введите текст сообщения"
                />
                <div className="mt-4 flex justify-end gap-2">
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setDialog(null)}>
                    Отмена
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy || !dialog.text.trim()} onClick={() => void submitMessageDialog()}>
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
                  className="mt-4 w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                  placeholder="Дней"
                />
                <div className="mt-4 flex justify-end gap-2">
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setDialog(null)}>
                    Отмена
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void submitExtendDialog()}>
                    Применить
                  </button>
                </div>
              </>
            ) : null}

            {dialog.kind === "create" ? (
              <>
                <h3 className="font-display text-xl font-semibold">Создать manual/test пользователя</h3>
                <p className="mt-1 text-xs text-slate-500">Manual-аккаунты допустимы только для админских и тестовых сценариев.</p>
                <input
                  value={dialog.displayName}
                  onChange={(event) => setDialog({ kind: "create", displayName: event.target.value, days: dialog.days })}
                  className="mt-4 w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                  placeholder="Имя пользователя"
                />
                <input
                  value={dialog.days}
                  onChange={(event) => setDialog({ kind: "create", displayName: dialog.displayName, days: event.target.value })}
                  type="number"
                  min={1}
                  className="mt-3 w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                  placeholder="Дней доступа"
                />
                <div className="mt-4 flex justify-end gap-2">
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setDialog(null)}>
                    Отмена
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void submitCreateManualDialog()}>
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
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setDialog(null)}>
                    Отмена
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void submitDeleteTestUserDialog()}>
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
                <div className="mt-4 flex justify-end gap-2">
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setDialog(null)}>
                    Отмена
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void runBulkAction(true)}>
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
                  className="mt-4 w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-3 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                />
                <div className="mt-4 flex justify-end gap-2">
                  <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void copyText(dialog.subscriptionUrl)}>
                    Скопировать
                  </button>
                  <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => setDialog(null)}>
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
