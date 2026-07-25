"use client";

import { CheckCircle2, Clock3, RefreshCw, Search, ShieldAlert, XCircle } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { adminFieldClass, adminTextAreaClass } from "@/components/admin/admin-shell";
import {
  adminProgramApplications,
  adminReviewProgramApplication,
  type AdminProgramApplication,
} from "@/lib/api";
import { fmtRuDate } from "@/lib/date-format";

const KIND_LABELS: Record<string, string> = {
  competitor_switch: "Переход от VPN",
  research: "Исследование",
  team_pack: "Команда",
};

const STATUS_LABELS: Record<string, string> = {
  submitted: "Принята",
  under_review: "Проверяется",
  approved: "Одобрена",
  rejected: "Отклонена",
  rewarded: "Награждена",
  cancelled: "Отменена",
};

export default function AdminProgramsPage() {
  const [rows, setRows] = useState<AdminProgramApplication[]>([]);
  const [status, setStatus] = useState("");
  const [kind, setKind] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [note, setNote] = useState("");
  const [rewardDays, setRewardDays] = useState<0 | 1 | 3 | 7>(0);
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState("");

  const selected = useMemo(() => rows.find((row) => row.id === selectedId) || null, [rows, selectedId]);

  const load = useCallback(async (): Promise<void> => {
    setError("");
    try {
      const next = await adminProgramApplications({ status, kind, limit: 200 });
      setRows(next);
      if (selectedId && !next.some((row) => row.id === selectedId)) setSelectedId("");
    } catch (caught) {
      setError(String((caught as { message?: string })?.message || "Не удалось загрузить заявки."));
    }
  }, [kind, selectedId, status]);

  useEffect(() => {
    void load();
  }, [load]);

  const choose = (row: AdminProgramApplication): void => {
    setSelectedId(row.id);
    setNote(row.operator_note || "");
    setRewardDays((row.reward_days === 1 || row.reward_days === 3 || row.reward_days === 7 ? row.reward_days : 0) as 0 | 1 | 3 | 7);
    setConfirmation("");
    setError("");
    setResult("");
  };

  const review = async (nextStatus: "under_review" | "approved" | "rejected"): Promise<void> => {
    if (!selected || busy) return;
    if (rewardDays > 0 && nextStatus !== "approved") {
      setError("Начисление возможно только вместе с одобрением.");
      return;
    }
    if (selected.kind === "team_pack" && rewardDays > 0) {
      setError("Заявка команды не начисляет бонусные дни.");
      return;
    }
    if (rewardDays > 0 && confirmation.trim() !== selected.id) {
      setError("Для начисления введите полный ID заявки.");
      return;
    }
    setBusy(true);
    setError("");
    setResult("");
    try {
      const response = await adminReviewProgramApplication(selected.id, {
        status: nextStatus,
        operator_note: note.trim() || null,
        reward_days: rewardDays,
        confirm_application_id: rewardDays > 0 ? confirmation.trim() : "",
      });
      setResult(response.application.rewarded ? `Начислено ${response.application.reward_days} дн. Идемпотентная операция сохранена.` : "Решение сохранено.");
      setConfirmation("");
      await load();
      setSelectedId(response.application.id);
    } catch (caught) {
      setError(String((caught as { message?: string })?.message || "Не удалось сохранить решение."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-5">
      <article className="glass-card p-4">
        <h2 className="font-display text-xl font-bold">Заявки программ</h2>
        <p className="mt-2 text-sm text-[color:var(--atlas-text-soft)]">
          Ничего не начисляется при отправке. Награда 1/3/7 дней требует одобрения и точного подтверждения ID.
        </p>
      </article>

      <article className="glass-card p-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end">
          <label className="flex flex-1 flex-col gap-1 text-xs font-semibold text-[color:var(--atlas-text-soft)]">
            Статус
            <select className={adminFieldClass} value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="">Все</option>
              {Object.entries(STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <label className="flex flex-1 flex-col gap-1 text-xs font-semibold text-[color:var(--atlas-text-soft)]">
            Тип
            <select className={adminFieldClass} value={kind} onChange={(event) => setKind(event.target.value)}>
              <option value="">Все</option>
              {Object.entries(KIND_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <button className="outline-btn inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void load()}>
            <RefreshCw size={15} /> Обновить
          </button>
        </div>
        {error ? <p className="mt-3 text-sm text-[color:var(--atlas-status-danger-text)]">{error}</p> : null}
      </article>

      <div className="grid gap-5 xl:grid-cols-[1.05fr_.95fr]">
        <article className="glass-card p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="font-display text-lg font-bold">Очередь</h2>
            <span className="badge badge-violet">{rows.length}</span>
          </div>
          <div className="space-y-2">
            {rows.length === 0 ? (
              <div className="empty-state"><Search size={28} /><p className="text-xs">Заявок по фильтру нет</p></div>
            ) : null}
            {rows.map((row) => (
              <button key={row.id} type="button" onClick={() => choose(row)} className={`node-card w-full text-left ${selectedId === row.id ? "ring-2 ring-[color:var(--atlas-brand)]" : ""}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-semibold">{KIND_LABELS[row.kind] || row.kind}</p>
                    <p className="mt-1 line-clamp-2 text-sm text-[color:var(--atlas-text-soft)]">{row.summary}</p>
                    <p className="mt-1 text-[10px] text-[color:var(--atlas-text-muted)]">{fmtRuDate(row.created_at)} · {row.account_id.slice(0, 10)}…</p>
                  </div>
                  <span className="badge badge-violet shrink-0">{STATUS_LABELS[row.status] || row.status}</span>
                </div>
              </button>
            ))}
          </div>
        </article>

        <article className="glass-card p-5">
          {!selected ? (
            <div className="empty-state"><Clock3 size={28} /><p className="text-xs">Выберите заявку слева</p></div>
          ) : (
            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold tracking-wide text-[color:var(--atlas-text-muted)] uppercase">{selected.id}</p>
                <h2 className="mt-1 font-display text-lg font-bold">{KIND_LABELS[selected.kind] || selected.kind}</h2>
                <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-[color:var(--atlas-text-soft)]">{selected.summary}</p>
                {selected.source_name ? <p className="mt-2 text-sm"><strong>Источник:</strong> {selected.source_name}</p> : null}
                {selected.seats ? <p className="mt-1 text-sm"><strong>Устройств:</strong> {selected.seats}</p> : null}
                {selected.contact ? <p className="mt-1 text-sm"><strong>Контакт:</strong> {selected.contact}</p> : null}
              </div>

              <label className="flex flex-col gap-1 text-xs font-semibold text-[color:var(--atlas-text-soft)]">
                Комментарий пользователю
                <textarea className={adminTextAreaClass} maxLength={1000} value={note} onChange={(event) => setNote(event.target.value)} placeholder="Почему одобрено или отклонено" />
              </label>

              <label className="flex flex-col gap-1 text-xs font-semibold text-[color:var(--atlas-text-soft)]">
                Награда после подтверждения
                <select className={adminFieldClass} value={rewardDays} disabled={selected.kind === "team_pack"} onChange={(event) => setRewardDays(Number(event.target.value) as 0 | 1 | 3 | 7)}>
                  <option value={0}>Без начисления</option>
                  <option value={1}>1 день</option>
                  <option value={3}>3 дня</option>
                  <option value={7}>7 дней</option>
                </select>
              </label>

              {rewardDays > 0 ? (
                <label className="flex flex-col gap-1 text-xs font-semibold text-[color:var(--atlas-status-warning-text)]">
                  Введите полный ID для начисления
                  <input className={`${adminFieldClass} font-mono`} value={confirmation} onChange={(event) => setConfirmation(event.target.value)} placeholder={selected.id} />
                </label>
              ) : null}

              {result ? <p className="text-sm text-[color:var(--atlas-status-success-text)]">{result}</p> : null}
              <div className="flex flex-wrap gap-2">
                <button className="outline-btn inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void review("under_review")}><Clock3 size={15} /> В работу</button>
                <button className="btn-primary inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold" type="button" disabled={busy} onClick={() => void review("approved")}><CheckCircle2 size={15} /> Одобрить</button>
                <button className="outline-btn inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-[color:var(--atlas-status-danger-text)]" type="button" disabled={busy || rewardDays > 0} onClick={() => void review("rejected")}><XCircle size={15} /> Отклонить</button>
              </div>
              <p className="flex items-start gap-2 text-xs leading-5 text-[color:var(--atlas-text-muted)]"><ShieldAlert size={15} className="mt-0.5 shrink-0" />Повторное одобрение той же уже награждённой заявки не создаёт второй grant.</p>
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
