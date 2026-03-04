"use client";

import {
  adminManualBlock,
  adminManualCreate,
  adminManualExtend,
  adminManualRegenerateToken,
  adminUserCard,
  adminUserMessage,
  adminUsers,
  type AdminUserCard,
  type AdminUserRow,
} from "@/lib/api";
import { useEffect, useState } from "react";
import { fmtRuDate } from "../nav";

export default function AdminUsersPage() {
  const [query, setQuery] = useState("");
  const [rows, setRows] = useState<AdminUserRow[]>([]);
  const [selected, setSelected] = useState<AdminUserCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const loadUsers = async (): Promise<void> => {
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
  };

  useEffect(() => {
    void loadUsers();
  }, []);

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

  const actionMessage = async (): Promise<void> => {
    if (!selectedTgId) return;
    const text = window.prompt("Текст сообщения пользователю:");
    if (!text?.trim()) return;
    setBusy(true);
    try {
      await adminUserMessage(selectedTgId, text.trim());
      await pickUser(selectedTgId);
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
      await pickUser(selectedTgId);
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
      await pickUser(selectedTgId);
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
      await pickUser(selectedTgId);
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
