"use client";

import {
  adminManualBlock,
  adminManualCreate,
  adminManualExtend,
  adminManualRegenerateToken,
  adminUserCard,
  adminUserKeyResetTraffic,
  adminUserKeyResyncSubId,
  adminUserKeyToggle,
  adminUserMessage,
  adminUsers,
  type AdminUserCard,
  type AdminUserKey,
  type AdminUserRow,
} from "@/lib/api";
import { useCallback, useEffect, useState } from "react";
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

export default function AdminUsersPage() {
  const [query, setQuery] = useState("");
  const [rows, setRows] = useState<AdminUserRow[]>([]);
  const [selected, setSelected] = useState<AdminUserCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [keyBusy, setKeyBusy] = useState("");
  const [error, setError] = useState("");

  const loadUsers = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError("");
    try {
      const users = await adminUsers(query, 80, 0);
      setRows(users);
      if (users.length > 0) {
        const firstId = users[0]?.tg_id;
        if (firstId) {
          const card = await adminUserCard(firstId);
          setSelected(card);
        }
      } else {
        setSelected(null);
      }
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка загрузки"));
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  const pickUser = async (tgId: number): Promise<void> => {
    setBusy(true);
    setError("");
    try {
      const card = await adminUserCard(tgId);
      setSelected(card);
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
    try {
      if (action === "toggle") {
        await adminUserKeyToggle(selectedTgId, key.node_code, !Boolean(key.enabled));
      } else if (action === "reset") {
        await adminUserKeyResetTraffic(selectedTgId, key.node_code);
      } else {
        await adminUserKeyResyncSubId(selectedTgId, key.node_code);
      }
      await reloadSelected();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка управления ключом"));
    } finally {
      setKeyBusy("");
    }
  };

  const keys = selected?.keys || [];
  const summary = selected?.summary;

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

        {loading ? <p className="text-sm text-slate-500">Загрузка пользователей...</p> : null}
        {error ? <p className="mb-2 text-sm text-rose-500">{error}</p> : null}

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

            <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
              <p>План: <strong>{selected.user.sub_type}</strong></p>
              <p>Stars paid: <strong>{selected.user.stars_paid}</strong></p>
              <p>Referral count: <strong>{selected.user.referral_count}</strong></p>
              <p>Streak: <strong>{selected.user.streak_months}</strong></p>
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

            <div className="mt-3 rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
              <div className="mb-2 flex items-center justify-between gap-2">
                <p className="font-semibold">Ключи и ноды</p>
                <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={() => void reloadSelected()} disabled={busy || !!keyBusy}>
                  Обновить
                </button>
              </div>
              {summary ? (
                <div className="mb-3 grid gap-2 text-xs sm:grid-cols-2">
                  <p>Нод с ключом: <strong>{summary.nodes_with_client}/{summary.nodes_total}</strong></p>
                  <p>Online нод: <strong>{summary.nodes_online}</strong></p>
                  <p>Enabled нод: <strong>{summary.nodes_enabled}</strong></p>
                  <p>SubId mismatch: <strong>{summary.subid_mismatch_count}</strong></p>
                  <p>Трафик всего: <strong>{fmtTraffic(summary.traffic_total_bytes)}</strong></p>
                  <p>Panel state: <strong>{summary.panel_state || "unknown"}</strong></p>
                </div>
              ) : null}

              <div className="space-y-2">
                {keys.length === 0 ? <p className="text-xs text-slate-500">Ключи не найдены для текущего плана.</p> : null}
                {keys.map((key) => {
                  const toggleOp = `${key.node_code}:toggle`;
                  const resetOp = `${key.node_code}:reset`;
                  const resyncOp = `${key.node_code}:resync`;
                  const busyToggle = keyBusy === toggleOp;
                  const busyReset = keyBusy === resetOp;
                  const busyResync = keyBusy === resyncOp;
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
                        <button
                          className="outline-btn rounded-xl px-2.5 py-1 text-[11px] font-semibold"
                          type="button"
                          disabled={busy || !key.exists || !!keyBusy}
                          onClick={() => void runKeyAction(key, "toggle")}
                        >
                          {busyToggle ? "..." : key.enabled ? "Disable" : "Enable"}
                        </button>
                        <button
                          className="outline-btn rounded-xl px-2.5 py-1 text-[11px] font-semibold"
                          type="button"
                          disabled={busy || !key.exists || !!keyBusy}
                          onClick={() => void runKeyAction(key, "reset")}
                        >
                          {busyReset ? "..." : "Reset traffic"}
                        </button>
                        <button
                          className="outline-btn rounded-xl px-2.5 py-1 text-[11px] font-semibold"
                          type="button"
                          disabled={busy || !key.exists || !!keyBusy}
                          onClick={() => void runKeyAction(key, "resync")}
                        >
                          {busyResync ? "..." : "Resync subId"}
                        </button>
                        <button
                          className="outline-btn rounded-xl px-2.5 py-1 text-[11px] font-semibold"
                          type="button"
                          disabled={!String(key.vless_link || "").trim()}
                          onClick={() => void copyText(String(key.vless_link || ""))}
                        >
                          Copy key
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <h3 className="mt-4 font-display text-xl font-semibold">Последние тикеты</h3>
            <div className="mt-2 space-y-2">
              {(selected.tickets || []).map((ticket) => (
                <div key={ticket.id} className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
                  <p className="font-medium">#{ticket.id} • {ticket.status_title}</p>
                  <p className="text-xs text-slate-500">{ticket.last_message_preview || "Без сообщений"}</p>
                </div>
              ))}
            </div>
          </>
        )}
      </article>
    </section>
  );
}
