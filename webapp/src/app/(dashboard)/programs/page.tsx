"use client";

import { ArrowRightLeft, BriefcaseBusiness, FlaskConical, Handshake, History, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { StatusHero } from "@/components/cabinet/status-hero";
import { FOCUS_RING } from "@/components/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Field, Input, Textarea } from "@/components/ui/input";
import { Note } from "@/components/ui/note";
import { SkeletonBlock, SkeletonRegion } from "@/components/ui/skeleton";
import {
  cancelProgramApplication,
  fetchClientPrograms,
  submitProgramApplication,
  type ClientProgramsPayload,
  type ProgramApplication,
  type ProgramKind,
} from "@/lib/api";

type SupportedKind = Exclude<ProgramKind, "affiliate">;

const PROGRAM_COPY: Record<ProgramKind, { short: string; description: string; icon: typeof ArrowRightLeft }> = {
  competitor_switch: {
    short: "Переход",
    description: "Расскажите, от какого VPN переходите и что вам важно сохранить.",
    icon: ArrowRightLeft,
  },
  research: {
    short: "Исследование",
    description: "Приватное интервью или воспроизводимый баг-репорт. Оценка в магазине не оплачивается.",
    icon: FlaskConical,
  },
  team_pack: {
    short: "Команда",
    description: "Запросите предложение для 2–50 устройств без автоматического списания.",
    icon: BriefcaseBusiness,
  },
  affiliate: {
    short: "Партнёры",
    description: "Фундамент готов, но приём партнёрских заявок пока закрыт.",
    icon: Handshake,
  },
};

const STATUS_COPY: Record<ProgramApplication["status"], { label: string; tone: "neutral" | "info" | "warning" | "success" }> = {
  submitted: { label: "Принята", tone: "neutral" },
  under_review: { label: "Проверка", tone: "info" },
  approved: { label: "Одобрена", tone: "success" },
  rejected: { label: "Закрыта", tone: "warning" },
  rewarded: { label: "Начислено", tone: "success" },
  cancelled: { label: "Отменена", tone: "neutral" },
};

function formatDate(value: string | null): string {
  if (!value) return "Дата уточняется";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Дата уточняется";
  return new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long", year: "numeric" }).format(parsed);
}

export default function ProgramsPage() {
  const [data, setData] = useState<ClientProgramsPayload | null>(null);
  const [kind, setKind] = useState<SupportedKind>("competitor_switch");
  const [sourceName, setSourceName] = useState("");
  const [seats, setSeats] = useState("2");
  const [summary, setSummary] = useState("");
  const [contact, setContact] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError("");
    try {
      setData(await fetchClientPrograms());
    } catch {
      setError("Не удалось загрузить программы и заявки.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const pendingKinds = useMemo(
    () => new Set((data?.applications || []).filter((item) => ["submitted", "under_review"].includes(item.status)).map((item) => item.kind)),
    [data?.applications],
  );

  const submit = async (): Promise<void> => {
    if (busy) return;
    const cleanSummary = summary.trim();
    if (cleanSummary.length < 20) {
      setError("Опишите задачу минимум в 20 символах.");
      return;
    }
    if (kind === "competitor_switch" && sourceName.trim().length < 2) {
      setError("Укажите VPN, от которого переходите.");
      return;
    }
    const seatCount = Number.parseInt(seats, 10);
    if (kind === "team_pack" && (!Number.isInteger(seatCount) || seatCount < 2 || seatCount > 50)) {
      setError("Для команды укажите от 2 до 50 устройств.");
      return;
    }
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await submitProgramApplication({
        kind,
        source_name: kind === "competitor_switch" ? sourceName.trim() : null,
        seats: kind === "team_pack" ? seatCount : null,
        summary: cleanSummary,
        contact: contact.trim() || null,
      });
      setSummary("");
      setSourceName("");
      setMessage("Заявка принята. Решение появится здесь и в уведомлениях.");
      await load();
    } catch (caught) {
      setError(String((caught as { message?: string })?.message || "Не удалось отправить заявку."));
    } finally {
      setBusy(false);
    }
  };

  const cancel = async (applicationId: string): Promise<void> => {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await cancelProgramApplication(applicationId);
      await load();
    } catch {
      setError("Не удалось отменить заявку.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="mx-auto flex w-full max-w-[980px] flex-col gap-5">
      <StatusHero
        title="Программы POKROV"
        meta="Только после ручной проверки"
        body="Переход от другого VPN, исследования и команды. Отправка заявки сама по себе не меняет срок доступа."
        tone="neutral"
        icon={Handshake}
      />

      {loading && !data ? (
        <SkeletonRegion label="Загружаем программы"><SkeletonBlock className="h-64" /></SkeletonRegion>
      ) : (
        <>
          <section className="grid gap-3 sm:grid-cols-2">
            {(data?.capabilities || []).map((capability) => {
              const copy = PROGRAM_COPY[capability.kind];
              const Icon = copy.icon;
              const selected = capability.kind === kind;
              const supported = capability.kind !== "affiliate";
              return (
                <button
                  key={capability.kind}
                  type="button"
                  disabled={!capability.enabled || !supported}
                  aria-pressed={selected}
                  aria-describedby={`program-${capability.kind}-description`}
                  onClick={() => supported && setKind(capability.kind as SupportedKind)}
                  className={`rounded-card border p-4 text-left transition-colors ${FOCUS_RING} ${selected ? "border-brand bg-brand-soft" : "border-line bg-surface hover:bg-canvas-alt"} disabled:cursor-not-allowed disabled:opacity-65`}
                >
                  <div className="flex items-start gap-3">
                    <span className="grid size-9 shrink-0 place-items-center rounded-[10px] bg-surface text-brand"><Icon size={18} strokeWidth={2} /></span>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-bold text-ink">{capability.title}</p>
                        {!capability.enabled ? <Badge tone="neutral">Позже</Badge> : pendingKinds.has(capability.kind as SupportedKind) ? <Badge tone="info">Есть заявка</Badge> : null}
                      </div>
                      <p id={`program-${capability.kind}-description`} className="mt-1 text-sm leading-5 text-ink-soft">{copy.description}</p>
                    </div>
                  </div>
                </button>
              );
            })}
          </section>

          <Card className="flex flex-col gap-4" data-testid="program-application-form">
            <div>
              <p className="text-xs font-bold tracking-[0.08em] text-ink-muted uppercase">Новая заявка</p>
              <h2 className="mt-1 text-lg font-bold text-ink">{PROGRAM_COPY[kind].short}</h2>
            </div>
            {pendingKinds.has(kind) ? (
              <Note tone="info">Заявка этого типа уже проверяется. Новую можно отправить после решения или отмены текущей.</Note>
            ) : (
              <>
                {kind === "competitor_switch" ? (
                  <Field label="От какого VPN переходите">
                    <Input value={sourceName} maxLength={100} onChange={(event) => setSourceName(event.target.value)} placeholder="Название сервиса" />
                  </Field>
                ) : null}
                {kind === "team_pack" ? (
                  <Field label="Сколько устройств" hint="От 2 до 50">
                    <Input type="number" min={2} max={50} value={seats} onChange={(event) => setSeats(event.target.value)} />
                  </Field>
                ) : null}
                <Field label={kind === "research" ? "Что вы нашли или готовы проверить" : "Что вам нужно"} hint="Минимум 20 символов; не вставляйте пароли, ключи и конфиги.">
                  <Textarea value={summary} maxLength={2000} onChange={(event) => setSummary(event.target.value)} placeholder="Кратко опишите задачу и ожидаемый результат" />
                </Field>
                <Field label="Контакт для ответа" hint="Необязательно: Telegram или email">
                  <Input value={contact} maxLength={160} onChange={(event) => setContact(event.target.value)} placeholder="@username или name@example.com" />
                </Field>
                {kind === "research" ? <Note tone="neutral">Вознаграждение возможно только за подтверждённый полезный вклад: 1, 3 или 7 дней. Публичная оценка приложения всегда добровольна и без оплаты.</Note> : null}
                <Button onClick={() => void submit()} loading={busy} disabled={busy}>Отправить на проверку</Button>
              </>
            )}
            {message ? <Note tone="success">{message}</Note> : null}
            {error ? <Note tone="danger">{error}</Note> : null}
          </Card>
        </>
      )}

      <section className="flex flex-col gap-2">
        <div className="flex items-center gap-2 px-1 text-xs font-bold tracking-[0.08em] text-ink-soft uppercase"><History size={15} />Ваши заявки</div>
        {(data?.applications || []).length ? (
          <div className="divide-y divide-line overflow-hidden rounded-card border border-line bg-surface shadow-soft">
            {(data?.applications || []).map((application) => {
              const status = STATUS_COPY[application.status];
              const pending = ["submitted", "under_review"].includes(application.status);
              return (
                <div key={application.id} className="flex flex-col gap-2 px-4 py-3.5 sm:flex-row sm:items-center">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold text-ink">{PROGRAM_COPY[application.kind].short}</p>
                      <Badge tone={status.tone}>{status.label}</Badge>
                      {application.reward_days > 0 ? <Badge tone="success">+{application.reward_days} дн.</Badge> : null}
                    </div>
                    <p className="mt-1 line-clamp-2 text-sm text-ink-soft">{application.summary}</p>
                    <p className="mt-1 text-xs text-ink-muted">{formatDate(application.created_at)}</p>
                    {application.decision_note ? <p className="mt-2 text-sm text-ink">Комментарий: {application.decision_note}</p> : null}
                  </div>
                  {pending ? (
                    <Button variant="ghost" size="sm" disabled={busy} onClick={() => void cancel(application.id)}>
                      <X size={16} />Отменить
                    </Button>
                  ) : null}
                </div>
              );
            })}
          </div>
        ) : (
          <Note tone="neutral">Заявок пока нет.</Note>
        )}
      </section>
    </main>
  );
}
